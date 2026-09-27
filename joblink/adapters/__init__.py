"""Adapters: one small class per source, sharing a polite collect loop.

Conventions
-----------
* ``parse_listing`` only *discovers* detail URLs (cheap, cacheable).
* ``parse_detail`` returns a :class:`Job` or ``None`` (drop + log).
* If a board exposes schema.org ``JobPosting`` JSON-LD, use ``jsonld_board`` -
  it is by far the most stable contract on the web and it survives redesigns.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Iterable
from urllib.parse import urljoin

from ..config import Source
from ..httpfetch import Fetcher, BlockedByUrl, strip_tags
from ..models import Job

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def iter_ldjson(text: str) -> Iterable[dict[str, Any]]:
    """Yield every JSON-LD object, flattening @graph / list wrappers."""
    for m in re.finditer(r"<script[^>]*application/ld\+json[^>]*>([\s\S]*?)</script>", text, re.I):
        blob = m.group(1).strip()
        if not blob:
            continue
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            continue
        stack = [data]
        while stack:
            cur = stack.pop()
            if isinstance(cur, list):
                stack.extend(cur)
            elif isinstance(cur, dict):
                if "@graph" in cur:
                    stack.append(cur["@graph"])
                yield cur


def job_postings(text: str) -> list[dict[str, Any]]:
    out = []
    for d in iter_ldjson(text):
        if str(d.get("@type", "")).lower() == "jobposting":
            out.append(d)
    return out


def links(text: str, pattern: str, base: str) -> list[str]:
    seen: list[str] = []
    for m in re.finditer(r"""href=["']([^"']+)["']""", text):
        href = m.group(1)
        if re.search(pattern, href):
            u = _abs(base, href.split("#")[0])
            if u not in seen:
                seen.append(u)
    return seen


def _abs(base: str, href: str) -> str:
    """urljoin(".../is-ilanlari", "34931-x-is-ilani") would drop the directory; boards do emit
    bare relative hrefs, so join against the *directory* of the current page."""
    if re.match(r"^[a-z]+://", href, re.I) or href.startswith("/"):
        return urljoin(base, href)
    return urljoin(base.rstrip("/") + "/", href)


SITEMAP_LOC = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.I)


def sitemap_urls(text: str) -> list[str]:
    return [u for u in SITEMAP_LOC.findall(text) if u.startswith("http")]


def as_list(v: Any) -> list[Any]:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _dict(v: Any) -> dict[str, Any]:
    if isinstance(v, list):
        v = next((x for x in v if isinstance(x, dict)), {})
    return v if isinstance(v, dict) else {}


def loc_str(job_loc: Any) -> str | None:
    for l in as_list(job_loc):
        if isinstance(l, dict):
            a = _dict(l.get("address"))   # schema.org allows address to be a list too
            parts = [a.get("addressLocality"), a.get("addressRegion"), a.get("addressCountry")]
            s = ", ".join(str(p) for p in parts if p)
            if s:
                return s
        elif isinstance(l, str):
            return l
    return None


def org_name(d: dict[str, Any]) -> str | None:
    """hiringOrganization is legally allowed to be a dict OR a list of dicts (real boards do both)."""
    org = d.get("hiringOrganization")
    if isinstance(org, list):
        org = next((o for o in org if isinstance(o, dict)), None)
    if isinstance(org, dict):
        return str(org.get("name") or "").strip() or None
    if isinstance(org, str):
        return org.strip() or None
    return None


def salary_from_ld(d: dict[str, Any]) -> tuple[float | None, float | None, str | None]:
    bs = d.get("baseSalary")
    if isinstance(bs, list):
        bs = next((x for x in bs if isinstance(x, dict)), None)
    if isinstance(bs, dict):
        val = bs.get("value")
        if isinstance(val, list):
            val = val[0] if val else {}
        cur = bs.get("currency")
        if isinstance(val, dict):
            cur = cur or val.get("currency")
            lo, hi = _num(val.get("minValue")), _num(val.get("maxValue"))
            flat = _num(val.get("value"))
            if lo is None and flat is not None:
                lo, hi = flat, flat
            unit = str(val.get("unitText") or bs.get("unitText") or "").upper()
            if unit in ("YEAR", "ANNUAL") and lo:                 # annual -> monthly (TR convention)
                lo, hi = lo / 12, (hi or lo) / 12
            return lo, hi, cur or "TRY"
        if isinstance(val, (int, float, str)):
            return _num(val), None, cur or "TRY"
    return None, None, None


def _num(v: Any) -> float | None:
    try:
        return float(str(v).replace(",", "").replace(".", "")) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- #
# base
# --------------------------------------------------------------------------- #
class Adapter:
    """Collects jobs for one source, honouring the source's budget knobs."""

    def __init__(self, source: Source, fetcher: Fetcher | None = None):
        self.source = source
        self.f = fetcher or Fetcher(source)
        self.errors: list[str] = []

    # -- overridable -------------------------------------------------------
    def list_pages(self) -> list[str]:
        return list(self.source.entry)

    def listing_pattern(self) -> str:
        return r"/(is-ilani|job|ilan)/"

    def parse_listing(self, text: str, url: str) -> list[str]:
        return links(text, self.listing_pattern(), url)

    def parse_detail(self, text: str, url: str) -> Job | None:  # pragma: no cover - abstract
        raise NotImplementedError

    def parse_card(self, text: str, url: str) -> list[Job]:
        """For boards where the listing page already contains everything (no detail fetch)."""
        return []

    def detail_urls(self) -> list[str]:
        """Preferred discovery order: published sitemap -> listing pages.
        A sitemap is a machine-readable contract the site *offers* to crawlers, so it is
        both cheaper and less arguable than guessing SEO paths."""
        sm = self.source.extra.get("sitemap")
        if not sm:
            return []
        urls: list[str] = []
        try:
            f = self.f.fetch(sm, ttl=24 * 3600)
        except BlockedByUrl as exc:
            self.errors.append(f"sitemap {sm}: {exc}")
            return []
        locs = sitemap_urls(f.text)
        for u in locs:
            if "<sitemap" in f.text[:400] or u.endswith(".xml"):          # index -> one level down
                if not u.endswith(".xml"):
                    continue
                try:
                    urls.extend(sitemap_urls(self.f.fetch(u, ttl=24 * 3600).text))
                except Exception as exc:  # noqa: BLE001
                    self.errors.append(f"sitemap child {u}: {exc}")
            else:
                urls.append(u)
        pat = self.source.extra.get("sitemap_filter") or self.listing_pattern()
        urls = [u for u in dict.fromkeys(urls) if re.search(pat, u)]
        return urls[: max(1, self.source.max_details)]

    # -- driver ------------------------------------------------------------
    def collect(self, *, max_details: int | None = None) -> list[Job]:
        budget = self.source.max_details if max_details is None else max_details
        jobs: dict[str, Job] = {}
        direct = self.detail_urls() if budget > 0 else []
        if direct:
            for u in direct:
                if len(jobs) >= budget:
                    break
                try:
                    df = self.f.fetch(u, ttl=self.source.ttl_detail)
                except BlockedByUrl as exc:
                    self.errors.append(f"detail {u}: {exc}")
                    continue
                if not df.ok:
                    continue
                try:
                    j = self.parse_detail(df.text, df.url)
                except Exception as exc:  # noqa: BLE001
                    self.errors.append(f"parse {u}: {type(exc).__name__}: {exc}")
                    j = None
                if j:
                    jobs.setdefault(j.uid, j)
            return list(jobs.values())
        for path in self.list_pages():
            try:
                lf = self.f.fetch(path, ttl=self.source.ttl_listing)
            except BlockedByUrl as exc:
                self.errors.append(f"listing {path}: {exc}")
                continue
            if not lf.ok:
                self.errors.append(f"listing {path}: http {lf.status}")
                continue
            for j in self.parse_card(lf.text, lf.url):
                jobs.setdefault(j.uid, j)
            if budget <= 0:
                continue
            for u in self.parse_listing(lf.text, lf.url):
                if len(jobs) >= budget:
                    break
                if u.startswith("mailto:") or u in (lf.url,):
                    continue
                try:
                    df = self.f.fetch(u, ttl=self.source.ttl_detail)
                except BlockedByUrl as exc:
                    self.errors.append(f"detail {u}: {exc}")
                    continue
                if not df.ok:
                    self.errors.append(f"detail {u}: http {df.status}")
                    continue
                try:
                    j = self.parse_detail(df.text, df.url)
                except Exception as exc:  # noqa: BLE001
                    self.errors.append(f"parse {u}: {type(exc).__name__}: {exc}")
                    j = None
                if j:
                    jobs.setdefault(j.uid, j)
        return list(jobs.values())


