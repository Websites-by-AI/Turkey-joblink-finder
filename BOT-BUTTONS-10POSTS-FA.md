# ربات با دکمه پنجره‌ای + 10 پست هر زمینه کار دیروز — فارسی و ترکی — آماده کانال و گروه

**تاریخ:** 2026-09-14 — ربات @joblink_AI_bot — دکمه‌ها تست شد — 10 پست با دکمه

---

## 1. دکمه پنجره‌ای (Inline Keyboard) روی ربات — اضافه شد

**فایل:** `joblink/bot.py` — `main_keyboard()`, `danesh_keyboard()`, `azmoon_keyboard()`, `job_keyboard()` + `handle_callback()`

**تست زنده:**
```bash
python -m joblink.cli # dummy api test
# API sendMessage has_markup=True — 4 rows buttons
```

### دکمه‌های /start:

```
[📚 پایگاه دانش] [📝 آزمون]
[💼 5 شغل جدید] [🔗 لینک‌ها]
[📢 کانال] [👥 گروه] — با لینک‌های شما https://t.me/+WALqOptGwnwyNmU0 و https://t.me/+YmyYph5XV-NlN2I8
[🤖 ربات] [🚀 Space]
```

- کانال و گروه با **url** — کلیک مستقیم می‌برد به کانال/گروه شما
- دانش، آزمون، شغل، لینک‌ها با **callback_data** — بدون خروج از ربات

### دکمه‌های /danesh:

12 دکمه d01-d12 در 3 ردیف 4 تایی + بازگشت

```
[d01 قوانین مهاجر] [d02 حفاظت] [d03 قانون کار] [d04 اخلاق AI]
[d05 مدل کسب‌وکار] [d06 مالی] [d07 امنیت] [d08 مهارت]
[d09 تلگرام] [d10 NLP] [d11 مهاجرت] [d12 استارتاپ]
[🔙 بازگشت]
```

### دکمه‌های /azmoon:

12 دکمه d01-d12 + تصادفی + بازگشت

### دکمه‌های آزمون (1,2,3,4):

```
[1] [2] [3] [4]
```
— به جای تایپ عدد، کلیک

### دکمه‌های شغل:

```
[📄 لینک اصلی] [📚 قوانین]
[💬 بحث در گروه] [📢 کانال]
[🔙 5 شغل دیگر]
```

- لینک اصلی → url آگهی eleman.net
- قوانین → callback danesh_d01
- بحث در گروه → url https://t.me/+YmyYph5XV-NlN2I8
- کانال → url https://t.me/+WALqOptGwnwyNmU0

**کد:** `bot.py` — `send_with_buttons()` — `reply_markup: {"inline_keyboard": [...]}`

---

## 2. 10 پست هر زمینه کار دیروز — فارسی و ترکی — با دکمه

**فایل:** `CHANNEL-POSTS-10-FA-TR.md` — 10 پست — هر کدام فارسی + ترکی + دکمه‌ها

**منبع:** دیروز — 84 آگهی — 10 زمینه: temizlik, paketleme, güvenlik, yazılım, muhasebe, satış, depo, şoför, aşçı, کیس Marfa

**هر پست شامل:**
- عنوان فارسی + ترکی
- شرکت + شهر + حقوق + لینک اصلی
- هشدار حقوقی Çalışma izni
- هشتگ #JobLink + شهر + زمینه
- دکمه‌ها: لینک اصلی, قوانین, بحث در گروه, کانال, ربات

**مثال پست 1 — نظافت:**
```
🧹 کار نظافت — استانبول Esenyurt

🏢 BENGİ GRUP
⏰ 08:30-18:00
💰 حداقل 26,005 TL
🔗 https://www.eleman.net/is-ilani/temizlik-personeli-i4762417

⚠️ حضوری — izni لازم
📚 /danesh d01
💬 @joblink_group — https://t.me/+YmyYph5XV-NlN2I8

[📄 لینک اصلی] [📚 قوانین]
[💬 بحث در گروه] [📢 کانال]
```

**برای کانال:** https://t.me/+WALqOptGwnwyNmU0 — joblink_tr_ir — 2 subs
**برای گروه:** https://t.me/+YmyYph5XV-NlN2I8 — joblink_group — 2 members — آماده گفتگو

---

## 3. چطور روی کانال پست کنی — با دکمه — آماده گفتگو

### کانال https://t.me/+WALqOptGwnwyNmU0:

