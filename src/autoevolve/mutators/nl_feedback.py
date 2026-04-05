"""Natural-language feedback mutator (OPRO-style).

Generates candidates by feeding prior candidates and their scores
as natural language context to the LLM.
"""

from __future__ import annotations

from datetime import datetime

from autoevolve.models import Candidate
from autoevolve.mutators.base import Mutator, MutationContext
from autoevolve.prompt_builder import build_mutation_prompt, parse_hypothesis_and_content


class NLFeedbackMutator(Mutator):
    """Generates candidates using natural-language optimization feedback.

    This is the OPRO-style mutation pattern. The model receives prior
    candidates, their scores, and optional metrics, then generates an
    improved candidate based on what seems to be working.
    """

    mutation_mode = "nl_feedback"

    def mutate(self, parent: Candidate, *, context: MutationContext) -> Candidate:
        """Generate a candidate using NL feedback from prior attempts."""
        prompt = build_mutation_prompt(
            mode="nl_feedback",
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
