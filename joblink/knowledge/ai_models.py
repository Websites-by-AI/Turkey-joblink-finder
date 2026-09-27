"""10 AI models comparison for JobLink + Top 3 custom models"""

from dataclasses import dataclass, field
from typing import List, Literal

@dataclass
class AIModel:
    id: str
    name: str
    type: Literal["embedding","llm","reranker"]
    params: str
    dims: int | None
    context: int
    languages: List[str]
    license: str
    hf_id: str
    inference_live: bool  # tested via /api/models?expand[]=inferenceProviderMapping
    cost_per_1m: str
    pros_fa: str
    cons_fa: str
    best_for: str
    iran_score: int  # 0-10 how good for Iran offline/CPU
    score_mteb: float | None = None

MODELS = [
    AIModel(
        id="emb_qwen3_06b",
        name="Qwen3-Embedding-0.6B",
        type="embedding",
        params="0.6B",
        dims=1024,
        context=32768,
        languages=["fa","tr","en","ar","100+"],
        license="Apache-2.0",
        hf_id="Qwen/Qwen3-Embedding-0.6B",
        inference_live=True,
        cost_per_1m="$0.01",
        pros_fa="سبک‌ترین مدل SOTA چندزبانه - 639MB، 32K کانتکست، MRL تا 32 بعد، MTEB multilingual 64.33، فارسی و ترکی عالی، ONNX و GGUF آماده، instruction-aware",
        cons_fa="دقت کمتر از 4B/8B، نیاز به fine-tune برای اصطلاحات یقه‌آبی ترکیه",
        best_for="بهترین انتخاب برای ایران - CPU/VPS ایران، ربات تلگرام، آفلاین",
        iran_score=10,
        score_mteb=64.33
    ),
    AIModel(
        id="emb_qwen3_4b",
        name="Qwen3-Embedding-4B",
        type="embedding",
        params="4B",
        dims=2560,
        context=32768,
        languages=["fa","tr","en","100+"],
        license="Apache-2.0",
        hf_id="Qwen/Qwen3-Embedding-4B",
        inference_live=True,
        cost_per_1m="$0.05",
        pros_fa="بالانس عالی دقت/حجم - MTEB 69.45 multilingual، 2560 بعد قابل truncate به 1024، 32K کانتکست",
        cons_fa="2.5GB حجم، نیاز به GPU T4 برای fine-tune، گران‌تر",
        best_for="سرور اصلی JobLink - دقت بالا با هزینه متوسط",
        iran_score=7,
        score_mteb=69.45
    ),
    AIModel(
        id="emb_qwen3_8b",
        name="Qwen3-Embedding-8B",
        type="embedding",
        params="8B",
        dims=4096,
        context=32768,
        languages=["fa","tr","en","100+"],
        license="Apache-2.0",
        hf_id="Qwen/Qwen3-Embedding-8B",
        inference_live=True,
        cost_per_1m="$0.10",
        pros_fa="بهترین MTEB multilingual 70.58، 4096 بعد، SOTA، instruction-aware، بهترین برای RAG پیچیده",
        cons_fa="4.7GB Q4، 15GB FP16، فقط GPU، برای ایران سنگین",
        best_for="تحقیقات و ارزیابی نهایی، نه تولید ایران",
        iran_score=5,
        score_mteb=70.58
    ),
    AIModel(
        id="emb_e5_large",
        name="multilingual-e5-large",
        type="embedding",
        params="560M",
        dims=1024,
        context=512,
        languages=["fa","tr","en","100"],
        license="MIT",
        hf_id="intfloat/multilingual-e5-large",
        inference_live=True,
        cost_per_1m="$0.02",
        pros_fa="مدل فعلی JobLink - تست شده live روی HF Router (hf-inference + deepinfra)، MIT، 1024 بعد، سریع، مستندات زیاد",
        cons_fa="512 توکن فقط، قدیمی‌تر از Qwen3، نیاز به prefix query/passage",
        best_for="پایه فعلی - اگر توکن scope درست شود سریع کار می‌کند",
        iran_score=8,
        score_mteb=63.22
    ),
    AIModel(
        id="emb_e5_instruct",
        name="multilingual-e5-large-instruct",
        type="embedding",
        params="560M",
        dims=1024,
        context=512,
        languages=["fa","tr","en","100"],
        license="MIT",
        hf_id="intfloat/multilingual-e5-large-instruct",
        inference_live=True,
        cost_per_1m="$0.02",
        pros_fa="نسخه instruct e5-large - بهتر برای query های پیچیده مثل 'یک شغل مناسب برای این رزومه'",
        cons_fa="همان محدودیت 512 توکن",
        best_for="جایگزین مستقیم e5-large با instruction",
        iran_score=8,
        score_mteb=65.53
    ),
    AIModel(
        id="emb_jina_v3",
        name="jina-embeddings-v3",
        type="embedding",
        params="570M",
        dims=1024,
        context=8192,
        languages=["fa","tr","en","89"],
        license="CC-BY-NC? (check) + API",
        hf_id="jinaai/jina-embeddings-v3",
        inference_live=True,
        cost_per_1m="$0.02 API",
        pros_fa="8192 توکن، 5 LoRA adapter برای task مختلف (retrieval, classification, text-matching)، MRL تا 32 بعد، بهتر از e5-large در تمام تست‌های چندزبانه (طبق مقاله Jina)",
        cons_fa="لایسنس CC-BY-NC برای تجاری محدود، 570M پارامتر",
        best_for="جایگزین سبک با کانتکست طولانی - بهترین برای رزومه‌های بلند",
        iran_score=9,
        score_mteb=63.35
    ),
    AIModel(
        id="emb_bge_m3",
        name="bge-m3",
        type="embedding",
        params="567M",
        dims=1024,
        context=8192,
        languages=["fa","tr","en","100+"],
        license="MIT",
        hf_id="BAAI/bge-m3",
        inference_live=True,
        cost_per_1m="self-hosted",
        pros_fa="سه کاره: dense + sparse (BM25-like) + ColBERT multi-vector در یک forward، 8192 توکن، 100+ زبان، MIT، بهترین برای hybrid search",
        cons_fa="فقط dense 1024، نیاز به FlagEmbedding برای sparse",
        best_for="Hybrid RAG - ترکیب BM25 + dense + rerank در یک مدل",
        iran_score=9,
        score_mteb=59.56
    ),
    AIModel(
        id="llm_qwen25_7b",
        name="Qwen2.5-7B-Instruct",
        type="llm",
        params="7.6B",
        dims=None,
        context=131072,
        languages=["fa","tr","en","ar","29+"],
        license="Qwen License (Apache-like)",
        hf_id="Qwen/Qwen2.5-7B-Instruct",
        inference_live=True,
        cost_per_1m="$0.30 input/output",
        pros_fa="بهترین مدل چندزبانه برای فارسی و ترکی - TurkishMMLU 54.28 vs Llama 45.61، 131K کانتکست، 8K خروجی، فارسی عالی، instruction following 74.87، QLoRA آماده",
        cons_fa="7.6B نیاز به GPU 16GB، GGUF 4.7GB Q4",
        best_for="LLM اصلی JobLink - توضیح فارسی چرا مچ + RAG",
        iran_score=8,
        score_mteb=None
    ),
    AIModel(
        id="llm_aya23_8b",
        name="aya-23-8B",
        type="llm",
        params="8B",
        dims=None,
        context=8192,
        languages=["fa","tr","en","23"],
        license="CC-BY-NC",
        hf_id="CohereLabs/aya-23-8B",
        inference_live=False,
        cost_per_1m="self-hosted",
        pros_fa="مخصوص 23 زبان شامل فارسی و ترکی - depth نه breadth، بهترین برای فارسی محاوره‌ای، 8B قابل اجرا روی T4، دستورالعمل‌های چندزبانه عالی",
        cons_fa="CC-BY-NC غیرتجاری، کانتکست 8192 کم، روی Inference Providers نیست (self-hosted)",
        best_for="جایگزین Qwen برای فارسی محاوره‌ای و ترکی - اگر لایسنس NC قبول",
        iran_score=7,
        score_mteb=None
    ),
    AIModel(
        id="llm_llama31_8b",
        name="Meta-Llama-3.1-8B-Instruct",
        type="llm",
        params="8B",
        dims=None,
        context=131072,
        languages=["en","tr","fa (weak)"],
        license="Llama 3.1 License",
        hf_id="meta-llama/Meta-Llama-3.1-8B-Instruct",
        inference_live=True,
        cost_per_1m="$0.02-0.05 via novita",
        pros_fa="ارزان‌ترین روی HF Router ($0.02/1M)، 128K کانتکست، جامعه بزرگ، تست شده در ai-check (pricing $0.02 input $0.05 output)",
        cons_fa="فارسی ضعیف‌تر از Qwen/Aya، ترکی متوسط",
        best_for="ارزان و سریع برای انگلیسی/ترکی، fallback اگر Qwen در دسترس نباشد",
        iran_score=6,
        score_mteb=None
    ),
]

