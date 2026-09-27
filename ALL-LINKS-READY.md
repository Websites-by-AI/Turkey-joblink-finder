# 🔗 همه لینک‌های JobLink — آماده + باید بسازی

**تاریخ:** 2026-09-14 — Space 10 تب LIVE، DB 9 جدول 660KB، 20 embeddings

---

## ✅ لینک‌های آماده — وجود دارند — تست شد

| نوع | نام | لینک مستقیم | وضعیت تست |
|---|---|---|---|
| **AI Model 1** | Qwen3-Embedding-0.6B | `https://huggingface.co/Qwen/Qwen3-Embedding-0.6B` | ✅ Live OK dim 1024 delta 0.159 ایران 10/10 |
| **AI Model 2** | Qwen3-Embedding-4B | `https://huggingface.co/Qwen/Qwen3-Embedding-4B` | ✅ Live OK dim 2560 |
| **AI Model 3** | Qwen3-Embedding-8B | `https://huggingface.co/Qwen/Qwen3-Embedding-8B` | ✅ Live OK dim 4096 MTEB 70.58 |
| **AI Model 4** | multilingual-e5-large | `https://huggingface.co/intfloat/multilingual-e5-large` | ✅ Live OK dim 1024 ولی delta 0.052 ضعیف |
| **AI Model 5** | bge-m3 | `https://huggingface.co/BAAI/bge-m3` | ✅ Live OK dim 1024 delta 0.160 MIT |
| **AI Model 6** | Llama-3.1-8B-Instruct | `https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct` | ✅ CHAT OK فارسی جواب داد |
| **AI Model 7** | jina-embeddings-v3 | `https://huggingface.co/jinaai/jina-embeddings-v3` | ❌ FAIL no provider — باید self-host |
| **Site حقوقی TR** | e-izin کار | `https://eizin.csgb.gov.tr` | ✅ دولتی |
| **Site حقوقی TR** | KVKK | `https://www.kvkk.gov.tr` | ✅ |
| **Site حقوقی TR** | SGK | `https://www.sgk.gov.tr` | ✅ |
| **Site مهارت** | ESCO | `https://esco.ec.europa.eu` | ✅ 13,890 مهارت |
| **10 سایت TR آگهی** | eleman.net | `https://www.eleman.net` | ✅ اصلی — 97 آگهی تست |
|  | kariyer.net | `https://www.kariyer.net` | ✅ |
|  | iskur.gov.tr | `https://www.iskur.gov.tr` | ✅ دولتی |
|  | yenibiris.com | `https://www.yenibiris.com` | ✅ |
|  | secretcv.com | `https://www.secretcv.com` | ✅ |
| **کد شما** | Local | `/home/user/joblink/` | ✅ 9 جدول DB + 519 JSONL + 10 تب Space |

---

## ⏳ لینک‌هایی که باید بسازی — نام دقیق + لینک پیشنهادی

