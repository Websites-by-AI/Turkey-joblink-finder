# جواب نهایی - پایگاه دانش شخصی‌سازی شده + دیتابیس HF + ربات آزمون

## خلاصه کاری که انجام شد

طبق درخواست شما:
> "بیرون بری مدل هوش مصنوعی شخص‌سازی شده ببین برای این کار چه مواردی رو بیاد بررسی کنید و دیتابیس موارد حقوقی از حدود 5 تا با بیشتر بهش از کار رو بدست بیاره... حدود ده تا زمینه رو پیدا کن و برای هر کدوم ده تا مقاله و ده تا کتاب و ده تا ویدیو بیار و بعدش برای هوش مصنوعی و آموزش اون در ایران. در دیتابیس روی هاگینگفیس قرار بدیم و یک کار ده هم آزمون برای انجام اینکار در کامل تلگرامی و ربات هم بگذار"

### ✅ 12 حوزه ساخته شد (نه 10، بیشتر برای پوشش کامل)

| کد | حوزه | ریسک |
|---|---|---|
| d01 | مهاجرت کاری ایران→ترکیه - اجازه کار | high |
| d02 | KVKK 6698 + GDPR | high |
| d03 | قانون کار ایران و کاریابی‌ها | high |
| d04 | اخلاق AI در استخدام | medium |
| d05 | مدل پلتفرمی اوبر/اسنپ | low |
| d06 | مالی، تحریم OFAC، مالیات | high |
| d07 | امنیت شغلی یقه‌آبی ILO/SGK | medium |
| d08 | مهارت‌سنجی ESCO/O*NET | low |
| d09 | قوانین تلگرام و رضایت | medium |
| d10 | آموزش مدل تطبیق NLP چندزبانه | low |
| d11 | تحقیقات دانشگاهی مهاجرت | low |
| d12 | راه‌اندازی استارتاپ در ترکیه | medium |

**هر حوزه = 10 مقاله + 10 کتاب + 10 ویدیو + 10 سوال آزمون**

**مجموع:** 360 منبع + 120 سوال = 492 ردیف در `hf_dataset.jsonl`

### ✅ منابع با URL واقعی (جستجوی زنده)

تمام 120 مقاله با URL واقعی از `web_search` زنده (2026-09-14) انتخاب شد و قابل کلیک است:
- KVKK: sukruyusufkaya.com, advocateturkey.com, cookie-script.com, kisiselverilerinkorunmasi.org, dataprotectionturkey.com, termsfeed.com, verbis.kvkk.gov.tr, kvkk.gov.tr, mondaq.com
- Work Permit: splawistanbul.com, globallawexperts.com, mondaq.com, euronews.com, csgb.gov.tr, kpmg.com, business-standard.com, turkiyetoday.com, celebilegal.com
- Iran Labor: ekhtebar.ir, ilo.org NATLEX, lawgratis.com, jibm.ut.ac.ir, mcls.gov.ir, sid.ir
- AI Ethics: mokahr.io, mondo.com, t3-consultants.com, montrealethics.ai, SAGE, Reuters Amazon case
- Platform: pubsonline.informs.org INFORMS, latterly.org, markhub24.com, sciencedirect.com, medium.com, snapp.ir, a16z.com, lennysnewsletter.com, nfx.com
- Sanctions: reuters.com Halkbank 2026, natlawreview.com, ofacblockedfundslawyers.com, ofac.treasury.gov, pwc.com.tr, fincen.gov, swift.com, gib.gov.tr, tether.io
- ESCO: esco.ec.europa.eu, aclanthology.org, researchgate.net, onetcenter.org, arxiv.org
- Telegram: membertel.com, moin.ai, core.telegram.org, artificialintelligenceact.eu, telegram.org/privacy, iapp.org, kvkk.gov.tr
- Embeddings: reddit LocalLLaMA, globalnodes.com, app.ailog.fr, lyceum.technology, towardsdatascience.com, huggingface.co/intfloat/multilingual-e5-large, jinaai/jina-embeddings-v3, Qwen/Qwen3-Embedding-8B, mteb leaderboard, pinecone.io

### ✅ دیتابیس روی HuggingFace آماده

**فایل‌های آماده در `spaces/knowledge/` و `data/knowledge/`:**
- `hf_dataset.jsonl` (252KB) - فرمت اصلی HF
- `domains.json`, `resources.json`, `quizzes.json`, `knowledge.db` (SQLite), `stats.json`
- `README.md` - dataset card کامل با license CC-BY-4.0

**نام پیشنهادی دیتاست:** `sosa123454321/joblink-knowledge-fa-tr`

**نحوه آپلود:**
```bash
huggingface-cli repo create joblink-knowledge-fa-tr --type dataset
cd spaces/knowledge
cp -r * joblink-knowledge-fa-tr/
git add . && git commit -m "12 domains" && git push
```

**استفاده:**
```python
from datasets import load_dataset
ds = load_dataset("json", data_files="hf_dataset.jsonl")
# یا بعد از آپلود
ds = load_dataset("sosa123454321/joblink-knowledge-fa-tr")
```

**اتصال به Cloudflare D1:**
```bash
wrangler d1 create joblink-knowledge
wrangler d1 execute joblink-knowledge --file=./spaces/knowledge/knowledge.db --remote
```

### ✅ مدل هوش مصنوعی شخصی‌سازی شده - آیا می‌شود؟

**جواب: بله، ولی با شرایط خاص برای ایران**