_JOBISH = ("aranan", "başvuru", "basvuru", "pozisyon", "görev", "calisma", "çalışma", "ilan",
           "استخدام", "شغل", "رزومه", "تجربه", "job description", "responsibilit", "arama")


# --------------------------------------------------------------------------- #
# generic JSON-LD JobPosting board  (eleman.net, secretcv.com, cvyolla.com, ...)
# --------------------------------------------------------------------------- #
from ..normalize import (detect_city, detect_lang_req, detect_remote, detect_skills,  # noqa: E402
                         norm_text, parse_salary)


class JsonLdBoard(Adapter):
    def parse_detail(self, text: str, url: str) -> Job | None:
        block = job_postings(text)
        if block:
            d = block[0]
            desc = strip_tags(str(d.get("description") or ""))
            req = [strip_tags(str(x)) for x in as_list(d.get("qualifications"))][:8]
            sk = [strip_tags(str(x)) for x in as_list(d.get("skills"))][:20]
            salary = d.get("baseSalary")
            smin, smax, cur = salary_from_ld(d)
            if smin is None:
                p = parse_salary(desc + " " + json.dumps(salary, ensure_ascii=False) if salary else desc)
                if p:
                    smin, smax, cur = p.monthly_min, p.monthly_max, p.currency
            blob = " ".join([str(d.get("title")), desc, " ".join(req), " ".join(sk)])
            skills, must = detect_skills(blob)
            if sk:
                cleaned = [re.sub(r"\s+", " ", x).strip().lower() for x in sk]
                skills = list(dict.fromkeys([c for c in cleaned if c] + skills))[:40]
            return Job(
                source=self.source.key, url=url, title=str(d.get("title") or "")[:200],
                company=org_name(d),
                city=detect_city(loc_str(d.get("jobLocation")) or "", self.source.country),
                country=self.source.country,
                description=desc[:6000],
                requirements=req, skills=skills, must_have=must,
                employment_type=(d.get("employmentType") or "").lower().replace("-", "") or None,
                remote=bool(d.get("jobLocationType") == "TELECOMMUTE") if d.get("jobLocationType")
                       else detect_remote(blob),
                seniority=None, salary_min=smin, salary_max=smax, currency=cur,
                lang_required=detect_lang_req(blob),
                posted_at=str(d.get("datePosted") or "")[:10] or None,
                raw={"tier": "ldjson"},
            ).clean()
        return self._fallback_job(text, url)

    _GENERIC_TITLES = {"", "iş ilanı", "is ilani", "ilan detayi", "ilan detay", "job detail",
                       "detay", "yeni is ilani", "eleman ilani"}
    # "Firma - Şehir - İlçe - Pozisyon İş İlanı" is the dominant ad-page heading format in TR
    _AD_LINE = re.compile(r"([A-Za-zÇĞİÖŞÜçğıöş0-9.&\s]{4,70}?)\s*-\s*"
                          r"([A-Za-zÇĞİÖŞÜçğıöş\s]{2,22})\s*-\s*"
                          r"([^\n]{3,60}?)\s*(?:İş|Is)\s*(?:İlanı|Ilani)", re.I)

    def _fallback_job(self, text: str, url: str) -> Job | None:
        """Boards without JSON-LD: <title> / <h1> / the ad-line pattern / slug.
        Refuses consent walls and JS shells so the index never gets poisoned."""
        body = strip_tags(text)
        if len(body) < 900 or not any(w in body.lower() for w in _JOBISH):
            return None
        ttl = re.search(r"<title[^>]*>([\s\S]{3,200}?)</title>", text, re.I)
        h1 = re.search(r"<h1[^>]*>([\s\S]{3,200}?)</h1>", text, re.I)
        m = re.search(r"/([a-z0-9\-\u0600-\u06FFçğıöşü]+)/?$", url.rstrip("/"))
        slug = re.sub(r"^\d+-|-\d{4,}$|\bis\s+ilani\b", "",
                      (m.group(1) if m else "").replace("-", " "), flags=re.I).strip()

        company = None
        title = ""
        for cand in (strip_tags(ttl.group(1)) if ttl else "",
                     strip_tags(h1.group(1)) if h1 else "", slug):
            cand = re.sub(r"\s*[-|–—]\s*[^-–—|]{0,30}$", "", cand).strip()
            if len(cand) > 6 and norm_text(cand) not in self._GENERIC_TITLES:
                title = cand
                break
        line = self._AD_LINE.search(title) or self._AD_LINE.search(body)
        if line:
            company = line.group(1).strip() or None
            if norm_text(title) == norm_text(line.group(0)):
                title = line.group(3).strip()
        if not title:
            return None
        skills, must = detect_skills(title + " " + body[:3000])
        p = parse_salary(body[:3000])
        return Job(source=self.source.key, url=url, title=title[:200], company=company,
                   description=body[:6000], skills=skills, must_have=must,
                   salary_min=p.monthly_min if p else None,
                   salary_max=p.monthly_max if p else None,
                   currency=p.currency if p else None,
                   city=detect_city(body[:1500], self.source.country),
                   country=self.source.country,
                   lang_required=detect_lang_req(title + " " + body[:2000]),
                   remote=detect_remote(title + " " + body[:1500])).clean()


