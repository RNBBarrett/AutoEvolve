"""Unit tests for autoevolve.engine.selection — beam-search survivor selection."""

from __future__ import annotations

import pytest

from autoevolve.engine.selection import select_survivors
from autoevolve.models import Candidate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_candidate(cid: str, score: float | None = None) -> Candidate:
    """Create a minimal Candidate with the given id and score."""
    return Candidate(
        id=cid,
        generation=0,
        parent_ids=[],
        content=f"content-{cid}",
        mutation_mode="rewrite",
        score=score,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSelectSurvivors:
    """Tests for ``select_survivors``."""

    def test_returns_top_by_score(self) -> None:
        """Should return the beam_width highest-scoring candidates."""
        candidates = [
            _make_candidate("a", score=0.2),
            _make_candidate("b", score=0.9),
            _make_candidate("c", score=0.5),
            _make_candidate("d", score=0.7),
        ]
        survivors = select_survivors(candidates, beam_width=2)

        assert len(survivors) == 2
        assert survivors[0].id == "b"
        assert survivors[1].id == "d"

    def test_survivors_marked_selected(self) -> None:
        """Selected survivors should have status set to 'selected'."""
        candidates = [_make_candidate("a", score=1.0)]
        survivors = select_survivors(candidates, beam_width=1)

        assert survivors[0].status == "selected"

    def test_none_scores_treated_as_negative_infinity(self) -> None:
        """Candidates with None scores should rank below all scored candidates."""
        candidates = [
            _make_candidate("a", score=None),
            _make_candidate("b", score=0.1),
            _make_candidate("c", score=None),
        ]
        survivors = select_survivors(candidates, beam_width=2)

        # "b" should be first because it has a real score.
        assert survivors[0].id == "b"
        # The second should be one of the None-scored candidates.
        assert survivors[1].score is None

    def test_empty_candidate_list(self) -> None:
        """An empty candidate list should return an empty list."""
        assert select_survivors([], beam_width=5) == []

    def test_beam_width_larger_than_count(self) -> None:
        """When beam_width > len(candidates), all candidates are returned."""
        candidates = [
            _make_candidate("a", score=0.8),
            _make_candidate("b", score=0.3),
        ]
        survivors = select_survivors(candidates, beam_width=10)

        assert len(survivors) == 2
        # All should be marked selected.
        assert all(s.status == "selected" for s in survivors)

    def test_deterministic_tiebreaker(self) -> None:
        """When scores are identical, selection should be deterministic (by id)."""
        candidates = [
            _make_candidate("z", score=0.5),
            _make_candidate("a", score=0.5),
            _make_candidate("m", score=0.5),
        ]

        survivors_1 = select_survivors(list(candidates), beam_width=2)
        survivors_2 = select_survivors(list(candidates), beam_width=2)

        # Same input should always produce the same order.
        assert [s.id for s in survivors_1] == [s.id for s in survivors_2]
