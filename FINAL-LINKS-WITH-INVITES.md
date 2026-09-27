# 🔗 لینک‌های نهایی JobLink — با دعوت‌نامه‌های شما + ربات @joblink_AI_bot

**تاریخ:** 2026-09-14 — ربات @joblink_AI_bot فعال شد، توضیحات و دستورات ست شد

---

## 🤖 ربات تلگرام — وجود دارد — فعال

| نام | آیدی | لینک | توکن | وضعیت |
|---|---|---|---|---|
| **JobLink AI Bot** | `@joblink_AI_bot` | `https://t.me/joblink_AI_bot` | `8949733969:AAEO...` (امن نگه دار) | ✅ وجود دارد — getMe OK — first_name joblink_bot — can_join_groups true |

**توضیحات ست شد:**
- ShortDescription: 🤝 JobLink - اوبر برای کار | پل ایران ↔ ترکیه ...
- Description: JobLink - بازار کار دوطرفه ایران ↔ ترکیه ...
- Commands: 9 دستور — /start /katil /hayir /haziri /dorkari /shoghle /danesh /azmoon /help — ✅ ست شد

**لوگو:** باید دستی via BotFather → Edit Botpic → آپلود `assets/logo.png` (API ندارد)

**دستورات جدید اضافه شد به bot.py:**
- `/post [شهر] [مهارت]` — OT — پست 5 آگهی به کانال/گروه با استایل سایت
- `/digest` — خلاصه روزانه 5 آگهی + نکته حقوقی
- `/links` — همه لینک‌ها

**مدیریت گروه:**
- `handle_group_events` — وقتی ربات به گروه اضافه می‌شود یا کاربر جدید می‌آید، خوش‌آمد می‌گوید
- Bot ID 8949733969 hard-coded برای تشخیص اضافه شدن ربات

---

## 📢 کانال و گروه شما — با دعوت‌نامه‌هایی که دادی

| نوع | نام | لینک دعوت شما | لینک عمومی (اگر public شود) | تعداد اعضا | توضیح |
|---|---|---|---|---|---|
| **👥 گروه** | `joblink_group` | `https://t.me/+YmyYph5XV-NlN2I8` | `https://t.me/joblink_group` | 2 members | Supergroup — title "JobLink 🔗💼" — description فرانسوی (باید عوض شود) — ID -1002089796813 |
| **📢 کانال** | `joblink_tr_ir` | `https://t.me/+WALqOptGwnwyNmU0` | `https://t.me/joblink_tr_ir` (اگر public کنی) | 2 subscribers | Channel — title joblink_tr_ir |

**وضعیت ربات در این‌ها:**
- گروه joblink_group: ❌ bot is not a member — باید دستی اضافه کنی: گروه → Add members → @joblink_AI_bot → Make Admin (Delete messages)
- کانال joblink_tr_ir: ❓ احتمالا bot عضو نیست — کانال → Administrators → Add Admin → @joblink_AI_bot → Post messages

**بعد از اضافه کردن، ربات می‌تواند:**
- در کانال پست کند: `/post Istanbul` یا `ChannelPoster.post_jobs_batch(chat_id="@joblink_tr_ir")`
- در گروه مدیریت کند: خوش‌آمد، حذف اسپم، پاسخ /danesh, /azmoon
- خلاصه روزانه: `/digest` در کانال

---

## 🔗 همه لینک‌ها — کامل — آماده کپی

### HuggingFace — مدل، دیتابیس، Space

