"""In-memory archive implementation."""

from __future__ import annotations

from autoevolve.archive.base import Archive
from autoevolve.archive.selectors import select_diverse_k, select_recent_k, select_top_k
from autoevolve.models import Candidate


class InMemoryArchive(Archive):
    """Stores candidates in memory with retrieval by top/recent/diverse."""

    def __init__(self) -> None:
        self._candidates: list[Candidate] = []

    def add(self, candidate: Candidate) -> None:
        """Add a candidate to the archive."""
        self._candidates.append(candidate)

    def get_top_k(self, k: int) -> list[Candidate]:
        """Return the k highest-scoring candidates."""
        return select_top_k(self._candidates, k)

    def get_recent_k(self, k: int) -> list[Candidate]:
        """Return the k most recently created candidates."""
        return select_recent_k(self._candidates, k)

    def get_diverse_k(self, k: int) -> list[Candidate]:
        """Return k candidates selected for diversity."""
        return select_diverse_k(self._candidates, k)

    def get_all(self) -> list[Candidate]:
        """Return all candidates in the archive."""
        return list(self._candidates)

    def size(self) -> int:
        """Return the number of candidates in the archive."""
        return len(self._candidates)
