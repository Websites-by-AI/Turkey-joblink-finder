"""Measure whether HF embeddings actually improve THIS corpus (fa/tr), before you commit to them.

    HF_TOKEN=hf_xxx python3 examples/hf_probe.py [--limit 60] [--persist]

Baseline = current engine (BM25 + skill lexicon + gates). Treatment = same engine with the
multilingual-e5 cosine blended into the semantic term. We report: how many top-3 sets move,
a couple of concrete before/after rows, and the token bill — because the free HF tier is
$0.10/month and "it works" is not the same question as "it works and is worth paying for".
"""

from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from joblink.config import SETTINGS          # noqa: E402
from joblink.emb import Embedder, cos        # noqa: E402
from joblink.matcher import Matcher          # noqa: E402
from joblink.store import Store              # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--persist", action="store_true", help="write vectors into the sqlite cache")
    a = ap.parse_args()

    if not os.environ.get("HF_TOKEN"):
        print("HF_TOKEN is not set. Use:  HF_TOKEN=hf_xxx python3 examples/hf_probe.py", file=sys.stderr)
        return 2

    st = Store(SETTINGS.db_path)
    jobs = st.jobs(limit=a.limit)
    cands = st.candidates()
    if not jobs or not cands:
        print("empty DB - run `python -m joblink.cli ingest` + `seed` first")
        return 2
    print(f"corpus: {len(jobs)} ads × {len(cands)} profiles | model={SETTINGS.hf_embed_model}")

    # ---- sanity: one live call, does the router answer at all? ----
    e = Embedder(db=st.db if a.persist else None, mode="router")
    t0 = time.time()
    probe = e.embed(["برنامه‌نویس پایتون با دژانگو و داکر", "Kıdemli Python Geliştirici (Django, Docker)",
                     "Garson aranıyor - restoran servisi", "Operasyon müdürü lojistik depo"])
    dt = time.time() - t0
    print(f"live call: {len(probe)}/4 vectors in {dt:.1f}s  status={e.status()}")
    if len(probe) < 4:
        print("  ✗ embeddings unavailable from this account/network — engine stays on BM25, fine.")
        return 1
    dims = {len(v) for v in probe.values()}
    print(f"  dims={dims}  (1024 expected for e5-large)")
    texts = list(probe)
    sim_fa_tr = cos(probe[texts[0]], probe[texts[1]])
    sim_off = cos(probe[texts[0]], probe[texts[2]])
    print(f"  cross-lingual check: python-fa ↔ python-tr = {sim_fa_tr:.3f} | python-fa ↔ waiter-tr = {sim_off:.3f}"
          f"  → {'OK' if sim_fa_tr > sim_off else 'SUSPECT'}")

    # ---- corpus-side vectors (this is the part that costs money) ----
    base = Matcher(jobs, embedder=Embedder(mode="off"))
    e2 = Embedder(db=st.db if a.persist else None, mode="router")
    t1 = time.time()
    chars = sum(len(j.search_text[:1800]) for j in jobs)
    vecs = e2.embed([j.search_text[:1800] for j in jobs])
    print(f"\nads embedded: {len(vecs)}/{len(jobs)} in {time.time()-t1:.1f}s "
          f"({chars:,} chars ≈ {chars//4:,} tokens)")
    adv = Matcher(jobs, embedder=e2)

    moved = kept = 0
    samples = []
    for c in cands:
        b = {m.job_uid for m in base.rank_jobs(c, k=3)}
        v = adv.rank_jobs(c, k=3)
        a_ = {m.job_uid for m in v}
        kept += len(b & a_)
        moved += len(a_ - b)
        if a_ - b and len(samples) < 3:
            samples.append((c.pseudonym, base.rank_jobs(c, k=1), v))
    tot = kept + moved
    print(f"top-3 churn: {moved}/{tot} slots changed ({100*moved/max(1,tot):.0f}%), "
          f"{kept} identical")
    for who, b, v in samples:
        print(f"\n■ {who}")
        print("  before:", " | ".join(f"{m.title[:34]} {m.score:.0f}" for m in b) or "—")
        print("  after :", " | ".join(f"{m.title[:34]} {m.score:.0f}" for m in v))

    if a.persist:
        n = st.db.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        print(f"\npersisted vectors in cache: {n} (a re-run of the same corpus now costs 0 tokens)")
    print("\nverdict guide: churn 0%  → the lexicon already carries it, keep it off (free)."
          "\n               churn 15-40% with better titles → worth it, but persist + batch."
          "\n               churn >60% → the two signals disagree; make embedding a reranker, not a scorer.")
    st.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
