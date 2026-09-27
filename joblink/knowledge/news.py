"""10 news articles for JobLink - Iran-Turkey jobs, work permit, cleaning, minimum wage"""

from dataclasses import dataclass
from typing import List

@dataclass
class NewsItem:
    id: str
    title_fa: str
    title_tr: str
    title_en: str
    date: str
    source: str
    url: str
    summary_fa: str
    summary_tr: str
    category: str  # work-permit, cleaning, minimum-wage, iranian-migration, etc.
    tags: List[str]
    importance: str  # high, medium, low

NEWS_10 = [
    NewsItem(
        id="news_01",
        title_fa="حداقل دستمزد ترکیه 2026: 33,030 لیر ناخالص — 28,075 خالص",
        title_tr="Türkiye Asgari Ücret 2026: 33,030 TL Brüt — 28,075 TL Net",
        title_en="Turkey Minimum Wage 2026: 33,030 TRY Gross",
        date="2026-01-01",
        source="CottGroup + Fragomen",
        url="https://www.cottgroup.com/en/blog/work-life/item/what-is-minimum-wage-how-much-is-the-minimum-wage-in-turkiye-2026",
        summary_fa="از 1 ژانویه 2026 حداقل دستمزد ناخالص 33,030 لیر، خالص 28,075 لیر شد (قبل 2025: 26,005 لیر). برای اجازه کار خارجی: کارگر خانگی و خدماتی حداقل 1x (33,030)، کار نیاز به تخصص 2x (66,060)، مدیر 3x (99,090)، مهندس 4x (132,120)، مدیر ارشد 5x (165,150). حقوق باید در تمام مدت اجازه کار تضمین شود — مزایا حساب نمی‌شود. برای نظافت و بسته‌بندی: حداقل 33,030 لیر.",
        summary_tr="1 Ocak 2026'dan itibaren brüt asgari ücret 33,030 TL, net 28,075 TL oldu (2025: 26,005 TL). Yabancı çalışma izni için: ev hizmetleri ve diğer 1x (33,030), uzmanlık 2x (66,060), yönetici 3x (99,090), mühendis 4x (132,120), üst düzey 5x (165,150). Maaş izin süresi boyunca garanti edilmeli. Temizlik/paketleme için en az 33,030 TL.",
        category="minimum-wage",
        tags=["asgari ücret", "minimum wage", "2026", "çalışma izni", "temizlik"],
        importance="high"
    ),
    NewsItem(
        id="news_02",
        title_fa="ایرانیان در ترکیه: 100,000 نفر در 2025 — اقامت کوتاه‌مدت 10 ساله",
        title_tr="Türkiye'de İranlılar: 2025'te 100,000 kişi — 10 yıldır kısa dönem ikamet",
        title_en="Iranians in Turkey: 100,000 in 2025 — 10 years on short-term permits",
        date="2026-04-22",
        source="KRMG + Washington Times + TÜİK",
        url="https://krmg.com/2026/04/22/iranians-have-long-sought-work-and-relative-stability-in-turkey-the-war-could-force-some-to-return/",
        summary_fa="حدود 100,000 ایرانی در 2025 در ترکیه زندگی می‌کنند (TÜİK). 89,000 نفر از شروع جنگ وارد، 72,000 خارج شدند (UNHCR). اکثرا با اقامت توریستی 6 ماه تا 2 سال تمدید می‌کنند — بعضی 10 سال همینطور. یک زن 42 ساله با ویزای دانشجویی صبح کلاس، تا 3 صبح کار خدماتی — اتاق مشترک با 6 نفر. گرفتن حمایت بین‌المللی سخت است — سیستم اقامت کوتاه‌مدت را تشویق می‌کند. جنگ و تحریم و قطعی اینترنت انتقال پول را سخت کرده.",
        summary_tr="TÜİK'e göre 2025'te Türkiye'de yaklaşık 100,000 İranlı yaşıyor. Savaşın başından beri 89,000 giriş, 72,000 çıkış (UNHCR). Çoğu 6 ay-2 yıl turistik ikamet uzatıyor — bazıları 10 yıldır böyle. 42 yaşında bir kadın öğrenci vizesiyle sabah ders, 03:00'e kadar hizmet işleri — 6 kişiyle oda paylaşımı. Uluslararası koruma almak zor. Savaş ve yaptırımlar para transferini zorlaştırıyor.",
        category="iranian-migration",
        tags=["iranian", "ikamet", "göç", "savaş", "TÜİK"],
        importance="high"
    ),
    NewsItem(
        id="news_03",
        title_fa="اجازه کار ترکیه برای ایرانیان: 90 روز بدون ویزا ولی بدون حق کار — کارفرما باید درخواست دهد",
        title_tr="İranlılar için Türkiye Çalışma İzni: 90 gün vizesiz ama çalışma yasak — işveren başvurmalı",
        title_en="Turkey Work Permit for Iranians: 90 days visa-free but no work — employer must apply",
        date="2025-08-18",
        source="inforeigner.com + istaproperty.com",
        url="https://inforeigner.com/i/turkey-work-permit-for-iranian-citizens/",
        summary_fa="ایرانیان 90 روز بدون ویزا می‌توانند بمانند ولی حق کار ندارند — کار = غیرقانونی، دیپورت + ممنوعیت دائم. اجازه کار را وزارت کار می‌دهد و جایگزین اقامت هم هست. دو روش: داخلی (با اقامت حداقل 6 ماه) و خارجی (از طریق سفارت ترکیه در ایران). اجازه کار وابسته: کارفرما باید درخواست دهد نه کارجو — با قرارداد + 16 رقم reference number. مدارک کارفرما: روزنامه تجاری، ترازنامه، SGK no، وکالتنامه. مدارک کارجو: پاسپورت ترجمه، دیپلم ترجمه، عکس. همه آنلاین با امضای الکترونیک. تمدید قبل انقضا.",
        summary_tr="İranlılar 90 gün vizesiz kalabilir ama çalışamaz — çalışmak yasadışı, deport + kalıcı yasak. Çalışma izni Çalışma Bakanlığı verir ve ikamet yerine geçer. İki yol: yurt içi (en az 6 ay ikametle) ve yurt dışı (İran'daki Türk temsilcilikleri). Bağımlı izin: işveren başvurmalı, yabancı değil — sözleşme + 16 haneli referans no. İşveren belgeleri: ticaret sicil, bilanço, SGK no, vekaletname. Yabancı belgeleri: pasaport tercüme, diploma tercüme, foto. Hepsi e-imza ile online. Uzatma süresi dolmadan.",
        category="work-permit",
        tags=["çalışma izni", "90 gün", "e-izin", "işveren", "referans no"],
        importance="high"
    ),
    NewsItem(
        id="news_04",
        title_fa="حقوق نظافتچی در استانبول 2025: 20,000 تا 45,000 لیر — میانه 33,000",
        title_tr="İstanbul'da Temizlikçi Maaşı 2025: 20,000-45,000 TL — Medyan 33,000",
        title_en="Cleaner Salary Istanbul 2025: 20K-45K TRY — Median 33K",
        date="2025-05-06",
        source="Glassdoor",
        url="https://www.glassdoor.com/Salaries/istanbul-turkey-cleaner-salary-SRCH_IL.0,15_IM1160_KO16,23.htm",
        summary_fa="متوسط حقوق نظافتچی در استانبول 32,500 لیر در سال یا 16 لیر در ساعت — 20% کمتر از میانگین ملی. رنج معمول 20,000 (25%) تا 45,000 (75%) در ماه. شرکت‌ها: Ülker 15K median، Midas 45K، Sabancı University 22K. برای کار یک‌ماهه نظافت: 20K-33K منطقی — کمتر از 26,005 (2025) یا 33,030 (2026) مشکوک.",
        summary_tr="İstanbul'da temizlikçi ortalama maaşı yılda 32,500 TL veya saatte 16 TL — ulusal ortalamanın %20 altında. Tipik aralık ayda 20,000 (%25) - 45,000 (%75). Şirketler: Ülker 15K medyan, Midas 45K, Sabancı 22K. 1 aylık temizlik için 20K-33K mantıklı — 26,005 (2025) veya 33,030 (2026) altı şüpheli.",
        category="cleaning-jobs",
        tags=["temizlik", "maaş", "İstanbul", "Glassdoor", "asgari"],
        importance="medium"
    ),
    NewsItem(
        id="news_05",
        title_fa="آگهی‌های نظافت منزل استانبول: 500 تا 1500 لیر هر بار — 35,000 تا 50,000 ماهانه",
        title_tr="İstanbul Ev Temizliği İlanları: 500-1500 TL/visit — 35,000-50,000 aylık",
        title_en="Istanbul Housekeeping Jobs: 500-1500 TL per visit — 35K-50K monthly",
        date="2025-12-24",
        source="bakicibuldum.com",
        url="https://bakicibuldum.com/en/housekeeping-jobs-istanbul/",
        summary_fa="سایت bakicibuldum.com آگهی‌های نظافت منزل استانبول: Bagcilar 500 TL هر بار، Sisli انگلیسی 1500 TL هر بار، Bagcilar 450 TL + 50,000 ماهانه، زندگی در منزل 500 TL + 35,000 ماهانه. وظایف: نظافت، لباسشویی، اتو، مرتب کردن کمد، آشپزی سبک. مناطق: Bagcilar, Sisli, Kadikoy, Kagithane, Buyukcekmece, Besiktas. برای یک‌ماهه: روزی 500-1500 TL — ماهانه 15,000-45,000 TL.",
        summary_tr="bakicibuldum.com İstanbul ev temizliği ilanları: Bağcılar 500 TL/visit, Şişli İngilizce 1500 TL/visit, Bağcılar 450 TL + 50,000 aylık, yatılı 500 TL + 35,000 aylık. Görevler: temizlik, çamaşır, ütü, dolap düzenleme, hafif yemek. Bölgeler: Bağcılar, Şişli, Kadıköy, Kağıthane, Büyükçekmece, Beşiktaş. 1 ay için günde 500-1500 TL — aylık 15,000-45,000 TL.",
        category="cleaning-jobs",
        tags=["ev temizliği", "housekeeping", "500 TL", "yatılı", "Şişli"],
        importance="medium"
    ),
    NewsItem(
        id="news_06",
        title_fa="آگهی‌های نظافت و خانه‌داری ترکیه: Maltepe، Florya، Altunizade، Üsküdar — روزانه و شبانه‌روزی",
        title_tr="Türkiye Ev İşleri İlanları: Maltepe, Florya, Altunizade, Üsküdar — gündüz ve yatılı",
        title_en="Turkey Housework Jobs: Maltepe, Florya, Altunizade, Üsküdar — daytime and live-in",
        date="2025-10-24",
        source="damladanismanlik.com",
        url="https://www.damladanismanlik.com/en/job-listings/housework-cleaning",
        summary_fa="سایت damladanismanlik.com: نظافت Maltepe Istanbul آنادولو شبانه‌روزی 24.10.2025، Florya روزانه 23.09.2025، Altunizade روزانه 06.05.2025، Üsküdar شبانه‌روزی 12.04.2025، Çekmeköy شبانه‌روزی 04.04.2025، Ümraniye روزانه 17.03.2025، Nişantaşı شبانه‌روزی 24.02.2025. نماینده Cansu. برای یک‌ماهه: روزانه (08:30-18:00) یا شبانه‌روزی (yatılı) — حقوق توافقی — مناطق بارانی Florya نزدیک دریا.",
        summary_tr="damladanismanlik.com: Maltepe İstanbul Anadolu yatılı 24.10.2025, Florya gündüz 23.09.2025, Altunizade gündüz 06.05.2025, Üsküdar yatılı 12.04.2025, Çekmeköy yatılı 04.04.2025, Ümraniye gündüz 17.03.2025, Nişantaşı yatılı 24.02.2025. Temsilci Cansu. 1 ay için gündüz (08:30-18:00) veya yatılı — maaş anlaşmalı — yağmurlu bölgeler Florya deniz yakını.",
        category="cleaning-jobs",
        tags=["ev işleri", "yatılı", "gündüz", "Florya", "Maltepe"],
        importance="medium"
    ),
    NewsItem(
        id="news_07",
        title_fa="78 کار نظافت در ترکیه — هتل‌های لوکس استانبول: Hilton، Raffles، Swissotel، Four Seasons",
        title_tr="Türkiye'de 78 Temizlik İşi — İstanbul Lüks Oteller: Hilton, Raffles, Swissotel, Four Seasons",
        title_en="78 Cleaning Jobs in Turkey — Luxury Hotels Istanbul: Hilton, Raffles, etc.",
        date="2026-05-11",
        source="Glassdoor",
        url="https://www.glassdoor.com/Job/turkey-cleaning-jobs-SRCH_IL.0,6_IN238_KO7,15.htm",
        summary_fa="78 کار نظافت در ترکیه — هتل‌های لوکس استانبول: Hilton Housekeeping Attendant Conrad Bosphorus، Raffles Housekeeping Room Attendant، Sheraton Levent Executive Housekeeper Kağıthane، Swissotel Bosphorus Lobby Hostess، The Hongkong and Shanghai Hotels Public Area Attendant، PepsiCo General Services Manager، Four Seasons F&B Server Assistant، Marriott F&B Support. حقوق هتل لوکس بیشتر — 30,000-45,000 TL — نیاز به انگلیسی + تجربه + اجازه کار.",
        summary_tr="Türkiye'de 78 temizlik işi — İstanbul lüks oteller: Hilton Housekeeping Attendant Conrad Bosphorus, Raffles Housekeeping Room Attendant, Sheraton Levent Executive Housekeeper Kağıthane, Swissotel Lobby Hostess, Hongkong Shanghai Public Area Attendant, PepsiCo General Services, Four Seasons F&B Server Assistant, Marriott F&B Support. Lüks otel maaşı daha yüksek — 30,000-45,000 TL — İngilizce + tecrübe + çalışma izni gerekli.",
        category="cleaning-jobs",
        tags=["otel", "Hilton", "Raffles", "luxury", "housekeeping"],
        importance="medium"
    ),
    NewsItem(
        id="news_08",
        title_fa="قانون جدید 10 اکتبر 2025: کار برای ترک‌تبارها — 10 شرط سخت — با تصمیم ریاست‌جمهوری",
        title_tr="10 Ekim 2025 Yeni Kanun: Türk Soylular için Çalışma — 10 Zor Şart — Cumhurbaşkanlığı Kararı",
        title_en="New Law Oct 10 2025: Work for Turkish Origin — 10 Hard Conditions — Presidential Decision",
        date="2025-10-10",
        source="kllegalconsultancy.com",
        url="https://www.kllegalconsultancy.com/en/articles/new-regulation-employment-turkish-origin-foreigners-turkey-october-10-2025",
        summary_fa="اصلاحیه روزنامه رسمی 33043 در 10 اکتبر 2025: مسیر کار ویژه تحت Law 2527 برای ترک‌تبارها را به استثنای باریک تبدیل کرد — نه حق کلی. ماده 2/A: جوامع واجد شرایط با تصمیم ریاست‌جمهوری تعیین می‌شود — ادعای نسب خوداثبات نیست. ماده 3: 10 شرط باید همزمان وجود داشته باشد: اقامت وزارت کشور، صلاحیت حرفه با مدارک ترکیه، معادل‌سازی دیپلم، عدم اعتراض امنیتی، ثبت در دفاتر ویژه خارجی‌ها، و 3 شرط جدید سخت: هویت قومی و فرهنگی متفاوت از اکثریت کشور تابعیت. برای ایرانیان معمولا کاربرد ندارد — مسیر اصلی همان Law 6735.",
        summary_tr="Resmi Gazete 33043'te 10 Ekim 2025 değişikliği: 2527 sayılı Kanun kapsamındaki özel çalışma yolunu dar, belge-ağır istisnaya dönüştürdü — genel hak değil. Madde 2/A: yararlanacak topluluklar Cumhurbaşkanlığı kararı ile belirlenir — soy iddiası kendiliğinden kanıt değil. Madde 3: 10 şart birlikte var olmalı: İçişleri ikameti, Türk makamlarından mesleki yeterlilik, diploma denkliği, güvenlik itirazı yok, yabancı özel kütüklere kayıt, ve 3 yeni zor şart: vatandaşlık ülkesinin çoğunluğundan farklı etnik/kültürel kimlik. İranlılar için genellikle uygulanmaz — ana yol yine 6735.",
        category="work-permit",
        tags=["Law 2527", "Türk soylu", "10 Ekim 2025", "Cumhurbaşkanlığı", "denklik"],
        importance="low"
    ),
    NewsItem(
        id="news_09",
        title_fa="هشدار: کار با ویزای توریستی ممنوع — دیپورت + ممنوعیت دائم ورود",
        title_tr="Uyarı: Turist Vizesiyle Çalışmak Yasak — Deport + Kalıcı Giriş Yasağı",
        title_en="Warning: Working with Tourist Visa Forbidden — Deport + Permanent Ban",
        date="2026-08-18",
        source="istaproperty.com",
        url="https://istaproperty.com/blog/turkey-passport-validity-requirements-2025",
        summary_fa="هشدار جدی: هرگز با معافیت ویزای توریستی در ترکیه کار نکن — غیرقانونی — اگر شناسایی شوی دیپورت فوری + ممنوعیت دائم ورود به خاک ترکیه. پاسپورت باید 150 روز اعتبار داشته باشد. اگر بیش از 90 روز در 180 روز بمانی، حتی برای توریستی نیاز به ویزا داری. برای تحصیل ویزای دانشجویی، برای کار ویزای کار. ایرانیان 90 روز بدون ویزا ولی بدون حق کار.",
        summary_tr="Ciddi uyarı: Asla turist vizesi muafiyeti ile Türkiye'de çalışmayın — yasadışı — tespit edilirse derhal deport + Türk topraklarına kalıcı giriş yasağı. Pasaport 150 gün geçerli olmalı. 180 günde 90 günden fazla kalacaksan turistik için bile vize gerekli. Eğitim için öğrenci vizesi, çalışma için çalışma vizesi. İranlılar 90 gün vizesiz ama çalışma hakkı yok.",
        category="work-permit",
        tags=["turist vizesi", "deport", "yasak", "150 gün", "90 gün"],
        importance="high"
    ),
    NewsItem(
        id="news_10",
        title_fa="بسته‌بندی و انبارداری استانبول: E-Ticaret + کargo + اینترنت — حقوق 30,000-40,000 TL",
        title_tr="İstanbul Paketleme ve Depo: E-Ticaret + Kargo + İnternet — Maaş 30,000-40,000 TL",
        title_en="Istanbul Packaging and Warehouse: E-Commerce + Cargo + Internet — Salary 30K-40K",
        date="2025-09-01",
        source="eleman.net + Glassdoor",
        url="https://www.eleman.net/is-ilani/paketleme-personeli-i4762303",
        summary_fa="کار بسته‌بندی و انبارداری استانبول: E-Ticaret + Kargo + اینترنت — حقوق 30,000-40,000 TL — شرکت Elit Müzik Şişli — حجم بالا — نیاز به دقت + سرعت + اینترنت برای پیگیری سفارش آنلاین — مناسب برای یک‌ماهه با اینترنت — مناطق Şişli, Beylikdüzü, Esenyurt — بارانی + اینترنت خوب — برای Simin و Saha بهترین — نیاز به اجازه کار ولی E-Ticaret شانس بیشتر.",
        summary_tr="İstanbul paketleme ve depo işleri: E-Ticaret + Kargo + İnternet — maaş 30,000-40,000 TL — Elit Müzik Şişli — yüksek hacim — dikkat + hız + online sipariş takibi için internet gerekli — 1 ay internetli için uygun — bölgeler Şişli, Beylikdüzü, Esenyurt — yağmurlu + internet iyi — Simin ve Saha için en iyi — çalışma izni gerekli ama E-Ticaret şansı daha yüksek.",
        category="packaging-jobs",
        tags=["paketleme", "depo", "E-Ticaret", "kargo", "internet", "Şişli"],
        importance="high"
    ),
]

def get_news():
    return NEWS_10

def get_news_by_category(cat: str):
    return [n for n in NEWS_10 if n.category==cat]

def get_important_news():
    return [n for n in NEWS_10 if n.importance=="high"]
