"""JSON utility functions.

This module provides utilities for safe JSON parsing, extraction from
text, and schema validation.
"""

from __future__ import annotations

import json
import re
from typing import Any


def safe_json_loads(text: str) -> tuple[Any | None, str | None]:
    """Safely parse JSON from a string.

    Args:
        text: The JSON string to parse

    Returns:
        Tuple of (parsed_data, error_message)
        - If successful: (data, None)
        - If failed: (None, error_message)
    """
    try:
        data = json.loads(text)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"JSON decode error at position {e.pos}: {e.msg}"


def safe_json_dumps(
    data: Any,
    indent: int | None = 2,
    ensure_ascii: bool = False,
) -> str:
    """Safely serialize data to JSON string.

    Args:
        data: Data to serialize
        indent: Indentation level (None for compact)
        ensure_ascii: Whether to escape non-ASCII characters

    Returns:
        JSON string representation
    """
    return json.dumps(
        data,
        indent=indent,
        ensure_ascii=ensure_ascii,
        default=str,  # Handle non-serializable types
    )


def extract_json_from_text(text: str) -> list[dict[str, Any]]:
    """Extract all valid JSON objects from text.

    This is useful for extracting JSON from LLM outputs that may contain
    additional text or multiple JSON objects.

    Args:
        text: Text potentially containing JSON

    Returns:
        List of successfully parsed JSON objects
    """
    results: list[dict[str, Any]] = []

    # Pattern 1: JSON in code blocks
    code_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
    for match in re.finditer(code_block_pattern, text):
        content = match.group(1).strip()
        data, error = safe_json_loads(content)
        if error is None and isinstance(data, dict):
            results.append(data)

    # Pattern 2: Standalone JSON objects (brace matching)
    brace_depth = 0
    start_idx = None

    for i, char in enumerate(text):
        if char == "{":
            if brace_depth == 0:
                start_idx = i
            brace_depth += 1
        elif char == "}":
            brace_depth -= 1
            if brace_depth == 0 and start_idx is not None:
                candidate = text[start_idx : i + 1]
                data, error = safe_json_loads(candidate)
                if error is None and isinstance(data, dict):
                    # Avoid duplicates from code blocks
                    if data not in results:
                        results.append(data)
                start_idx = None

    return results


def validate_json_schema(
    data: dict[str, Any],
    required_fields: list[str] | None = None,
    field_types: dict[str, type] | None = None,
) -> tuple[bool, list[str]]:
    """Validate JSON data against a simple schema.

    Args:
        data: The data to validate
        required_fields: List of required field names
        field_types: Dictionary mapping field names to expected types

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors: list[str] = []

    # Check required fields
    if required_fields:
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

    # Check field types
    if field_types:
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                actual_type = type(data[field]).__name__
                expected_name = expected_type.__name__
                errors.append(
                    f"Field '{field}' has wrong type: expected {expected_name}, got {actual_type}"
                )

    return len(errors) == 0, errors


def merge_json_objects(*objects: dict[str, Any]) -> dict[str, Any]:
    """Deep merge multiple JSON objects.

    Later objects override earlier ones for conflicting keys.
    Nested dictionaries are merged recursively.

    Args:
        *objects: JSON objects to merge

    Returns:
        Merged JSON object
    """
    result: dict[str, Any] = {}

    for obj in objects:
        for key, value in obj.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = merge_json_objects(result[key], value)
            else:
                result[key] = value

    return result


def flatten_json(
    data: dict[str, Any],
    separator: str = ".",
    prefix: str = "",
) -> dict[str, Any]:
    """Flatten a nested JSON object.

    Args:
        data: Nested JSON object
        separator: Separator for nested keys
        prefix: Prefix for keys (used in recursion)

    Returns:
        Flattened dictionary with dotted keys

    Example:
        {"a": {"b": 1}} -> {"a.b": 1}
    """
    result: dict[str, Any] = {}

    for key, value in data.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key

        if isinstance(value, dict):
            result.update(flatten_json(value, separator, new_key))
        else:
            result[new_key] = value

    return result
