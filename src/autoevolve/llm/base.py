"""Base LLM provider abstraction."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from functools import partial
from typing import Any

from autoevolve.errors import ProviderError
from autoevolve.models import MutatorConfig


class Provider(ABC):
    """Base class for LLM providers.

    All providers must implement the synchronous generate() method.
    The async agenerate() method has a default implementation that runs
    generate() in a thread executor.
    """

    @abstractmethod
    def generate(self, prompt: str, *, metadata: dict[str, Any] | None = None) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: The complete prompt string.
            metadata: Optional metadata (model, temperature, etc.).

        Returns:
            The model's response text.
        """

    async def agenerate(self, prompt: str, *, metadata: dict[str, Any] | None = None) -> str:
        """Async version of generate. Default runs sync in executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, partial(self.generate, prompt, metadata=metadata)
        )


def create_provider(name: str, config: MutatorConfig) -> Provider:
    """Factory function to create a provider by name.

    Args:
        name: Provider name ('mock', 'anthropic', 'openai', 'ollama', 'external_command').
        config: Mutator configuration with model, temperature, etc.

    Returns:
        A Provider instance.

    Raises:
        ProviderError: If the provider name is not recognized.
    """
    if name == "mock":
        from autoevolve.llm.mock_provider import MockProvider
        return MockProvider(model=config.model)
    elif name == "anthropic":
        from autoevolve.llm.anthropic_provider import AnthropicProvider
        return AnthropicProvider(model=config.model, temperature=config.temperature)
    elif name == "openai":
        from autoevolve.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(model=config.model, temperature=config.temperature)
    elif name == "ollama":
        from autoevolve.llm.ollama_provider import OllamaProvider
        return OllamaProvider(model=config.model, temperature=config.temperature)
    elif name == "external_command":
        from autoevolve.llm.external_command_provider import ExternalCommandProvider
        return ExternalCommandProvider(
            command=config.external_command or "",
            mode=config.external_command_mode,
        )
    else:
        raise ProviderError(
            f"Unknown provider '{name}'. "
            f"Available: mock, anthropic, openai, ollama, external_command"
        )
