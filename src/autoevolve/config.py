"""Task configuration parsing and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from autoevolve.errors import TaskValidationError
from autoevolve.models import (
    BudgetConfig,
    MutatorConfig,
    OutputConfig,
    StrategyConfig,
    SwarmConfig,
    TaskConfig,
)

REQUIRED_TOP_LEVEL_KEYS = {"name", "artifact_type", "artifact_path", "evaluator_path"}
VALID_ARTIFACT_TYPES = {"python_code", "prompt_text"}
VALID_STRATEGY_TYPES = {"beam", "beam_archive", "swarm"}
VALID_PROVIDER_TYPES = {"mock", "anthropic", "openai", "ollama", "external_command"}
VALID_MUTATION_MODES = {"rewrite", "patch", "nl_feedback"}


def parse_task_yaml(path: Path) -> dict[str, Any]:
    """Read and parse a task YAML file.

    Args:
        path: Path to the task.yaml file.

    Returns:
        Parsed YAML as a dictionary.

    Raises:
        TaskValidationError: If the file cannot be read or parsed.
    """
    if not path.is_file():
        raise TaskValidationError(f"Task file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise TaskValidationError(f"Invalid YAML in {path}: {e}")

    if not isinstance(data, dict):
        raise TaskValidationError(f"Task file must contain a YAML mapping, got {type(data).__name__}")

    return data


def validate_task_config(config: dict[str, Any], task_dir: Path) -> list[str]:
    """Validate a task configuration dictionary.

    Args:
        config: Parsed YAML data.
        task_dir: Directory containing the task file (for path resolution).

    Returns:
        List of error messages. Empty list means valid.
    """
    errors = []

    # Check required keys
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in config:
            errors.append(f"Missing required field: '{key}'")

    # Validate artifact type
    artifact_type = config.get("artifact_type", "")
    if artifact_type and artifact_type not in VALID_ARTIFACT_TYPES:
        errors.append(
            f"Invalid artifact_type '{artifact_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_ARTIFACT_TYPES))}"
        )

    # Validate file paths exist
    for key in ("artifact_path", "evaluator_path", "goal_path"):
        rel_path = config.get(key, "")
        if rel_path:
            full_path = task_dir / rel_path
            if not full_path.is_file():
                errors.append(f"File not found for '{key}': {full_path}")

    # Validate strategy type if present
    strategy = config.get("strategy", {})
    if isinstance(strategy, dict):
        stype = strategy.get("type", "")
        if stype and stype not in VALID_STRATEGY_TYPES:
            errors.append(
                f"Invalid strategy type '{stype}'. "
                f"Must be one of: {', '.join(sorted(VALID_STRATEGY_TYPES))}"
            )

    # Validate provider if present
    mutator = config.get("mutator", {})
    if isinstance(mutator, dict):
        provider = mutator.get("provider", "")
        if provider and provider not in VALID_PROVIDER_TYPES:
            errors.append(
                f"Invalid provider '{provider}'. "
                f"Must be one of: {', '.join(sorted(VALID_PROVIDER_TYPES))}"
            )
        mode = mutator.get("mode", "")
        if mode and mode not in VALID_MUTATION_MODES:
            errors.append(
                f"Invalid mutation mode '{mode}'. "
                f"Must be one of: {', '.join(sorted(VALID_MUTATION_MODES))}"
            )

    # Validate dataset path if specified
    dataset_path = config.get("dataset_path", "")
    if dataset_path:
        full_path = task_dir / dataset_path
        if not full_path.is_file():
            errors.append(f"Dataset file not found: {full_path}")

    return errors


def build_task_config(yaml_dict: dict[str, Any], task_dir: Path) -> TaskConfig:
    """Build a TaskConfig from parsed YAML data.

    Args:
        yaml_dict: Parsed and validated YAML data.
        task_dir: Directory containing the task file.

    Returns:
        A fully initialized TaskConfig.
    """
    strategy_data = yaml_dict.get("strategy", {}) or {}
    mutator_data = yaml_dict.get("mutator", {}) or {}
    swarm_data = yaml_dict.get("swarm", {}) or {}
    budget_data = yaml_dict.get("budget", {}) or {}
    output_data = yaml_dict.get("output", {}) or {}

    return TaskConfig(
        name=yaml_dict["name"],
        artifact_type=yaml_dict["artifact_type"],
        artifact_path=yaml_dict["artifact_path"],
        goal_path=yaml_dict.get("goal_path", "goal.md"),
        evaluator_path=yaml_dict["evaluator_path"],
        task_dir=task_dir,
        strategy=StrategyConfig(**{k: v for k, v in strategy_data.items() if k in StrategyConfig.__dataclass_fields__}),
        mutator=MutatorConfig(**{k: v for k, v in mutator_data.items() if k in MutatorConfig.__dataclass_fields__}),
        swarm=SwarmConfig(**{k: v for k, v in swarm_data.items() if k in SwarmConfig.__dataclass_fields__}),
        budget=BudgetConfig(**{k: v for k, v in budget_data.items() if k in BudgetConfig.__dataclass_fields__}),
        output=OutputConfig(**{k: v for k, v in output_data.items() if k in OutputConfig.__dataclass_fields__}),
        dataset_path=yaml_dict.get("dataset_path"),
    )
