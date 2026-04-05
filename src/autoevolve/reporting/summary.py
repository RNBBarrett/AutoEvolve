"""Final summary and leaderboard generation."""

from __future__ import annotations

import json
from pathlib import Path

from autoevolve.models import Candidate, RunState
from autoevolve.utils.files import ensure_dir, write_json, write_text


def write_final_summary(
    run_dir: Path,
    run_state: RunState,
    all_candidates: list[Candidate],
    baseline_score: float | None,
) -> None:
    """Write final_summary.md and leaderboard.json.

    Args:
        run_dir: Path to the run output directory.
        run_state: Final run state.
        all_candidates: All evaluated candidates.
        baseline_score: Score of the original baseline artifact.
    """
    summaries_dir = ensure_dir(run_dir / "summaries")

    # --- final_summary.md ---
    best_score = run_state.best_score
    improvement = None
    if baseline_score is not None and best_score is not None:
        improvement = best_score - baseline_score

    lines = [
        "# Run Summary\n",
        f"**Task:** {run_state.task_config.name}\n",
        f"**Status:** {run_state.status}\n",
        f"**Start:** {run_state.start_time}\n",
        f"**End:** {run_state.end_time or 'N/A'}\n",
        "",
        "## Results\n",
        f"**Baseline score:** {_fmt_score(baseline_score)}\n",
        f"**Best final score:** {_fmt_score(best_score)}\n",
    ]

    if improvement is not None:
        sign = "+" if improvement >= 0 else ""
        lines.append(f"**Improvement:** {sign}{improvement:.4f}\n")

    lines.extend([
        f"**Best candidate:** {run_state.best_candidate_id or 'N/A'}\n",
        f"**Generations completed:** {len(run_state.completed_generations)}\n",
        f"**Total candidates evaluated:** {run_state.total_candidates_evaluated}\n",
        "",
    ])

    # Count failures
    failed = [c for c in all_candidates if c.status == "failed"]
    if failed:
        lines.append(f"**Failed evaluations:** {len(failed)}\n")

    write_text(summaries_dir / "final_summary.md", "\n".join(lines))

    # --- leaderboard.json ---
    scored = [c for c in all_candidates if c.score is not None]
    leaderboard = sorted(
        [
            {
                "candidate_id": c.id,
                "score": c.score,
                "generation": c.generation,
                "mutation_mode": c.mutation_mode,
                "hypothesis": c.hypothesis,
            }
            for c in scored
        ],
        key=lambda x: x["score"],
        reverse=True,
    )
    write_json(summaries_dir / "leaderboard.json", leaderboard)


def print_run_inspection(run_dir: Path) -> None:
    """Print a human-readable inspection of a completed run."""
    run_json = run_dir / "run.json"
    if not run_json.is_file():
        print(f"No run.json found in {run_dir}")
        return

    with open(run_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"\nRun: {data.get('run_id', 'unknown')}")
    print(f"Task: {data.get('task_config', {}).get('name', 'unknown')}")
    print(f"Status: {data.get('status', 'unknown')}")
    print(f"Generations: {len(data.get('completed_generations', []))}")
    print(f"Candidates evaluated: {data.get('total_candidates_evaluated', 0)}")

    best_score = data.get("best_score")
    if best_score is not None:
        print(f"Best score: {best_score:.4f}")

    best_id = data.get("best_candidate_id")
    if best_id:
        print(f"Best candidate: {best_id}")

    print(f"Run directory: {run_dir}")

    # Check for summary
    summary_path = run_dir / "summaries" / "final_summary.md"
    if summary_path.is_file():
        print(f"\n--- Summary ---")
        print(summary_path.read_text(encoding="utf-8"))


def _fmt_score(score: float | None) -> str:
    """Format a score for display."""
    return f"{score:.4f}" if score is not None else "N/A"
