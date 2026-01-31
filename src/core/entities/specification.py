"""Specification entity representing Ethereum protocol specifications.

This module defines data structures for representing specification documents,
their chunks, and normalized requirement formats.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SpecCategory(str, Enum):
    """Categories of Ethereum specifications."""

    EXECUTION = "execution"
    CONSENSUS = "consensus"
    EIP = "eip"
    FORK = "fork"
    STATE = "state"
    TRANSACTION = "transaction"
    BLOCK = "block"
    VM = "vm"
    PRECOMPILE = "precompile"
    NETWORKING = "networking"
    OTHER = "other"


class RequirementType(str, Enum):
    """Types of requirements in specifications."""

    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    CONSTRAINT = "constraint"
    INVARIANT = "invariant"
    EDGE_CASE = "edge_case"
    PRECONDITION = "precondition"
    POSTCONDITION = "postcondition"


@dataclass(frozen=True)
class SpecificationMetadata:
    """Metadata for a specification document.

    Attributes:
        source_repo: Source repository (e.g., 'ethereum/execution-specs')
        fork_version: Fork version (e.g., 'cancun', 'prague')
        category: Specification category
        file_path: Path to the specification file
        commit_hash: Git commit hash of the specification
        last_updated: Last modification timestamp
        eip_number: Associated EIP number if applicable
    """

    source_repo: str
    fork_version: str
    category: SpecCategory
    file_path: str
    commit_hash: str | None = None
    last_updated: datetime | None = None
    eip_number: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary representation."""
        return {
            "source_repo": self.source_repo,
            "fork_version": self.fork_version,
            "category": self.category.value,
            "file_path": self.file_path,
            "commit_hash": self.commit_hash,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "eip_number": self.eip_number,
        }


@dataclass(frozen=True)
class SpecificationChunk:
    """A semantic chunk of specification text.

    Attributes:
        chunk_id: Unique identifier for the chunk
        content: The text content of the chunk
        metadata: Associated metadata
        requirement_type: Type of requirement this chunk represents
        embedding: Vector embedding (populated after embedding generation)
        parent_section: Parent section title
        related_chunks: IDs of related chunks
    """

    chunk_id: str
    content: str
    metadata: SpecificationMetadata
    requirement_type: RequirementType = RequirementType.FUNCTIONAL
    embedding: tuple[float, ...] | None = None
    parent_section: str | None = None
    related_chunks: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Convert chunk to dictionary representation."""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
            "requirement_type": self.requirement_type.value,
            "has_embedding": self.embedding is not None,
            "parent_section": self.parent_section,
            "related_chunks": list(self.related_chunks),
        }


@dataclass(frozen=True)
class SpecificationDocument:
    """Represents a complete specification document.

    Attributes:
        doc_id: Unique document identifier
        title: Document title
        content: Full document content
        metadata: Document metadata
        chunks: Semantic chunks extracted from the document
        sections: Section hierarchy
    """

    doc_id: str
    title: str
    content: str
    metadata: SpecificationMetadata
    chunks: tuple[SpecificationChunk, ...] = field(default_factory=tuple)
    sections: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert document to dictionary representation."""
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "metadata": self.metadata.to_dict(),
            "chunk_count": len(self.chunks),
            "sections": list(self.sections.keys()),
        }


@dataclass(frozen=True)
class Requirement:
    """A normalized requirement extracted from specifications.

    Attributes:
        req_id: Requirement identifier (e.g., 'REQ-001')
        description: Human-readable requirement description
        source_chunk: Source chunk ID
        category: Requirement category
        priority: Priority level (1-5, with 1 being highest)
        related_requirements: IDs of related requirements
    """

    req_id: str
    description: str
    source_chunk: str
    category: SpecCategory = SpecCategory.OTHER
    priority: int = 3
    related_requirements: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Convert requirement to dictionary representation."""
        return {
            "req_id": self.req_id,
            "description": self.description,
            "source_chunk": self.source_chunk,
            "category": self.category.value,
            "priority": self.priority,
            "related_requirements": list(self.related_requirements),
        }


@dataclass(frozen=True)
class Constraint:
    """A constraint extracted from specifications.

    Attributes:
        constraint_id: Constraint identifier (e.g., 'CON-001')
        description: Human-readable constraint description
        source_chunk: Source chunk ID
        constraint_type: Type of constraint
        is_hard: Whether this is a hard (must) or soft (should) constraint
    """

    constraint_id: str
    description: str
    source_chunk: str
    constraint_type: str = "general"
    is_hard: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert constraint to dictionary representation."""
        return {
            "constraint_id": self.constraint_id,
            "description": self.description,
            "source_chunk": self.source_chunk,
            "constraint_type": self.constraint_type,
            "is_hard": self.is_hard,
        }


