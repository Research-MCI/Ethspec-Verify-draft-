"""Vector store interface for semantic search.

This module defines the abstract interface for vector database operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SearchResult:
    """Result from a vector similarity search.

    Attributes:
        chunk_id: ID of the matching chunk
        content: Text content of the chunk
        score: Similarity score (higher is more similar)
        metadata: Associated metadata
    """

    chunk_id: str
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStore(ABC):
    """Abstract interface for vector store implementations.

    Implementations should handle storage and retrieval of vector embeddings
    for semantic similarity search.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector store connection.

        This should create collections/indices if they don't exist.
        """
        ...

    @abstractmethod
    async def add(
        self,
        chunk_id: str,
        content: str,
        embedding: tuple[float, ...],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a single document to the store.

        Args:
            chunk_id: Unique identifier for the chunk
            content: Text content of the chunk
            embedding: Vector embedding
            metadata: Optional metadata to store
        """
        ...

    @abstractmethod
    async def add_batch(
        self,
        chunk_ids: list[str],
        contents: list[str],
        embeddings: list[tuple[float, ...]],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add multiple documents to the store.

        Args:
            chunk_ids: List of chunk identifiers
            contents: List of text contents
            embeddings: List of embeddings
            metadatas: Optional list of metadata dicts
        """
        ...

    @abstractmethod
    async def search(
        self,
        query_embedding: tuple[float, ...],
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents.

        Args:
            query_embedding: The query embedding vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of SearchResult sorted by similarity
        """
        ...

    @abstractmethod
    async def search_by_text(
        self,
        query_text: str,
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents by text.

        This method should handle embedding generation internally.

        Args:
            query_text: The query text
            top_k: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of SearchResult sorted by similarity
        """
        ...

    @abstractmethod
    async def get(self, chunk_id: str) -> SearchResult | None:
        """Get a specific document by ID.

        Args:
            chunk_id: The chunk identifier

        Returns:
            SearchResult if found, None otherwise
        """
        ...

    @abstractmethod
    async def delete(self, chunk_id: str) -> bool:
        """Delete a document by ID.

        Args:
            chunk_id: The chunk identifier

        Returns:
            True if deleted, False if not found
        """
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Clear all documents from the store."""
        ...

    @abstractmethod
    async def count(self) -> int:
        """Get the number of documents in the store.

        Returns:
            Number of documents
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the vector store connection."""
        ...
