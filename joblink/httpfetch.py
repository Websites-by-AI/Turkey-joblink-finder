"""Tiered, polite HTTP layer.

Ladder (each tier tried in order, first success wins):

  ``direct``       plain httpx with browser-ish headers, cookie jar, per-host throttle
  ``flaresolverr`` self-hosted FlareSolverr for Cloudflare *managed* challenges
  ``browser``      Cloudflare Browser Run / Browser Rendering REST API (real Chrome, CF egress)
  ``proxy``        your own geo-egress (needed for ``.ir`` hosts: they drop foreign DC IPs)
  ``reader``       text-rendering proxy (r.jina.ai style) - last resort, loses markup

Guarantees:
  * robots.txt gate before any live fetch (fail-closed for unknown/disallowed)
  * per-host minimum interval + jitter, global requests/min limiter, exponential backoff
  * per-host circuit breaker so one angry site cannot stall the whole run
  * on-disk cache with per-tier TTL, so a re-run costs zero requests
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from .config import SETTINGS, Source
from .robots import RobotsGate

_LAST: dict[str, float] = {}
_LOCK = threading.RLock()
_CALLS: list[float] = []
_BREAKER: dict[str, tuple[int, float]] = {}

UA_POOL = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/127.0.0.0 Safari/537.36",
)

def _accept_encoding() -> str:
    """Advertise only the codecs httpx can actually decode, otherwise the body comes back
    as raw brotli bytes and every parser silently finds zero links (real bug, seen 2026-09-13)."""
    have = ["gzip", "deflate"]
    for mod in ("brotli", "brotlicffi"):
        try:
            __import__(mod)
            have.append("br")
            break
        except ImportError:
            pass
    return ", ".join(have)


BLOCK_MARKERS = (
    "just a moment", "cf-mitigated", "attention required", "checking your browser",
    "enable javascript and cookies to continue", "access denied", "rate limit",
)


class BlockedByUrl(RuntimeError):
    """robots.txt or the source config forbade this URL."""


@dataclass
class Fetched:
    url: str
    status: int
    text: str
    tier: str
    cached: bool = False
    headers: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300 and bool(self.text)

    def looks_garbled(self) -> bool:
        """Undecoded body (brotli/zstd without codecs) or binary -> no point parsing it."""
        if not self.text:
            return True
        sample = self.text[:4000]
        bad = sum(1 for ch in sample if ch in ("\ufffd",) or (ord(ch) < 9))
        return bad > max(4, len(sample) * 0.01)

    def looks_blocked(self) -> bool:
        if self.looks_garbled():
            return True
        if self.status in (403, 429, 503):
            return True
        if "cf-mitigated" in {k.lower() for k in self.headers}:
            return True
        head = self.text[:1200].lower()
        return any(m in head for m in BLOCK_MARKERS)


def _cache_path(url: str) -> str:
    os.makedirs(SETTINGS.cache_dir, exist_ok=True)
    return os.path.join(SETTINGS.cache_dir, hashlib.sha1(url.encode()).hexdigest() + ".json")


def _cache_get(url: str, ttl: int) -> Fetched | None:
    if ttl <= 0:
        return None
    p = _cache_path(url)
    if not os.path.exists(p):
        return None
    if time.time() - os.path.getmtime(p) > ttl:
        return None
    try:
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        return Fetched(d["url"], d["status"], d["text"], d["tier"], cached=True,
                       headers=d.get("headers", {}))
    except Exception:
        return None


def _cache_put(f: Fetched) -> None:
    try:
        with open(_cache_path(f.url), "w", encoding="utf-8") as fh:
            json.dump({"url": f.url, "status": f.status, "tier": f.tier,
                       "headers": dict(f.headers), "text": f.text[:2_000_000]}, fh)
    except OSError:
        pass


def _throttle(host: str, min_interval: float) -> None:
    with _LOCK:
        wait = (_LAST.get(host, 0) + min_interval * random.uniform(0.85, 1.6)) - time.time()
        if wait > 0:
            time.sleep(wait)
        _LAST[host] = time.time()
        # global rpm
        now = time.time()
        while len(_CALLS) and now - _CALLS[0] > 60:
            _CALLS.pop(0)
        if len(_CALLS) >= SETTINGS.global_per_minute:
            time.sleep(60 - (now - _CALLS[0]) + 0.1)
        _CALLS.append(time.time())


def _breaker_open(host: str) -> bool:
    fails, until = _BREAKER.get(host, (0, 0.0))
    if fails >= 3 and time.time() < until:
        return True
    return False


def _breaker_hit(host: str) -> None:
    fails, _ = _BREAKER.get(host, (0, 0.0))
    _BREAKER[host] = (fails + 1, time.time() + min(900, 60 * 2 ** fails))


def _breaker_ok(host: str) -> None:
    _BREAKER[host] = (0, 0.0)


def _headers(url: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    host = urlparse(url).netloc
    lang = "tr-TR,tr;q=0.9,en;q=0.6" if host.endswith((".tr", "com.tr")) else \
           "fa-IR,fa;q=0.9,en;q=0.6" if host.endswith(".ir") else "en-US,en;q=0.8"
    h = {
        "User-Agent": random.choice(UA_POOL),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,*/*;q=0.8",
        "Accept-Language": lang,
        "Accept-Encoding": _accept_encoding(),
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin" if "kariyer" not in host else "none",
        "Sec-Fetch-User": "?1",
        "sec-ch-ua": '"Chromium";v="126", "Not(A:Brand";v="24"',
        "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": '"Windows"',
        "Connection": "keep-alive",
        "Referer": f"https://{host}/",
    }
    if extra:
        h.update(extra)
    return h


def _client_kwargs() -> dict[str, Any]:
    kw: dict[str, Any] = {"timeout": 25.0, "follow_redirects": True,
                          "verify": os.environ.get("SSL_CERT_FILE", True)}
    if SETTINGS.proxy:
        kw["proxy"] = SETTINGS.proxy
    return kw


# ----------------------------- tiers --------------------------------------- #

def _t_direct(url: str, *, referer: str | None, cookies: sqlite3.Connection | None = None) -> Fetched:
    kw = _client_kwargs()
    kw["headers"] = _headers(url, {"Referer": referer} if referer else None)
    with httpx.Client(**kw) as c:
        r = c.get(url)
    return Fetched(str(r.url), r.status_code, r.text, "direct", headers=dict(r.headers))


def _t_proxy(url: str, **_: Any) -> Fetched:
    """Direct fetch but through the configured in-region proxy."""
    if not SETTINGS.proxy:
        raise RuntimeError("JOBLINK_PROXY not configured")
    f = _t_direct(url)
    return Fetched(f.url, f.status, f.text, "proxy", headers=f.headers)


def _t_reader(url: str, **_: Any) -> Fetched:
    """Markdown/text rendering proxy. Loses markup -> only for intel extraction, not for parsing."""
    base = SETTINGS.reader_base
    if not base:
        raise RuntimeError("JOBLINK_READER_BASE not configured")
    target = url if base.endswith("/") else base.rstrip("/") + "/" + url.lstrip("/")
    headers = {"Accept": "text/plain", "Content-Type": "text/plain"}
    if SETTINGS.reader_token:
        headers["Authorization"] = f"Bearer {SETTINGS.reader_token}"
    with httpx.Client(timeout=60.0, follow_redirects=True) as c:
        r = c.get(target, headers=headers)
    return Fetched(url, r.status_code, r.text, "reader", headers=dict(r.headers))


def _t_flaresolverr(url: str, **_: Any) -> Fetched:
    if not SETTINGS.flaresolverr:
        raise RuntimeError("JOBLINK_FLARESOLVERR not configured")
    payload = {"cmd": "get", "url": url, "maxTimeout": 60000}
    with httpx.Client(timeout=75.0) as c:
        r = c.post(SETTINGS.flaresolverr.rstrip("/") + "/v1", json=payload)
        r.raise_for_status()
        d = r.json()["data"]
    return Fetched(d["url"], d.get("status", 200), d.get("solution", {}).get("response", ""),
                   "flaresolverr")


def _t_browser(url: str, **_: Any) -> Fetched:
    """Cloudflare Browser Run (formerly Browser Rendering) REST API: /html and /crawl."""
    if not SETTINGS.cf_browser_token:
        raise RuntimeError("CF_API_TOKEN not configured")
    base = SETTINGS.cf_browser_base.rstrip("/")
    headers = {"Authorization": f"Bearer {SETTINGS.cf_browser_token}"}
    params = {"url": url, "waitUntil": "networkidle", "timeout": "25000"}
    with httpx.Client(timeout=90.0) as c:
        r = c.get(f"{base}/html", params=params, headers=headers)
        r.raise_for_status()
    return Fetched(url, 200, r.text, "browser")


TIERS: dict[str, Any] = {
    "direct": _t_direct, "proxy": _t_proxy, "reader": _t_reader,
    "flaresolverr": _t_flaresolverr, "browser": _t_browser,
}


class Fetcher:
    def __init__(self, source: Source):
        self.source = source
        self.gate = RobotsGate(source.base, respect=SETTINGS.respect_robots)

    def url(self, path: str) -> str:
        return path if path.startswith("http") else urljoin(self.source.base + "/", path.lstrip("/"))

    def fetch(self, path: str, *, ttl: int | None = None, tier: list[str] | None = None,
              referer: str | None = None) -> Fetched:
        url = self.url(path)
        host = urlparse(url).netloc
        ttl = self.source.ttl_listing if ttl is None else ttl
        cached = _cache_get(url, ttl)
        if cached:
            return cached
        if not self.gate.allowed(url):
            raise BlockedByUrl(f"robots.txt disallows {url} ({host})")
        if _breaker_open(host):
            raise BlockedByUrl(f"circuit open for {host}")

        errors: list[str] = []
        for name in (tier or list(self.source.tier)):
            fn = TIERS.get(name)
            if fn is None:
                errors.append(f"{name}: unknown tier")
                continue
            for attempt in range(2):
                try:
                    _throttle(host, self.source.min_interval)
                    f = fn(url, referer=referer)
                    if f.ok and not f.looks_blocked():
                        _breaker_ok(host)
                        _cache_put(f)
                        return f
                    errors.append(f"{name}: status={f.status} blocked={f.looks_blocked()}")
                    # blocked -> don't retry same tier, escalate
                    break
                except Exception as exc:  # noqa: BLE001 - a tier failing must escalate, not crash
                    errors.append(f"{name}: {type(exc).__name__}: {exc}")
                    time.sleep(1.5 * (attempt + 1) + random.random())
        _breaker_hit(host)
        # Last-ditch: serve stale cache rather than nothing.
        stale = _cache_get(url, 10 ** 9)
        if stale:
            stale.tier = "stale-cache"
            return stale
        raise BlockedByUrl(f"all tiers failed for {url}: " + " | ".join(errors[-4:]))


def strip_tags(html_text: str) -> str:
    t = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html_text)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = (t.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
          .replace("&#39;", "'").replace("&lt;", "<").replace("&gt;", ">"))
    return re.sub(r"\s+", " ", t).strip()
