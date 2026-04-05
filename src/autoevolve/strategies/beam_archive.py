"""Beam search with archive exemplar feedback."""

from __future__ import annotations

from autoevolve.engine.run_context import RunContext
from autoevolve.models import Candidate
from autoevolve.strategies.beam import BeamStrategy


class BeamArchiveStrategy(BeamStrategy):
    """Beam search that includes archive exemplars in mutation prompts.

    Inherits from BeamStrategy. The archive exemplars are automatically
    included in prompts via the generate_candidates function, which reads
    from the RunContext's archive.

    This is the key default strategy — it brings in the exemplar-feedback
    behavior inspired by FunSearch-like storage of strong programs.
    """

    def run_generation(
        self,
        generation: int,
        parents: list[Candidate],
        ctx: RunContext,
    ) -> list[Candidate]:
        """Run one generation with archive-augmented prompts.

        The only difference from BeamStrategy is that this strategy
        explicitly uses the archive. Since generate_candidates already
        pulls from the archive when it's populated, the behavior
        difference emerges naturally as the archive fills up.
        """
        return super().run_generation(generation, parents, ctx)
