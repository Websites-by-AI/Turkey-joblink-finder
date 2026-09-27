# نقد دیتابیس جدید Rituq Insider — آیا OK است؟ (2026-09-14)

**تست با ۲ توکن:** Rag1 (main) و Addiction (hulevin) — همون توکن‌های قبلی

---

## 1. وضعیت توکن‌ها — بدون تغییر، هنوز مشکل دارد

| توکن | displayName | has inference? | تست embedding | تست LLM |
|---|---|---|---|---|
| Rag1-main | Rag1 | ❌ False | 403 Forbidden lacks Inference Providers | 403 |
| Addiction-hulevin | Addiction | ✅ True | ✅ OK 5 مدل (Qwen3 0.6B/4B/8B, e5-large, bge-m3) — ولی بعد 20 چانک 402 Payment Required | Llama-3.1-8B ✅ OK، Qwen2.5-7B ❌ needs enable providers |

**نتیجه:** همون مشکل قبلی:
- Rag1 باید پاک شود و دوباره با scope `inference.serverless.write` + `inference.endpoints.infer.write` ساخته شود
- hulevin کار می‌کند ولی free tier $0.10 فقط 20 چانک می‌دهد، بعد 402

**برای Baby Rituq:** hulevin تا 20 چانک semantic ساخت، بعد credit تمام شد — برای 492 کامل نیاز به PRO $9

---

## 2. دیتابیس جدید — 9 جدول — آیا OK؟

```
Tables: domains (12), resources (360), quizzes (120), ai_models (11), top3_models (3), custom_models (3), rag_10_models (10), knowledge_embeddings (20)
```

**خوب:**
- ✅ از 5 جدول → 9 جدول — اضافه شدن 3 کاستوم + 10 RAG + embeddings
- ✅ `custom_models.json` (4.3K) و `rag_10_models.json` (4.7K) و `recommendation.json` ساخته شد
- ✅ `hf_dataset.jsonl` 519 ردیف (12+360+120+11+3+3+10) — منطقی
- ✅ `knowledge.db` 660KB (قبل 152KB) — embeddings 20 تا
- ✅ stats.json شامل custom_models 3 و rag_10_models 10

**بد:**
- ⚠️ `knowledge_embeddings` فقط 20 نه 492 — چون credit تمام شد. در README نوشتیم 20 ولی کاربر انتظار 492 دارد
- ⚠️ embeddings_store.py fallback به sentence_transformers دارد ولی ما نصب نکردیم — اگر نصب بود، 492 را local می‌ساخت 0$
- ⚠️ هیچ index برای vector search سریع نیست — برای 492 چانک cosine loop OK است، برای 10K نیاز به FAISS/Qdrant

**نمره دیتابیس:** 8/10 — ساختار عالی، ولی embeddings ناقص

---

## 3. 3 مدل کاستوم Rituq Insider — آیا واقعی هستند؟

| مدل | Base | Training rows | Status | واقعی؟ |
|---|---|---|---|---|
| custom_rituq_inside_06b | Qwen3-0.6B | 1143 | ready_to_train | ❌ mock — فقط تعریف، وزن fine-tune نشده |
| custom_rag_master_bge | bge-m3 | 1143 | ready_to_train | ❌ mock |
| custom_baby_rituq_phi3 | Phi-3-mini | 500 | ready_to_train | ❌ mock |

**خوب:**
- ✅ training_data دقیق: 12 domains + 360 resources + 97 jobs + 554 golden + 120 quizzes = 1143 — محاسبه درست
- ✅ insider_knowledge لیست شده (d01, d02, etc)
- ✅ method دقیق: InfoNCE + MRL + hard negatives kaynak
- ✅ cost و Iran score منطقی

**بد:**
- ❌ هیچ کد fine-tune واقعی اجرا نشده — فقط dataclass تعریف شده
- ❌ hf_repo `sosa123454321/joblink-rituq-06b-inside` وجود ندارد — فقط placeholder
- ❌ برای Baby Rituq گفتی QLoRA r=16 ولی کد QLoRA نداریم

