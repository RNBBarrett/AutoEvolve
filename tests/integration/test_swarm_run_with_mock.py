"""Integration test: swarm strategy with mock provider.

Loads a task config, overrides the strategy to ``swarm``, and verifies that
the run completes and produces candidates.  Uses the python_code fixture
because it is faster to evaluate.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autoevolve.engine.loop import run_evolution
from autoevolve.models import TaskConfig
from autoevolve.task_loader import load_task

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
PYTHON_TASK_YAML = FIXTURES_DIR / "python_task" / "task.yaml"


@pytest.fixture()
def swarm_task_config() -> TaskConfig:
    """Load the python_code fixture configured for swarm strategy."""
    config = load_task(PYTHON_TASK_YAML)
    config.strategy.type = "swarm"
    config.strategy.generations = 2
    config.strategy.beam_width = 2
    config.strategy.children_per_parent = 2
    config.mutator.provider = "mock"
    config.mutator.model = "mock-deterministic"
    config.swarm.enabled = True
    config.swarm.mutation_agents = 2
    config.swarm.use_critic = True
    config.swarm.use_diversity_agent = False
    config.swarm.max_concurrent_calls = 2
    config.budget.max_total_candidates = 30
    config.budget.max_runtime_seconds = 120
    return config


@pytest.fixture()
def run_in_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Change cwd to *tmp_path* so that ``runs/`` is created there."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestSwarmRunWithMock:
    """End-to-end swarm-strategy run with mock provider."""

    def test_swarm_run_completes(
        self, swarm_task_config: TaskConfig, run_in_tmp: Path
    ) -> None:
        run_state = run_evolution(swarm_task_config)
        assert run_state.status == "completed"

    def test_swarm_produces_candidates(
        self, swarm_task_config: TaskConfig, run_in_tmp: Path
    ) -> None:
        run_state = run_evolution(swarm_task_config)
        assert run_state.total_candidates_evaluated > 0, (
            "Swarm should produce at least one evaluated candidate"
        )

    def test_swarm_best_score_is_set(
        self, swarm_task_config: TaskConfig, run_in_tmp: Path
    ) -> None:
        run_state = run_evolution(swarm_task_config)
        assert run_state.best_score is not None

    def test_swarm_run_directory_created(
        self, swarm_task_config: TaskConfig, run_in_tmp: Path
    ) -> None:
        run_state = run_evolution(swarm_task_config)
        run_dir = Path(run_state.run_dir)
        assert run_dir.is_dir()
        assert (run_dir / "events.jsonl").is_file()
        assert (run_dir / "run.json").is_file()
