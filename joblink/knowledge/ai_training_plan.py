"""برنامه آموزش مدل شخصی‌سازی شده JobLink برای ایران - قابل اجرا روی HF Spaces"""

TRAINING_PLAN_FA = """
# برنامه آموزش مدل هوش مصنوعی شخصی‌سازی شده JobLink برای ایران

## 1. هدف مدل
یک مدل دوکاره:
- **Embedder**: فارسی/ترکی/انگلیسی → یک فضای برداری مشترک برای تطبیق شغل (جایگزین BM25)
- **RAG Explainer**: توضیح فارسی چرا یک آگهی به کارجو می‌خورد + چه فاصله‌ای دارد

## 2. معماری پیشنهادی (با توجه به تحریم و اینترنت ایران)

### مرحله A: Embeddings (اولویت 1)
- **Base**: intfloat/multilingual-e5-large (1024 dim) - روی HF Inference Providers live است (تست شد)
- **چرا نه base**: multilingual-e5-base هیچ provider ندارد (null) - تست کردیم
- **Alternative**: jinaai/jina-embeddings-v3 (مصرف کمتر، سریع‌تر) یا Qwen3-Embedding-0.6B (سبک برای ایران)
- **Fine-tune strategy**:
  1. ساخت golden dataset 500 جفت: (رزومه فارسی → آگهی ترکی مثبت/منفی)
  2. استفاده از همین LEXICON 70 مهارت + ESCO 13k به عنوان weak supervision
  3. Contrastive loss: (query: رزومه) vs (passage: آگهی) با instruction فارسی:
     "Instruct: یک شغل مناسب برای این رزومه پیدا کن\\nQuery: {cv}"
  4. آموزش با SentenceTransformers روی HF Space T4 (رایگان) یا داخل ایران با 1x 4090

### مرحله B: RAG / LLM Explainer (اولویت 2)
- **Base LLM**: Llama-3.1-8B-Instruct یا Qwen2.5-7B (هر دو روی HF Router pricing $0.02/1M input)
- **RAG corpus**: همین knowledge base 12 حوزه (360 منبع + 120 سوال) + 97 آگهی زنده + 14 رزومه مصنوعی
- **Prompt template**:
```
تو یک مشاور شغلی برای ایرانیان متقاضی کار در ترکیه هستی.
رزومه: {cv}
آگهی: {job}
قوانین مرتبط: {domain knowledge chunk}
وظیفه: امتیاز 0-100 بده، 3 مهارت هم‌پوشان، 2 فاصله، و هشدار حقوقی اگر حضوری است.
```
- **Hallucination guard**: 
  - اگر حقوق <26,005 TL → flag below-minimum-wage
  - اگر حضوری و open_to_relocate=False → بگو /haziri لازم است
  - اگر آگهی بدون بیمه SGK → هشدار

### مرحله C: اجرا در ایران (تحریم‌محور)
- **مشکل**: HF Inference از ایران فیلتر است، API نیاز به توکن با scope Inference Providers دارد (توکن فعلی کاربر فاقد scope است → 403)
- **راه‌حل 1 (توصیه)**: مدل را به صورت ONNX / GGUF export کن، روی یک VPS ایران (مثل پارس‌پک، ایران‌سرور) با CPU inference اجرا کن
  - e5-large ONNX ~ 1.2GB، با optimum می‌شود 300MB quantized
- **راه‌حل 2**: استفاده از Cloudflare Workers AI (مدل bge-m3) به عنوان پروکسی - از ایران قابل دسترس‌تر است
- **راه‌حل 3**: HF Space را به صورت private + proxy نگه دار، ربات تلگرام از طریق Space صدا بزند (نه مستقیم HF)

## 3. دیتاست برای HF Hub

نام پیشنهادی: `sosa123454321/joblink-knowledge-fa-tr`

فایل‌ها:
- `hf_dataset.jsonl` (این فایل الان در data/knowledge موجود است) - 12 domain + 360 resource + 120 quiz = ~492 ردیف
- `domains.json`, `resources.json`, `quizzes.json`
- `README.md` با dataset card فارسی

**Dataset card** باید شامل:
- زبان‌ها: fa, tr, en
- لایسنس: CC-BY-4.0 برای دانش، MIT برای کد
- نحوه استفاده: `load_dataset("json", data_files="hf_dataset.jsonl")`
- ارزیابی: Recall@5 روی 14 رزومه مصنوعی

## 4. هزینه واقعی (اندازه‌گیری شده)

از `ai-check`:
- 84 آگهی → ~36k tokens embedding
- 84 توضیح → ~33.6k tokens LLM → $0.000672 با قیمت novita
- Free tier HF: $0.10/month → برای 500 درخواست کافی نیست، باید PRO $9 → $2 credit
- Cloudflare Workers AI: 10k tokens/day رایگان، بعد $5/1M tokens

## 5. آزمون تلگرام - اتصال به آموزش

هر کارجو بعد از /katil می‌تواند /azmoon بزند:
- 10 سوال تصادفی از حوزه مرتبط با شغلش (مثلا جوشکار → d07 ایمنی + d01 اجازه کار)
- اگر 7/10 بگیرد → badge "آگاه به حقوق" و اولویت در نمایش به کارفرما
- این داده به fine-tune برمی‌گردد: سوالاتی که زیاد غلط جواب داده می‌شود → توضیح RAG بهتر شود

## 6. نقشه راه 4 هفته‌ای

هفته 1: انتشار دیتاست روی HF Hub + تست embedding با توکن درست (scope Inference Providers)
هفته 2: fine-tune e5-large روی 500 جفت fa→tr با 5 epoch، ارزیابی Recall@k
هفته 3: اتصال به ربات: /azmoon + /danesh + نمایش منبع حقوقی در هر مچ
هفته 4: ONNX export + استقرار روی VPS ایران + Cloudflare Worker به عنوان fallback

## 7. ملاحظات اخلاقی برای ایران

- **حریم خصوصی**: رزومه‌ها هرگز در دیتاست عمومی HF نروند؛ فقط دانش عمومی + آگهی‌های عمومی
- **سوگیری**: تست کن که مدل زن/مرد، ترک/کرد/فارس را تبعیض ندهد (آزمون d04)
- **تحریم**: هیچ پرداخت دلاری از داخل ایران انجام نشود؛ از طریق ترکیه یا HF Free استفاده شود
- **شفافیت**: هر جواب AI باید بگوید "این توضیح توسط AI تولید شده" (EU AI Act Art 50)
"""

def get_plan():
    return TRAINING_PLAN_FA

# برای استفاده در CLI
def print_plan():
    print(TRAINING_PLAN_FA)