**نمره کاستوم:** 6/10 — ایده عالی، ولی mock است نه trained

**فیکس پیشنهادی:**
- یک Space با T4 بساز و `finetune/top1_qwen3_06b_finetune.py` را واقعا اجرا کن
- یا حداقل یک LoRA adapter کوچک (چند MB) train کن و در HF آپلود کن تا ثابت شود pipeline کار می‌کند

---

## 4. 10 مدل RAG — آیا delta واقعی است؟

| Rank | نام | Live Test واقعی | Delta | واقعی؟ |
|---|---|---|---|---|
| 1 | Qwen3-0.6B | ✅ OK dim 1024 | 0.159 | ✅ تست زنده کردیم |
| 2 | bge-m3 | ✅ OK dim 1024 | 0.160 | ✅ تست زنده |
| 3 | e5-large | ✅ OK dim 1024 | 0.052 | ✅ تست زنده |
| 4 | Qwen3-4B | ✅ OK dim 2560 | 0.18 est | ⚠️ تخمینی، تست نکردیم |
| 5 | Qwen3-8B | ✅ OK dim 4096 | 0.20 est | ⚠️ تخمینی |
| 6 | jina-v3 | ❌ FAIL no provider | 0.14 est | ✅ FAIL واقعی، delta تخمینی |
| 7 | e5-instruct | ✅ (same as e5-large) | 0.07 | ⚠️ تخمینی |
| 8 | gte-multilingual | ⚠️ not tested | 0.10 est | ❌ not tested |
| 9 | mxbai-large | ⚠️ EN only | 0.05 | ❌ not tested |
| 10 | bge-reranker-v2-m3 | ✅ via bge-m3 | 0.25 | ⚠️ تخمینی ولی منطقی (cross-encoder بهتر) |

**خوب:**
- ✅ 3 مدل اصلی (Qwen3-0.6B, bge-m3, e5-large) delta واقعی با تست polysemy
- ✅ Live Test ستون درست — jina FAIL واقعی
- ✅ نتیجه درست: Qwen3 و bge-m3 بهتر از e5

**بد:**
- ⚠️ 7 مدل delta تخمینی (est) — باید یا تست کنیم یا بنویسیم "estimated from docs"
- ⚠️ gte و mxbai اصلا تست نکردیم — باید حذف یا تست شوند

**نمره RAG 10:** 7/10 — 3 مدل واقعی، 7 تخمینی

---

## 5. RAG معنایی — 20 embedding — آیا OK؟

**تست:**
```bash
HF_TOKEN=hulevin python -m joblink.knowledge.embeddings_store --query "اجازه کار ترکیه" --top 5
# نتیجه: KPMG Tech Visa 0.673, d01 domain 0.626, Yabancı Çalışma İzni 0.586 — مرتبط ✅
```

**قبل (keyword):**
```
"جوشکار CO2" → Güvenlik CCTV Operatörü score 14 — بی‌ربط ❌
```

**خوب:**
- ✅ semantic search کار می‌کند و بهتر از keyword است
- ✅ embeddings_store.py fallback به keyword اگر embedding نباشد
- ✅ 20 چانک ساخته شد و در DB ذخیره شد

**بد:**
- ❌ فقط 20 چانک، نه 492 — چون free tier $0.10 تمام شد (402 Payment Required)
- ❌ برای هر query جدید هم باید embedding query بسازد — که باز credit می‌خواهد — الان بعد 20 چانک حتی query هم 402 می‌دهد
- ❌ sentence_transformers نصب نیست — اگر بود local 0$ می‌ساخت

**فیکس:**
```bash
pip install sentence-transformers
python -m joblink.knowledge.embeddings_store --build --model Qwen/Qwen3-Embedding-0.6B
# local → 0$ → 492 کامل
```
یا PRO $9 بخر

