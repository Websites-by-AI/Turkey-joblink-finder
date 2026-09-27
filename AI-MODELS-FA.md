# مقایسه 10 مدل AI برای JobLink + 3 مدل برتر سفارشی

> این فایل جواب بخش دوم درخواست: "make customized fine tune ai model or RAG knowledge base or others ai model and list around 10 different ai model for it and suggest which one is better and make three top model ai"

## لیست 10 مدل اصلی + 1 مدل فوق سبک (جمع 11)

| # | نام | نوع | پارامتر | بعد | کانتکست | زبان fa/tr | لایسنس | HF Inference Live? | MTEB | Iran Score /10 | بهترین برای |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Qwen3-Embedding-0.6B** | embedding | 0.6B | 1024 (MRL 32-1024) | 32K | ✅ fa/tr عالی | Apache-2.0 | ✅ live | 64.33 multilingual | 10 | ایران - سبک، CPU، ربات تلگرام |
| 2 | Qwen3-Embedding-4B | embedding | 4B | 2560 (MRL) | 32K | ✅ عالی | Apache-2.0 | ✅ live | 69.45 | 7 | سرور اصلی - بالانس |
| 3 | Qwen3-Embedding-8B | embedding | 8B | 4096 (MRL) | 32K | ✅ عالی | Apache-2.0 | ✅ live | 70.58 #1 | 5 | تحقیقات - بهترین دقت |
| 4 | **multilingual-e5-large** | embedding | 560M | 1024 | 512 | ✅ خوب | MIT | ✅ live (hf+deepinfra) | 63.22 | 8 | پایه فعلی JobLink |
| 5 | multilingual-e5-large-instruct | embedding | 560M | 1024 | 512 | ✅ خوب | MIT | ✅ live | 65.53 | 8 | جایگزین instruct |
| 6 | **jina-embeddings-v3** | embedding | 570M | 1024 (MRL) | 8192 | ✅ 89 زبان | CC-BY-NC? | ✅ live | 63.35 | 9 | رزومه بلند 8192 توکن |
| 7 | **bge-m3** | embedding | 567M | 1024 dense+ sparse+colbert | 8192 | ✅ 100+ | MIT | ✅ live | 59.56 | 9 | Hybrid search (dense+BM25+ColBERT) |
| 8 | **Qwen2.5-7B-Instruct** | llm | 7.6B | - | 131K | ✅ fa/tr عالی TurkishMMLU 54.28 vs Llama 45.61 | Qwen | ✅ live $0.30/1M | - | 8 | LLM اصلی - توضیح فارسی RAG |
| 9 | aya-23-8B | llm | 8B | - | 8192 | ✅ 23 زبان fa/tr depth | CC-BY-NC | ❌ no provider (self-host) | - | 7 | فارسی محاوره‌ای |
| 10 | Llama-3.1-8B-Instruct | llm | 8B | - | 131K | ⚠️ fa ضعیف | Llama 3.1 | ✅ live $0.02/1M novita | - | 6 | ارزان fallback |
| 11 | Phi-3-mini-4k-instruct | llm | 3.8B | - | 4K | ⚠️ fa ضعیف | MIT | ✅ live | - | 10 | فوق سبک آفلاین ایران |

**منبع ابعاد و MTEB:** particula.tech blog, morphllm.com, qwen.ai/blog, docs.api.nvidia.com bge-m3, jina.ai news

---

## تحلیل کدام بهتر است؟

### برای Embedding (تطبیق شغل fa→tr):

**برنده: Qwen3-Embedding-0.6B**

دلایل:
- **سبک‌ترین SOTA:** 639MB vs 4.7GB 8B، 0.6B با MTEB 64.33 از mxbai-embed-large 64.68 انگلیسی بهتر در ترک چندزبانه
- **کانتکست 32K:** vs e5 512 و jina/bge 8192 - رزومه‌های بلند فارسی را کامل می‌گیرد
- **MRL:** می‌توانی بعد را از 1024 به 512 یا 256 کم کنی بدون افت زیاد (برای D1 SQLite)
- **100+ زبان:** فارسی و ترکی هر دو native، نه ترجمه
- **Apache-2.0:** تجاری مجاز، برخلاف jina CC-BY-NC و aya CC-BY-NC
- **GGUF/ONNX آماده:** Qwen3-Embedding-8B-GGUF و 0.6B GGUF موجود - llama.cpp
- **Instruction-aware:** `Instruct: یک شغل مناسب برای این رزومه پیدا کن\nQuery: {cv}`

