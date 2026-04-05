"""Unit tests for autoevolve.prompt_builder — mutation/crossover prompt formatting."""

from __future__ import annotations

import pytest

from autoevolve.models import Candidate
from autoevolve.prompt_builder import (
    ARTIFACT_END,
    ARTIFACT_START,
    build_crossover_prompt,
    build_mutation_prompt,
    parse_hypothesis_and_content,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_candidate(
    cid: str,
    score: float | None = None,
    content: str = "",
) -> Candidate:
    """Create a minimal Candidate with the given id, score, and content."""
    return Candidate(
        id=cid,
        generation=0,
        parent_ids=[],
        content=content or f"content-{cid}",
        mutation_mode="rewrite",
        score=score,
    )


# ---------------------------------------------------------------------------
# build_mutation_prompt
# ---------------------------------------------------------------------------


class TestBuildMutationPrompt:
    """Tests for ``build_mutation_prompt``."""

    def test_python_code_includes_delimiters(self) -> None:
        """The prompt for python_code must include ARTIFACT_START and ARTIFACT_END."""
        prompt = build_mutation_prompt(
            mode="rewrite",
            artifact_content="print('hello')",
            goal="Improve the code.",
            artifact_type="python_code",
        )

        assert ARTIFACT_START in prompt
        assert ARTIFACT_END in prompt
        assert "print('hello')" in prompt

    def test_python_code_output_discipline(self) -> None:
        """Python-code prompts should instruct returning only valid Python."""
        prompt = build_mutation_prompt(
            mode="rewrite",
            artifact_content="x = 1",
            goal="Optimize.",
            artifact_type="python_code",
        )

        assert "Python" in prompt
        assert "Do NOT include markdown fences" in prompt

    def test_prompt_text_output_discipline(self) -> None:
        """Prompt-text prompts should instruct returning only raw prompt text."""
        prompt = build_mutation_prompt(
            mode="rewrite",
            artifact_content="Summarize the article.",
            goal="Improve clarity.",
            artifact_type="prompt_text",
        )

        assert "prompt text" in prompt.lower()
        assert "Do NOT include markdown fences" in prompt

    def test_goal_included(self) -> None:
        """The goal text must appear in the generated prompt."""
        prompt = build_mutation_prompt(
            mode="rewrite",
            artifact_content="body",
            goal="Maximize recall.",
            artifact_type="python_code",
        )

        assert "Maximize recall." in prompt

    def test_artifact_content_between_delimiters(self) -> None:
        """The artifact content should appear between the start and end delimiters."""
        artifact = "def solve(x): return x * 2"
        prompt = build_mutation_prompt(
            mode="rewrite",
            artifact_content=artifact,
            goal="Goal.",
            artifact_type="python_code",
        )

        start_idx = prompt.index(ARTIFACT_START)
        end_idx = prompt.index(ARTIFACT_END)
        between = prompt[start_idx:end_idx]
        assert artifact in between


# ---------------------------------------------------------------------------
# build_crossover_prompt
# ---------------------------------------------------------------------------


class TestBuildCrossoverPrompt:
    """Tests for ``build_crossover_prompt``."""

    def test_includes_both_parents(self) -> None:
        """The crossover prompt must include content from both parents."""
        parent_a = _make_candidate("a", score=0.9, content="alpha approach")
        parent_b = _make_candidate("b", score=0.7, content="beta approach")

        prompt = build_crossover_prompt(
            parent_a=parent_a,
            parent_b=parent_b,
            goal="Combine strengths.",
            artifact_type="python_code",
        )

        assert "alpha approach" in prompt
        assert "beta approach" in prompt

    def test_includes_parent_scores(self) -> None:
        """The crossover prompt should mention both parent scores for context."""
        parent_a = _make_candidate("a", score=0.9, content="alpha")
        parent_b = _make_candidate("b", score=0.7, content="beta")

        prompt = build_crossover_prompt(
            parent_a=parent_a,
            parent_b=parent_b,
            goal="Goal.",
            artifact_type="python_code",
        )

        assert "0.9" in prompt
        assert "0.7" in prompt

    def test_includes_artifact_delimiters(self) -> None:
        """Parent A content should be wrapped in ARTIFACT_START / ARTIFACT_END."""
        parent_a = _make_candidate("a", score=0.9, content="alpha")
        parent_b = _make_candidate("b", score=0.7, content="beta")

        prompt = build_crossover_prompt(
            parent_a=parent_a,
            parent_b=parent_b,
            goal="Goal.",
            artifact_type="python_code",
        )

        assert ARTIFACT_START in prompt
        assert ARTIFACT_END in prompt


# ---------------------------------------------------------------------------
# parse_hypothesis_and_content
# ---------------------------------------------------------------------------


class TestParseHypothesisAndContent:
    """Tests for ``parse_hypothesis_and_content``."""

    def test_extracts_hypothesis(self) -> None:
        """A response starting with HYPOTHESIS: should be split correctly."""
        raw = "HYPOTHESIS: Adding caching will speed up the loop.\ndef solve(x):\n    return x"
        hypothesis, content = parse_hypothesis_and_content(raw)

        assert hypothesis == "Adding caching will speed up the loop."
        assert content.startswith("def solve(x):")

    def test_case_insensitive_prefix(self) -> None:
        """The HYPOTHESIS: prefix should be detected regardless of case."""
        raw = "hypothesis: lowercase hypothesis\nresult body"
        hypothesis, content = parse_hypothesis_and_content(raw)

        assert hypothesis == "lowercase hypothesis"
        assert content == "result body"

    def test_no_hypothesis(self) -> None:
        """When no HYPOTHESIS: prefix is present, hypothesis should be None."""
        raw = "def solve(x):\n    return x * 2"
        hypothesis, content = parse_hypothesis_and_content(raw)

        assert hypothesis is None
        assert content == raw.strip()

    def test_empty_string(self) -> None:
        """An empty string should return None hypothesis and empty content."""
        hypothesis, content = parse_hypothesis_and_content("")

        assert hypothesis is None
        assert content == ""

    def test_hypothesis_only_no_body(self) -> None:
        """A response with only a HYPOTHESIS: line and no body should return empty content."""
        raw = "HYPOTHESIS: Just a hypothesis, nothing else"
        hypothesis, content = parse_hypothesis_and_content(raw)

        assert hypothesis == "Just a hypothesis, nothing else"
        assert content == ""
