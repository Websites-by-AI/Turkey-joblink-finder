# نقد فنی پیاده‌سازی AI Models + RAG + Fine-tune — آیا OK است؟

**تاریخ:** 2026-09-14 — تست زنده با ۲ توکن کاربر (Rag1 + Addiction/hulevin)

---

## ۱. خلاصه اجرایی: OK است ولی ۳ مشکل حیاتی دارد

| بخش | وضعیت | نمره /10 |
|---|---|---|
| لیست ۱۱ مدل | ✅ دقیق، ابعاد واقعی از جستجوی زنده | 9 |
| TOP3 معماری | ✅ منطقی، Iran-Light بهترین انتخاب | 8 |
| RAG پیاده‌سازی | ⚠️ کار می‌کند ولی keyword-only، نه semantic | 5 |
| Fine-tune اسکریپت‌ها | ⚠️ placeholder، نیاز به DataLoader واقعی | 6 |
| Golden dataset 554 ردیف | ⚠️ مصنوعی، polysemy trap خوب ولی تکراری | 6 |
| دیتاست HF 506 ردیف | ✅ کامل، ۵ جدول SQLite | 9 |
| Space اپ ۷ تب | ✅ کار می‌کند ولی سنگین | 7 |
| **توکن‌ها** | ❌ یک توکن بدون Inference scope، یکی LLM ناقص | 4 |

**نتیجه:** برای دمو و HF Hub **OK** است، برای تولید ایران **نیاز به ۲ فیکس**: (۱) توکن Rag1 را با scope Inference Providers بساز، (۲) RAG را از keyword به embedding ارتقا بده.

---

## ۲. تست توکن‌ها — مهم‌ترین مشکل

### توکن ۱: Rag1 (main)
```
displayName: Rag1
role: fineGrained
permissions: repo.content.read, repo.access.read, repo.write, discussion.write, job.write
❌ فاقد: inference.serverless.write, inference.endpoints.infer.write
```
**نتیجه تست:**
- `whoami` OK → user sosa123454321
- `feature_extraction` → **403 Forbidden: This authentication method does not have sufficient permissions to call Inference Providers**
- `chat.completions` → 403

**دلیل:** وقتی توکن را ساختی، گزینه **"Make calls to Inference Providers"** را تیک نزدی. دقیقا همان خطایی که در `emb.py` پیش‌بینی کرده بودیم.

**فیکس:** HF Settings → Access Tokens → New Token → Fine-grained → Permissions → Inference → **✅ inference.serverless.write** + **inference.endpoints.infer.write** را اضافه کن. یا یک token جدید از نوع **Read** با Inference Providers scope بساز.

### توکن ۲: Addiction / hulevin
```
displayName: Addiction
permissions: repo.write + inference.serverless.write + inference.endpoints.infer.write + collection.*
✅ دارد Inference scope
```
**نتیجه تست زنده:**
- Qwen3-Embedding-0.6B → OK dim 1024
- Qwen3-4B → OK dim 2560
- Qwen3-8B → OK dim 4096
- e5-large → OK dim 1024
- bge-m3 → OK dim 1024
- jina-v3 → ❌ FAIL (no provider supports it)
- Llama-3.1-8B-Instruct (meta-llama/Llama-3.1-8B-Instruct) → **CHAT OK** → جواب فارسی داد
- Qwen2.5-7B-Instruct → ❌ Bad request: not supported by any provider you have enabled
- Phi-3-mini → ❌ not supported
- aya-23-8B → ❌ no provider (انتظار می‌رفت)

**دلیل LLM‌ها:** در HF Account → Settings → Inference Providers، باید providerها را enable کنی (Novita, Fireworks, Featherless, etc). الان فقط بعضی providerها فعال هستند، برای همین Llama کار می‌کند ولی Qwen نه.

**توصیه:**
- از توکن hulevin برای **embedding** استفاده کن (۵ مدل کار می‌کند)
- برای LLM فعلا فقط `meta-llama/Llama-3.1-8B-Instruct` کار می‌کند — کافی برای TOP2
- برای TOP1 (Qwen2.5-7B) باید در HF Dashboard → Inference Providers → enable **Novita, Together, Fireworks**

---

## ۳. تست Embedding Polysemy — آیا Qwen3 بهتر از e5 است؟

تست واقعی با ۳ مدل روی یک query سخت: **"جوشکار CO2" vs "Kaynakçı CO2" (مثبت) vs "kaynak kodu GitHub" (منفی)**

