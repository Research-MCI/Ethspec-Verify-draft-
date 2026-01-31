"""Control Flow Graph (CFG) generator.

This module generates control flow graphs from AST representations
for execution path modeling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from src.core.entities.behavioral_model import (
    CFGEdge,
    CFGNode,
    ControlFlowGraph,
    NodeType,
)

if TYPE_CHECKING:
    from src.core.entities.behavioral_model import ASTNode


class CFGGenerator:
    """Generates Control Flow Graphs from AST.

    Creates a CFG representation that models all possible execution
    paths through the code.
    """

    def __init__(self) -> None:
        """Initialize the CFG generator."""
        self._nodes: list[CFGNode] = []
        self._edges: list[CFGEdge] = []
        self._node_counter = 0

    def generate(self, ast: ASTNode) -> ControlFlowGraph:
        """Generate a CFG from an AST.

        Args:
            ast: The AST root node

        Returns:
            ControlFlowGraph instance
        """
        # Reset state
        self._nodes = []
        self._edges = []
        self._node_counter = 0

        # Create entry node
        entry_node = self._create_node("entry", "Entry", is_entry=True)

        # Process AST
        exit_nodes = self._process_node(ast, entry_node.node_id)

        # Create exit node
        exit_node = self._create_node("exit", "Exit", is_exit=True)

        # Connect all exit points to the exit node
        for exit_id in exit_nodes:
            self._create_edge(exit_id, exit_node.node_id)

        return ControlFlowGraph(
            nodes=tuple(self._nodes),
            edges=tuple(self._edges),
            entry_node=entry_node.node_id,
            exit_nodes=(exit_node.node_id,),
        )

    def _create_node(
        self,
        node_type: str,
        label: str,
        ast_node: ASTNode | None = None,
        is_entry: bool = False,
        is_exit: bool = False,
    ) -> CFGNode:
        """Create a CFG node.

        Args:
            node_type: Type of CFG node
            label: Human-readable label
            ast_node: Optional reference to AST node
            is_entry: Whether this is an entry node
            is_exit: Whether this is an exit node

        Returns:
            Created CFGNode
        """
        self._node_counter += 1
        node_id = f"n{self._node_counter}"

        node = CFGNode(
            node_id=node_id,
            node_type=node_type,
            label=label,
            ast_node=ast_node,
            is_entry=is_entry,
            is_exit=is_exit,
        )
        self._nodes.append(node)
        return node

    def _create_edge(
        self,
        source: str,
        target: str,
        condition: str | None = None,
        edge_type: str = "normal",
    ) -> CFGEdge:
        """Create a CFG edge.

        Args:
            source: Source node ID
            target: Target node ID
            condition: Optional condition label
            edge_type: Type of edge

        Returns:
            Created CFGEdge
        """
        edge = CFGEdge(
            source=source,
            target=target,
            condition=condition,
            edge_type=edge_type,
        )
        self._edges.append(edge)
        return edge

    def _process_node(
        self,
        node: ASTNode,
        current_id: str,
    ) -> list[str]:
        """Process an AST node and return exit point IDs.

        Args:
            node: The AST node to process
            current_id: Current CFG node ID

        Returns:
            List of exit point node IDs
        """
        node_type = node.node_type

        if node_type == NodeType.MODULE:
            return self._process_module(node, current_id)
        elif node_type == NodeType.FUNCTION:
            return self._process_function(node, current_id)
        elif node_type == NodeType.IF:
            return self._process_if(node, current_id)
        elif node_type == NodeType.FOR:
            return self._process_for(node, current_id)
        elif node_type == NodeType.WHILE:
            return self._process_while(node, current_id)
        elif node_type == NodeType.TRY:
            return self._process_try(node, current_id)
        elif node_type == NodeType.RETURN:
            return self._process_return(node, current_id)
        else:
            return self._process_statement(node, current_id)

    def _process_module(self, node: ASTNode, current_id: str) -> list[str]:
        """Process a module node (sequence of statements).

        Args:
            node: Module AST node
            current_id: Current CFG node ID

        Returns:
            List of exit point node IDs
        """
        exit_points = [current_id]

        for child in node.children:
            new_exit_points = []
            for exit_id in exit_points:
                new_exit_points.extend(self._process_node(child, exit_id))
            exit_points = new_exit_points

        return exit_points

    def _process_function(self, node: ASTNode, current_id: str) -> list[str]:
        """Process a function definition.

        Args:
            node: Function AST node
            current_id: Current CFG node ID

        Returns:
            List of exit point node IDs
        """
        func_name = node.name or "anonymous"
        func_node = self._create_node("function", f"def {func_name}", node)
        self._create_edge(current_id, func_node.node_id)

        # Process function body
        exit_points = [func_node.node_id]
        for child in node.children:
            new_exit_points = []
            for exit_id in exit_points:
                new_exit_points.extend(self._process_node(child, exit_id))
            exit_points = new_exit_points

        return exit_points

    def _process_if(self, node: ASTNode, current_id: str) -> list[str]:
        """Process an if statement.

        Args:
            node: If AST node
            current_id: Current CFG node ID

        Returns:
            List of exit point node IDs
        """
        # Create condition node
        condition_node = self._create_node("condition", "if condition", node)
        self._create_edge(current_id, condition_node.node_id)

        exit_points: list[str] = []

        # Process true branch
        true_branch = self._create_node("block", "then", node)
        self._create_edge(
            condition_node.node_id,
            true_branch.node_id,
            condition="True",
            edge_type="true_branch",
        )

        # Process children in true branch
        true_exits = [true_branch.node_id]
        for i, child in enumerate(node.children):
            if i == 0:  # Assuming first child is condition, skip
                continue
            new_exits = []
            for exit_id in true_exits:
                new_exits.extend(self._process_node(child, exit_id))
            true_exits = new_exits

        exit_points.extend(true_exits)

        # Create false branch (else or fall-through)
        false_branch = self._create_node("block", "else", node)
        self._create_edge(
            condition_node.node_id,
            false_branch.node_id,
            condition="False",
            edge_type="false_branch",
        )
        exit_points.append(false_branch.node_id)

        return exit_points

    def _process_for(self, node: ASTNode, current_id: str) -> list[str]:
        """Process a for loop.

        Args:
            node: For AST node
            current_id: Current CFG node ID

        Returns:
            List of exit point node IDs
        """
        # Create loop header
        loop_header = self._create_node("loop_header", "for", node)
        self._create_edge(current_id, loop_header.node_id)

        # Create loop body
        loop_body = self._create_node("loop_body", "loop body", node)
        self._create_edge(
            loop_header.node_id,
            loop_body.node_id,
            condition="iterate",
            edge_type="true_branch",
        )

        # Process body
        body_exits = [loop_body.node_id]
        for child in node.children:
            new_exits = []
            for exit_id in body_exits:
                new_exits.extend(self._process_node(child, exit_id))
            body_exits = new_exits

        # Back edge to loop header
        for exit_id in body_exits:
            self._create_edge(exit_id, loop_header.node_id, edge_type="back")

        # Exit edge
        loop_exit = self._create_node("block", "loop exit", node)
        self._create_edge(
            loop_header.node_id,
            loop_exit.node_id,
            condition="done",
            edge_type="false_branch",
        )

        return [loop_exit.node_id]

    def _process_while(self, node: ASTNode, current_id: str) -> list[str]:
        """Process a while loop.

        Args:
            node: While AST node
            current_id: Current CFG node ID

        Returns:
            List of exit point node IDs
        """
        # Similar structure to for loop
        loop_header = self._create_node("loop_header", "while", node)
        self._create_edge(current_id, loop_header.node_id)

        loop_body = self._create_node("loop_body", "loop body", node)
        self._create_edge(
            loop_header.node_id,
            loop_body.node_id,
            condition="True",
            edge_type="true_branch",
        )

        # Process body
        body_exits = [loop_body.node_id]
        for child in node.children:
            new_exits = []
            for exit_id in body_exits:
                new_exits.extend(self._process_node(child, exit_id))
            body_exits = new_exits

        # Back edge
        for exit_id in body_exits:
            self._create_edge(exit_id, loop_header.node_id, edge_type="back")

        # Exit edge
        loop_exit = self._create_node("block", "loop exit", node)
        self._create_edge(
            loop_header.node_id,
            loop_exit.node_id,
            condition="False",
            edge_type="false_branch",
        )

        return [loop_exit.node_id]

    def _process_try(self, node: ASTNode, current_id: str) -> list[str]:
        """Process a try/except block.

        Args:
            node: Try AST node
            current_id: Current CFG node ID

        Returns:
            List of exit point node IDs
        """
        try_node = self._create_node("try", "try", node)
        self._create_edge(current_id, try_node.node_id)

        exit_points: list[str] = []

        # Try block
        try_exits = [try_node.node_id]
        for child in node.children:
            new_exits = []
            for exit_id in try_exits:
                new_exits.extend(self._process_node(child, exit_id))
            try_exits = new_exits
        exit_points.extend(try_exits)

        # Exception handler
        except_node = self._create_node("except", "except", node)
        self._create_edge(
            try_node.node_id,
            except_node.node_id,
            condition="exception",
            edge_type="exception",
        )
        exit_points.append(except_node.node_id)

        return exit_points

    def _process_return(self, node: ASTNode, current_id: str) -> list[str]:
        """Process a return statement.

        Args:
            node: Return AST node
            current_id: Current CFG node ID

        Returns:
            Empty list (return terminates flow)
        """
        return_node = self._create_node("return", "return", node)
        self._create_edge(current_id, return_node.node_id)
        return [return_node.node_id]

    def _process_statement(self, node: ASTNode, current_id: str) -> list[str]:
        """Process a general statement.

        Args:
            node: AST node
            current_id: Current CFG node ID

        Returns:
            List containing the new node ID
        """
        label = node.name or node.node_type.value
        stmt_node = self._create_node("statement", label, node)
        self._create_edge(current_id, stmt_node.node_id)
        return [stmt_node.node_id]
