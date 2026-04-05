"""Beam search strategy."""

from __future__ import annotations

from autoevolve.engine.generation import generate_candidates
from autoevolve.engine.run_context import RunContext
from autoevolve.engine.selection import select_parents_for_crossover
from autoevolve.evaluation.runner import EvaluationRunner
from autoevolve.models import Candidate
from autoevolve.mutators.base import create_mutator
from autoevolve.mutators.crossover import CrossoverMutator
from autoevolve.mutators.base import MutationContext
from autoevolve.strategies.base import Strategy
from autoevolve.utils.hashing import candidate_id


class BeamStrategy(Strategy):
    """Simple beam-search strategy.

    Each generation:
    1. Generate children_per_parent children for each parent
    2. Optionally attempt crossover on top parents
    3. Evaluate all candidates
    4. Select top beam_width as survivors
    """

    def run_generation(
        self,
        generation: int,
        parents: list[Candidate],
        ctx: RunContext,
    ) -> list[Candidate]:
        """Run one generation of beam search."""
        mutator = create_mutator(ctx.task_config.mutator.mode)

        # Generate children
        children = generate_candidates(parents, mutator, generation, ctx)

        # Optional crossover
        if ctx.task_config.strategy.crossover_enabled and len(parents) >= 2:
            crossover_children = self._do_crossover(parents, generation, len(children), ctx)
            children.extend(crossover_children)

        # Evaluate
        runner = EvaluationRunner(ctx.task_config)
        gen_dir = ctx.generation_dir(generation)

        if ctx.task_config.output.save_all_candidates:
            runner.evaluate_candidates(children, output_dir=gen_dir)
        else:
            runner.evaluate_candidates(children)

        return children

    def _do_crossover(
        self,
        parents: list[Candidate],
        generation: int,
        start_index: int,
        ctx: RunContext,
    ) -> list[Candidate]:
        """Attempt crossover on top parent pairs."""
        from autoevolve.llm.base import create_provider
        from autoevolve.utils.files import read_text

        pairs = select_parents_for_crossover(parents, count=1)
        if not pairs:
            return []

        provider = create_provider(ctx.task_config.mutator.provider, ctx.task_config.mutator)
        goal = read_text(ctx.task_config.task_dir / ctx.task_config.goal_path)

        crossover = CrossoverMutator()
        crossover_children = []

        for i, (parent_a, parent_b) in enumerate(pairs):
            context = MutationContext(
                goal=goal,
                artifact_type=ctx.task_config.artifact_type,
                provider=provider,
            )
            try:
                child = crossover.mutate_pair(parent_a, parent_b, context=context)
                child.id = candidate_id(generation, start_index + i)
                child.generation = generation
                crossover_children.append(child)
            except Exception as e:
                ctx.emit_event("crossover_failed", {"error": str(e)})

        return crossover_children
