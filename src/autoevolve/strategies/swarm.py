"""Swarm strategy — delegates to the swarm orchestrator."""

from __future__ import annotations

import asyncio

from autoevolve.engine.run_context import RunContext
from autoevolve.evaluation.runner import EvaluationRunner
from autoevolve.models import Candidate
from autoevolve.strategies.base import Strategy
from autoevolve.swarm.orchestrator import SwarmOrchestrator


class SwarmStrategy(Strategy):
    """Advanced strategy using multiple specialized agents concurrently.

    The swarm orchestrator handles:
    - Multiple mutation agents with different specializations
    - Optional critic screening
    - Optional crossover
    - Optional diversity injection

    This strategy wraps the async swarm orchestrator in asyncio.run()
    to keep the engine loop synchronous.
    """

    def run_generation(
        self,
        generation: int,
        parents: list[Candidate],
        ctx: RunContext,
    ) -> list[Candidate]:
        """Run one swarm generation."""
        orchestrator = SwarmOrchestrator(ctx)

        # Run async swarm in a fresh event loop
        candidates = asyncio.run(
            orchestrator.run_generation(generation, parents)
        )

        # Evaluate all candidates
        runner = EvaluationRunner(ctx.task_config)
        gen_dir = ctx.generation_dir(generation)

        if ctx.task_config.output.save_all_candidates:
            runner.evaluate_candidates(candidates, output_dir=gen_dir)
        else:
            runner.evaluate_candidates(candidates)

        return candidates
