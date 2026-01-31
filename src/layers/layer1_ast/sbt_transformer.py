"""Structure-Based Traversal (SBT) transformer.

This module transforms AST nodes into linearized SBT representations
suitable for sequence-based analysis.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.entities.behavioral_model import ASTNode


class SBTTransformer:
    """Transforms AST to Structure-Based Traversal representation.

    SBT creates a linearized representation of the AST that preserves
    structural information while being suitable for sequential processing.
    """

    def __init__(
        self,
        include_values: bool = True,
        include_names: bool = True,
        max_depth: int | None = None,
    ) -> None:
        """Initialize the SBT transformer.

        Args:
            include_values: Whether to include node values
            include_names: Whether to include node names
            max_depth: Maximum depth to traverse (None for unlimited)
        """
        self.include_values = include_values
        self.include_names = include_names
        self.max_depth = max_depth

    def transform(self, ast: ASTNode) -> str:
        """Transform AST to SBT string representation.

        Args:
            ast: The AST root node

        Returns:
            SBT string representation
        """
        tokens: list[str] = []
        self._traverse(ast, tokens, depth=0)
        return " ".join(tokens)

    def transform_to_tokens(self, ast: ASTNode) -> list[str]:
        """Transform AST to list of SBT tokens.

        Args:
            ast: The AST root node

        Returns:
            List of SBT tokens
        """
        tokens: list[str] = []
        self._traverse(ast, tokens, depth=0)
        return tokens

    def _traverse(
        self,
        node: ASTNode,
        tokens: list[str],
        depth: int,
    ) -> None:
        """Recursively traverse AST and generate SBT tokens.

        Args:
            node: Current AST node
            tokens: List to accumulate tokens
            depth: Current traversal depth
        """
        if self.max_depth is not None and depth > self.max_depth:
            return

        # Opening token with node type
        type_str = node.node_type.value
        tokens.append(f"({type_str}")

        # Include name if present and enabled
        if self.include_names and node.name:
            tokens.append(f"[{node.name}]")

        # Include value if present and enabled
        if self.include_values and node.value is not None:
            value_str = self._format_value(node.value)
            tokens.append(f"={value_str}")

        # Traverse children
        for child in node.children:
            self._traverse(child, tokens, depth + 1)

        # Closing token
        tokens.append(f"){type_str}")

    def _format_value(self, value: object) -> str:
        """Format a value for SBT representation.

        Args:
            value: The value to format

        Returns:
            Formatted value string
        """
        if isinstance(value, str):
            # Truncate long strings
            if len(value) > 20:
                return f'"{value[:17]}..."'
            return f'"{value}"'
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif value is None:
            return "null"
        else:
            return str(type(value).__name__)


class CompactSBTTransformer(SBTTransformer):
    """Compact SBT transformer for reduced token count.

    Creates a more compact representation by abbreviating type names
    and omitting some details.
    """

    # Type abbreviations
    TYPE_ABBREV = {
        "module": "M",
        "function": "F",
        "class": "C",
        "assignment": "A",
        "if": "I",
        "for": "L",  # Loop
        "while": "W",
        "return": "R",
        "call": "X",  # eXecute
        "import": "P",  # imPort
        "constant": "K",
        "name": "N",
        "attribute": "T",  # aTtribute
        "binary_op": "B",
        "compare": "Q",  # compare/Query
        "expression": "E",
        "unknown": "U",
    }

    def __init__(self, max_depth: int | None = 10) -> None:
        """Initialize compact transformer with defaults."""
        super().__init__(
            include_values=False,
            include_names=True,
            max_depth=max_depth,
        )

    def _traverse(
        self,
        node: ASTNode,
        tokens: list[str],
        depth: int,
    ) -> None:
        """Traverse with compact representation.

        Args:
            node: Current AST node
            tokens: List to accumulate tokens
            depth: Current traversal depth
        """
        if self.max_depth is not None and depth > self.max_depth:
            return

        # Use abbreviated type
        type_str = self.TYPE_ABBREV.get(node.node_type.value, "U")
        tokens.append(f"({type_str}")

        # Include name for important nodes only
        if self.include_names and node.name and node.node_type.value in (
            "function",
            "class",
            "assignment",
            "name",
        ):
            tokens.append(f"[{node.name}]")

        # Traverse children
        for child in node.children:
            self._traverse(child, tokens, depth + 1)

        # Closing token
        tokens.append(f"){type_str}")
