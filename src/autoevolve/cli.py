"""Command-line interface for autoevolve."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from autoevolve.version import __version__


def main(argv: list[str] | None = None) -> None:
    """Entry point for the autoevolve CLI."""
    parser = argparse.ArgumentParser(
        prog="autoevolve",
        description="A general-purpose evolutionary optimization framework using LLMs.",
    )
    parser.add_argument(
        "--version", action="version", version=f"autoevolve {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- run ---
    run_parser = subparsers.add_parser("run", help="Run an evolutionary optimization task")
    run_parser.add_argument("--task", required=True, help="Path to task.yaml")
    run_parser.add_argument("--strategy", help="Override strategy type (beam, beam_archive, swarm)")
    run_parser.add_argument("--provider", help="Override LLM provider (mock, anthropic, openai, ollama, external_command)")
    run_parser.add_argument("--generations", type=int, help="Override number of generations")
    run_parser.add_argument("--beam-width", type=int, help="Override beam width")
    run_parser.add_argument("--run-name", help="Override run directory name")

    # --- resume ---
    resume_parser = subparsers.add_parser("resume", help="Resume a previous run")
    resume_parser.add_argument("--run-dir", required=True, help="Path to the run directory")

    # --- inspect ---
    inspect_parser = subparsers.add_parser("inspect", help="Inspect a completed run")
    inspect_parser.add_argument("--run-dir", required=True, help="Path to the run directory")

    # --- validate-task ---
    validate_parser = subparsers.add_parser("validate-task", help="Validate a task without running")
    validate_parser.add_argument("--task", required=True, help="Path to task.yaml")

    # --- list-examples ---
    subparsers.add_parser("list-examples", help="List bundled example tasks")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "run":
        _cmd_run(args)
    elif args.command == "resume":
        _cmd_resume(args)
    elif args.command == "inspect":
        _cmd_inspect(args)
    elif args.command == "validate-task":
        _cmd_validate_task(args)
    elif args.command == "list-examples":
        _cmd_list_examples(args)


def _cmd_run(args: argparse.Namespace) -> None:
    """Execute a full evolutionary optimization run."""
    from autoevolve.task_loader import load_task
    from autoevolve.engine.loop import run_evolution

    task_config = load_task(args.task)

    # Apply CLI overrides
    if args.strategy:
        task_config.strategy.type = args.strategy
        if args.strategy == "swarm":
            task_config.swarm.enabled = True
    if args.provider:
        task_config.mutator.provider = args.provider
    if args.generations is not None:
        task_config.strategy.generations = args.generations
    if args.beam_width is not None:
        task_config.strategy.beam_width = args.beam_width

    run_state = run_evolution(task_config, run_name=args.run_name)

    print(f"\nRun completed: {run_state.status}")
    if run_state.best_score is not None:
        print(f"Best score: {run_state.best_score}")
    print(f"Run directory: {run_state.run_dir}")


def _cmd_resume(args: argparse.Namespace) -> None:
    """Resume a previous run from its run directory."""
    from autoevolve.engine.loop import resume_evolution

    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        print(f"Error: Run directory not found: {run_dir}", file=sys.stderr)
        sys.exit(1)

    run_state = resume_evolution(run_dir)

    print(f"\nResumed run completed: {run_state.status}")
    if run_state.best_score is not None:
        print(f"Best score: {run_state.best_score}")
    print(f"Run directory: {run_state.run_dir}")


def _cmd_inspect(args: argparse.Namespace) -> None:
    """Print a human-readable summary of a run."""
    from autoevolve.reporting.summary import print_run_inspection

    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        print(f"Error: Run directory not found: {run_dir}", file=sys.stderr)
        sys.exit(1)

    print_run_inspection(run_dir)


def _cmd_validate_task(args: argparse.Namespace) -> None:
    """Validate a task file without running any LLM calls."""
    from autoevolve.task_loader import load_task
    from autoevolve.errors import TaskValidationError

    task_path = Path(args.task)
    if not task_path.is_file():
        print(f"Error: Task file not found: {task_path}", file=sys.stderr)
        sys.exit(1)

    try:
        task_config = load_task(args.task)
        print(f"Task '{task_config.name}' is valid.")
        print(f"  Artifact type: {task_config.artifact_type}")
        print(f"  Strategy: {task_config.strategy.type}")
        print(f"  Provider: {task_config.mutator.provider}")
        print(f"  Generations: {task_config.strategy.generations}")
        print(f"  Evaluator: {task_config.evaluator_path}")
    except TaskValidationError as e:
        print(f"Validation failed: {e}", file=sys.stderr)
        sys.exit(1)


def _cmd_list_examples(args: argparse.Namespace) -> None:
    """List bundled example tasks."""
    # Find examples relative to the package location
    package_dir = Path(__file__).resolve().parent
    examples_dir = package_dir.parent.parent / "examples"

    if not examples_dir.is_dir():
        # Try relative to working directory
        examples_dir = Path("examples")

    if not examples_dir.is_dir():
        print("No examples directory found.", file=sys.stderr)
        sys.exit(1)

    print("Bundled examples:\n")

    for example_dir in sorted(examples_dir.iterdir()):
        if not example_dir.is_dir():
            continue
        task_yaml = example_dir / "task.yaml"
        if task_yaml.is_file():
            import yaml

            with open(task_yaml, "r", encoding="utf-8") as f:
                task_data = yaml.safe_load(f)
            name = task_data.get("name", example_dir.name)
            artifact_type = task_data.get("artifact_type", "unknown")
            print(f"  {example_dir.name}/")
            print(f"    Name: {name}")
            print(f"    Type: {artifact_type}")
            print(f"    Path: {task_yaml}")
            print()
