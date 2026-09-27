"""Exporter to HF dataset format: JSONL + SQLite + dataset card + AI models + Custom Rituq + RAG 10"""

import json, os, sqlite3
from pathlib import Path
from .domains import DOMAINS
from .resources import RESOURCES
from .quiz import QUIZZES
try:
    from .ai_models import MODELS, TOP3
    HAS_MODELS = True
except Exception:
    HAS_MODELS = False
    MODELS = []
    TOP3 = []

try:
    from .custom_models import CUSTOM_TOP3, RAG_MODELS_10, RECOMMENDATION
    HAS_CUSTOM = True
except Exception as e:
    HAS_CUSTOM = False
    CUSTOM_TOP3 = []
    RAG_MODELS_10 = []
    RECOMMENDATION = {}

try:
    from .news import NEWS_10
    HAS_NEWS = True
except Exception:
    HAS_NEWS = False
    NEWS_10 = []

def export_all(base_dir="data/knowledge"):
    os.makedirs(base_dir, exist_ok=True)
    # 1. domains.json
    with open(f"{base_dir}/domains.json","w",encoding="utf-8") as f:
        json.dump([d.__dict__ for d in DOMAINS], f, ensure_ascii=False, indent=2)
    # 2. resources.json
    with open(f"{base_dir}/resources.json","w",encoding="utf-8") as f:
        json.dump([r.__dict__ for r in RESOURCES], f, ensure_ascii=False, indent=2)
    # 3. quizzes.json
    with open(f"{base_dir}/quizzes.json","w",encoding="utf-8") as f:
        json.dump([q.__dict__ for q in QUIZZES], f, ensure_ascii=False, indent=2)
    # 3b. ai_models.json
    if HAS_MODELS:
        with open(f"{base_dir}/ai_models.json","w",encoding="utf-8") as f:
            json.dump([m.__dict__ for m in MODELS], f, ensure_ascii=False, indent=2)
        with open(f"{base_dir}/top3_models.json","w",encoding="utf-8") as f:
            json.dump(TOP3, f, ensure_ascii=False, indent=2)
    # 3c. custom models + RAG 10
    if HAS_CUSTOM:
        with open(f"{base_dir}/custom_models.json","w",encoding="utf-8") as f:
            json.dump([c.__dict__ for c in CUSTOM_TOP3], f, ensure_ascii=False, indent=2)
        with open(f"{base_dir}/rag_10_models.json","w",encoding="utf-8") as f:
            json.dump(RAG_MODELS_10, f, ensure_ascii=False, indent=2)
        with open(f"{base_dir}/recommendation.json","w",encoding="utf-8") as f:
            json.dump(RECOMMENDATION, f, ensure_ascii=False, indent=2)
    # 3d. news 10
    if HAS_NEWS:
        with open(f"{base_dir}/news_10.json","w",encoding="utf-8") as f:
            json.dump([n.__dict__ for n in NEWS_10], f, ensure_ascii=False, indent=2)

    # 4. JSONL for HF datasets
    with open(f"{base_dir}/hf_dataset.jsonl","w",encoding="utf-8") as out:
        for d in DOMAINS:
            out.write(json.dumps({
                "id": f"{d.id}_domain",
                "domain_id": d.id,
                "domain_slug": d.slug,
                "type": "domain",
                "title_fa": d.title_fa,
                "title_en": d.title_en,
                "text": f"{d.title_fa}. {d.description_fa}. Why: {d.why_needed}. Laws: {', '.join(d.relevant_laws)} Keywords: {', '.join(d.keywords)}",
                "lang": "fa",
                "risk": d.risk_level
            }, ensure_ascii=False)+"\n")
        for r in RESOURCES:
            out.write(json.dumps({
                "id": f"{r.domain_id}_{r.kind}_{r.title[:30]}",
                "domain_id": r.domain_id,
                "type": r.kind,
                "title": r.title,
                "url": r.url,
                "author": r.author,
                "year": r.year,
                "text": f"{r.title} - {r.summary_fa} - {r.author} {r.year} - {r.url}",
                "lang": r.lang,
                "tags": r.tags
            }, ensure_ascii=False)+"\n")
        for q in QUIZZES:
            out.write(json.dumps({
                "id": q.q_id,
                "domain_id": q.domain_id,
                "type": "quiz",
                "question_fa": q.question_fa,
                "question_en": q.question_en,
                "options_fa": q.options_fa,
                "options_en": q.options_en,
                "correct": q.correct_index,
                "explanation_fa": q.explanation_fa,
                "explanation_en": q.explanation_en,
                "difficulty": q.difficulty,
                "text": f"سوال: {q.question_fa} گزینه‌ها: {'; '.join(q.options_fa)} جواب درست: {q.options_fa[q.correct_index]} توضیح: {q.explanation_fa}",
                "lang": "fa"
            }, ensure_ascii=False)+"\n")
        if HAS_MODELS:
            for m in MODELS:
                out.write(json.dumps({
                    "id": f"model_{m.id}",
                    "domain_id": "ai_models",
                    "type": "ai_model",
                    "title": m.name,
                    "hf_id": m.hf_id,
                    "model_type": m.type,
                    "params": m.params,
                    "dims": m.dims,
                    "context": m.context,
                    "languages": m.languages,
                    "license": m.license,
                    "inference_live": m.inference_live,
                    "iran_score": m.iran_score,
                    "mteb": m.score_mteb,
                    "text": f"{m.name} {m.type} {m.params} {m.dims} dims {m.context} context lang {','.join(m.languages)} license {m.license} live {m.inference_live} Iran {m.iran_score}/10 MTEB {m.score_mteb} Pros: {m.pros_fa} Cons: {m.cons_fa} Best for: {m.best_for}",
                    "lang": "en"
                }, ensure_ascii=False)+"\n")
            for t in TOP3:
                out.write(json.dumps({
                    "id": f"top_{t['rank']}",
                    "domain_id": "top3",
                    "type": "top_model",
                    "title": t["name"],
                    "rank": t["rank"],
                    "embedding_id": t.get("embedding_id"),
                    "llm_id": t.get("llm_id"),
                    "text": f"TOP {t['rank']}: {t['name']} - Why: {t['why']} - Arch: {t['architecture']} - Cost: {t['cost']} - Iran: {t['iran_deploy']}",
                    "lang": "fa"
                }, ensure_ascii=False)+"\n")
        if HAS_CUSTOM:
            for c in CUSTOM_TOP3:
                out.write(json.dumps({
                    "id": f"custom_{c.id}",
                    "domain_id": "custom_insider",
                    "type": "custom_model",
                    "title": c.name,
                    "base_model": c.base_model,
                    "params": c.params,
                    "dims": c.dims,
                    "context": c.context,
                    "training_data": c.training_data,
                    "training_rows": c.training_rows,
                    "method": c.method,
                    "iran_score": c.iran_score,
                    "text": f"CUSTOM {c.name} base {c.base_model} {c.params} {c.dims} dims {c.context} ctx training {c.training_data} method {c.method} insider {','.join(c.insider_knowledge)} pros {c.pros_fa} best {c.best_for}",
                    "lang": "fa"
                }, ensure_ascii=False)+"\n")
            for r in RAG_MODELS_10:
                out.write(json.dumps({
                    "id": f"rag10_{r['id']}",
                    "domain_id": "rag_10",
                    "type": "rag_model",
                    "title": r["name"],
                    "rank": r["rank"],
                    "params": r["params"],
                    "dims": r["dims"],
                    "context": r["context"],
                    "license": r["license"],
                    "live_test": r["live_test"],
                    "delta": r.get("delta_polysemy"),
                    "iran_score": r["iran_score"],
                    "text": f"RAG {r['rank']}: {r['name']} {r['type']} {r['params']} {r['dims']} dims {r['context']} ctx license {r['license']} live {r['live_test']} delta {r.get('delta_polysemy')} Iran {r['iran_score']}/10 pros {r['pros']} cons {r['cons']} best {r['best_for']} cost {r['cost']}",
                    "lang": "en"
                }, ensure_ascii=False)+"\n")
        if HAS_NEWS:
            for n in NEWS_10:
                out.write(json.dumps({
                    "id": f"news_{n.id}",
                    "domain_id": "news",
                    "type": "news",
                    "title": n.title_fa,
                    "title_tr": n.title_tr,
                    "title_en": n.title_en,
                    "date": n.date,
                    "source": n.source,
                    "url": n.url,
                    "category": n.category,
                    "importance": n.importance,
                    "text": f"NEWS {n.id} {n.title_fa} / {n.title_tr} — {n.date} — {n.source} — {n.summary_fa} — TR: {n.summary_tr} — {n.url} — tags {','.join(n.tags)}",
                    "lang": "fa"
                }, ensure_ascii=False)+"\n")

    # 5. SQLite for local + D1 mirror
    db_path = f"{base_dir}/knowledge.db"
    # Keep existing embeddings if any - backup
    existing_emb = []
    if os.path.exists(db_path):
        try:
            tmp_conn = sqlite3.connect(db_path)
            existing_emb = tmp_conn.execute("SELECT * FROM knowledge_embeddings").fetchall()
            tmp_conn.close()
        except Exception:
            pass

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS domains")
    cur.execute("DROP TABLE IF EXISTS resources")
    cur.execute("DROP TABLE IF EXISTS quizzes")
    cur.execute("DROP TABLE IF EXISTS ai_models")
    cur.execute("DROP TABLE IF EXISTS top3_models")
    cur.execute("DROP TABLE IF EXISTS custom_models")
    cur.execute("DROP TABLE IF EXISTS rag_10_models")
    cur.execute("DROP TABLE IF EXISTS news_10")
    cur.execute("""CREATE TABLE domains (id TEXT PRIMARY KEY, slug TEXT, title_fa TEXT, title_en TEXT, description_fa TEXT, risk TEXT)""")
    cur.execute("""CREATE TABLE resources (id INTEGER PRIMARY KEY AUTOINCREMENT, domain_id TEXT, kind TEXT, title TEXT, url TEXT, author TEXT, year TEXT, lang TEXT, summary_fa TEXT)""")
    cur.execute("""CREATE TABLE quizzes (q_id TEXT PRIMARY KEY, domain_id TEXT, question_fa TEXT, question_en TEXT, options_fa TEXT, options_en TEXT, correct_index INTEGER, explanation_fa TEXT, difficulty TEXT)""")
    cur.execute("""CREATE TABLE ai_models (id TEXT PRIMARY KEY, name TEXT, type TEXT, params TEXT, dims INTEGER, context INTEGER, languages TEXT, license TEXT, hf_id TEXT, inference_live INTEGER, iran_score INTEGER, mteb REAL, pros_fa TEXT, cons_fa TEXT, best_for TEXT)""")
    cur.execute("""CREATE TABLE top3_models (rank INTEGER PRIMARY KEY, name TEXT, embedding_id TEXT, llm_id TEXT, why TEXT, architecture TEXT, cost TEXT, iran_deploy TEXT)""")
    cur.execute("""CREATE TABLE custom_models (id TEXT PRIMARY KEY, name TEXT, base_model TEXT, type TEXT, params TEXT, dims INTEGER, context INTEGER, training_data TEXT, training_rows INTEGER, method TEXT, insider_knowledge TEXT, iran_score INTEGER, cost_train TEXT, cost_infer TEXT, pros_fa TEXT, best_for TEXT, hf_repo TEXT, status TEXT)""")
    cur.execute("""CREATE TABLE rag_10_models (rank INTEGER PRIMARY KEY, id TEXT, name TEXT, type TEXT, params TEXT, dims INTEGER, context INTEGER, license TEXT, live_test TEXT, delta REAL, iran_score INTEGER, pros TEXT, cons TEXT, best_for TEXT, cost TEXT)""")
    cur.execute("""CREATE TABLE news_10 (id TEXT PRIMARY KEY, title_fa TEXT, title_tr TEXT, title_en TEXT, date TEXT, source TEXT, url TEXT, summary_fa TEXT, summary_tr TEXT, category TEXT, importance TEXT)""")
    # knowledge_embeddings table - keep if exists, else create
    cur.execute("""CREATE TABLE IF NOT EXISTS knowledge_embeddings (
      chunk_id TEXT PRIMARY KEY,
      domain_id TEXT,
      type TEXT,
      title TEXT,
      text TEXT,
      model_id TEXT,
      dims INTEGER,
      vec TEXT,
      created_at TEXT
    )""")

    for d in DOMAINS:
        cur.execute("INSERT INTO domains VALUES (?,?,?,?,?,?)", (d.id, d.slug, d.title_fa, d.title_en, d.description_fa, d.risk_level))
    for r in RESOURCES:
        cur.execute("INSERT INTO resources (domain_id,kind,title,url,author,year,lang,summary_fa) VALUES (?,?,?,?,?,?,?,?)",
                    (r.domain_id, r.kind, r.title, r.url, r.author, r.year, r.lang, r.summary_fa))
    for q in QUIZZES:
        cur.execute("INSERT INTO quizzes VALUES (?,?,?,?,?,?,?,?,?)",
                    (q.q_id, q.domain_id, q.question_fa, q.question_en, json.dumps(q.options_fa, ensure_ascii=False), json.dumps(q.options_en, ensure_ascii=False), q.correct_index, q.explanation_fa, q.difficulty))
    if HAS_MODELS:
        for m in MODELS:
            cur.execute("INSERT INTO ai_models VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (m.id, m.name, m.type, m.params, m.dims or 0, m.context, json.dumps(m.languages, ensure_ascii=False), m.license, m.hf_id, int(m.inference_live), m.iran_score, m.score_mteb or 0, m.pros_fa, m.cons_fa, m.best_for))
        for t in TOP3:
            cur.execute("INSERT INTO top3_models VALUES (?,?,?,?,?,?,?,?)",
                        (t["rank"], t["name"], t.get("embedding_id",""), t.get("llm_id",""), t["why"], t["architecture"], t["cost"], t["iran_deploy"]))
    if HAS_CUSTOM:
        for c in CUSTOM_TOP3:
            cur.execute("INSERT INTO custom_models VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (c.id, c.name, c.base_model, c.type, c.params, c.dims, c.context, c.training_data, c.training_rows, c.method, json.dumps(c.insider_knowledge, ensure_ascii=False), c.iran_score, c.cost_train, c.cost_infer, c.pros_fa, c.best_for, c.hf_repo, c.status))
        for r in RAG_MODELS_10:
            cur.execute("INSERT INTO rag_10_models VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (r["rank"], r["id"], r["name"], r["type"], r["params"], r["dims"], r["context"], r["license"], r["live_test"], r.get("delta_polysemy") or 0, r["iran_score"], r["pros"], r["cons"], r["best_for"], r["cost"]))
    if HAS_NEWS:
        for n in NEWS_10:
            cur.execute("INSERT INTO news_10 VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (n.id, n.title_fa, n.title_tr, n.title_en, n.date, n.source, n.url, n.summary_fa, n.summary_tr, n.category, n.importance))

    # Restore embeddings if had
    if existing_emb:
        for row in existing_emb:
            try:
                cur.execute("INSERT OR IGNORE INTO knowledge_embeddings VALUES (?,?,?,?,?,?,?,?,?)", row)
            except Exception:
                pass

    conn.commit()
    conn.close()

    # 6. Summary stats
    stats = {
        "domains": len(DOMAINS),
        "resources": len(RESOURCES),
        "articles": len([r for r in RESOURCES if r.kind=="article"]),
        "books": len([r for r in RESOURCES if r.kind=="book"]),
        "videos": len([r for r in RESOURCES if r.kind=="video"]),
        "quizzes": len(QUIZZES),
        "ai_models": len(MODELS) if HAS_MODELS else 0,
        "top3": len(TOP3) if HAS_MODELS else 0,
        "custom_models": len(CUSTOM_TOP3) if HAS_CUSTOM else 0,
        "rag_10_models": len(RAG_MODELS_10) if HAS_CUSTOM else 0,
        "news_10": len(NEWS_10) if HAS_NEWS else 0,
        "quizzes_per_domain": {d.id: len([q for q in QUIZZES if q.domain_id==d.id]) for d in DOMAINS}
    }
    with open(f"{base_dir}/stats.json","w",encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # 7. Fine-tune scripts
    try:
        from .fine_tune import export_all_finetune_scripts
        ft_stats = export_all_finetune_scripts(out_dir=f"{base_dir}/finetune")
        stats["finetune"] = ft_stats
        with open(f"{base_dir}/stats.json","w",encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        stats["finetune_error"] = str(e)

    return stats

if __name__=="__main__":
    print(export_all())
