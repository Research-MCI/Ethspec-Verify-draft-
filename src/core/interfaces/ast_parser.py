"""AST parser interface for code analysis.

This module defines the abstract interface for AST parsing implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.core.entities.behavioral_model import ASTNode


@dataclass(frozen=True)
class ASTParserResult:
    """Result from AST parsing operation.

    Attributes:
        ast: The parsed AST root node
        raw_json: Raw JSON representation from LLM
        semantic_score: Semantic quality score
        is_valid: Whether the AST is valid
        validation_errors: List of validation errors if any
        metadata: Additional parsing metadata
    """

    ast: ASTNode | None
    raw_json: dict[str, Any]
    semantic_score: float
    is_valid: bool
    validation_errors: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def has_errors(self) -> bool:
        """Check if there were validation errors."""
        return len(self.validation_errors) > 0


class ASTParser(ABC):
    """Abstract interface for AST parsing implementations.

    Implementations should handle LLM-based AST induction from source code,
    JSON validation, and semantic scoring.
    """

    @abstractmethod
    async def parse(self, source_code: str, language: str = "python") -> ASTParserResult:
        """Parse source code and return AST result.

        Args:
            source_code: The source code to parse
            language: Programming language of the source code

        Returns:
            ASTParserResult containing the parsed AST and metadata
        """
        ...

    @abstractmethod
    async def parse_file(self, file_path: str) -> ASTParserResult:
        """Parse a source file and return AST result.

        Args:
            file_path: Path to the source file

        Returns:
            ASTParserResult containing the parsed AST and metadata
        """
        ...

    @abstractmethod
    def validate_ast(self, ast_json: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate AST JSON structure.

        Args:
            ast_json: The AST in JSON format

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        ...

    @abstractmethod
    def calculate_semantic_score(self, ast_json: dict[str, Any]) -> float:
        """Calculate semantic quality score for the AST.

        The score considers:
        - Presence of import nodes
        - State assignments
        - Type definitions
        - Constants
        - Function/class definitions
        - Control flow structures

        Args:
            ast_json: The AST in JSON format

        Returns:
            Semantic score between 0.0 and 1.0
        """
        ...
