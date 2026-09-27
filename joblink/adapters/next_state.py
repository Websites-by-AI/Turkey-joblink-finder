"""Read the JSON state a JS site already ships to the browser (`__NEXT_DATA__`).

Why: isinolsun.com's *detail* pages are unreachable from a datacenter IP (connection reset),
yet its homepage state carries 36 complete ad objects — title, employer, city, lat/lon,
`salaryValue`, verification flag and age. Parsing the state beats both HTML scraping and a browser:
fewer bytes, no challenge, and it survives CSS/class churn. Prefer this wherever it exists.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from ..config import Source
from ..models import Job
from ..normalize import detect_lang_req, detect_skills, norm_text
from . import Adapter

NEXT_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>([\s\S]*?)</script>', re.I)


def page_state(html: str) -> dict[str, Any]:
    m = NEXT_RE.search(html)
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return {}


def dig(obj: Any, path: str) -> list[Any]:
    """`props.pageProps.suggestJobsAll.jobs` -> list, tolerating the group nesting."""
    cur: Any = obj
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list):
            nxt = []
            for x in cur:
                if isinstance(x, dict) and x.get(part) is not None:
                    v = x[part]
                    nxt.extend(v if isinstance(v, list) else [v])
            cur = nxt
        else:
            return []
    if isinstance(cur, dict):
        return [cur]
    return list(cur or [])


_AGE_RE = re.compile(r"(\d+)\s*(g|gun|gün|d|day|gün)", re.I)


def age_days(raw: Any) -> tuple[str | None, int | None]:
    """'1s' / '5 gün' -> (posted_at ISO, days). Returns (None, None) when unknowable."""
    s = str(raw or "")
    m = re.match(r"^\s*(\d+)\s*[sd]\b", s, re.I) or _AGE_RE.search(s)
    if not m:
        return None, None
    days = int(m.group(1))
    return (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat(), days


def split_range(raw: Any) -> tuple[float | None, float | None]:
    """'30.000 - 40.000' -> (30000, 40000). Turkish thousands separator, not a decimal."""
    txt = str(raw or "")
    nums = [n for n in re.findall(r"\d[\d.]{2,}", txt)]
    vals = []
    for n in nums:
        if re.fullmatch(r"\d{1,3}(\.\d{3})+", n):
            n = n.replace(".", "")
        try:
            vals.append(float(n))
        except ValueError:
            continue
    if not vals:
        return None, None
    return min(vals), (max(vals) if len(vals) > 1 else None)


WORK_TYPE = {1: "fulltime", 2: "parttime", 3: "temporary", 4: "internship", 5: "freelance"}


class NextDataBoard(Adapter):
    """Config-driven state reader.

    source.extra = {
      "jobs_path": "props.pageProps.suggestJobsAll.jobs",
      "fields":    {"title": "positionName", "company": "companyName", ...},
      "groups":    "props.pageProps.suggestJobsAll",     # optional: read group name as tag
    }
    """

    def collect(self, *, max_details: int | None = 0) -> list[Job]:
        fields = self.source.extra.get("fields") or {}
        jobs_path = self.source.extra.get("jobs_path", "props.pageProps.jobs")
        groups_path = self.source.extra.get("groups")
        jobs: dict[str, Job] = {}
        for path in self.list_pages():
            try:
                f = self.f.fetch(path, ttl=self.source.ttl_listing)
            except Exception as exc:  # noqa: BLE001
                self.errors.append(f"{path}: {type(exc).__name__}: {str(exc)[:150]}")
                continue
            state = page_state(f.text)
            if not state:
                self.errors.append(f"{path}: no __NEXT_DATA__ ({len(f.text)} bytes)")
                continue
            groups: list[tuple[str, list[dict]]] = []
            if groups_path:
                for g in dig(state, groups_path):
                    if isinstance(g, dict):
                        groups.append((str(g.get("name") or ""),
                                       [x for x in (g.get(self.source.extra.get("group_items", "jobs")) or [])
                                        if isinstance(x, dict)]))
            if not groups:
                groups = [("", [x for x in dig(state, jobs_path) if isinstance(x, dict)])]
            for tag, items in groups:
                for it in items:
                    j = self._map(it, fields, tag)
                    if j:
                        jobs.setdefault(j.uid, j)
        return list(jobs.values())

    def _map(self, it: dict[str, Any], fields: dict[str, str], tag: str) -> Job | None:
        def get(name: str, default=None):
            key = fields.get(name, name)
            return it.get(key, default)

        title = str(get("title") or "").strip()
        url = str(get("url") or "").strip()
        if not title or not url:
            return None
        ext = str(get("id") or "") or None
        lo, hi = split_range(get("salary"))
        # İşin Olsun publishes a *daily* TL figure for part-time ads ("1000" = per day).
        # Treating it as monthly would make the wage gate scream and would mislead a seeker
        # comparing against 26.005 TL/month, so convert with 21.7 working days and keep the
        # original text in raw for audit.
        if lo and lo < 5_000:          # cannot be a 2026 monthly wage in TL (min is 26.005 net)
            lo, hi = lo * 21.7, (hi or lo) * 21.7
        posted, days = age_days(get("age"))
        emp = WORK_TYPE.get(get("work_type") if isinstance(get("work_type"), int) else 0)
        blob = " ".join(filter(None, [title, str(get("company") or ""), tag, str(get("description") or "")]))
        skills, must = detect_skills(blob)
        return Job(
            source=self.source.key, external_id=ext, url=url, title=title,
            company=str(get("company") or "").strip() or None,
            city=str(get("city") or "").strip() or None, country=self.source.country,
            description=str(get("description") or f"{title} — {get('company') or ''} {tag}").strip()[:6000],
            skills=skills, must_have=must, employment_type=emp,
            remote=True if "uzaktan" in norm_text(blob) or "remote" in norm_text(blob) else None,
            salary_min=lo, salary_max=hi, currency="TRY" if lo else None,
            lang_required=detect_lang_req(blob),
            posted_at=posted,
            raw={"salary_text": get("salary"), "town": get("district"), "tag": tag,
                 "verified": get("verified"), "age_days": days,
                 "lat": get("lat"), "lon": get("lon")},
        ).clean()
