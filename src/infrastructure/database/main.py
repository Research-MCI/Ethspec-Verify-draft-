# main.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))  # adds ethspec-verify/ to path

from src.infrastructure.database.services.ingest import ingest_folder
from src.infrastructure.database.services.query import query

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["ingest", "query"])
    parser.add_argument("--q", help="Query text")
    args = parser.parse_args()

    if args.action == "ingest":
        ingest_folder(Path("documents"))
    elif args.action == "query":
        query(args.q)