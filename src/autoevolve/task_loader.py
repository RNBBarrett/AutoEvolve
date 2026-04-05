"""Task loading and path resolution."""

from __future__ import annotations

from pathlib import Path

from autoevolve.config import build_task_config, parse_task_yaml, validate_task_config
from autoevolve.errors import TaskValidationError
from autoevolve.models import TaskConfig


def load_task(task_path: str | Path) -> TaskConfig:
    """Load and validate a task from a YAML file.

    All relative paths in the task are resolved against the task file's directory.

    Args:
        task_path: Path to the task.yaml file.

    Returns:
        A validated TaskConfig ready for execution.

    Raises:
        TaskValidationError: If the task is invalid or files are missing.
    """
    task_path = Path(task_path).resolve()
    task_dir = task_path.parent

    # Parse YAML
    yaml_dict = parse_task_yaml(task_path)

    # Validate
    errors = validate_task_config(yaml_dict, task_dir)
    if errors:
        error_list = "\n  - ".join(errors)
        raise TaskValidationError(
            f"Task validation failed for {task_path}:\n  - {error_list}"
        )

    # Build config
    config = build_task_config(yaml_dict, task_dir)

    return config