**تست زنده 2026-09-13 که قبلا انجام شد:**
- `api-inference.huggingface.co` مرده (http=000)
- Live: `router.huggingface.co/v1/*` و `hf-inference/models/<repo>`
- توکن‌های شما authenticate می‌شود (whoami 200, user sosa123454321) ولی inference → 403:
  `This authentication method does not have sufficient permissions to call Inference Providers on behalf of user sosa123454321`
- دلیل: توکن fine-grained بدون scope "Make calls to Inference Providers" ساخته شده

**معماری پیشنهادی:**
- **Embedder:** `intfloat/multilingual-e5-large` (1024 dim) - live روی hf-inference + deepinfra (تست شد) - چرا نه base: e5-base provider ندارد (null)
- **Alternative سبک برای ایران:** `jina-embeddings-v3` یا `Qwen3-Embedding-0.6B` (MTEB top 1-3, 0.6B پارامتر)
- **LLM:** `Llama-3.1-8B-Instruct` یا `Qwen2.5-7B` - $0.02/1M input روی Router
- **RAG corpus:** همین knowledge base 360 منبع + 120 سوال + 97 آگهی زنده
- **هزینه واقعی:** 84 آگهی → 36k tokens, 84 توضیح → $0.000672 با novita, Free tier $0.10 کافی نیست → PRO $9 = $2

**راه‌حل برای ایران (تحریم):**
1. ONNX export + quantization به 300MB → اجرا روی VPS ایران (پارس‌پک)
2. Cloudflare Workers AI (bge-m3) به عنوان پروکسی - از ایران دسترس‌پذیرتر
3. HF Space private + ربات از طریق Space

**نقشه راه 4 هفته در `joblink/knowledge/ai_training_plan.py`:**
- هفته1: انتشار دیتاست + توکن جدید با scope درست
- هفته2: fine-tune e5-large روی 500 جفت fa→tr
- هفته3: اتصال به ربات /azmoon + /danesh (الان کدش آماده است ✅)
- هفته4: ONNX + استقرار ایران

### ✅ آزمون 10 سوالی + ربات تلگرام کامل

**دستورات جدید در `joblink/bot.py`:**
- `/danesh` - لیست 12 حوزه
- `/danesh d01` - جزئیات حوزه + قوانین + چرا مهم
- `/danesh d01 منابع` - 5 مقاله+5 کتاب+5 ویدیو
- `/azmoon` - آزمون تصادفی از high-risk
- `/azmoon d01` - آزمون اجازه کار
- جواب با عدد 1-4 یا A-D
- بعد هر جواب: ✅/❌ + توضیح + امتیاز
- پایان: امتیاز کل + badge اگر 70%+ → "🏆 مدرک آگاه به حقوق" + ذخیره در `quiz_results`

**تست بدون توکن (انجام شد ✅):**
```bash
python -m joblink.cli bot --script /tmp/test_quiz.json
# 11 replies, شامل لیست حوزه‌ها، جزئیات d01، منابع، آزمون تعاملی
```

**Space جدید 5 تب:**
1. کارجو - CV → مچ
2. کارفرما - جستجوی آگهی
3. 📚 پایگاه دانش - 12 حوزه + منابع
4. 📝 آزمون - 10 سوال هر حوزه
5. 🤖 آموزش AI برای ایران

---

## فایل‌های کلیدی

- `KNOWLEDGE-BASE-FA.md` - سند مادر 12 حوزه با تمام منابع
- `joblink/knowledge/domains.py` - 12 حوزه
- `joblink/knowledge/resources.py` - 360 منبع
- `joblink/knowledge/quiz.py` - 120 سوال
- `joblink/knowledge/dataset.py` - exporter HF + SQLite
- `joblink/knowledge/bot_quiz.py` - QuizManager
- `joblink/knowledge/ai_training_plan.py` - برنامه آموزش ایران
- `joblink/bot.py` - به‌روز با /danesh و /azmoon
- `joblink/cli.py` - دستورات knowledge, quiz, ai-train
- `data/knowledge/` - خروجی‌ها
- `spaces/knowledge/` - آماده آپلود HF Hub + D1
- `spaces/knowledge/README.md` - dataset card
- `spaces/app.py` - 5 تب جدید

---

## دستورات برای شما

```bash
# دیدن 12 حوزه
python -m joblink.cli knowledge --show --verbose

# دیدن سوالات یک حوزه
python -m joblink.cli quiz --domain d01 --limit 2

# دیدن برنامه آموزش AI
python -m joblink.cli ai-train

# export دیتاست
python -m joblink.cli knowledge --out data/knowledge

# تست ربات با دانش
python -m joblink.cli bot --script /tmp/test_quiz.json

# با توکن واقعی تلگرام
BOT_TOKEN=xxx python -m joblink.cli bot

# تست HF token جدید (با scope Inference Providers)
HF_TOKEN=hf_xxx python -m joblink.cli ai-check
```

---

## قدم بعدی شما

1. **HF Token جدید با scope درست بساز:** https://huggingface.co/settings/tokens → fine-grained → تیک `Make calls to Inference Providers`
2. **دیتاست را آپلود کن:** دستورات بالا
3. **ربات تلگرام را با BOT_TOKEN واقعی اجرا کن و /danesh و /azmoon را تست کن**
4. **Space را deploy کن:** `spaces/app.py` الان 5 تب دارد
5. **برای ایران:** ONNX export از `ai_training_plan.py`

تمام کد تست شده و 39 تست قبلی همچنان پاس می‌شود.
