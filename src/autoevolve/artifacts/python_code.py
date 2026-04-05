"""Python code artifact type."""

from __future__ import annotations

from pathlib import Path

from autoevolve.artifacts.base import Artifact
from autoevolve.errors import ArtifactError


class PythonCodeArtifact(Artifact):
    """Handles Python source code artifacts (.py files)."""

    artifact_type = "python_code"
    file_extension = ".py"

    def load(self, path: Path) -> str:
        """Load Python source code from a file."""
        path = Path(path)
        if not path.is_file():
            raise ArtifactError(f"Python artifact not found: {path}")
        return path.read_text(encoding="utf-8")

    def save(self, content: str, path: Path) -> Path:
        """Save Python source code to a .py file."""
        path = Path(path)
        if path.is_dir():
            path = path / f"artifact{self.file_extension}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def validate(self, content: str) -> bool:
        """Validate that the content is syntactically valid Python.

        Uses compile() to check for syntax errors.
        """
        try:
            compile(content, "<candidate>", "exec")
            return True
        except SyntaxError:
            return False
