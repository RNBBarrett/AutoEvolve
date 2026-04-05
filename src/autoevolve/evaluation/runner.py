"""High-level evaluation orchestration."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from autoevolve.evaluation.sandbox import SandboxEvaluator
from autoevolve.models import Candidate, EvaluationResult, TaskConfig


class EvaluationRunner:
    """Evaluates candidates using the sandbox evaluator."""

    def __init__(self, task_config: TaskConfig) -> None:
        self.task_config = task_config
        self.sandbox = SandboxEvaluator(
            timeout_seconds=task_config.budget.eval_timeout_seconds
        )

    def evaluate_candidate(
        self,
        candidate: Candidate,
        output_dir: Path | None = None,
    ) -> Candidate:
        """Evaluate a single candidate and update it with results.

        Args:
            candidate: The candidate to evaluate.
            output_dir: Optional directory to write the candidate artifact.

        Returns:
            The same candidate, updated with score, status, and metrics.
        """
        result = self.sandbox.evaluate(
            candidate_content=candidate.content,
            task_config=self.task_config,
            candidate_id=candidate.id,
            output_dir=output_dir,
        )

        candidate.score = result.score
        candidate.passed = result.passed
        candidate.metrics = result.metrics
        candidate.error = result.error
        candidate.evaluated_at = datetime.now().isoformat()

        if result.error and result.score is None:
            candidate.status = "failed"
        else:
            candidate.status = "evaluated"

        return candidate

    def evaluate_candidates(
        self,
        candidates: list[Candidate],
        output_dir: Path | None = None,
    ) -> list[Candidate]:
        """Evaluate a list of candidates sequentially.

        Args:
            candidates: Candidates to evaluate.
            output_dir: Optional directory for candidate artifacts.

        Returns:
            The same candidates, updated with evaluation results.
        """
        for candidate in candidates:
            self.evaluate_candidate(candidate, output_dir=output_dir)
        return candidates