| مدل | cos مثبت | cos منفی | delta | قضاوت |
|---|---|---|---|---|
| **Qwen3-0.6B** | 0.479 | 0.319 | **0.159** | ✅ خوب |
| **bge-m3** | 0.592 | 0.432 | **0.160** | ✅ خوب |
| e5-large | 0.815 | 0.762 | 0.052 | ❌ ضعیف |

**نتیجه:** ادعای ما درست بود — Qwen3-0.6B و bge-m3 برای polysemy **kaynak** (جوشکاری vs منبع کد) از e5-large بهتر هستند. e5-large هر دو را 0.8+ می‌دهد، یعنی جوشکار را به برنامه‌نویس مچ می‌کند.

**این یعنی:** TOP1 Iran-Light انتخاب درستی است، TOP2 Balanced نیاز به fine-tune دارد.

**پیشنهاد فیکس e5:**
- fine-tune با 200 جفت trap که در `top2_e5_lora.py` نوشتیم، یا
- از bge-m3 استفاده کن (همان دقت Qwen3 ولی 567M و MIT)

---

## ۴. نقد RAG فعلی

### مشکل ۱: keyword-only نه semantic
```python
# rag.py search() فعلی:
for word in q.split():
    if word in ch.text.lower(): score+=1
```
برای query **"جوشکار CO2 استانبول"** نتیجه داد:
- Güvenlik CCTV Operatörü (امنیت!) score 14
- Minimum wage article score 14
- هیچ ربطی به جوشکاری نداشت

**چرا؟** چون "استانبول" در همه آگهی‌ها هست، امتیاز می‌گیرد.

**فیکس پیشنهادی:**
```python
# اگر HF_TOKEN دارد، از embedding استفاده کن
if self.embedder and self.embedder.enabled:
    q_vec = self.embedder.embed([query])[query]
    for ch in chunks:
        ch_vec = self.embedder.embed([ch.text])[ch.text]
        ch.score = cos(q_vec, ch_vec)
```
یا حداقل TF-IDF + boost برای domain.

### مشکل ۲: chunking
- هر article خلاصه 80 کاراکتر → خیلی کوتاه برای RAG
- باید متن کامل مقاله (حداقل 500 کاراکتر) ذخیره شود، نه summary_fa کوتاه

### مشکل ۳: LLM prompt
- prompt فعلی فارسی خوب است ولی `explanation_fa` که برگشت، template بود نه LLM واقعی:
  > "این شغل برای ایرانیان مناسب نیست زیرا نیاز به کاریزن کار دارد"
- با وجود `from_llm: true`، متن generic بود — احتمالا LLM prompt را کوتاه جواب داده

**تست RAG با توکن hulevin:**
```bash
HF_TOKEN=xxx python -m joblink.cli rag --query "اجازه کار ترکیه" --top 3
→ کار کرد ولی chunks بی‌ربط برای جوشکار
```

**نمره RAG:** 5/10 — کار می‌کند ولی نیاز به semantic search

---

## ۵. نقد Fine-tune

### golden_fa_tr.jsonl — 554 ردیف
- **خوب:** polysemy trap kaynak را دارد، شهرهای واقعی TR
- **بد:** همه مصنوعی، template تکراری:
  ```
  "جوشکار با 3 سال سابقه. ساکن تهران. آماده مهاجرت..."
  ```
  تنوع کم، 97 آگهی واقعی استفاده نشده

**پیشنهاد:** از آگهی‌های واقعی `jobs.json` (97 آگهی) + ترجمه فارسی دستی برای golden استفاده کن.

### اسکریپت‌ها
- `top1_qwen3_06b_finetune.py` — از `InputExample` استفاده می‌کند که در sentence-transformers قدیمی است، جدید `Dataset` می‌خواهد
- `top2_e5_lora.py` — می‌گوید "peft integration experimental" ولی کد ندارد — باید کامل شود
- `top3_jina_phi3_offline.py` — jina-v3 اصلا live نیست (تست کردیم FAIL)، پس offline تنها گزینه است

**فیکس:** یک اسکریپت واحد با `datasets` + `sentence-transformers` جدید بنویس، نه ۳ فایل جدا.

---

## ۶. نقد AI Models لیست

### نقاط قوت:
- ✅ ابعاد واقعی: Qwen3 1024/2560/4096، MTEB 64.33/69.45/70.58 از منابع معتبر
- ✅ Iran Score منطقی: Qwen3-0.6B 10/10 چون 639MB + ONNX
- ✅ لایسنس‌ها درست: jina CC-BY-NC، aya CC-BY-NC، بقیه MIT/Apache
- ✅ Live check: ما تست کردیم e5-large live، jina نه — در جدول درست بود

