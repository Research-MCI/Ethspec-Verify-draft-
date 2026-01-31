"""Verification-related exceptions for Layer 3.

This module defines exceptions that can occur during the verification
process, including RAG retrieval, reasoning, and report generation.
"""

from __future__ import annotations


class VerificationError(Exception):
    """Base exception for verification-related errors.

    Attributes:
        message: Error message
        run_id: Optional verification run ID
        requirement_id: Optional requirement being verified
    """

    def __init__(
        self,
        message: str,
        run_id: str | None = None,
        requirement_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.run_id = run_id
        self.requirement_id = requirement_id

    def __str__(self) -> str:
        parts = [self.message]
        if self.run_id:
            parts.append(f" (run: {self.run_id})")
        if self.requirement_id:
            parts.append(f" (requirement: {self.requirement_id})")
        return "".join(parts)


class SpecificationNotFoundError(VerificationError):
    """Exception when required specification cannot be found.

    Raised when the specification needed for verification is not
    available in the knowledge base.
    """

    def __init__(
        self,
        message: str,
        fork_version: str | None = None,
        spec_category: str | None = None,
    ) -> None:
        super().__init__(message)
        self.fork_version = fork_version
        self.spec_category = spec_category


class RAGRetrievalError(VerificationError):
    """Exception for RAG retrieval failures.

    Raised when the RAG system fails to retrieve relevant context.
    """

    def __init__(
        self,
        message: str,
        query: str | None = None,
        retrieval_count: int = 0,
    ) -> None:
        super().__init__(message)
        self.query = query
        self.retrieval_count = retrieval_count


class ReasoningError(VerificationError):
    """Exception for Chain-of-Thought reasoning failures.

    Raised when the reasoning engine fails to produce valid output.
    """

    def __init__(
        self,
        message: str,
        reasoning_step: str | None = None,
        llm_error: str | None = None,
    ) -> None:
        super().__init__(message)
        self.reasoning_step = reasoning_step
        self.llm_error = llm_error


class ConfidenceCalculationError(VerificationError):
    """Exception for confidence score calculation failures.

    Raised when confidence scores cannot be calculated properly.
    """

    def __init__(
        self,
        message: str,
        evidence_count: int = 0,
        calculation_error: str | None = None,
    ) -> None:
        super().__init__(message)
        self.evidence_count = evidence_count
        self.calculation_error = calculation_error


class ReportGenerationError(VerificationError):
    """Exception for report generation failures.

    Raised when the verification report cannot be generated.
    """

    def __init__(
        self,
        message: str,
        report_format: str | None = None,
        output_path: str | None = None,
    ) -> None:
        super().__init__(message)
        self.report_format = report_format
        self.output_path = output_path
