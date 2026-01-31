"""Vector database implementation using ChromaDB.

This module provides vector storage and retrieval functionality
for semantic search of specification chunks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.core.interfaces.vector_store import SearchResult, VectorStore
from src.shared.logger import LoggerMixin

if TYPE_CHECKING:
    from src.core.interfaces.embedding_generator import EmbeddingGenerator


class ChromaDBVectorStore(VectorStore, LoggerMixin):
    """ChromaDB-based vector store implementation.

    Provides persistent storage and semantic search for specification
    chunk embeddings.
    """

    def __init__(
        self,
        embedding_generator: EmbeddingGenerator,
        persist_directory: str = "./data/chromadb",
        collection_name: str = "eth_specifications",
    ) -> None:
        """Initialize the ChromaDB vector store.

        Args:
            embedding_generator: Embedding generator for search queries
            persist_directory: Directory for persistent storage
            collection_name: Name of the collection
        """
        self._embedding_generator = embedding_generator
        self._persist_directory = persist_directory
        self._collection_name = collection_name
        self._client: object | None = None
        self._collection: object | None = None

    async def initialize(self) -> None:
        """Initialize the ChromaDB client and collection."""
        try:
            import chromadb
            from chromadb.config import Settings

            self._client = chromadb.PersistentClient(
                path=self._persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )

            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )

            self.logger.info(
                "chromadb_initialized",
                collection=self._collection_name,
                persist_dir=self._persist_directory,
            )

        except ImportError:
            raise ImportError(
                "chromadb package is required. Install with: pip install chromadb"
            )

    async def add(
        self,
        chunk_id: str,
        content: str,
        embedding: tuple[float, ...],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a single document to the store.

        Args:
            chunk_id: Unique identifier
            content: Text content
            embedding: Vector embedding
            metadata: Optional metadata
        """
        if self._collection is None:
            await self.initialize()

        # Filter metadata to only include supported types
        filtered_metadata = self._filter_metadata(metadata) if metadata else {}

        self._collection.add(
            ids=[chunk_id],
            documents=[content],
            embeddings=[list(embedding)],
            metadatas=[filtered_metadata],
        )

    async def add_batch(
        self,
        chunk_ids: list[str],
        contents: list[str],
        embeddings: list[tuple[float, ...]],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add multiple documents to the store.

        Args:
            chunk_ids: List of identifiers
            contents: List of text contents
            embeddings: List of embeddings
            metadatas: Optional list of metadata dicts
        """
        if self._collection is None:
            await self.initialize()

        # Filter metadata
        if metadatas:
            filtered_metadatas = [self._filter_metadata(m) for m in metadatas]
        else:
            filtered_metadatas = [{}] * len(chunk_ids)

        # Convert embeddings to lists
        embedding_lists = [list(e) for e in embeddings]

        self._collection.add(
            ids=chunk_ids,
            documents=contents,
            embeddings=embedding_lists,
            metadatas=filtered_metadatas,
        )

        self.logger.info("batch_added", count=len(chunk_ids))

    async def search(
        self,
        query_embedding: tuple[float, ...],
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results
            filter_metadata: Optional metadata filter

        Returns:
            List of SearchResult
        """
        if self._collection is None:
            await self.initialize()

        # Build where clause from filter
        where = self._build_where_clause(filter_metadata) if filter_metadata else None

        results = self._collection.query(
            query_embeddings=[list(query_embedding)],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        return self._parse_results(results)

    async def search_by_text(
        self,
        query_text: str,
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search by text query.

        Args:
            query_text: Query text
            top_k: Number of results
            filter_metadata: Optional metadata filter

        Returns:
            List of SearchResult
        """
        # Generate embedding for query
        query_embedding = await self._embedding_generator.generate(query_text)
        return await self.search(query_embedding, top_k, filter_metadata)

    async def get(self, chunk_id: str) -> SearchResult | None:
        """Get a specific document by ID.

        Args:
            chunk_id: Document identifier

        Returns:
            SearchResult if found, None otherwise
        """
        if self._collection is None:
            await self.initialize()

        try:
            result = self._collection.get(
                ids=[chunk_id],
                include=["documents", "metadatas"],
            )

            if result["ids"]:
                return SearchResult(
                    chunk_id=result["ids"][0],
                    content=result["documents"][0] if result["documents"] else "",
                    score=1.0,
                    metadata=result["metadatas"][0] if result["metadatas"] else {},
                )

        except Exception:
            pass

        return None

    async def delete(self, chunk_id: str) -> bool:
        """Delete a document by ID.

        Args:
            chunk_id: Document identifier

        Returns:
            True if deleted
        """
        if self._collection is None:
            await self.initialize()

        try:
            self._collection.delete(ids=[chunk_id])
            return True
        except Exception:
            return False

    async def clear(self) -> None:
        """Clear all documents from the store."""
        if self._client is None:
            await self.initialize()

        self._client.delete_collection(self._collection_name)
        self._collection = self._client.create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        self.logger.info("collection_cleared", collection=self._collection_name)

    async def count(self) -> int:
        """Get document count.

        Returns:
            Number of documents
        """
        if self._collection is None:
            await self.initialize()

        return self._collection.count()

    async def close(self) -> None:
        """Close the connection."""
        self._collection = None
        self._client = None

    def _filter_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Filter metadata to only include ChromaDB-supported types.

        Args:
            metadata: Original metadata

        Returns:
            Filtered metadata
        """
        filtered: dict[str, Any] = {}

        for key, value in metadata.items():
            # ChromaDB supports: str, int, float, bool
            if isinstance(value, (str, int, float, bool)):
                filtered[key] = value
            elif value is None:
                continue
            else:
                # Convert to string
                filtered[key] = str(value)

        return filtered

    def _build_where_clause(
        self,
        filter_metadata: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Build ChromaDB where clause from metadata filter.

        Args:
            filter_metadata: Filter dictionary

        Returns:
            ChromaDB where clause
        """
        if not filter_metadata:
            return None

        # For single key-value, use direct equality
        if len(filter_metadata) == 1:
            key, value = next(iter(filter_metadata.items()))
            return {key: value}

        # For multiple filters, use $and
        conditions = [{k: v} for k, v in filter_metadata.items()]
        return {"$and": conditions}

    def _parse_results(self, results: dict[str, Any]) -> list[SearchResult]:
        """Parse ChromaDB results into SearchResult objects.

        Args:
            results: ChromaDB query results

        Returns:
            List of SearchResult
        """
        search_results: list[SearchResult] = []

        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, chunk_id in enumerate(ids):
            # Convert distance to similarity score (cosine distance to similarity)
            distance = distances[i] if i < len(distances) else 0
            score = 1 - distance  # Cosine distance to similarity

            search_results.append(
                SearchResult(
                    chunk_id=chunk_id,
                    content=documents[i] if i < len(documents) else "",
                    score=score,
                    metadata=metadatas[i] if i < len(metadatas) else {},
                )
            )

        return search_results
