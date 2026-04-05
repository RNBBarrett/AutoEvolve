"""ID generation utilities for autoevolve."""

from __future__ import annotations

from datetime import datetime


def candidate_id(generation: int, index: int) -> str:
    """Generate a deterministic, sortable candidate ID.

    Example: candidate_id(3, 2) -> "gen003_cand002"
    """
    return f"gen{generation:03d}_cand{index:03d}"


def run_id(task_name: str, timestamp: datetime | None = None) -> str:
    """Generate a timestamped run directory name.

    Example: run_id("text_compression_poem") -> "2026-04-05_120000_text_compression_poem"
    """
    if timestamp is None:
        timestamp = datetime.now()
    ts = timestamp.strftime("%Y-%m-%d_%H%M%S")
    return f"{ts}_{task_name}"