**رتبه‌بندی embedding:**
1. Qwen3-0.6B (10/10 ایران) - بهترین برای ایران
2. jina-v3 (9/10) - بهترین برای کانتکست 8192 + 5 task adapter
3. bge-m3 (9/10) - بهترین برای hybrid (dense+sparse+colbert) - یک مدل سه کاره
4. e5-large (8/10) - پایه فعلی، live، MIT، سریع
5. Qwen3-4B (7/10) - بالانس دقت/حجم

### برای LLM (توضیح فارسی + RAG):

**برنده: Qwen2.5-7B-Instruct**

دلایل:
- **TurkishMMLU 54.28 vs Llama 45.61:** +19% بهتر در ترکی
- **فارسی عالی:** 29+ زبان، فارسی جزو اصلی، instruction following 74.87 multilingual
- **131K کانتکست:** می‌تواند کل دانش حقوقی d01+d02+d06 را در یک prompt بگیرد
- **QLoRA آماده:** fine-tune روی T4 با 16GB
- **قیمت:** $0.30/1M - متوسط

**رتبه‌بندی LLM:**
1. Qwen2.5-7B (8/10) - بهترین fa/tr
2. aya-23-8B (7/10) - بهترین فارسی محاوره‌ای ولی NC license و 8192 کانتکست کم و no provider
3. Llama-3.1-8B (6/10) - ارزان‌ترین $0.02/1M روی novita ولی fa ضعیف
4. Phi-3-mini (10/10 ایران) - فوق سبک 3.8B 2.2GB Q4، MIT، CPU-only، آفلاین کامل

---

## 3 مدل برتر سفارشی JobLink (ساخته شده)

### 🥇 TOP 1: JobLink-Iran-Light (توصیه اصلی برای ایران)

**نام:** `JobLink-Iran-Light: Qwen3-0.6B + Qwen2.5-7B`

**ترکیب:**
- Embedding: Qwen3-Embedding-0.6B (1024 dim → truncate 512 برای D1)
- Reranker: Qwen3-Reranker-0.6B (اختیاری)
- LLM: Qwen2.5-7B-Instruct (131K context)

**چرا بهترین:**
- سبک: 639MB emb + 4.7GB LLM Q4 = 5.3GB کل - قابل اجرا روی VPS ایران 8GB RAM + T4 یا حتی CPU
- فارسی و ترکی SOTA: TurkishMMLU 54.28, MTEB 64.33 multilingual
- لایسنس تجاری مجاز: Apache-2.0 + Qwen License
- ONNX + GGUF آماده: بدون نیاز به HF API (مهم برای ایران فیلتر)
- MRL: بعد قابل تنظیم 32-1024 - برای D1 512 ذخیره کن
- 32K+131K کانتکست: رزومه بلند + دانش حقوقی کامل

**معماری:**
```
CV فارسی → Instruct: یک شغل مناسب برای این رزومه پیدا کن\nQuery: {cv}
→ Qwen3-0.6B 1024 dim → truncate 512 → cosine search روی 97 آگهی + 360 دانش + 120 quiz
→ Top 10 → Qwen3-Reranker-0.6B rerank → Top 5
→ LLM Qwen2.5-7B با RAG chunks (KVKK + اجازه کار + تحریم) → JSON: score, matched_skills, gaps, legal_warning, explanation_fa
```

**Fine-tune (کد در data/knowledge/finetune/top1_qwen3_06b_finetune.py):**
- Golden dataset: `data/knowledge/golden_fa_tr.jsonl` - 552 ردیف شامل polysemy trap kaynak (جوشکار vs منبع کد)
- Contrastive InfoNCE, 5 epoch, batch 32, lr 2e-5, warmup 10% روی T4 HF Space (~2h, $0.5)
- هدف: Recall@5 روی 14 رزومه مصنوعی 0.80+
- ONNX export: `optimum-cli export onnx --model models/joblink-qwen3-0.6b-fa-tr --task feature-extraction models/qwen3-06b-onnx/` → int8 quantization → 300MB برای VPS ایران

**هزینه:**
- Training ~2h T4 $0.5, Inference 36k tokens → $0.00036, LLM $0.000672 → total <$0.01 per 100 jobs

