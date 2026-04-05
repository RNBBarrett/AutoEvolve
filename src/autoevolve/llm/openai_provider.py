"""OpenAI provider."""

from __future__ import annotations

import os
from typing import Any

from autoevolve.errors import ProviderError
from autoevolve.llm.base import Provider


class OpenAIProvider(Provider):
    """LLM provider using the OpenAI API."""

    def __init__(self, model: str = "gpt-4o", temperature: float = 0.2) -> None:
        self.model = model
        self.temperature = temperature
        self._api_key = os.environ.get("OPENAI_API_KEY", "")
        if not self._api_key:
            raise ProviderError(
                "OPENAI_API_KEY environment variable is not set. "
                "Set it to use the OpenAI provider."
            )

    def generate(self, prompt: str, *, metadata: dict[str, Any] | None = None) -> str:
        """Generate a response using the OpenAI API."""
        try:
            import openai
        except ImportError:
            raise ProviderError(
                "The 'openai' package is not installed. "
                "Install it with: pip install autoevolve[openai]"
            )

        client = openai.OpenAI(api_key=self._api_key)
        try:
            response = client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise ProviderError(f"OpenAI API call failed: {e}")

    async def agenerate(self, prompt: str, *, metadata: dict[str, Any] | None = None) -> str:
        """Async generation using the OpenAI async client."""
        try:
            import openai
        except ImportError:
            raise ProviderError(
                "The 'openai' package is not installed. "
                "Install it with: pip install autoevolve[openai]"
            )

        client = openai.AsyncOpenAI(api_key=self._api_key)
        try:
            response = await client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise ProviderError(f"OpenAI API call failed: {e}")
