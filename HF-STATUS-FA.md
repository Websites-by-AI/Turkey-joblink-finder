# وضعیت HuggingFace — مدل، دیتابیس، Space — آیا کار می‌کند؟ (2026-09-14)

**تست با 2 توکن:** Rag1 (main) و Addiction (hulevin)

---

## 1. دیتابیس — knowledge.db — ✅ OK

**فایل:** `data/knowledge/knowledge.db` — 660KB (قبل 152KB)

| جدول | تعداد | وضعیت |
|---|---|---|
| domains | 12 | ✅ |
| resources | 360 (120 مقاله+120 کتاب+120 ویدیو) | ✅ |
| quizzes | 120 (10 هر حوزه) | ✅ |
| ai_models | 11 | ✅ |
| top3_models | 3 | ✅ |
| custom_models | 3 — Rituq Insider | ✅ جدید |
| rag_10_models | 10 — RAG با delta | ✅ جدید |
| knowledge_embeddings | 20 — Qwen3-0.6B dim 1024 | ⚠️ فقط 20 نه 492 — credit تمام شد |

**hf_dataset.jsonl:** 519 ردیف (12+360+120+11+3+3+10) — 278KB

**stats.json:**
```json
{
  "domains": 12,
  "resources": 360,
  "ai_models": 11,
  "top3": 3,
  "custom_models": 3,
  "rag_10_models": 10
}
```

**آیا برای HF آماده؟** ✅ بله — 519 ردیف JSONL + 8 JSON + 660KB DB

**دستور push:**
```bash
huggingface-cli upload sosa123454321/joblink-knowledge-fa-tr data/knowledge/ --repo-type dataset
```

---

## 2. مدل‌ها — 11 + 3 کاستوم + 10 RAG — ⚠️ نیمه OK

### 11 مدل اصلی

| مدل | HF ID | Live Test 2026-09-14 با hulevin | وضعیت |
|---|---|---|---|
| Qwen3-0.6B | Qwen/Qwen3-Embedding-0.6B | ✅ OK dim 1024 delta 0.159 | ✅ کار می‌کند |
| Qwen3-4B | Qwen/Qwen3-Embedding-4B | ✅ OK dim 2560 | ✅ |
| Qwen3-8B | Qwen/Qwen3-Embedding-8B | ✅ OK dim 4096 | ✅ |
| e5-large | intfloat/multilingual-e5-large | ✅ OK dim 1024 delta 0.052 ضعیف | ✅ ولی ضعیف |
| bge-m3 | BAAI/bge-m3 | ✅ OK dim 1024 delta 0.160 | ✅ |
| jina-v3 | jinaai/jina-embeddings-v3 | ❌ FAIL no provider | ❌ نیاز به self-host |
| Llama-3.1-8B | meta-llama/Llama-3.1-8B-Instruct | ✅ CHAT OK فارسی جواب داد | ✅ |
| Qwen2.5-7B | Qwen/Qwen2.5-7B-Instruct | ❌ needs enable providers | ⚠️ باید در HF Dashboard → Inference Providers → Novita/Together enable کنی |
| Phi-3-mini | microsoft/Phi-3-mini-4k-instruct | ❌ needs provider | ⚠️ |
| aya-23-8B | CohereForAI/aya-23-8B | ❌ no provider | ❌ expected |

**نتیجه:** 5 embedding + 1 LLM کار می‌کند — کافی برای دمو

### 3 مدل کاستوم Rituq

| مدل | Status | واقعی؟ |
|---|---|---|
| Rituq-Inside 0.6B | ready_to_train | ❌ mock — فقط تعریف، وزن train نشده |
| RAG-Master bge-m3 | ready_to_train | ❌ mock |
| Baby-Rituq Phi3 | ready_to_train | ❌ mock |

**برای واقعی شدن:** یک Space T4 بساز و `finetune/top1_qwen3_06b_finetune.py` را اجرا کن

### 10 مدل RAG

- 3 مدل delta واقعی (Qwen3-0.6B 0.159, bge-m3 0.160, e5-large 0.052)
- 7 مدل delta تخمینی (est)

**توصیه نهایی:**
- Best overall: Qwen3-0.6B (ایران 10/10)
- Best RAG: bge-m3 (hybrid)
- Best offline Baby Rituq: Phi-3-mini 0$

---

## 3. Space — Gradio App — ✅ OK (8 تب)

**فایل:** `spaces/app.py` — 399 خط — 8 تب

| تب | نام | وضعیت |
|---|---|---|
| 1 | کارجو / Job seeker | ✅ |
| 2 | کارفرما / Employer | ✅ |
| 3 | 📚 پایگاه دانش | ✅ 12 حوزه |
| 4 | 📝 آزمون | ✅ 120 سوال |
| 5 | 🤖 10 مدل AI + TOP3 | ✅ 11 مدل + TOP3 |
| 6 | 👶 Rituq Insider + RAG 10 | ✅ جدید — 3 کاستوم + 10 RAG |
| 7 | 🔍 RAG / جستجوی دانش | ✅ keyword + semantic (20 emb) |
| 8 | 📖 آموزش AI ایران | ✅ |

**تست local:**
```bash
cd spaces && python app.py
# Gradio should launch on 7860
```

**آیا برای HF Space آماده؟** ✅ بله