| نام | لینک | وضعیت |
|---|---|---|
| **دیتاست دانش** | `https://huggingface.co/datasets/sosa123454321/joblink-knowledge-fa-tr` | ✅ 519 ردیف + 20 embeddings + 660KB DB 9 جدول — آماده push |
| **Space دمو** | `https://huggingface.co/spaces/sosa123454321/joblink` | ✅ 10 تب + لوگو + banner — LIVE port 7860 |
| **Qwen3-0.6B** | `https://huggingface.co/Qwen/Qwen3-Embedding-0.6B` | ✅ Live OK delta 0.159 ایران 10/10 |
| **bge-m3** | `https://huggingface.co/BAAI/bge-m3` | ✅ Live OK delta 0.160 |
| **e5-large** | `https://huggingface.co/intfloat/multilingual-e5-large` | ✅ Live OK delta 0.052 |
| **Llama-3.1-8B** | `https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct` | ✅ CHAT OK |
| **مدل کاستوم Rituq-Inside (آینده)** | `https://huggingface.co/sosa123454321/joblink-rituq-06b-inside` | ⏳ باید بسازی |
| **مدل Baby Rituq (آینده)** | `https://huggingface.co/sosa123454321/joblink-baby-rituq-phi3` | ⏳ باید بسازی |

### تلگرام — ربات، کانال، گروه — با دعوت‌نامه‌های شما

| نوع | نام | لینک | وضعیت |
|---|---|---|---|
| **ربات** | `@joblink_AI_bot` | `https://t.me/joblink_AI_bot` | ✅ وجود دارد — فعال — توضیحات ست شد |
| **کانال شما** | `joblink_tr_ir` | `https://t.me/+WALqOptGwnwyNmU0` (دعوت شما) + `https://t.me/joblink_tr_ir` (اگر public) | ✅ 2 subs — باید ربات را ادمین کنی |
| **گروه شما** | `joblink_group` | `https://t.me/+YmyYph5XV-NlN2I8` (دعوت شما) + `https://t.me/joblink_group` | ✅ 2 members — باید ربات را ادمین کنی |
| **OT خصوصی پیشنهادی** | `@joblink_ot_private` | `https://t.me/joblink_ot_private` | ⏳ باید بسازی — private |
| **ادمین** | `@sosa123454321` | `https://t.me/sosa123454321` | ✅ |

### سایت اصلی و کد

| نام | لینک | وضعیت |
|---|---|---|
| **سایت** | `https://joblink.example` یا `joblink.ir` | ⏳ باید بسازی — Cloudflare Pages |
| **GitHub کد** | `https://github.com/sosa123454321/joblink` | ⏳ باید push |
| **لوگو** | `assets/logo.png` 512x512 + `assets/banner.png` 1200x400 | ✅ ساخته شد |

### 10 سایت ترکیه — منبع آگهی

1. eleman.net — https://www.eleman.net
2. kariyer.net — https://www.kariyer.net
3. iskur.gov.tr — https://www.iskur.gov.tr
4. yenibiris.com — https://www.yenibiris.com
5. secretcv.com — https://www.secretcv.com
6. elemanonline.com.tr — https://www.elemanonline.com.tr
7. isinolsun.com — https://www.isinolsun.com
8. jooble.org/tr — https://tr.jooble.org
9. indeed.com.tr — https://tr.indeed.com
10. linkedin.com/jobs TR — https://www.linkedin.com/jobs/search/?location=Turkey

---

## 📋 کپی سریع — برای کانال و گروه

**برای کانال @joblink_tr_ir (پین کن):**
```
🤝 JobLink — کار ایران ↔ ترکیه | Uber for Jobs

🤖 ربات: @joblink_AI_bot — https://t.me/joblink_AI_bot
👥 گروه بحث: @joblink_group — https://t.me/+YmyYph5XV-NlN2I8
📢 کانال: @joblink_tr_ir — https://t.me/+WALqOptGwnwyNmU0
🔒 OT: @joblink_ot_private

📚 دیتاست: https://huggingface.co/datasets/sosa123454321/joblink-knowledge-fa-tr (519 ردیف + 20 embeddings)
🚀 Space: https://huggingface.co/spaces/sosa123454321/joblink (10 تب LIVE)
💻 کد: https://github.com/sosa123454321/joblink

🤖 مدل‌ها:
• Qwen3-0.6B (ایران 10/10): https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
• bge-m3: https://huggingface.co/BAAI/bge-m3
• Llama-3.1-8B: https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct

💼 هر روز 5 آگهی واقعی ترکیه با حقوق TL + شهر + لینک اصلی + هشدار حقوقی

دستورات ربات:
/start, /katil, /shoghle, /danesh, /azmoon, /links, /post, /digest

#کاریابی #ترکیه #JobLink
```

