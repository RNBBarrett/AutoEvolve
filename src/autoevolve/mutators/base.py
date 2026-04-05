"""Base mutator abstraction and mutation context."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from autoevolve.llm.base import Provider
from autoevolve.models import Candidate


@dataclass
class MutationContext:
    """Context passed to mutators for generating candidates."""

    goal: str
    artifact_type: str
    provider: Provider
    archive_exemplars: list[Candidate] = field(default_factory=list)
    best_candidate: Candidate | None = None
    score_summary: str | None = None
    specialization: str | None = None


class Mutator(ABC):
    """Base class for mutation operators."""

    mutation_mode: str

    @abstractmethod
    def mutate(self, parent: Candidate, *, context: MutationContext) -> Candidate:
        """Generate a new candidate from a parent.

        Args:
            parent: The parent candidate to mutate.
            context: Mutation context with goal, provider, archive info.

        Returns:
            A new Candidate with the mutated content.
        """

    async def amutate(self, parent: Candidate, *, context: MutationContext) -> Candidate:
        """Async version of mutate. Default runs sync in executor."""
        import asyncio
        from functools import partial
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, partial(self.mutate, parent, context=context)
        )


def create_mutator(mode: str) -> Mutator:
    """Factory function to create a mutator by mode name.

    Args:
        mode: One of 'rewrite', 'patch', 'nl_feedback', 'crossover'.

    Returns:
        A Mutator instance.
    """
    if mode == "rewrite":
        from autoevolve.mutators.rewrite import RewriteMutator
        return RewriteMutator()
    elif mode == "patch":
        from autoevolve.mutators.patch import PatchMutator
        return PatchMutator()
    elif mode == "nl_feedback":
        from autoevolve.mutators.nl_feedback import NLFeedbackMutator
        return NLFeedbackMutator()
    elif mode == "crossover":
        from autoevolve.mutators.crossover import CrossoverMutator
        return CrossoverMutator()
    else:
        raise ValueError(
            f"Unknown mutation mode '{mode}'. "
            f"Available: rewrite, patch, nl_feedback, crossover"
        )
