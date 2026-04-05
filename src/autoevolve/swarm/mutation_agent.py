"""Swarm mutation agent — a specialized mutator with a particular focus."""

from __future__ import annotations

from datetime import datetime

from autoevolve.llm.base import Provider
from autoevolve.models import Candidate
from autoevolve.mutators.base import MutationContext
from autoevolve.prompt_builder import build_mutation_prompt, parse_hypothesis_and_content


SPECIALIZATIONS = {
    "algorithmic": (
        "Focus on ALGORITHMIC improvements. Look for better data structures, "
        "more efficient algorithms, reduced time complexity, or smarter use "
        "of mathematical properties."
    ),
    "optimization": (
        "Focus on PERFORMANCE OPTIMIZATION. Look for unnecessary work, "
        "redundant computations, opportunities for caching, loop optimization, "
        "or memory efficiency improvements."
    ),
    "architectural": (
        "Focus on STRUCTURAL/ARCHITECTURAL improvements. Look for better "
        "code organization, cleaner abstractions, more readable logic, "
        "or simplified control flow."
    ),
    "hybrid": (
        "Take a CREATIVE, HYBRID approach. Combine ideas from different "
        "optimization strategies. Try unconventional approaches that might "
        "achieve a breakthrough improvement."
    ),
}


class MutationAgent:
    """A swarm mutation agent with a specific specialization."""

    def __init__(self, specialization: str, provider: Provider) -> None:
        self.specialization = specialization
        self.provider = provider
        self.spec_instruction = SPECIALIZATIONS.get(specialization, specialization)

    async def generate(
        self,
        parent: Candidate,
        context: MutationContext,
    ) -> Candidate:
        """Generate a candidate with this agent's specialization."""
        context_with_spec = MutationContext(
            goal=context.goal,
            artifact_type=context.artifact_type,
            provider=self.provider,
            archive_exemplars=context.archive_exemplars,
            best_candidate=context.best_candidate,
            score_summary=context.score_summary,
            specialization=self.spec_instruction,
        )

        prompt = build_mutation_prompt(
            mode="rewrite",
            artifact_content=parent.content,
            goal=context_with_spec.goal,
            artifact_type=context_with_spec.artifact_type,
            archive_exemplars=context_with_spec.archive_exemplars,
            best_candidate=context_with_spec.best_candidate,
            score_summary=context_with_spec.score_summary,
            specialization=context_with_spec.specialization,
        )

        raw_response = await self.provider.agenerate(prompt)
        hypothesis, content = parse_hypothesis_and_content(raw_response)

        return Candidate(
            id="",  # Assigned by orchestrator
            generation=parent.generation + 1,
            parent_ids=[parent.id],
            content=content,
            mutation_mode=f"swarm_{self.specialization}",
            hypothesis=hypothesis,
            created_at=datetime.now().isoformat(),
            metadata={"specialization": self.specialization},
        )