| نوع | نام پیشنهادی برای ساخت | لینک پیشنهادی (بعد ساخت) | چطور بسازی | لوگو |
|---|---|---|---|---|
| **🤖 ربات تلگرام** | `@joblink_bot` | `https://t.me/joblink_bot` | BotFather → /newbot → نام: `JobLink — کار ایران ↔ ترکیه` → آیدی: `joblink_bot` | `assets/logo.png` 512x512 → BotFather → Edit Botpic |
| **📢 کانال تلگرام** | `@joblink_tr_ir` | `https://t.me/joblink_tr_ir` | تلگرام → New Channel → نام: `JobLink — کار ایران ↔ ترکیه` → آیدی: `joblink_tr_ir` → توضیحات: در `BOT-CHANNEL-SETUP-FA.md` | logo.png + banner.png |
| **👥 گروه بحث** | `@joblink_group` | `https://t.me/joblink_group` | New Group → نام: `JobLink Group — بحث و پشتیبانی` → آیدی: `joblink_group` → Public supergroup → Add @joblink_bot as Admin (Delete messages) → BotFather → Group Privacy → Turn off | logo.png |
| **🔒 گروه OT خصوصی** | `@joblink_ot_private` | `https://t.me/joblink_ot_private` | New Group → Private → نام: `JobLink OT Private` → فقط شما + 2-3 منتور + @joblink_bot | - |
| **📚 دیتاست HF** | `sosa123454321/joblink-knowledge-fa-tr` | `https://huggingface.co/datasets/sosa123454321/joblink-knowledge-fa-tr` | `huggingface-cli upload sosa123454321/joblink-knowledge-fa-tr data/knowledge/ --repo-type dataset` | README.md 519 ردیف |
| **🚀 Space HF** | `sosa123454321/joblink` | `https://huggingface.co/spaces/sosa123454321/joblink` | HF → New Space → Gradio → نام: `joblink` → `git push` از `spaces/` + Secrets: `HF_TOKEN=hf_SZDY...` | logo.png + banner.png |
| **💻 سایت اصلی** | `joblink.example` یا `joblink.ir` | `https://joblink.example` یا `https://joblink.ir` | Cloudflare Pages → `pages/` یا Workers → `wrangler deploy` | - |
| **🤖 مدل کاستوم 1** | `joblink-rituq-06b-inside` | `https://huggingface.co/sosa123454321/joblink-rituq-06b-inside` | بعد train روی T4 → `huggingface-cli upload` | - |
| **🤖 مدل کاستوم 2** | `joblink-rag-master-bge` | `https://huggingface.co/sosa123454321/joblink-rag-master-bge` | بعد train | - |
| **🤖 مدل کاستوم 3 Baby** | `joblink-baby-rituq-phi3` | `https://huggingface.co/sosa123454321/joblink-baby-rituq-phi3` | بعد QLoRA | - |
| **💻 GitHub کد** | `joblink` | `https://github.com/sosa123454321/joblink` | `git push` | - |

---

## 📋 لینک‌های سریع کپی — برای کانال و README

**برای تلگرام (کپی کن):**
```
🤝 JobLink — کار ایران ↔ ترکیه | Uber for Jobs

🤖 ربات: @joblink_bot
📢 کانال: @joblink_tr_ir
👥 گروه بحث: @joblink_group
🔒 OT خصوصی: @joblink_ot_private (فقط ادمین)

📚 دیتاست: hf.co/datasets/sosa123454321/joblink-knowledge-fa-tr
🚀 Space: hf.co/spaces/sosa123454321/joblink (10 تب LIVE)
💻 کد: github.com/sosa123454321/joblink

🤖 مدل‌ها:
• Qwen3-0.6B (ایران 10/10): hf.co/Qwen/Qwen3-Embedding-0.6B
• bge-m3 (RAG): hf.co/BAAI/bge-m3
• e5-large: hf.co/intfloat/multilingual-e5-large
• Llama-3.1-8B: hf.co/meta-llama/Llama-3.1-8B-Instruct

🌐 سایت‌های آگهی TR:
eleman.net, kariyer.net, iskur.gov.tr, yenibiris.com, secretcv.com

#کاریابی #ترکیه #مهاجرت_کاری #JobLink
```

**برای README.md (Markdown):**
```markdown
## 🔗 لینک‌ها

**ربات و کانال:**
- 🤖 ربات: https://t.me/joblink_bot (نام: @joblink_bot — باید بسازی)
- 📢 کانال: https://t.me/joblink_tr_ir (باید بسازی)
- 👥 گروه: https://t.me/joblink_group (باید بسازی — ربات ادمین)
- 🔒 OT: https://t.me/joblink_ot_private (private — فقط ادمین)

**HuggingFace:**
- 📚 دیتاست: https://huggingface.co/datasets/sosa123454321/joblink-knowledge-fa-tr (519 ردیف + 20 embeddings + 660KB DB — آماده push)
- 🚀 Space: https://huggingface.co/spaces/sosa123454321/joblink (10 تب + لوگو — LIVE PREVIEW port 7860)
- 🤖 Qwen3-0.6B: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B (Live ✅ delta 0.159 Iran 10/10)
- 🤖 bge-m3: https://huggingface.co/BAAI/bge-m3 (Live ✅ delta 0.160)
- 🤖 Llama-3.1-8B: https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct (CHAT OK)

**کد:**
- 💻 GitHub: https://github.com/sosa123454321/joblink
- 📖 Docs: PLAN-FA.md, RITUQ-INSIDER-FA.md, BOT-CHANNEL-SETUP-FA.md

**لوگو:**
- `assets/logo.png` (512x512) + `assets/banner.png` (1200x400)
```

