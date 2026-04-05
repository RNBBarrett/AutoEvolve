"""Shared pytest fixtures for the autoevolve test suite.

Provides:
- ``python_task_dir``   — path to the ``tests/fixtures/python_task/`` directory.
- ``prompt_task_dir``   — path to the ``tests/fixtures/prompt_task/`` directory.
- ``python_task_config`` — a fully loaded ``TaskConfig`` for the Python-code fixture.
- ``prompt_task_config`` — a fully loaded ``TaskConfig`` for the prompt-text fixture.
- ``tmp_output_dir``    — a fresh temporary directory (via ``tmp_path``) for test output.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autoevolve.task_loader import load_task
from autoevolve.models import TaskConfig

# ---------------------------------------------------------------------------
# Fixture directory roots
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
PYTHON_TASK_DIR = FIXTURES_DIR / "python_task"
PROMPT_TASK_DIR = FIXTURES_DIR / "prompt_task"


# ---------------------------------------------------------------------------
# Path fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def python_task_dir() -> Path:
    """Return the absolute path to the ``python_task`` fixture directory."""
    assert PYTHON_TASK_DIR.is_dir(), f"Fixture directory not found: {PYTHON_TASK_DIR}"
    return PYTHON_TASK_DIR


@pytest.fixture()
def prompt_task_dir() -> Path:
    """Return the absolute path to the ``prompt_task`` fixture directory."""
    assert PROMPT_TASK_DIR.is_dir(), f"Fixture directory not found: {PROMPT_TASK_DIR}"
    return PROMPT_TASK_DIR


# ---------------------------------------------------------------------------
# Loaded TaskConfig fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def python_task_config() -> TaskConfig:
    """Load and return the ``TaskConfig`` for the Python-code test task."""
    return load_task(PYTHON_TASK_DIR / "task.yaml")


@pytest.fixture()
def prompt_task_config() -> TaskConfig:
    """Load and return the ``TaskConfig`` for the prompt-text test task."""
    return load_task(PROMPT_TASK_DIR / "task.yaml")


# ---------------------------------------------------------------------------
# Temporary output directory
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_output_dir(tmp_path: Path) -> Path:
    """Return a temporary directory suitable for storing test run output.

    The directory is automatically cleaned up by pytest after the test session.
    """
    out = tmp_path / "output"
    out.mkdir()
    return out
