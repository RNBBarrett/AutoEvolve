"""Swarm diversity agent — detects and breaks beam collapse."""

from __future__ import annotations

from datetime import datetime

from autoevolve.llm.base import Provider
from autoevolve.models import Candidate
from autoevolve.prompt_builder import build_diversity_prompt, parse_hypothesis_and_content
from autoevolve.utils.text import compute_similarity


COLLAPSE_THRESHOLD = 0.85


class DiversityAgent:
    """Detects beam collapse and injects diverse candidates."""

    def __init__(self, provider: Provider) -> None:
        self.provider = provider

    def detect_collapse(self, candidates: list[Candidate]) -> bool:
        """Check if all candidate pairs have high similarity.

        Returns True if beam collapse is detected.
        """
        if len(candidates) < 2:
            return False

        for i in range(len(candidates)):
            for j in range(i + 1, len(candidates)):
                sim = compute_similarity(candidates[i].content, candidates[j].content)
                if sim < COLLAPSE_THRESHOLD:
                    return False

        return True

    async def inject_diversity(
        self,
        candidates: list[Candidate],
        goal: str,
        artifact_type: str,
        artifact_content: str,
    ) -> Candidate | None:
        """Generate a deliberately different candidate if collapse is detected.

        Returns None if collapse is not detected.
        """
        if not self.detect_collapse(candidates):
            return None

        prompt = build_diversity_prompt(
            current_candidates=candidates,
            goal=goal,
            artifact_type=artifact_type,
            artifact_content=artifact_content,
        )

        try:
            raw_response = await self.provider.agenerate(prompt)
            hypothesis, content = parse_hypothesis_and_content(raw_response)

            generation = max(c.generation for c in candidates) if candidates else 0

            return Candidate(
                id="",
                generation=generation,
                parent_ids=[],
                content=content,
                mutation_mode="swarm_diversity",
                hypothesis=hypothesis,
                created_at=datetime.now().isoformat(),
                metadata={"diversity_injection": True},
            )
        except Exception:
            return None
