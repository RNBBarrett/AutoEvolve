"""Markdown log writer."""

from __future__ import annotations

from pathlib import Path

from autoevolve.models import Candidate, TaskConfig


class MarkdownLogger:
    """Builds a human-readable log.md incrementally."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path

    def write_header(self, task_config: TaskConfig, run_id: str) -> None:
        """Write the run header."""
        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write(f"# autoevolve Run Log\n\n")
            f.write(f"**Run ID:** {run_id}\n\n")
            f.write(f"**Task:** {task_config.name}\n\n")
            f.write(f"**Artifact type:** {task_config.artifact_type}\n\n")
            f.write(f"**Strategy:** {task_config.strategy.type}\n\n")
            f.write(f"**Provider:** {task_config.mutator.provider}\n\n")
            f.write(f"**Generations:** {task_config.strategy.generations}\n\n")
            f.write(f"**Beam width:** {task_config.strategy.beam_width}\n\n")
            f.write(f"---\n\n")

    def write_generation(
        self,
        generation: int,
        candidates: list[Candidate],
        survivors: list[Candidate],
        best_overall: Candidate | None,
    ) -> None:
        """Append a generation section to the log."""
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"## Generation {generation}\n\n")

            # Score table
            f.write("| Candidate | Parents | Mode | Score | Status | Hypothesis |\n")
            f.write("|-----------|---------|------|-------|--------|------------|\n")
            for c in sorted(candidates, key=lambda x: (x.score is not None, x.score or 0), reverse=True):
                score_str = f"{c.score:.4f}" if c.score is not None else "N/A"
                parents = ", ".join(c.parent_ids) if c.parent_ids else "-"
                hyp = (c.hypothesis or "")[:60]
                f.write(f"| {c.id} | {parents} | {c.mutation_mode} | {score_str} | {c.status} | {hyp} |\n")
            f.write("\n")

            # Survivors
            if survivors:
                survivor_ids = ", ".join(s.id for s in survivors)
                f.write(f"**Survivors:** {survivor_ids}\n\n")

            # Best overall
            if best_overall and best_overall.score is not None:
                f.write(f"**Best overall:** {best_overall.id} (score: {best_overall.score:.4f})\n\n")

            f.write("---\n\n")

    def write_footer(
        self,
        best_candidate: Candidate | None,
        total_evaluated: int,
    ) -> None:
        """Write the final footer."""
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write("## Final Results\n\n")
            if best_candidate:
                score_str = f"{best_candidate.score:.4f}" if best_candidate.score is not None else "N/A"
                f.write(f"**Best candidate:** {best_candidate.id}\n\n")
                f.write(f"**Best score:** {score_str}\n\n")
            f.write(f"**Total candidates evaluated:** {total_evaluated}\n\n")
