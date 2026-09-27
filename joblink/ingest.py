"""Pipeline orchestration: registry -> adapter -> store, with per-source error capture."""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from typing import Any

from .adapters import REGISTRY
from .config import SOURCES, SETTINGS, Source
from .normalize import detect_family
from .quality import screen
from .store import Store


def build(source: Source):
    try:
        cls = REGISTRY[source.adapter]
    except KeyError:
        raise ValueError(f"unknown adapter {source.adapter!r} for {source.key}") from None
    return cls(source)


def ingest(store: Store, keys: list[str] | None = None, *, only_role: str | None = "jobs",
           max_details: int | None = None, force: bool = False) -> dict[str, Any]:
    summary: dict[str, Any] = {"ok": {}, "failed": {}, "skipped": {}, "seconds": 0.0}
    t0 = time.time()
    targets = [s for s in SOURCES.values()
               if (keys is None or s.key in keys) and (only_role is None or s.role == only_role or s.key in (keys or []))]
    for src in targets:
        if not (src.enabled or force or (keys and src.key in keys)):
            summary["skipped"][src.key] = "disabled in config (see notes)"
            continue
        ad = build(src)
        try:
            jobs = ad.collect(max_details=max_details)
        except Exception as exc:  # noqa: BLE001 - one hostile site must not kill the run
            summary["failed"][src.key] = f"{type(exc).__name__}: {str(exc)[:220]}"
            store.log_run(src.key, "jobs", 0, summary["failed"][src.key])
            continue
        flagged: list[str] = []
        for j in jobs:
            q = screen(j)
            store.upsert_job(j, family=detect_family(j.search_text), status="open" if q.ok else "rejected",
                             quality={"score": round(q.score, 3), "flags": q.flags})
            if not q.ok:
                flagged.append(f"{j.url} :: {','.join(q.flags)}")
        store.log_run(src.key, "jobs", len(jobs),
                      "; ".join([*ad.errors[:4], *flagged[:4]]))
        (summary["ok"] if jobs else summary["failed"])[src.key] = {
            "jobs": len(jobs), "rejected_by_quality_gate": len(flagged),
            "flags": [f for f in flagged[:3]], "errors": ad.errors[:5]}
    summary["seconds"] = round(time.time() - t0, 1)
    summary["db"] = store.stats()
    return summary


def match_all(store: Store, top_k: int = 8) -> dict[str, int]:
    from .matcher import Matcher
    from .models import now_iso
    jobs = store.jobs()
    cands = store.candidates()
    if not jobs:
        return {"candidates": len(cands), "jobs": 0, "matches": 0}
    m = Matcher(jobs)
    n = 0
    for c in cands:
        matches = m.rank_jobs(c, k=top_k)
        for mm in matches:
            mm.created_at = now_iso()
        # replace, never merge: yesterday's recommendation must not survive today's rescoring
        store.db.execute("DELETE FROM matches WHERE cid=?", (c.cid,))
        n += store.save_matches(matches)
    return {"candidates": len(cands), "jobs": len(jobs), "matches": n}


def dump_json(obj: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
