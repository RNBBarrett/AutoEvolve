"""Run context — holds all state for a running evolution."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from autoevolve.archive.in_memory import InMemoryArchive
from autoevolve.lineage import LineageTracker
from autoevolve.models import Candidate, RunState, TaskConfig
from autoevolve.reporting.console import ConsoleReporter
from autoevolve.reporting.jsonl_log import JsonlLogger
from autoevolve.reporting.markdown_log import MarkdownLogger
from autoevolve.utils.files import ensure_dir, write_json
from autoevolve.utils.hashing import run_id as make_run_id
from autoevolve.utils.timeouts import BudgetTracker


class RunContext:
    """Holds all state and services for a single evolution run."""

    def __init__(
        self,
        task_config: TaskConfig,
        run_dir: Path,
        run_state: RunState,
    ) -> None:
        self.task_config = task_config
        self.run_dir = run_dir
        self.run_state = run_state

        # Core components
        self.archive = InMemoryArchive()
        self.lineage = LineageTracker()
        self.budget = BudgetTracker(
            max_runtime_seconds=task_config.budget.max_runtime_seconds,
            max_total_candidates=task_config.budget.max_total_candidates,
        )

        # Reporters
        self.console = ConsoleReporter(task_config)
        self.jsonl = JsonlLogger(run_dir / "events.jsonl")
        self.markdown = MarkdownLogger(run_dir / "log.md")

        # Track all candidates for summary
        self.all_candidates: list[Candidate] = []
        self.baseline_score: float | None = None

    def emit_event(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        """Log an event to events.jsonl."""
        if self.task_config.output.write_jsonl_events:
            self.jsonl.log_event(event_type, data)

    def save_run_state(self) -> None:
        """Write run.json to disk."""
        write_json(self.run_dir / "run.json", self.run_state.to_dict())

    def generation_dir(self, generation: int) -> Path:
        """Get or create the directory for a generation."""
        gen_dir = self.run_dir / "generations" / f"gen_{generation:03d}"
        return ensure_dir(gen_dir)


def create_run_context(
    task_config: TaskConfig,
    run_name: str | None = None,
    base_dir: Path | None = None,
) -> RunContext:
    """Create a new RunContext with a fresh run directory.

    Args:
        task_config: The task configuration.
        run_name: Optional override for the run directory name.
        base_dir: Base directory for runs (defaults to ./runs).

    Returns:
        An initialized RunContext.
    """
    if base_dir is None:
        base_dir = Path("runs")

    name = run_name or task_config.name
    rid = make_run_id(name)
    run_dir = ensure_dir(base_dir / rid)
    ensure_dir(run_dir / "best_candidate")
    ensure_dir(run_dir / "generations")
    ensure_dir(run_dir / "summaries")

    run_state = RunState(
        run_id=rid,
        task_config=task_config,
        status="running",
        start_time=datetime.now().isoformat(),
        run_dir=str(run_dir),
    )

    ctx = RunContext(task_config, run_dir, run_state)

    # Write initial header for markdown log
    if task_config.output.write_markdown_log:
        ctx.markdown.write_header(task_config, rid)

    return ctx
