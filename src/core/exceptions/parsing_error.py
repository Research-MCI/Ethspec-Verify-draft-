"""Parsing-related exceptions for Layer 1.

This module defines exceptions that can occur during AST parsing,
JSON validation, and semantic analysis.
"""

from __future__ import annotations


class ParsingError(Exception):
    """Base exception for parsing-related errors.

    Attributes:
        message: Error message
        source: Optional source code or file that caused the error
        line_number: Optional line number where error occurred
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        source: str | None = None,
        line_number: int | None = None,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.source = source
        self.line_number = line_number
        self.details = details or {}

    def __str__(self) -> str:
        parts = [self.message]
        if self.line_number is not None:
            parts.append(f" (line {self.line_number})")
        if self.source:
            preview = self.source[:100] + "..." if len(self.source) > 100 else self.source
            parts.append(f"\nSource: {preview}")
        return "".join(parts)


class SourceCodeError(ParsingError):
    """Exception for invalid or unreadable source code.

    Raised when the input source code cannot be processed.
    """

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        encoding_error: bool = False,
    ) -> None:
        super().__init__(message)
        self.file_path = file_path
        self.encoding_error = encoding_error


class JSONParsingError(ParsingError):
    """Exception for JSON parsing failures.

    Raised when LLM output cannot be parsed as valid JSON.
    """

    def __init__(
        self,
        message: str,
        raw_output: str | None = None,
        json_error: str | None = None,
    ) -> None:
        super().__init__(message, source=raw_output)
        self.raw_output = raw_output
        self.json_error = json_error


class ASTGenerationError(ParsingError):
    """Exception for AST generation failures.

    Raised when the LLM fails to generate a valid AST.
    """

    def __init__(
        self,
        message: str,
        llm_response: str | None = None,
        validation_errors: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.llm_response = llm_response
        self.validation_errors = validation_errors or []


class SemanticValidationError(ParsingError):
    """Exception for semantic validation failures.

    Raised when the AST passes structural validation but fails
    semantic quality checks.
    """

    def __init__(
        self,
        message: str,
        semantic_score: float,
        threshold: float,
        missing_elements: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.semantic_score = semantic_score
        self.threshold = threshold
        self.missing_elements = missing_elements or []

    def __str__(self) -> str:
        return (
            f"{self.message} "
            f"(score: {self.semantic_score:.2f}, threshold: {self.threshold:.2f})"
        )
