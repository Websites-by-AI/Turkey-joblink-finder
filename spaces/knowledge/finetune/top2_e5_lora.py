
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
