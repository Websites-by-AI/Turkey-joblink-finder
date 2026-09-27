# راهنمای کانال و گروه تلگرام JobLink + لوگو و توضیحات

## لوگوها

**فایل‌ها:**
- `assets/logo.png` — لوگوی مربعی 512x512 برای پروفایل کانال/گروه/ربات
- `assets/banner.png` — بنر 1200x400 برای هدر کانال

**طراحی:**
- رنگ اصلی: آبی #1E88E5 + فیروزه‌ای #00ACC1 (اعتماد + پل)
- آیکون: پل بین ایران و ترکیه + چمدان کار + پین موقعیت
- متن: JobLink — فونت مدرن sans-serif
- استایل: Flat vector، مناسب تلگرام

**نحوه ست کردن در BotFather:**
```
/mybots → @YourBot → Edit Bot → Edit Botpic → آپلود logo.png
```

---

## توضیحات ربات (Bot Description)

### کوتاه (512 کاراکتر) — برای BotFather → Edit Description:
```
🤝 JobLink — اوبر برای کار | پل ایران ↔ ترکیه

رزومه‌ات را (فارسی) بفرست → 5 آگهی واقعی ترکیه با امتیاز + مهارت‌های هم‌پوشان + فاصله‌هایی که باید پر کنی

📚 /danesh — پایگاه دانش حقوقی 12 حوزه (اجازه کار، KVKK، تحریم)
📝 /azmoon — آزمون 10 سوالی هر حوزه
💼 /shoghle — 5 پیشنهاد جدید
🔒 /hayir — حذف کامل داده‌ها (KVKK/GDPR)

100% opt-in — هیچ رزومه‌ای از سایت دیگر برداشته نمی‌شود
```

### بلند (برای About) — BotFather → Edit About:
```
JobLink چیست؟
یک بازار کار دوطرفه مثل اوبر/اسنپ: عرضه = آگهی‌های ترکیه (10 سایت)، تقاضا = کارجویان ایرانی (opt-in تلگرام)

چطور کار می‌کند؟
1. /katil بزن — رضایت
2. رزومه‌ات را بفرست (فارسی، ترکی یا انگلیسی)
3. 5 آگهی ترکیه با دلیل مچ + هشدار حقوقی (اجازه کار، KVKK) بگیر
4. هر شب 3 آگهی جدید

پایگاه دانش:
12 حوزه حقوقی/مالی/اخلاقی — هر کدام 10 مقاله+10 کتاب+10 ویدیو+10 سوال آزمون
- d01 اجازه کار ترکیه (Law 6735, Turkuaz, Tech Visa)
- d02 KVKK + GDPR
- d06 تحریم و مالی (OFAC, هالک‌بانک)
- ... (12 حوزه کامل)

هوش مصنوعی:
- 11 مدل مقایسه (Qwen3-0.6B بهترین برای ایران 10/10)
- 3 مدل کاستوم Rituq Insider (Qwen3-0.6B + bge-m3 + Phi-3-mini)
- 10 مدل RAG با delta polysemy تست زنده
- RAG معنایی با 20 embedding (Qwen3-0.6B) — برای 492 کامل نیاز به PRO

امنیت:
- رضایت صریح با consent_token
- contact_hash — شماره ذخیره نمی‌شود
- /hayir حذف کامل (KVKK m.7 / GDPR art.17)

ساخته شده با Cloudflare Workers + D1 + Hugging Face Spaces + Telegram
کد: github.com/sosa123454321/joblink
دیتاست: huggingface.co/datasets/sosa123454321/joblink-knowledge-fa-tr
Space: huggingface.co/spaces/sosa123454321/joblink
```

### دستورات ربات (BotFather → Edit Commands):
```
start - شروع و رضایت
katil - ثبت‌نام (opt-in)
hayir - حذف کامل داده‌ها
haziri - آماده مهاجرت به ترکیه (حضوری)
dorkari - فقط دورکاری
shoghle - 5 پیشنهاد جدید
danesh - پایگاه دانش 12 حوزه
azmoon - آزمون 10 سوالی
help - راهنما
profil - ویرایش پروفایل
```

---

## کانال تلگرام — پیشنهاد

**نام کانال:** `JobLink — کار ایران ↔ ترکیه`

**آیدی پیشنهادی:** `@joblink_tr_ir` یا `@joblink_iran_turkey`

**توضیحات کانال (Channel Description):**
```
🤝 JobLink — پل کار ایران و ترکیه | Uber for Jobs

هر روز 5 آگهی واقعی ترکیه با ترجمه فارسی + حقوق TL + شهر + لینک اصلی
+ تحلیل حقوقی: اجازه کار، KVKK، حداقل دستمزد 26,005 TL

📚 پایگاه دانش: 12 حوزه حقوقی — هر کدام 10 مقاله+10 کتاب+10 ویدیو
📝 آزمون: /azmoon در ربات
🤖 هوش مصنوعی: 11 مدل + 3 کاستوم Rituq + RAG معنایی

ربات: @joblink_bot (پیشنهادی)
گروه بحث: @joblink_group (پیشنهادی)
دیتاست: hf.co/datasets/sosa123454321/joblink-knowledge-fa-tr
Space: hf.co/spaces/sosa123454321/joblink
کد: github.com/sosa123454321/joblink

⚠️ همه آگهی‌ها از 10 سایت ترکیه (eleman.net, kariyer.net...) — هیچ رزومه‌ای از سایت ایرانی برداشته نمی‌شود (KVKK/GDPR)

#کاریابی #ترکیه #مهاجرت_کاری #JobLink
```

