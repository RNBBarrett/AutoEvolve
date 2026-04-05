"""Main evolution loop — the core orchestrator for autoevolve runs."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from autoevolve.artifacts.base import get_artifact_handler
from autoevolve.engine.run_context import RunContext, create_run_context
from autoevolve.engine.selection import select_survivors
from autoevolve.evaluation.runner import EvaluationRunner
from autoevolve.lineage import LineageTracker
from autoevolve.models import Candidate, EvaluationResult, RunState, TaskConfig
from autoevolve.reporting.summary import write_final_summary
from autoevolve.strategies.base import create_strategy
from autoevolve.utils.files import read_jsonl, read_text, write_json
from autoevolve.utils.hashing import candidate_id


def run_evolution(task_config: TaskConfig, run_name: str | None = None) -> RunState:
    """Run a full evolutionary optimization.

    Args:
        task_config: Validated task configuration.
        run_name: Optional override for the run directory name.

    Returns:
        Final RunState with results.
    """
    ctx = create_run_context(task_config, run_name=run_name)

    ctx.console.report_run_start(task_config)
    ctx.emit_event("run_started", {
        "task": task_config.name,
        "strategy": task_config.strategy.type,
        "provider": task_config.mutator.provider,
    })

    try:
        # Evaluate baseline
        baseline = _evaluate_baseline(task_config, ctx)
        parents = [baseline]

        # Initialize best from baseline
        if baseline.score is not None:
            ctx.run_state.best_score = baseline.score
            ctx.run_state.best_candidate_id = baseline.id
            _save_best_candidate(baseline, task_config, ctx)

        # Run generations
        strategy = create_strategy(task_config.strategy.type)

        for gen in range(task_config.strategy.generations):
            if ctx.budget.is_budget_exceeded():
                ctx.emit_event("budget_exceeded", {
                    "generation": gen,
                    "elapsed": ctx.budget.elapsed_seconds(),
                    "candidates": ctx.budget.candidates_evaluated,
                })
                break

            ctx.console.report_generation_start(gen, task_config.strategy.generations)
            ctx.emit_event("generation_started", {"generation": gen})

            # Run strategy for this generation
            candidates = strategy.run_generation(gen, parents, ctx)

            # Record all candidates
            for c in candidates:
                ctx.archive.add(c)
                ctx.lineage.record(c)
                ctx.all_candidates.append(c)
                ctx.budget.record_candidate()

                ctx.emit_event("candidate_evaluated", {
                    "candidate_id": c.id,
                    "score": c.score,
                    "status": c.status,
                    "mutation_mode": c.mutation_mode,
                    "parent_ids": c.parent_ids,
                    "generation": c.generation,
                    "content": c.content,
                    "hypothesis": c.hypothesis,
                })

            # Select survivors
            survivors = strategy.select_survivors(candidates, ctx)

            for s in survivors:
                ctx.emit_event("candidate_selected", {
                    "candidate_id": s.id,
                    "score": s.score,
                    "generation": gen,
                })

            # Update best
            scored = [c for c in candidates if c.score is not None]
            if scored:
                gen_best = max(scored, key=lambda c: c.score)
                if ctx.run_state.best_score is None or gen_best.score > ctx.run_state.best_score:
                    ctx.run_state.best_score = gen_best.score
                    ctx.run_state.best_candidate_id = gen_best.id
                    _save_best_candidate(gen_best, task_config, ctx)

            # Update run state
            ctx.run_state.current_generation = gen
            ctx.run_state.completed_generations.append(gen)
            ctx.run_state.total_candidates_evaluated = ctx.budget.candidates_evaluated

            # Report
            ctx.console.report_generation_end(gen, candidates, ctx.run_state.best_score)

            if task_config.output.write_markdown_log:
                best_candidates = ctx.archive.get_top_k(1)
                best_overall = best_candidates[0] if best_candidates else None
                ctx.markdown.write_generation(gen, candidates, survivors, best_overall)

            ctx.emit_event("generation_completed", {
                "generation": gen,
                "survivor_ids": [s.id for s in survivors],
            })

            # Save state after each generation (for resume)
            ctx.save_run_state()

            # Set parents for next generation
            parents = survivors if survivors else parents

        # Run complete
        ctx.run_state.status = "completed"
        ctx.run_state.end_time = datetime.now().isoformat()

    except Exception as e:
        ctx.run_state.status = "failed"
        ctx.run_state.end_time = datetime.now().isoformat()
        ctx.emit_event("run_failed", {"error": str(e)})
        raise

    finally:
        # Always write final state and summary
        ctx.save_run_state()

        if task_config.output.write_markdown_log:
            best_candidates = ctx.archive.get_top_k(1)
            best = best_candidates[0] if best_candidates else None
            ctx.markdown.write_footer(best, ctx.budget.candidates_evaluated)

        write_final_summary(
            ctx.run_dir, ctx.run_state, ctx.all_candidates, ctx.baseline_score
        )

        ctx.emit_event("run_completed", {
            "status": ctx.run_state.status,
            "best_score": ctx.run_state.best_score,
            "total_evaluated": ctx.run_state.total_candidates_evaluated,
        })

        ctx.console.report_run_end(
            ctx.run_state.best_score,
            ctx.run_state.best_candidate_id,
            str(ctx.run_dir),
        )

    return ctx.run_state


def resume_evolution(run_dir: Path) -> RunState:
    """Resume a previously interrupted run.

    Args:
        run_dir: Path to the existing run directory.

    Returns:
        Final RunState after the resumed run completes.
    """
    from autoevolve.errors import ResumeError

    run_json_path = run_dir / "run.json"
    events_path = run_dir / "events.jsonl"

    if not run_json_path.is_file():
        raise ResumeError(f"run.json not found in {run_dir}")

    # Load run state
    with open(run_json_path, "r", encoding="utf-8") as f:
        run_data = json.load(f)

    run_state = RunState.from_dict(run_data)
    task_config = run_state.task_config

    # Create run context pointing to existing dir
    ctx = RunContext(task_config, run_dir, run_state)

    # Reconstruct archive from events
    events = read_jsonl(events_path)
    for event in events:
        if event.get("event") == "candidate_evaluated":
            candidate = Candidate(
                id=event.get("candidate_id", ""),
                generation=event.get("generation", 0),
                parent_ids=event.get("parent_ids", []),
                content=event.get("content", ""),
                mutation_mode=event.get("mutation_mode", "unknown"),
                score=event.get("score"),
                status=event.get("status", "evaluated"),
                hypothesis=event.get("hypothesis"),
            )
            ctx.archive.add(candidate)
            ctx.lineage.record(candidate)
            ctx.all_candidates.append(candidate)

    # Reconstruct baseline score
    for event in events:
        if event.get("event") == "baseline_evaluated":
            ctx.baseline_score = event.get("score")
            break

    # Determine resume point
    completed = set(run_state.completed_generations)
    start_gen = max(completed) + 1 if completed else 0
    remaining_gens = task_config.strategy.generations - start_gen

    if remaining_gens <= 0:
        print("Run already completed all generations.")
        return run_state

    ctx.run_state.status = "running"
    ctx.console.report_run_start(task_config)
    print(f"  Resuming from generation {start_gen}...")
    ctx.emit_event("run_resumed", {"from_generation": start_gen})

    # Get current parents from top archive candidates
    parents = ctx.archive.get_top_k(task_config.strategy.beam_width)
    if not parents:
        # Reload baseline
        parents = [_evaluate_baseline(task_config, ctx)]

    strategy = create_strategy(task_config.strategy.type)

    try:
        for gen in range(start_gen, task_config.strategy.generations):
            if ctx.budget.is_budget_exceeded():
                break

            ctx.console.report_generation_start(gen, task_config.strategy.generations)
            ctx.emit_event("generation_started", {"generation": gen})

            candidates = strategy.run_generation(gen, parents, ctx)

            for c in candidates:
                ctx.archive.add(c)
                ctx.lineage.record(c)
                ctx.all_candidates.append(c)
                ctx.budget.record_candidate()

                ctx.emit_event("candidate_evaluated", {
                    "candidate_id": c.id,
                    "score": c.score,
                    "status": c.status,
                    "mutation_mode": c.mutation_mode,
                    "parent_ids": c.parent_ids,
                    "generation": c.generation,
                    "content": c.content,
                    "hypothesis": c.hypothesis,
                })

            survivors = strategy.select_survivors(candidates, ctx)

            for s in survivors:
                ctx.emit_event("candidate_selected", {
                    "candidate_id": s.id,
                    "score": s.score,
                    "generation": gen,
                })

            scored = [c for c in candidates if c.score is not None]
            if scored:
                gen_best = max(scored, key=lambda c: c.score)
                if ctx.run_state.best_score is None or gen_best.score > ctx.run_state.best_score:
                    ctx.run_state.best_score = gen_best.score
                    ctx.run_state.best_candidate_id = gen_best.id
                    _save_best_candidate(gen_best, task_config, ctx)

            ctx.run_state.current_generation = gen
            ctx.run_state.completed_generations.append(gen)
            ctx.run_state.total_candidates_evaluated += len(candidates)

            ctx.console.report_generation_end(gen, candidates, ctx.run_state.best_score)

            if task_config.output.write_markdown_log:
                best_candidates = ctx.archive.get_top_k(1)
                best_overall = best_candidates[0] if best_candidates else None
                ctx.markdown.write_generation(gen, candidates, survivors, best_overall)

            ctx.emit_event("generation_completed", {
                "generation": gen,
                "survivor_ids": [s.id for s in survivors],
            })

            ctx.save_run_state()
            parents = survivors if survivors else parents

        ctx.run_state.status = "completed"
        ctx.run_state.end_time = datetime.now().isoformat()

    except Exception as e:
        ctx.run_state.status = "failed"
        ctx.run_state.end_time = datetime.now().isoformat()
        ctx.emit_event("run_failed", {"error": str(e)})
        raise

    finally:
        ctx.save_run_state()
        write_final_summary(
            ctx.run_dir, ctx.run_state, ctx.all_candidates, ctx.baseline_score
        )
        ctx.emit_event("run_completed", {
            "status": ctx.run_state.status,
            "best_score": ctx.run_state.best_score,
        })
        ctx.console.report_run_end(
            ctx.run_state.best_score,
            ctx.run_state.best_candidate_id,
            str(ctx.run_dir),
        )

    return ctx.run_state


def _evaluate_baseline(task_config: TaskConfig, ctx: RunContext) -> Candidate:
    """Load and evaluate the baseline artifact."""
    handler = get_artifact_handler(task_config.artifact_type)
    artifact_path = task_config.task_dir / task_config.artifact_path
    content = handler.load(artifact_path)

    baseline = Candidate(
        id="baseline",
        generation=-1,
        parent_ids=[],
        content=content,
        mutation_mode="baseline",
    )

    runner = EvaluationRunner(task_config)
    runner.evaluate_candidate(baseline)

    ctx.archive.add(baseline)
    ctx.lineage.record(baseline)
    ctx.all_candidates.append(baseline)
    ctx.baseline_score = baseline.score

    ctx.emit_event("baseline_evaluated", {
        "score": baseline.score,
        "passed": baseline.passed,
    })

    score_str = f"{baseline.score:.4f}" if baseline.score is not None else "N/A"
    print(f"  Baseline score: {score_str}")

    return baseline


def _save_best_candidate(
    candidate: Candidate,
    task_config: TaskConfig,
    ctx: RunContext,
) -> None:
    """Save the best candidate artifact to the best_candidate/ directory."""
    handler = get_artifact_handler(task_config.artifact_type)
    best_dir = ctx.run_dir / "best_candidate"
    handler.save(candidate.content, best_dir / f"artifact{handler.file_extension}")
