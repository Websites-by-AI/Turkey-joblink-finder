"""Cross-lingual normalisation: Farsi (fa) + Turkish (tr) + English (en) -> one vector space.

Why this file matters: a Jobinja ad says «برنامه‌نویس پایتون», a Kariyer.net ad says
"Python Geliştirici" and the candidate's CV says "Python developer". Without a shared
canonical layer, no matcher - embedding model or not - will ever connect them reliably.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# text plumbing
# --------------------------------------------------------------------------- #
_ZWNJ = "\u200c"
_PERSIAN_MAP = str.maketrans({
    "\u064a": "\u06cc",  # Arabic yeh  -> Persian yeh
    "\u0643": "\u06a9",  # Arabic kaf  -> Persian kehe
    "\u060c": "،",
    "\u0640": "",        # tatweel
})
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_TURKISH_LOWER = str.maketrans({"İ": "i", "I": "ı", "Ş": "ş", "Ğ": "ğ", "Ü": "ü",
                                "Ö": "ö", "Ç": "ç", "Â": "a", "â": "a"})

FA_STOP = set("""و در به از با که این آن برای هم با خود را می شود است شده خواهد بود هست
دارد دارند کرد کردیم انجام همه هر یک دو سه چند با روی تحت ضمن اینک اکنون """.split())
TR_STOP = set("""ve ile bir bu da de için olarak daha çok sonra önce hakkında olan olmak
yapmak bulunmakta aranan aday personel""".split())
EN_STOP = set("""the a an and or of for to in on with is are be as at by from we you our
their will would can could should must looking seeking strong good nice team environment
experience required responsibilities qualification qualifications benefits""".split())
STOPWORDS = FA_STOP | TR_STOP | EN_STOP


def norm_text(s: str | None) -> str:
    """Language-agnostic visual normalisation (keeps both scripts intact)."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.translate(_PERSIAN_MAP).translate(_DIGITS).translate(_TURKISH_LOWER)
    # fold latin diacritics so "Yazılım"/"yazilim" and "MÜHENDİS"/"muhendis" collide,
    # while Persian/Arabic script passes through untouched (it has no combining marks here)
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("ı", "i").replace("İ", "i")
    s = unicodedata.normalize("NFC", s)
    s = s.replace(_ZWNJ, " ")                       # نیم‌فاصله -> space (پایتون matches برنامه نویسی پایتون)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\[\d+\]|\(\d+\)", " ", s)          # "1." list bullets / counters are noise
    s = re.sub(r"(?<=\s)\d{1,2}[.)](?=\s)|^\d{1,2}[.)](?=\s)", " ", s)
    s = re.sub(r"[^\w\s\u0600-\u06FF،؛٪+%.,/&$€£-]", " ", s, flags=re.UNICODE)
    s = re.sub(r"_+", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def tokens(s: str | None) -> list[str]:
    s = norm_text(s)
    out: list[str] = []
    for raw in re.findall(r"[\w\u0600-\u06FF][\w\u0600-\u06FF+#.\-/]*", s):
        if len(raw) < 2 or raw in STOPWORDS:
            continue
        out.append(raw)
    return out


def light_stem(tok: str) -> str:
    """Cheap suffix stripper for tr/fa/en tech vocabulary. Not linguistically pure - just
    enough that geliştirici/geliştirme, برنامه‌نویسی/برنامه‌نویس, developers/developer collapse."""
    for suf in ("leri", "lari", "cusu", "cisi", "sı", "si", "cu", "cı", "ian", "ing",
                "ers", "or", "er", "ed", "es", "ar", "ci", "cı", "si", "lı", "li", "u", "ı", "s"):
        if len(tok) > len(suf) + 3 and tok.endswith(suf):
            return tok[: -len(suf)]
    return tok


def content_tokens(s: str | None) -> list[str]:
    return [light_stem(t) for t in tokens(s)]


# --------------------------------------------------------------------------- #
# skill + occupation lexicon  (alias -> canonical id)
# --------------------------------------------------------------------------- #
LEXICON: dict[str, list[str]] = {
    "python": ["python", "پایتون", "python developer", "python ile"],
    "django": ["django", "جنگو", "flask", "fastapi", "lumen"],
    "javascript": ["javascript", "js", "جاوا اسکریپت", "ecmascript", "typescript", "ts"],
    "react": ["react", "react.js", "reactjs", "ریاکت", "next.js", "nextjs"],
    "vue": ["vue", "vue.js", "nuxt"],
    "angular": ["angular", "angularjs"],
    "nodejs": ["node", "node.js", "nodejs", "express.js", "nestjs"],
    "php": ["php", "laravel", "symfony", "ووردپرس", "wordpress", "woocommerce"],
    "java": ["java", "spring", "spring boot", "جافا", "kotlin", "android"],
    "swift": ["swift", "ios", "xcode"],
    "csharp": ["c#", "csharp", ".net", "asp.net", "dotnet", "maui"],
    "sql": ["sql", "t-sql", "plsql", "کوئری", "query", "mysql", "mariadb", "postgresql", "postgres"],
    "nosql": ["mongodb", "redis", "cassandra", "dynamodb", "nosql", "elasticsearch", "opensearch"],
    "django_rest": ["rest api", "restful", "rest servis", "rest service", "graphql", "swagger", "openapi"],
    "git": ["git", "github", "gitlab", "version control", "source control"],
    "docker": ["docker", "container", "compose", "podman"],
    "kubernetes": ["kubernetes", "k8s", "helm", "openshift"],
    "cicd": ["ci/cd", "ci cd", "jenkins", "github actions", "gitlab ci", "argocd"],
    "aws": ["aws", "ec2", "s3", "lambda", "azure", "gcp", "cloud", "ابر", "کلاد", "cloudflare"],
    "linux": ["linux", "ubuntu", "centos", "debian", "bash", "unix", "لینوکس"],
    "windows_server": ["windows server", "active directory", "gpo", "ads"],
    "network": ["network", "cisco", "mikrotik", "ccna", "ccnp", "firewall", "شبکه", "vlan", "dns"],
    "security": ["security", "cybersecurity", "pentest", "information security", "امنیت"],
    "power_bi": ["power bi", "powerbi", "tableau", "looker", "داشبورد"],
    "excel": ["excel", "microsoft office", "اکسل", "vba", "pivot table", "power query"],
    "data_analysis": ["data analysis", "data analyst", "تحلیل داده", "statistics", "spss", "r language", "pandas", "numpy"],
    "machine_learning": ["machine learning", "deep learning", "ai", "nlp", "yapay zeka", "هوش مصنوعی",
                         "tensorflow", "pytorch", "llm", "computer vision", "opencv"],
    "etl": ["etl", "airflow", "dbt", "data pipeline", "databricks", "snowflake", "data warehouse", "anbar داده"],
    "frontend": ["frontend", "front-end", "ui implementation", "فرانت", "کاربری رابط", "html", "css", "tailwind", "sass"],
    "backend": ["backend", "back-end", "api design", "بک اند", "میکروسرویس", "microservices"],
    "mobile": ["mobile", "android", "ios", "flutter", "react native", "موبایل", "اپلیکیشن"],
    "qa": ["qa", "test", "testing", "qael", "selenium", "cypress", "playwright", "تست نرم افزار", "کیفیت"],
    "product": ["product manager", "product owner", "مدیر محصول", "scrum", "agile", "kanban", "jira"],
    "ux": ["ux", "ui", "figma", "adobe xd", "sketch", "تجربه کاربری", "طراح رابط کاربری", "photoshop", "illustrator"],
    "seo": ["seo", "content marketing", "دیجیتال مارکتینگ", "digital marketing", "google ads", "meta ads", "اینستاگرام"],
    "social_media": ["social media", "ادمین اینستاگرام", "instagram", "telegram admin", "community management"],
    "sales": ["sales", "فروش", "بازاریابی", "vending", "business development", "satış", "pazarlama", "cold call"],
    "accounting": ["accounting", "حسابداری", "muhasebe", "financial", "مالی", "vergi", "tax", "auditing", "mali müşavir"],
    "hr": ["hr", "human resources", "منابع انسانی", "İK", "insan kaynakları", "recruitment", "استخدام", "kariyer danışmanı"],
    "customer_service": ["customer service", "پشتیبانی", "call center", "çağrı merkezi", "مشتری", "تیکت", "support"],
    "teaching": ["teacher", "مدرس", "آموزش", "öğretmen", "education", "tutor", "english teacher", "itep"],
    "translation": ["translation", "ترجمه", "tercüme", "interpreter", "مترجم", "subtitle"],
    "content": ["content", "تولید محتوا", "content writer", "kopya", "copywriting", "redaksiyon", "ویراستاری"],
    "graphic_design": ["graphic", "طراحی", "design", "logo", "brand", "CorelDRAW", "inDesign", "after effects", "premiere", "ویدیو ادیت", "edit"],
    "nursing": ["nurse", "پرستار", "hemşire", "healthcare", "بهداشت", "hospital"],
    "welding": ["welding", "kaynakçı", "kaynak ustası", "kaynak dikişi", "jarko", "arc welding", "برقکاری", "جوش", "جوشکاری", "سازه فلزی", "miggaz", "tig kay"],
    "cnc": ["cnc", "cnc tezgah", "lathe operatörü", "tornacı", "freze tezgahı", "milling", "تراشکاری", "سنبه‌زنی", "ahşap cnc"],
    "forklift": ["forklift", "لیفتراک", "forvlift"],
    "driver": ["driver", "ranande", "راننده", "şoför", "araç kullanma", "ehliyet", "گواهینامه", "src belgesi"],
    "delivery": ["delivery", "پیک", "moto", "پیک موتوری", "kurye", "distribution", "trear"],
    "cleaning": ["cleaning", "تاسیزات", "housekeeping", "temizlik", "نیرو خدماتی"],
    "security_guard": ["guard", "نگهبان", "güvenlik görevlisi", "حراست", "پاسبان", "özel güvenlik"],
    "electrician": ["electrician", "برقکار", "elektrik teknisyeni", "الکتریک", "تأسیسات برقی"],
    "plumbing": ["plumbing", "لوله‌کشی", "tesisat", "taasisat", "sanitary"],
    "warehouse": ["warehouse", "انبار", "depo", "anbar", "stock", "inventory", "مخزن"],
    "logistics": ["logistics", "لجستیک", "lojistik", "supply chain", "زنجیره تامین", "gumruk", "customs"],
    "construction": ["construction", "ساختمان", "inşaat", "عمران", "civil", "memar", "architect", "معمار", "metraj", "ihale"],
    "mechatronics": ["mechatronic", "مکاترونیک", "otomasyon", "plc", "automation", "اتوماسیون", "scada"],
    "project_mgmt": ["project management", "مدیریت پروژه", "proje yönetimi", "pmp", "pmr", "msp", "supervision", "نظارت"],
    "procurement": ["procurement", "تدارکات", "satın alma", "purchasing", "خرید"],
    "legal": ["law", "حقوق", "hukuk", "avukat", "وکیل", "legal", "contract"],
    "marketing": ["marketing", "بازاریابی", "pazarlama", "brand", "cgm"],
    "finance": ["finance", "مالی", "finans", "treasury", "خزانه", "investment", "سرمایه"],
    "language_en": ["english", "زبان انگلیسی", "ingilizce", "IELTS", "TOEFL"],
    "language_tr": ["turkish", "ترکی استانبولی", "türkçe", "istambul turkcesi"],
}

# Occupation families: used for coarse recall + "similar jobs" grouping.
FAMILIES: dict[str, list[str]] = {
    "software": ["developer", "programmer", "mühendis yazılım", "برنامه نویس", "software", "yazilim", "engineer computer"],
    "data_ai": ["data", "analyst", "تحلیلگر", "veri", "ai", "machine learning", "bilim"],
    "design": ["designer", "طراح", "tasarımcı", "grafik", "graphic", "ux", "ui"],
    "marketing_sales": ["marketing", "pazarlama", "sales", "satış", "بازاریاب", "فروشنده", "dijital"],
    "finance_admin": ["muhasebe", "accounting", "حسابدار", "finans", "مالی", "admin", "idari", "اداری", "sekreter", "منشی"],
    "hr_recruiting": ["İK", "insan kaynakları", "منابع انسانی", "recruitment", "hr"],
    "customer": ["çağrı", "call center", "müşteri", "پشتیبان", "support", "destek"],
    "teaching_lang": ["teacher", "öğretmen", "مدرس", "آموزگار", "english teacher", "itep", "yds", "kpds"],
    "skilled_trade": ["teknisyen", "technician", "ustası", "usta", "elektrik", "elektrikçi", "cnc", "kaynak",
                       "welder", "tamirci", "montaj", "bakım", "ariza",
                       "برقکار", "تعمیرات", "تعمیرکار", "مونتاژ", "نصب", "مکانیک", "جوش", "جوشکار",
                       "لوله‌کش", "لوله کش", "نجار", "نقاشی ساختمان", "کنتور", "پلیس?"],
    "industry": ["uretim", "production", "تولید", "fabrika", "کارخانه", "imalat", "kalite", "quality", "کنترل کیفیت"],
    "construction": ["inşaat", "construction", "santiye", "mimar", "kalfa", "istan", "demirci", "kalipçi",
                      "ساختمان", "شانتی", "بنایی", "نقشه‌بردار", "معمار", "سازه", "عمران", "راه", "پل"],
    "logistics": ["lojistik", "depo", "warehouse", "kargo", "sevk", "iradiye", "tuketim", "forklift",
                   "انبار", "باربری", "حمل", "حمل‌ونقل", "جابه‌جایی", "لیفتراک", "پخش", "راننده", "توزیع"],
    "healthcare": ["hemşire", "nurse", "sağlık", "درمان", "health", "eczac", "داروساز"],
    "service": ["garson", "komis", "asci", "temizlik", "catı", "otel", "reception", "market", "kasa",
                 "آشپز", "کمک آشپز", "پیشخدمت", "گارسون", "نظافت", "تمیزکاری", "خدمات", "پذیرش",
                 "فروشگاه", "صندوق", "اتاق‌خواب", "housekeeping", "cleaning"],
    "management": ["manager", "müdür", "مدیر", "yönetici", "supervisor", "سرپرست", "başkan", "ceo", "cto"],
}

CITIES_TR = ["istanbul", "ankara", "izmir", "bursa", "antalya", "adana", "kocaeli", "gaziantep",
             "konya", "mersin", "diyarbakir", "eskisehir", "samsun", "denizli", "trakya", "tekirdag"]
CITIES_IR = ["tehran", "تهران", "mashhad", "مشهد", "isfahan", "اصفهان", "shiraz", "شیراز",
             "tabriz", "تبریز", "karaj", "کرج", "ahvaz", "اهواز", "qom", "قم", "rasht", "رشت",
             "kermanshah", "کرمانشاه", "urmia", "ارومیه", "arak", "اراک", "yazd", "یزد"]

SENIORITY = {
    "intern": ["intern", "stajyer", "کارآموز", "trainee", "staj"],
    "junior": ["junior", "entry level", "associate", "junior", "کم تجربه", "new grad", "yeni mezun", "0-2"],
    "mid": ["mid", "ortа", "mid-level", "deneyimli", "2-5", "3-5"],
    "senior": ["senior", "kıdemli", "ارشد", "senior", "5+", "7+", "uzman"],
    "lead": ["lead", "principal", "staff", "سرگروه", "team lead", "başuzman"],
    "manager": ["manager", "müdür", "مدیر", "head", "director", "başkan", "yönetici", "سرپرست"],
}

REMOTE_WORDS = ["remote", "uzaktan", "دورکاری", "evden", "work from home", "wfh", "hybrid", "yari zamanli evden", "نیمه وقت"]
ONSITE_WORDS = ["onsite", "yerinde", "hazır", "ofiste"]

# Salary: TL monthly gross is the TR convention; Toman/Rial monthly is the IR one.
_MULTIPLIERS = {"bin": 1e3, "هزار": 1e3, "hazari": 1e3, "thousand": 1e3, "milyon": 1e6,
                "million": 1e6, "میلیون": 1e6, "milyar": 1e9, "میلیارد": 1e9, "billion": 1e9}
_CURRENCIES = {"tl": "TRY", "try": "TRY", "lira": "TRY", "toman": "TOMAN", "تومان": "TOMAN",
               "tomani": "TOMAN", "rial": "IRR", "ریال": "IRR", "irr": "IRR", "usd": "USD",
               "$": "USD", "usd$": "USD", "eur": "EUR", "euro": "EUR", "€": "EUR"}
_NUM = r"(\d[\d]*(?:[.,]\d{3})*(?:[.,]\d{1,2})?)"


@dataclass
class Salary:
    monthly_min: float | None = None
    monthly_max: float | None = None
    currency: str | None = None

    @property
    def monthly_usd(self) -> tuple[float | None, float | None]:
        from .config import FX_TO_USD
        if not self.currency or self.currency.upper() not in FX_TO_USD:
            return None, None
        k = FX_TO_USD[self.currency.upper()]
        a = self.monthly_min * k if self.monthly_min else None
        b = self.monthly_max * k if self.monthly_max else None
        return a, b


def _to_float(raw: str) -> float | None:
    d = raw.replace(",", "")
    # "45.000" is a thousands separator in tr/fa, "1.800,50" -> keep it simple: drop dots
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", d):
        d = d.replace(".", "")
    else:
        d = re.sub(r"[.,](?=\d{1,2}$)", "", d)
        d = d.replace(".", "") if re.fullmatch(r"\d+(\.\d{3})+", d) else d
    try:
        v = float(d)
    except ValueError:
        return None
    return v


def _mult_near(text: str) -> float:
    for w, m in _MULTIPLIERS.items():
        if re.search(rf"\b{re.escape(w)}\b", text):
            return m
    return 1.0


def parse_salary(text: str | None) -> Salary | None:
    """Parses "45.000 - 60.000 TL", "Maaş 42.235 TL + 3000 TL yemek", "۱۵ میلیون تومان",
    "$1,800 /ay". Only numbers *adjacent* to a currency token are considered, so an ad's
    "İlan No: 4762405" can never become the salary again."""
    if not text:
        return None
    t = norm_text(text)
    annual = bool(re.search(r"(yıllık|yillik|annual|senelik|saatte|hourly|saatlik)", t))
    word = r"[a-zçğıöşâûé\u0600-\u06FF]{1,12}"
    sep = r"(?:[-–—:/]|\bto\b|\bile\b|\bta\b|\bile\b)?"
    for tok, cur in _CURRENCIES.items():
        lo = hi = None
        # "45.000 - 60.000 TL", "8 تا 12 میلیون تومان", "3 bin TL"  (perks like "+3000 TL yemek"
        # are deliberately NOT folded into the range: only the first amount phrase counts)
        pat = rf"{_NUM}(?:\s*{word})?\s*{sep}\s*{_NUM}?(?:\s*{word})?\s*{re.escape(tok)}"
        m = re.search(pat, t)
        if m:
            g = [x for x in re.findall(_NUM, m.group(0))]
            mul = _mult_near(m.group(0))
            vals = [(_to_float(x) or 0) * mul for x in g] or None
            if vals:
                lo, hi = min(vals), max(vals)
        if lo is None:
            m2 = re.search(rf"{re.escape(tok)}\s*{_NUM}", t)              # "$1,800" / "TL 45.000"
            if m2:
                v = _to_float(m2.group(1))
                lo = hi = v
        if lo is None:
            continue
        if cur == "IRR":
            lo, hi, cur = lo / 10, hi / 10, "TOMAN"
        if annual and (lo > 50_000 or cur in ("USD", "EUR")):
            lo, hi = lo / 12, hi / 12
        if cur == "TRY" and (lo < 5_000 or lo > 1_500_000):
            continue        # implausible monthly gross in 2026 Turkey -> treat as unknown
        if cur in ("USD", "EUR") and (lo < 30 or lo > 60_000):
            continue
        if cur in ("TOMAN",) and lo < 100_000:
            continue
        return Salary(monthly_min=lo, monthly_max=hi if hi != lo else None, currency=cur)
    return None


def detect_skills(text: str | None, *, limit: int = 40) -> tuple[list[str], list[str]]:
    """Return (canonical skills, must_have phrases)."""
    t = norm_text(text)
    if not t:
        return [], []
    hits: list[str] = []
    for canon, aliases in LEXICON.items():
        for a in aliases:
            na = norm_text(a)
            if not na:
                continue
            if len(na) <= 3:
                if re.search(rf"(^|\s){re.escape(na)}($|\s)", t):
                    hits.append(canon)
                    break
            elif na in t:
                hits.append(canon)
                break
    seen: list[str] = []
    for h in hits:
        if h not in seen:
            seen.append(h)
    must: list[str] = []
    for m in re.finditer(r"(?:باید|الزامی|required|gereken|aranan|şart|حداقل)\s*[:\-]?\s*([^.\n؛;]{4,90})",
                         norm_text(text or ""), re.I):
        phrase = m.group(1).strip()
        if len(phrase.split()) <= 10:
            must.append(phrase)
    return seen[:limit], must[:6]


def detect_family(text: str | None) -> str | None:
    t = norm_text(text)
    best, best_len = None, 0
    for fam, keys in FAMILIES.items():
        for k in keys:
            nk = norm_text(k)
            if nk and nk in t and len(nk) > best_len:
                best, best_len = fam, len(nk)
    return best


def detect_seniority(text: str | None) -> str | None:
    t = norm_text(text)
    years = [int(x) for x in re.findall(r"(\d{1,2})\s*(?:yıl|سال|years?|senesi)\s*(?:deneyim|تجربه|experience)?", t)]
    for lvl, keys in SENIORITY.items():
        if any(norm_text(k) in t for k in keys):
            return lvl
    if years:
        y = max(years)
        return "junior" if y <= 2 else "mid" if y <= 5 else "senior" if y <= 9 else "lead"
    return None


def detect_city(text: str | None, country: str) -> str | None:
    t = norm_text(text)
    pool = CITIES_TR if country == "TR" else CITIES_IR
    for c in pool:
        if c in t:
            return c.title()
    return None


def detect_remote(text: str | None) -> bool | None:
    t = norm_text(text)
    if not t:
        return None
    if any(w in t for w in map(norm_text, REMOTE_WORDS)):
        return True
    if any(w in t for w in map(norm_text, ONSITE_WORDS)):
        return False
    return None


def detect_lang_req(text: str | None) -> dict[str, int]:
    """Which languages the ad demands, with a crude level guess.

    Turkish fluency is the single biggest blocker for an Iranian candidate in an
    on-site TR job - it must be a hard gate, not a soft score.
    """
    t = norm_text(text)
    out: dict[str, int] = {}
    if not t:
        return out
    low_words = r"(başlangıç|elementary|beginner|a1|a2|temel|آشنایی|متوسط|intermediate|b1)"
    high_words = r"(ileri|iyi derecede|advanced|fluent|c1|c2|hakim|good level|سلطه|پیشرفته)"
    for code, keys in (("tr", ["türkçe", "turkish", "استانبولی"]),
                       ("en", ["english", "ingilizce", "انگلیسی"]),
                       ("de", ["german", "almanc", "آلمانی"]),
                       ("ar", ["arabic", "arapça", "عربی"]),
                       ("ru", ["russian", "rusça", "روسی"]),
                       ("fa", ["persian", "farsça", "فارسی"])):
        for k in keys:
            nk = norm_text(k)
            i = t.find(nk) if nk else -1
            if i < 0:
                continue
            win = t[max(0, i - 60): i + len(nk) + 60]
            lvl = 4
            if re.search(low_words, win):
                lvl = 2
            if re.search(high_words, win):
                lvl = 5
            out[code] = max(out.get(code, 0), lvl)
            break
    return out


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