# --------------------------------------------------------------------------- #
# kariyer.net - 403 to plain HTTP: only the browser/flare tiers can read it
# --------------------------------------------------------------------------- #
class Kariyer(JsonLdBoard):
    def list_pages(self) -> list[str]:
        kw = self.source.extra.get("keywords") or ["python", "muhasebe", "muhendis"]
        return [f"/is-ilanlari?keyword={k}" for k in kw]

    def listing_pattern(self) -> str:
        return r"/is-ilani/[^\"']*\d{5,}"


# --------------------------------------------------------------------------- #
# İŞKUR public listings (server-rendered table, no JSON-LD)
# --------------------------------------------------------------------------- #
class Iskur(Adapter):
    def listing_pattern(self) -> str:
        return r"/meslek-detaylari\.aspx"

    def parse_detail(self, text: str, url: str) -> Job | None:
        body = strip_tags(text)
        skills, must = detect_skills(body[:4000])
        return Job(source=self.source.key, url=url,
                   title=(re.search(r"<title>(.*?)</title>", text, re.S) or [None, "İŞKUR ilan"])[1].strip()[:200],
                   description=body[:6000], country="TR", skills=skills, must_have=must).clean()


# --------------------------------------------------------------------------- #
# LinkedIn guest fragment API (disabled by default - ToS!)
# --------------------------------------------------------------------------- #
class LinkedInGuest(Adapter):
    def list_pages(self) -> list[str]:
        kws = self.source.extra.get("keywords") or ["python", "accounting", "welder"]
        out = []
        for kw in kws:
            for start in range(0, self.source.pages * 25, 25):
                out.append(f"/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={kw}"
                           f"&location=Turkey&start={start}")
        return out or list(self.source.entry)

    def parse_card(self, text: str, url: str) -> list[Job]:
        jobs: list[Job] = []
        for card in re.split(r"<div class=\"base-card", text)[1:]:
            href = re.search(r'<a class="base-card__full-link[^"]*"\s+href="([^"]+)"', card)
            title = re.search(r'base-search-card__title[^>]*>\s*([\s\S]*?)\s*</h3>', card)
            sub = re.search(r'base-search-card__subtitle[^>]*>\s*([\s\S]*?)\s*</h4>', card)
            loc = re.search(r'job-search-card__location[^>]*>\s*([\s\S]*?)\s*</span>', card)
            when = re.search(r'datetime="([\d-]{10})"', card)
            if not (href and title):
                continue
            t, s = strip_tags(title.group(1)), strip_tags(sub.group(1)) if sub else ""
            blob = f"{t} {s}"
            skills, must = detect_skills(blob)
            jobs.append(Job(
                source=self.source.key, external_id=(re.search(r"(\d{8,})", card) or [None, None])[0],
                url=href.group(1).split("?")[0], title=t, company=s or None,
                city=strip_tags(loc.group(1)) if loc else None, country="TR",
                description=blob[:2000], skills=skills, must_have=must,
                posted_at=when.group(1) if when else None,
                lang_required=detect_lang_req(blob),
                remote=True if "remote" in blob.lower() else None,
            ).clean())
        return jobs

    def parse_detail(self, text: str, url: str) -> Job | None:  # not used
        return None


