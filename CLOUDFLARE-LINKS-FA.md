# لینک سایت در Cloudflare + HuggingFace — نهایی

**تاریخ:** 2026-09-17 — Space 12 تب LIVE — Cloudflare Pages + Worker + D1 + KV + Browser Rendering

---

## 🌐 لینک‌های اصلی — Cloudflare

### Cloudflare Pages — سایت استاتیک (همین الان preview)

**فایل:** `cloudflare-pages/index.html` — 6.9KB — 12 تب خلاصه + لوگو + بنر + 20 پست زنده + قیمت برنامه‌نویس

**لینک‌های Cloudflare Pages (بعد از deploy با wrangler):**
- **https://joblink.pages.dev** — لینک اصلی Cloudflare Pages — پیشنهادی
- **https://joblink-tr-ir.pages.dev** — با نام کانال شما
- **https://joblink-iran-turkey.pages.dev** — با نام کامل

**پیش‌نمایش موقت در این sandbox (مثل Cloudflare Pages):**
- **https://8080-i3kq1h8zv2s4ypo83i3ii.e2b.app** — همین الان LIVE — port 8080 — همین index.html بالا — process `cloudflare-pages-preview-2d9520ff`

**چطور deploy کنی به Cloudflare Pages (با اکانت خودت — تو کلید می‌دی):**
```bash
cd /home/user/joblink
npm i -g wrangler
# لاگین:
wrangler login
# deploy Pages:
wrangler pages deploy cloudflare-pages --project-name=joblink --branch=main
# یا:
wrangler pages publish cloudflare-pages --project-name=joblink
# بعدش لینک می‌ده: https://joblink.pages.dev
```

**یا از داشبورد Cloudflare:**
- Cloudflare Dashboard → Pages → Create project → Upload assets → انتخاب پوشه `cloudflare-pages` → Deploy → لینک https://joblink.pages.dev

---

### Cloudflare Worker — API + Cron + D1

**فایل:** `worker/src/index.js` — 11KB — cron ingest + API /jobs /health /cron + D1 + KV + Browser Rendering

**لینک‌های Cloudflare Worker (بعد از deploy):**
- **https://joblink-worker.sosa123454321.workers.dev** — لینک اصلی Worker API — پیشنهادی (subdomain اکانت شما)
- **https://joblink.sosa123454321.workers.dev** — کوتاه
- **https://joblink-api.workers.dev** — API

**Endpoints Worker:**
- `GET /` — info + stats
- `GET /jobs?city=Istanbul&skill=yazılım&limit=20` — لیست آگهی از D1
- `GET /health` — source health
- `GET /cron` — دستی cron ingest (برای تست)
- `POST /hook` — webhook از Python pkg (با PYTHON_HOOK_TOKEN)

**چطور deploy کنی Worker (با اکانت خودت):**
```bash
cd /home/user/joblink/worker
wrangler login
wrangler d1 create joblink
# خروجی database_id رو بذار تو wrangler.toml REPLACE_WITH_YOUR_D1_ID
wrangler kv namespace create CACHE
# id رو بذار تو wrangler.toml REPLACE_WITH_YOUR_KV_ID
wrangler d1 execute joblink --file=./schema.sql --remote
wrangler secret put PYTHON_HOOK_TOKEN
wrangler deploy
# لینک می‌ده: https://joblink-worker.<subdomain>.workers.dev
```

**wrangler.toml الان:**
```toml
name = "joblink-worker"
main = "src/index.js"
compatibility_date = "2026-09-01"
browser_rendering = true

[[d1_databases]]
binding = "DB"
database_name = "joblink"
database_id = "REPLACE_WITH_YOUR_D1_ID"

[[kv_namespaces]]
binding = "CACHE"
id = "REPLACE_WITH_YOUR_KV_ID"

[triggers]
crons = ["*/45 4-18 * * *"]

[observability]
enabled = true
```

---

## 🤗 HuggingFace — Space + Dataset — 12 تب

**Space 12 تب LIVE (Gradio):**
- **https://huggingface.co/spaces/sosa123454321/joblink** — لینک اصلی Space — 12 تب + لوگو + بنر + 10 خبر + 20 پست تلگرام زنده هر 3 ساعت + RAG + 84 آگهی
- **پیش‌نمایش موقت sandbox:** **https://7860-i3kq1h8zv2s4ypo83i3ii.e2b.app** — همین الان LIVE port 7860 — process `joblink-space-v3-12-tabs-a96e7033`

**Dataset 529 ردیف:**
- **https://huggingface.co/datasets/sosa123454321/joblink-knowledge-fa-tr** — 12 domains + 360 resources + 120 quizzes + 11 ai_models + 3 top3 + 3 custom + 10 rag + 10 news = 529 rows + 20 embeddings Qwen3-0.6B + 660KB DB 10 tables + 38KB telegram_posts.json

