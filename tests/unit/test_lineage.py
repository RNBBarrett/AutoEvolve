"""Unit tests for autoevolve.lineage — LineageTracker."""

from __future__ import annotations

import pytest

from autoevolve.lineage import LineageTracker
from autoevolve.models import Candidate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_candidate(
    cid: str,
    parent_ids: list[str] | None = None,
    generation: int = 0,
) -> Candidate:
    """Create a minimal Candidate for lineage testing."""
    return Candidate(
        id=cid,
        generation=generation,
        parent_ids=parent_ids or [],
        content=f"content-{cid}",
        mutation_mode="rewrite",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLineageRecord:
    """Tests for LineageTracker.record."""

    def test_record_adds_candidate(self) -> None:
        """After recording a candidate, its parents should be retrievable."""
        tracker = LineageTracker()
        child = _make_candidate("c1", parent_ids=["p1"])

        tracker.record(child)

        assert tracker.get_parents("c1") == ["p1"]

    def test_record_updates_children_index(self) -> None:
        """After recording a child, the parent should list it as a child."""
        tracker = LineageTracker()
        child = _make_candidate("c1", parent_ids=["p1"])

        tracker.record(child)

        assert "c1" in tracker.get_children("p1")

    def test_record_multiple_parents(self) -> None:
        """A candidate with two parents (crossover) should record both."""
        tracker = LineageTracker()
        child = _make_candidate("cross1", parent_ids=["p1", "p2"])

        tracker.record(child)

        assert tracker.get_parents("cross1") == ["p1", "p2"]
        assert "cross1" in tracker.get_children("p1")
        assert "cross1" in tracker.get_children("p2")


class TestLineageAncestors:
    """Tests for LineageTracker.get_ancestors."""

    def test_get_ancestors_returns_correct_chain(self) -> None:
        """get_ancestors should return the full ancestor chain (breadth-first)."""
        tracker = LineageTracker()

        # Build a chain: grandparent -> parent -> child
        grandparent = _make_candidate("g", generation=0)
        parent = _make_candidate("p", parent_ids=["g"], generation=1)
        child = _make_candidate("c", parent_ids=["p"], generation=2)

        tracker.record(grandparent)
        tracker.record(parent)
        tracker.record(child)

        ancestors = tracker.get_ancestors("c")

        assert "p" in ancestors
        assert "g" in ancestors
        # Parent should come before grandparent (BFS order)
        assert ancestors.index("p") < ancestors.index("g")

    def test_get_ancestors_of_root_is_empty(self) -> None:
        """A candidate with no parents (baseline) should have an empty ancestor list."""
        tracker = LineageTracker()
        root = _make_candidate("root")

        tracker.record(root)

        assert tracker.get_ancestors("root") == []

    def test_get_ancestors_diamond(self) -> None:
        """Ancestors in a diamond graph should not contain duplicates."""
        tracker = LineageTracker()

        # Diamond: root -> a, root -> b, a+b -> leaf
        root = _make_candidate("root")
        a = _make_candidate("a", parent_ids=["root"], generation=1)
        b = _make_candidate("b", parent_ids=["root"], generation=1)
        leaf = _make_candidate("leaf", parent_ids=["a", "b"], generation=2)

        tracker.record(root)
        tracker.record(a)
        tracker.record(b)
        tracker.record(leaf)

        ancestors = tracker.get_ancestors("leaf")

        # Should contain a, b, root (each exactly once)
        assert sorted(ancestors) == ["a", "b", "root"]
        assert len(ancestors) == len(set(ancestors))  # no duplicates


class TestLineageDescendants:
    """Tests for LineageTracker.get_descendants."""

    def test_get_descendants_returns_correct_set(self) -> None:
        """get_descendants should return all descendants (breadth-first)."""
        tracker = LineageTracker()

        root = _make_candidate("root")
        child_a = _make_candidate("a", parent_ids=["root"], generation=1)
        child_b = _make_candidate("b", parent_ids=["root"], generation=1)
        grandchild = _make_candidate("gc", parent_ids=["a"], generation=2)

        tracker.record(root)
        tracker.record(child_a)
        tracker.record(child_b)
        tracker.record(grandchild)

        descendants = tracker.get_descendants("root")

        assert "a" in descendants
        assert "b" in descendants
        assert "gc" in descendants
        assert "root" not in descendants

    def test_get_descendants_of_leaf_is_empty(self) -> None:
        """A candidate with no children should have an empty descendant list."""
        tracker = LineageTracker()
        leaf = _make_candidate("leaf", parent_ids=["p1"])

        tracker.record(leaf)

        assert tracker.get_descendants("leaf") == []


class TestLineageFromCandidates:
    """Tests for LineageTracker.from_candidates."""

    def test_from_candidates_reconstructs_tracker(self) -> None:
        """from_candidates should rebuild the lineage graph from a list."""
        candidates = [
            _make_candidate("root", generation=0),
            _make_candidate("c1", parent_ids=["root"], generation=1),
            _make_candidate("c2", parent_ids=["root"], generation=1),
            _make_candidate("c3", parent_ids=["c1"], generation=2),
        ]

        tracker = LineageTracker.from_candidates(candidates)

        assert tracker.get_parents("c1") == ["root"]
        assert tracker.get_parents("c2") == ["root"]
        assert tracker.get_parents("c3") == ["c1"]
        assert set(tracker.get_children("root")) == {"c1", "c2"}
        assert tracker.get_children("c1") == ["c3"]

    def test_from_candidates_empty_list(self) -> None:
        """from_candidates with an empty list should produce an empty tracker."""
        tracker = LineageTracker.from_candidates([])

        assert tracker.get_parents("anything") == []
        assert tracker.get_children("anything") == []


class TestLineageBaselineCandidate:
    """Tests for candidates with no parents (baseline / generation-0)."""

    def test_baseline_has_empty_parent_list(self) -> None:
        """A baseline candidate recorded with no parent_ids should have empty parents."""
        tracker = LineageTracker()
        baseline = _make_candidate("base")

        tracker.record(baseline)

        assert tracker.get_parents("base") == []

    def test_baseline_can_have_children(self) -> None:
        """A baseline candidate can still be a parent to other candidates."""
        tracker = LineageTracker()
        baseline = _make_candidate("base")
        child = _make_candidate("child", parent_ids=["base"], generation=1)

        tracker.record(baseline)
        tracker.record(child)

        assert tracker.get_children("base") == ["child"]
        assert tracker.get_ancestors("child") == ["base"]
