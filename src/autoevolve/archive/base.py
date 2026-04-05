"""Base archive abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod

from autoevolve.models import Candidate


class Archive(ABC):
    """Base class for candidate archives.

    The archive stores every evaluated candidate and provides retrieval
    methods for feeding exemplars back into future mutation prompts.
    """

    @abstractmethod
    def add(self, candidate: Candidate) -> None:
        """Add a candidate to the archive."""

    @abstractmethod
    def get_top_k(self, k: int) -> list[Candidate]:
        """Return the k highest-scoring candidates."""

    @abstractmethod
    def get_recent_k(self, k: int) -> list[Candidate]:
        """Return the k most recently created candidates."""

    @abstractmethod
    def get_diverse_k(self, k: int) -> list[Candidate]:
        """Return k candidates selected for diversity."""

    @abstractmethod
    def get_all(self) -> list[Candidate]:
        """Return all candidates in the archive."""

    @abstractmethod
    def size(self) -> int:
        """Return the number of candidates in the archive."""