1. ربات @joblink_AI_bot را ادمین کن: Channel Info → Administrators → Add → @joblink_AI_bot → ✅ Post messages
2. پست 10 زمینه را بفرست — با دکمه:
```bash
BOT_TOKEN=8949733969:AAEO... python -m joblink.channel_poster --chat-id @joblink_tr_ir --limit 10
# یا
BOT_TOKEN=... python -c "
from joblink.channel_poster import ChannelPoster
poster=ChannelPoster(bot_token='...')
poster.post_10_fields(chat_id='@joblink_tr_ir', lang='both')
"
```
3. هر پست دکمه دارد: لینک اصلی + قوانین + بحث در گروه + کانال + ربات
4. کاربر روی "💬 بحث در گروه" کلیک می‌کند → می‌رود به گروه https://t.me/+YmyYph5XV-NlN2I8 → گفتگو شروع می‌شود

### گروه https://t.me/+YmyYph5XV-NlN2I8 — آماده گفتگو:

1. ربات را ادمین کن: Add members → @joblink_AI_bot → Make Admin → ✅ Delete messages, Pin
2. BotFather → Group Privacy → Turn off + Allow Groups → Enable
3. در گروه پین کن:
```
👥 به گروه JobLink خوش آمدید — اینجا می‌تونید درباره 10 زمینه کاری دیروز گفتگو کنید

📚 10 زمینه:
1. نظافت — Esenyurt
2. بسته‌بندی — Şişli (اینترنت)
3. امنیت — Tersane
4. برنامه‌نویسی — دورکاری
5. حسابداری — دورکاری
6. فروش — دورکاری
7. انباردار — Beylikdüzü بارانی
8. راننده — استانبول
9. آشپز — Beylikdüzü
10. کیس Marfa — با/بدون اجازه کار

هر کدوم را می‌خوای بحث کنیم؟ /danesh یا /azmoon بزن
ربات: @joblink_AI_bot
کانال: https://t.me/+WALqOptGwnwyNmU0
```
4. وقتی کسی در گروه سوال کرد — ربات با دکمه‌ها جواب می‌دهد — گفتگو

### ربات @joblink_AI_bot — دکمه‌ها:

- /start → 4 ردیف دکمه با لینک کانال و گروه شما
- /danesh → 12 دکمه حوزه
- /azmoon → 12 دکمه + تصادفی
- آزمون → دکمه 1,2,3,4
- /shoghle → 5 شغل با دکمه لینک اصلی + قوانین + گروه + کانال
- /post10 → 10 پست هر زمینه دیروز با دکمه — فارسی+ترکی — آماده کانال

**تست local:**
```bash
python -c "from joblink.store import Store; from joblink.bot import Bot; ..."
# has_markup=True — تست شد
```

---

## 4. Space — 10 تب — با لینک‌های شما — LIVE

**فایل:** `spaces/app.py` — 506 خط — 10 تب

| تب | نام |
|---|---|
| 1 | کارجو |
| 2 | کارفرما |
| 3 | 📚 پایگاه دانش |
| 4 | 📝 آزمون |
| 5 | 🤖 10 مدل + TOP3 |
| 6 | 👶 Rituq Insider + RAG 10 |
| 7 | 🔍 RAG |
| 8 | 📖 آموزش AI |
| 9 | 🔗 لینک‌ها — با دعوت‌نامه‌های شما https://t.me/+YmyYph5XV-NlN2I8 و https://t.me/+WALqOptGwnwyNmU0 |
| 10 | 🤖 ربات + کانال + گروه — با لوگو و توضیحات + OT |

**Live Preview:** port 7860 — https://7860-...e2b.app — فعال

**لوگو:** `spaces/logo.png` (504KB) + `banner.png` (1.6MB) — در تب لینک‌ها نمایش

---

## 5. فایل‌های جدید

- `joblink/bot.py` — دکمه پنجره‌ای + callback + 10 پست + group events
- `joblink/channel_poster.py` — post_job با دکمه + post_10_fields
- `CHANNEL-POSTS-10-FA-TR.md` — 10 پست فارسی+ترکی با دکمه — آماده کانال و گروه
- `BOT-BUTTONS-10POSTS-FA.md` — این فایل
- `spaces/app.py` — 10 تب + لینک‌های شما + لوگو
- `assets/logo.png` + `banner.png`

---

## 6. اقدام فوری — 5 دقیقه

1. **ربات را به کانال و گروه خودت ادمین کن** (بالا)
2. **در گروه:** `/post10` بزن — 10 پست هر زمینه دیروز با دکمه فارسی+ترکی ارسال می‌شود
3. **در کانال:** همون 10 پست را فوروارد کن یا دوباره /post10 در کانال (اگر ربات ادمین کانال باشد)
4. **گفتگو:** کاربر روی "💬 بحث در گروه" کلیک می‌کند → می‌آید گروه → درباره کارها گفتگو
5. **لوگو:** BotFather → Edit Botpic → logo.png

**همه با دکمه پنجره‌ای — فارسی و ترکی — آماده کانال و گروه — آماده گفتگو**
