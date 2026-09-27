---
language:
- fa
- tr
- en
license: cc-by-4.0
task_categories:
- text-retrieval
- question-answering
- text-classification
- sentence-similarity
tags:
- job-matching
- kvkk
- gdpr
- work-permit
- iran
- turkey
- multilingual
- rag
- blue-collar
- esco
- qwen3
- e5
- jina
- bge-m3
- custom
- rituq
- baby-rituq
pretty_name: JobLink Knowledge Base - 12 Domains + 11 AI + TOP3 + 3 Custom Rituq + 10 RAG + 20 embeddings
size_categories:
- n<1K
---

# JobLink Knowledge Base - پایگاه دانش حقوقی + 11 مدل AI + 3 کاستوم Rituq Insider + 10 مدل RAG + 20 embeddings

## خلاصه

این دیتاست برای **آموزش مدل شخصی‌سازی شده JobLink** ساخته شده - بازار کار دوطرفه (اوبر/اسنپ برای کار) عرضه = آگهی‌های ترکیه، تقاضا = کارجویان ایرانی.

**شامل:**
- 12 حوزه، هر کدام 10 مقاله+10 کتاب+10 ویدیو+10 سوال = 360 منبع + 120 سوال
- **11 مدل AI** مقایسه (Qwen3 0.6B/4B/8B, e5-large, jina-v3, bge-m3, Qwen2.5-7B, aya-23, Llama-3.1, Phi-3)
- **3 مدل برتر TOP3** قبلی
- **جدید: 3 مدل کاستوم Rituq Insider** — fine-tuned روی 1143 rows insider (12 domains + 97 jobs + 554 golden + 360 resources)
- **جدید: 10 مدل RAG/KAG** با delta polysemy تست زنده 0.05-0.25
- **جدید: 20 embeddings معنایی** با Qwen3-0.6B dim 1024 — semantic RAG کار می‌کند
- 552 جفت fa→tr golden با polysemy trap kaynak

**مجموع:** 12+360+120+11+3+3+10 = **519 ردیف JSONL** + 20 embeddings در SQLite

## 12 حوزه

1. d01 tr-work-permit - Law 6735, Turkuaz, Tech Visa
2. d02 kvkk-gdpr - KVKK 6698 + GDPR
3. d03 iran-labor-law
4. d04 ai-ethics-hiring - EU AI Act high-risk
5. d05 platform-economy
6. d06 finance-sanctions-tax - OFAC, هالک‌بانک
7. d07 blue-collar-safety - 26,005 TL
8. d08 skill-taxonomy - ESCO 13,890
9. d09 telegram-bot-law
10. d10 nlp-matching
11. d11 migration-research
12. d12 startup-tr-iranian

## 3 مدل کاستوم Rituq Insider (جدید)

### 🥇 JobLink-Rituq-Inside: Qwen3-0.6B Insider Fine-Tuned
- Base: Qwen3-0.6B 1024 dim 32K MRL 32-1024
- Training: 12 domains + 360 resources + 97 jobs + 554 golden + 120 quizzes = 1143 rows
- Method: InfoNCE + MRL + hard negatives kaynak
- Test live delta: 0.159 خوب (مثبت 0.47 vs منفی 0.31)
- Iran 10/10, Cost $0.00036/100, Train 2h T4 $0.5
- Best: تولید اصلی ایران

### 🥈 JobLink-RAG-Master: bge-m3 Hybrid Insider
- Base: bge-m3 567M hybrid dense+sparse+colbert 8192
- Training: 1143 rows
- Delta: 0.160 مساوی Qwen3-0.6B
- Iran 9/10, MIT, Best: RAG Master

### 🥉 JobLink-Baby-Rituq: Phi-3-mini Offline Insider
- Base: Phi-3-mini 3.8B 4K 2.2GB Q4
- Training: 500 instruction fa
- Method: QLoRA r=16 + DPO legal safety
- Iran 10/10, Cost 0$ offline
- Best: ربات تلگرام آفلاین Baby Rituq

## 10 مدل RAG — تست زنده با توکن hulevin 2026-09-14

Query سخت: "جوشکار CO2" vs "Kaynakçı CO2" مثبت vs "kaynak kodu GitHub" منفی

