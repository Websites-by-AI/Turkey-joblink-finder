"""10 Telegram job channels for Turkey - monitored every 3h"""
from dataclasses import dataclass
from typing import List

@dataclass
class TGChannel:
    id: str
    username: str  # without @
    title_fa: str
    title_tr: str
    url: str
    tme_url: str  # https://t.me/s/...
    members: int
    lang: str
    commission: str  # ucretsiz / ucretli
    category: str
    description_fa: str
    contact_public: str  # public handle only, no private phone
    is_best: bool = False

CHANNELS_10: List[TGChannel] = [
    TGChannel(
        id="ch01",
        username="karyabi06666",
        title_fa="کاریابی رایگان ترکیه",
        title_tr="Ücretsiz Türkiye İş İlanları",
        url="https://t.me/karyabi06666",
        tme_url="https://t.me/s/karyabi06666",
        members=25158,
        lang="fa",
        commission="بدون کمیسیون - ucretsiz",
        category="عمومی - نظافت، بسته‌بندی، نانوایی، رستوران",
        description_fa="هر روز کارهای مختلف بدون کمیسیون - مراقب کلاهبردار باشید - همه کارها شماره داره - ادمین @Mohamadkhedmati - بهترین کانال",
        contact_public="@Mohamadkhedmati",
        is_best=True,
    ),
    TGChannel(
        id="ch02",
        username="turk_iran_karyabi",
        title_fa="کاریابی ترک ایران استانبول",
        title_tr="Türk İran İş Bulma İstanbul",
        url="https://t.me/turk_iran_karyabi",
        tme_url="https://t.me/s/turkirangroup2018",
        members=5000,
        lang="fa",
        commission="نامشخص",
        category="نظافت منزل شیشلی/بی‌اوغلی، ماساژور هتل",
        description_fa="کاریابی ترک ایران - نظافت منزل منطقه شیشلی بی اوغلی تسویه روزانه/ماهانه - هتل",
        contact_public="@turk_iran_karyabi",
        is_best=True,
    ),
    TGChannel(
        id="ch03",
        username="ostadkaraniraq",
        title_fa="کاریابی عراق، ترکیه، ارمنستان",
        title_tr="Irak Türkiye Ermenistan İş",
        url="https://t.me/ostadkaraniraq",
        tme_url="https://t.me/s/ostadkaraniraq",
        members=6330,
        lang="fa",
        commission="هزینه کاریابی دارد",
        category="کارگر ساده خدماتی مالات دیاربکر 25-30K، کیملیک می‌گیرند",
        description_fa="15 نفر نیروی ساده خدماتی مالات نزدیک دیاربکر - تایم 8-6 - پاترون ترک خوش‌حساب - کیملیک - پاسپورت الزامی",
        contact_public="@fms93",
        is_best=False,
    ),
    TGChannel(
        id="ch04",
        username="dalgagroup",
        title_fa="دلگا گروپ کاریابی استانبول",
        title_tr="Dalga Group İstanbul İş",
        url="https://t.me/dalgagroup",
        tme_url="https://t.me/s/dalgagroup",
        members=8000,
        lang="fa",
        commission="بدون کمیسیون",
        category="کارواش، رستوران گارسون، منشی شرکت، چاپ لباس",
        description_fa="اکثر کارها جای خواب + ناهار دارد - حقوق 2000-3000 لیر قدیم - آگهی استخدام استانبول - اینستا turkykaryab",
        contact_public="@d_turkey",
        is_best=True,
    ),
    TGChannel(
        id="ch05",
        username="karyabiyesenator",
        title_fa="کاریابی سناتور استانبول",
        title_tr="Senator İş Bulma İstanbul",
        url="https://t.me/karyabiyesenator",
        tme_url="https://t.me/s/karyabiyesenator",
        members=1990,
        lang="fa",
        commission="تضمینی با مجوز گردشگری",
        category="کارگاه قاشق چنگال گونشلی 90 لیر روزانه تسویه هفتگی",
        description_fa="با مجوز اداره گردشگری ترکیه - کادر مجرب - @vahidtur - 00905461152327 - انواع کار تضمینی",
        contact_public="@vahidtur",
        is_best=False,
    ),
    TGChannel(
        id="ch06",
        username="venusdogan",
        title_fa="گروه مشاورین آیتاج کاریابی",
        title_tr="Aytaç Danışmanlık İş",
        url="https://t.me/venusdogan",
        tme_url="https://t.me/s/venusdogan",
        members=3000,
        lang="fa",
        commission="نامشخص",
        category="باریستا گون گورن، تدارکات صبحانه اسن‌یورت 2500 لیر",
        description_fa="باریستا خانم گون گورن جای خواب ندارد غذا دارد - تدارکات میز صبحانه اسن یورت آقا جای خواب دارد 8:30-19:00 یکشنبه تعطیل",
        contact_public="@venusdogan",
        is_best=False,
    ),
    TGChannel(
        id="ch07",
        username="divar_estanbul",
        title_fa="دیوار و کاریابی استانبول",
        title_tr="İstanbul Duvar İş İlanları",
        url="https://t.me/divar_estanbul",
        tme_url="https://t.me/s/divar_estanbul",
        members=2010,
        lang="fa",
        commission="رایگان جویای کار",
        category="جویای کار - راننده سنگین، نصاب کرکره برقی، برق صنعتی",
        description_fa="تبلیغات جویای کار رایگان - دیوار استانبول - ادمین @ads_turkey @ejare_istanbul @Amlak_turkey",
        contact_public="@ads_turkey",
        is_best=False,
    ),
    TGChannel(
        id="ch08",
        username="istkaryab",
        title_fa="کاریابی ایشبول استانبول",
        title_tr="İşbul İstanbul İş",
        url="https://t.me/istkaryab",
        tme_url="https://t.me/s/istkaryab",
        members=21,
        lang="fa",
        commission="100% تضمینی ادعا",
        category="شیرینی‌پز، عکاس مجالس، املاک توریستی، شیشه‌بر",
        description_fa="100% تضمینی - خرید اجاره منزل - ارسال کالا ایران - رهام ادیبان +90 537 233 50 89 طاها بهرامی",
        contact_public="@istkaryab",
        is_best=False,
    ),
    TGChannel(
        id="ch09",
        username="linkdoni_turkye",
        title_fa="لینکدونی ترکیه",
        title_tr="Türkiye Linkdoni",
        url="https://t.me/linkdoni_turkye",
        tme_url="https://t.me/s/linkdoni_turkye",
        members=10000,
        lang="fa",
        commission="تبلیغات آزاد",
        category="املاک، توریستی، صرافی، اخذ اقامت، پاسپورت، ترانسفر",
        description_fa="گروه ایرانیان ترکیه تبلیغات آزاد - کسب و کار رونق - @Turkish_Groupp @Iranian_grooup",
        contact_public="@Turkish_Groupp",
        is_best=False,
    ),
    TGChannel(
        id="ch10",
        username="joblink_tr_ir",
        title_fa="JobLink کانال رسمی شما",
        title_tr="JobLink Resmi Kanal",
        url="https://t.me/+WALqOptGwnwyNmU0",
        tme_url="https://t.me/s/joblink_tr_ir",
        members=2,
        lang="fa/tr",
        commission="بدون کمیسیون - رسمی JobLink",
        category="10 حوزه کاری + 20 شغل + خبر + AI",
        description_fa="کانال رسمی JobLink شما - دعوت https://t.me/+WALqOptGwnwyNmU0 - گروه https://t.me/+YmyYph5XV-NlN2I8 - ربات @joblink_AI_bot - Space 11 تب",
        contact_public="@joblink_AI_bot",
        is_best=True,
    ),
]

def get_best_channels():
    return [c for c in CHANNELS_10 if c.is_best]

def get_all_usernames():
    return [c.username for c in CHANNELS_10]
