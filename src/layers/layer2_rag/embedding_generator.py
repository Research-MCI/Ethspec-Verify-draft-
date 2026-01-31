"""Embedding generator implementation using Google Gemini.

This module provides vector embedding generation for semantic search.
"""

from __future__ import annotations

import asyncio
import math
from collections.abc import Sequence
from typing import TYPE_CHECKING

from src.core.interfaces.embedding_generator import EmbeddingGenerator
from src.shared.logger import LoggerMixin

if TYPE_CHECKING:
    pass


class GeminiEmbeddingGenerator(EmbeddingGenerator, LoggerMixin):
    """Google Gemini-based embedding generator.

    Uses Gemini's text-embedding model for generating vector embeddings.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "text-embedding-004",
        dimension: int = 768,
    ) -> None:
        """Initialize the Gemini embedding generator.

        Args:
            api_key: Gemini API key
            model_name: Embedding model name
            dimension: Embedding dimension
        """
        self._api_key = api_key
        self._model_name = model_name
        self._dimension = dimension
        self._client: object | None = None

    async def _ensure_client(self) -> None:
        """Ensure the Gemini client is initialized."""
        if self._client is None:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self._api_key)
                self._client = genai
            except ImportError:
                raise ImportError(
                    "google-generativeai package is required. "
                    "Install with: pip install google-generativeai"
                )

    @property
    def embedding_dimension(self) -> int:
        """Get the dimension of generated embeddings."""
        return self._dimension

    @property
    def model_name(self) -> str:
        """Get the name of the embedding model."""
        return self._model_name

    async def generate(self, text: str) -> tuple[float, ...]:
        """Generate embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            Tuple of floats representing the embedding vector
        """
        await self._ensure_client()

        try:
            result = self._client.embed_content(
                model=f"models/{self._model_name}",
                content=text,
                task_type="retrieval_document",
            )

            embedding = result["embedding"]
            return tuple(embedding)

        except Exception as e:
            self.logger.error("embedding_generation_failed", error=str(e), text_length=len(text))
            raise

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
        await self._ensure_client()

        embeddings: list[tuple[float, ...]] = []
        total = len(texts)

        self.logger.info(
            "generating_batch_embeddings",
            total_texts=total,
            batch_size=batch_size,
        )

        for i in range(0, total, batch_size):
            batch = texts[i : i + batch_size]

            try:
                # Process batch
                batch_embeddings = []
                for text in batch:
                    embedding = await self.generate(text)
                    batch_embeddings.append(embedding)
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.05)

                embeddings.extend(batch_embeddings)

                self.logger.debug(
                    "batch_processed",
                    batch_start=i,
                    batch_size=len(batch),
                    total_processed=len(embeddings),
                )

            except Exception as e:
                self.logger.error(
                    "batch_embedding_failed",
                    batch_start=i,
                    error=str(e),
                )
                # Fill with zero vectors for failed batch
                for _ in batch:
                    embeddings.append(tuple([0.0] * self._dimension))

        return embeddings

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
        # Calculate cosine similarity
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = math.sqrt(sum(a * a for a in embedding1))
        norm2 = math.sqrt(sum(b * b for b in embedding2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Normalize to 0-1 range (cosine similarity is -1 to 1)
        return (similarity + 1) / 2


class MockEmbeddingGenerator(EmbeddingGenerator):
    """Mock embedding generator for testing.

    Generates deterministic embeddings based on text hash.
    """

    def __init__(self, dimension: int = 768) -> None:
        """Initialize mock generator.

        Args:
            dimension: Embedding dimension
        """
        self._dimension = dimension

    @property
    def embedding_dimension(self) -> int:
        """Get the dimension of generated embeddings."""
        return self._dimension

    @property
    def model_name(self) -> str:
        """Get the name of the embedding model."""
        return "mock-embedding"

    async def generate(self, text: str) -> tuple[float, ...]:
        """Generate deterministic embedding for text.

        Args:
            text: The text to embed

        Returns:
            Deterministic embedding tuple
        """
        # Use hash to generate deterministic values
        text_hash = hash(text)
        embedding = []

        for i in range(self._dimension):
            # Generate pseudo-random but deterministic value
            value = ((text_hash + i * 31) % 10000) / 10000.0 - 0.5
            embedding.append(value)

        # Normalize
        norm = math.sqrt(sum(v * v for v in embedding))
        if norm > 0:
            embedding = [v / norm for v in embedding]

        return tuple(embedding)

    async def generate_batch(
        self,
        texts: Sequence[str],
        batch_size: int = 100,
    ) -> list[tuple[float, ...]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: Sequence of texts to embed
            batch_size: Ignored in mock

        Returns:
            List of embedding tuples
        """
        return [await self.generate(text) for text in texts]

    async def similarity(
        self,
        embedding1: tuple[float, ...],
        embedding2: tuple[float, ...],
    ) -> float:
        """Calculate cosine similarity.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Cosine similarity
        """
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = math.sqrt(sum(a * a for a in embedding1))
        norm2 = math.sqrt(sum(b * b for b in embedding2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return (dot_product / (norm1 * norm2) + 1) / 2
