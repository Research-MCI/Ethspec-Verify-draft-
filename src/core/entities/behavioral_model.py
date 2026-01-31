"""Behavioral model entity representing extracted code behavior.

This module defines the data structures for representing code behavior
extracted through AST analysis, control flow graphs, and data flow analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    """Types of AST nodes."""

    MODULE = "module"
    FUNCTION = "function"
    CLASS = "class"
    ASSIGNMENT = "assignment"
    IF = "if"
    FOR = "for"
    WHILE = "while"
    RETURN = "return"
    CALL = "call"
    IMPORT = "import"
    EXPRESSION = "expression"
    CONSTANT = "constant"
    NAME = "name"
    ATTRIBUTE = "attribute"
    BINARY_OP = "binary_op"
    COMPARE = "compare"
    SUBSCRIPT = "subscript"
    LIST = "list"
    DICT = "dict"
    TUPLE = "tuple"
    TRY = "try"
    RAISE = "raise"
    ASSERT = "assert"
    WITH = "with"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ASTNode:
    """Represents a node in the Abstract Syntax Tree.

    Attributes:
        node_type: The type of AST node
        name: Optional name associated with the node
        value: Optional value (for constants, literals)
        children: Child nodes in the AST
        metadata: Additional metadata about the node
        line_number: Source code line number
        column: Source code column offset
    """

    node_type: NodeType
    name: str | None = None
    value: Any = None
    children: tuple[ASTNode, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)
    line_number: int | None = None
    column: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert AST node to dictionary representation."""
        result: dict[str, Any] = {"type": self.node_type.value}

        if self.name:
            result["name"] = self.name
        if self.value is not None:
            result["value"] = self.value
        if self.children:
            result["children"] = [child.to_dict() for child in self.children]
        if self.metadata:
            result["metadata"] = self.metadata
        if self.line_number is not None:
            result["line"] = self.line_number
        if self.column is not None:
            result["col"] = self.column

        return result


@dataclass(frozen=True)
class CFGNode:
    """Represents a node in the Control Flow Graph.

    Attributes:
        node_id: Unique identifier for the node
        node_type: Type of control flow node
        label: Human-readable label
        ast_node: Reference to the corresponding AST node
        is_entry: Whether this is an entry point
        is_exit: Whether this is an exit point
    """

    node_id: str
    node_type: str
    label: str
    ast_node: ASTNode | None = None
    is_entry: bool = False
    is_exit: bool = False


@dataclass(frozen=True)
class CFGEdge:
    """Represents an edge in the Control Flow Graph.

    Attributes:
        source: Source node ID
        target: Target node ID
        condition: Optional condition for conditional edges
        edge_type: Type of edge (normal, true_branch, false_branch, exception)
    """

    source: str
    target: str
    condition: str | None = None
    edge_type: str = "normal"


@dataclass(frozen=True)
class ControlFlowGraph:
    """Represents the Control Flow Graph of a code unit.

    Attributes:
        nodes: All nodes in the CFG
        edges: All edges connecting nodes
        entry_node: The entry point node ID
        exit_nodes: List of exit point node IDs
    """

    nodes: tuple[CFGNode, ...]
    edges: tuple[CFGEdge, ...]
    entry_node: str
    exit_nodes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert CFG to dictionary representation."""
        return {
            "nodes": [
                {
                    "id": n.node_id,
                    "type": n.node_type,
                    "label": n.label,
                    "is_entry": n.is_entry,
                    "is_exit": n.is_exit,
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "condition": e.condition,
                    "type": e.edge_type,
                }
                for e in self.edges
            ],
            "entry": self.entry_node,
            "exits": list(self.exit_nodes),
        }


@dataclass(frozen=True)
class DataFlowInfo:
    """Contains data flow analysis results.

    Attributes:
        state_reads: Variables/state that are read
        state_writes: Variables/state that are written
        constants: Constant values defined
        imports: Imported modules/names
        function_calls: Functions that are called
        type_definitions: Type annotations and definitions
        global_refs: References to global variables
    """

    state_reads: tuple[str, ...] = field(default_factory=tuple)
    state_writes: tuple[str, ...] = field(default_factory=tuple)
    constants: tuple[Any, ...] = field(default_factory=tuple)
    imports: tuple[str, ...] = field(default_factory=tuple)
    function_calls: tuple[str, ...] = field(default_factory=tuple)
    type_definitions: tuple[str, ...] = field(default_factory=tuple)
    global_refs: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Convert data flow info to dictionary representation."""
        return {
            "state_reads": list(self.state_reads),
            "state_writes": list(self.state_writes),
            "constants": list(self.constants),
            "imports": list(self.imports),
            "function_calls": list(self.function_calls),
            "type_definitions": list(self.type_definitions),
            "global_refs": list(self.global_refs),
        }


@dataclass(frozen=True)
class BehavioralModel:
    """Represents the extracted behavioral model from source code.

    This is the primary output of Layer 1, containing all structural and
    behavioral information extracted from the source code.

    Attributes:
        source_file: Path to the source file
        ast: The root AST node
        sbt: Structure-Based Traversal string representation
        cfg: Control Flow Graph
        data_flow: Data flow analysis results
        precondition: Extracted precondition description
        postcondition: Extracted postcondition description
        invariant: Extracted invariant description
        semantic_score: Quality score of the extraction
        raw_source: Original source code
    """

    source_file: str
    ast: ASTNode
    sbt: str
    cfg: ControlFlowGraph
    data_flow: DataFlowInfo
    precondition: str
    postcondition: str
    invariant: str
    semantic_score: float
    raw_source: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert behavioral model to dictionary representation."""
        return {
            "source_file": self.source_file,
            "ast": self.ast.to_dict(),
            "sbt": self.sbt,
            "cfg": self.cfg.to_dict(),
            "data_flow": self.data_flow.to_dict(),
            "behavioral_model": {
                "precondition": self.precondition,
                "postcondition": self.postcondition,
                "invariant": self.invariant,
            },
            "semantic_score": self.semantic_score,
        }

    @property
    def is_valid(self) -> bool:
        """Check if the behavioral model meets minimum quality criteria."""
        return (
            self.semantic_score >= 0.3
            and len(self.ast.children) > 0
            and bool(self.precondition or self.postcondition or self.invariant)
        )
