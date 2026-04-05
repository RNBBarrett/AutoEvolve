"""Swarm orchestrator — coordinates multiple specialized agents."""

from __future__ import annotations

import asyncio
from typing import Any

from autoevolve.engine.run_context import RunContext
from autoevolve.llm.base import Provider, create_provider
from autoevolve.models import Candidate
from autoevolve.mutators.base import MutationContext
from autoevolve.prompt_builder import build_score_summary
from autoevolve.swarm.critic_agent import CriticAgent
from autoevolve.swarm.crossover_agent import CrossoverAgent
from autoevolve.swarm.diversity_agent import DiversityAgent
from autoevolve.swarm.mutation_agent import MutationAgent
from autoevolve.utils.files import read_text
from autoevolve.utils.hashing import candidate_id


AGENT_SPECIALIZATIONS = ["algorithmic", "optimization", "architectural", "hybrid"]


class SwarmOrchestrator:
    """Orchestrates multiple swarm agents per generation.

    For each generation:
    1. Launch mutation agents concurrently
    2. Optionally run critic screening
    3. Optionally run crossover on top parents
    4. Optionally trigger diversity injection
    5. Return all approved candidates for evaluation
    """

    def __init__(self, ctx: RunContext) -> None:
        self.ctx = ctx
        self.config = ctx.task_config.swarm
        self.provider = create_provider(
            ctx.task_config.mutator.provider,
            ctx.task_config.mutator,
        )

    async def run_generation(
        self,
        generation: int,
        parents: list[Candidate],
    ) -> list[Candidate]:
        """Run one swarm generation asynchronously."""
        goal = read_text(self.ctx.task_config.task_dir / self.ctx.task_config.goal_path)
        artifact_type = self.ctx.task_config.artifact_type

        # Build shared mutation context
        archive_exemplars = []
        top_k = self.ctx.archive.get_top_k(self.ctx.task_config.strategy.archive_top_k)
        diverse_k = self.ctx.archive.get_diverse_k(self.ctx.task_config.strategy.archive_diverse_k)
        seen: set[str] = set()
        for c in top_k + diverse_k:
            if c.id not in seen:
                archive_exemplars.append(c)
                seen.add(c.id)

        best_candidates = self.ctx.archive.get_top_k(1)
        best_candidate = best_candidates[0] if best_candidates else None

        recent = self.ctx.archive.get_recent_k(self.ctx.task_config.strategy.archive_recent_k)
        score_summary = build_score_summary(recent) if recent else None

        context = MutationContext(
            goal=goal,
            artifact_type=artifact_type,
            provider=self.provider,
            archive_exemplars=archive_exemplars,
            best_candidate=best_candidate,
            score_summary=score_summary,
        )

        # 1. Launch mutation agents concurrently
        semaphore = asyncio.Semaphore(self.config.max_concurrent_calls)
        agents = self._create_agents()
        candidates = await self._run_mutation_agents(
            agents, parents, context, generation, semaphore
        )

        # 2. Critic screening
        if self.config.use_critic and candidates:
            candidates = await self._run_critic(candidates, goal, artifact_type, semaphore)

        # 3. Crossover
        if self.ctx.task_config.strategy.crossover_enabled and len(parents) >= 2:
            crossover_child = await self._run_crossover(
                parents, goal, artifact_type, generation, len(candidates)
            )
            if crossover_child:
                candidates.append(crossover_child)

        # 4. Diversity injection
        if self.config.use_diversity_agent and candidates:
            artifact_content = parents[0].content if parents else ""
            diversity_child = await self._run_diversity(
                candidates, goal, artifact_type, artifact_content, generation, len(candidates)
            )
            if diversity_child:
                candidates.append(diversity_child)

        return candidates

    def _create_agents(self) -> list[MutationAgent]:
        """Create mutation agents with different specializations."""
        num_agents = self.config.mutation_agents
        agents = []
        for i in range(num_agents):
            spec = AGENT_SPECIALIZATIONS[i % len(AGENT_SPECIALIZATIONS)]
            agents.append(MutationAgent(spec, self.provider))
        return agents

    async def _run_mutation_agents(
        self,
        agents: list[MutationAgent],
        parents: list[Candidate],
        context: MutationContext,
        generation: int,
        semaphore: asyncio.Semaphore,
    ) -> list[Candidate]:
        """Run all mutation agents concurrently with bounded concurrency."""
        tasks = []
        for i, agent in enumerate(agents):
            parent = parents[i % len(parents)] if parents else parents[0]

            async def run_agent(a: MutationAgent, p: Candidate, idx: int) -> Candidate | None:
                async with semaphore:
                    try:
                        child = await a.generate(p, context)
                        child.id = candidate_id(generation, idx)
                        child.generation = generation
                        return child
                    except Exception as e:
                        self.ctx.emit_event("swarm_agent_failed", {
                            "agent": a.specialization,
                            "error": str(e),
                        })
                        return None

            tasks.append(run_agent(agent, parent, i))

        results = await asyncio.gather(*tasks)
        return [c for c in results if c is not None]

    async def _run_critic(
        self,
        candidates: list[Candidate],
        goal: str,
        artifact_type: str,
        semaphore: asyncio.Semaphore,
    ) -> list[Candidate]:
        """Run critic screening on all candidates."""
        critic = CriticAgent(self.provider)
        approved = []

        for candidate in candidates:
            async with semaphore:
                is_approved = await critic.review(candidate, goal, artifact_type)
                if is_approved:
                    approved.append(candidate)
                else:
                    self.ctx.emit_event("candidate_rejected_by_critic", {
                        "candidate_id": candidate.id,
                        "reason": candidate.metadata.get("critic_reason", ""),
                    })

        return approved if approved else candidates[:1]  # Keep at least one

    async def _run_crossover(
        self,
        parents: list[Candidate],
        goal: str,
        artifact_type: str,
        generation: int,
        start_index: int,
    ) -> Candidate | None:
        """Attempt crossover on top two parents."""
        if len(parents) < 2:
            return None

        sorted_parents = sorted(
            parents,
            key=lambda c: (c.score is not None, c.score or 0),
            reverse=True,
        )

        crossover_agent = CrossoverAgent(self.provider)
        try:
            child = await crossover_agent.crossover(
                sorted_parents[0], sorted_parents[1], goal, artifact_type
            )
            child.id = candidate_id(generation, start_index)
            child.generation = generation
            return child
        except Exception as e:
            self.ctx.emit_event("swarm_crossover_failed", {"error": str(e)})
            return None

    async def _run_diversity(
        self,
        candidates: list[Candidate],
        goal: str,
        artifact_type: str,
        artifact_content: str,
        generation: int,
        start_index: int,
    ) -> Candidate | None:
        """Check for collapse and inject diversity if needed."""
        diversity_agent = DiversityAgent(self.provider)
        child = await diversity_agent.inject_diversity(
            candidates, goal, artifact_type, artifact_content
        )
        if child:
            child.id = candidate_id(generation, start_index)
            child.generation = generation
        return child