# --------------------------------------------------------------------------- #
# Iranian boards: markdown/text from the rendering proxy is the only thing that
# survives from a foreign egress; we store *listing intel*, never personal data.
# --------------------------------------------------------------------------- #
class IranBoard(Adapter):
    def parse_listing(self, text: str, url: str) -> list[str]:
        pat = self.source.extra.get("pattern") or r"/(job|ilan|kariyer|project|e-family)/"
        urls = links(text, pat, url)
        if urls:
            return urls
        return re.findall(r"\]\((https?://[^)]+/(?:job|project)[^)]*)\)", text)[:40]

    def parse_detail(self, text: str, url: str) -> Job | None:
        body = strip_tags(text) if "<" in text[:400] else text
        if len(body) < 200:
            return None
        title_m = re.search(r"(?:^|\n)#*\s*([^\n]{10,120})", body)
        title = (title_m.group(1).strip() if title_m else "") or url.rstrip("/").split("/")[-1]
        skills, must = detect_skills(title + " " + body[:2500])
        p = parse_salary(body[:2500])
        return Job(
            source=self.source.key, url=url, title=title[:200],
            country=self.source.country, description=body[:4000], skills=skills,
            must_have=must, salary_min=p.monthly_min if p else None,
            salary_max=p.monthly_max if p else None, currency=p.currency if p else None,
            city=detect_city(body[:1200], "IR"), remote=detect_remote(title + " " + body[:1200]),
            lang_required=detect_lang_req(title + " " + body[:1500]),
        ).clean()

    def collect(self, *, max_details: int | None = None) -> list[Job]:
        try:
            return super().collect(max_details=max_details)
        except BlockedByUrl as exc:
            self.errors.append(str(exc)[:200])
            return []


from .next_state import NextDataBoard  # noqa: E402

REGISTRY: dict[str, Callable[[Source], Adapter]] = {
    "next_data": NextDataBoard,
    "jsonld_board": JsonLdBoard,
    "kariyer": Kariyer,
    "iskur": Iskur,
    "linkedin_guest": LinkedInGuest,
    "iran_board": IranBoard,
}
