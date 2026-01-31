"""Knowledge graph interface for specification relationships.

This module defines the abstract interface for knowledge graph operations
used to model relationships between specifications, requirements, and code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RelationType(str, Enum):
    """Types of relationships in the knowledge graph."""

    REQUIRES = "REQUIRES"
    IMPLIES = "IMPLIES"
    CONFLICTS_WITH = "CONFLICTS_WITH"
    DEPENDS_ON = "DEPENDS_ON"
    IMPLEMENTS = "IMPLEMENTS"
    SPECIFIES = "SPECIFIES"
    CONTAINS = "CONTAINS"
    REFERENCES = "REFERENCES"
    SUPERSEDES = "SUPERSEDES"
    RELATED_TO = "RELATED_TO"


class NodeType(str, Enum):
    """Types of nodes in the knowledge graph."""

    SPECIFICATION = "Specification"
    REQUIREMENT = "Requirement"
    CONSTRAINT = "Constraint"
    INVARIANT = "Invariant"
    EDGE_CASE = "EdgeCase"
    CODE_ELEMENT = "CodeElement"
    FUNCTION = "Function"
    STATE_VARIABLE = "StateVariable"
    FORK = "Fork"
    EIP = "EIP"


@dataclass(frozen=True)
class KnowledgeNode:
    """A node in the knowledge graph.

    Attributes:
        node_id: Unique node identifier
        node_type: Type of the node
        label: Human-readable label
        properties: Additional node properties
    """

    node_id: str
    node_type: NodeType
    label: str
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "label": self.label,
            "properties": self.properties,
        }


@dataclass(frozen=True)
class KnowledgeRelation:
    """A relationship between nodes in the knowledge graph.

    Attributes:
        relation_id: Unique relation identifier
        source_id: Source node ID
        target_id: Target node ID
        relation_type: Type of relationship
        properties: Additional relationship properties
    """

    relation_id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert relation to dictionary representation."""
        return {
            "relation_id": self.relation_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
            "properties": self.properties,
        }


class KnowledgeGraph(ABC):
    """Abstract interface for knowledge graph implementations.

    Implementations should handle storage and querying of specification
    relationships for requirement tracing and impact analysis.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the knowledge graph connection.

        This should create necessary indices and constraints.
        """
        ...

    @abstractmethod
    async def add_node(self, node: KnowledgeNode) -> None:
        """Add a node to the graph.

        Args:
            node: The node to add
        """
        ...

    @abstractmethod
    async def add_relation(self, relation: KnowledgeRelation) -> None:
        """Add a relationship to the graph.

        Args:
            relation: The relationship to add
        """
        ...

    @abstractmethod
    async def get_node(self, node_id: str) -> KnowledgeNode | None:
        """Get a node by ID.

        Args:
            node_id: The node identifier

        Returns:
            KnowledgeNode if found, None otherwise
        """
        ...

    @abstractmethod
    async def get_related_nodes(
        self,
        node_id: str,
        relation_type: RelationType | None = None,
        direction: str = "both",
    ) -> list[tuple[KnowledgeNode, KnowledgeRelation]]:
        """Get nodes related to a given node.

        Args:
            node_id: The source node ID
            relation_type: Optional filter by relation type
            direction: 'outgoing', 'incoming', or 'both'

        Returns:
            List of (node, relation) tuples
        """
        ...

    @abstractmethod
    async def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
    ) -> list[tuple[KnowledgeNode, KnowledgeRelation | None]]:
        """Find a path between two nodes.

        Args:
            source_id: Starting node ID
            target_id: Target node ID
            max_depth: Maximum path length

        Returns:
            List of (node, relation) tuples representing the path
        """
        ...

    @abstractmethod
    async def query_by_type(
        self,
        node_type: NodeType,
        properties: dict[str, Any] | None = None,
    ) -> list[KnowledgeNode]:
        """Query nodes by type and optional properties.

        Args:
            node_type: Type of nodes to find
            properties: Optional property filters

        Returns:
            List of matching nodes
        """
        ...

    @abstractmethod
    async def get_implementation_trace(
        self,
        requirement_id: str,
    ) -> list[KnowledgeNode]:
        """Get code elements implementing a requirement.

        Args:
            requirement_id: The requirement node ID

        Returns:
            List of code element nodes
        """
        ...

    @abstractmethod
    async def get_impact_analysis(
        self,
        node_id: str,
    ) -> dict[str, list[KnowledgeNode]]:
        """Analyze impact of changes to a node.

        Args:
            node_id: The node being changed

        Returns:
            Dictionary mapping impact types to affected nodes
        """
        ...

    @abstractmethod
    async def delete_node(self, node_id: str) -> bool:
        """Delete a node and its relationships.

        Args:
            node_id: The node identifier

        Returns:
            True if deleted, False if not found
        """
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Clear all nodes and relationships from the graph."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the graph connection."""
        ...
