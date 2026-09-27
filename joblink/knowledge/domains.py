"""12 حوزه دانش برای JobLink - هر حوزه = یک فصل حقوقی/اخلاقی/مالی/دانشگاهی"""
from dataclasses import dataclass
from typing import List

@dataclass
class Domain:
    id: str
    title_fa: str
    title_en: str
    slug: str
    description_fa: str
    description_en: str
    why_needed: str
    keywords: List[str]
    risk_level: str  # low/medium/high
    relevant_laws: List[str]

DOMAINS = [
    Domain(
        id="d01",
        slug="tr-work-permit",
        title_fa="قوانین مهاجرت کاری ایرانیان به ترکیه - اجازه کار",
        title_en="Turkish Work Permit Law for Iranians",
        description_fa="قانون نیروی کار بین‌المللی 6735 ترکیه، انواع اجازه کار (موقت، نامحدود، مستقل، تورکواز کارت)، معافیت‌ها، شرایط 5 ترک برای هر خارجی، حداقل حقوق، پروسه e-izin، و ویزای فناوری 2024.",
        description_en="Law No.6735, work permit types, 5:1 rule, salary thresholds, e-permit process, Tech Visa 2024.",
        why_needed="بدون درک Çalışma izni، هر تطبیق شغلی حضوری غیرقانونی و قابل ابطال است؛ موتور مچینگ باید شغل‌های حضوری را فقط با flag open_to_relocate نشان دهد.",
        keywords=["Çalışma izni", "Law 6735", "Turkuaz Kart", "Tech Visa Turkey", "e-izin", "5 Turk rule"],
        risk_level="high",
        relevant_laws=["Law No.6735", "Regulation 48/2024", "Law 6458 Foreigners", "Tech Visa 2024"]
    ),
    Domain(
        id="d02",
        slug="kvkk-gdpr",
        title_fa="حفاظت از داده شخصی - KVKK ترکیه و GDPR اروپا",
        title_en="KVKK 6698 + GDPR",
        description_fa="اصول KVKK ماده 4، رضایت صریح، داده حساس، VERBİS، حق فراموشی، انتقال فرامرزی، جریمه‌ها، تفاوت KVKK با GDPR، پیاده‌سازی در ربات تلگرام.",
        description_en="KVKK principles, explicit consent, sensitive data, VERBIS, cross-border, fines, vs GDPR.",
        why_needed="JobLink داده رزومه پردازش می‌کند؛ اگر consent_token نداشته باشد باید ConsentError بدهد. این خط قرمز پروژه است.",
        keywords=["KVKK", "Law 6698", "VERBIS", "explicit consent", "GDPR art 17", "cross-border transfer"],
        risk_level="high",
        relevant_laws=["KVKK 6698", "Turkish Penal 135/136", "GDPR", "EU AI Act Art 50"]
    ),
    Domain(
        id="d03",
        slug="iran-labor-law",
        title_fa="قانون کار ایران و مقررات کاریابی‌ها",
        title_en="Iran Labor Code & Employment Agencies",
        description_fa="قانون کار 1369، مواد 120-129 اشتغال اتباع بیگانه، آیین‌نامه کاریابی‌های داخلی و خارجی، مجوز وزارت کار، ممنوعیت دریافت وجه از کارجو.",
        description_en="Iran Labor Code 1990, foreign employment articles, recruitment agency regulations.",
        why_needed="برای جذب کارجو از دیوار/جابینجا فقط می‌توان لینک opt-in گذاشت؛ اسکرپ رزومه هم غیرفنی هم جرم است.",
        keywords=["قانون کار 1369", "ماده 120", "کاریابی خارجی", "وزارت تعاون", "حق‌الزحمه کاریابی"],
        risk_level="high",
        relevant_laws=["Iran Labor Code 203 articles", "Regulation of Private Employment Agencies 1387"]
    ),
    Domain(
        id="d04",
        slug="ai-ethics-hiring",
        title_fa="اخلاق هوش مصنوعی در استخدام - عدالت و سوگیری",
        title_en="AI Ethics in Hiring - Fairness & Bias",
        description_fa="انواع fairness (demographic parity, equal opportunity), proxy reduction, audit, explainability, ممنوعیت تحلیل چهره در EU AI Act, مسئولیت انسانی.",
        description_en="Fairness definitions, bias sources, audits, explainability, face analysis ban.",
        why_needed="موتور مچینگ نباید جنسیت/قومیت را وزن دهد؛ باید دلیل مچ را توضیح دهد و gap را بگوید نه اینکه رد پنهان کند.",
        keywords=["algorithmic fairness", "bias audit", "proxy reduction", "EU AI Act", "explainable AI", "80% rule"],
        risk_level="medium",
        relevant_laws=["EU AI Act 2024", "EEOC Guidance AI", "GDPR Art 22"]
    ),
    Domain(
        id="d05",
        slug="platform-economy",
        title_fa="مدل کسب‌وکار پلتفرمی اوبر/اسنپ برای بازار کار",
        title_en="Uber/Snapp Platform Business Model",
        description_fa="دو طرفه بودن بازار، network effects, liquidity, dispatch vs search, take-rate, disintermediation, قیمت‌گذاری پویا، استراتژی دوگانه.",
        description_en="Two-sided marketplace, liquidity, dispatch, take-rate, disintermediation.",
        why_needed="JobLink اوبر برای کار است؛ باید از روز اول بفهمد liquidity چیست و چرا با عمود آبی شروع می‌کند.",
        keywords=["two-sided marketplace", "network effects", "liquidity", "dispatch", "take-rate", "Snapp"],
        risk_level="low",
        relevant_laws=["Platform-to-Business Regulation EU", "Turkish Competition Law"]
    ),
    Domain(
        id="d06",
        slug="finance-sanctions-tax",
        title_fa="مالی، پرداخت، مالیات و تحریم‌ها",
        title_en="Finance, Payments, Tax & Sanctions",
        description_fa="تحریم OFAC علیه ایران، ممنوعیت حواله مستقیم، U-Turn، هالک‌بانک، استفاده از ترکیه/امارات به عنوان واسط، رمز ارز ممنوع، مالیات ترکیه، قرارداد کار.",
        description_en="OFAC Iran sanctions, Halkbank, crypto ban, tax in Turkey, payment via third country.",
        why_needed="اگر پرداخت حقوق کارجو ایرانی مقیم ایران از ترکیه را حواله‌ای یا کریپتو حل کنیم، هم ما هم کارفرما تحت پیگرد ثانویه قرار می‌گیرد.",
        keywords=["OFAC", "ITSR 560", "Halkbank", "hawala", "crypto ban", "Turkish tax"],
        risk_level="high",
        relevant_laws=["ITSR 31 CFR 560", "CAATSA", "Turkish Tax Law", "Law 6735 salary thresholds"]
    ),
    Domain(
        id="d07",
        slug="blue-collar-safety",
        title_fa="امنیت شغلی کارگران یقه‌آبی و استانداردهای ILO",
        title_en="Blue-Collar Safety & ILO Standards",
        description_fa="ILO C155, قانون کار ترکیه 4857 ساعات کار، اضافه‌کاری، بیمه SGK، حوادث کار، کارهای ممنوع برای اتباع.",
        description_en="ILO conventions, Turkish Labor Law 4857, SGK, occupational safety.",
        why_needed="عمود آبی JobLink باید آگهی‌های بدون بیمه یا زیر حداقل دستمزد 26,005 TL را flag کند.",
        keywords=["ILO", "Law 4857", "SGK", "minimum wage", "occupational safety", "blue-collar"],
        risk_level="medium",
        relevant_laws=["Turkish Labor Law 4857", "ILO C155", "SGK Law 5510"]
    ),
    Domain(
        id="d08",
        slug="skill-taxonomy",
        title_fa="مهارت‌سنجی و طبقه‌بندی مشاغل - ESCO/O*NET",
        title_en="Skill Taxonomy ESCO O*NET",
        description_fa="ESCO 13,890 مهارت، O*NET 1,016 شغل، crosswalk، استخراج مهارت با LLM، CareerBERT، نرمال‌سازی فارسی/ترکی/انگلیسی.",
        description_en="ESCO, O*NET, crosswalk, skill extraction, multilingual normalization.",
        why_needed="LEXICON ما 70 مهارت دارد؛ ESCO مبنای 13k مهارت است تا جوشکار به برنامه‌نویس مچ نشود.",
        keywords=["ESCO", "O*NET", "skill extraction", "CareerBERT", "taxonomy", "normalization"],
        risk_level="low",
        relevant_laws=["EU ESCO Regulation", "EURES"]
    ),
    Domain(
        id="d09",
        slug="telegram-bot-law",
        title_fa="قوانین تلگرام، ربات، رضایت‌نامه و حریم خصوصی",
        title_en="Telegram Bot Law, Consent & Privacy",
        description_fa="Telegram Bot API، مسئول کنترل داده بودن ادمین کانال، DPA، حق حذف، لاگ رضایت، EU AI Act شفافیت بات از اوت 2026.",
        description_en="Telegram Bot API, controller role, DPA, deletion, consent log, AI Act transparency.",
        why_needed="ربات تلگرام تنها کانال جذب ماست؛ باید /katil و /hayir را لاگ کند وگرنه KVKK نقض می‌شود.",
        keywords=["Telegram Bot", "data controller", "consent log", "GDPR", "AI Act Art 50", "purge"],
        risk_level="medium",
        relevant_laws=["Telegram ToS", "KVKK", "GDPR", "EU AI Act Art 50"]
    ),
    Domain(
        id="d10",
        slug="nlp-matching",
        title_fa="آموزش مدل تطبیق شغل با NLP چندزبانه - Embeddings و RAG",
        title_en="Multilingual Job Matching NLP - Embeddings RAG",
        description_fa="multilingual-e5-large, jina-embeddings-v3, Qwen3-Embedding, instruction tuning، ساخت golden dataset، ارزیابی Recall@k، fine-tune برای فارسی-ترکی.",
        description_en="e5, jina v3, Qwen3, instruction, golden dataset, Recall@k, fa-tr fine-tune.",
        why_needed="موتور فعلی BM25 است؛ اگر HF token درست شود، embeddings باید فارسی «جوشکار» را به ترکی «kaynakçı» نزدیک کند نه به «kaynak kodu».",
        keywords=["multilingual-e5", "jina-embeddings", "Qwen3-Embedding", "RAG", "fine-tune", "Recall@k"],
        risk_level="low",
        relevant_laws=["HF Model Licenses", "EU AI Act transparency"]
    ),
    Domain(
        id="d11",
        slug="migration-research",
        title_fa="تحقیقات دانشگاهی مهاجرت کاری ایرانیان",
        title_en="Academic Research on Iranian Labor Migration",
        description_fa="brain drain، مهاجرت یقه‌آبی، ترکیه به عنوان هاب، داده TÜİK، تحقیقات دانشگاهی ایران-ترکیه، push/pull factors.",
        description_en="Brain drain, blue-collar migration, Turkey hub, TÜİK data, push/pull.",
        why_needed="برای pitch به سرمایه‌گذار و برای فهم اینکه چرا اصفهان به استانبول می‌رود نه برعکس.",
        keywords=["brain drain", "TÜİK", "migration", "push pull", "Iran Turkey", "diaspora"],
        risk_level="low",
        relevant_laws=["Turkish Migration Law 6458", "Iranian Exit Law"]
    ),
    Domain(
        id="d12",
        slug="startup-tr-iranian",
        title_fa="راه‌اندازی استارتاپ در ترکیه برای ایرانیان - شرکت، اقامت، مجوز",
        title_en="Starting Startup in Turkey for Iranians",
        description_fa="انواع شرکت (Ltd, A.Ş)، هزینه، تکنوپارک، معافیت مالیاتی، Tech Visa، اقامت از طریق شرکت، حساب بانکی، VERBİS ثبت.",
        description_en="Company types, cost, technopark, tax exemption, Tech Visa, residence via company.",
        why_needed="JobLink خودش باید در ترکیه ثبت شود؛ این دانش هم برای ما هم برای کارجویان کارآفرین است.",
        keywords=["Ltd Şti", "Teknopark", "Tech Visa", "residence permit", "bank account", "VERBIS"],
        risk_level="medium",
        relevant_laws=["Turkish Commercial Code 6102", "Tech Visa 2024", "Tax Law 4691 Technopark"]
    ),
]
