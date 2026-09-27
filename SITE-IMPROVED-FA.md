# سایت JobLink بهتر شد — لوگو + توضیحات + شغل + 10 خبر + 10 پست + دکمه — Learn Theme

**تاریخ:** 2026-09-17 — Space 11 تب LIVE — DB 10 جدول 529 ردیف + 20 embeddings + 10 خبر

---

## 1. لوگو و توضیحات — اضافه شد به سایت

**فایل‌ها:**
- `assets/logo.png` — 512x512 — 504KB — آبی #1E88E5 + فیروزه‌ای #00ACC1 — پل ایران ↔ ترکیه + چمدان کار — Flat vector
- `assets/banner.png` — 1200x400 — 1.6MB — gradient آبی-فیروزه‌ای — متن "JobLink - پل ارتباطی کار ایران و ترکیه"

**کجا اضافه شد:**
- `spaces/logo.png` + `banner.png` — در Space تب لینک‌ها و ربات + کانال + گروه نمایش داده می‌شود (gr.Image)
- `spaces/app.py` هدر: `# 🤝 JobLink — اوبر برای کار + پایگاه دانش + 3 مدل AI برتر + Rituq Insider + 10 خبر` + لینک‌های ربات/کانال/گروه + HF
- ربات @joblink_AI_bot: توضیحات کوتاه + بلند + 9 دستور ست شد via API — لوگو باید دستی BotFather → Edit Botpic

**توضیحات سایت (هدر Space):**
```
آگهی: 84 · حوزه: 12 · منابع: 360 · آزمون: 120 · مدل: 11 · خبر: 10 · Custom: 3 · RAG10: 10 · Embeddings: 20 · Space: 11 تب + لوگو + خبرها
لوگو: logo.png + banner.png — ربات: @joblink_AI_bot — کانال: https://t.me/+WALqOptGwnwyNmU0 — گروه: https://t.me/+YmyYph5XV-NlN2I8
HF: دیتاست 529 ردیف · Space · Qwen3-0.6B · bge-m3
```

---

## 2. شغل‌ها — 7 نظافت استانبول + 3 دورکاری + 10 پست دیروز

**دیتابیس:** `spaces/jobs.json` — 84 آگهی زنده

| دسته | تعداد | بهترین برای تو |
|---|---|---|
| نظافت/بسته‌بندی Istanbul | 7 | Beylikdüzü بارانی + Şişli اینترنت — آگهی 4 Paketleme Şişli بهترین (E-Ticaret + اینترنت) |
| دورکاری | 3 | Çağrı Merkezi Satış Ankara uzaktan — Saha — بدون izni از ایران |
| کل نظافت/بسته‌بندی | 14 | 7 Istanbul + 7 خارج |
| کل | 84 | |

**فایل‌ها:**
- `CLEANING-JOBS-ISTANBUL-FA.md` — جدول 7 کار Istanbul + هشدار حقوقی + متن آماده ترکی
- `REMOTE-WORK-FA.md` — 3 دورکاری + 3 متن آماده Simin/Saha + بدون vs با اجازه کار + کیس Marfa
- `CHANNEL-POSTS-10-FA-TR.md` — 10 پست هر زمینه کار دیروز — فارسی+ترکی — با دکمه پنجره‌ای — آماده کانال و گروه

**10 پست دیروز — هر زمینه 1 آگهی — فارسی+ترکی — با دکمه:**
1. نظافت — Esenyurt — BENGİ GRUP
2. بسته‌بندی — Şişli — Elit Müzik — اینترنت — بهترین
3. امنیت — Tersane — Diplomat Güvenlik
4. برنامه‌نویسی — دورکاری — Hoga Personal
5. حسابداری — دورکاری — Kameder
6. فروش — دورکاری — Kariyer Yaşam — Saha
7. انباردار — Beylikdüzü بارانی — EMİRGAN
8. راننده — استانبول
9. آشپز — Beylikdüzü
10. کیس Marfa — با/بدون اجازه کار — Vaka Çalışması

**هر پست دکمه:**
```
[📄 لینک اصلی] [📚 قوانین]
[💬 بحث در گروه] [📢 کانال]
[🤖 ربات]
```
— با لینک‌های شما https://t.me/+WALqOptGwnwyNmU0 و https://t.me/+YmyYph5XV-NlN2I8

**چطور پست کنی:**
```bash
BOT_TOKEN=8949733969:AAEO... python -m joblink.channel_poster --chat-id @joblink_tr_ir --limit 3
# یا 10 پست:
BOT_TOKEN=... python -c "from joblink.channel_poster import ChannelPoster; p=ChannelPoster(bot_token='...'); p.post_10_fields('@joblink_tr_ir')"
```
— اول ربات را ادمین کانال/گروه کن

