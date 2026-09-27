# لینک‌های کامل JobLink — سایت‌ها، HuggingFace، ربات، کانال، گروه

## 1. HuggingFace — مدل‌ها، دیتاست، Space

### دیتاست و Space (مال شما)

| نام | لینک | وضعیت | توضیح |
|---|---|---|---|
| **دیتاست دانش** | `https://huggingface.co/datasets/sosa123454321/joblink-knowledge-fa-tr` | ✅ آماده push — 519 ردیف + 20 embeddings + 660KB DB | 12 حوزه + 360 منبع + 120 سوال + 11 مدل + 3 کاستوم + 10 RAG |
| **Space دمو** | `https://huggingface.co/spaces/sosa123454321/joblink` | ✅ آماده — 8 تب — 399 خط | Gradio: کارجو، کارفرما، دانش، آزمون، 10 مدل، Rituq، RAG، آموزش AI |
| **مدل کاستوم Rituq-Inside (آینده)** | `https://huggingface.co/sosa123454321/joblink-rituq-06b-inside` | ⏳ باید بسازی — ready_to_train | Qwen3-0.6B fine-tuned روی 1143 rows |
| **مدل RAG-Master (آینده)** | `https://huggingface.co/sosa123454321/joblink-rag-master-bge` | ⏳ باید بسازی | bge-m3 hybrid |
| **مدل Baby-Rituq (آینده)** | `https://huggingface.co/sosa123454321/joblink-baby-rituq-phi3` | ⏳ باید بسازی | Phi-3-mini offline |

### 11 مدل اصلی — لینک مستقیم HF

| ID | نام | لینک HF | Live Test 2026-09-14 | Iran Score |
|---|---|---|---|---|
| emb_qwen3_06b | Qwen3-Embedding-0.6B | `https://huggingface.co/Qwen/Qwen3-Embedding-0.6B` | ✅ OK dim 1024 delta 0.159 | 10 |
| emb_qwen3_4b | Qwen3-Embedding-4B | `https://huggingface.co/Qwen/Qwen3-Embedding-4B` | ✅ OK dim 2560 | 7 |
| emb_qwen3_8b | Qwen3-Embedding-8B | `https://huggingface.co/Qwen/Qwen3-Embedding-8B` | ✅ OK dim 4096 | 5 |
| emb_e5_large | multilingual-e5-large | `https://huggingface.co/intfloat/multilingual-e5-large` | ✅ OK dim 1024 delta 0.052 ضعیف | 8 |
| emb_e5_instruct | e5-large-instruct | `https://huggingface.co/intfloat/multilingual-e5-large-instruct` | ✅ (same) | 8 |
| emb_jina_v3 | jina-embeddings-v3 | `https://huggingface.co/jinaai/jina-embeddings-v3` | ❌ FAIL no provider | 9 |
| emb_bge_m3 | bge-m3 | `https://huggingface.co/BAAI/bge-m3` | ✅ OK dim 1024 delta 0.160 | 9 |
| llm_qwen25_7b | Qwen2.5-7B-Instruct | `https://huggingface.co/Qwen/Qwen2.5-7B-Instruct` | ❌ needs enable providers | 8 |
| llm_aya23_8b | aya-23-8B | `https://huggingface.co/CohereForAI/aya-23-8B` | ❌ no provider | 7 |
| llm_llama31_8b | Llama-3.1-8B-Instruct | `https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct` | ✅ CHAT OK | 6 |
| llm_phi3 | Phi-3-mini-4k | `https://huggingface.co/microsoft/Phi-3-mini-4k-instruct` | ❌ needs provider | 10 |

### 3 مدل کاستوم Rituq — لینک آینده

- Rituq-Inside: `https://huggingface.co/sosa123454321/joblink-rituq-06b-inside`
- RAG-Master: `https://huggingface.co/sosa123454321/joblink-rag-master-bge`
- Baby-Rituq: `https://huggingface.co/sosa123454321/joblink-baby-rituq-phi3`

---

## 2. تلگرام — ربات، کانال، گروه

