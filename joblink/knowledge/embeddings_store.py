"""Embeddings store for true semantic RAG - uses HF Inference with working token"""

import os, json, sqlite3, hashlib
from typing import List, Dict, Optional
from dataclasses import dataclass

DDL_EMB = """
CREATE TABLE IF NOT EXISTS knowledge_embeddings (
  chunk_id TEXT PRIMARY KEY,
  domain_id TEXT,
  type TEXT,
  title TEXT,
  text TEXT,
  model_id TEXT,
  dims INTEGER,
  vec TEXT,
  created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_emb_domain ON knowledge_embeddings(domain_id);
CREATE INDEX IF NOT EXISTS idx_emb_model ON knowledge_embeddings(model_id);
"""

@dataclass
class EmbeddedChunk:
    chunk_id: str
    domain_id: str
    type: str
    title: str
    text: str
    model_id: str
    dims: int
    vec: List[float]

class EmbeddingStore:
    def __init__(self, db_path="data/knowledge/knowledge.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.executescript(DDL_EMB)
        self.conn.commit()

    def _hash_id(self, text: str, model: str) -> str:
        return hashlib.sha1(f"{model}|{text}".encode()).hexdigest()[:16]

    def embed_via_hf(self, texts: List[str], model="Qwen/Qwen3-Embedding-0.6B", token: Optional[str]=None) -> List[List[float]]:
        """Use HF InferenceClient - requires HF_TOKEN env with inference scope"""
        tok = token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
        if not tok:
            raise ValueError("HF_TOKEN not set - need token with inference.serverless.write")
        try:
            from huggingface_hub import InferenceClient
            import numpy as np
            client = InferenceClient(token=tok)
            # Batch
            results = []
            batch_size = 8
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                # Qwen needs instruction?
                # For retrieval, we use query/passage format
                batch_emb = client.feature_extraction(batch, model=model)
                # batch_emb could be ndarray (batch, dim) or list
                if hasattr(batch_emb, 'shape'):
                    if len(batch_emb.shape)==2:
                        # batch
                        for row in batch_emb:
                            results.append(row.tolist() if hasattr(row, 'tolist') else list(row))
                    else:
                        results.append(batch_emb.tolist())
                else:
                    # list
                    if isinstance(batch_emb[0], list):
                        results.extend(batch_emb)
                    else:
                        results.append(batch_emb)
            return results
        except Exception as e:
            print(f"HF embed failed {e}, fallback to local if available")
            # Try local sentence-transformers
            try:
                from sentence_transformers import SentenceTransformer
                st = SentenceTransformer(model, device="cpu")
                embs = st.encode(texts, normalize_embeddings=True)
                return [list(v) for v in embs]
            except Exception as e2:
                raise RuntimeError(f"Both HF and local failed: {e} / {e2}")

    def build_knowledge_index(self, model_id="emb_qwen3_06b", hf_model="Qwen/Qwen3-Embedding-0.6B", token=None, limit=None):
        """Embed all knowledge chunks (domains+resources+quizzes) into DB"""
        from .domains import DOMAINS
        from .resources import RESOURCES
        from .quiz import QUIZZES

        chunks = []
        for d in DOMAINS:
            chunks.append({
                "chunk_id": f"{d.id}_domain",
                "domain_id": d.id,
                "type": "domain",
                "title": d.title_fa,
                "text": f"{d.title_fa}. {d.description_fa}. {d.why_needed}. Laws: {', '.join(d.relevant_laws)} Keywords: {', '.join(d.keywords)}"
            })
        for r in RESOURCES:
            chunks.append({
                "chunk_id": f"{r.domain_id}_{r.kind}_{hashlib.sha1(r.title.encode()).hexdigest()[:8]}",
                "domain_id": r.domain_id,
                "type": r.kind,
                "title": r.title,
                "text": f"{r.title} - {r.summary_fa} - {r.author} {r.year}"
            })
        for q in QUIZZES:
            chunks.append({
                "chunk_id": q.q_id,
                "domain_id": q.domain_id,
                "type": "quiz",
                "title": q.question_fa[:60],
                "text": f"سوال: {q.question_fa} جواب: {q.options_fa[q.correct_index]} توضیح: {q.explanation_fa}"
            })

        if limit:
            chunks = chunks[:limit]

        print(f"Embedding {len(chunks)} chunks with {hf_model}...")
        texts = [c["text"][:1000] for c in chunks]
        vecs = self.embed_via_hf(texts, model=hf_model, token=token)

        cur = self.conn.cursor()
        for ch, vec in zip(chunks, vecs):
            cur.execute("INSERT OR REPLACE INTO knowledge_embeddings VALUES (?,?,?,?,?,?,?,?,datetime('now'))",
                        (ch["chunk_id"], ch["domain_id"], ch["type"], ch["title"], ch["text"], model_id, len(vec), json.dumps(vec)))
        self.conn.commit()
        print(f"Stored {len(chunks)} embeddings dim {len(vecs[0]) if vecs else 0}")
        return len(chunks)

    def search(self, query: str, top_k=5, domain_filter=None, model_id="emb_qwen3_06b") -> List[Dict]:
        """Semantic search via cosine"""
        import math
        # embed query
        q_vec = self.embed_via_hf([query], model=self._hf_model_from_id(model_id))[0]
        # fetch candidates
        cur = self.conn.cursor()
        if domain_filter:
            rows = cur.execute("SELECT chunk_id, domain_id, type, title, text, vec FROM knowledge_embeddings WHERE domain_id=? AND model_id=?", (domain_filter, model_id)).fetchall()
        else:
            rows = cur.execute("SELECT chunk_id, domain_id, type, title, text, vec FROM knowledge_embeddings WHERE model_id=?", (model_id,)).fetchall()
        if not rows:
            # fallback to keyword if no embeddings yet
            print("No embeddings in DB, need build_knowledge_index first")
            return []

        def cos(a,b):
            dot = sum(x*y for x,y in zip(a,b))
            na = math.sqrt(sum(x*x for x in a))
            nb = math.sqrt(sum(x*x for x in b))
            return dot/(na*nb) if na and nb else 0

        scored = []
        for chunk_id, domain_id, typ, title, text, vec_json in rows:
            vec = json.loads(vec_json)
            score = cos(q_vec, vec)
            scored.append({"chunk_id": chunk_id, "domain_id": domain_id, "type": typ, "title": title, "text": text, "score": score})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def _hf_model_from_id(self, model_id):
        mapping = {
            "emb_qwen3_06b": "Qwen/Qwen3-Embedding-0.6B",
            "emb_qwen3_4b": "Qwen/Qwen3-Embedding-4B",
            "emb_qwen3_8b": "Qwen/Qwen3-Embedding-8B",
            "emb_e5_large": "intfloat/multilingual-e5-large",
            "emb_bge_m3": "BAAI/bge-m3",
            "emb_jina_v3": "jinaai/jina-embeddings-v3",
        }
        return mapping.get(model_id, "Qwen/Qwen3-Embedding-0.6B")

    def stats(self):
        cur = self.conn.cursor()
        rows = cur.execute("SELECT model_id, COUNT(*), AVG(dims) FROM knowledge_embeddings GROUP BY model_id").fetchall()
        return [{"model_id": r[0], "count": r[1], "avg_dims": r[2]} for r in rows]

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--build", action="store_true")
    p.add_argument("--model", default="Qwen/Qwen3-Embedding-0.6B")
    p.add_argument("--model_id", default="emb_qwen3_06b")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--query", default="اجازه کار ترکیه")
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--domain", default="")
    args = p.parse_args()
    store = EmbeddingStore()
    if args.build:
        store.build_knowledge_index(model_id=args.model_id, hf_model=args.model, limit=args.limit or None)
    print("stats", store.stats())
    if args.query:
        res = store.search(args.query, top_k=args.top, domain_filter=args.domain or None, model_id=args.model_id)
        for r in res:
            print(f"{r['domain_id']} {r['type']} {r['score']:.3f} {r['title'][:60]}")