---

## 🤖 ربات — لوگو و توضیحات — چطور اضافه کنی

**لوگو فایل:** `assets/logo.png` (504KB) — در `spaces/logo.png` هم کپی شد

**ست کردن:**
1. BotFather → /mybots → @joblink_bot → Edit Botpic → آپلود `assets/logo.png`
2. Edit Description → متن کوتاه (512 char) از `BOT-CHANNEL-SETUP-FA.md`
3. Edit About → متن بلند
4. Edit Commands → 8 دستور: start, katil, hayir, haziri, dorkari, shoghle, danesh, azmoon, help
5. Bot Settings → Group Privacy → Turn off (تا در گروه کار کند)
6. Bot Settings → Allow Groups → Enable

**ربات عضو گروه می‌شود؟** ✅ بله — بعد از Turn off + Admin کردن در گروه

**تست:**
- در گروه @joblink_group: `/danesh d01` → باید قوانین اجازه کار بدهد
- `/azmoon d01` → باید آزمون شروع شود
- رزومه بفرست → باید در PV ربات جواب بدهد (نه گروه)

---

## 👥 گروه تلگرام + OT — چطور بسازی

**گروه بحث @joblink_group:**
1. تلگرام → New Group → 2 نفر اضافه → نام: `JobLink Group — بحث و پشتیبانی` → آیدی: `joblink_group` → Public
2. Add member → @joblink_bot
3. Make Admin → ✅ Delete messages
4. توضیحات گروه از `BOT-CHANNEL-SETUP-FA.md`

**گروه OT خصوصی @joblink_ot_private:**
1. New Group → Private → نام: `JobLink OT Private`
2. فقط شما + 2-3 منتور + @joblink_bot
3. برای هماهنگی عملیاتی — آگهی مشکوک، سوال حقوقی سخت

---

## ✅ چک نهایی — HuggingFace کار می‌کند؟

| بخش | لینک | وضعیت |
|---|---|---|
| **دیتابیس** | `data/knowledge/knowledge.db` 660KB 9 جدول + 20 emb + `hf_dataset.jsonl` 519 ردیف | ✅ OK — آماده push به `hf.co/datasets/sosa123454321/joblink-knowledge-fa-tr` |
| **مدل‌ها** | Qwen3-0.6B, bge-m3, e5-large, Llama-3.1-8B | ✅ 5 embedding + 1 LLM Live OK — تست با hulevin |
| **Space** | `spaces/app.py` 10 تب + logo.png + banner.png | ✅ OK — LIVE PREVIEW port 7860 — https://7860-...e2b.app |
| **OS Runner** | Local + HF Space runner | ✅ Local OK, HF Space نیاز به HF_TOKEN secret |
| **ربات** | @joblink_bot → https://t.me/joblink_bot | ⏳ باید بسازی — نام دقیق داده شد |
| **کانال** | @joblink_tr_ir → https://t.me/joblink_tr_ir | ⏳ باید بسازی |
| **گروه** | @joblink_group → https://t.me/joblink_group | ⏳ باید بسازی — ربات ادمین |
| **OT گروه** | @joblink_ot_private → https://t.me/joblink_ot_private | ⏳ باید بسازی — private |
| **لوگو** | assets/logo.png + banner.png | ✅ ساخته شد — 504KB + 1.6MB |

---

## 🎯 اقدام فوری — 5 دقیقه

1. **ربات بساز:** BotFather → /newbot → `joblink_bot` → آپلود logo.png
2. **کانال بساز:** @joblink_tr_ir + logo + توضیحات
3. **گروه بساز:** @joblink_group + ربات ادمین + Group Privacy Turn off
4. **OT بساز:** @joblink_ot_private private
5. **HF push:** `huggingface-cli upload ...` + Space deploy + Secrets HF_TOKEN

**همه نام‌ها و لینک‌ها دقیق داده شد — فقط بساز و لینک‌ها فعال می‌شوند**
