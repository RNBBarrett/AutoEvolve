"""Prompt text artifact type."""

from __future__ import annotations

from pathlib import Path

from autoevolve.artifacts.base import Artifact
from autoevolve.errors import ArtifactError


class PromptTextArtifact(Artifact):
    """Handles prompt text artifacts (.txt files)."""

    artifact_type = "prompt_text"
    file_extension = ".txt"

    def load(self, path: Path) -> str:
        """Load prompt text from a file."""
        path = Path(path)
        if not path.is_file():
            raise ArtifactError(f"Prompt artifact not found: {path}")
        return path.read_text(encoding="utf-8")

    def save(self, content: str, path: Path) -> Path:
        """Save prompt text to a .txt file."""
        path = Path(path)
        if path.is_dir():
            path = path / f"artifact{self.file_extension}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def validate(self, content: str) -> bool:
        """Validate that the content is non-empty text."""
        return bool(content and content.strip())
