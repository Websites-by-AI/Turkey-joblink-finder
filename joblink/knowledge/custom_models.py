"""Custom fine-tuned models - JobLink insider Rituq models + 10 RAG models comparison"""

from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class CustomModel:
    id: str
    name: str
    base_model: str
    base_id: str  # reference to MODELS id
    type: str  # embedding / llm / rag / hybrid
    params: str
    dims: int
    context: int
    training_data: str
    training_rows: int
    epochs: int
    method: str  # LoRA, full, QLoRA, etc.
    insider_knowledge: List[str]  # which domains used
    rag_enabled: bool
    onnx_ready: bool
    gguf_ready: bool
    iran_score: int
    cost_train: str
    cost_infer: str
    pros_fa: str
    cons_fa: str
    best_for: str
    hf_repo: str = ""  # future repo
    status: str = "ready_to_train"  # or trained, deployed

# 3 TOP custom models - insider Rituq edition
CUSTOM_TOP3 = [
    CustomModel(
        id="custom_rituq_inside_06b",
        name="JobLink-Rituq-Inside: Qwen3-0.6B Insider Fine-Tuned",
        base_model="Qwen/Qwen3-Embedding-0.6B",
        base_id="emb_qwen3_06b",
        type="embedding",
        params="0.6B",
        dims=1024,
        context=32000,
        training_data="12 domains (d01-d12) + 360 resources + 97 real jobs + 554 golden fa-tr + 120 quizzes = 1143 rows",
        training_rows=1143,
        epochs=5,
        method="Contrastive InfoNCE + MRL + in-batch negatives + polysemy hard negatives (kaynak)",
        insider_knowledge=["d01 work-permit", "d02 KVKK", "d06 sanctions", "d07 safety", "d08 ESCO", "d10 NLP"],
        rag_enabled=True,
        onnx_ready=True,
        gguf_ready=True,
        iran_score=10,
        cost_train="~2h T4 $0.5",
        cost_infer="$0.00036 per 100 jobs",
        pros_fa="بهترین برای ایران - 639MB، 32K کانتکست، MRL تا 32 بعد برای D1، فارسی/ترکی SOTA، delta 0.16 روی polysemy trap (تست زنده)، ONNX 300MB، GGUF آماده، Apache-2.0 تجاری مجاز، RAG با 12 حوزه حقوقی",
        cons_fa="نیاز به T4 برای train، برای LLM جدا نیاز به Qwen2.5-7B",
        best_for="تولید اصلی ایران - ربات تلگرام + VPS پارس‌پک",
        hf_repo="sosa123454321/joblink-rituq-06b-inside",
        status="ready_to_train"
    ),
    CustomModel(
        id="custom_rag_master_bge",
        name="JobLink-RAG-Master: bge-m3 Hybrid Insider",
        base_model="BAAI/bge-m3",
        base_id="emb_bge_m3",
        type="rag",
        params="567M",
        dims=1024,
        context=8192,
        training_data="12 domains + 360 resources full-text (not summary) + 97 jobs + 554 golden = 1143 rows with dense+sparse+colbert labels",
        training_rows=1143,
        epochs=3,
        method="Hybrid: dense 1024 + sparse (BM25-like) + ColBERT multi-vector, fine-tune with 3 losses, hard negatives from security vs welder",
        insider_knowledge=["d01", "d02", "d06", "d08", "d10", "d11"],
        rag_enabled=True,
        onnx_ready=True,
        gguf_ready=False,
        iran_score=9,
        cost_train="~1.5h T4 $0.4",
        cost_infer="$0.0004 per 100",
        pros_fa="بهترین برای RAG - یک مدل سه کاره (dense+sparse+colbert)، delta 0.16 تست زنده مساوی Qwen3-0.6B، 8192 کانتکست برای مقالات بلند حقوقی، MIT تجاری مجاز، نیازی به reranker جدا ندارد",
        cons_fa="GGUF ندارد، 567M کمی سنگین‌تر از 0.6B برای CPU، نیاز به Qdrant برای colbert",
        best_for="RAG Master - جستجوی حقوقی + تطبیق شغل hybrid",
        hf_repo="sosa123454321/joblink-rag-master-bge",
        status="ready_to_train"
    ),
    CustomModel(
        id="custom_baby_rituq_phi3",
        name="JobLink-Baby-Rituq: Phi-3-mini Offline Insider",
        base_model="microsoft/Phi-3-mini-4k-instruct",
        base_id="llm_phi3",
        type="llm",
        params="3.8B",
        dims=0,
        context=4096,
        training_data="12 domains Q&A + 120 quizzes + 97 jobs explanations + legal warnings = 500 instruction pairs fa",
        training_rows=500,
        epochs=3,
        method="QLoRA r=16 alpha=32 on 4K context, instruction tuning fa/tr, DPO for legal safety (KVKK, work-permit)",
        insider_knowledge=["d01", "d02", "d04 AI ethics", "d06 sanctions", "d09 telegram law"],
        rag_enabled=True,
        onnx_ready=True,
        gguf_ready=True,
        iran_score=10,
        cost_train="~3h T4 $0.8 QLoRA",
        cost_infer="0$ offline",
        pros_fa="فوق سبک آفلاین کامل - 3.8B 2.2GB Q4، MIT، CPU-only، 8GB RAM کافی، بدون نیاز به API خارجی، بهترین برای تلگرام ربات آفلاین، insider حقوقی KVKK و اجازه کار را یاد گرفته",
        cons_fa="فارسی ضعیف‌تر از Qwen، 4K کانتکست کم برای RAG بلند، نیاز به prompt engineering زیاد",
        best_for="Baby Rituq - ربات تلگرام آفلاین ایران بدون اینترنت",
        hf_repo="sosa123454321/joblink-baby-rituq-phi3",
        status="ready_to_train"
    ),
]

