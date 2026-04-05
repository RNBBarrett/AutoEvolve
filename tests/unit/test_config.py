"""Unit tests for autoevolve.config — YAML parsing, validation, and TaskConfig building."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from autoevolve.config import (
    build_task_config,
    parse_task_yaml,
    validate_task_config,
)
from autoevolve.errors import TaskValidationError
from autoevolve.models import TaskConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_VALID_YAML: dict = {
    "name": "unit_test_task",
    "artifact_type": "python_code",
    "artifact_path": "artifact.py",
    "goal_path": "goal.md",
    "evaluator_path": "evaluator.py",
}


def _write_yaml(path: Path, data: dict) -> Path:
    """Write *data* as YAML to *path* and return the path."""
    path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
    return path


def _create_dummy_files(directory: Path, filenames: list[str]) -> None:
    """Create empty placeholder files inside *directory*."""
    directory.mkdir(parents=True, exist_ok=True)
    for name in filenames:
        (directory / name).write_text("", encoding="utf-8")


# ---------------------------------------------------------------------------
# parse_task_yaml
# ---------------------------------------------------------------------------


class TestParseTaskYaml:
    """Tests for ``parse_task_yaml``."""

    def test_valid_yaml_file(self, tmp_path: Path) -> None:
        """parse_task_yaml returns a dict for a well-formed YAML file."""
        yaml_path = _write_yaml(tmp_path / "task.yaml", MINIMAL_VALID_YAML)

        result = parse_task_yaml(yaml_path)

        assert isinstance(result, dict)
        assert result["name"] == "unit_test_task"
        assert result["artifact_type"] == "python_code"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        """parse_task_yaml raises TaskValidationError for a nonexistent file."""
        with pytest.raises(TaskValidationError, match="not found"):
            parse_task_yaml(tmp_path / "nonexistent.yaml")


# ---------------------------------------------------------------------------
# validate_task_config
# ---------------------------------------------------------------------------


class TestValidateTaskConfig:
    """Tests for ``validate_task_config``."""

    def test_missing_required_keys(self, tmp_path: Path) -> None:
        """Each missing required key produces an error message."""
        _create_dummy_files(tmp_path, ["artifact.py", "evaluator.py", "goal.md"])

        # Provide only the artifact_type — name, artifact_path, evaluator_path are missing.
        incomplete = {"artifact_type": "python_code"}
        errors = validate_task_config(incomplete, tmp_path)

        # All three missing keys should be reported.
        missing_keys = {"name", "artifact_path", "evaluator_path"}
        for key in missing_keys:
            assert any(key in e for e in errors), f"Expected error for missing '{key}'"

    def test_invalid_artifact_type(self, tmp_path: Path) -> None:
        """An unrecognised artifact_type is flagged."""
        _create_dummy_files(tmp_path, ["artifact.py", "evaluator.py", "goal.md"])

        config = {**MINIMAL_VALID_YAML, "artifact_type": "csv_table"}
        errors = validate_task_config(config, tmp_path)

        assert any("artifact_type" in e and "csv_table" in e for e in errors)

    def test_invalid_strategy_type(self, tmp_path: Path) -> None:
        """An unrecognised strategy type is flagged."""
        _create_dummy_files(tmp_path, ["artifact.py", "evaluator.py", "goal.md"])

        config = {**MINIMAL_VALID_YAML, "strategy": {"type": "random_walk"}}
        errors = validate_task_config(config, tmp_path)

        assert any("strategy" in e.lower() and "random_walk" in e for e in errors)

    def test_invalid_provider_type(self, tmp_path: Path) -> None:
        """An unrecognised mutator provider is flagged."""
        _create_dummy_files(tmp_path, ["artifact.py", "evaluator.py", "goal.md"])

        config = {**MINIMAL_VALID_YAML, "mutator": {"provider": "gemini"}}
        errors = validate_task_config(config, tmp_path)

        assert any("provider" in e.lower() and "gemini" in e for e in errors)

    def test_valid_config_returns_no_errors(self, tmp_path: Path) -> None:
        """A fully valid configuration produces an empty error list."""
        _create_dummy_files(tmp_path, ["artifact.py", "evaluator.py", "goal.md"])

        errors = validate_task_config(MINIMAL_VALID_YAML, tmp_path)

        assert errors == []


# ---------------------------------------------------------------------------
# build_task_config
# ---------------------------------------------------------------------------


class TestBuildTaskConfig:
    """Tests for ``build_task_config``."""

    def test_produces_valid_task_config(self, tmp_path: Path) -> None:
        """build_task_config returns a TaskConfig with the correct fields."""
        task_dir = tmp_path / "task"
        task_dir.mkdir()

        config = build_task_config(MINIMAL_VALID_YAML, task_dir)

        assert isinstance(config, TaskConfig)
        assert config.name == "unit_test_task"
        assert config.artifact_type == "python_code"
        assert config.task_dir == task_dir
        # Defaults should be filled in for nested configs.
        assert config.strategy.type == "beam_archive"
        assert config.mutator.provider == "mock"

    def test_strategy_overrides_applied(self, tmp_path: Path) -> None:
        """build_task_config respects strategy overrides from YAML."""
        task_dir = tmp_path / "task"
        task_dir.mkdir()

        yaml_dict = {
            **MINIMAL_VALID_YAML,
            "strategy": {"type": "beam", "generations": 5},
        }
        config = build_task_config(yaml_dict, task_dir)

        assert config.strategy.type == "beam"
        assert config.strategy.generations == 5
