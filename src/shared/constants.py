"""Application constants and enumerations.

This module defines constants used throughout the application.
"""

from __future__ import annotations

from enum import Enum
from typing import Final

# =============================================================================
# Ethereum Fork Versions
# =============================================================================

SUPPORTED_FORKS: Final[tuple[str, ...]] = (
    "frontier",
    "homestead",
    "tangerine_whistle",
    "spurious_dragon",
    "byzantium",
    "constantinople",
    "petersburg",
    "istanbul",
    "muir_glacier",
    "berlin",
    "london",
    "arrow_glacier",
    "gray_glacier",
    "paris",
    "shanghai",
    "cancun",
    "prague",
)

DEFAULT_FORK: Final[str] = "cancun"

# =============================================================================
# Programming Languages
# =============================================================================

SUPPORTED_LANGUAGES: Final[tuple[str, ...]] = (
    "python",
    "solidity",
    "rust",
    "go",
    "javascript",
    "typescript",
)

DEFAULT_LANGUAGE: Final[str] = "python"

# =============================================================================
# Verification Thresholds
# =============================================================================

DEFAULT_CONFIDENCE_THRESHOLD: Final[float] = 0.7
MIN_SEMANTIC_SCORE: Final[float] = 0.3
HIGH_CONFIDENCE_THRESHOLD: Final[float] = 0.8
LOW_CONFIDENCE_THRESHOLD: Final[float] = 0.5

# =============================================================================
# RAG Configuration
# =============================================================================

DEFAULT_TOP_K: Final[int] = 10
MAX_TOP_K: Final[int] = 50
DEFAULT_CHUNK_SIZE: Final[int] = 512
DEFAULT_CHUNK_OVERLAP: Final[int] = 50
MIN_CHUNK_SIZE: Final[int] = 100
MAX_CHUNK_SIZE: Final[int] = 2000

# =============================================================================
# LLM Configuration
# =============================================================================

DEFAULT_TEMPERATURE: Final[float] = 0.1
DEFAULT_MAX_TOKENS: Final[int] = 8192
MAX_RETRIES: Final[int] = 3
RETRY_DELAY_SECONDS: Final[float] = 1.0

# =============================================================================
# File Extensions
# =============================================================================

PYTHON_EXTENSIONS: Final[tuple[str, ...]] = (".py", ".pyi")
MARKDOWN_EXTENSIONS: Final[tuple[str, ...]] = (".md", ".markdown")
SPEC_EXTENSIONS: Final[tuple[str, ...]] = (".py", ".md", ".rst", ".txt")

# =============================================================================
# GitHub Integration
# =============================================================================

GITHUB_API_VERSION: Final[str] = "2022-11-28"
MAX_PR_COMMENT_LENGTH: Final[int] = 65536
MAX_FINDINGS_IN_COMMENT: Final[int] = 20

# =============================================================================
# Report Configuration
# =============================================================================

SARIF_SCHEMA_VERSION: Final[str] = "2.1.0"
SARIF_SCHEMA_URI: Final[str] = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
)

# =============================================================================
# Enumerations
# =============================================================================


class Environment(str, Enum):
    """Deployment environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class OutputFormat(str, Enum):
    """Output format options."""

    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    SARIF = "sarif"
    CONSOLE = "console"


class VerbosityLevel(str, Enum):
    """Verbosity level for output."""

    QUIET = "quiet"
    NORMAL = "normal"
    VERBOSE = "verbose"
    DEBUG = "debug"


# =============================================================================
# Error Messages
# =============================================================================


class ErrorMessages:
    """Standard error messages."""

    INVALID_FORK = "Invalid fork version: {fork}. Supported forks: {supported}"
    INVALID_LANGUAGE = "Invalid language: {lang}. Supported languages: {supported}"
    FILE_NOT_FOUND = "File not found: {path}"
    PARSE_ERROR = "Failed to parse {file}: {error}"
    LLM_ERROR = "LLM request failed: {error}"
    EMBEDDING_ERROR = "Embedding generation failed: {error}"
    VERIFICATION_ERROR = "Verification failed: {error}"
    CONFIG_ERROR = "Configuration error: {error}"


# =============================================================================
# Success Messages
# =============================================================================


class SuccessMessages:
    """Standard success messages."""

    INGESTION_COMPLETE = "Successfully ingested {count} specification chunks"
    VERIFICATION_COMPLETE = "Verification complete: {status}"
    REPORT_GENERATED = "Report generated: {path}"
