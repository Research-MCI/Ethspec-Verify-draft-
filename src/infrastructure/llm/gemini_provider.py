"""Google Gemini LLM provider implementation.

This module provides the Gemini API integration for text generation.
"""

from __future__ import annotations

from typing import Any

from src.core.interfaces.llm_provider import LLMResponse, ResponseFormat
from src.infrastructure.llm.base_provider import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider.

    Uses the Google Generative AI SDK for text generation.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        max_tokens: int = 8192,
        max_retries: int = 3,
    ) -> None:
        """Initialize the Gemini provider.

        Args:
            api_key: Gemini API key
            model_name: Model name (e.g., 'gemini-2.5-flash', 'gemini-pro')
            max_tokens: Maximum tokens for generation
            max_retries: Maximum retry attempts
        """
        super().__init__(
            model_name=model_name,
            max_tokens=max_tokens,
            max_retries=max_retries,
        )
        self._api_key = api_key
        self._model: Any = None
        self._genai: Any = None

    async def _ensure_client(self) -> None:
        """Ensure the Gemini client is initialized."""
        if self._model is None:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self._api_key)
                self._genai = genai
                self._model = genai.GenerativeModel(self._model_name)
            except ImportError:
                raise ImportError(
                    "google-generativeai package is required. "
                    "Install with: pip install google-generativeai"
                )

    async def _generate_impl(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int | None = None,
        response_format: ResponseFormat = ResponseFormat.TEXT,
    ) -> LLMResponse:
        """Generate response using Gemini API.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            response_format: Expected response format

        Returns:
            LLMResponse
        """
        await self._ensure_client()

        # Build the full prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt

        # Configure generation
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens or self._max_tokens,
        }

        # Add JSON mode hint if requested
        if response_format == ResponseFormat.JSON:
            generation_config["response_mime_type"] = "application/json"

        try:
            response = self._model.generate_content(
                full_prompt,
                generation_config=generation_config,
            )

            # Extract content
            content = response.text

            # Estimate tokens (Gemini doesn't always return usage)
            tokens_used = len(full_prompt) // 4 + len(content) // 4

            return LLMResponse(
                content=content,
                model=self._model_name,
                tokens_used=tokens_used,
                finish_reason=self._map_finish_reason(response),
                raw_response={"text": content},
            )

        except Exception as e:
            self.logger.error("gemini_generation_error", error=str(e))
            raise

    def _map_finish_reason(self, response: Any) -> str:
        """Map Gemini finish reason to standard format.

        Args:
            response: Gemini response object

        Returns:
            Standardized finish reason
        """
        try:
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "finish_reason"):
                    reason = str(candidate.finish_reason)
                    if "STOP" in reason:
                        return "stop"
                    elif "MAX_TOKENS" in reason:
                        return "length"
                    elif "SAFETY" in reason:
                        return "content_filter"
                    return reason.lower()
        except Exception:
            pass
        return "stop"

    async def count_tokens(self, text: str) -> int:
        """Count tokens using Gemini's tokenizer.

        Args:
            text: Text to count

        Returns:
            Token count
        """
        await self._ensure_client()

        try:
            result = self._model.count_tokens(text)
            return result.total_tokens
        except Exception:
            # Fallback to estimate
            return len(text) // 4

    async def health_check(self) -> bool:
        """Check if Gemini API is accessible.

        Returns:
            True if healthy
        """
        try:
            await self._ensure_client()
            response = await self._generate_impl(
                prompt="Respond with OK",
                max_tokens=10,
            )
            return "ok" in response.content.lower()
        except Exception as e:
            self.logger.error("gemini_health_check_failed", error=str(e))
            return False


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing.

    Returns deterministic responses based on prompts.
    """

    def __init__(self) -> None:
        """Initialize mock provider."""
        super().__init__(
            model_name="mock-llm",
            max_tokens=4096,
            max_retries=1,
        )
        self._responses: dict[str, str] = {}

    def set_response(self, prompt_contains: str, response: str) -> None:
        """Set a mock response for a prompt pattern.

        Args:
            prompt_contains: String that prompt should contain
            response: Response to return
        """
        self._responses[prompt_contains] = response

    async def _generate_impl(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int | None = None,
        response_format: ResponseFormat = ResponseFormat.TEXT,
    ) -> LLMResponse:
        """Generate mock response.

        Args:
            prompt: The prompt
            system_prompt: Ignored
            temperature: Ignored
            max_tokens: Ignored
            response_format: Response format

        Returns:
            LLMResponse
        """
        # Check for matching response
        for pattern, response in self._responses.items():
            if pattern in prompt:
                return LLMResponse(
                    content=response,
                    model="mock-llm",
                    tokens_used=len(response) // 4,
                )

        # Default response
        if response_format == ResponseFormat.JSON:
            content = '{"status": "ok"}'
        else:
            content = "Mock response for: " + prompt[:50]

        return LLMResponse(
            content=content,
            model="mock-llm",
            tokens_used=len(content) // 4,
        )

    async def health_check(self) -> bool:
        """Always healthy."""
        return True
