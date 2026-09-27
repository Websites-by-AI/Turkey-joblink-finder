"""Employer-facing feed + the salary-transparency feature.

42 of the 51 ads we scraped today state no salary. For an Iranian blue-collar applicant that is
the difference between "an opportunity" and "a risk", so the feed exposes what is *known*,
converts it to all three currencies the two sides think in (TL / USD / Toman), and lets the buyer
filter to transparent ads only. That filter is a product, not a nicety.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Iterable

from .config import FX_TO_USD

EUR_PER_USD = 1 / 1.06


def tl_monthly(job) -> tuple[float | None, float | None]:
    cur = (job.currency or "TRY").upper()
    k = FX_TO_USD.get(cur, 1.0)
    return (job.salary_min or 0) * k / FX_TO_USD.get("TRY", 1.0) if job.salary_min else (None, None), \
           (job.salary_max or 0) * k / FX_TO_USD.get("TRY", 1.0) if job.salary_max else None


def money(job) -> dict[str, Any]:
    """Normalised monthly money in the three currencies seekers/employers actually compare."""
    lo_usd, hi_usd = None, None
    if job.salary_min:
        rate = FX_TO_USD.get((job.currency or "TRY").upper())
        if rate:
            lo_usd = job.salary_min * rate
            hi_usd = (job.salary_max or job.salary_min) * rate
    out: dict[str, Any] = {"salary_stated": bool(job.salary_min), "monthly_usd": None,
                           "monthly_try": None, "monthly_toman": None, "raw": None}
    if lo_usd:
        out["monthly_usd"] = [round(lo_usd), round(hi_usd or lo_usd)]
        out["monthly_try"] = [round(lo_usd / FX_TO_USD["TRY"]), round((hi_usd or lo_usd) / FX_TO_USD["TRY"])]
        out["monthly_toman"] = [round(lo_usd / FX_TO_USD["TOMAN"]), round((hi_usd or lo_usd) / FX_TO_USD["TOMAN"])]
    elif getattr(job, "raw", None):
        out["raw"] = (job.raw or {}).get("salary_text")
    return out


def fmt_local(v: float | None) -> str:
    return f"{round(v):,}".replace(",", "٬") if v else "—"


def summarize(job) -> str:
    """One line an employer can read in a Telegram/email digest."""
    m = money(job)
    sal = (f"{fmt_local(m['monthly_try'][0])}–{fmt_local(m['monthly_try'][1])} TL "
           f"(≈ {m['monthly_usd'][0]}$)") if m["salary_stated"] else "حقوق در آگهی نیامده"
    bits = [job.title, job.company or "—", job.city or "TR", sal]
    if job.remote:
        bits.append("دورکاری")
    return " · ".join(bits)


def build_feed(store, *, salary_only: bool = False, city: str | None = None,
               family: str | None = None, limit: int = 100,
               with_candidates: bool = False, top_k: int = 3) -> list[dict]:
    jobs = store.jobs()
    out: list[dict] = []
    cands = store.candidates() if with_candidates else []
    matcher = None
    if with_candidates:
        from .matcher import Matcher
        matcher = Matcher(jobs)
    for j in jobs:
        m = money(j)
        if salary_only and not m["salary_stated"]:
            continue
        if city and (j.city or "").lower() != city.lower():
            continue
        row: dict[str, Any] = {
            "title": j.title, "company": j.company, "city": j.city, "country": j.country,
            "remote": j.remote, "salary_stated": m["salary_stated"],
            "monthly_try": m["monthly_try"], "monthly_usd": m["monthly_usd"],
            "monthly_toman": m["monthly_toman"], "employment_type": j.employment_type,
            "skills": j.skills[:12], "url": j.url, "source": j.source, "posted_at": j.posted_at,
        }
        with store.db as db:
            r = db.execute("SELECT family FROM jobs WHERE url=?", (j.url,)).fetchone()
            row["family"] = r["family"] if r else None
        if family and row["family"] != family:
            continue
        if matcher is not None:
            from .models import Candidate, Skill   # noqa: PLC0415
            pool = []
            for c in cands:
                mm = matcher.score(c, j, 0.0, 1.0, None)
                if mm.score >= 35:
                    pool.append({"cid": c.cid, "pseudonym": c.pseudonym, "score": mm.score,
                                 "skills": [s.name for s in c.skills][:8], "matched": mm.matched_skills})
            row["candidates"] = sorted(pool, key=lambda x: -x["score"])[:top_k]
        out.append(row)
        if len(out) >= limit:
            break
    return out


def to_csv(rows: Iterable[dict]) -> str:
    rows = list(rows)
    if not rows:
        return ""
    buf = io.StringIO()
    cols = [c for c in rows[0] if c not in ("candidates",)]
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        r = dict(r)
        for k in ("monthly_try", "monthly_usd", "monthly_toman", "skills"):
            if r.get(k) is not None:
                r[k] = json.dumps(r[k], ensure_ascii=False)
        w.writerow(r)
    return buf.getvalue()
