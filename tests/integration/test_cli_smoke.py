"""Integration tests for the autoevolve CLI.

These tests invoke the CLI via subprocess to verify that the top-level
entry point works end-to-end without importing internals directly.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

# Resolve project root so we can reference examples/ reliably.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_TASK = PROJECT_ROOT / "examples" / "01_text_compression_poem" / "task.yaml"


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    """Helper: invoke ``python -m autoevolve`` with *args* and return the result."""
    cmd = [sys.executable, "-m", "autoevolve", *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd or str(PROJECT_ROOT),
        timeout=60,
    )


class TestCliHelp:
    """Verify --help and top-level subcommand listing."""

    def test_help_returns_zero(self) -> None:
        result = _run_cli("--help")
        assert result.returncode == 0, result.stderr

    def test_help_shows_subcommands(self) -> None:
        result = _run_cli("--help")
        output = result.stdout
        for subcommand in ("run", "resume", "inspect", "validate-task", "list-examples"):
            assert subcommand in output, (
                f"Expected subcommand '{subcommand}' in help output:\n{output}"
            )


class TestValidateTask:
    """Verify the validate-task subcommand."""

    def test_validate_example_task(self) -> None:
        result = _run_cli("validate-task", "--task", str(EXAMPLE_TASK))
        assert result.returncode == 0, result.stderr
        assert "valid" in result.stdout.lower(), result.stdout

    def test_validate_nonexistent_task_fails(self) -> None:
        result = _run_cli("validate-task", "--task", "nonexistent/task.yaml")
        assert result.returncode != 0


class TestListExamples:
    """Verify the list-examples subcommand."""

    def test_list_examples_returns_zero(self) -> None:
        result = _run_cli("list-examples")
        assert result.returncode == 0, result.stderr

    def test_list_examples_shows_examples(self) -> None:
        result = _run_cli("list-examples")
        output = result.stdout
        # We expect at least one example to be listed
        assert "Name:" in output, f"Expected example listing in output:\n{output}"