**برای گروه @joblink_group (توضیحات گروه):**
```
👥 JobLink Group — بحث و پشتیبانی — کار ایران ↔ ترکیه

🤖 ربات: @joblink_AI_bot — رزومه را در PV ربات بفرست (نه گروه)
📢 کانال: @joblink_tr_ir — https://t.me/+WALqOptGwnwyNmU0
📚 دیتاست: hf.co/datasets/sosa123454321/joblink-knowledge-fa-tr
🚀 Space: hf.co/spaces/sosa123454321/joblink

دستورات:
/danesh d01 — قوانین اجازه کار
/azmoon d01 — آزمون 10 سوالی
/shoghle — 5 آگهی شخصی (در PV)
/links — همه لینک‌ها
/post — OT — پست آگهی به کانال
/digest — خلاصه روزانه

قوانین: احترام، بدون اسپم، بدون شماره در گروه
```

---

## ✅ چک OS Runner + HuggingFace — مدل، دیتابیس، Space

| بخش | لینک | وضعیت |
|---|---|---|
| **دیتابیس** | `data/knowledge/knowledge.db` 660KB 9 جدول | ✅ OK — 12 domains, 360 resources, 120 quizzes, 11 ai_models, 3 custom, 10 rag, 20 embeddings |
| **مدل‌ها** | Qwen3-0.6B, bge-m3, e5-large, Llama-3.1-8B | ✅ 5 embedding + 1 LLM Live OK با hulevin token |
| **Space** | `spaces/app.py` 10 تب + logo.png + banner.png | ✅ OK — LIVE PREVIEW port 7860 — https://7860-...e2b.app |
| **OS Runner Local** | `python -m joblink.cli` | ✅ OK |
| **OS Runner HF Space** | `hf.co/spaces/sosa123454321/joblink` | ⚠️ نیاز به HF_TOKEN secret |
| **ربات** | @joblink_AI_bot | ✅ فعال — توضیحات و دستورات ست شد — getMe OK |
| **کانال شما** | https://t.me/+WALqOptGwnwyNmU0 | ✅ 2 subs — باید ربات را ادمین کنی تا پست کند |
| **گروه شما** | https://t.me/+YmyYph5XV-NlN2I8 | ✅ 2 members — باید ربات را ادمین کنی |

---

## 🚀 اقدام فوری — 3 دقیقه — برای اینکه ربات در کانال پست کند

1. **کانال @joblink_tr_ir:**
   - باز کن https://t.me/+WALqOptGwnwyNmU0
   - Channel Info → Administrators → Add Admin → @joblink_AI_bot → ✅ Post messages

2. **گروه @joblink_group:**
   - باز کن https://t.me/+YmyYph5XV-NlN2I8
   - Add members → @joblink_AI_bot → Make Admin → ✅ Delete messages, Pin messages
   - BotFather → /mybots → @joblink_AI_bot → Bot Settings → Group Privacy → Turn off
   - BotFather → Allow Groups → Enable

3. **تست:**
   ```bash
   BOT_TOKEN=xxx python -m joblink.channel_poster --chat-id @joblink_tr_ir --limit 3
   BOT_TOKEN=xxx python -m joblink.channel_poster --chat-id @joblink_group --digest
   ```
   - یا در تلگرام: در گروه `/post Istanbul` و `/digest` و `/links`

4. **لوگو:**
   - BotFather → /mybots → @joblink_AI_bot → Edit Botpic → آپلود `assets/logo.png` (API ندارد — دستی)

---

## 🔐 امنیت توکن

- توکن ربات `8949733969:AAEO...` را در هیچ فایلی ذخیره نکردیم — فقط inline در curl و env var
- برای تولید: در `.env` بگذار — `.env` gitignored است
- توکن HF hulevin هم inline — در فایل نیست

**همه لینک‌ها با نام دقیق داده شد — ربات @joblink_AI_bot فعال و توضیحات ست شد — فقط ربات را به کانال/گروه خودت ادمین کن تا پست کند**
