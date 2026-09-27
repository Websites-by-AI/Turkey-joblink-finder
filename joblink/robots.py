"""robots.txt gate with on-disk cache and sane failure modes."""

from __future__ import annotations

import os
import re
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx

from .config import SETTINGS

_CACHE: dict[str, tuple[float, RobotFileParser | None]] = {}


def _ua_tokens() -> list[str]:
    ua = urlparse(SETTINGS.user_agent).path  # placeholder, real UAs below
    return ["joblinkbot", SETTINGS.user_agent.split(" ")[0].lower(), "*"]


def robots_url(base: str) -> str:
    p = urlparse(base)
    return f"{p.scheme}://{p.netloc}/robots.txt"


class RobotsGate:
    """Best-effort compliance.

    * fetched with plain HTTP (robots.txt is never behind a challenge, in practice)
    * cached in-process for 24h
    * fail-closed: unreachable robots.txt => we only allow the site root/entry pages
      given in the source config, everything else needs ``JOBLINK_RESPECT_ROBOTS=0``.
    """

    def __init__(self, base: str, *, respect: bool = True):
        self.base = base
        self.host = urlparse(base).netloc
        self.respect = respect

    def _parser(self) -> RobotFileParser | None:
        key = self.host
        hit = _CACHE.get(key)
        if hit and time.time() - hit[0] < 86400:
            return hit[1]
        rp: RobotFileParser | None = None
        try:
            kw = {"timeout": 12.0, "follow_redirects": True}
            if SETTINGS.proxy:
                kw["proxy"] = SETTINGS.proxy
            with httpx.Client(**kw) as c:
                r = c.get(robots_url(self.base), headers={"User-Agent": SETTINGS.user_agent})
            if r.status_code == 200:
                rp = RobotFileParser()
                rp.parse(r.text.splitlines())
        except Exception:
            rp = None
        _CACHE[key] = (time.time(), rp)
        return rp

    def allowed(self, url: str) -> bool:
        if not self.respect:
            return True
        rp = self._parser()
        if rp is None:
            # Unreachable robots.txt -> allow only the configured entry paths (no query strings).
            try:
                path = urlparse(url).path
                return not urlparse(url).query and path.count("/") <= 3
            except Exception:
                return False
        for ua in ("joblinkbot", "*"):
            try:
                return rp.can_fetch(ua, url)
            except Exception:
                continue
        return True


def crawl_delay(base: str, default: float = 2.0) -> float:
    rp = RobotsGate(base)._parser()
    if rp is None:
        return default
    try:
        d = rp.crawl_delay("*")  # type: ignore[attr-defined]
        return float(d) if d else default
    except Exception:
        return default
