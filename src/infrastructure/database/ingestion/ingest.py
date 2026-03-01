import hashlib
import json
from pathlib import Path
from ..client import get_chroma_client
from ..collection import get_documents_collection
import sys

HASH_STORE = Path("db/file_hashes.json")

# -------------------------
# Helpers
# -------------------------
def load_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

def get_file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()

# -------------------------
# Hash store
# -------------------------
def load_hash_store() -> dict:
    if HASH_STORE.exists():
        return json.loads(HASH_STORE.read_text())
    return {}

def save_hash_store(store: dict):
    HASH_STORE.parent.mkdir(parents=True, exist_ok=True)
    HASH_STORE.write_text(json.dumps(store, indent=2))

def has_file_changed(filename: str, current_hash: str, store: dict) -> bool:
    return store.get(filename) != current_hash

# -------------------------
# Ingestion
# -------------------------
collection = get_documents_collection()

def add_document_to_collection(path: Path):
    text = load_text_file(path)
    chunks = chunk_text(text)

    existing = collection.get(where={"source": path.name})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    documents, metadatas, ids = [], [], []
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        metadatas.append({"source": path.name, "chunk": i})
        ids.append(f"{path.stem}_{i}")

    collection.add(documents=documents, metadatas=metadatas, ids=ids)

# -------------------------
# Ingest only changed files
# -------------------------
def ingest_folder(folder_path: Path):
    store = load_hash_store()
    updated = False

    for file in folder_path.glob("*.txt"):
        current_hash = get_file_hash(file)

        if not has_file_changed(file.name, current_hash, store):
            print(f"[SKIP] {file.name} unchanged")
            continue

        add_document_to_collection(file)
        store[file.name] = current_hash
        updated = True
        print(f"[OK] Ingested {file.name}")

    if updated:
        save_hash_store(store)
        print("[DONE] Changes ingested and persisted.")
    else:
        print("[DONE] No changes detected.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        folder = Path(sys.argv[1])
    else:
        folder = Path("/app/documents")
    ingest_folder(folder)