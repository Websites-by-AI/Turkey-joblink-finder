"""Fine-tune scripts for top 3 JobLink models - ready to run on HF Spaces or local GPU"""

import json, os, random
from dataclasses import dataclass
from typing import List

# Mock dataset generator for fa->tr job matching
def generate_golden_dataset(n=500, out_path="data/knowledge/golden_fa_tr.jsonl"):
    """Generate synthetic golden dataset for fine-tuning embeddings"""
    # Use existing LEXICON + ESCO concepts
    skills_map = {
        "جوشکار": ["kaynakçı", "CO2 kaynak", "argon kaynak", "welding"],
        "راننده لیفتراک": ["forklift operatörü", "depo personeli", "forklift"],
        "نظافت": ["temizlik personeli", "temizlik görevlisi", "cleaning"],
        "نگهبان": ["güvenlik personeli", "bekçi", "security"],
        "برنامه‌نویس": ["yazılım geliştirici", "python developer", "software"],
        "حسابدار": ["muhasebe", "ön muhasebe", "accountant"],
        "فروشنده": ["satış danışmanı", "mağaza satış", "sales"],
        "انباردار": ["depo personeli", "depo elemanı", "warehouse"],
        "راننده": ["şoför", "sevkiyat şoförü", "driver"],
        "آشپز": ["aşçı", "mutfak personeli", "cook"],
    }
    
    cities = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya"]
    
    rows = []
    for i in range(n):
        fa_skill = random.choice(list(skills_map.keys()))
        tr_variants = skills_map[fa_skill]
        # positive pair
        fa_cv = f"{fa_skill} با {random.randint(1,10)} سال سابقه. ساکن تهران. آماده مهاجرت به ترکیه. زبان ترکی در حد آشنایی."
        tr_job_pos = f"{random.choice(tr_variants)} - {random.choice(cities)} - {random.randint(26005,50000)} TL maaş + SGK + yemek - deneyim {random.randint(1,5)} yıl"
        rows.append({"query": fa_cv, "passage_pos": tr_job_pos, "passage_neg": f"yazılım geliştirici - Python Django - {random.choice(cities)}", "label": fa_skill, "type": "positive" if fa_skill!="برنامه‌نویس" else "hard_negative_check"})
        
        # negative pair (polysemy trap: kaynak)
        if fa_skill == "جوشکار":
            rows.append({"query": fa_cv, "passage_pos": tr_job_pos, "passage_neg": "kaynak kodu - yazılım - GitHub - source code - İstanbul", "label": "kaynak_polysemy", "type": "polysemy_trap"})
    
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False)+"\n")
    return out_path, len(rows)

def get_finetune_code_top1():
    return '''
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
        query = f"Instruct: یک شغل مناسب برای این رزومه پیدا کن\\nQuery: {obj['query']}"
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
'''

def get_finetune_code_top2():
    return '''
# Top2: e5-large LoRA for kaynak polysemy
# pip install sentence-transformers peft

from sentence_transformers import SentenceTransformer
from peft import LoraConfig, get_peft_model

base = SentenceTransformer("intfloat/multilingual-e5-large")

# LoRA config for embeddings (lightweight)
config = LoraConfig(r=16, lora_alpha=32, target_modules=["query","value"], lora_dropout=0.1)
# Note: sentence-transformers + peft integration is experimental - alternatively fine-tune full model 1 epoch

# Dataset: focus on polysemy traps
# 200 pairs: (جوشکار -> kaynakçı positive) vs (جوشکار -> kaynak kodu negative)

# Training 1 epoch only to avoid overfitting
# See top1 code for DataLoader - same but 1 epoch, lr 1e-5

# After fine-tune, test:
# query "جوشکار CO2" should have cosine >0.7 with "CO2 kaynakçısı - İstanbul" and <0.3 with "kaynak kodu yazılım"
'''

def get_finetune_code_top3():
    return '''
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
'''

def export_all_finetune_scripts(out_dir="data/knowledge/finetune"):
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/top1_qwen3_06b_finetune.py","w",encoding="utf-8") as f:
        f.write(get_finetune_code_top1())
    with open(f"{out_dir}/top2_e5_lora.py","w",encoding="utf-8") as f:
        f.write(get_finetune_code_top2())
    with open(f"{out_dir}/top3_jina_phi3_offline.py","w",encoding="utf-8") as f:
        f.write(get_finetune_code_top3())
    # generate golden dataset
    path, n = generate_golden_dataset(n=500, out_path=f"{out_dir}/../golden_fa_tr.jsonl")
    return {"scripts": 3, "golden_dataset": path, "rows": n}

if __name__=="__main__":
    print(export_all_finetune_scripts())
