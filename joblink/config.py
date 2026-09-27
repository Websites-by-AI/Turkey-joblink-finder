"""Site registry + runtime knobs.

Every entry is a *source*, described declaratively, so adding a site = adding a dict.
The ``tier`` list is the fallback ladder used by :mod:`joblink.httpfetch`.

Measured feasibility from a plain EU datacenter IP (curl, no browser), 2026-09-13:
    kariyer.net      -> HTTP 403 on every path            (needs browser tier + TR/EU IP)
    yenibiris.com    -> HTTP 403, `cf-mitigated: challenge` (Cloudflare managed challenge)
    tr.indeed.com    -> HTTP 403
    jooble.org       -> HTTP 403
    secretcv.com     -> HTTP 200 (static, JSON-LD blocks present)
    eleman.net       -> HTTP 200 (static, JobPosting JSON-LD on detail pages)  <-- best free source
    cvyolla.com      -> HTTP 200 (static, sitemap.xml published in robots.txt)
    isinolsun.com    -> HTTP 200 but flaky/timeouts
    iskur.gov.tr     -> HTTP 200 (public portal)
    tr.linkedin.com/jobs-guest/... -> HTTP 200, 30 cards/page (ToS-risky, keep off the main path)
    *.ir boards      -> TCP timeout from this egress (they filter foreign DC space);
                        reachable through a rendering proxy / in-region egress
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass
class Source:
    key: str
    name: str
    country: str
    role: str                       # "jobs" | "talent"
    adapter: str                    # key in joblink.adapters.REGISTRY
    base: str
    tier: tuple[str, ...] = ("direct", "browser", "reader")
    entry: tuple[str, ...] = ()    # listing entry points (relative or absolute)
    pages: int = 2                  # listing pages per entry per run
    max_details: int = 12           # detail pages per run (be polite: hard budget)
    ttl_listing: int = 6 * 3600
    ttl_detail: int = 7 * 24 * 3600
    min_interval: float = 2.5
    enabled: bool = True
    notes: str = ""
    extra: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# TURKEY - supply side (job offers)
# --------------------------------------------------------------------------- #
TR_SOURCES: list[Source] = [
    # Backbone of the blue-collar vertical: city + category SEO hubs, all 200 on plain HTTP,
    # and every detail page carries schema.org JobPosting (measured 2026-09-13).
    Source("eleman_net", "Eleman.net", "TR", "jobs", "jsonld_board",
           "https://www.eleman.net",
           tier=("direct", "reader"),
           entry=("/is-ilanlari/istanbul", "/is-ilanlari/ankara", "/is-ilanlari/izmir",
                  "/is-ilanlari/bursa", "/is-ilanlari/kocaeli", "/is-ilanlari/antalya",
                  "/is-ilanlari/uretim", "/is-ilanlari/guvenlik", "/is-ilanlari/temizlik",
                  "/is-ilanlari/imalat", "/is-ilanlari"),
           pages=1, max_details=45, min_interval=1.6,
           notes="SEO hubs beat query strings for robots-compliance AND stability. Unknown slugs "
                 "return the generic page (same byte size) - harmless, dedupe absorbs it."),
    Source("secretcv", "SecretCV", "TR", "jobs", "jsonld_board",
           "https://www.secretcv.com",
           tier=("browser", "direct"),
           entry=("/is-ilanlari", "/is-ilanlari/istanbul", "/is-ilanlari/ankara"),
           pages=1, max_details=8, enabled=False,
           notes="robots disallows */?p=*, */?k=*, /is-ilanlari/ara -> crawl SEO city/category "
                 "paths only, never the query-string search."),
    Source("kariyer_net", "Kariyer.net", "TR", "jobs", "kariyer",
           "https://www.kariyer.net",
           tier=("browser", "flaresolverr", "reader"),
           entry=("/is-ilanlari",), pages=1, max_details=6, min_interval=4.0,
           enabled=False,
           notes="Plain HTTP returns 403. Use Cloudflare Browser Run / stealth browser from a "
                 "TR or EU egress; prefer their official feed/partnership over crawling."),
    Source("yenibiris", "Yenibiriş", "TR", "jobs", "jsonld_board",
           "https://www.yenibiris.com",
           tier=("browser", "flaresolverr"),
           entry=("/is-ilanlari",), pages=1, max_details=6,
           notes="Cloudflare managed challenge (cf-mitigated: challenge) => browser tier mandatory."),
    Source("isinolsun", "İşin Olsun (Next.js state)", "TR", "jobs", "next_data",
           "https://www.isinolsun.com",
           tier=("direct",), entry=("/",), pages=1, max_details=0, min_interval=6.0,
           ttl_listing=3 * 3600,
           extra={
               "jobs_path": "props.pageProps.suggestJobsAll.jobs",
               "groups": "props.pageProps.suggestJobsAll", "group_items": "jobs",
               "fields": {"title": "positionName", "company": "companyName", "id": "jobId",
                          "url": "shareUrl", "city": "cityName", "district": "townName",
                          "salary": "salaryValue", "work_type": "workType", "age": "durationDayText",
                          "verified": "companyVerificationStateType", "lat": "latitude",
                          "lon": "longitude"},
           },
           notes="measured: '/' -> 200 with 36 ad objects inside __NEXT_DATA__ incl. salaryValue "
                 "and lat/lon, while /is-ilani/* details reset the connection -> parse the state, "
                 "never the detail page. Kariyer.net group, so this covers much of that inventory."),
    Source("cvyolla", "CV Yolla", "TR", "jobs", "jsonld_board",
           "https://www.cvyolla.com",
           tier=("direct",),
           entry=("/is-ilanlari",), pages=1, max_details=6,
           extra={"sitemap": "/sitemaps/ilanlar.xml", "sitemap_filter": r"-is-ilani$"},
           notes="robots.txt publishes a sitemap index (/sitemap.xml -> sitemaps/ilanlar.xml). "
                 "Discovery via <loc> beats scraping the search page."),
    Source("iskur", "İŞKUR (gov)", "TR", "jobs", "iskur",
           "https://www.iskur.gov.tr",
           tier=("direct", "reader"),
           entry=("/acik-is-v2.aspx?menu=isArayis",), pages=1, max_details=4, min_interval=5.0,
           enabled=False,
           notes="measured: /acik-is-v2.aspx returns a 390-byte stub; the real search is a POST "
                 "form on eservis.iskur.gov.tr (unreachable here). Needs a form-login replay - "
                 "low priority, and public-portal data is the most sensitive to hammer."),
    Source("toptalent", "Toptalent.co", "TR", "jobs", "jsonld_board",
           "https://www.toptalent.co",
           tier=("direct", "browser"),
           entry=("/popis",), pages=1, max_details=4,
           notes="Guess the path: 404 on /popis from here - confirm before enabling."),
    Source("careerjet_tr", "Careerjet (TR aggregator)", "TR", "jobs", "careerjet",
           "https://www.careerjet.com.tr",
           tier=("direct", "reader"),
           entry=("/is-ilanlari?q=python", "/is-ilanlari?q=muhasebe"),
           pages=1, max_details=0, enabled=False,
           notes="measured: every path returns the same 10,953-byte page containing a reCAPTCHA "
                 "data-sitekey -> it is a consent/challenge wall, not results. Dead end without a "
                 "licensed feed; do NOT try to solve captchas."),
    Source("linkedin_tr", "LinkedIn Jobs (guest, TR)", "TR", "jobs", "linkedin_guest",
           "https://tr.linkedin.com",
           tier=("direct",),
           entry=("/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=python&location=Turkey&start=0",),
           pages=1, max_details=0, enabled=False,
           notes="Works today (200, 30 cards) BUT scraping it breaches LinkedIn user agreement - "
                 "keep disabled unless you have a licensed data partner."),
]

# --------------------------------------------------------------------------- #
# IRAN - demand side.
#
# IMPORTANT (read PLAN-FA.md §4): the *resume databases* of these boards are not
# scrapeable and must not be scraped. They are login-gated to paying employers,
# and bulk acquisition of personal data is a criminal offence in TR (TCK 136,
# 2-4 y.) and unlawful processing under GDPR/KVKK.
# So IR sources are used for: (a) market/salary intel from PUBLIC ad pages,
# (b) candidate *acquisition* (we drive traffic there, candidates opt in to US),
# (c) official partner feeds / Telegram channels the board itself publishes.
# --------------------------------------------------------------------------- #
IR_SOURCES: list[Source] = [
    Source("jobinja", "Jobinja", "IR", "intel", "iran_board",
           "https://jobinja.ir", tier=("proxy", "reader", "direct"),
           entry=("/jobs",), pages=1, max_details=4,
           notes="Reachable from IR/qualified egress; from a foreign DC IP: TCP timeout. "
                 "Public job pages only."),
    Source("jobvision", "JobVision", "IR", "intel", "iran_board",
           "https://jobvision.ir", tier=("proxy", "reader"),
           entry=("/jobs",), pages=1, max_details=4,
           notes="Heavy JS app -> needs browser/proxy tier."),
    Source("e_estekhdam", "E-Estekhdam", "IR", "intel", "iran_board",
           "https://www.e-estekhdam.com", tier=("proxy", "reader"),
           entry=("/job",), pages=1, max_details=4,
           notes="Large volume of gov/private ads, classic server-rendered HTML + RSS-ish feeds."),
    Source("irantalent", "IranTalent", "IR", "talent", "iran_board",
           "https://www.irantalent.com", tier=("proxy", "reader"),
           entry=("/en/jobs/", "/jobs/"), pages=1, max_details=4,
           notes="English-language listings + diaspora-facing. Closest analogue to our product."),
    Source("quera", "Quera Jobs", "IR", "intel", "iran_board",
           "https://www.quera.com", tier=("direct", "proxy"),
           entry=("/job",), pages=1, max_details=4,
           notes="Dev-focused; reachable from this egress (HTTP 200 confirmed)."),
    Source("ponisha", "Ponisha", "IR", "intel", "iran_board",
           "https://ponisha.ir", tier=("direct", "proxy"),
           entry=("/projects",), pages=1, max_details=4,
           notes="Freelance projects = remote-ready supply of *workers*, best for the "
                 "'gig' wedge of the marketplace. 200 confirmed from here."),
    Source("karboom", "Karboom", "IR", "intel", "iran_board",
           "https://karboom.io", tier=("proxy", "reader"),
           entry=("/jobs",), pages=1, max_details=4, notes=""),
    Source("eekhtebkar", "Eekhtebkar", "IR", "intel", "iran_board",
           "https://www.eekhtebkar.ir", tier=("proxy", "reader"),
           entry=("/JobIndex",), pages=1, max_details=2, notes=""),
    Source("divar_jobs", "Divar - jobs", "IR", "intel", "iran_board",
           "https://divar.ir", tier=("proxy", "reader"),
           entry=("/s/tehran/jobs",), pages=1, max_details=2,
           notes="Classifieds, huge volume of informal work; API exists (divar.ir/serv14) "
                 "but is private - use the public web pages."),
    Source("sheypoor_jobs", "Sheypoor - jobs", "IR", "intel", "iran_board",
           "https://www.sheypoor.com", tier=("proxy", "reader"),
           entry=("/tehran/jobs",), pages=1, max_details=2, notes=""),
]

SOURCES: dict[str, Source] = {s.key: s for s in (*TR_SOURCES, *IR_SOURCES)}


@dataclass
class Settings:
    data_dir: str = _env("JOBLINK_DATA", "data")
    proxy: str = _env("JOBLINK_PROXY")                       # e.g. http://user:pass@ir-egress:8080
    user_agent: str = _env(
        "JOBLINK_UA",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    )
    # Tier 2: Cloudflare "Browser Run" / Browser Rendering REST API
    cf_browser_base: str = _env("CF_BROWSER_BASE", "https://browser-rendering.cloudflare.com")
    cf_browser_token: str = _env("CF_API_TOKEN")
    # Tier 3: text-rendering proxy (jina.ai style) - the only thing that reached .ir from a DC IP
    reader_base: str = _env("JOBLINK_READER_BASE", "https://r.jina.ai/")
    reader_token: str = _env("JOBLINK_READER_TOKEN")
    # Tier 1.5: FlareSolverr self-hosted (solve CF challenges)
    flaresolverr: str = _env("JOBLINK_FLARESOLVERR")         # http://localhost:8191
    respect_robots: bool = _env("JOBLINK_RESPECT_ROBOTS", "1") == "1"
    hf_token: str = _env("HF_TOKEN")
    # 2026-09-13 probe: api-inference.huggingface.co is gone (connection closed, no HTTP status).
    # Live surface is router.huggingface.co. intfloat/multilingual-e5-large is served by
    # hf-inference + deepinfra; multilingual-e5-BASE has NO provider (inferenceProviderMapping:null)
    # so do not "downgrade" to base - it would 404.
    hf_embed_model: str = _env("JOBLINK_EMBED_MODEL", "intfloat/multilingual-e5-large")
    hf_embed_mode: str = _env("JOBLINK_EMBED_MODE", "auto")   # auto | off | router | local
    hf_llm_model: str = _env("JOBLINK_LLM_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    global_per_minute: int = int(_env("JOBLINK_RPM", "20") or 20)

    @property
    def db_path(self) -> str:
        return os.path.join(self.data_dir, "joblink.sqlite3")

    @property
    def cache_dir(self) -> str:
        return os.path.join(self.data_dir, "cache")


SETTINGS = Settings()

# Currency → USD heuristic (manual table, refreshed weekly by an operator).
FX_TO_USD = {"TRY": 0.024, "TL": 0.024, "IRR": 0.000016, "IRT": 0.00016,
             "TOMAN": 0.00016, "USD": 1.0, "EUR": 1.06}
