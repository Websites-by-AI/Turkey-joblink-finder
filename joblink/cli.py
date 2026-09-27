"""JobLink CLI.

    python -m joblink.cli sites                 # registry + measured feasibility
    python -m joblink.cli check  --source eleman_net
    python -m joblink.cli ingest --source eleman_net --source linkedin_tr
    python -m joblink.cli seed    --file examples/candidates.json
    python -m joblink.cli match   --top 8
    python -m joblink.cli report  --out data/report.html
    python -m joblink.cli demo                          # ingest+seed+match+report in one go
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict

from .config import SETTINGS, SOURCES, TR_SOURCES, IR_SOURCES
from .ingest import build, ingest, match_all
from .store import Store


def _p(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def cmd_sites(_: argparse.Namespace) -> int:
    for label, arr in (("TURKIYE - job offers", TR_SOURCES), ("IRAN - intel / demand side", IR_SOURCES)):
        print(f"\n### {label}")
        for s in arr:
            print(f"  {s.key:<16} {s.name:<26} adapter={s.adapter:<14} tier={'→'.join(s.tier):<28} "
                  f"enabled={s.enabled} role={s.role}")
            if s.notes:
                print(f"      note: {s.notes[:160]}")
    print(f"\nsettings: respect_robots={SETTINGS.respect_robots} proxy={'set' if SETTINGS.proxy else 'unset'} "
          f"cf_browser={'set' if SETTINGS.cf_browser_token else 'unset'} "
          f"reader={SETTINGS.reader_base or 'unset'} flaresolverr={'set' if SETTINGS.flaresolverr else 'unset'}")
    return 0


def cmd_check(a: argparse.Namespace) -> int:
    src = SOURCES.get(a.source)
    if not src:
        print(f"unknown source {a.source}", file=sys.stderr)
        return 2
    ad = build(src)
    out: dict = {"source": a.source, "base": src.base, "tier": list(src.tier), "entries": []}
    from .robots import RobotsGate
    out["robots"] = {"url": RobotsGate(src.base).host,
                     "allowed_entry": [RobotsGate(src.base).allowed(ad.f.url(e)) for e in src.entry]}
    for e in (src.entry[:1] if not a.all else src.entry):
        try:
            f = ad.f.fetch(e, ttl=0 if a.no_cache else src.ttl_listing)
            out["entries"].append({"path": e, "status": f.status, "tier": f.tier,
                                   "bytes": len(f.text), "looks_blocked": f.looks_blocked()})
        except Exception as exc:  # noqa: BLE001
            out["entries"].append({"path": e, "error": f"{type(exc).__name__}: {str(exc)[:300]}"})
    if a.parse:
        try:
            jobs = ad.collect(max_details=a.max_details)
            out["collected"] = len(jobs)
            out["sample"] = [asdict(j) | {"skills": j.skills} for j in jobs[:2]]
            out["sample"] = [{k: v for k, v in s.items() if k in
                              ("title", "company", "city", "url", "skills", "salary_min", "currency",
                               "remote", "requirements", "posted_at")} for s in out["sample"]]
        except Exception as exc:  # noqa: BLE001
            out["collect_error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
    _p(out)
    return 0


def cmd_ingest(a: argparse.Namespace) -> int:
    st = Store(SETTINGS.db_path)
    res = ingest(st, keys=a.source, only_role=None if a.all_roles else "jobs",
                 max_details=a.max_details, force=a.force)
    _p(res)
    st.close()
    return 0 if res["ok"] else 1


def cmd_seed(a: argparse.Namespace) -> int:
    from .intake import candidate_from_cv
    st = Store(SETTINGS.db_path)
    rows = json.load(open(a.file, encoding="utf-8"))
    n = 0
    for r in rows:
        c = candidate_from_cv(
            r["cv_text"], cid=r.get("cid") or f"demo-{n:03d}", pseudonym=r.get("pseudonym"),
            consent_token=r.get("consent_token") or "v1:demo:synthetic-consent-0000000000",
            country=r.get("country", "IR"), open_remote=r.get("open_to_remote", True),
            relocate=r.get("open_to_relocate", False))
        st.upsert_candidate(c)
        n += 1
    _p({"seeded": n, "db": st.stats()})
    st.close()
    return 0


def cmd_match(a: argparse.Namespace) -> int:
    st = Store(SETTINGS.db_path)
    _p(match_all(st, top_k=a.top))
    st.close()
    return 0


def cmd_report(a: argparse.Namespace) -> int:
    from .report import render
    _p(render(SETTINGS.db_path, a.out))
    print(f"wrote {a.out}")
    return 0


def cmd_export(a: argparse.Namespace) -> int:
    """Dump the job index to JSON so the HF Space / a static frontend can ship with real data."""
    st = Store(SETTINGS.db_path)
    rows = [j.model_dump(exclude={"raw"}) for j in st.jobs(limit=a.limit)]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=1)
    _p({"exported": len(rows), "out": a.out})
    st.close()
    return 0


def cmd_feed(a: argparse.Namespace) -> int:
    from .feed import build_feed, to_csv
    st = Store(SETTINGS.db_path)
    rows = build_feed(st, salary_only=a.salary_only, city=a.city, family=a.family,
                      limit=a.limit, with_candidates=a.with_candidates, top_k=a.top)
    txt = to_csv(rows) if a.out.endswith(".csv") else json.dumps(rows, ensure_ascii=False, indent=1)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(txt)
    _p({"feed_rows": len(rows), "out": a.out, "salary_only": a.salary_only})
    st.close()
    return 0


def cmd_alerts(a: argparse.Namespace) -> int:
    from .monitor import health, telegram_alert
    st = Store(SETTINGS.db_path)
    h = health(st)
    _p(h)
    if a.send and h["alerts"]:
        ok = telegram_alert("⚠️ JobLink\n" + "\n".join(h["alerts"]),
                            token=os.environ.get("BOT_TOKEN", ""),
                            chat_id=os.environ.get("ALERT_CHAT_ID", ""))
        print("alert delivered" if ok else "no BOT_TOKEN/ALERT_CHAT_ID - not sent")
    st.close()
    return 1 if (h["alerts"] and a.strict) else 0


def cmd_bot(a: argparse.Namespace) -> int:
    """Telegram intake. --script replays a local conversation (no token, no network)."""
    from .bot import Bot, ensure_schema
    st = Store(SETTINGS.db_path)
    ensure_schema(st)
    if a.script:
        calls: list[dict] = []
        bot = Bot(store=st, api=lambda m, **kw: (calls.append({"method": m, **kw}), {"ok": True, "result": []})[1])
        for i, msg in enumerate(json.load(open(a.script, encoding="utf-8"))):
            bot.handle_update({"update_id": i + 1, "message": {"chat": {"id": msg["chat_id"]},
                                                               "text": msg["text"]}})
        for chat, text in bot.sent:
            print(f"\n[->{chat}]\n{text}")
        _p({"replies": len(bot.sent), "api_calls": len(calls), "db": st.stats()})
        st.close()
        return 0
    token = os.environ.get("BOT_TOKEN", "")
    if not token:
        print("BOT_TOKEN is not set. (Rehearse locally: --script examples/tg_conversation.json)",
              file=sys.stderr)
        st.close()
        return 2
    from .bot import api_caller
    bot = Bot(store=st, api=api_caller(token))
    if a.broadcast:
        _p({"digests_sent": bot.broadcast(k=a.top)})
        st.close()
        return 0
    print("long-polling… (ctrl-c to stop)")
    bot.run()
    return 0


def cmd_ai_check(a: argparse.Namespace) -> int:
    """One command that tells you exactly why the AI path is or isn't working.

    Measured behaviour (2026-09-13): api-inference.huggingface.co is dead; the router answers 403
    '...does not have sufficient permissions to call Inference Providers' for fine-grained tokens
    that were created without that scope. This distinguishes that from a quota/model problem.
    """
    import httpx
    from .config import SETTINGS as S
    from .emb import Embedder
    from .llm import LLM
    st = Store(S.db_path) if os.path.exists(S.db_path) else None
    out: dict = {"embed_model": S.hf_embed_model, "llm_model": S.hf_llm_model,
                 "token": "set" if S.hf_token else "unset (export HF_TOKEN=hf_...)"}
    if not S.hf_token:
        _p(out | {"verdict": "no token - engine runs on BM25 + lexicon (this is the default and it works)"})
        return 0
    try:
        with httpx.Client(timeout=20.0) as c:
            w = c.get("https://huggingface.co/api/whoami-v2",
                      headers={"Authorization": f"Bearer {S.hf_token}"})
        out["whoami"] = {"http": w.status_code, "user": (w.json() or {}).get("name") if w.status_code == 200 else w.text[:120]}
    except Exception as exc:  # noqa: BLE001
        out["whoami"] = {"error": f"{type(exc).__name__}: {exc}"}
    emb = Embedder(db=st.db if st else None, mode="router")
    v = emb.embed(["selam dünya", "سلام دنیا"])
    out["embeddings"] = {"vectors": len(v), "dim": (len(next(iter(v.values()))) if v else 0),
                         "mode_after": emb.mode, "error": emb.last_error}
    llm = LLM(db=st.db if st else None)
    r = llm.ask("Reply with exactly: ok", max_tokens=8)
    out["chat"] = {"ok": r.ok, "cached": r.cached, "chars_in": r.chars_in,
                   "reply": r.text[:60], "error": r.error[:200]}
    errs = " ".join([str(out["embeddings"].get("error", "")), r.error]).lower()
    if "inference providers" in errs:
        out["fix"] = ("token scope: create a fine-grained token with 'Make calls to Inference Providers' "
                      "enabled - https://huggingface.co/settings/tokens/type:fine-grained")
    elif "credit" in errs or "quota" in errs or "402" in errs:
        out["fix"] = "no credits left: free tier is $0.10/month (PRO $9 = $2) - or run embeddings locally: pip install sentence-transformers && JOBLINK_EMBED_MODE=local"
    elif not out["embeddings"]["vectors"]:
        out["fix"] = "model not served by any provider for this task - try JOBLINK_EMBED_MODEL=BAAI/bge-m3 (check huggingface.co/api/models/<id>?expand[]=inferenceProviderMapping)"
    else:
        out["fix"] = "embeddings work; chat blocked (or vice versa) - see per-capability error above"
    n = len(st.jobs()) if st else 0
    out["cost_estimate"] = f"{n} ads → {emb.cost_note(n)}; ~{n} explanations → {__import__('joblink.llm', fromlist=['x']).estimate_cost(n*1600)}"
    _p(out)
    if st:
        st.close()
    return 0 if out["embeddings"]["vectors"] or out["chat"]["ok"] else 1


def cmd_explain(a: argparse.Namespace) -> int:
    """Attach a grounded 'why + what to fix' note to the top matches (LLM if usable, template if not)."""
    from .llm import LLM, explain_match
    from .matcher import Matcher
    st = Store(SETTINGS.db_path)
    jobs = {j.url: j for j in st.jobs()}
    cands = {c.cid: c for c in st.candidates()}
    m = Matcher(st.jobs(), db=st.db)
    llm = LLM(db=st.db)
    rows = list(st.db.execute(
        "SELECT cid, url, job_uid, title, score, matched_skills, gaps FROM matches "
        "ORDER BY cid, score DESC LIMIT ?", (a.limit,))) if os.path.exists(SETTINGS.db_path) else []
    out: dict[str, str] = {}
    used_llm = 0
    by_uid = {j.uid: j for j in jobs.values()}
    for r in rows:
        job = by_uid.get(r["job_uid"]) or jobs.get(r["url"])
        cand = cands.get(r["cid"])
        if not job or not cand:
            continue
        from .models import Match, Gap
        mm = Match(cid=r["cid"], job_uid=r["job_uid"], source="?", url=r["url"], title=r["title"],
                   score=r["score"], matched_skills=json.loads(r["matched_skills"] or "[]"),
                   gaps=[Gap(**g) for g in json.loads(r["gaps"] or "[]")])
        text = explain_match(llm, cand, job, mm)
        used_llm += 1 if not text.startswith("• چرا این آگهی:") else 0
        out[f"{r['cid']}::{r['url']}"] = text
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    _p({"notes": len(out), "from_llm": used_llm, "template_fallback": len(out) - used_llm,
        "llm_model": llm.model if llm.enabled else "off (no HF_TOKEN) - template wording used",
        "pii_redaction": "phones/emails/ids stripped before any request", "out": a.out})
    st.close()
    return 0


def cmd_stats(_: argparse.Namespace) -> int:
    st = Store(SETTINGS.db_path)
    _p(st.stats())
    st.close()
    return 0


def cmd_purge(_: argparse.Namespace) -> int:
    st = Store(SETTINGS.db_path)
    closed = st.mark_stale_jobs_closed(SETTINGS.__dict__.get("stale_days", 21))
    gone = st.purge_consent_revoked()
    _p({"jobs_marked_stale": closed, "candidates_deleted_for_revoked_consent": gone})
    st.close()
    return 0


def cmd_knowledge(a: argparse.Namespace) -> int:
    from .knowledge.dataset import export_all
    from .knowledge.domains import DOMAINS
    from .knowledge.resources import RESOURCES
    from .knowledge.quiz import QUIZZES
    stats = export_all(base_dir=a.out)
    # also print domains
    if a.show:
        for d in DOMAINS:
            print(f"{d.id} - {d.title_fa} [{d.risk_level}] - {d.slug}")
            if a.verbose:
                print(f"  {d.description_fa[:120]}")
                res = [r for r in RESOURCES if r.domain_id==d.id]
                print(f"  resources: {len(res)} quiz: {len([q for q in QUIZZES if q.domain_id==d.id])}")
    _p(stats)
    return 0

def cmd_quiz(a: argparse.Namespace) -> int:
    from .knowledge.quiz import get_quiz, get_all_quizzes_grouped
    from .knowledge.domains import DOMAINS
    if a.domain:
        qs = get_quiz(a.domain)
        if not qs:
            print(f"domain {a.domain} not found")
            return 2
        for q in qs[:a.limit]:
            print(f"\n{q.q_id}: {q.question_fa}")
            for i, opt in enumerate(q.options_fa):
                print(f"  {i+1}) {opt}")
            print(f"  => {q.correct_index+1}) {q.options_fa[q.correct_index]} - {q.explanation_fa}")
    else:
        grouped = get_all_quizzes_grouped()
        for did, qs in grouped.items():
            dom = next((d for d in DOMAINS if d.id==did), None)
            title = dom.title_fa if dom else did
            print(f"{did} - {title}: {len(qs)} Q")
    return 0

def cmd_ai_train(a: argparse.Namespace) -> int:
    from .knowledge.ai_training_plan import get_plan
    print(get_plan())
    if a.export:
        from .knowledge.dataset import export_all
        stats = export_all(base_dir=a.export)
        _p(stats)
    return 0

def cmd_ai_models(a: argparse.Namespace) -> int:
    from .knowledge.ai_models import MODELS, TOP3
    from .knowledge.custom_models import CUSTOM_TOP3, RAG_MODELS_10, RECOMMENDATION
    if a.top:
        _p(TOP3)
        for t in TOP3:
            print(f"\n=== TOP {t['rank']}: {t['name']} ===")
            print(f"Why: {t['why'][:200]}")
            print(f"Arch: {t['architecture'][:200]}")
            print(f"Cost: {t['cost']}")
    elif a.custom:
        print("=== CUSTOM TOP3 Rituq Insider ===")
        for c in CUSTOM_TOP3:
            print(f"{c.id} {c.name} base {c.base_model} {c.params} {c.dims} ctx {c.context} rows {c.training_rows} Iran {c.iran_score}/10 {c.best_for[:60]}")
        print("\n=== RAG 10 Models ===")
        for r in RAG_MODELS_10:
            print(f"{r['rank']:2d} {r['name']:<30} {r['type']:<25} delta {r.get('delta_polysemy')} Iran {r['iran_score']}/10 live {r['live_test']} - {r['best_for']}")
        _p(RECOMMENDATION)
    else:
        for m in MODELS:
            print(f"{m.id:<20} {m.name:<35} {m.type:<10} {m.params:<6} Iran {m.iran_score}/10 Live {m.inference_live} MTEB {m.score_mteb} - {m.best_for[:60]}")
        _p({"models": len(MODELS), "top3": len(TOP3), "custom": len(CUSTOM_TOP3), "rag_10": len(RAG_MODELS_10)})
    return 0

def cmd_rag(a: argparse.Namespace) -> int:
    from .knowledge.rag import get_rag
    rag = get_rag()
    if a.semantic:
        chunks = rag.search_semantic(a.query, top_k=a.top, domain_filter=a.domain)
        print(f"=== SEMANTIC RAG ({len(chunks)} results) ===")
    else:
        chunks = rag.search(a.query, top_k=a.top, domain_filter=a.domain)
        print(f"=== KEYWORD RAG ({len(chunks)} results) ===")
    for c in chunks:
        print(f"[{c.domain_id} {c.type} score {c.score:.3f}] {c.title} - {c.text[:150]} - {c.url}")
    if a.cv and a.job:
        from types import SimpleNamespace
        job = SimpleNamespace(title=a.job, description=a.job, skills=["welding"], city="Istanbul", url="https://example.com")
        res = rag.explain_with_llm(a.cv, job, top_k=a.top, domain_hint=a.domain)
        _p(res)
    return 0

def cmd_custom(a: argparse.Namespace) -> int:
    from .knowledge.custom_models import CUSTOM_TOP3, RAG_MODELS_10, RECOMMENDATION
    if a.list_rag:
        for r in RAG_MODELS_10:
            print(f"{r['rank']}. {r['name']} - {r['type']} - dim {r['dims']} ctx {r['context']} - delta {r.get('delta_polysemy')} - Iran {r['iran_score']}/10 - {r['live_test']} - {r['pros'][:80]}")
    else:
        for c in CUSTOM_TOP3:
            print(f"\n=== {c.id} ===")
            print(f"Name: {c.name}")
            print(f"Base: {c.base_model} {c.params} {c.dims} dims {c.context} ctx")
            print(f"Training: {c.training_data}")
            print(f"Method: {c.method}")
            print(f"Insider: {c.insider_knowledge}")
            print(f"Iran: {c.iran_score}/10 Cost train {c.cost_train} infer {c.cost_infer}")
            print(f"Pros: {c.pros_fa[:150]}")
            print(f"Best: {c.best_for}")
    _p(RECOMMENDATION)
    return 0

def cmd_demo(a: argparse.Namespace) -> int:
    st = Store(SETTINGS.db_path)
    src = a.source or ["eleman_net"]
    _p(ingest(st, keys=src, only_role=None, max_details=a.max_details, force=True))
    seed = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "examples", "candidates.json")
    if os.path.exists(seed):
        ns = argparse.Namespace(file=seed)
        cmd_seed(ns)
    _p(match_all(st, top_k=a.top))
    from .report import render
    _p(render(SETTINGS.db_path, a.out))
    print(f"report -> {a.out}")
    st.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="joblink", description="TR offers ⇄ IR seekers, matched.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("sites").set_defaults(fn=cmd_sites)

    p = sub.add_parser("check"); p.add_argument("--source", required=True)
    p.add_argument("--parse", action="store_true"); p.add_argument("--all", action="store_true")
    p.add_argument("--no-cache", action="store_true"); p.add_argument("--max-details", type=int, default=2)
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("ingest"); p.add_argument("--source", action="append")
    p.add_argument("--max-details", type=int, default=None)
    p.add_argument("--all-roles", action="store_true"); p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_ingest)

    p = sub.add_parser("seed"); p.add_argument("--file", required=True); p.set_defaults(fn=cmd_seed)
    p = sub.add_parser("match"); p.add_argument("--top", type=int, default=8); p.set_defaults(fn=cmd_match)
    p = sub.add_parser("report"); p.add_argument("--out", default=os.path.join(SETTINGS.data_dir, "report.html"))
    p.set_defaults(fn=cmd_report)
    p = sub.add_parser("feed"); p.add_argument("--out", default=os.path.join(SETTINGS.data_dir, "feed.json"))
    p.add_argument("--salary-only", action="store_true"); p.add_argument("--city")
    p.add_argument("--family"); p.add_argument("--limit", type=int, default=100)
    p.add_argument("--with-candidates", action="store_true"); p.add_argument("--top", type=int, default=3)
    p.set_defaults(fn=cmd_feed)

    p = sub.add_parser("alerts"); p.add_argument("--send", action="store_true")
    p.add_argument("--strict", action="store_true"); p.set_defaults(fn=cmd_alerts)

    p = sub.add_parser("bot"); p.add_argument("--script"); p.add_argument("--broadcast", action="store_true")
    p.add_argument("--top", type=int, default=3); p.set_defaults(fn=cmd_bot)

    p = sub.add_parser("ai-check"); p.set_defaults(fn=cmd_ai_check)
    p = sub.add_parser("explain"); p.add_argument("--limit", type=int, default=40)
    p.add_argument("--out", default=os.path.join(SETTINGS.data_dir, "explanations.json"))
    p.set_defaults(fn=cmd_explain)

    sub.add_parser("stats").set_defaults(fn=cmd_stats)
    p = sub.add_parser("export"); p.add_argument("--out", default="spaces/jobs.json")
    p.add_argument("--limit", type=int, default=5000); p.set_defaults(fn=cmd_export)
    sub.add_parser("purge").set_defaults(fn=cmd_purge)

    p = sub.add_parser("knowledge"); p.add_argument("--out", default=os.path.join(SETTINGS.data_dir, "knowledge"))
    p.add_argument("--show", action="store_true"); p.add_argument("--verbose", action="store_true")
    p.set_defaults(fn=cmd_knowledge)

    p = sub.add_parser("quiz"); p.add_argument("--domain"); p.add_argument("--limit", type=int, default=10)
    p.set_defaults(fn=cmd_quiz)

    p = sub.add_parser("ai-train"); p.add_argument("--export", default=""); p.set_defaults(fn=cmd_ai_train)

    p = sub.add_parser("ai-models"); p.add_argument("--top", action="store_true"); p.add_argument("--custom", action="store_true"); p.set_defaults(fn=cmd_ai_models)

    p = sub.add_parser("rag"); p.add_argument("--query", default="اجازه کار ترکیه"); p.add_argument("--top", type=int, default=5)
    p.add_argument("--domain"); p.add_argument("--cv", default=""); p.add_argument("--job", default=""); p.add_argument("--semantic", action="store_true")
    p.set_defaults(fn=cmd_rag)

    p = sub.add_parser("custom"); p.add_argument("--list-rag", action="store_true"); p.set_defaults(fn=cmd_custom)

    p = sub.add_parser("demo"); p.add_argument("--source", action="append")
    p.add_argument("--max-details", type=int, default=6); p.add_argument("--top", type=int, default=6)
    p.add_argument("--out", default=os.path.join(SETTINGS.data_dir, "report.html"))
    p.set_defaults(fn=cmd_demo)

    ns = ap.parse_args(argv)
    os.makedirs(SETTINGS.data_dir, exist_ok=True)
    return ns.fn(ns)


if __name__ == "__main__":
    raise SystemExit(main())
