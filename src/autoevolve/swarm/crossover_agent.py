"""Swarm crossover agent — combines pairs of candidates."""

from __future__ import annotations

from datetime import datetime

from autoevolve.llm.base import Provider
from autoevolve.models import Candidate
from autoevolve.prompt_builder import build_crossover_prompt, parse_hypothesis_and_content


class CrossoverAgent:
    """Produces a child by combining two parent candidates."""

    def __init__(self, provider: Provider) -> None:
        self.provider = provider

    async def crossover(
        self,
        parent_a: Candidate,
        parent_b: Candidate,
        goal: str,
        artifact_type: str,
    ) -> Candidate:
        """Generate a crossover child from two parents."""
        prompt = build_crossover_prompt(parent_a, parent_b, goal, artifact_type)
        raw_response = await self.provider.agenerate(prompt)
        hypothesis, content = parse_hypothesis_and_content(raw_response)

        return Candidate(
            id="",
            generation=max(parent_a.generation, parent_b.generation) + 1,
            parent_ids=[parent_a.id, parent_b.id],
            content=content,
            mutation_mode="swarm_crossover",
            hypothesis=hypothesis,
            created_at=datetime.now().isoformat(),
        )
