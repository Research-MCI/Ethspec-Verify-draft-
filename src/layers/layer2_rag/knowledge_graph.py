"""In-memory knowledge graph implementation.

This module provides an in-memory knowledge graph for modeling
relationships between specifications, requirements, and code.
"""

from __future__ import annotations

from typing import Any

from src.core.interfaces.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeNode,
    KnowledgeRelation,
    NodeType,
    RelationType,
)
from src.shared.logger import LoggerMixin


class InMemoryKnowledgeGraph(KnowledgeGraph, LoggerMixin):
    """In-memory knowledge graph implementation.

    Provides a simple graph structure for development and testing.
    For production, use Neo4jKnowledgeGraph.
    """

    def __init__(self) -> None:
        """Initialize the in-memory knowledge graph."""
        self._nodes: dict[str, KnowledgeNode] = {}
        self._relations: dict[str, KnowledgeRelation] = {}
        self._outgoing: dict[str, list[str]] = {}  # node_id -> relation_ids
        self._incoming: dict[str, list[str]] = {}  # node_id -> relation_ids

    async def initialize(self) -> None:
        """Initialize the graph (no-op for in-memory)."""
        self.logger.info("in_memory_graph_initialized")

    async def add_node(self, node: KnowledgeNode) -> None:
        """Add a node to the graph.

        Args:
            node: The node to add
        """
        self._nodes[node.node_id] = node

        if node.node_id not in self._outgoing:
            self._outgoing[node.node_id] = []
        if node.node_id not in self._incoming:
            self._incoming[node.node_id] = []

    async def add_relation(self, relation: KnowledgeRelation) -> None:
        """Add a relationship to the graph.

        Args:
            relation: The relationship to add
        """
        self._relations[relation.relation_id] = relation

        # Update adjacency lists
        if relation.source_id not in self._outgoing:
            self._outgoing[relation.source_id] = []
        self._outgoing[relation.source_id].append(relation.relation_id)

        if relation.target_id not in self._incoming:
            self._incoming[relation.target_id] = []
        self._incoming[relation.target_id].append(relation.relation_id)

    async def get_node(self, node_id: str) -> KnowledgeNode | None:
        """Get a node by ID.

        Args:
            node_id: Node identifier

        Returns:
            KnowledgeNode if found
        """
        return self._nodes.get(node_id)

    async def get_related_nodes(
        self,
        node_id: str,
        relation_type: RelationType | None = None,
        direction: str = "both",
    ) -> list[tuple[KnowledgeNode, KnowledgeRelation]]:
        """Get nodes related to a given node.

        Args:
            node_id: Source node ID
            relation_type: Optional filter by relation type
            direction: 'outgoing', 'incoming', or 'both'

        Returns:
            List of (node, relation) tuples
        """
        results: list[tuple[KnowledgeNode, KnowledgeRelation]] = []

        # Get outgoing relations
        if direction in ("outgoing", "both"):
            for rel_id in self._outgoing.get(node_id, []):
                relation = self._relations.get(rel_id)
                if relation and (relation_type is None or relation.relation_type == relation_type):
                    target_node = self._nodes.get(relation.target_id)
                    if target_node:
                        results.append((target_node, relation))

        # Get incoming relations
        if direction in ("incoming", "both"):
            for rel_id in self._incoming.get(node_id, []):
                relation = self._relations.get(rel_id)
                if relation and (relation_type is None or relation.relation_type == relation_type):
                    source_node = self._nodes.get(relation.source_id)
                    if source_node:
                        results.append((source_node, relation))

        return results

    async def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
    ) -> list[tuple[KnowledgeNode, KnowledgeRelation | None]]:
        """Find a path between two nodes using BFS.

        Args:
            source_id: Starting node ID
            target_id: Target node ID
            max_depth: Maximum path length

        Returns:
            List of (node, relation) tuples representing the path
        """
        if source_id not in self._nodes or target_id not in self._nodes:
            return []

        # BFS
        from collections import deque

        queue: deque[tuple[str, list[tuple[str, str | None]]]] = deque()
        queue.append((source_id, [(source_id, None)]))
        visited = {source_id}

        while queue:
            current_id, path = queue.popleft()

            if len(path) > max_depth:
                continue

            if current_id == target_id:
                # Convert path to (node, relation) tuples
                result: list[tuple[KnowledgeNode, KnowledgeRelation | None]] = []
                for node_id, rel_id in path:
                    node = self._nodes.get(node_id)
                    relation = self._relations.get(rel_id) if rel_id else None
                    if node:
                        result.append((node, relation))
                return result

            # Explore neighbors
            for rel_id in self._outgoing.get(current_id, []):
                relation = self._relations.get(rel_id)
                if relation and relation.target_id not in visited:
                    visited.add(relation.target_id)
                    new_path = path + [(relation.target_id, rel_id)]
                    queue.append((relation.target_id, new_path))

        return []

    async def query_by_type(
        self,
        node_type: NodeType,
        properties: dict[str, Any] | None = None,
    ) -> list[KnowledgeNode]:
        """Query nodes by type and properties.

        Args:
            node_type: Type of nodes to find
            properties: Optional property filters

        Returns:
            List of matching nodes
        """
        results: list[KnowledgeNode] = []

        for node in self._nodes.values():
            if node.node_type != node_type:
                continue

            if properties:
                # Check if all properties match
                match = all(
                    node.properties.get(k) == v for k, v in properties.items()
                )
                if not match:
                    continue

            results.append(node)

        return results

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
        results: list[KnowledgeNode] = []

        # Find nodes connected by IMPLEMENTS relation
        for rel in self._relations.values():
            if (
                rel.source_id == requirement_id
                and rel.relation_type == RelationType.IMPLEMENTS
            ):
                node = self._nodes.get(rel.target_id)
                if node and node.node_type == NodeType.CODE_ELEMENT:
                    results.append(node)

        return results

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
        impact: dict[str, list[KnowledgeNode]] = {
            "direct": [],
            "indirect": [],
            "dependent": [],
        }

        # Get directly related nodes
        related = await self.get_related_nodes(node_id, direction="both")
        for node, relation in related:
            impact["direct"].append(node)

            # Get second-level relations
            second_level = await self.get_related_nodes(node.node_id, direction="outgoing")
            for second_node, _ in second_level:
                if second_node.node_id != node_id:
                    impact["indirect"].append(second_node)

        # Find dependent nodes (things that depend on this node)
        for node, relation in await self.get_related_nodes(node_id, direction="incoming"):
            if relation.relation_type == RelationType.DEPENDS_ON:
                impact["dependent"].append(node)

        # Remove duplicates
        for key in impact:
            seen = set()
            unique = []
            for node in impact[key]:
                if node.node_id not in seen:
                    seen.add(node.node_id)
                    unique.append(node)
            impact[key] = unique

        return impact

    async def delete_node(self, node_id: str) -> bool:
        """Delete a node and its relationships.

        Args:
            node_id: Node identifier

        Returns:
            True if deleted
        """
        if node_id not in self._nodes:
            return False

        # Remove all relations involving this node
        relations_to_remove = []
        for rel_id, rel in self._relations.items():
            if rel.source_id == node_id or rel.target_id == node_id:
                relations_to_remove.append(rel_id)

        for rel_id in relations_to_remove:
            del self._relations[rel_id]

        # Clean up adjacency lists
        if node_id in self._outgoing:
            del self._outgoing[node_id]
        if node_id in self._incoming:
            del self._incoming[node_id]

        # Remove from other nodes' lists
        for node_list in self._outgoing.values():
            node_list[:] = [r for r in node_list if r not in relations_to_remove]
        for node_list in self._incoming.values():
            node_list[:] = [r for r in node_list if r not in relations_to_remove]

        # Remove node
        del self._nodes[node_id]

        return True

    async def clear(self) -> None:
        """Clear all nodes and relationships."""
        self._nodes.clear()
        self._relations.clear()
        self._outgoing.clear()
        self._incoming.clear()
        self.logger.info("graph_cleared")

    async def close(self) -> None:
        """Close the graph (no-op for in-memory)."""
        pass

    def get_statistics(self) -> dict[str, int]:
        """Get graph statistics.

        Returns:
            Dictionary with node and relation counts
        """
        node_counts: dict[str, int] = {}
        for node in self._nodes.values():
            type_name = node.node_type.value
            node_counts[type_name] = node_counts.get(type_name, 0) + 1

        relation_counts: dict[str, int] = {}
        for rel in self._relations.values():
            type_name = rel.relation_type.value
            relation_counts[type_name] = relation_counts.get(type_name, 0) + 1

        return {
            "total_nodes": len(self._nodes),
            "total_relations": len(self._relations),
            "node_types": node_counts,
            "relation_types": relation_counts,
        }
