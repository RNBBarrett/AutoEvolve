"""Core data models for autoevolve.

All models use standard library dataclasses for simplicity and minimal dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class StrategyConfig:
    """Configuration for the search strategy."""

    type: str = "beam_archive"
    generations: int = 8
    beam_width: int = 2
    children_per_parent: int = 3
    crossover_enabled: bool = True
    archive_top_k: int = 5
    archive_diverse_k: int = 3
    archive_recent_k: int = 3


@dataclass
class MutatorConfig:
    """Configuration for candidate mutation."""

    provider: str = "mock"
    mode: str = "rewrite"
    model: str = "mock-deterministic"
    temperature: float = 0.2
    max_candidates_per_call: int = 1
    external_command: str | None = None
    external_command_mode: str = "tempfile"


@dataclass
class SwarmConfig:
    """Configuration for swarm mode."""

    enabled: bool = False
    mutation_agents: int = 4
    use_critic: bool = True
    use_diversity_agent: bool = True
    max_concurrent_calls: int = 4


@dataclass
class BudgetConfig:
    """Budget limits for a run."""

    max_total_candidates: int = 50
    max_runtime_seconds: int = 600
    eval_timeout_seconds: int = 10


@dataclass
class OutputConfig:
    """Configuration for run output."""

    save_all_candidates: bool = True
    write_markdown_log: bool = True
    write_jsonl_events: bool = True


@dataclass
class TaskConfig:
    """Complete configuration for an optimization task."""

    name: str
    artifact_type: str
    artifact_path: str
    goal_path: str
    evaluator_path: str
    task_dir: Path
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    mutator: MutatorConfig = field(default_factory=MutatorConfig)
    swarm: SwarmConfig = field(default_factory=SwarmConfig)
    budget: BudgetConfig = field(default_factory=BudgetConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    dataset_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dictionary."""
        d = asdict(self)
        d["task_dir"] = str(self.task_dir)
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TaskConfig:
        """Deserialize from a dictionary."""
        d = dict(d)  # shallow copy
        d["task_dir"] = Path(d["task_dir"])
        d["strategy"] = StrategyConfig(**d.get("strategy", {}))
        d["mutator"] = MutatorConfig(**d.get("mutator", {}))
        d["swarm"] = SwarmConfig(**d.get("swarm", {}))
        d["budget"] = BudgetConfig(**d.get("budget", {}))
        d["output"] = OutputConfig(**d.get("output", {}))
        return cls(**d)


@dataclass
class Candidate:
    """Represents one generated artifact version."""

    id: str
    generation: int
    parent_ids: list[str]
    content: str
    mutation_mode: str
    hypothesis: str | None = None
    score: float | None = None
    passed: bool | None = None
    status: str = "pending"  # pending | evaluated | failed | selected
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    created_at: str = ""
    evaluated_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Candidate:
        """Deserialize from a dictionary."""
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class EvaluationResult:
    """Structured result from evaluating a candidate."""

    score: float | None
    passed: bool
    metrics: dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    error: str | None = None
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dictionary."""
        return asdict(self)


@dataclass
class RunState:
    """Persistent state for a run, written to run.json after each generation."""

    run_id: str
    task_config: TaskConfig
    status: str  # running | completed | failed | interrupted
    start_time: str
    run_dir: str = ""
    end_time: str | None = None
    current_generation: int = 0
    total_candidates_evaluated: int = 0
    best_score: float | None = None
    best_candidate_id: str | None = None
    completed_generations: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dictionary."""
        d = asdict(self)
        d["task_config"] = self.task_config.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RunState:
        """Deserialize from a dictionary."""
        d = dict(d)
        d["task_config"] = TaskConfig.from_dict(d["task_config"])
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
