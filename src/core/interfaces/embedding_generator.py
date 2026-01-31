"""Embedding generator interface for vector embeddings.

This module defines the abstract interface for generating vector embeddings
from text content for semantic search.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence


class EmbeddingGenerator(ABC):
    """Abstract interface for embedding generation implementations.

    Implementations should handle generating vector embeddings from text
    for storage in vector databases and semantic similarity search.
    """

    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Get the dimension of generated embeddings.

        Returns:
            The dimension of embedding vectors
        """
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the name of the embedding model.

        Returns:
            Model name string
        """
        ...

    @abstractmethod
    async def generate(self, text: str) -> tuple[float, ...]:
        """Generate embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            Tuple of floats representing the embedding vector
        """
        ...

    @abstractmethod
    async def generate_batch(
        self,
        texts: Sequence[str],
        batch_size: int = 100,
    ) -> list[tuple[float, ...]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: Sequence of texts to embed
            batch_size: Number of texts to process per batch

        Returns:
            List of embedding tuples
        """
        ...

    @abstractmethod
    async def similarity(
        self,
        embedding1: tuple[float, ...],
        embedding2: tuple[float, ...],
    ) -> float:
        """Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score between 0.0 and 1.0
        """
        ...
