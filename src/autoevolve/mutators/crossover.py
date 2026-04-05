"""Crossover mutator — combines two parent candidates."""

from __future__ import annotations

from datetime import datetime

from autoevolve.models import Candidate
from autoevolve.mutators.base import Mutator, MutationContext
from autoevolve.prompt_builder import build_crossover_prompt, parse_hypothesis_and_content


class CrossoverMutator(Mutator):
    """Combines the best parts of two parent candidates.

    This performs semantic crossover (not naive text splicing).
    The LLM is asked to intelligently combine strengths of both parents.
    """

    mutation_mode = "crossover"

    def mutate(self, parent: Candidate, *, context: MutationContext) -> Candidate:
        """Generate a crossover candidate.

        Note: For crossover, the second parent should be provided via
        context.best_candidate or use mutate_pair() directly.
        """
        second_parent = context.best_candidate
        if second_parent is None or second_parent.id == parent.id:
            # Fallback: just rewrite if no second parent
            from autoevolve.mutators.rewrite import RewriteMutator
            return RewriteMutator().mutate(parent, context=context)

        return self.mutate_pair(parent, second_parent, context=context)

    def mutate_pair(
        self,
        parent_a: Candidate,
        parent_b: Candidate,
        *,
        context: MutationContext,
    ) -> Candidate:
        """Generate a child from two parents."""
        prompt = build_crossover_prompt(
            parent_a=parent_a,
            parent_b=parent_b,
            goal=context.goal,
            artifact_type=context.artifact_type,
        )

        raw_response = context.provider.generate(prompt)
        hypothesis, content = parse_hypothesis_and_content(raw_response)

        return Candidate(
            id="",
            generation=max(parent_a.generation, parent_b.generation) + 1,
            parent_ids=[parent_a.id, parent_b.id],
            content=content,
            mutation_mode=self.mutation_mode,
            hypothesis=hypothesis,
            created_at=datetime.now().isoformat(),
        )
