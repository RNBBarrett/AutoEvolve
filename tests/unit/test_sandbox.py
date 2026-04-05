"""Unit tests for autoevolve.evaluation.sandbox — SandboxEvaluator."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from autoevolve.evaluation.sandbox import SandboxEvaluator
from autoevolve.models import (
    BudgetConfig,
    MutatorConfig,
    OutputConfig,
    StrategyConfig,
    TaskConfig,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_task_dir(
    base: Path,
    evaluator_code: str,
    artifact_type: str = "python_code",
) -> TaskConfig:
    """Create a minimal task directory with a task.yaml, evaluator.py, and seed artifact.

    Returns a TaskConfig pointing at the created directory.
    """
    base.mkdir(parents=True, exist_ok=True)

    # Write a minimal task.yaml (not used directly by SandboxEvaluator, but
    # TaskConfig needs paths that exist).
    goal_file = base / "goal.md"
    goal_file.write_text("Test goal.", encoding="utf-8")

    evaluator_file = base / "evaluator.py"
    evaluator_file.write_text(evaluator_code, encoding="utf-8")

    if artifact_type == "python_code":
        artifact_file = base / "artifact.py"
        artifact_file.write_text("# seed\n", encoding="utf-8")
    else:
        artifact_file = base / "artifact.txt"
        artifact_file.write_text("seed prompt\n", encoding="utf-8")

    return TaskConfig(
        name="sandbox_test",
        artifact_type=artifact_type,
        artifact_path=artifact_file.name,
        goal_path=goal_file.name,
        evaluator_path=evaluator_file.name,
        task_dir=base,
        strategy=StrategyConfig(),
        mutator=MutatorConfig(),
        budget=BudgetConfig(),
        output=OutputConfig(),
    )


# ---------------------------------------------------------------------------
# Evaluator code snippets (written to temp evaluator.py files)
# ---------------------------------------------------------------------------

PASSING_EVALUATOR = textwrap.dedent("""\
    import json

    def evaluate(candidate_path, task_dir):
        with open(candidate_path, encoding="utf-8") as f:
            content = f.read()
        return {
            "score": 0.85,
            "passed": True,
            "summary": f"Evaluated {len(content)} chars",
        }
""")

SLEEPING_EVALUATOR = textwrap.dedent("""\
    import json
    import time

    def evaluate(candidate_path, task_dir):
        time.sleep(30)
        return {"score": 1.0, "passed": True, "summary": "Should not reach here"}
""")

CRASHING_EVALUATOR = textwrap.dedent("""\
    def evaluate(candidate_path, task_dir):
        raise RuntimeError("Evaluator deliberately crashed")
""")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSandboxEvaluatorSuccess:
    """Tests for successful evaluator execution."""

    def test_passing_evaluator_returns_score(self, tmp_path: Path) -> None:
        """A well-behaved evaluator should return a valid EvaluationResult with score."""
        task_dir = tmp_path / "task"
        task_config = _write_task_dir(task_dir, PASSING_EVALUATOR)

        sandbox = SandboxEvaluator(timeout_seconds=30)
        result = sandbox.evaluate(
            candidate_content="def add(a, b): return a + b\n",
            task_config=task_config,
            candidate_id="test-001",
            output_dir=tmp_path / "candidates",
        )

        assert result.score == pytest.approx(0.85)
        assert result.passed is True
        assert result.error is None

    def test_passing_evaluator_summary_present(self, tmp_path: Path) -> None:
        """The result summary from a passing evaluator should be non-empty."""
        task_dir = tmp_path / "task"
        task_config = _write_task_dir(task_dir, PASSING_EVALUATOR)

        sandbox = SandboxEvaluator(timeout_seconds=30)
        result = sandbox.evaluate(
            candidate_content="x = 1\n",
            task_config=task_config,
            candidate_id="test-002",
            output_dir=tmp_path / "candidates",
        )

        assert result.summary  # non-empty string


class TestSandboxEvaluatorTimeout:
    """Tests for timeout handling."""

    def test_timeout_returns_timeout_result(self, tmp_path: Path) -> None:
        """An evaluator that exceeds the timeout should return a timed-out result."""
        task_dir = tmp_path / "task"
        task_config = _write_task_dir(task_dir, SLEEPING_EVALUATOR)

        sandbox = SandboxEvaluator(timeout_seconds=2)
        result = sandbox.evaluate(
            candidate_content="def f(): pass\n",
            task_config=task_config,
            candidate_id="test-timeout",
            output_dir=tmp_path / "candidates",
        )

        assert result.passed is False
        assert result.score is None
        assert "timeout" in (result.error or "").lower() or "timed out" in (result.summary or "").lower()


class TestSandboxEvaluatorCrash:
    """Tests for evaluator crash handling."""

    def test_crashing_evaluator_returns_error_result(self, tmp_path: Path) -> None:
        """An evaluator that raises an exception should return a failed result, not crash the host."""
        task_dir = tmp_path / "task"
        task_config = _write_task_dir(task_dir, CRASHING_EVALUATOR)

        sandbox = SandboxEvaluator(timeout_seconds=30)
        result = sandbox.evaluate(
            candidate_content="def f(): pass\n",
            task_config=task_config,
            candidate_id="test-crash",
            output_dir=tmp_path / "candidates",
        )

        assert result.passed is False
        assert result.score is None
        # The error should mention the crash somehow
        combined = (result.error or "") + (result.summary or "") + (result.stdout or "")
        assert "crash" in combined.lower() or "RuntimeError" in combined or "exited" in combined.lower()

    def test_crashing_evaluator_does_not_raise(self, tmp_path: Path) -> None:
        """SandboxEvaluator must not let evaluator exceptions propagate to the caller."""
        task_dir = tmp_path / "task"
        task_config = _write_task_dir(task_dir, CRASHING_EVALUATOR)

        sandbox = SandboxEvaluator(timeout_seconds=30)

        # This should NOT raise — the crash is caught inside the sandbox.
        result = sandbox.evaluate(
            candidate_content="pass\n",
            task_config=task_config,
            candidate_id="test-no-raise",
            output_dir=tmp_path / "candidates",
        )

        assert isinstance(result.passed, bool)
