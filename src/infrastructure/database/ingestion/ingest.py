import hashlib
import json
from pathlib import Path
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

def load_json_file(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    # Convert to readable text — adjust based on your JSON shape
    return json.dumps(data, indent=2)

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

def add_document_to_collection(path: Path, collection):
    if path.suffix == ".json":
        text = load_json_file(path)
    else:
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

    for subfolder in folder_path.iterdir():
        if not subfolder.is_dir():
            continue

        collection = get_documents_collection(name=subfolder.name)  # e.g. "invoices", "reports"
        print(f"[COLLECTION] Using collection: {subfolder.name}")

        for file in subfolder.glob("*"):
            if file.suffix not in {".txt", ".json"}:
                continue

            current_hash = get_file_hash(file)
            store_key = f"{subfolder.name}/{file.name}"  # namespaced key

            if not has_file_changed(store_key, current_hash, store):
                print(f"  [SKIP] {file.name} unchanged")
                continue

            add_document_to_collection(file, collection)
            store[store_key] = current_hash
            updated = True
            print(f"  [OK] Ingested {file.name}")

        # After the loop in ingest_folder()
        for stored_file in list(store.keys()):
            if not (folder_path / stored_file).exists():
                existing = collection.get(where={"source": stored_file})
                if existing["ids"]:
                    collection.delete(ids=existing["ids"])
                del store[stored_file]
                print(f"[DELETED] {stored_file} removed from collection")

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