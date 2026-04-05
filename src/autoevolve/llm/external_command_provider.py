"""External command provider for integrating shell-based tools and agents."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from autoevolve.errors import ProviderError
from autoevolve.llm.base import Provider
from autoevolve.utils.subprocesses import run_subprocess


class ExternalCommandProvider(Provider):
    """Provider that executes an external command to generate responses.

    Supports two modes:
    - 'tempfile' (default): Writes prompt to a temp file, passes path as argument
    - 'stdin': Pipes prompt to the command's stdin
    """

    def __init__(self, command: str, mode: str = "tempfile") -> None:
        if not command:
            raise ProviderError(
                "External command provider requires a command. "
                "Set 'external_command' in task.yaml or "
                "AUTOEVOLVE_EXTERNAL_CMD environment variable."
            )
        self.command = command
        self.mode = mode

    def generate(self, prompt: str, *, metadata: dict[str, Any] | None = None) -> str:
        """Generate by running the external command."""
        import os
        cmd = os.environ.get("AUTOEVOLVE_EXTERNAL_CMD", self.command)

        if self.mode == "stdin":
            return self._generate_stdin(cmd, prompt)
        else:
            return self._generate_tempfile(cmd, prompt)

    def _generate_tempfile(self, command: str, prompt: str) -> str:
        """Write prompt to temp file and pass path as argument."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(prompt)
            temp_path = f.name

        try:
            result = run_subprocess(
                [command, temp_path],
                timeout=120,
                capture=True,
            )
            if result.returncode != 0:
                raise ProviderError(
                    f"External command failed (exit {result.returncode}): {result.stderr}"
                )
            return result.stdout.strip()
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def _generate_stdin(self, command: str, prompt: str) -> str:
        """Pipe prompt to command's stdin."""
        import subprocess

        try:
            result = subprocess.run(
                [command],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                raise ProviderError(
                    f"External command failed (exit {result.returncode}): {result.stderr}"
                )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise ProviderError("External command timed out after 120s")
        except FileNotFoundError:
            raise ProviderError(f"External command not found: {command}")
