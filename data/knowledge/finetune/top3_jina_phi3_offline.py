
# Top3: jina-v3 ultra-light offline - no LLM fine-tune, only prompt engineering
# jina-embeddings-v3 already ONNX ready: Xenova/jina-embeddings-v3

# Python offline inference (no HF API needed):
from transformers import AutoTokenizer, AutoModel
import torch, torch.nn.functional as F

tok = AutoTokenizer.from_pretrained("jinaai/jina-embeddings-v3", trust_remote_code=True)
model = AutoModel.from_pretrained("jinaai/jina-embeddings-v3", trust_remote_code=True).eval()

def embed(texts, task="retrieval.passage"):
    # jina uses task LoRA adapters
    inputs = tok(texts, padding=True, truncation=True, max_length=8192, return_tensors="pt")
    with torch.no_grad():
        # mean pooling
        out = model(**inputs)
        emb = out.last_hidden_state.mean(dim=1)
        emb = F.normalize(emb, p=2, dim=1)
    return emb

# For Iran laptop: use ONNX version
# from optimum.onnxruntime import ORTModelForFeatureExtraction
# model = ORTModelForFeatureExtraction.from_pretrained("Xenova/jina-embeddings-v3")

# Phi-3-mini GGUF for offline LLM
# Download: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf
# llama.cpp: ./llama-cli -m Phi-3-mini-4k-instruct-q4.gguf -p "تو یک مشاور شغلی هستی... رزومه: جوشکار... آگهی: kaynakçı..."
