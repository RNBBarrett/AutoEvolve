"""Candidate generation orchestration."""

from __future__ import annotations

from autoevolve.engine.run_context import RunContext
from autoevolve.models import Candidate
from autoevolve.mutators.base import MutationContext, Mutator
from autoevolve.prompt_builder import build_score_summary
from autoevolve.utils.hashing import candidate_id


def generate_candidates(
    parents: list[Candidate],
    mutator: Mutator,
    generation: int,
    ctx: RunContext,
) -> list[Candidate]:
    """Generate child candidates from parents using the given mutator.

    Args:
        parents: Parent candidates to mutate.
        mutator: The mutator to use for generation.
        generation: Current generation number.
        ctx: Run context with archive, config, etc.

    Returns:
        List of new (unevaluated) Candidate objects.
    """
    from autoevolve.utils.files import read_text

    goal = read_text(ctx.task_config.task_dir / ctx.task_config.goal_path)

    # Build archive exemplars for the prompt
    archive_exemplars = []
    top_k = ctx.archive.get_top_k(ctx.task_config.strategy.archive_top_k)
    diverse_k = ctx.archive.get_diverse_k(ctx.task_config.strategy.archive_diverse_k)

    # Merge without duplicates
    seen_ids: set[str] = set()
    for c in top_k + diverse_k:
        if c.id not in seen_ids:
            archive_exemplars.append(c)
            seen_ids.add(c.id)

    # Best candidate
    best_candidates = ctx.archive.get_top_k(1)
    best_candidate = best_candidates[0] if best_candidates else None

    # Score summary
    recent = ctx.archive.get_recent_k(ctx.task_config.strategy.archive_recent_k)
    score_summary = build_score_summary(recent) if recent else None

    from autoevolve.llm.base import create_provider
    provider = create_provider(ctx.task_config.mutator.provider, ctx.task_config.mutator)

    mutation_context = MutationContext(
        goal=goal,
        artifact_type=ctx.task_config.artifact_type,
        provider=provider,
        archive_exemplars=archive_exemplars,
        best_candidate=best_candidate,
        score_summary=score_summary,
    )

    children: list[Candidate] = []
    child_index = 0

    for parent in parents:
        for _ in range(ctx.task_config.strategy.children_per_parent):
            if ctx.budget.is_budget_exceeded():
                break

            try:
                child = mutator.mutate(parent, context=mutation_context)
                child.id = candidate_id(generation, child_index)
                child.generation = generation
                children.append(child)
                child_index += 1
            except Exception as e:
                # Log but don't crash the run
                ctx.emit_event("candidate_generation_failed", {
                    "parent_id": parent.id,
                    "error": str(e),
                })

    return children
