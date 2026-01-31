"""Core exceptions for the verification framework."""

from src.core.exceptions.parsing_error import (
    ASTGenerationError,
    JSONParsingError,
    ParsingError,
    SemanticValidationError,
    SourceCodeError,
)
from src.core.exceptions.validation_error import (
    ConfigurationError,
    SchemaValidationError,
    ValidationError,
)
from src.core.exceptions.verification_error import (
    ConfidenceCalculationError,
    RAGRetrievalError,
    ReasoningError,
    ReportGenerationError,
    SpecificationNotFoundError,
    VerificationError,
)

__all__ = [
    # Parsing Errors
    "ASTGenerationError",
    "JSONParsingError",
    "ParsingError",
    "SemanticValidationError",
    "SourceCodeError",
    # Validation Errors
    "ConfigurationError",
    "SchemaValidationError",
    "ValidationError",
    # Verification Errors
    "ConfidenceCalculationError",
    "RAGRetrievalError",
    "ReasoningError",
    "ReportGenerationError",
    "SpecificationNotFoundError",
    "VerificationError",
]
