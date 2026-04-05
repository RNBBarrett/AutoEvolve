"""Console output reporter."""

from __future__ import annotations

from autoevolve.models import Candidate, TaskConfig


class ConsoleReporter:
    """Prints concise progress information to stdout."""

    def __init__(self, task_config: TaskConfig) -> None:
        self.task_name = task_config.name

    def report_run_start(self, task_config: TaskConfig) -> None:
        """Print run start information."""
        print(f"\n{'=' * 60}")
        print(f"  autoevolve — {task_config.name}")
        print(f"  Strategy: {task_config.strategy.type}")
        print(f"  Provider: {task_config.mutator.provider}")
        print(f"  Generations: {task_config.strategy.generations}")
        print(f"  Beam width: {task_config.strategy.beam_width}")
        print(f"{'=' * 60}\n")

    def report_generation_start(self, generation: int, total: int) -> None:
        """Print generation start."""
        print(f"  Generation {generation}/{total - 1}...")

    def report_generation_end(
        self,
        generation: int,
        candidates: list[Candidate],
        best_score: float | None,
    ) -> None:
        """Print generation results."""
        scored = [c for c in candidates if c.score is not None]
        failed = [c for c in candidates if c.status == "failed"]

        gen_best = max(
            (c.score for c in scored if c.score is not None),
            default=None,
        )

        parts = [f"    {len(scored)} evaluated"]
        if failed:
            parts.append(f"{len(failed)} failed")
        if gen_best is not None:
            parts.append(f"gen best: {gen_best:.4f}")
        if best_score is not None:
            parts.append(f"overall best: {best_score:.4f}")

        print(" | ".join(parts))

    def report_run_end(
        self,
        best_score: float | None,
        best_candidate_id: str | None,
        run_dir: str,
    ) -> None:
        """Print run completion summary."""
        print(f"\n{'=' * 60}")
        print(f"  Run complete")
        if best_score is not None:
            print(f"  Best score: {best_score:.4f}")
        if best_candidate_id:
            print(f"  Best candidate: {best_candidate_id}")
        print(f"  Output: {run_dir}")
        print(f"{'=' * 60}\n")
