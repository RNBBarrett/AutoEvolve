"""Integration test: full beam-strategy run on a prompt_text artifact.

Uses the ``tests/fixtures/prompt_task/`` fixture with the mock provider to
verify that the engine loop completes, scores improve over the baseline,
and candidate_evaluated events are recorded.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoevolve.engine.loop import run_evolution
from autoevolve.models import TaskConfig
from autoevolve.task_loader import load_task

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
PROMPT_TASK_YAML = FIXTURES_DIR / "prompt_task" / "task.yaml"


@pytest.fixture()
def prompt_task_config_short() -> TaskConfig:
    """Load the prompt_text fixture task with generations capped at 2."""
    config = load_task(PROMPT_TASK_YAML)
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


class TestBeamRunPromptText:
    """End-to-end beam run on a prompt_text artifact."""

    def test_run_completes(
        self, prompt_task_config_short: TaskConfig, run_in_tmp: Path
    ) -> None:
        run_state = run_evolution(prompt_task_config_short)
        assert run_state.status == "completed"

    def test_best_score_at_least_baseline(
        self, prompt_task_config_short: TaskConfig, run_in_tmp: Path
    ) -> None:
        """Best score should be >= the baseline score."""
        run_state = run_evolution(prompt_task_config_short)

        # Read events to find baseline_evaluated
        events_path = Path(run_state.run_dir) / "events.jsonl"
        events = [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        baseline_events = [e for e in events if e.get("event") == "baseline_evaluated"]
        assert len(baseline_events) == 1, "Expected exactly one baseline_evaluated event"
        baseline_score = baseline_events[0].get("score")

        assert run_state.best_score is not None
        assert baseline_score is not None
        assert run_state.best_score >= baseline_score, (
            f"Best score ({run_state.best_score}) should be >= baseline ({baseline_score})"
        )

    def test_events_contain_candidate_evaluated(
        self, prompt_task_config_short: TaskConfig, run_in_tmp: Path
    ) -> None:
        run_state = run_evolution(prompt_task_config_short)

        events_path = Path(run_state.run_dir) / "events.jsonl"
        events = [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        candidate_events = [e for e in events if e.get("event") == "candidate_evaluated"]
        assert len(candidate_events) > 0, "Expected at least one candidate_evaluated event"

        # Each candidate event should have a score
        for ce in candidate_events:
            assert "score" in ce, f"candidate_evaluated event missing 'score': {ce}"

    def test_completed_generations_match(
        self, prompt_task_config_short: TaskConfig, run_in_tmp: Path
    ) -> None:
        run_state = run_evolution(prompt_task_config_short)
        assert len(run_state.completed_generations) == 2
