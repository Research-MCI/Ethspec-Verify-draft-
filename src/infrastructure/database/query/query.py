import json
from pathlib import Path
from src.infrastructure.database.search import search_vectors

def query(text: str, limit: int = 3) -> dict:
    matches = search_vectors(query=text, limit=limit)
    return {
        "query": text,
        "results": matches
    }

if __name__ == "__main__":
    q = input("Enter query: What is BRICS? ")
    output = query(q)

    filename = q[:30].strip().replace(" ", "_") + ".json"
    output_path = Path("results") / filename
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2))
    print(f"[DONE] Results saved to {output_path}")
