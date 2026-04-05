"""Base strategy abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod

from autoevolve.engine.run_context import RunContext
from autoevolve.models import Candidate


class Strategy(ABC):
    """Base class for search strategies."""

    @abstractmethod
    def run_generation(
        self,
        generation: int,
        parents: list[Candidate],
        ctx: RunContext,
    ) -> list[Candidate]:
        """Run one generation of the search.

        Args:
            generation: Current generation number.
            parents: Parent candidates (survivors from previous generation).
            ctx: Run context with archive, config, reporters, etc.

        Returns:
            List of evaluated candidates from this generation.
        """

    def select_survivors(
        self,
        candidates: list[Candidate],
        ctx: RunContext,
    ) -> list[Candidate]:
        """Select survivors for the next generation.

        Default implementation uses beam selection.

        Args:
            candidates: Evaluated candidates.
            ctx: Run context.

        Returns:
            Survivors that will become parents of the next generation.
        """
        from autoevolve.engine.selection import select_survivors
        return select_survivors(candidates, ctx.task_config.strategy.beam_width)


def create_strategy(strategy_type: str) -> Strategy:
    """Factory function to create a strategy by type.

    Args:
        strategy_type: One of 'beam', 'beam_archive', 'swarm'.

    Returns:
        A Strategy instance.
    """
    if strategy_type == "beam":
        from autoevolve.strategies.beam import BeamStrategy
        return BeamStrategy()
    elif strategy_type == "beam_archive":
        from autoevolve.strategies.beam_archive import BeamArchiveStrategy
        return BeamArchiveStrategy()
    elif strategy_type == "swarm":
        from autoevolve.strategies.swarm import SwarmStrategy
        return SwarmStrategy()
    else:
        raise ValueError(
            f"Unknown strategy '{strategy_type}'. "
            f"Available: beam, beam_archive, swarm"
        )