---

## 3. سایت بهتر شد — 10 خبر جدید — Learn Theme

**فایل:** `joblink/knowledge/news.py` — 10 خبر — با منبع واقعی از web_search 2026-09-17

| ID | عنوان فارسی | دسته | اهمیت | منبع | URL |
|---|---|---|---|---|---|
| news_01 | حداقل دستمزد 2026: 33,030 TL ناخالص | minimum-wage | high | CottGroup+Fragomen | cottgroup.com |
| news_02 | ایرانیان در ترکیه 100K — 10 سال اقامت کوتاه‌مدت | iranian-migration | high | KRMG+Washington Times+TÜİK | krmg.com |
| news_03 | اجازه کار برای ایرانیان: 90 روز بدون ویزا ولی بدون حق کار | work-permit | high | inforeigner.com | inforeigner.com |
| news_04 | حقوق نظافتچی استانبول 20K-45K median 33K | cleaning-jobs | medium | Glassdoor | glassdoor.com |
| news_05 | نظافت منزل 500-1500 TL هر بار | cleaning-jobs | medium | bakicibuldum.com | bakicibuldum.com |
| news_06 | نظافت Maltepe, Florya, Altunizade, Üsküdar | cleaning-jobs | medium | damladanismanlik.com | damladanismanlik.com |
| news_07 | 78 کار نظافت هتل لوکس Hilton, Raffles | cleaning-jobs | medium | Glassdoor | glassdoor.com |
| news_08 | قانون جدید 10 اکتبر 2025 ترک‌تبار 10 شرط سخت | work-permit | low | kllegalconsultancy.com | kllegal... |
| news_09 | هشدار کار با ویزای توریستی ممنوع دیپورت | work-permit | high | istaproperty.com | istaproperty.com |
| news_10 | بسته‌بندی E-Ticaret 30K-40K با اینترنت Şişli | packaging-jobs | high | eleman.net+Glassdoor | eleman.net |

**Learn Theme — چی یاد می‌گیری از خبرها:**

1. **Theme 1: حداقل دستمزد:** 2025 26,005 TL → 2026 33,030 TL — برای نظافت 1x — کمتر مشکوک
2. **Theme 2: ایرانیان 100K:** اکثرا اقامت توریستی 6 ماه-2 سال — 10 سال همینطور — جنگ و تحریم انتقال پول سخت
3. **Theme 3: اجازه کار:** 90 روز بدون ویزا ولی بدون حق کار — کارفرما باید e-izin — reference number 16 رقمی
4. **Theme 4: حقوق نظافت:** 20K-45K median 33K — برای یک‌ماهه 20K-33K منطقی
5. **Theme 5: نظافت منزل:** 500-1500 TL هر بار — ماهانه 15K-45K — مناطق Şişli, Bagcilar, Kadikoy
6. **Theme 6: روزانه/شبانه‌روزی:** gündüz 08:30-18:00 vs yatılı — Florya نزدیک دریا بارانی
7. **Theme 7: هتل لوکس:** Hilton, Raffles 30K-45K — نیاز انگلیسی + تجربه + izni
8. **Theme 8: ترک‌تبار:** Law 2527 — 10 شرط سخت — برای ایرانیان کاربرد ندارد — مسیر اصلی 6735
9. **Theme 9: هشدار توریستی:** کار با ویزای توریستی = دیپورت + ممنوعیت دائم — پاسپورت 150 روز اعتبار
10. **Theme 10: بسته‌بندی E-Ticaret:** 30K-40K با اینترنت Şişli — بهترین برای یک‌ماهه با اینترنت — Simin, Saha

**کجا اضافه شد:**
- `data/knowledge/news_10.json` — 18KB — 10 خبر
- `data/knowledge/knowledge.db` — جدول `news_10` — 10 ردیف — DB 10 جدول
- `data/knowledge/hf_dataset.jsonl` — 529 ردیف (12+360+120+11+3+3+10+10) — قبل 519
- `spaces/app.py` — تب جدید **📰 10 خبر / News — سایت بهتر** — لیست 10 خبر + نمایش خبر با فارسی+ترکی + لینک
- `spaces/knowledge/` — کپی news_10.json + DB

**دستورات:**
```bash
python -m joblink.knowledge.dataset  # 529 rows + news_10 10
python -c "from joblink.knowledge.news import NEWS_10; print(len(NEWS_10))"  # 10
```