@dataclass(frozen=True)
class Invariant:
    """An invariant extracted from specifications.

    Attributes:
        invariant_id: Invariant identifier (e.g., 'INV-001')
        description: Human-readable invariant description
        source_chunk: Source chunk ID
        scope: Scope of the invariant (e.g., 'state', 'transaction')
    """

    invariant_id: str
    description: str
    source_chunk: str
    scope: str = "global"

    def to_dict(self) -> dict[str, Any]:
        """Convert invariant to dictionary representation."""
        return {
            "invariant_id": self.invariant_id,
            "description": self.description,
            "source_chunk": self.source_chunk,
            "scope": self.scope,
        }


@dataclass(frozen=True)
class EdgeCase:
    """An edge case extracted from specifications.

    Attributes:
        edge_case_id: Edge case identifier (e.g., 'EDGE-001')
        description: Human-readable edge case description
        source_chunk: Source chunk ID
        trigger_condition: Condition that triggers this edge case
        expected_behavior: Expected behavior when triggered
    """

    edge_case_id: str
    description: str
    source_chunk: str
    trigger_condition: str = ""
    expected_behavior: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert edge case to dictionary representation."""
        return {
            "edge_case_id": self.edge_case_id,
            "description": self.description,
            "source_chunk": self.source_chunk,
            "trigger_condition": self.trigger_condition,
            "expected_behavior": self.expected_behavior,
        }


@dataclass(frozen=True)
class TraceabilityHint:
    """A hint for tracing between spec and implementation.

    Attributes:
        hint_id: Hint identifier
        spec_reference: Reference in specification
        implementation_hint: Hint for finding implementation
        keywords: Keywords to search for
    """

    hint_id: str
    spec_reference: str
    implementation_hint: str
    keywords: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Convert traceability hint to dictionary representation."""
        return {
            "hint_id": self.hint_id,
            "spec_reference": self.spec_reference,
            "implementation_hint": self.implementation_hint,
            "keywords": list(self.keywords),
        }


@dataclass(frozen=True)
class NormalizedSpecification:
    """The normalized specification output from Layer 2.

    This contains all extracted and structured information from the
    specification documents, ready for verification in Layer 3.

    Attributes:
        spec_id: Unique specification identifier
        fork_version: Fork version
        requirements: Extracted requirements
        constraints: Extracted constraints
        invariants: Extracted invariants
        edge_cases: Extracted edge cases
        traceability_hints: Traceability hints
        implementation_implications: Implementation notes
        source_documents: Source document IDs
    """

    spec_id: str
    fork_version: str
    requirements: tuple[Requirement, ...]
    constraints: tuple[Constraint, ...]
    invariants: tuple[Invariant, ...]
    edge_cases: tuple[EdgeCase, ...] = field(default_factory=tuple)
    traceability_hints: tuple[TraceabilityHint, ...] = field(default_factory=tuple)
    implementation_implications: tuple[str, ...] = field(default_factory=tuple)
    source_documents: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Convert normalized specification to dictionary representation."""
        return {
            "spec_id": self.spec_id,
            "fork_version": self.fork_version,
            "requirements": [r.to_dict() for r in self.requirements],
            "constraints": [c.to_dict() for c in self.constraints],
            "invariants": [i.to_dict() for i in self.invariants],
            "edge_cases": [e.to_dict() for e in self.edge_cases],
            "traceability_hints": [t.to_dict() for t in self.traceability_hints],
            "implementation_implications": list(self.implementation_implications),
            "source_documents": list(self.source_documents),
        }

    @property
    def total_items(self) -> int:
        """Get total number of specification items."""
        return (
            len(self.requirements)
            + len(self.constraints)
            + len(self.invariants)
            + len(self.edge_cases)
        )
