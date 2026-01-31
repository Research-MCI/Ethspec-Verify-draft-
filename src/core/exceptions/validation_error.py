"""Validation-related exceptions.

This module defines exceptions for configuration and schema validation.
"""

from __future__ import annotations

from typing import Any


class ValidationError(Exception):
    """Base exception for validation-related errors.

    Attributes:
        message: Error message
        field: Field that failed validation
        value: The invalid value
        expected: Expected value or pattern
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        expected: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.field = field
        self.value = value
        self.expected = expected

    def __str__(self) -> str:
        parts = [self.message]
        if self.field:
            parts.append(f" (field: {self.field})")
        if self.expected:
            parts.append(f" Expected: {self.expected}")
        return "".join(parts)


class ConfigurationError(ValidationError):
    """Exception for configuration validation failures.

    Raised when configuration values are invalid or missing.
    """

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        config_file: str | None = None,
    ) -> None:
        super().__init__(message, field=config_key)
        self.config_key = config_key
        self.config_file = config_file


class SchemaValidationError(ValidationError):
    """Exception for JSON schema validation failures.

    Raised when data does not conform to expected schema.
    """

    def __init__(
        self,
        message: str,
        schema_path: str | None = None,
        validation_errors: list[str] | None = None,
        data: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.schema_path = schema_path
        self.validation_errors = validation_errors or []
        self.data = data

    def __str__(self) -> str:
        parts = [self.message]
        if self.validation_errors:
            parts.append(f"\nValidation errors: {', '.join(self.validation_errors)}")
        return "".join(parts)