**نمره RAG semantic:** 7/10 — کار می‌کند ولی ناقص (20/492)

---

## 6. CLI و Space — آیا OK؟

**CLI:**
```bash
python -m joblink.cli ai-models --custom  # OK
python -m joblink.cli custom --list-rag   # OK
python -m joblink.cli rag --query "اجازه کار" --top 3 --semantic  # fallback به keyword چون credit تمام
```

**Space app.py:**
- 8 تب الان (اضافه شد 👶 Rituq Insider + RAG 10)
- list_custom() کار می‌کند
- ولی semantic search در Space هم نیاز به HF_TOKEN در Secrets دارد

**نمره:** 8/10

---

## 7. فایل‌های تحویل — آیا کامل؟

| فایل | وضعیت |
|---|---|
| custom_models.py | ✅ 3 مدل + 10 RAG + RECOMMENDATION |
| embeddings_store.py | ✅ semantic RAG |
| dataset.py | ✅ 9 جدول + preserve embeddings |
| data/knowledge/*.json | ✅ 8 فایل JSON |
| knowledge.db 660KB | ✅ 9 جدول + 20 embeddings |
| RITUQ-INSIDER-FA.md | ✅ گزارش کامل |
| CRITIQUE-FA.md قبلی | ✅ نقد توکن‌ها |
| spaces/app.py | ✅ 8 تب |
| spaces/knowledge/README.md | ✅ آپدیت 519 ردیف + 10 RAG |

**نمره:** 9/10

---

## 8. نتیجه نهایی — آیا OK است؟

| بخش | قبل (CRITIQUE-FA) | الان (Rituq) | بهبود؟ |
|---|---|---|---|
| دیتابیس | 5 جدول 152KB | 9 جدول 660KB + 20 emb | ✅ + |
| مدل‌ها | 11 + TOP3 | 11 + TOP3 + 3 custom + 10 RAG | ✅ + |
| RAG | keyword-only | semantic 20 + keyword fallback | ✅ + |
| توکن‌ها | Rag1 ❌, hulevin ✅ ولی 402 | همون — بدون تغییر | ❌ بدون تغییر |
| کاستوم واقعی؟ | mock | mock (ready_to_train) | ⚠️ هنوز mock |
| CLI | ai-models, rag | + custom, + semantic flag | ✅ + |
| Space | 7 تب | 8 تب + Rituq | ✅ + |

**نمره کل:**
- **برای دمو/HF Hub:** 9/10 — عالی، کامل‌ترین پایگاه fa-tr با 3 کاستوم + 10 RAG + 20 semantic
- **برای تولید ایران:** 6.5/10 — هنوز 3 مشکل:
  1. توکن Rag1 بدون inference scope (باید دوباره بسازی)
  2. embeddings فقط 20 نه 492 (نیاز به PRO $9 یا local sentence-transformers)
  3. کاستوم مدل‌ها mock هستند نه trained (نیاز به یک train واقعی روی T4)

**آیا OK است؟**
> **بله برای نمایش، خیر برای تولید واقعی — دقیقا مثل قبل ولی بهتر شده**

**اگر همین الان بخواهی deploy کنی:**
- از hulevin استفاده کن (Addiction) — 20 embedding دارد
- مدل: Qwen3-0.6B (تست OK) + Llama-3.1-8B (تست OK)
- RAG: semantic برای 20 چانک اول، بقیه keyword fallback
- برای Baby Rituq: Phi-3-mini QLoRA هنوز train نشده — فعلا prompt engineering

**فوری فیکس کن:**
1. Rag1 را پاک کن، جدید با inference scope بساز
2. `pip install sentence-transformers` و 492 embedding local بساز 0$
3. یک fine-tune کوچک واقعی روی T4 اجرا کن تا custom_rituq_inside_06b واقعا trained شود
