"""Base LLM provider with common functionality.

This module provides a base class for LLM provider implementations
with retry logic, rate limiting, and common utilities.
"""

from __future__ import annotations

import asyncio
from abc import abstractmethod
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.core.interfaces.llm_provider import LLMProvider, LLMResponse, ResponseFormat
from src.shared.logger import LoggerMixin


class BaseLLMProvider(LLMProvider, LoggerMixin):
    """Base class for LLM provider implementations.

    Provides common functionality like retry logic and rate limiting.
    """

    def __init__(
        self,
        model_name: str,
        max_tokens: int = 8192,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize the base provider.

        Args:
            model_name: Name of the model
            max_tokens: Maximum tokens for generation
            max_retries: Maximum retry attempts
            retry_delay: Base delay between retries
        """
        self._model_name = model_name
        self._max_tokens = max_tokens
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._request_count = 0
        self._token_count = 0

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name

    @property
    def max_tokens(self) -> int:
        """Get the maximum tokens."""
        return self._max_tokens

    @abstractmethod
    async def _generate_impl(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int | None = None,
        response_format: ResponseFormat = ResponseFormat.TEXT,
    ) -> LLMResponse:
        """Implementation-specific generation logic.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            response_format: Expected response format

        Returns:
            LLMResponse
        """
        ...

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int | None = None,
        response_format: ResponseFormat = ResponseFormat.TEXT,
    ) -> LLMResponse:
        """Generate a response with retry logic.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            response_format: Expected response format

        Returns:
            LLMResponse
        """
        max_tokens = max_tokens or self._max_tokens

        for attempt in range(self._max_retries):
            try:
                self._request_count += 1
                response = await self._generate_impl(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                )
                self._token_count += response.tokens_used

                self.logger.debug(
                    "llm_request_complete",
                    model=self._model_name,
                    tokens=response.tokens_used,
                    attempt=attempt + 1,
                )

                return response

            except Exception as e:
                self.logger.warning(
                    "llm_request_failed",
                    attempt=attempt + 1,
                    error=str(e),
                )

                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (2**attempt)
                    await asyncio.sleep(delay)
                else:
                    raise

        # Should not reach here, but satisfy type checker
        raise RuntimeError("Max retries exceeded")

    async def generate_with_context(
        self,
        prompt: str,
        context: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate with conversation context.

        Default implementation concatenates context into prompt.
        Subclasses may override for native context support.

        Args:
            prompt: Current user prompt
            context: Previous messages
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            LLMResponse
        """
        # Build context into prompt
        context_parts = []
        for msg in context:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            context_parts.append(f"{role.title()}: {content}")

        full_prompt = "\n".join(context_parts) + f"\n\nUser: {prompt}"

        return await self.generate(
            prompt=full_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def generate_json(
        self,
        prompt: str,
        schema: dict[str, Any] | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """Generate JSON response.

        Args:
            prompt: The user prompt
            schema: Optional JSON schema
            system_prompt: Optional system prompt
            temperature: Sampling temperature

        Returns:
            Parsed JSON dictionary

        Raises:
            ValueError: If response is not valid JSON
        """
        import json

        # Add JSON instruction to prompt
        json_prompt = prompt + "\n\nRespond with ONLY valid JSON, no explanations."

        if schema:
            json_prompt += f"\n\nExpected schema: {json.dumps(schema)}"

        response = await self.generate(
            prompt=json_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            response_format=ResponseFormat.JSON,
        )

        # Parse JSON from response
        from src.shared.utils.json_utils import extract_json_from_text

        json_objects = extract_json_from_text(response.content)

        if not json_objects:
            raise ValueError(f"No valid JSON found in response: {response.content[:200]}")

        return json_objects[0]

    async def count_tokens(self, text: str) -> int:
        """Estimate token count.

        Default implementation uses character-based estimate.
        Subclasses may override for accurate counting.

        Args:
            text: Text to count

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4

    async def health_check(self) -> bool:
        """Check provider health.

        Args:
            None

        Returns:
            True if healthy
        """
        try:
            response = await self.generate(
                prompt="Say 'OK'",
                max_tokens=10,
            )
            return bool(response.content)
        except Exception:
            return False

    def get_statistics(self) -> dict[str, int]:
        """Get usage statistics.

        Returns:
            Dictionary with request and token counts
        """
        return {
            "request_count": self._request_count,
            "token_count": self._token_count,
        }
