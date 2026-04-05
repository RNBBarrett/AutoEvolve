"""Integration test: resuming a completed run.

Runs a full 2-generation evolution, then calls ``resume_evolution`` on the
completed run directory.  The spec says this should detect that all
generations are already completed and return the existing run state with
the message "Run already completed all generations."
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autoevolve.engine.loop import resume_evolution, run_evolution
from autoevolve.models import TaskConfig
from autoevolve.task_loader import load_task

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
PYTHON_TASK_YAML = FIXTURES_DIR / "python_task" / "task.yaml"


@pytest.fixture()
def python_task_config_short() -> TaskConfig:
    """Load the python_code fixture task with generations capped at 2."""
    config = load_task(PYTHON_TASK_YAML)
    config.strategy.generations = 2
    config.strategy.beam_width = 2
    config.strategy.children_per_parent = 2
    config.mutator.provider = "mock"
    config.mutator.model = "mock-deterministic"
    return config


@pytest.fixture()
def run_in_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Change cwd to *tmp_path* so that ``runs/`` is created there."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestResumeRun:
    """Test the resume_evolution flow."""

    def test_resume_completed_run_returns_state(
        self, python_task_config_short: TaskConfig, run_in_tmp: Path
    ) -> None:
        """Resuming a fully completed run should return the existing state."""
        # Step 1: run a full evolution
        initial_state = run_evolution(python_task_config_short)
        assert initial_state.status == "completed"

        # Step 2: attempt to resume the already-completed run
        run_dir = Path(initial_state.run_dir)
        resumed_state = resume_evolution(run_dir)

        # The function should detect "all generations done" and return
        assert resumed_state.status == "completed"
        assert set(resumed_state.completed_generations) == {0, 1}

    def test_resume_preserves_best_score(
        self, python_task_config_short: TaskConfig, run_in_tmp: Path
    ) -> None:
        """Resuming should not lose the best score from the original run."""
        initial_state = run_evolution(python_task_config_short)
        run_dir = Path(initial_state.run_dir)

        resumed_state = resume_evolution(run_dir)

        assert resumed_state.best_score == initial_state.best_score
        assert resumed_state.best_candidate_id == initial_state.best_candidate_id

    def test_resume_nonexistent_dir_raises(self, run_in_tmp: Path) -> None:
        """Resuming from a nonexistent directory should raise ResumeError."""
        from autoevolve.errors import ResumeError

        with pytest.raises(ResumeError):
            resume_evolution(run_in_tmp / "nonexistent_run")
