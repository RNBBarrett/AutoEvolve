"""Swarm critic agent — screens candidates for validity."""

from __future__ import annotations

from autoevolve.llm.base import Provider
from autoevolve.models import Candidate
from autoevolve.prompt_builder import build_critic_prompt


class CriticAgent:
    """Conservative critic that rejects obviously broken candidates.

    If the critic errors, the candidate is approved (conservative failure mode).
    """

    def __init__(self, provider: Provider) -> None:
        self.provider = provider

    async def review(
        self,
        candidate: Candidate,
        goal: str,
        artifact_type: str,
    ) -> bool:
        """Review a candidate. Returns True if approved, False if rejected.

        On any error, defaults to approving the candidate.
        """
        prompt = build_critic_prompt(candidate.content, goal, artifact_type)

        try:
            response = await self.provider.agenerate(prompt)
            response_upper = response.strip().upper()

            if response_upper.startswith("REJECT"):
                candidate.metadata["critic_verdict"] = "rejected"
                candidate.metadata["critic_reason"] = response.strip()
                return False

            # Default: approve (conservative)
            candidate.metadata["critic_verdict"] = "approved"
            return True

        except Exception:
            # On error, approve (conservative failure mode per spec §13)
            candidate.metadata["critic_verdict"] = "approved_on_error"
            return True
