import os
import chromadb

def get_chroma_client():
    return chromadb.HttpClient(
    host="chroma",
    port=8000
)