"""Unit tests for autoevolve.archive.selectors — top-k, recent-k, diverse-k selection."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from autoevolve.archive.selectors import (
    select_diverse_k,
    select_recent_k,
    select_top_k,
)
from autoevolve.models import Candidate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_candidate(
    cid: str,
    score: float | None = None,
    content: str = "",
    minutes_ago: int = 0,
) -> Candidate:
    """Create a Candidate with the given id, score, content, and age."""
    created = (datetime.now() - timedelta(minutes=minutes_ago)).isoformat()
    return Candidate(
        id=cid,
        generation=0,
        parent_ids=[],
        content=content or f"content-{cid}",
        mutation_mode="rewrite",
        score=score,
        created_at=created,
    )


# ---------------------------------------------------------------------------
# select_top_k
# ---------------------------------------------------------------------------


class TestSelectTopK:
    """Tests for ``select_top_k``."""

    def test_returns_highest_scored(self) -> None:
        """Should return the k highest-scoring candidates in descending order."""
        candidates = [
            _make_candidate("a", score=0.3),
            _make_candidate("b", score=0.9),
            _make_candidate("c", score=0.6),
        ]
        result = select_top_k(candidates, 2)

        assert len(result) == 2
        assert result[0].id == "b"
        assert result[1].id == "c"

    def test_handles_ties(self) -> None:
        """When scores tie, all tied candidates should be eligible for selection."""
        candidates = [
            _make_candidate("a", score=0.5),
            _make_candidate("b", score=0.5),
            _make_candidate("c", score=0.5),
        ]
        result = select_top_k(candidates, 2)

        assert len(result) == 2
        # All have the same score, so any two is acceptable.
        returned_ids = {c.id for c in result}
        assert returned_ids.issubset({"a", "b", "c"})

    def test_none_scores_sorted_last(self) -> None:
        """Candidates with None scores should appear after scored candidates."""
        candidates = [
            _make_candidate("a", score=None),
            _make_candidate("b", score=0.1),
        ]
        result = select_top_k(candidates, 2)

        assert result[0].id == "b"
        assert result[1].id == "a"

    def test_empty_list(self) -> None:
        """Selecting from an empty list returns an empty list."""
        assert select_top_k([], 5) == []

    def test_k_zero(self) -> None:
        """k=0 should return an empty list."""
        candidates = [_make_candidate("a", score=1.0)]
        assert select_top_k(candidates, 0) == []

    def test_k_greater_than_length(self) -> None:
        """k > len(candidates) returns all candidates (no error)."""
        candidates = [_make_candidate("a", score=1.0)]
        result = select_top_k(candidates, 10)

        assert len(result) == 1


# ---------------------------------------------------------------------------
# select_recent_k
# ---------------------------------------------------------------------------


class TestSelectRecentK:
    """Tests for ``select_recent_k``."""

    def test_returns_most_recent(self) -> None:
        """Should return the k most recently created candidates."""
        candidates = [
            _make_candidate("old", minutes_ago=60),
            _make_candidate("mid", minutes_ago=30),
            _make_candidate("new", minutes_ago=0),
        ]
        result = select_recent_k(candidates, 2)

        assert len(result) == 2
        assert result[0].id == "new"
        assert result[1].id == "mid"

    def test_empty_list(self) -> None:
        """Selecting from an empty list returns an empty list."""
        assert select_recent_k([], 3) == []

    def test_k_zero(self) -> None:
        """k=0 should return an empty list."""
        candidates = [_make_candidate("a")]
        assert select_recent_k(candidates, 0) == []

    def test_k_greater_than_length(self) -> None:
        """k > len(candidates) returns all candidates."""
        candidates = [_make_candidate("a")]
        result = select_recent_k(candidates, 10)

        assert len(result) == 1


# ---------------------------------------------------------------------------
# select_diverse_k
# ---------------------------------------------------------------------------


class TestSelectDiverseK:
    """Tests for ``select_diverse_k``."""

    def test_returns_diverse_candidates(self) -> None:
        """Diverse selection should not return all-identical content when alternatives exist."""
        candidates = [
            _make_candidate("a", score=0.9, content="alpha bravo charlie"),
            _make_candidate("b", score=0.8, content="alpha bravo charlie"),  # duplicate of a
            _make_candidate("c", score=0.7, content="delta echo foxtrot"),  # very different
        ]
        result = select_diverse_k(candidates, 2)

        # The first pick should be "a" (top score).
        assert result[0].id == "a"
        # The second should prefer "c" (more diverse) over "b" (duplicate).
        assert result[1].id == "c"

    def test_returns_all_when_k_exceeds_length(self) -> None:
        """When k >= len(candidates), all candidates are returned."""
        candidates = [
            _make_candidate("a", score=0.9, content="foo"),
            _make_candidate("b", score=0.5, content="bar"),
        ]
        result = select_diverse_k(candidates, 10)

        assert len(result) == 2

    def test_empty_list(self) -> None:
        """Selecting from an empty list returns an empty list."""
        assert select_diverse_k([], 3) == []

    def test_k_zero(self) -> None:
        """k=0 should return an empty list."""
        candidates = [_make_candidate("a", score=1.0)]
        assert select_diverse_k(candidates, 0) == []

    def test_single_candidate(self) -> None:
        """A single candidate is always returned when k >= 1."""
        candidates = [_make_candidate("a", score=0.5, content="solo")]
        result = select_diverse_k(candidates, 1)

        assert len(result) == 1
        assert result[0].id == "a"
