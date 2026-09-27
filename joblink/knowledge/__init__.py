"""JobLink Knowledge Base - 12 domain + 11 AI models + TOP3 + RAG + fine-tune + Custom Rituq + News 10"""
from .domains import DOMAINS, Domain
from .resources import RESOURCES, Resource
from .quiz import QUIZZES, QuizQuestion, get_quiz
try:
    from .ai_models import MODELS, TOP3, AIModel
except Exception:
    MODELS = []; TOP3 = []; AIModel = None
try:
    from .custom_models import CUSTOM_TOP3, RAG_MODELS_10, RECOMMENDATION
except Exception:
    CUSTOM_TOP3 = []; RAG_MODELS_10 = []; RECOMMENDATION = {}
try:
    from .news import NEWS_10
except Exception:
    NEWS_10 = []
try:
    from .rag import KnowledgeRAG, get_rag
except Exception:
    KnowledgeRAG = None; get_rag = None
try:
    from .fine_tune import export_all_finetune_scripts, generate_golden_dataset
except Exception:
    export_all_finetune_scripts = None
    generate_golden_dataset = None
try:
    from .embeddings_store import EmbeddingStore
except Exception:
    EmbeddingStore = None