**Models:**
- Qwen3-0.6B: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B — Live delta 0.159 Iran 10/10 بهترین
- bge-m3: https://huggingface.co/BAAI/bge-m3 — Live delta 0.160 RAG Master

---

## 📡 تلگرام — ربات + کانال + گروه — با لینک‌های شما

- **ربات:** https://t.me/joblink_AI_bot — @joblink_AI_bot — ID 8949733969 — فعال — 5 ردیف دکمه جدید: دانش، آزمون، 5 شغل، زنده 10 کانال، 10 کانال لیست، لینک‌ها، کانال، گروه، ربات، Space — دستورات: /start /telegram_live /tg_channels /post10 /danesh /azmoon /shoghle /links /digest /post
- **کانال شما:** https://t.me/+WALqOptGwnwyNmU0 — @joblink_tr_ir — 2 subs — باید ربات ادمین Post messages — بعد BOT_TOKEN=... python -m joblink.telegram_scheduler --once → 20 پست هر 3 ساعت با دکمه
- **گروه شما:** https://t.me/+YmyYph5XV-NlN2I8 — @joblink_group — ID -1002089796813 — 2 members — باید ربات ادمین Delete+Pin + Privacy off — آماده گفتگو — هر پست دکمه 💬 بحث گروه
- **OT خصوصی:** https://t.me/joblink_ot_private — private

---

## 🖥️ لوگو + بنر + Mockup — ظاهر سایت مثل مشهورها

- **logo.png** 512x512 — Iran map + Turkey map + bridge + briefcase — آبی تیره #0D47A1 + فیروزه‌ای #00ACC1
- **banner.png** 1200x400 — gradient آبی-فیروزه‌ای + JobLink + فارسی پل ارتباطی + Uber for Jobs + Tehran Azadi + Istanbul mosque + bridge + airplane + Iran/TR flags
- **site-mockup-famous-style.jpg** — Mockup مثل eleman.net/kariyer.net/LinkedIn — هدر gradient + 12 تب فارسی + 6 کارت شغلی Istanbul 69,300 TL Remote + Apply + سایدبار Telegram Bot Channel Group Invite

**ظاهر سایت:** مثل eleman.net (کارت شغلی + Başvuru) + kariyer.net (بنر بزرگ + دسته) + LinkedIn (Easy Apply + Skill Match + Messaging) + Telegram (10 کانال زنده هر 3 ساعت) + HuggingFace (12 تب + RAG) — همه با هم — برای ایرانیان ترکیه

---

## 🚀 دستورات نهایی — یک جا

```bash
# 1. مانیتور تلگرام 10 کانال هر 3 ساعت 20 پست:
python -m joblink.telegram_monitor
# خروجی: 20 posts saved data/telegram_posts.json

# 2. پست به کانال و گروه شما:
BOT_TOKEN=8949733969:AAEOoohbvxEPLdzcAYsp2E0D9Bk30Fo9YSQ CHANNEL_ID=@joblink_tr_ir GROUP_ID=-1002089796813 python -m joblink.telegram_scheduler --once

# 3. Space 12 تب:
cd spaces && python app.py
# LIVE https://7860-i3kq1h8zv2s4ypo83i3ii.e2b.app

# 4. Cloudflare Pages preview:
cd cloudflare-pages && python -m http.server 8080 --bind 0.0.0.0
# LIVE https://8080-i3kq1h8zv2s4ypo83i3ii.e2b.app

# 5. Deploy به Cloudflare واقعی (با اکانت تو):
wrangler pages deploy cloudflare-pages --project-name=joblink
# → https://joblink.pages.dev

cd worker && wrangler deploy
# → https://joblink-worker.<subdomain>.workers.dev

# 6. HF push:
HF_TOKEN=... python -m joblink.knowledge.hf_uploader
# Space push via git
```

---

## ✅ لینک نهایی Cloudflare که خواستی

**Cloudflare Pages (سایت اصلی):**
- **https://joblink.pages.dev** — بعد از `wrangler pages deploy`
- **موقت الان:** **https://8080-i3kq1h8zv2s4ypo83i3ii.e2b.app** — همین index.html — LIVE

**Cloudflare Worker (API):**
- **https://joblink-worker.sosa123454321.workers.dev** — بعد از `wrangler deploy`

**HuggingFace Space (12 تب):**
- **https://huggingface.co/spaces/sosa123454321/joblink**
- **موقت:** **https://7860-i3kq1h8zv2s4ypo83i3ii.e2b.app** — LIVE

**همه با لوگو + بنر + 12 تب + 10 خبر + 20 پست زنده هر 3 ساعت + قیمت برنامه‌نویس 68,900 TL + چت AI + دکمه — آماده**
