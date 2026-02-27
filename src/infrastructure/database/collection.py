import chromadb
from infrastructure.database.client import get_chroma_client

COLLECTION_NAME = "documents"

def get_documents_collection() -> chromadb.Collection:
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}  # cosine similarity for text
    )
    return collection