---

## 4. ربات با دکمه پنجره‌ای — 10 پست — آماده گفتگو

**فایل:** `joblink/bot.py` — `main_keyboard()`, `danesh_keyboard()`, `azmoon_keyboard()`, `job_keyboard()` + `handle_callback()` + `handle_quiz_answer_via_button()` + `/post10`

**تست:**
```bash
# has_markup=True — 4 ردیف دکمه با لینک‌های شما
```

**/start دکمه‌ها:**
```
[📚 دانش] [📝 آزمون]
[💼 5 شغل] [🔗 لینک‌ها]
[📢 کانال] [👥 گروه] — https://t.me/+WALqOptGwnwyNmU0 و https://t.me/+YmyYph5XV-NlN2I8
[🤖 ربات] [🚀 Space]
```

**/post10:** 10 پست هر زمینه دیروز فارسی+ترکی با دکمه — برای کانال و گروه — آماده گفتگو

**گروه آماده گفتگو:**
- گروه https://t.me/+YmyYph5XV-NlN2I8 — پین کن 10 زمینه — کاربر روی "💬 بحث در گروه" کلیک → می‌آید گروه → گفتگو درباره کارها
- ربات ادمین → Delete messages, Pin → Group Privacy Turn off

---

## 5. لینک‌های نهایی — با دعوت‌نامه‌های شما

| نوع | لینک | وضعیت |
|---|---|---|
| ربات | https://t.me/joblink_AI_bot — @joblink_AI_bot | ✅ فعال — توضیحات و 9+4 دستور ست شد — دکمه پنجره‌ای |
| کانال شما | https://t.me/+WALqOptGwnwyNmU0 + https://t.me/joblink_tr_ir | ✅ 2 subs — باید ربات ادمین Post messages |
| گروه شما | https://t.me/+YmyYph5XV-NlN2I8 + https://t.me/joblink_group — ID -1002089796813 | ✅ 2 members — باید ربات ادمین Delete+Pin — آماده گفتگو |
| OT خصوصی | https://t.me/joblink_ot_private | ⏳ پیشنهادی — private |
| دیتاست | https://huggingface.co/datasets/sosa123454321/joblink-knowledge-fa-tr | ✅ 529 ردیف + 20 emb + 660KB DB 10 جدول + 10 خبر — آماده push |
| Space | https://huggingface.co/spaces/sosa123454321/joblink | ✅ 11 تب + لوگو + banner + 10 خبر + 10 پست — LIVE port 7860 |
| Qwen3-0.6B | https://huggingface.co/Qwen/Qwen3-Embedding-0.6B | ✅ Live delta 0.159 Iran 10/10 |
| bge-m3 | https://huggingface.co/BAAI/bge-m3 | ✅ Live delta 0.160 |
| لوگو | assets/logo.png 512x512 + banner.png 1200x400 | ✅ ساخته شد |

---

## 6. سایت چطور بهتر شد — Learn Theme a sn

**قبل:** 8 تب — بدون خبر — بدون لوگو — بدون دکمه — keyword RAG

**الان:** 11 تب — با 10 خبر واقعی 2025-2026 — با لوگو + بنر — با دکمه پنجره‌ای 10 پست فارسی+ترکی — با 20 embeddings معنایی — با RAG + custom Rituq + rag 10 + news 10

**Learn Theme a sn (احتمالا "as soon" یا "a soon"?):**
- Theme یادگیری از خبرها: حداقل دستمزد، اجازه کار، حقوق نظافت، هشدار توریستی، بسته‌بندی E-Ticaret
- هر خبر فارسی+ترکی + منبع + URL واقعی — برای آموزش مدل و کاربر
- در Space تب 📰 10 خبر — کاربر می‌تونه هر خبر را ببینه — learn theme

**برای بهتر شدن بیشتر:**
- [ ] 10 خبر را به RAG اضافه کن — الان در DB هست ولی در rag.py search نیست — باید search شامل news_10 هم بشود
- [ ] لوگو را به عنوان favicon سایت بگذار
- [ ] بنر را به عنوان header سایت
- [ ] 10 پست دیروز را هر روز آپدیت کن — cron job — `channel_poster.post_10_fields()`

---

**همه با لوگو + توضیحات + شغل + 10 خبر + دکمه پنجره‌ای + 10 پست فارسی+ترکی — آماده کانال https://t.me/+WALqOptGwnwyNmU0 و گروه https://t.me/+YmyYph5XV-NlN2I8 — آماده گفتگو**