# Top 3 custom models for JobLink
TOP3 = [
    {
        "rank": 1,
        "name": "JobLink-Iran-Light: Qwen3-0.6B + Qwen2.5-7B",
        "embedding_id": "emb_qwen3_06b",
        "llm_id": "llm_qwen25_7b",
        "why": "بهترین برای ایران - سبک (639MB emb + 4.7GB LLM Q4)، 32K+131K کانتکست، فارسی و ترکی عالی (TurkishMMLU 54.28)، Apache-2.0 + Qwen License تجاری مجاز، ONNX و GGUF آماده، CPU inference ممکن، MRL برای کاهش بعد به 512 برای D1",
        "architecture": "Bi-encoder: Query = Instruct: یک شغل مناسب برای این رزومه پیدا کن\\nQuery: {cv_fa} → 1024 dim → truncate 512 برای ذخیره → cosine search روی 97 آگهی + 360 دانش → Top 5 → Reranker Qwen3-Reranker-0.6B → LLM Qwen2.5-7B با RAG chunk از knowledge base (KVKK + اجازه کار) → توضیح فارسی + هشدار حقوقی",
        "fine_tune_steps": [
            "ساخت golden dataset 500 جفت: (رزومه فارسی → آگهی ترکی مثبت/منفی) از LEXICON + ESCO",
            "Contrastive loss InfoNCE با in-batch negatives",
            "5 epoch, batch 32, lr 2e-5, warmup 10% روی T4 HF Space",
            "ارزیابی Recall@5 روی 14 رزومه مصنوعی - هدف 0.80+",
            "ONNX export: optimum-cli export onnx --model Qwen/Qwen3-Embedding-0.6B --task feature-extraction qwen3-06b-onnx/",
            "Quantization: int8 → 300MB برای VPS ایران"
        ],
        "cost": "Training ~2h T4 ($0.5), Inference 36k tokens → $0.00036, LLM $0.000672 → total <$0.01 per 100 jobs",
        "iran_deploy": "VPS ایران: python -m optimum.onnxruntime + FastAPI, یا GGUF via llama.cpp, Cloudflare Workers AI fallback bge-m3"
    },
    {
        "rank": 2,
        "name": "JobLink-Balanced: e5-large + Llama-3.1-8B",
        "embedding_id": "emb_e5_large",
        "llm_id": "llm_llama31_8b",
        "why": "بالانس دقت/هزینه/دسترسی - هر دو مدل live روی HF Router (تست شده 2026-09-13)، ارزان‌ترین ($0.02/1M)، MIT + Llama 3.1 License تجاری مجاز، مستندات زیاد، کد فعلی JobLink با e5 کار می‌کند",
        "architecture": "Query: 'query: {cv}' Passage: 'passage: {job}' → e5-large 1024 dim → BM25 blend 0.34 skill/0.26 semantic → Top 5 → Llama-3.1-8B با prompt فارسی + قوانین KVKK → توضیح",
        "fine_tune_steps": [
            "نیازی به fine-tune سنگین نیست - فقط LoRA adapter برای اصطلاحات یقه‌آبی",
            "ساخت 200 جفت fa→tr با تمرکز بر kaynak polysemy (جوشکاری vs منبع کد)",
            "1 epoch, lr 1e-5",
            "تست: جوشکار نباید به software engineer مچ شود"
        ],
        "cost": "ارزان‌ترین - $0.000672 per 84 explanations",
        "iran_deploy": "HF Router + Cloudflare Workers AI, اگر فیلتر: Space proxy"
    },
    {
        "rank": 3,
        "name": "JobLink-UltraLight-Offline: jina-v3 + Phi-3-mini",
        "embedding_id": "emb_jina_v3",
        "llm_id": "llm_phi3",
        "why": "فوق سبک آفلاین کامل برای ایران بدون اینترنت بین‌الملل - jina-v3 570M 8192 توکن با 5 task adapter، Phi-3-mini 3.8B 4K کانتکست، هر دو ONNX و GGUF، CPU-only، بدون نیاز به API خارجی",
        "architecture": "jina-v3 task=retrieval.query 512 dim (MRL) → Qdrant local → Phi-3-mini با RAG → توضیح کوتاه فارسی",
        "fine_tune_steps": [
            "بدون fine-tune LLM - فقط prompt engineering فارسی",
            "Embedding: fine-tune jina-v3 با 300 جفت fa-tr",
            "Export ONNX: Xenova/jina-embeddings-v3 already ONNX ready",
            "Phi-3 GGUF Q4 2.2GB"
        ],
        "cost": "0$ - کاملا آفلاین",
        "iran_deploy": "لپ‌تاپ یا VPS ایران بدون GPU - 8GB RAM کافی"
    }
]

# Add Phi-3 as extra for top3
MODELS.append(
    AIModel(
        id="llm_phi3",
        name="Phi-3-mini-4k-instruct",
        type="llm",
        params="3.8B",
        dims=None,
        context=4096,
        languages=["en","tr (weak)","fa (weak)"],
        license="MIT",
        hf_id="microsoft/Phi-3-mini-4k-instruct",
        inference_live=True,
        cost_per_1m="$0.02",
        pros_fa="فوق سبک 3.8B - 2.2GB Q4، MIT، 4K کانتکست، CPU inference عالی، بهترین برای آفلاین کامل ایران",
        cons_fa="فارسی ضعیف، نیاز به prompt فارسی قوی",
        best_for="Ultra-light offline Iran",
        iran_score=10,
        score_mteb=None
    )
)
