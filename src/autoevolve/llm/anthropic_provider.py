"""Anthropic Claude provider."""

from __future__ import annotations

import os
from typing import Any

from autoevolve.errors import ProviderError
from autoevolve.llm.base import Provider


class AnthropicProvider(Provider):
    """LLM provider using the Anthropic API."""

    def __init__(self, model: str = "claude-sonnet-4-20250514", temperature: float = 0.2) -> None:
        self.model = model
        self.temperature = temperature
        self._api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not self._api_key:
            raise ProviderError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Set it to use the Anthropic provider."
            )

    def generate(self, prompt: str, *, metadata: dict[str, Any] | None = None) -> str:
        """Generate a response using the Anthropic API."""
        try:
            import anthropic
        except ImportError:
            raise ProviderError(
                "The 'anthropic' package is not installed. "
                "Install it with: pip install autoevolve[anthropic]"
            )

        client = anthropic.Anthropic(api_key=self._api_key)
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            raise ProviderError(f"Anthropic API call failed: {e}")

    async def agenerate(self, prompt: str, *, metadata: dict[str, Any] | None = None) -> str:
        """Async generation using the Anthropic async client."""
        try:
            import anthropic
        except ImportError:
            raise ProviderError(
                "The 'anthropic' package is not installed. "
                "Install it with: pip install autoevolve[anthropic]"
            )

        client = anthropic.AsyncAnthropic(api_key=self._api_key)
        try:
            response = await client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            raise ProviderError(f"Anthropic API call failed: {e}")