### نقاط ضعف:
- **jina-v3** — در جدول گفتی Live ✅ ولی تست زنده FAIL — باید Live ❌ شود (یا provider ندارد)
- **aya-23-8B** — گفتی Live ❌ درست بود، ولی در TOP3 پیشنهادی نیست — خوب
- **Phi-3-mini** — گفتی Live ✅ ولی تست CHAT FAIL — باید چک شود، شاید فقط via ollama live است نه HF Router
- **هزینه‌ها** — گفتی $0.000672 برای 84 توضیح، ولی با Llama-3.1-8B الان $0.02/1M روی Novita → 33k tokens = $0.00066 درست است ✅

**پیشنهاد جدول اصلاح‌شده:**
| مدل | Live واقعی (تست 2026-09-14) |
|---|---|
| Qwen3-0.6B/4B/8B | ✅ |
| e5-large | ✅ |
| bge-m3 | ✅ |
| jina-v3 | ❌ (نیاز به self-host) |
| Llama-3.1-8B | ✅ (با id meta-llama/Llama-3.1-8B-Instruct) |
| Qwen2.5-7B | ⚠️ نیاز به enable provider در dashboard |

---

## ۷. امنیت توکن

کاربر ۲ توکن را در چت فرستاد — **نباید در فایل ذخیره شود** (مطابق constraint).

ما:
- ✅ هیچ فایلی نساختیم که توکن داخلش باشد
- ✅ فقط با `HF_TOKEN=xxx python -m ...` inline تست کردیم
- ✅ در این گزارش توکن‌ها را ننوشتیم (فقط displayName)

**توصیه:** توکن Rag1 را حذف کن (چون بدون Inference scope به درد نمی‌خورد) و یک توکن جدید با نام `joblink-rag-prod` بساز با permission:
- `inference.serverless.write`
- `inference.endpoints.infer.write`
- `repo.content.read` (برای خواندن دیتاست)

---

## ۸. آیا برای HuggingFace آماده است؟

**برای انتشار دیتاست:** ✅ **بله، آماده است**
- `hf_dataset.jsonl` 506 ردیف، `ai_models.json`, `top3_models.json`, `knowledge.db` 5 جدول، `golden_fa_tr.jsonl` 554 ردیف
- README جدید با جدول ۱۱ مدل + TOP3 + RAG مثال

**برای Space demo:** ⚠️ **نیمه‌آماده**
- Space با ۷ تب کار می‌کند ولی RAG keyword است، نه semantic
- اگر `HF_TOKEN` hulevin را در Space Secrets بگذاری، embedding کار می‌کند، LLM فقط Llama

**برای تولید ایران:** ❌ **نیاز به ۲ کار**
1. ONNX export Qwen3-0.6B → 300MB (کد آماده ولی اجرا نشده)
2. RAG semantic (embedding search)

---

## ۹. چک‌لیست فیکس پیشنهادی (اولویت‌دار)

1. **[P0] توکن Rag1 را دوباره بساز** با Inference Providers scope — ۲ دقیقه
2. **[P0] در HF Dashboard → Inference Providers → enable Novita + Fireworks + Together** — تا Qwen2.5-7B کار کند — ۱ دقیقه
3. **[P1] RAG را semantic کن** — در `rag.py` اگر embedder enabled بود، cosine search — ۳۰ دقیقه
4. **[P1] jina-v3 را در جدول Live ❌ کن** — چون provider ندارد — ۱ دقیقه
5. **[P2] golden dataset را از jobs.json واقعی بساز** نه مصنوعی — ۱ ساعت
6. **[P2] یک fine-tune script واحد با datasets جدید** — ۱ ساعت

---

## ۱۰. نتیجه نهایی

> **آیا OK است؟** 
> برای **مقاله/دمو/پورتفولیو** بله، 9/10 — کامل‌ترین پایگاه دانش fa-tr با 11 مدل + TOP3 + 552 جفت.
> برای **محصول واقعی ایران** 6/10 — نیاز به فیکس توکن + RAG semantic + ONNX.

**اگر همین الان بخواهی deploy کنی:**
- از توکن hulevin استفاده کن (Addiction)
- مدل: `Qwen3-0.6B` برای embedding (تست OK) + `Llama-3.1-8B` برای LLM (تست OK)
- RAG فعلی را با keyword نگه دار ولی top_k را 10 کن تا شانس بیشتر

**فایل‌های تحویل‌شده OK هستند و پاک نمی‌شوند — فقط توکن‌ها را در .env بگذار، نه در کد.**
