"""Validation utility functions.

This module provides common validation functions for input validation.
"""

from __future__ import annotations

from pathlib import Path

from src.core.exceptions import ConfigurationError, ValidationError
from src.shared.constants import SUPPORTED_FORKS, SUPPORTED_LANGUAGES


def validate_fork_version(fork: str, raise_error: bool = True) -> bool:
    """Validate that a fork version is supported.

    Args:
        fork: Fork version to validate
        raise_error: Whether to raise an error on invalid input

    Returns:
        True if valid

    Raises:
        ValidationError: If fork is invalid and raise_error is True
    """
    fork_lower = fork.lower()
    is_valid = fork_lower in SUPPORTED_FORKS

    if not is_valid and raise_error:
        raise ValidationError(
            f"Invalid fork version: {fork}",
            field="fork",
            value=fork,
            expected=f"One of: {', '.join(SUPPORTED_FORKS)}",
        )

    return is_valid


def validate_language(language: str, raise_error: bool = True) -> bool:
    """Validate that a programming language is supported.

    Args:
        language: Language to validate
        raise_error: Whether to raise an error on invalid input

    Returns:
        True if valid

    Raises:
        ValidationError: If language is invalid and raise_error is True
    """
    lang_lower = language.lower()
    is_valid = lang_lower in SUPPORTED_LANGUAGES

    if not is_valid and raise_error:
        raise ValidationError(
            f"Invalid language: {language}",
            field="language",
            value=language,
            expected=f"One of: {', '.join(SUPPORTED_LANGUAGES)}",
        )

    return is_valid


def validate_file_path(
    path: str | Path,
    must_exist: bool = True,
    must_be_file: bool = True,
    allowed_extensions: tuple[str, ...] | None = None,
    raise_error: bool = True,
) -> bool:
    """Validate a file path.

    Args:
        path: Path to validate
        must_exist: Whether the file must exist
        must_be_file: Whether the path must be a file (not directory)
        allowed_extensions: Tuple of allowed file extensions
        raise_error: Whether to raise an error on invalid input

    Returns:
        True if valid

    Raises:
        ValidationError: If path is invalid and raise_error is True
    """
    path_obj = Path(path)

    # Check existence
    if must_exist and not path_obj.exists():
        if raise_error:
            raise ValidationError(
                f"Path does not exist: {path}",
                field="path",
                value=str(path),
            )
        return False

    # Check if it's a file
    if must_exist and must_be_file and not path_obj.is_file():
        if raise_error:
            raise ValidationError(
                f"Path is not a file: {path}",
                field="path",
                value=str(path),
            )
        return False

    # Check extension
    if allowed_extensions:
        if path_obj.suffix.lower() not in allowed_extensions:
            if raise_error:
                raise ValidationError(
                    f"Invalid file extension: {path_obj.suffix}",
                    field="path",
                    value=str(path),
                    expected=f"One of: {', '.join(allowed_extensions)}",
                )
            return False

    return True


def validate_confidence_threshold(
    threshold: float,
    raise_error: bool = True,
) -> bool:
    """Validate a confidence threshold value.

    Args:
        threshold: Threshold value to validate
        raise_error: Whether to raise an error on invalid input

    Returns:
        True if valid

    Raises:
        ValidationError: If threshold is invalid and raise_error is True
    """
    is_valid = 0.0 <= threshold <= 1.0

    if not is_valid and raise_error:
        raise ValidationError(
            f"Invalid confidence threshold: {threshold}",
            field="confidence_threshold",
            value=threshold,
            expected="Value between 0.0 and 1.0",
        )

    return is_valid


def validate_api_key(
    api_key: str,
    key_name: str = "API key",
    raise_error: bool = True,
) -> bool:
    """Validate that an API key is not empty.

    Args:
        api_key: API key to validate
        key_name: Name of the key for error messages
        raise_error: Whether to raise an error on invalid input

    Returns:
        True if valid

    Raises:
        ConfigurationError: If API key is empty and raise_error is True
    """
    is_valid = bool(api_key and api_key.strip())

    if not is_valid and raise_error:
        raise ConfigurationError(
            f"{key_name} is not configured",
            config_key=key_name,
        )

    return is_valid


def validate_positive_int(
    value: int,
    field_name: str,
    min_value: int = 1,
    max_value: int | None = None,
    raise_error: bool = True,
) -> bool:
    """Validate a positive integer value.

    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_value: Minimum allowed value
        max_value: Maximum allowed value (None for no limit)
        raise_error: Whether to raise an error on invalid input

    Returns:
        True if valid

    Raises:
        ValidationError: If value is invalid and raise_error is True
    """
    is_valid = value >= min_value
    if max_value is not None:
        is_valid = is_valid and value <= max_value

    if not is_valid and raise_error:
        if max_value is not None:
            expected = f"Integer between {min_value} and {max_value}"
        else:
            expected = f"Integer >= {min_value}"

        raise ValidationError(
            f"Invalid {field_name}: {value}",
            field=field_name,
            value=value,
            expected=expected,
        )

    return is_valid
