"""Integration test: full beam-strategy run on a python_code artifact.

Uses the ``tests/fixtures/python_task/`` fixture with the mock provider to
verify that the engine loop completes successfully and produces the expected
output files.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoevolve.engine.loop import run_evolution
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


class TestBeamRunPythonCode:
    """End-to-end beam run on a python_code artifact."""

    def test_run_completes_with_status_completed(
        self, python_task_config_short: TaskConfig, run_in_tmp: Path
    ) -> None:
        run_state = run_evolution(python_task_config_short)
        assert run_state.status == "completed"

    def test_run_directory_is_created(
        self, python_task_config_short: TaskConfig, run_in_tmp: Path
    ) -> None:
        run_state = run_evolution(python_task_config_short)
        run_dir = Path(run_state.run_dir)
        assert run_dir.is_dir(), f"Run directory not created: {run_dir}"

    def test_events_jsonl_exists_and_has_entries(
        self, python_task_config_short: TaskConfig, run_in_tmp: Path
    ) -> None:
        run_state = run_evolution(python_task_config_short)
        events_path = Path(run_state.run_dir) / "events.jsonl"
        assert events_path.is_file(), "events.jsonl not found"

        lines = [
            line.strip()
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(lines) > 0, "events.jsonl has no entries"

        # Verify each line is valid JSON
        for line in lines:
            event = json.loads(line)
            assert "event" in event

    def test_best_candidate_directory_exists(
        self, python_task_config_short: TaskConfig, run_in_tmp: Path
    ) -> None:
        run_state = run_evolution(python_task_config_short)
        best_dir = Path(run_state.run_dir) / "best_candidate"
        assert best_dir.is_dir(), "best_candidate/ directory not found"

    def test_completed_generations_match(
        self, python_task_config_short: TaskConfig, run_in_tmp: Path
    ) -> None:
        run_state = run_evolution(python_task_config_short)
        assert len(run_state.completed_generations) == 2
        assert set(run_state.completed_generations) == {0, 1}

    def test_best_score_is_set(
        self, python_task_config_short: TaskConfig, run_in_tmp: Path
    ) -> None:
        run_state = run_evolution(python_task_config_short)
        assert run_state.best_score is not None
        assert run_state.best_score >= 0.0
