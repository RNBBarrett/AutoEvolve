"""Unit tests for autoevolve.llm.mock_provider — MockProvider."""

from __future__ import annotations

import pytest

from autoevolve.llm.mock_provider import MockProvider
from autoevolve.prompt_builder import ARTIFACT_START, ARTIFACT_END


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_prompt(artifact_content: str, code: bool = True) -> str:
    """Build a minimal prompt with artifact delimiters.

    If *code* is True, includes markers that make the mock provider treat
    this as a Python code artifact prompt.
    """
    preamble = "Improve the following Python code artifact." if code else "Improve the following prompt."
    return (
        f"{preamble}\n\n"
        f"{ARTIFACT_START}\n{artifact_content}\n{ARTIFACT_END}"
    )


# ---------------------------------------------------------------------------
# Tests — mock-deterministic mode
# ---------------------------------------------------------------------------


class TestMockDeterministic:
    """Tests for MockProvider in 'mock-deterministic' mode."""

    def test_extracts_artifact_and_returns_modified(self) -> None:
        """The provider should extract the artifact from between delimiters and
        return content that starts with HYPOTHESIS."""
        provider = MockProvider(model="mock-deterministic")
        prompt = _build_prompt("def add(a, b):\n    return a + b")

        result = provider.generate(prompt)

        assert "HYPOTHESIS" in result
        # The original code should be embedded somewhere in the result
        assert "add" in result or "return" in result

    def test_hypothesis_prefix_present(self) -> None:
        """The deterministic response must begin with 'HYPOTHESIS:'."""
        provider = MockProvider(model="mock-deterministic")
        prompt = _build_prompt("x = 1")

        result = provider.generate(prompt)

        assert result.startswith("HYPOTHESIS:")

    def test_successive_calls_produce_different_results(self) -> None:
        """Successive calls should cycle through different transforms, producing
        different output each time (round-robin across 4 transforms)."""
        provider = MockProvider(model="mock-deterministic")
        prompt = _build_prompt("def solve(x):\n    return x * 2")

        results = [provider.generate(prompt) for _ in range(4)]

        # At least two of the four results should be distinct
        unique = set(results)
        assert len(unique) >= 2, f"Expected varied results, got {len(unique)} unique out of 4"

    def test_counter_increments(self) -> None:
        """The internal counter should increment on each generate() call."""
        provider = MockProvider(model="mock-deterministic")
        prompt = _build_prompt("y = 2")

        assert provider._counter == 0
        provider.generate(prompt)
        assert provider._counter == 1
        provider.generate(prompt)
        assert provider._counter == 2

    def test_prompt_text_artifact_transform(self) -> None:
        """For a prompt-text artifact (no code markers), deterministic mode should
        still return a HYPOTHESIS-prefixed transformation."""
        provider = MockProvider(model="mock-deterministic")
        prompt = _build_prompt("Classify this review.", code=False)

        result = provider.generate(prompt)

        assert result.startswith("HYPOTHESIS:")
        # The transformed text should contain something from the original
        assert "Classify" in result or "review" in result or "specific" in result.lower()


# ---------------------------------------------------------------------------
# Tests — mock-malformed mode
# ---------------------------------------------------------------------------


class TestMockMalformed:
    """Tests for MockProvider in 'mock-malformed' mode."""

    def test_returns_malformed_content(self) -> None:
        """mock-malformed should return content that is NOT clean artifact text
        — for example, markdown fences or conversational filler."""
        provider = MockProvider(model="mock-malformed")
        prompt = _build_prompt("def f(): pass")

        result = provider.generate(prompt)

        # The first malformed response (counter=1, index 1) is conversational text.
        # Check that the result is one of the known malformed patterns.
        is_fenced = "```" in result
        is_conversational = "help" in result.lower() or "explain" in result.lower() or "analysis" in result.lower()
        is_empty = result == ""
        assert is_fenced or is_conversational or is_empty, (
            f"Expected malformed output, got: {result!r}"
        )

    def test_malformed_cycles_through_variants(self) -> None:
        """Successive malformed calls should cycle through different malformed outputs."""
        provider = MockProvider(model="mock-malformed")
        prompt = _build_prompt("x = 1")

        results = [provider.generate(prompt) for _ in range(4)]

        unique = set(results)
        assert len(unique) >= 2, f"Expected varied malformed results, got {len(unique)} unique"


# ---------------------------------------------------------------------------
# Tests — mock-noop mode
# ---------------------------------------------------------------------------


class TestMockNoop:
    """Tests for MockProvider in 'mock-noop' mode."""

    def test_returns_artifact_unchanged(self) -> None:
        """mock-noop should return the original artifact content extracted from
        between the delimiters, without modification."""
        provider = MockProvider(model="mock-noop")
        original = "def add(a, b):\n    return a + b"
        prompt = _build_prompt(original)

        result = provider.generate(prompt)

        assert result == original

    def test_noop_is_stable_across_calls(self) -> None:
        """Successive noop calls with the same prompt should always return the
        same content."""
        provider = MockProvider(model="mock-noop")
        original = "Summarize the article."
        prompt = _build_prompt(original, code=False)

        results = [provider.generate(prompt) for _ in range(3)]

        assert all(r == original for r in results)
