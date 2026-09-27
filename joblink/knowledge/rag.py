"""RAG pipeline for JobLink - uses knowledge base + jobs + embeddings"""

from __future__ import annotations
import json, os, sqlite3
from typing import List, Dict, Optional
from dataclasses import dataclass

# Try import embeddings
try:
    from ..emb import Embedder
    from ..llm import LLM
    HAS_EMB = True
except Exception:
    HAS_EMB = False

@dataclass
class RAGChunk:
    domain_id: str
    type: str
    title: str
    text: str
    url: str = ""
    score: float = 0.0

class KnowledgeRAG:
    """Simple RAG over knowledge base + jobs"""
    
    def __init__(self, knowledge_dir="data/knowledge", db_path="data/knowledge/knowledge.db"):
        self.knowledge_dir = knowledge_dir
        self.db_path = db_path
        self.chunks: List[RAGChunk] = []
        self.load()

    def load(self):
        # Load from JSONL
        jl_path = os.path.join(self.knowledge_dir, "hf_dataset.jsonl")
        if os.path.exists(jl_path):
            with open(jl_path, encoding="utf-8") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        # only keep domain + article + quiz as RAG corpus (books/videos are metadata)
                        if obj.get("type") in ("domain","article","quiz"):
                            self.chunks.append(RAGChunk(
                                domain_id=obj.get("domain_id",""),
                                type=obj.get("type",""),
                                title=obj.get("title") or obj.get("title_fa") or obj.get("question_fa","")[:50],
                                text=obj.get("text","")[:1000],
                                url=obj.get("url",""),
                                score=0.0
                            ))
                    except Exception:
                        continue
        # Load jobs as well
        jobs_path = os.path.join(os.path.dirname(self.knowledge_dir), "report.html")  # fallback
        # jobs are in main db
        try:
            from ..store import Store
            from ..config import SETTINGS
            if os.path.exists(SETTINGS.db_path):
                st = Store(SETTINGS.db_path)
                for job in st.jobs(limit=200):
                    self.chunks.append(RAGChunk(
                        domain_id="jobs",
                        type="job",
                        title=job.title,
                        text=f"{job.title} - {job.company} - {job.city} - {job.description[:500]} - skills: {', '.join(job.skills[:10])}",
                        url=job.url
                    ))
                st.close()
        except Exception:
            pass

    def search(self, query: str, top_k=5, domain_filter: Optional[str]=None, semantic: bool=False) -> List[RAGChunk]:
        """BM25-like keyword search + optional semantic embedding rerank via knowledge_embeddings table"""
        # Try semantic if requested and embeddings exist
        if semantic:
            try:
                from .embeddings_store import EmbeddingStore
                store = EmbeddingStore(db_path=self.db_path)
                # check if embeddings exist
                if store.stats():
                    results = store.search(query, top_k=top_k, domain_filter=domain_filter, model_id="emb_qwen3_06b")
                    if results:
                        out = []
                        for r in results:
                            out.append(RAGChunk(
                                domain_id=r["domain_id"],
                                type=r["type"],
                                title=r["title"],
                                text=r["text"],
                                url="",
                                score=r["score"]
                            ))
                        return out
            except Exception as e:
                print(f"semantic search fallback: {e}")

        q = query.lower()
        scored = []
        for ch in self.chunks:
            if domain_filter and ch.domain_id != domain_filter:
                continue
            # simple scoring: count overlapping words
            score = 0
            # keyword overlap
            for word in q.split():
                if len(word)>=3 and word in ch.text.lower():
                    score += 1
                if word in ch.title.lower():
                    score += 2
            # boost for domain match
            if domain_filter and ch.domain_id==domain_filter:
                score += 5
            # boost for high-risk domains
            if ch.domain_id in ("d01","d02","d06"):
                score += 0.5
            if score>0:
                ch.score = score
                scored.append(ch)
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]

    def search_semantic(self, query: str, top_k=5, domain_filter: Optional[str]=None, model_id="emb_qwen3_06b"):
        """Force semantic search via embeddings_store"""
        return self.search(query, top_k=top_k, domain_filter=domain_filter, semantic=True)

    def build_prompt(self, cv_text: str, job_title: str, job_desc: str, top_chunks: List[RAGChunk]) -> str:
        ctx = "\n\n".join([f"[{c.domain_id} - {c.type}] {c.title}: {c.text[:400]} (منبع: {c.url or c.domain_id})" for c in top_chunks])
        prompt = f"""تو یک مشاور شغلی متخصص برای ایرانیان متقاضی کار در ترکیه هستی. باید صادق، دقیق و حقوقی باشی.

رزومه کارجو (فارسی):
{cv_text[:800]}

آگهی شغلی ترکیه:
عنوان: {job_title}
توضیح: {job_desc[:800]}

دانش حقوقی مرتبط (RAG):
{ctx}

وظیفه:
1. امتیاز 0-100 بده (0 = بی‌ربط، 100 = عالی)
2. 3 مهارت هم‌پوشان
3. 2 فاصله که کارجو باید پر کند
4. هشدار حقوقی اگر شغل حضوری است و کارجو در ایران است (Çalışma izni لازم است)
5. آیا حقوق کمتر از حداقل دستمزد 26,005 TL است؟
6. توضیح فارسی کوتاه (2-3 جمله) چرا این مچ خوب یا بد است.

فرمت خروجی JSON:
{{"score": 75, "matched_skills": ["..."], "gaps": ["..."], "legal_warning": "...", "explanation_fa": "..."}}

این توضیح توسط AI تولید شده (EU AI Act Art 50).
"""
        return prompt

    def explain_with_llm(self, cv_text: str, job, top_k=3, domain_hint: Optional[str]=None) -> Dict:
        """Full RAG + LLM path if HF_TOKEN available, else template fallback"""
        chunks = self.search(f"{cv_text} {job.title} {job.description}", top_k=top_k, domain_filter=domain_hint)
        prompt = self.build_prompt(cv_text, job.title, job.description, chunks)
        
        # Try LLM if available
        if HAS_EMB:
            try:
                from ..llm import LLM
                from ..store import Store
                from ..config import SETTINGS
                import os
                db = None
                if os.path.exists(SETTINGS.db_path):
                    # open readonly
                    db = sqlite3.connect(SETTINGS.db_path)
                llm = LLM(db=db)
                if llm.enabled:
                    res = llm.ask(prompt, max_tokens=400)
                    if res.ok and res.text:
                        # try parse JSON
                        try:
                            # extract JSON block
                            import re
                            m = re.search(r'\{.*\}', res.text, re.DOTALL)
                            if m:
                                parsed = json.loads(m.group(0))
                                parsed["rag_chunks"] = [c.__dict__ for c in chunks]
                                parsed["from_llm"] = True
                                return parsed
                        except Exception:
                            return {"explanation_fa": res.text[:500], "rag_chunks": [c.__dict__ for c in chunks], "from_llm": True}
            except Exception as e:
                print(f"LLM failed: {e}")
        
        # Fallback template
        return {
            "score": 50,
            "matched_skills": job.skills[:3],
            "gaps": ["زبان ترکی", "اجازه کار"],
            "legal_warning": "اگر حضوری است، بدون Çalışma izni شروع نکن - /danesh d01",
            "explanation_fa": f"این آگهی {job.title} در {job.city} با مهارت‌های {', '.join(job.skills[:3])} هم‌پوشانی دارد. باید زبان ترکی و اجازه کار را بررسی کنی.",
            "rag_chunks": [c.__dict__ for c in chunks],
            "from_llm": False
        }

# Singleton
_rag_instance = None
def get_rag():
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = KnowledgeRAG()
    return _rag_instance
