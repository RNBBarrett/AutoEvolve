"""JSONL event logging."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from autoevolve.utils.files import append_jsonl


class JsonlLogger:
    """Appends structured events to events.jsonl."""

    def __init__(self, events_path: Path) -> None:
        self.events_path = events_path

    def log_event(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        """Log a single event.

        Args:
            event_type: Type of event (e.g., 'run_started', 'candidate_evaluated').
            data: Additional event data.
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            **(data or {}),
        }
        append_jsonl(self.events_path, record)
