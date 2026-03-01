from src.infrastructure.database.collection import get_documents_collection

def search_vectors(query: str, limit: int = 3):
    collection = get_documents_collection()

    results = collection.query(
        query_texts=[query],
        n_results=limit
    )

    matches = []
    for doc, meta, _id, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["ids"][0],
        results["distances"][0]
    ):
        matches.append({
            "id": _id,
            "text": doc,
            "source": meta["source"],
            "chunk": meta["chunk"],
            "distance": distance
        })

    return matches