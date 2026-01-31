"""Unit tests for Layer 2: RAG-Enhanced Specification."""

from __future__ import annotations

import pytest

from src.core.entities.specification import (
    RequirementType,
    SpecCategory,
    SpecificationDocument,
    SpecificationMetadata,
)
from src.layers.layer2_rag.semantic_chunker import SemanticChunker


class TestSemanticChunker:
    """Tests for SemanticChunker."""

    @pytest.fixture
    def sample_document(self, sample_spec_metadata: SpecificationMetadata) -> SpecificationDocument:
        """Create a sample document for testing."""
        content = """
# Fork Specification

## Requirements

The fork criteria must be defined by a specific block number.
This block number shall be immutable once set.

The implementation should validate all blocks against the fork rules.

## Constraints

The maximum block size is limited to 1048576 bytes.
Blocks exceeding this limit must be rejected.

## Edge Cases

When the block number equals the fork criteria exactly,
the new rules should be applied.
"""
        return SpecificationDocument(
            doc_id="test-doc",
            title="Fork Specification",
            content=content,
            metadata=sample_spec_metadata,
            sections={
                "requirements": "The fork criteria must be defined...",
                "constraints": "The maximum block size...",
                "edge_cases": "When the block number equals...",
            },
        )

    def test_chunk_document(self, sample_document: SpecificationDocument) -> None:
        """Test document chunking."""
        chunker = SemanticChunker(chunk_size=200, chunk_overlap=20)
        chunks = chunker.chunk(sample_document)

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.chunk_id is not None
            assert chunk.content != ""
            assert chunk.metadata is not None

    def test_chunk_size_limit(self, sample_document: SpecificationDocument) -> None:
        """Test that chunks respect size limits."""
        chunk_size = 200
        chunker = SemanticChunker(chunk_size=chunk_size, chunk_overlap=0)
        chunks = chunker.chunk(sample_document)

        for chunk in chunks:
            # Allow some tolerance for semantic boundaries
            assert len(chunk.content) <= chunk_size * 2

    def test_requirement_type_detection(self) -> None:
        """Test requirement type detection."""
        chunker = SemanticChunker()

        # Test MUST keyword
        must_type = chunker._detect_requirement_type("The system must validate inputs")
        assert must_type == RequirementType.FUNCTIONAL

        # Test constraint keyword
        constraint_type = chunker._detect_requirement_type("Maximum value is 100")
        assert constraint_type == RequirementType.CONSTRAINT

        # Test invariant keyword
        invariant_type = chunker._detect_requirement_type("This value is always positive")
        assert invariant_type == RequirementType.INVARIANT

    def test_related_chunks_identified(self, sample_document: SpecificationDocument) -> None:
        """Test that related chunks are identified."""
        chunker = SemanticChunker(chunk_size=100)
        chunks = chunker.chunk(sample_document)

        # Chunks in the same section should be related
        section_chunks = [c for c in chunks if c.parent_section == "requirements"]
        if len(section_chunks) > 1:
            # First chunk should have related chunks
            assert len(section_chunks[0].related_chunks) > 0


class TestContextAssembler:
    """Tests for ContextAssembler."""

    def test_assemble_basic_context(self, sample_behavioral_model) -> None:
        """Test basic context assembly."""
        from src.core.interfaces.vector_store import SearchResult
        from src.layers.layer2_rag.context_assembler import ContextAssembler

        assembler = ContextAssembler(max_context_tokens=1000)

        search_results = [
            SearchResult(
                chunk_id="chunk-1",
                content="The fork criteria must be defined.",
                score=0.9,
                metadata={"fork_version": "cancun"},
            ),
            SearchResult(
                chunk_id="chunk-2",
                content="Validation must check block size.",
                score=0.8,
                metadata={"fork_version": "cancun"},
            ),
        ]

        context = assembler.assemble(search_results, sample_behavioral_model)

        assert context.specification_context != ""
        assert context.implementation_context != ""
        assert context.combined_context != ""
        assert context.token_estimate > 0
        assert len(context.sources) == 2

    def test_context_token_limit(self, sample_behavioral_model) -> None:
        """Test that context respects token limit."""
        from src.core.interfaces.vector_store import SearchResult
        from src.layers.layer2_rag.context_assembler import ContextAssembler

        assembler = ContextAssembler(max_context_tokens=100)  # Very low limit

        # Create many search results
        search_results = [
            SearchResult(
                chunk_id=f"chunk-{i}",
                content="X" * 200,  # Long content
                score=0.9 - i * 0.1,
                metadata={},
            )
            for i in range(10)
        ]

        context = assembler.assemble(search_results, sample_behavioral_model)

        # Should not include all results due to limit
        assert len(context.sources) < 10