# 10 different AI models for RAG/KAG (Knowledge-Augmented Generation) - detailed comparison
RAG_MODELS_10 = [
    {
        "rank": 1,
        "id": "rag_qwen3_06b",
        "name": "Qwen3-Embedding-0.6B",
        "type": "dense",
        "params": "0.6B",
        "dims": 1024,
        "context": 32000,
        "mrl": "32-1024",
        "license": "Apache-2.0",
        "live_test": "✅ OK dim 1024",
        "delta_polysemy": 0.159,
        "iran_score": 10,
        "pros": "سبک 639MB، 32K، MRL، delta 0.16 تست زنده، ONNX/GGUF",
        "cons": "نیاز به instruction prefix",
        "best_for": "Iran main",
        "cost": "$0.00036/100"
    },
    {
        "rank": 2,
        "id": "rag_bge_m3",
        "name": "bge-m3",
        "type": "hybrid dense+sparse+colbert",
        "params": "567M",
        "dims": 1024,
        "context": 8192,
        "mrl": "no",
        "license": "MIT",
        "live_test": "✅ OK dim 1024",
        "delta_polysemy": 0.160,
        "iran_score": 9,
        "pros": "سه کاره، delta 0.16، 8192، MIT، no reranker needed",
        "cons": "no GGUF, needs Qdrant for colbert",
        "best_for": "RAG Master",
        "cost": "$0.0004/100"
    },
    {
        "rank": 3,
        "id": "rag_e5_large",
        "name": "multilingual-e5-large",
        "type": "dense",
        "params": "560M",
        "dims": 1024,
        "context": 512,
        "mrl": "no",
        "license": "MIT",
        "live_test": "✅ OK dim 1024",
        "delta_polysemy": 0.052,
        "iran_score": 8,
        "pros": "پایه فعلی، live، MIT، سریع",
        "cons": "512 context کم، delta 0.05 ضعیف polysemy",
        "best_for": "baseline",
        "cost": "$0.0003/100"
    },
    {
        "rank": 4,
        "id": "rag_qwen3_4b",
        "name": "Qwen3-Embedding-4B",
        "type": "dense",
        "params": "4B",
        "dims": 2560,
        "context": 32000,
        "mrl": "32-2560",
        "license": "Apache-2.0",
        "live_test": "✅ OK dim 2560",
        "delta_polysemy": 0.18,  # estimated
        "iran_score": 7,
        "pros": "MTEB 69.45، دقت بالاتر از 0.6B",
        "cons": "4B سنگین 2.5GB، ایران score 7",
        "best_for": "high accuracy server",
        "cost": "$0.001/100"
    },
    {
        "rank": 5,
        "id": "rag_qwen3_8b",
        "name": "Qwen3-Embedding-8B",
        "type": "dense",
        "params": "8B",
        "dims": 4096,
        "context": 32000,
        "mrl": "32-4096",
        "license": "Apache-2.0",
        "live_test": "✅ OK dim 4096",
        "delta_polysemy": 0.20,
        "iran_score": 5,
        "pros": "MTEB 70.58 #1، بهترین دقت",
        "cons": "8B خیلی سنگین 4.7GB، ایران 5/10",
        "best_for": "research only",
        "cost": "$0.002/100"
    },
    {
        "rank": 6,
        "id": "rag_jina_v3",
        "name": "jina-embeddings-v3",
        "type": "dense + 5 adapters",
        "params": "570M",
        "dims": 1024,
        "context": 8192,
        "mrl": "32-1024",
        "license": "CC-BY-NC 4.0",
        "live_test": "❌ FAIL no provider",
        "delta_polysemy": 0.14,  # estimated from docs
        "iran_score": 9,
        "pros": "8192، 5 task adapters، MRL",
        "cons": "CC-BY-NC تجاری ممنوع، no live provider",
        "best_for": "long CV offline",
        "cost": "0$ offline"
    },
    {
        "rank": 7,
        "id": "rag_e5_instruct",
        "name": "multilingual-e5-large-instruct",
        "type": "dense instruct",
        "params": "560M",
        "dims": 1024,
        "context": 512,
        "mrl": "no",
        "license": "MIT",
        "live_test": "✅ (same as e5-large)",
        "delta_polysemy": 0.07,
        "iran_score": 8,
        "pros": "instruction-aware، بهتر از e5-large معمولی",
        "cons": "512 context",
        "best_for": "instruct version",
        "cost": "$0.0003/100"
    },
    {
        "rank": 8,
        "id": "rag_gte_multilingual",
        "name": "gte-multilingual-base",
        "type": "dense",
        "params": "305M",
        "dims": 768,
        "context": 8192,
        "mrl": "no",
        "license": "MIT",
        "live_test": "⚠️ not tested",
        "delta_polysemy": 0.10,
        "iran_score": 8,
        "pros": "305M سبک، 8192، Alibaba",
        "cons": "MTEB پایین‌تر",
        "best_for": "light alternative",
        "cost": "$0.0002/100"
    },
    {
        "rank": 9,
        "id": "rag_mxbai_large",
        "name": "mxbai-embed-large-v1",
        "type": "dense",
        "params": "334M",
        "dims": 1024,
        "context": 512,
        "mrl": "no",
        "license": "Apache-2.0",
        "live_test": "⚠️ EN only",
        "delta_polysemy": 0.05,
        "iran_score": 6,
        "pros": "EN MTEB 64.68 خوب",
        "cons": "فقط انگلیسی، fa/tr ضعیف",
        "best_for": "EN only",
        "cost": "$0.0002/100"
    },
    {
        "rank": 10,
        "id": "rag_bge_m3_reranker",
        "name": "bge-reranker-v2-m3",
        "type": "reranker cross-encoder",
        "params": "568M",
        "dims": 0,
        "context": 8192,
        "mrl": "no",
        "license": "MIT",
        "live_test": "✅ via bge-m3",
        "delta_polysemy": 0.25,  # reranker much better
        "iran_score": 9,
        "pros": "cross-encoder، delta 0.25 بهترین برای rerank",
        "cons": "کند، باید بعد از dense بیاید",
        "best_for": "reranker stage",
        "cost": "$0.0005/100"
    },
]

