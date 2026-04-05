"""Live integration test for the OpenAI provider.

Skipped automatically unless the ``OPENAI_API_KEY`` environment variable
is set.  These tests make real API calls and may incur costs.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set — skipping live OpenAI tests",
)


class TestLiveOpenAI:
    """Live tests that hit the real OpenAI API."""

    def test_generate_returns_nonempty_response(self) -> None:
        from autoevolve.llm.openai_provider import OpenAIProvider

        provider = OpenAIProvider(
            model="gpt-4o-mini",
            temperature=0.0,
        )
        response = provider.generate("Say hello in exactly one word.")

        assert isinstance(response, str)
        assert len(response.strip()) > 0, "OpenAI returned an empty response"

    def test_generate_with_longer_prompt(self) -> None:
        from autoevolve.llm.openai_provider import OpenAIProvider

        provider = OpenAIProvider(
            model="gpt-4o-mini",
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
