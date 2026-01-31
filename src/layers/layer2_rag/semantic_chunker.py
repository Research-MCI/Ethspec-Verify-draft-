"""Semantic chunking for specification documents.

This module implements semantic chunking that preserves meaningful
boundaries in specification text.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from uuid import uuid4

from src.core.entities.specification import (
    RequirementType,
    SpecificationChunk,
)
from src.shared.constants import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    MAX_CHUNK_SIZE,
    MIN_CHUNK_SIZE,
)

if TYPE_CHECKING:
    from src.core.entities.specification import SpecificationDocument


class SemanticChunker:
    """Chunks specification documents into semantically meaningful segments.

    Uses a combination of:
    - Section boundaries
    - Paragraph breaks
    - Requirement keyword detection
    - Size constraints
    """

    # Keywords that indicate requirement boundaries
    REQUIREMENT_KEYWORDS = {
        "must",
        "shall",
        "should",
        "will",
        "required",
        "mandatory",
    }

    # Keywords that indicate constraints
    CONSTRAINT_KEYWORDS = {
        "maximum",
        "minimum",
        "limit",
        "bound",
        "range",
        "at most",
        "at least",
        "no more than",
        "no less than",
    }

    # Keywords that indicate invariants
    INVARIANT_KEYWORDS = {
        "always",
        "never",
        "invariant",
        "constant",
        "immutable",
        "unchanging",
    }

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        """Initialize the semantic chunker.

        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = max(MIN_CHUNK_SIZE, min(MAX_CHUNK_SIZE, chunk_size))
        self.chunk_overlap = chunk_overlap

    def chunk(self, document: SpecificationDocument) -> list[SpecificationChunk]:
        """Chunk a specification document.

        Args:
            document: The document to chunk

        Returns:
            List of specification chunks
        """
        chunks: list[SpecificationChunk] = []

        # Process each section
        for section_name, section_content in document.sections.items():
            section_chunks = self._chunk_section(
                content=section_content,
                section_name=section_name,
                document=document,
            )
            chunks.extend(section_chunks)

        # If no sections, chunk the full content
        if not document.sections:
            chunks = self._chunk_section(
                content=document.content,
                section_name="main",
                document=document,
            )

        # Identify related chunks
        chunks = self._identify_related_chunks(chunks)

        return chunks

    def _chunk_section(
        self,
        content: str,
        section_name: str,
        document: SpecificationDocument,
    ) -> list[SpecificationChunk]:
        """Chunk a single section.

        Args:
            content: Section content
            section_name: Name of the section
            document: Parent document

        Returns:
            List of chunks from this section
        """
        chunks: list[SpecificationChunk] = []

        # Split by paragraphs first
        paragraphs = self._split_into_paragraphs(content)

        current_chunk_text: list[str] = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)

            # If single paragraph exceeds chunk size, split it
            if para_size > self.chunk_size:
                # Save current chunk first
                if current_chunk_text:
                    chunk = self._create_chunk(
                        content="\n\n".join(current_chunk_text),
                        section_name=section_name,
                        document=document,
                    )
                    chunks.append(chunk)
                    current_chunk_text = []
                    current_size = 0

                # Split large paragraph
                sub_chunks = self._split_large_paragraph(para, section_name, document)
                chunks.extend(sub_chunks)

            # If adding this paragraph would exceed size, start new chunk
            elif current_size + para_size > self.chunk_size and current_chunk_text:
                chunk = self._create_chunk(
                    content="\n\n".join(current_chunk_text),
                    section_name=section_name,
                    document=document,
                )
                chunks.append(chunk)

                # Start new chunk with overlap
                if self.chunk_overlap > 0 and current_chunk_text:
                    # Keep last part of previous chunk for overlap
                    overlap_text = current_chunk_text[-1]
                    if len(overlap_text) > self.chunk_overlap:
                        overlap_text = overlap_text[-self.chunk_overlap :]
                    current_chunk_text = [overlap_text, para]
                    current_size = len(overlap_text) + para_size
                else:
                    current_chunk_text = [para]
                    current_size = para_size
            else:
                current_chunk_text.append(para)
                current_size += para_size

        # Don't forget the last chunk
        if current_chunk_text:
            chunk = self._create_chunk(
                content="\n\n".join(current_chunk_text),
                section_name=section_name,
                document=document,
            )
            chunks.append(chunk)

        return chunks

    def _split_into_paragraphs(self, content: str) -> list[str]:
        """Split content into paragraphs.

        Args:
            content: Text content

        Returns:
            List of paragraphs
        """
        # Split on double newlines or bullet points
        paragraphs = re.split(r"\n\s*\n|\n(?=[-*•]\s)", content)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_large_paragraph(
        self,
        paragraph: str,
        section_name: str,
        document: SpecificationDocument,
    ) -> list[SpecificationChunk]:
        """Split a large paragraph into smaller chunks.

        Args:
            paragraph: Large paragraph text
            section_name: Section name
            document: Parent document

        Returns:
            List of chunks
        """
        chunks: list[SpecificationChunk] = []

        # Split by sentences
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)

        current_text: list[str] = []
        current_size = 0

        for sentence in sentences:
            if current_size + len(sentence) > self.chunk_size and current_text:
                chunk = self._create_chunk(
                    content=" ".join(current_text),
                    section_name=section_name,
                    document=document,
                )
                chunks.append(chunk)
                current_text = []
                current_size = 0

            current_text.append(sentence)
            current_size += len(sentence)

        if current_text:
            chunk = self._create_chunk(
                content=" ".join(current_text),
                section_name=section_name,
                document=document,
            )
            chunks.append(chunk)

        return chunks

    def _create_chunk(
        self,
        content: str,
        section_name: str,
        document: SpecificationDocument,
    ) -> SpecificationChunk:
        """Create a specification chunk.

        Args:
            content: Chunk content
            section_name: Section name
            document: Parent document

        Returns:
            SpecificationChunk
        """
        # Detect requirement type from content
        requirement_type = self._detect_requirement_type(content)

        return SpecificationChunk(
            chunk_id=f"chunk-{uuid4().hex[:8]}",
            content=content,
            metadata=document.metadata,
            requirement_type=requirement_type,
            parent_section=section_name,
        )

    def _detect_requirement_type(self, content: str) -> RequirementType:
        """Detect the requirement type from content.

        Args:
            content: Chunk content

        Returns:
            Detected RequirementType
        """
        content_lower = content.lower()

        # Check for invariants first (most specific)
        if any(kw in content_lower for kw in self.INVARIANT_KEYWORDS):
            return RequirementType.INVARIANT

        # Check for constraints
        if any(kw in content_lower for kw in self.CONSTRAINT_KEYWORDS):
            return RequirementType.CONSTRAINT

        # Check for requirements
        if any(kw in content_lower for kw in self.REQUIREMENT_KEYWORDS):
            return RequirementType.FUNCTIONAL

        # Check for edge cases
        if any(kw in content_lower for kw in ("edge case", "corner case", "exception", "error")):
            return RequirementType.EDGE_CASE

        # Check for preconditions/postconditions
        if "before" in content_lower or "prior" in content_lower:
            return RequirementType.PRECONDITION
        if "after" in content_lower or "result" in content_lower:
            return RequirementType.POSTCONDITION

        return RequirementType.FUNCTIONAL

    def _identify_related_chunks(
        self,
        chunks: list[SpecificationChunk],
    ) -> list[SpecificationChunk]:
        """Identify and link related chunks.

        Args:
            chunks: List of chunks

        Returns:
            Updated list with related_chunks populated
        """
        # Simple approach: chunks in the same section are related
        section_chunks: dict[str, list[str]] = {}

        for chunk in chunks:
            section = chunk.parent_section or "main"
            if section not in section_chunks:
                section_chunks[section] = []
            section_chunks[section].append(chunk.chunk_id)

        # Create new chunks with related IDs
        updated_chunks: list[SpecificationChunk] = []

        for chunk in chunks:
            section = chunk.parent_section or "main"
            related = [
                cid
                for cid in section_chunks.get(section, [])
                if cid != chunk.chunk_id
            ]

            updated_chunk = SpecificationChunk(
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                metadata=chunk.metadata,
                requirement_type=chunk.requirement_type,
                embedding=chunk.embedding,
                parent_section=chunk.parent_section,
                related_chunks=tuple(related[:5]),  # Limit to 5 related
            )
            updated_chunks.append(updated_chunk)

        return updated_chunks
