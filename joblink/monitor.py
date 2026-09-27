"""Source health — a crawler that silently returns 0 is worse than one that crashes.

Each run is recorded in the `runs` table. This turns that log into two answers:
  * which source is broken / degraded / stale, and what to do about it
  * is my *supply* actually fresh (median ad age, share with a stated salary)
"""

from __future__ import annotations

from datetime import datetime, timezone


def _age_hours(ts: str | None) -> float | None:
    if not ts:
        return None
    try:
        d = datetime.fromisoformat(ts)
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - d).days * 24 + (datetime.now(timezone.utc) - d).seconds / 3600


def health(store, *, stale_hours: float = 30.0) -> dict:
    sources = sorted({s.key for s in _all_sources()})
    out: dict[str, dict] = {}
    for key in sources:
        last = store.db.execute(
            "SELECT ts, items, errors FROM runs WHERE source=? ORDER BY id DESC LIMIT 1", (key,)).fetchone()
        cnt = store.db.execute(
            "SELECT COUNT(*) n, MAX(last_seen_at) seen, AVG(salary_min IS NOT NULL) sal, "
            "COUNT(*) FILTER (WHERE status='rejected') rej FROM jobs WHERE source=?", (key,)).fetchone() \
            if _supports_filter() else store.db.execute(
            "SELECT COUNT(*) n, MAX(last_seen_at) seen, AVG(salary_min IS NOT NULL) sal, "
            "SUM(status='rejected') rej FROM jobs WHERE source=?", (key,)).fetchone()
        hours = _age_hours(last["ts"]) if last else None
        state = "never-ran"
        if last is not None:
            if (last["items"] or 0) == 0:
                state = "broken"
            elif hours is not None and hours > stale_hours:
                state = "stale"
            else:
                state = "ok"
        out[key] = {
            "state": state, "last_run": last["ts"] if last else None,
            "last_items": (last["items"] if last else None), "open_jobs": cnt["n"] or 0,
            "salary_transparency": round((cnt["sal"] or 0) * 100, 1) if cnt["n"] else 0.0,
            "rejected": cnt["rej"] or 0, "last_error": (last["errors"] or "")[:220] if last else "",
        }
    return {"sources": out, "alerts": _alerts(out)}


def _supports_filter() -> bool:
    import sqlite3
    try:
        c = sqlite3.connect(":memory:")
        c.execute("CREATE TABLE t(a INT)").execute("SELECT COUNT(*) FILTER (WHERE a=1) FROM t")
        return True
    except Exception:
        return False


def _all_sources():
    from .config import SOURCES
    return SOURCES.values()


def _alerts(out: dict) -> list[str]:
    a = []
    for k, v in out.items():
        if v["state"] == "broken":
            a.append(f"{k}: آخرین اجرا صفر آیتم — {v['last_error'][:120] or 'بدون خطای ثبت‌شده'}")
        elif v["state"] == "stale":
            a.append(f"{k}: بیش از ۳۰ ساعت است اجرای موفق نداشته")
        elif v["state"] == "never-ran":
            pass
        if v["open_jobs"] and v["salary_transparency"] < 25:
            a.append(f"{k}: فقط {v['salary_transparency']}٪ آگهی‌ها حقوق دارند — فیلتر 'شفاف' را روشن نگه دار")
    return a


def telegram_alert(text: str, *, token: str, chat_id: str) -> bool:
    if not token:
        return False
    import httpx
    try:
        r = httpx.post(f"https://api.telegram.org/bot{token}/sendMessage",
                       json={"chat_id": chat_id, "text": text[:3900]}, timeout=15.0)
        return bool(r.json().get("ok"))
    except Exception:
        return False
