"""Subprocess-based sandbox for evaluator execution.

This is the critical safety module. Candidate code is NEVER imported
directly into the main framework process. Evaluation always runs in
a child subprocess with timeout and output capture.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from autoevolve.evaluation.result_parser import parse_evaluation_output
from autoevolve.models import EvaluationResult, TaskConfig
from autoevolve.utils.subprocesses import run_subprocess


# Wrapper script template executed in the subprocess.
# It imports the evaluator from the task directory and calls it.
EVAL_WRAPPER_TEMPLATE = '''
import json
import sys
import pathlib

task_dir = {task_dir!r}
candidate_path = {candidate_path!r}

sys.path.insert(0, task_dir)

try:
    from evaluator import evaluate
    result = evaluate(candidate_path, task_dir)
    if not isinstance(result, dict):
        result = {{"score": None, "passed": False, "error": "Evaluator did not return a dict"}}
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{
        "score": None,
        "passed": False,
        "error": str(e),
        "summary": "Evaluator crashed"
    }}))
    sys.exit(1)
'''


class SandboxEvaluator:
    """Runs evaluators in isolated subprocesses with timeout."""

    def __init__(self, timeout_seconds: int = 10) -> None:
        self.timeout_seconds = timeout_seconds

    def evaluate(
        self,
        candidate_content: str,
        task_config: TaskConfig,
        candidate_id: str,
        output_dir: Path | None = None,
    ) -> EvaluationResult:
        """Evaluate a candidate artifact in a subprocess sandbox.

        Args:
            candidate_content: The candidate artifact text.
            task_config: Task configuration for paths and settings.
            candidate_id: Identifier for the candidate (used in file naming).
            output_dir: Optional directory to write the candidate file.
                        If None, a temporary directory is used.

        Returns:
            Structured EvaluationResult.
        """
        from autoevolve.artifacts.base import get_artifact_handler

        artifact_handler = get_artifact_handler(task_config.artifact_type)
        task_dir = str(task_config.task_dir)

        # Write candidate to a file
        if output_dir:
            candidate_path = (output_dir / f"{candidate_id}{artifact_handler.file_extension}").resolve()
            artifact_handler.save(candidate_content, candidate_path)
        else:
            suffix = artifact_handler.file_extension
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=suffix, delete=False, encoding="utf-8", dir=task_dir
            ) as f:
                f.write(candidate_content)
                candidate_path = Path(f.name)

        # Write the wrapper script
        wrapper_code = EVAL_WRAPPER_TEMPLATE.format(
            task_dir=task_dir,
            candidate_path=str(candidate_path),
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(wrapper_code)
            wrapper_path = f.name

        try:
            # Run the evaluator in a subprocess
            result = run_subprocess(
                [sys.executable, wrapper_path],
                timeout=self.timeout_seconds,
                cwd=Path(task_dir),
                capture=True,
            )

            if result.timed_out:
                return EvaluationResult(
                    score=None,
                    passed=False,
                    summary=f"Evaluation timed out after {self.timeout_seconds}s",
                    error=f"Timeout after {self.timeout_seconds}s",
                    stdout=result.stdout,
                    stderr=result.stderr,
                    duration_seconds=result.duration_seconds,
                )

            return parse_evaluation_output(
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                duration=result.duration_seconds,
            )
        finally:
            # Clean up wrapper script (but keep candidate file for inspection)
            Path(wrapper_path).unlink(missing_ok=True)
            # Clean up temp candidate if we created one
            if not output_dir:
                candidate_path.unlink(missing_ok=True)
