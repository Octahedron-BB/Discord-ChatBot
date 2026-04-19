import json
import torch
import chromadb
from sentence_transformers import SentenceTransformer
import config

# 1. Check and enable Mac GPU (MPS)
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"🚀 Using device: {device}")

# 2. Initialize ChromaDB
client = chromadb.PersistentClient(path="./discord_memory_db")
try:
    client.delete_collection(name="chat_history")
except:
    pass
collection = client.create_collection(name="chat_history")

# 3. Load model (using config)
model_name = config.EMBEDDING_MODEL
print(f"⏳ Downloading and loading {model_name}...")
model = SentenceTransformer(model_name, device=device)

# 4. Read and slice (sliding window logic)
with open('cleaned_chat.json', 'r', encoding='utf-8') as f:
    sessions = json.load(f)

documents = []
metadatas = []
ids = []
doc_id = 0

WINDOW_SIZE = config.WINDOW_SIZE
STEP = config.STEP

print("🧠 Processing memory slices...")
for session in sessions:
    # E5 recommends adding "passage: " before content for retrieval
    for i in range(0, len(session) - WINDOW_SIZE + 1, STEP):
        window = session[i:i + WINDOW_SIZE]
        context_block = "\n".join([f"{m['role']}: {m['text']}" for m in window])

        documents.append(f"passage: {context_block}")
        metadatas.append({"session_start": window[0]['time']})
        ids.append(f"memory_block_{doc_id}")
        doc_id += 1

# 5. Batch write
embeddings = model.encode(documents, normalize_embeddings=True).tolist()
collection.add(embeddings=embeddings, documents=documents, metadatas=metadatas, ids=ids)

print(f"✅ Database update complete! Total {doc_id} memory blocks stored.")