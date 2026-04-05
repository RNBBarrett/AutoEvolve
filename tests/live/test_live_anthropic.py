"""Live integration test for the Anthropic provider.

Skipped automatically unless the ``ANTHROPIC_API_KEY`` environment variable
is set.  These tests make real API calls and may incur costs.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live Anthropic tests",
)


class TestLiveAnthropic:
    """Live tests that hit the real Anthropic API."""

    def test_generate_returns_nonempty_response(self) -> None:
        from autoevolve.llm.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider(
            model="claude-sonnet-4-20250514",
            temperature=0.0,
        )
        response = provider.generate("Say hello in exactly one word.")

        assert isinstance(response, str)
        assert len(response.strip()) > 0, "Anthropic returned an empty response"

    def test_generate_with_longer_prompt(self) -> None:
        from autoevolve.llm.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider(
            model="claude-sonnet-4-20250514",
            temperature=0.0,
        )
        prompt = (
            "You are a helpful assistant. "
            "What is 2 + 2? Answer with just the number."
        )
        response = provider.generate(prompt)

        assert isinstance(response, str)
        assert len(response.strip()) > 0
        assert "4" in response
