"""Patch mutator — makes a focused, targeted improvement."""

from __future__ import annotations

from datetime import datetime

from autoevolve.models import Candidate
from autoevolve.mutators.base import Mutator, MutationContext
from autoevolve.prompt_builder import build_mutation_prompt, parse_hypothesis_and_content


class PatchMutator(Mutator):
    """Generates a focused improvement to the artifact.

    For v1, the full artifact is still returned, but the prompt frames
    the request as a constrained, targeted change.
    """

    mutation_mode = "patch"

    def mutate(self, parent: Candidate, *, context: MutationContext) -> Candidate:
        """Generate a patched candidate."""
        prompt = build_mutation_prompt(
            mode="patch",
            artifact_content=parent.content,
            goal=context.goal,
            artifact_type=context.artifact_type,
            archive_exemplars=context.archive_exemplars,
            best_candidate=context.best_candidate,
            score_summary=context.score_summary,
            specialization=context.specialization,
        )

        raw_response = context.provider.generate(prompt)
        hypothesis, content = parse_hypothesis_and_content(raw_response)

        return Candidate(
            id="",
            generation=parent.generation + 1,
            parent_ids=[parent.id],
            content=content,
            mutation_mode=self.mutation_mode,
            hypothesis=hypothesis,
            created_at=datetime.now().isoformat(),
        )
