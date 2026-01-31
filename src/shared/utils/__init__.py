"""Shared utility functions."""

from src.shared.utils.json_utils import (
    extract_json_from_text,
    safe_json_dumps,
    safe_json_loads,
    validate_json_schema,
)
from src.shared.utils.text_utils import (
    clean_text,
    extract_code_blocks,
    normalize_whitespace,
    truncate_text,
)
from src.shared.utils.validation import (
    validate_file_path,
    validate_fork_version,
    validate_language,
)

__all__ = [
    # JSON utilities
    "extract_json_from_text",
    "safe_json_dumps",
    "safe_json_loads",
    "validate_json_schema",
    # Text utilities
    "clean_text",
    "extract_code_blocks",
    "normalize_whitespace",
    "truncate_text",
    # Validation utilities
    "validate_file_path",
    "validate_fork_version",
    "validate_language",
]
