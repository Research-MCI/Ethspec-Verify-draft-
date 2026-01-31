"""RAG retriever for specification context.

This module provides retrieval of relevant specification context
for verification queries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.shared.logger import LoggerMixin

if TYPE_CHECKING:
    from src.core.interfaces.vector_store import SearchResult, VectorStore


class RAGRetriever(LoggerMixin):
    """Retrieves relevant specification context using RAG.

    Combines vector similarity search with metadata filtering
    to find the most relevant specification excerpts.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        default_top_k: int = 10,
    ) -> None:
        """Initialize the RAG retriever.

        Args:
            vector_store: Vector store for similarity search
            default_top_k: Default number of results to return
        """
        self._vector_store = vector_store
        self._default_top_k = default_top_k

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Retrieve relevant specification context.

        Args:
            query: Search query
            top_k: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of SearchResult
        """
        k = top_k or self._default_top_k

        self.logger.info(
            "retrieving_context",
            query_preview=query[:100],
            top_k=k,
            has_filter=filter_metadata is not None,
        )

        results = await self._vector_store.search_by_text(
            query_text=query,
            top_k=k,
            filter_metadata=filter_metadata,
        )

        self.logger.info(
            "retrieval_complete",
            result_count=len(results),
            top_score=results[0].score if results else 0,
        )

        return results

    async def retrieve_for_requirement(
        self,
        requirement_text: str,
        fork_version: str | None = None,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Retrieve context specific to a requirement.

        Args:
            requirement_text: The requirement text
            fork_version: Optional fork version filter
            top_k: Number of results

        Returns:
            List of SearchResult
        """
        filter_metadata = None
        if fork_version:
            filter_metadata = {"fork_version": fork_version}

        return await self.retrieve(
            query=requirement_text,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )

    async def retrieve_multi_query(
        self,
        queries: list[str],
        top_k_per_query: int = 3,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Retrieve using multiple queries and merge results.

        Args:
            queries: List of queries
            top_k_per_query: Results per query
            filter_metadata: Optional metadata filter

        Returns:
            Merged and deduplicated results
        """
        all_results: dict[str, SearchResult] = {}

        for query in queries:
            results = await self.retrieve(
                query=query,
                top_k=top_k_per_query,
                filter_metadata=filter_metadata,
            )

            for result in results:
                # Keep the highest scoring result for each chunk
                if result.chunk_id not in all_results:
                    all_results[result.chunk_id] = result
                elif result.score > all_results[result.chunk_id].score:
                    all_results[result.chunk_id] = result

        # Sort by score
        sorted_results = sorted(
            all_results.values(),
            key=lambda r: r.score,
            reverse=True,
        )

        return sorted_results

    async def retrieve_by_keywords(
        self,
        keywords: list[str],
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Retrieve using keywords as query.

        Args:
            keywords: List of keywords
            top_k: Number of results
            filter_metadata: Optional metadata filter

        Returns:
            List of SearchResult
        """
        query = " ".join(keywords)
        return await self.retrieve(
            query=query,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )

    def rerank_results(
        self,
        results: list[SearchResult],
        boost_keywords: list[str] | None = None,
    ) -> list[SearchResult]:
        """Rerank results with optional keyword boosting.

        Args:
            results: Original results
            boost_keywords: Keywords to boost

        Returns:
            Reranked results
        """
        if not boost_keywords:
            return results

        # Create new results with adjusted scores
        reranked: list[tuple[float, SearchResult]] = []

        for result in results:
            boost = 0.0
            content_lower = result.content.lower()

            for keyword in boost_keywords:
                if keyword.lower() in content_lower:
                    boost += 0.1

            adjusted_score = min(1.0, result.score + boost)
            reranked.append((adjusted_score, result))

        # Sort by adjusted score
        reranked.sort(key=lambda x: x[0], reverse=True)

        # Create new SearchResult objects with adjusted scores
        return [
            SearchResult(
                chunk_id=r.chunk_id,
                content=r.content,
                score=score,
                metadata=r.metadata,
            )
            for score, r in reranked
        ]