| نوع | آیدی پیشنهادی | لینک | وضعیت | توضیح |
|---|---|---|---|---|
| **ربات** | `@joblink_bot` | `https://t.me/joblink_bot` | ⏳ باید بسازی — BotFather /newbot | 8 دستور: /start /katil /hayir /shoghle /danesh /azmoon /help |
| **کانال اصلی** | `@joblink_tr_ir` | `https://t.me/joblink_tr_ir` | ⏳ باید بسازی | هر روز 5 آگهی ترکیه + تحلیل حقوقی |
| **گروه بحث** | `@joblink_group` | `https://t.me/joblink_group` | ⏳ باید بسازی | بحث آزاد + ربات داخل گروه |
| **گروه OT خصوصی** | `@joblink_ot_private` | `https://t.me/joblink_ot_private` | ⏳ باید بسازی — private | فقط ادمین‌ها + ربات — هماهنگی |
| **ادمین** | `@sosa123454321` | `https://t.me/sosa123454321` | ✅ موجود | شما |

**دستورات ربات برای BotFather:**
```
start - شروع و رضایت
katil - ثبت‌نام (opt-in)
hayir - حذف کامل داده‌ها
haziri - آماده مهاجرت به ترکیه
dorkari - فقط دورکاری
shoghle - 5 پیشنهاد جدید
danesh - پایگاه دانش 12 حوزه
azmoon - آزمون 10 سوالی
help - راهنما
```

---

## 3. 10 سایت ترکیه — منبع آگهی (Scraping)

| # | سایت | لینک | نوع | توضیح |
|---|---|---|---|---|
| 1 | eleman.net | `https://www.eleman.net` | یقه‌آبی اصلی | 97 آگهی تست از اینجا — بیشترین |
| 2 | kariyer.net | `https://www.kariyer.net` | عمومی | بزرگ‌ترین سایت کاریابی TR |
| 3 | iskur.gov.tr | `https://www.iskur.gov.tr` | دولتی | اداره کار ترکیه — رسمی |
| 4 | yenibiris.com | `https://www.yenibiris.com` | عمومی | قدیمی |
| 5 | secretcv.com | `https://www.secretcv.com` | عمومی | |
| 6 | elemanonline.com.tr | `https://www.elemanonline.com.tr` | یقه‌آبی | |
| 7 | isinolsun.com | `https://www.isinolsun.com` | یقه‌آبی | |
| 8 | jooble.org/tr | `https://tr.jooble.org` | aggregator | جمع‌کننده آگهی |
| 9 | indeed.com.tr | `https://tr.indeed.com` | aggregator | |
| 10 | linkedin.com/jobs (TR) | `https://www.linkedin.com/jobs/search/?location=Turkey` | حرفه‌ای | برای senior |

**کد اسکرپر:** `joblink/scrapers/` — هر سایت یک فایل

---

## 4. 10 سایت ایران — فقط کانال جذب (نه اسکرپ رزومه)

| # | سایت | لینک | نقش | توضیح |
|---|---|---|---|---|
| 1 | divar.ir | `https://divar.ir` | جذب | آگهی بده: "کار در ترکیه با JobLink" |
| 2 | sheypoor.com | `https://www.sheypoor.com` | جذب | |
| 3 | jobinja.ir | `https://jobinja.ir` | جذب | |
| 4 | jobvision.ir | `https://jobvision.ir` | جذب | |
| 5 | iran-talent.com | `https://www.iran-talent.com` | جذب | |
| 6 | quera.org (کاریابی) | `https://quera.org` | جذب | جامعه برنامه‌نویس |
| 7 | porsline.ir | `https://porsline.ir` | نظرسنجی | برای نیازسنجی |
| 8 | telegram channels | `https://t.me/s/jobs` | جذب | کانال‌های کاریابی فارسی |
| 9 | instagram | `https://instagram.com` | جذب | پیج اینستا JobLink |
| 10 | linkedin (IR) | `https://www.linkedin.com` | جذب | گروه ایرانیان مقیم ترکیه |

**نکته حقوقی:** هیچ رزومه‌ای از این 10 سایت برداشته نمی‌شود — فقط opt-in تلگرام (KVKK/GDPR)

---

## 5. سایت‌های حقوقی و دولتی — برای RAG

| موضوع | سایت | لینک |
|---|---|---|
| اجازه کار ترکیه | e-izin | `https://eizin.csgb.gov.tr` |
| KVKK | kvkk.gov.tr | `https://www.kvkk.gov.tr` |
| SGK | sgk.gov.tr | `https://www.sgk.gov.tr` |
| حداقل دستمزد | csgb.gov.tr | `https://www.csgb.gov.tr` |
| TÜİK مهاجرت | tuik.gov.tr | `https://www.tuik.gov.tr` |
| IOM | iom.int | `https://www.iom.int` |
| OFAC تحریم | ofac.treasury.gov | `https://ofac.treasury.gov` |
| ESCO مهارت | esco.ec.europa.eu | `https://esco.ec.europa.eu` |
| O*NET | onetonline.org | `https://www.onetonline.org` |
| EU AI Act | artificialintelligenceact.eu | `https://artificialintelligenceact.eu` |

