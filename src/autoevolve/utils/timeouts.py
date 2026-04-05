"""Timeout utilities for autoevolve."""

from __future__ import annotations

import time


class BudgetTracker:
    """Track time and candidate budgets for a run."""

    def __init__(self, max_runtime_seconds: int, max_total_candidates: int) -> None:
        self.max_runtime_seconds = max_runtime_seconds
        self.max_total_candidates = max_total_candidates
        self.start_time = time.monotonic()
        self.candidates_evaluated = 0

    def record_candidate(self) -> None:
        """Record that a candidate was evaluated."""
        self.candidates_evaluated += 1

    def elapsed_seconds(self) -> float:
        """Return seconds elapsed since tracking started."""
        return time.monotonic() - self.start_time

    def is_time_exceeded(self) -> bool:
        """Check if the runtime budget has been exceeded."""
        return self.elapsed_seconds() >= self.max_runtime_seconds

    def is_candidate_limit_reached(self) -> bool:
        """Check if the candidate budget has been reached."""
        return self.candidates_evaluated >= self.max_total_candidates

    def is_budget_exceeded(self) -> bool:
        """Check if either budget limit has been exceeded."""
        return self.is_time_exceeded() or self.is_candidate_limit_reached()