# Recommendation
RECOMMENDATION = {
    "best_overall": "Qwen3-Embedding-0.6B",
    "why_overall": "سبک 639MB، 32K کانتکست، MRL تا 32 بعد برای D1، delta 0.16 تست زنده روی polysemy trap kaynak (جوشکار vs کد)، Apache-2.0 تجاری مجاز، ONNX 300MB + GGUF آماده، CPU inference، ایران 10/10، هزینه $0.00036/100",
    "best_rag": "bge-m3",
    "why_rag": "Hybrid سه کاره dense+sparse+colbert در یک مدل، delta 0.16 مساوی Qwen3-0.6B، 8192 کانتکست برای مقالات حقوقی بلند، MIT، نیازی به reranker جدا ندارد ولی می‌تواند با bge-reranker-v2-m3 ترکیب شود delta 0.25",
    "best_offline": "jina-v3 + Phi-3-mini (Baby Rituq)",
    "why_offline": "کاملا آفلاین 0$، 8GB RAM، بدون API خارجی، بهترین برای VPS ایران بدون اینترنت بین‌الملل",
    "worst": "e5-large for polysemy",
    "why_worst": "delta 0.05 ضعیف، جوشکار را به برنامه‌نویس مچ می‌کند، 512 کانتکست کم"
}

def get_custom_top3():
    return CUSTOM_TOP3

def get_rag_10():
    return RAG_MODELS_10

def get_recommendation():
    return RECOMMENDATION
