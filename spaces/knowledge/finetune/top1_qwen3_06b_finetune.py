
# Top1: Qwen3-Embedding-0.6B fine-tune for fa->tr blue-collar
# pip install sentence-transformers datasets optimum[onnxruntime]

from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
from datasets import load_dataset

model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")

# Load golden dataset
# data/knowledge/golden_fa_tr.jsonl: {"query": "...", "passage_pos": "...", "passage_neg": "..."}
train_examples = []
with open("data/knowledge/golden_fa_tr.jsonl", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        # Instruction format for Qwen3
        query = f"Instruct: یک شغل مناسب برای این رزومه پیدا کن\nQuery: {obj['query']}"
        pos = f"passage: {obj['passage_pos']}"
        neg = f"passage: {obj['passage_neg']}"
        train_examples.append(InputExample(texts=[query, pos, neg]))

loader = DataLoader(train_examples, batch_size=32, shuffle=True)
loss = losses.MultipleNegativesRankingLoss(model)

# 5 epoch, lr 2e-5
model.fit(train_objectives=[(loader, loss)], epochs=5, warmup_steps=100, optimizer_params={'lr': 2e-5}, output_path="models/joblink-qwen3-0.6b-fa-tr")

# Evaluate Recall@5 on 14 synthetic candidates
# python -m joblink.cli match --top 5 -> check if welder no longer matches software

# ONNX export for Iran VPS
# optimum-cli export onnx --model models/joblink-qwen3-0.6b-fa-tr --task feature-extraction models/qwen3-06b-onnx/
# Quantize int8 -> 300MB
from optimum.onnxruntime import ORTModelForFeatureExtraction
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("models/joblink-qwen3-0.6b-fa-tr")
ort_model = ORTModelForFeatureExtraction.from_pretrained("models/qwen3-06b-onnx/")
# Now CPU inference: tok + ort_model -> 1024 dim -> truncate 512 for D1