**فایل‌های Space:**
- `app.py` (399 خط)
- `knowledge/` — 8 JSON + DB + README + finetune/
- `requirements.txt` — gradio, sentence-transformers, etc.

**دستور deploy:**
```bash
# در HF Space repo
git clone https://huggingface.co/spaces/sosa123454321/joblink
cp -r spaces/* .
git add .
git commit -m "Update 8 tabs + Rituq + 20 embeddings"
git push
```

**نیاز به Secrets در Space:**
- `HF_TOKEN` = توکن hulevin (Addiction) — برای embedding و LLM

---

## 4. OS Runner — آیا کار می‌کند؟

**منظور از OS Runner:** GitHub Actions یا HF Space runner که مدل و دیتابیس را اجرا می‌کند

**وضعیت فعلی:**

| Runner | وضعیت | توضیح |
|---|---|---|
| **Local runner** (این محیط) | ✅ OK | 9 جدول، 20 embeddings، CLI کار می‌کند |
| **HF Space runner** | ⚠️ نیمه OK | app.py 8 تب دارد، ولی نیاز به HF_TOKEN secret + PRO برای 492 embeddings |
| **HF Inference runner** | ⚠️ نیمه OK | 5 embedding + 1 LLM کار می‌کند، بقیه نیاز به enable providers |
| **Cloudflare Workers runner** | ⏳ باید بسازی | wrangler deploy — bge-m3 fallback |

**تست runner local:**
```bash
python -m joblink.cli knowledge --out data/knowledge --show  # OK
python -m joblink.cli ai-models --custom  # OK
python -m joblink.cli rag --query "اجازه کار" --top 3  # OK keyword
HF_TOKEN=xxx python -m joblink.knowledge.embeddings_store --query "اجازه کار" --top 3  # OK semantic 20
```

**تست Space runner (شبیه‌سازی):**
```bash
cd spaces && python app.py
# باید 8 تب بیاید
```

---

## 5. مشکلات و فیکس‌ها

| مشکل | شدت | فیکس |
|---|---|---|
| Rag1 token بدون inference scope | P0 | پاک کن، جدید با inference.serverless.write بساز |
| hulevin free tier $0.10 → 20 chunks بعد 402 | P0 | PRO $9 بخر (→ $2 credit) یا `pip install sentence-transformers` local |
| jina-v3 no provider | P1 | در جدول Live ❌ کن — قبلا کردیم |
| Qwen2.5-7B needs enable providers | P1 | HF Dashboard → Inference Providers → enable Novita, Together, Fireworks |
| custom models mock نه trained | P2 | یک T4 Space بساز و train واقعی |
| knowledge_embeddings فقط 20 نه 492 | P1 | PRO یا local |

---

## 6. نتیجه — آیا HF کار می‌کند؟

| بخش | وضعیت | نمره |
|---|---|---|
| دیتابیس (DB) | ✅ 9 جدول 660KB + 519 JSONL | 9/10 |
| مدل‌ها (Models) | ⚠️ 5 embedding + 1 LLM OK، بقیه needs enable | 6/10 |
| Space (App) | ✅ 8 تب 399 خط | 9/10 |
| OS Runner (Local) | ✅ CLI OK | 9/10 |
| OS Runner (HF Space) | ⚠️ نیاز به HF_TOKEN secret + PRO | 6/10 |
| OS Runner (HF Inference) | ⚠️ 5/11 کار می‌کند | 6/10 |

**آیا OK است؟**
> **برای دمو بله 8/10 — برای تولید 6/10 — 2 فیکس فوری: (1) Rag1 token جدید با inference scope، (2) PRO $9 یا local sentence-transformers برای 492 embeddings**

**اگر همین الان deploy کنی:**
- دیتاست: push کن — 519 ردیف آماده
- Space: deploy کن — 8 تب کار می‌کند با 20 embeddings + keyword fallback
- مدل: از Qwen3-0.6B + Llama-3.1-8B استفاده کن (هر دو تست OK)

---

## 7. دستورات نهایی برای HF

```bash
# 1. دیتاست
huggingface-cli upload sosa123454321/joblink-knowledge-fa-tr data/knowledge/ --repo-type dataset

# 2. Space
git clone https://huggingface.co/spaces/sosa123454321/joblink
cp spaces/app.py spaces/knowledge/* spaces/
git add .
git commit -m "Rituq Insider: 3 custom + 10 RAG + 20 embeddings + 8 tabs"
git push

# 3. در Space Settings → Variables → Secrets
HF_TOKEN = <REVOKED_HF_TOKEN>  # hulevin

# 4. تست Space
# باز کن: https://huggingface.co/spaces/sosa123454321/joblink
# 8 تب باید بیاید
# تب RAG → query "اجازه کار" → باید 0.673 KPMG بدهد
```

---

## 8. لینک‌های HF

- دیتاست: https://huggingface.co/datasets/sosa123454321/joblink-knowledge-fa-tr
- Space: https://huggingface.co/spaces/sosa123454321/joblink
- مدل Qwen3-0.6B: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
- مدل bge-m3: https://huggingface.co/BAAI/bge-m3
- مدل e5-large: https://huggingface.co/intfloat/multilingual-e5-large
- مدل Llama-3.1-8B: https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
