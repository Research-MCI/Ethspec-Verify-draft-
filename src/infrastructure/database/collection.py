import chromadb
from src.infrastructure.database.client import get_chroma_client

COLLECTION_NAME = "documents"

def get_documents_collection(name: str = "documents") -> chromadb.Collection:
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )
    return collection