**Deploy ایران:**
- VPS ایران: `python -m optimum.onnxruntime + FastAPI`
- یا GGUF via llama.cpp: `./llama-cli -m qwen3-embedding-0.6b-q4.gguf`
- Fallback: Cloudflare Workers AI bge-m3

**وضعیت:** ✅ کد آماده، golden dataset ساخته شد، فقط نیاز به GPU برای اجرا

---

### 🥈 TOP 2: JobLink-Balanced (توصیه برای تولید جهانی)

**نام:** `JobLink-Balanced: e5-large + Llama-3.1-8B`

**ترکیب:**
- Embedding: multilingual-e5-large (1024 dim)
- LLM: Llama-3.1-8B-Instruct

**چرا:**
- هر دو live روی HF Router (تست شده 2026-09-13: e5-large → hf-inference + deepinfra live, Llama → novita $0.02/1M)
- ارزان‌ترین: $0.000672 per 84 explanations
- MIT + Llama 3.1 License تجاری مجاز
- کد فعلی JobLink با e5 کار می‌کند - بدون تغییر
- مستندات زیاد

**معماری:**
```
Query: 'query: {cv}' Passage: 'passage: {job}' → e5-large 1024 dim → BM25 blend 0.34 skill/0.26 semantic → Top 5 → Llama-3.1-8B prompt فارسی + KVKK → توضیح
```

**Fine-tune (data/knowledge/finetune/top2_e5_lora.py):**
- LoRA r=16 برای اصطلاحات یقه‌آبی
- 200 جفت fa→tr با تمرکز بر kaynak polysemy
- 1 epoch, lr 1e-5 - جلوگیری از overfit
- تست: جوشکار نباید به software engineer مچ شود

**وضعیت:** ✅ بدون fine-tune هم کار می‌کند - فقط توکن scope درست لازم است

---

### 🥉 TOP 3: JobLink-UltraLight-Offline (توصیه برای آفلاین کامل ایران)

**نام:** `JobLink-UltraLight-Offline: jina-v3 + Phi-3-mini`

**ترکیب:**
- Embedding: jina-embeddings-v3 (570M, 8192 context, 5 task adapters, MRL)
- LLM: Phi-3-mini-4k-instruct (3.8B, 2.2GB Q4, MIT)

**چرا:**
- فوق سبک آفلاین کامل: بدون نیاز به اینترنت بین‌الملل، بدون API خارجی
- jina-v3 8192 توکن - بهترین برای رزومه‌های بلند فارسی
- 5 LoRA adapter: retrieval.query, retrieval.passage, text-matching, classification, separation
- Phi-3 MIT, CPU inference عالی, 8GB RAM کافی
- 0$ هزینه - کاملا آفلاین

**معماری:**
```
jina-v3 task=retrieval.query 512 dim (MRL) → Qdrant local → Phi-3-mini با RAG → توضیح کوتاه فارسی
```

**Fine-tune (data/knowledge/finetune/top3_jina_phi3_offline.py):**
- بدون fine-tune LLM - فقط prompt engineering فارسی
- Embedding: 300 جفت fa-tr
- ONNX: Xenova/jina-embeddings-v3 already ONNX ready
- Phi-3 GGUF Q4 2.2GB

**وضعیت:** ✅ کاملا آفلاین، لپ‌تاپ ایران بدون GPU کافی

---

## جدول مقایسه نهایی 3 مدل برتر

| معیار | TOP1 Iran-Light | TOP2 Balanced | TOP3 UltraLight |
|---|---|---|---|
| Embedding | Qwen3-0.6B 1024 dim 32K | e5-large 1024 dim 512 | jina-v3 1024 dim 8192 |
| LLM | Qwen2.5-7B 131K | Llama-3.1-8B 131K | Phi-3-mini 4K |
| حجم کل | 5.3GB Q4 | 2GB | 2.8GB Q4 |
| MTEB multilingual | 64.33 | 63.22 | 63.35 |
| TurkishMMLU | 54.28 | 45.61 | ~40 |
| فارسی | عالی | ضعیف | ضعیف |
| کانتکست | 32K+131K | 512+131K | 8192+4K |
| لایسنس تجاری | ✅ Apache+Qwen | ✅ MIT+Llama | ⚠️ jina NC + MIT |
| HF Live | ✅ | ✅ | ✅ |
| Iran Score | 10/10 | 8/10 | 10/10 |
| هزینه 100 شغل | <$0.01 | $0.000672 | $0 |
| CPU inference | ✅ ممکن | ✅ ممکن | ✅ عالی |
| ONNX/GGUF | ✅ آماده | ✅ ممکن | ✅ آماده |
| نیاز GPU | T4 برای train, CPU برای infer | CPU | CPU |
| بهترین برای | **ایران تولید** | **جهانی ارزان** | **آفلاین کامل** |

