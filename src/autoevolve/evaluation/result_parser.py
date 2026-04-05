"""Parse evaluation subprocess output into structured results."""

from __future__ import annotations

import json

from autoevolve.models import EvaluationResult


def parse_evaluation_output(
    stdout: str,
    stderr: str,
    returncode: int,
    duration: float,
) -> EvaluationResult:
    """Parse the output of an evaluator subprocess into an EvaluationResult.

    The evaluator is expected to print a JSON object to stdout.
    If the output is not valid JSON, or the process failed, an
    appropriate error result is returned.

    Args:
        stdout: Captured stdout from the subprocess.
        stderr: Captured stderr from the subprocess.
        returncode: Process exit code.
        duration: Wall-clock execution time in seconds.

    Returns:
        An EvaluationResult.
    """
    if returncode != 0:
        return EvaluationResult(
            score=None,
            passed=False,
            summary=f"Evaluator exited with code {returncode}",
            error=stderr.strip() or f"Non-zero exit code: {returncode}",
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration,
        )

    # Try to parse JSON from stdout
    stdout_stripped = stdout.strip()
    if not stdout_stripped:
        return EvaluationResult(
            score=None,
            passed=False,
            summary="Evaluator produced no output",
            error="Empty stdout from evaluator",
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration,
        )

    try:
        data = json.loads(stdout_stripped)
    except json.JSONDecodeError as e:
        return EvaluationResult(
            score=None,
            passed=False,
            summary="Evaluator output is not valid JSON",
            error=f"JSON parse error: {e}",
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration,
        )

    if not isinstance(data, dict):
        return EvaluationResult(
            score=None,
            passed=False,
            summary="Evaluator output is not a JSON object",
            error=f"Expected dict, got {type(data).__name__}",
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration,
        )

    return EvaluationResult(
        score=data.get("score"),
        passed=bool(data.get("passed", False)),
        metrics=data.get("metrics", {}),
        summary=data.get("summary", ""),
        error=data.get("error"),
        stdout=stdout,
        stderr=stderr,
        duration_seconds=duration,
    )
