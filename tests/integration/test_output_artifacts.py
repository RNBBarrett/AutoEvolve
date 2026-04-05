"""Integration test: verify output file structure after a run.

Runs a full evolution and checks that every expected file and directory
is present in the run output.
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
def completed_run_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Run a full evolution and return the resulting run directory."""
    monkeypatch.chdir(tmp_path)

    config = load_task(PYTHON_TASK_YAML)
    config.strategy.generations = 2
    config.strategy.beam_width = 2
    config.strategy.children_per_parent = 2
    config.mutator.provider = "mock"
    config.mutator.model = "mock-deterministic"

    run_state = run_evolution(config)
    return Path(run_state.run_dir)


class TestOutputArtifacts:
    """Verify the file structure produced by a completed run."""

    def test_run_json_exists(self, completed_run_dir: Path) -> None:
        run_json = completed_run_dir / "run.json"
        assert run_json.is_file(), "run.json not found in run directory"

        # Verify it is valid JSON
        data = json.loads(run_json.read_text(encoding="utf-8"))
        assert data["status"] == "completed"

    def test_events_jsonl_exists(self, completed_run_dir: Path) -> None:
        events_path = completed_run_dir / "events.jsonl"
        assert events_path.is_file(), "events.jsonl not found"

        lines = [
            line.strip()
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(lines) > 0, "events.jsonl should have at least one entry"

    def test_markdown_log_exists(self, completed_run_dir: Path) -> None:
        log_md = completed_run_dir / "log.md"
        assert log_md.is_file(), "log.md not found (markdown log should be enabled)"
        content = log_md.read_text(encoding="utf-8")
        assert len(content) > 0, "log.md is empty"

    def test_best_candidate_directory_exists(self, completed_run_dir: Path) -> None:
        best_dir = completed_run_dir / "best_candidate"
        assert best_dir.is_dir(), "best_candidate/ directory not found"

    def test_summaries_final_summary_exists(self, completed_run_dir: Path) -> None:
        summary_path = completed_run_dir / "summaries" / "final_summary.md"
        assert summary_path.is_file(), "summaries/final_summary.md not found"
        content = summary_path.read_text(encoding="utf-8")
        assert "Run Summary" in content

    def test_summaries_leaderboard_exists(self, completed_run_dir: Path) -> None:
        leaderboard_path = completed_run_dir / "summaries" / "leaderboard.json"
        assert leaderboard_path.is_file(), "summaries/leaderboard.json not found"

        # Verify it is valid JSON (a list of dicts)
        data = json.loads(leaderboard_path.read_text(encoding="utf-8"))
        assert isinstance(data, list), "leaderboard.json should be a JSON array"
        if len(data) > 0:
            assert "candidate_id" in data[0]
            assert "score" in data[0]

    def test_run_json_has_expected_fields(self, completed_run_dir: Path) -> None:
        run_json = completed_run_dir / "run.json"
        data = json.loads(run_json.read_text(encoding="utf-8"))

        expected_keys = [
            "run_id",
            "task_config",
            "status",
            "start_time",
            "end_time",
            "completed_generations",
            "best_score",
            "best_candidate_id",
            "total_candidates_evaluated",
        ]
        for key in expected_keys:
            assert key in data, f"run.json missing expected field: {key}"

    def test_events_contain_full_lifecycle(self, completed_run_dir: Path) -> None:
        """Verify that key lifecycle events appear in events.jsonl."""
        events_path = completed_run_dir / "events.jsonl"
        events = [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        event_types = {e.get("event") for e in events}
        expected_types = {
            "run_started",
            "baseline_evaluated",
            "generation_started",
            "candidate_evaluated",
            "generation_completed",
            "run_completed",
        }
        for etype in expected_types:
            assert etype in event_types, (
                f"Expected event '{etype}' in events.jsonl. Found: {event_types}"
            )
