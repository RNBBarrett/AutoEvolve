"""Unit tests for autoevolve.task_loader — loading and validating task YAML files."""

from __future__ import annotations

from pathlib import Path

import pytest

from autoevolve.errors import TaskValidationError
from autoevolve.models import TaskConfig
from autoevolve.task_loader import load_task


# ---------------------------------------------------------------------------
# Happy-path tests using conftest fixtures
# ---------------------------------------------------------------------------


class TestLoadTask:
    """Tests for ``load_task``."""

    def test_load_python_task(self, python_task_dir: Path) -> None:
        """load_task returns a valid TaskConfig for the python_code fixture."""
        config = load_task(python_task_dir / "task.yaml")

        assert isinstance(config, TaskConfig)
        assert config.name == "test_python"
        assert config.artifact_type == "python_code"

    def test_load_prompt_task(self, prompt_task_dir: Path) -> None:
        """load_task returns a valid TaskConfig for the prompt_text fixture."""
        config = load_task(prompt_task_dir / "task.yaml")

        assert isinstance(config, TaskConfig)
        assert config.name == "test_prompt"
        assert config.artifact_type == "prompt_text"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        """load_task raises TaskValidationError when the YAML file does not exist."""
        with pytest.raises(TaskValidationError, match="not found"):
            load_task(tmp_path / "does_not_exist.yaml")

    def test_resolved_paths_are_absolute(self, python_task_dir: Path) -> None:
        """The task_dir stored in the loaded config must be an absolute path."""
        config = load_task(python_task_dir / "task.yaml")

        assert config.task_dir.is_absolute()

    def test_loaded_task_dir_matches_fixture(self, python_task_dir: Path) -> None:
        """task_dir should resolve to the same directory as the fixture."""
        config = load_task(python_task_dir / "task.yaml")

        assert config.task_dir == python_task_dir.resolve()