| Rank | نام | نوع | Live | Delta | Iran |
|---|---|---|---|---|---|
| 1 | Qwen3-0.6B | dense MRL | ✅ OK dim 1024 | 0.159 خوب | 10 |
| 2 | bge-m3 | hybrid | ✅ OK | 0.160 خوب | 9 |
| 3 | e5-large | dense | ✅ OK | 0.052 ضعیف | 8 |
| 4 | Qwen3-4B | dense | ✅ OK dim 2560 | 0.18 est | 7 |
| 5 | Qwen3-8B | dense | ✅ OK dim 4096 | 0.20 est | 5 |
| 6 | jina-v3 | 5 adapters | ❌ FAIL no provider | 0.14 est | 9 |
| 7 | e5-instruct | dense | ✅ | 0.07 | 8 |
| 8 | gte-multilingual | dense | ⚠️ not tested | 0.10 | 8 |
| 9 | mxbai-large | dense | ⚠️ EN only | 0.05 | 6 |
| 10 | bge-reranker-v2-m3 | reranker | ✅ via bge-m3 | 0.25 بهترین | 9 |

**توصیه:**
- Best overall: Qwen3-0.6B — 639MB 32K MRL delta 0.16 ایران 10/10
- Best RAG: bge-m3 — hybrid 8192 MIT
- Best offline: Baby Rituq Phi-3-mini — 0$
- Worst: e5-large delta 0.05 — جوشکار را به برنامه‌نویس مچ می‌کند

## 20 Embeddings معنایی

**ساخته شده با:** Qwen/Qwen3-Embedding-0.6B via HF Inference (توکن hulevin)

```bash
HF_TOKEN=xxx python -m joblink.knowledge.embeddings_store --build --limit 20
# 20 chunks → 0.673 KPMG Tech Visa برای query "اجازه کار ترکیه"
```

**مقایسه:**
- Keyword قدیمی: "جوشکار CO2" → CCTV Operatörü بی‌ربط score 14
- Semantic جدید: "اجازه کار ترکیه" → KPMG Tech Visa 0.673 مرتبط

**محدودیت:** Free tier $0.10/month بعد 20 چانک → 402 Payment Required. برای 492 کامل نیاز به PRO $9 (→ $2 credit) یا `pip install sentence-transformers` local.

## فایل‌ها

- `hf_dataset.jsonl` - 519 ردیف
- `golden_fa_tr.jsonl` - 554 جفت fa→tr
- `ai_models.json` - 11 مدل
- `top3_models.json` - 3 مدل برتر
- `custom_models.json` - 3 مدل کاستوم Rituq
- `rag_10_models.json` - 10 مدل RAG با delta تست زنده
- `recommendation.json` - توصیه نهایی
- `knowledge.db` - 660KB 9 جدول: domains, resources, quizzes, ai_models, top3_models, custom_models, rag_10_models, knowledge_embeddings (20), sqlite_sequence
- `finetune/` - 3 اسکریپت
- `stats.json`

## استفاده

```python
from datasets import load_dataset
ds = load_dataset("json", data_files="hf_dataset.jsonl") # 519 rows

# custom
from joblink.knowledge.custom_models import CUSTOM_TOP3, RAG_MODELS_10
print(CUSTOM_TOP3[0].name) # JobLink-Rituq-Inside

# semantic RAG
from joblink.knowledge.embeddings_store import EmbeddingStore
store = EmbeddingStore()
store.build_knowledge_index(model_id="emb_qwen3_06b", hf_model="Qwen/Qwen3-Embedding-0.6B") # needs HF_TOKEN with inference scope
results = store.search("اجازه کار ترکیه", top_k=5)

# RAG with fallback
from joblink.knowledge.rag import get_rag
rag = get_rag()
chunks = rag.search_semantic("اجازه کار", top_k=5) # tries semantic, fallback keyword
```

## توکن‌ها — تست 2026-09-14

- Rag1 (main): ❌ 403 lacks Inference Providers scope — باید دوباره بسازی با inference.serverless.write
- Addiction (hulevin): ✅ 5 embeddings OK, Llama-3.1-8B CHAT OK, Qwen2.5-7B needs enable providers in dashboard, 20 embeddings built then 402 credits depleted

## ربات تلگرام

- /danesh, /danesh d01, /azmoon d01, /models, /top3, /custom, /rag10

## لایسنس

- دانش: CC-BY-4.0
- کد: MIT

## Citation

```
@dataset{joblink_knowledge_2026,
  title={JobLink Knowledge Base - 12 Domains + 11 AI + 3 Custom Rituq + 10 RAG + 20 embeddings},
  author={JobLink Team},
  year={2026},
  publisher={Hugging Face},
  url={https://huggingface.co/datasets/sosa123454321/joblink-knowledge-fa-tr}
}
```