---

## 6. Cloudflare — زیرساخت

| سرویس | لینک | توضیح |
|---|---|---|
| Workers | `https://workers.cloudflare.com` | API + bot webhook |
| D1 | `https://developers.cloudflare.com/d1/` | DB اصلی (mirror knowledge.db) |
| R2 | `https://developers.cloudflare.com/r2/` | ذخیره رزومه + logo |
| Workers AI | `https://developers.cloudflare.com/workers-ai/` | bge-m3 fallback اگر HF فیلتر |
| Pages | `https://pages.cloudflare.com` | لندینگ joblink.example |

**دامنه پیشنهادی:** `joblink.example` یا `joblink.ir` یا `joblink.tr`

---

## 7. کد و مستندات

| نام | لینک | وضعیت |
|---|---|---|
| GitHub کد | `https://github.com/sosa123454321/joblink` | ⏳ باید push |
| README اصلی | `README.md` | ✅ |
| PLAN-FA | `PLAN-FA.md` | ✅ |
| KNOWLEDGE-BASE-FA | `KNOWLEDGE-BASE-FA.md` | ✅ |
| AI-MODELS-FA | `AI-MODELS-FA.md` | ✅ 11 مدل + TOP3 |
| RITUQ-INSIDER-FA | `RITUQ-INSIDER-FA.md` | ✅ 3 کاستوم + 10 RAG + 20 emb |
| CRITIQUE-FA | `CRITIQUE-FA.md` | ✅ نقد توکن‌ها |
| CRITIQUE-RITUQ-FA | `CRITIQUE-RITUQ-FA.md` | ✅ نقد Rituq |
| BOT-CHANNEL-SETUP-FA | `BOT-CHANNEL-SETUP-FA.md` | ✅ لوگو + توضیحات کانال/گروه |
| LINKS-FA | `LINKS-FA.md` | ✅ این فایل |
| HF-STATUS-FA | `HF-STATUS-FA.md` | ⏳ باید بسازی |

---

## 8. لینک‌های سریع — کپی پیست

**برای README و کانال:**

```markdown
🤖 ربات: https://t.me/joblink_bot
📢 کانال: https://t.me/joblink_tr_ir
👥 گروه: https://t.me/joblink_group
📚 دیتاست: https://huggingface.co/datasets/sosa123454321/joblink-knowledge-fa-tr
🚀 Space: https://huggingface.co/spaces/sosa123454321/joblink
💻 کد: https://github.com/sosa123454321/joblink
📖 داک: https://github.com/sosa123454321/joblink/blob/main/PLAN-FA.md

مدل‌ها:
- Qwen3-0.6B: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
- bge-m3: https://huggingface.co/BAAI/bge-m3
- e5-large: https://huggingface.co/intfloat/multilingual-e5-large
- Llama-3.1-8B: https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
```

**برای تلگرام:**

```
🤝 JobLink — کار ایران ↔ ترکیه

ربات: @joblink_bot
کانال: @joblink_tr_ir
گروه: @joblink_group
دیتاست: hf.co/datasets/sosa123454321/joblink-knowledge-fa-tr
Space: hf.co/spaces/sosa123454321/joblink
```

---

## 9. چک‌لیست لینک‌ها

- [ ] ساخت ربات @joblink_bot در BotFather
- [ ] ساخت کانال @joblink_tr_ir + آپلود logo.png
- [ ] ساخت گروه @joblink_group + اضافه کردن ربات به عنوان ادمین
- [ ] ساخت گروه خصوصی @joblink_ot_private
- [ ] push دیتاست به HF: `huggingface.co/datasets/sosa123454321/joblink-knowledge-fa-tr`
- [ ] deploy Space به HF: `huggingface.co/spaces/sosa123454321/joblink`
- [ ] push کد به GitHub: `github.com/sosa123454321/joblink`
- [ ] تست: ربات /start → /katil → رزومه → /shoghle
- [ ] تست: گروه /danesh d01 → باید جواب بدهد
- [ ] تست: Space 8 تب → همه کار می‌کند