**توصیه نهایی:**
- **اگر در ایران هستی و می‌خواهی تولید واقعی:** TOP1 Qwen3-0.6B + Qwen2.5-7B
- **اگر می‌خواهی سریع و ارزان جهانی:** TOP2 e5-large + Llama-3.1-8B (کد فعلی)
- **اگر اینترنت بین‌الملل نداری:** TOP3 jina-v3 + Phi-3-mini

---

## RAG پیاده‌سازی شده

**فایل:** `joblink/knowledge/rag.py`

**قابلیت‌ها:**
- 492 chunk: 12 domain + 120 article + 120 quiz + 97 job + ...
- جستجوی BM25-like + boost high-risk domains (d01,d02,d06)
- `search(query, top_k=5, domain_filter="d01")`
- `build_prompt(cv, job_title, job_desc, chunks)` → prompt فارسی با قوانین حقوقی
- `explain_with_llm(cv, job)` → اگر HF_TOKEN live باشد LLM، وگرنه template fallback با هشدار حقوقی

**مثال:**
```python
from joblink.knowledge.rag import get_rag
rag = get_rag()
chunks = rag.search("جوشکار CO2 استانبول اجازه کار", top_k=3, domain_filter="d01")
# → chunks از d01: Law 6735, 5:1 rule, Tech Visa

prompt = rag.build_prompt(cv_text="جوشکار...", job_title="Kaynakçı", job_desc="...", top_chunks=chunks)
# → prompt فارسی با دانش حقوقی

result = rag.explain_with_llm(cv_text, job) 
# → {"score": 75, "matched_skills": ["welding"], "gaps": ["Turkish B1"], "legal_warning": "بدون Çalışma izni شروع نکن", "explanation_fa": "...", "from_llm": True/False}
```

---

## فایل‌های جدید

- `joblink/knowledge/ai_models.py` - 11 مدل + TOP3
- `joblink/knowledge/rag.py` - RAG pipeline
- `joblink/knowledge/fine_tune.py` - generator golden dataset + 3 fine-tune scripts
- `data/knowledge/ai_models.json` - 11 مدل
- `data/knowledge/top3_models.json` - 3 مدل برتر
- `data/knowledge/golden_fa_tr.jsonl` - 552 ردیف fa→tr با polysemy trap
- `data/knowledge/finetune/` - 3 اسکریپت پایتون آماده اجرا
- `spaces/knowledge/` - کپی همه فایل‌ها برای HF Hub + D1
- `AI-MODELS-FA.md` - این فایل

---

## دستورات اجرا

```bash
# دیدن 10 مدل
python -c "from joblink.knowledge.ai_models import MODELS; [print(f'{m.id} {m.name} {m.iran_score}/10 MTEB {m.score_mteb}') for m in MODELS]"

# دیدن TOP3
python -c "from joblink.knowledge.ai_models import TOP3; import json; print(json.dumps(TOP3, ensure_ascii=False, indent=2))"

# ساخت golden dataset + fine-tune scripts
python -m joblink.knowledge.fine_tune

# تست RAG
python -c "from joblink.knowledge.rag import get_rag; rag=get_rag(); print(rag.search('اجازه کار ترکیه', top_k=2)[0].text[:200])"

# export کامل
python -m joblink.cli knowledge --out data/knowledge --show
```

---

## قدم بعدی

1. **TOP1 را fine-tune کن:** `python data/knowledge/finetune/top1_qwen3_06b_finetune.py` روی HF Space T4
2. **ONNX export برای ایران:** `optimum-cli export onnx --model models/joblink-qwen3-0.6b-fa-tr --task feature-extraction models/qwen3-06b-onnx/`
3. **RAG را به bot وصل کن:** در `bot.py` بعد از مچ، `rag.explain_with_llm(cv, job)` صدا بزن تا توضیح حقوقی بدهد
4. **دیتاست جدید را به HF Hub بفرست:** شامل ai_models.json + top3_models.json + golden dataset