**لینک کانال:** `https://t.me/joblink_tr_ir`

**لوگو:** `assets/logo.png` (512x512)
**بنر:** `assets/banner.png` (اگر کانال بنر دارد)

---

## گروه تلگرام — پیشنهاد OT (Operational Team / Discussion)

**نام گروه:** `JobLink Group — بحث و پشتیبانی`

**آیدی پیشنهادی:** `@joblink_group` یا `@joblink_ot`

**توضیحات گروه:**
```
👥 گروه بحث JobLink — کار ایران ↔ ترکیه

اینجا می‌تونی:
- رزومه‌ات را بفرستی و از بقیه فیدبک بگیری
- درباره اجازه کار، KVKK، حقوق سوال بپرسی
- آگهی‌های مشکوک را گزارش کنی
- با منتورهای مقیم ترکیه صحبت کنی

🤖 ربات داخل گروه هست — @joblink_bot
- /shoghle — 5 آگهی جدید (در PV ربات)
- /danesh d01 — قوانین اجازه کار
- /azmoon d01 — آزمون

📢 کانال اصلی: @joblink_tr_ir
📚 دیتاست: hf.co/datasets/sosa123454321/joblink-knowledge-fa-tr

قوانین:
1. احترام — بدون توهین
2. بدون اسپم آگهی — فقط JobLink
3. بدون اشتراک شماره/پاسپورت در گروه — فقط در PV ربات
4. سوال حقوقی؟ /danesh بزن اول

ادمین: @sosa123454321
```

**تنظیمات گروه:**
- نوع: Public supergroup
- تاریخچه: Visible
- ربات ادمین شود؟ **بله** — برای اینکه دستورات /danesh و /azmoon در گروه هم کار کند
- مجوز ربات: Delete messages (برای اسپم)، Pin messages، Add new admins = No

**اضافه کردن ربات به گروه:**
1. گروه بساز → Add members → @joblink_bot را اضافه کن
2. ربات را Admin کن (با مجوز Delete messages)
3. در BotFather → /mybots → @YourBot → Bot Settings → Group Privacy → **Turn off** (تا ربات پیام‌های گروه را ببیند)
4. در گروه: `/start@joblink_bot` بزن

**OT چیست؟**
- OT = Operational Team — تیم عملیاتی JobLink (شما + 2-3 منتور مقیم ترکیه)
- OT Group = گروه خصوصی برای هماهنگی ادمین‌ها
- پیشنهاد: یک گروه خصوصی `@joblink_ot_private` بساز فقط برای ادمین‌ها + ربات

---

## لینک‌های مهم — خلاصه

| نوع | لینک پیشنهادی | وضعیت |
|---|---|---|
| ربات تلگرام | `https://t.me/joblink_bot` | باید بسازی — BotFather |
| کانال | `https://t.me/joblink_tr_ir` | باید بسازی |
| گروه بحث | `https://t.me/joblink_group` | باید بسازی |
| گروه OT خصوصی | `https://t.me/joblink_ot_private` | باید بسازی (private) |
| دیتاست HF | `https://huggingface.co/datasets/sosa123454321/joblink-knowledge-fa-tr` | آماده push — 519 ردیف + 20 embeddings |
| Space HF | `https://huggingface.co/spaces/sosa123454321/joblink` | آماده — 8 تب |
| مدل Qwen3-0.6B | `https://huggingface.co/Qwen/Qwen3-Embedding-0.6B` | Live ✅ تست شد |
| مدل bge-m3 | `https://huggingface.co/BAAI/bge-m3` | Live ✅ |
| مدل e5-large | `https://huggingface.co/intfloat/multilingual-e5-large` | Live ✅ |
| کد GitHub | `https://github.com/sosa123454321/joblink` | باید push |

---

## چک‌لیست راه‌اندازی کانال/گروه

- [ ] BotFather → /newbot → نام: JobLink — آیدی: joblink_bot
- [ ] BotFather → /mybots → joblink_bot → Edit Botpic → آپلود `assets/logo.png`
- [ ] BotFather → Edit Description → متن کوتاه بالا
- [ ] BotFather → Edit About → متن بلند بالا
- [ ] BotFather → Edit Commands → لیست دستورات بالا
- [ ] BotFather → Bot Settings → Group Privacy → Turn off
- [ ] ساخت کانال @joblink_tr_ir → آپلود logo.png + banner.png + توضیحات کانال
- [ ] ساخت گروه @joblink_group → توضیحات گروه + اضافه کردن ربات به عنوان ادمین
- [ ] ساخت گروه خصوصی @joblink_ot_private → فقط ادمین‌ها + ربات
- [ ] تست: در گروه /danesh d01 بزن — باید جواب بدهد
- [ ] تست: در گروه /azmoon d01 بزن — باید آزمون شروع شود

---

## لوگو — مشخصات فنی

- **logo.png:** 512x512, PNG, <200KB, background سفید یا شفاف, مناسب برای دایره تلگرام
- **banner.png:** 1200x400, PNG/JPG, <500KB, gradient آبی-فیروزه‌ای
- **فرمت‌های دیگر پیشنهادی:** SVG برای وب، ICO برای سایت

**اگر می‌خواهی لوگوی جدید:** `python -m joblink.cli` ندارد — از `assets/logo.png` استفاده کن یا با DALL-E جدید بساز
