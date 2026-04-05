"""Lineage tracking for candidate parent-child relationships."""

from __future__ import annotations

from autoevolve.models import Candidate


class LineageTracker:
    """Tracks parent-child relationships between candidates."""

    def __init__(self) -> None:
        self._parents: dict[str, list[str]] = {}  # child_id -> [parent_ids]
        self._children: dict[str, list[str]] = {}  # parent_id -> [child_ids]

    def record(self, candidate: Candidate) -> None:
        """Record a candidate's lineage."""
        self._parents[candidate.id] = list(candidate.parent_ids)
        for parent_id in candidate.parent_ids:
            if parent_id not in self._children:
                self._children[parent_id] = []
            self._children[parent_id].append(candidate.id)

    def get_parents(self, candidate_id: str) -> list[str]:
        """Get direct parent IDs of a candidate."""
        return self._parents.get(candidate_id, [])

    def get_children(self, candidate_id: str) -> list[str]:
        """Get direct child IDs of a candidate."""
        return self._children.get(candidate_id, [])

    def get_ancestors(self, candidate_id: str) -> list[str]:
        """Get all ancestor IDs recursively (breadth-first)."""
        visited: set[str] = set()
        queue = list(self.get_parents(candidate_id))
        ancestors = []

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            ancestors.append(current)
            queue.extend(self.get_parents(current))

        return ancestors

    def get_descendants(self, candidate_id: str) -> list[str]:
        """Get all descendant IDs recursively (breadth-first)."""
        visited: set[str] = set()
        queue = list(self.get_children(candidate_id))
        descendants = []

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            descendants.append(current)
            queue.extend(self.get_children(current))

        return descendants

    def to_dict(self) -> dict[str, dict[str, list[str]]]:
        """Serialize lineage data."""
        return {
            "parents": dict(self._parents),
            "children": dict(self._children),
        }

    @classmethod
    def from_dict(cls, data: dict) -> LineageTracker:
        """Reconstruct a LineageTracker from serialized data."""
        tracker = cls()
        tracker._parents = {k: list(v) for k, v in data.get("parents", {}).items()}
        tracker._children = {k: list(v) for k, v in data.get("children", {}).items()}
        return tracker

    @classmethod
    def from_candidates(cls, candidates: list[Candidate]) -> LineageTracker:
        """Build a LineageTracker from a list of candidates."""
        tracker = cls()
        for candidate in candidates:
            tracker.record(candidate)
        return tracker
