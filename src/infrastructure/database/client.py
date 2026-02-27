import chromadb
from chromadb.config import Settings

_client = None

def get_chroma_client() -> chromadb.Client:
    global _client
    if _client is None:
        _client = chromadb.Client(
            Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory="db",
                anonymized_telemetry=False
            )
        )
    return _client