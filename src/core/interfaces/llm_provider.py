"""LLM provider interface for language model interactions.

This module defines the abstract interface for LLM provider implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ResponseFormat(str, Enum):
    """Expected response format from LLM."""

    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass(frozen=True)
class LLMResponse:
    """Response from an LLM call.

    Attributes:
        content: The response content
        model: Model used for generation
        tokens_used: Number of tokens consumed
        finish_reason: Reason for completion
        raw_response: Raw response from the API
        metadata: Additional response metadata
    """

    content: str
    model: str
    tokens_used: int
    finish_reason: str = "stop"
    raw_response: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        """Check if response completed normally."""
        return self.finish_reason in ("stop", "end_turn")

    @property
    def is_truncated(self) -> bool:
        """Check if response was truncated."""
        return self.finish_reason in ("length", "max_tokens")


class LLMProvider(ABC):
    """Abstract interface for LLM provider implementations.

    Implementations should handle API calls to language models for
    AST generation, specification processing, and verification reasoning.
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the name of the model being used.

        Returns:
            Model name string
        """
        ...

    @property
    @abstractmethod
    def max_tokens(self) -> int:
        """Get the maximum tokens for generation.

        Returns:
            Maximum token limit
        """
        ...

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int | None = None,
        response_format: ResponseFormat = ResponseFormat.TEXT,
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            response_format: Expected response format

        Returns:
            LLMResponse containing the generated content
        """
        ...

    @abstractmethod
    async def generate_with_context(
        self,
        prompt: str,
        context: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate a response with conversation context.

        Args:
            prompt: The current user prompt
            context: List of previous messages [{"role": "user/assistant", "content": "..."}]
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse containing the generated content
        """
        ...

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        schema: dict[str, Any] | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """Generate a JSON response from the LLM.

        Args:
            prompt: The user prompt
            schema: Optional JSON schema for validation
            system_prompt: Optional system prompt
            temperature: Sampling temperature

        Returns:
            Parsed JSON dictionary

        Raises:
            ValueError: If the response is not valid JSON
        """
        ...

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text.

        Args:
            text: The text to count tokens for

        Returns:
            Number of tokens
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the LLM provider is healthy and accessible.

        Returns:
            True if healthy, False otherwise
        """
        ...
