# autoevolve Architecture Guide

This document is written for implementers who want to understand, extend, or debug
autoevolve. It covers every major module, explains how data flows through the system,
and provides step-by-step instructions for adding new artifact types, strategies, and
LLM providers.

---

## Table of Contents

1. [High-Level Overview](#high-level-overview)
2. [Module Responsibilities](#module-responsibilities)
3. [Data Flow](#data-flow)
4. [Run Lifecycle](#run-lifecycle)
5. [Archive Retrieval](#archive-retrieval)
6. [How Providers Plug In](#how-providers-plug-in)
7. [How to Add a New Artifact Type](#how-to-add-a-new-artifact-type)
8. [How to Add a New Strategy](#how-to-add-a-new-strategy)
9. [How Resume Works](#how-resume-works)

---

## High-Level Overview

autoevolve is an evolutionary optimization framework that uses LLMs as intelligent
mutation operators. You define a **task** (an artifact to optimize, a goal description,
and an evaluator script), and autoevolve iteratively generates improved candidates by
asking an LLM to mutate, rewrite, or recombine prior attempts. Each candidate is
scored by the evaluator in a sandboxed subprocess, and the best candidates survive
to become parents of the next generation.

```
                         +------------------+
                         |   task.yaml      |
                         | (configuration)  |
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         |   TaskLoader     |
                         | (parse, validate)|
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         |   TaskConfig     |
                         | (dataclass)      |
                         +--------+---------+
                                  |
                                  v
                       +---------------------+
                       |   Engine Loop       |
                       |   (loop.py)         |
                       |                     |
                       |  for each gen:      |
                       |   Strategy          |
                       |    -> Mutators      |
                       |      -> LLM        |
                       |    -> Evaluator    |
                       |    -> Selection    |
                       |    -> Archive      |
                       +----------+----------+
                                  |
                                  v
                       +---------------------+
                       |   Run Directory     |
                       | run.json            |
                       | events.jsonl        |
                       | log.md              |
                       | best_candidate/     |
                       | generations/        |
                       | summaries/          |
                       +---------------------+
```

---

## Module Responsibilities

### Core Modules (`src/autoevolve/`)

| Module | File(s) | Responsibility |
|--------|---------|----------------|
| **CLI** | `cli.py` | Argparse-based entry point with `run`, `resume`, `inspect`, `validate-task`, and `list-examples` subcommands. Applies CLI overrides to `TaskConfig`. |
| **Config** | `config.py` | Parses `task.yaml` with PyYAML, validates required fields and allowed values, builds `TaskConfig`. |
| **Task Loader** | `task_loader.py` | High-level facade: resolves paths relative to the task directory, calls config parsing and validation, returns a ready-to-use `TaskConfig`. |
| **Models** | `models.py` | Pure dataclasses: `TaskConfig`, `StrategyConfig`, `MutatorConfig`, `SwarmConfig`, `BudgetConfig`, `OutputConfig`, `Candidate`, `EvaluationResult`, `RunState`. All have `to_dict()` / `from_dict()` for JSON serialization. |
| **Errors** | `errors.py` | Exception hierarchy rooted at `AutoEvolveError`. Subclasses: `TaskValidationError`, `EvaluatorError`, `ProviderError`, `ResumeError`, `SandboxTimeoutError`, `ArtifactError`. |
| **Prompt Builder** | `prompt_builder.py` | Centralized prompt templates for mutation, crossover, critic, and diversity operations. Uses `ARTIFACT_START` / `ARTIFACT_END` delimiters. Parses `HYPOTHESIS:` lines from LLM responses. |
| **Lineage** | `lineage.py` | `LineageTracker` records parent-child relationships between candidates. Supports ancestor/descendant traversal and serialization. Reconstructed during resume from event replay. |

### Artifacts (`artifacts/`)

| Module | Responsibility |
|--------|----------------|
| `base.py` | Abstract `Artifact` base class with `load()`, `save()`, `validate()`. Factory function `get_artifact_handler()` maps type strings to implementations. |
| `python_code.py` | `PythonCodeArtifact` -- loads/saves `.py` files, validates with `compile()`. |
| `prompt_text.py` | `PromptTextArtifact` -- loads/saves `.txt` files, validates non-empty content. |

### Archive (`archive/`)

| Module | Responsibility |
|--------|----------------|
| `base.py` | Abstract `Archive` base class defining `add()`, `get_top_k()`, `get_recent_k()`, `get_diverse_k()`, `get_all()`, `size()`. |
| `in_memory.py` | `InMemoryArchive` -- stores all evaluated candidates in a list. Delegates retrieval to selector functions. |
| `selectors.py` | Pure functions: `select_top_k` (sort by score), `select_recent_k` (sort by creation time), `select_diverse_k` (greedy max-min distance using `difflib` similarity). |

### Engine (`engine/`)

| Module | Responsibility |
|--------|----------------|
| `loop.py` | **The main orchestrator.** Contains `run_evolution()` (fresh runs) and `resume_evolution()` (resumed runs). Drives the generational loop, coordinates baseline evaluation, strategy execution, archive updates, survivor selection, event emission, and state persistence. |
| `run_context.py` | `RunContext` bundles all per-run state: archive, lineage tracker, budget tracker, reporters (console, JSONL, markdown), candidate list, and baseline score. `create_run_context()` sets up the run directory structure. |
| `generation.py` | `generate_candidates()` -- builds `MutationContext` with archive exemplars, creates a provider, and calls the mutator for each parent x `children_per_parent`. |
| `selection.py` | `select_survivors()` -- beam selection by score. `select_parents_for_crossover()` -- pairs top candidates for crossover. |

### Evaluation (`evaluation/`)

| Module | Responsibility |
|--------|----------------|
| `sandbox.py` | `SandboxEvaluator` -- writes the candidate artifact to a file, generates a wrapper Python script, runs it in a **child subprocess** with a timeout. Candidate code is **never** imported into the main process. |
| `runner.py` | `EvaluationRunner` -- high-level interface that wraps `SandboxEvaluator` and updates `Candidate` fields (score, status, metrics) after evaluation. |
| `result_parser.py` | `parse_evaluation_output()` -- parses JSON from evaluator subprocess stdout into an `EvaluationResult`. Handles non-zero exit codes, empty output, and malformed JSON gracefully. |

### LLM Providers (`llm/`)

| Module | Responsibility |
|--------|----------------|
| `base.py` | Abstract `Provider` base class with `generate()` (sync) and `agenerate()` (async, default uses `run_in_executor`). Factory `create_provider()` maps names to implementations. |
| `mock_provider.py` | Deterministic mock for testing -- no API calls. |
| `anthropic_provider.py` | Anthropic API (Claude models). |
| `openai_provider.py` | OpenAI API (GPT models). |
| `ollama_provider.py` | Local Ollama API. |
| `external_command_provider.py` | Shells out to an arbitrary CLI command. |

### Mutators (`mutators/`)

| Module | Responsibility |
|--------|----------------|
| `base.py` | Abstract `Mutator` base class with `mutate()` (sync) and `amutate()` (async). `MutationContext` dataclass bundles goal, provider, archive exemplars, and best candidate. Factory `create_mutator()` maps mode names to implementations. |
| `rewrite.py` | `RewriteMutator` -- asks the LLM to produce a complete improved version. |
| `patch.py` | `PatchMutator` -- asks the LLM for a focused, targeted fix. |
| `nl_feedback.py` | `NLFeedbackMutator` -- feeds prior scores and hypotheses back as natural-language optimization context. |
| `crossover.py` | `CrossoverMutator` -- combines two parent candidates via `build_crossover_prompt`. Has `mutate_pair()` for two-parent recombination. |

### Strategies (`strategies/`)

| Module | Responsibility |
|--------|----------------|
| `base.py` | Abstract `Strategy` base class with `run_generation()` and `select_survivors()`. Factory `create_strategy()` maps type strings to implementations. |
| `beam.py` | `BeamStrategy` -- for each generation: mutate parents, optionally crossover, evaluate, select top beam_width. |
| `beam_archive.py` | `BeamArchiveStrategy` -- inherits from `BeamStrategy`. The archive exemplars are automatically included in prompts via `generate_candidates()`, which reads from `RunContext.archive`. This is the **default strategy**. |
| `swarm.py` | `SwarmStrategy` -- delegates to `SwarmOrchestrator`, wraps async execution with `asyncio.run()`. |

### Swarm (`swarm/`)

| Module | Responsibility |
|--------|----------------|
| `orchestrator.py` | `SwarmOrchestrator` -- coordinates the swarm pipeline: launch mutation agents concurrently (with semaphore-bounded concurrency), optionally run critic screening, optionally run crossover, optionally inject diversity. |
| `mutation_agent.py` | `MutationAgent` -- specialized mutator with one of four focuses: algorithmic, optimization, architectural, or hybrid. Uses async `agenerate()`. |
| `critic_agent.py` | `CriticAgent` -- reviews candidates, responds APPROVE or REJECT. Conservative failure mode: approves on error. |
| `crossover_agent.py` | `CrossoverAgent` -- async crossover between the two top-scoring parents. |
| `diversity_agent.py` | `DiversityAgent` -- detects beam collapse (all pairwise similarities above 0.85) and generates a deliberately different candidate. |

### Reporting (`reporting/`)

| Module | Responsibility |
|--------|----------------|
| `console.py` | `ConsoleReporter` -- prints run start, generation progress, and run end to stdout. |
| `markdown_log.py` | `MarkdownLogger` -- writes `log.md` with per-generation tables and a final summary. |
| `jsonl_log.py` | `JsonlLogger` -- appends structured events to `events.jsonl`. This is the foundation for resume. |
| `summary.py` | `write_final_summary()` -- writes `summary.json` to the summaries directory. `print_run_inspection()` -- reads and displays a run for `inspect`. |

### Utilities (`utils/`)

| Module | Responsibility |
|--------|----------------|
| `files.py` | File I/O helpers: `read_text`, `write_json`, `read_jsonl`, `append_jsonl`, `ensure_dir`. |
| `hashing.py` | `candidate_id()` -- generates deterministic IDs like `gen002_child005`. `run_id()` -- generates timestamped run directory names. |
| `text.py` | `compute_similarity()` -- difflib-based string similarity in [0, 1]. Used by diversity selector and collapse detection. |
| `subprocesses.py` | `run_subprocess()` -- runs a command with timeout, captures stdout/stderr, returns structured result. |
| `timeouts.py` | `BudgetTracker` -- tracks elapsed time and candidate count against configured limits. |

---

## Data Flow

The data flow is a pipeline that transforms a task definition into scored, ranked candidates:

```
task.yaml
    |
    v
[TaskLoader] --parse, validate--> TaskConfig
    |
    v
[RunContext] --create run dir, initialize archive/lineage/budget/reporters-->
    |
    v
[Baseline Evaluation]
    |  Load artifact via ArtifactHandler
    |  Evaluate in SandboxEvaluator
    |  Store in Archive + Lineage
    |
    v
[Generational Loop]  (repeated for each generation)
    |
    |  1. Budget check -- stop if exceeded
    |
    |  2. Strategy.run_generation(gen, parents, ctx)
    |     |
    |     |  [generate_candidates]
    |     |     |
    |     |     |  Read goal.md from task directory
    |     |     |  Retrieve archive exemplars:
    |     |     |     top_k + diverse_k (deduplicated)
    |     |     |  Build MutationContext (goal, provider, exemplars, best, scores)
    |     |     |  For each parent x children_per_parent:
    |     |     |     Mutator.mutate(parent, context)
    |     |     |        |
    |     |     |        |  PromptBuilder builds the prompt
    |     |     |        |  Provider.generate(prompt) calls the LLM
    |     |     |        |  Parse HYPOTHESIS: line + artifact content
    |     |     |        |  Return new Candidate
    |     |     |
    |     |  [crossover] (optional)
    |     |     Select top parent pairs
    |     |     CrossoverMutator.mutate_pair(parent_a, parent_b)
    |     |
    |     |  [evaluate]
    |     |     EvaluationRunner -> SandboxEvaluator
    |     |        Write candidate to file
    |     |        Run evaluator.py in subprocess with timeout
    |     |        Parse JSON output -> EvaluationResult
    |     |        Update Candidate (score, status, metrics)
    |     |
    |     |  Return list[Candidate]
    |
    |  3. Record candidates in Archive + Lineage
    |  4. Emit candidate_evaluated events to events.jsonl
    |  5. Strategy.select_survivors(candidates, ctx)
    |        -> top beam_width by score
    |  6. Update best candidate if improved
    |  7. Report to console + markdown log
    |  8. Save run.json (for resume)
    |  9. Survivors become parents for next generation
    |
    v
[Final Summary]
    Write summary.json
    Write markdown log footer
    Emit run_completed event
```

### Key data types at each stage

- **Input**: `task.yaml` (YAML file on disk)
- **Parsed**: `TaskConfig` dataclass (in memory)
- **Runtime state**: `RunContext` (archive, lineage, budget, reporters)
- **Per-candidate**: `Candidate` dataclass (content, score, hypothesis, lineage)
- **Evaluation**: `EvaluationResult` dataclass (score, passed, metrics, stdout/stderr)
- **Persisted**: `RunState` dataclass (serialized to `run.json`)
- **Events**: Structured dicts appended to `events.jsonl`

---

## Run Lifecycle

A complete run proceeds through these phases:

### Phase 1: Initialization

1. `cli.py` parses command-line arguments.
2. `task_loader.load_task()` reads `task.yaml`, validates it, resolves paths
   relative to the task directory, and returns a `TaskConfig`.
3. CLI overrides (strategy, provider, generations, beam width) are applied.
4. `create_run_context()` creates the run directory structure:
   ```
   runs/<task_name>_<timestamp>/
       run.json
       events.jsonl
       log.md
       best_candidate/
       generations/
       summaries/
   ```
5. Console reporter prints the run header.
6. A `run_started` event is emitted.

### Phase 2: Baseline Evaluation

1. The artifact file is loaded via `get_artifact_handler()`.
2. A `Candidate` with `id="baseline"` and `generation=-1` is created.
3. `EvaluationRunner` evaluates the baseline in the sandbox.
4. The baseline is added to the archive, lineage, and all_candidates list.
5. `baseline_evaluated` event is emitted.
6. If the baseline has a score, it becomes the initial `best_score`.

### Phase 3: Generational Loop

For each generation `gen` in `range(strategy.generations)`:

1. **Budget check**: If `BudgetTracker.is_budget_exceeded()` returns True
   (elapsed time or candidate count), the loop breaks with a `budget_exceeded` event.
2. **Strategy execution**: `strategy.run_generation(gen, parents, ctx)` produces
   evaluated candidates. The strategy internally handles mutation, optional crossover,
   and evaluation.
3. **Recording**: Each candidate is added to the archive, lineage, and all_candidates
   list. A `candidate_evaluated` event is emitted for each.
4. **Survivor selection**: `strategy.select_survivors()` picks the top `beam_width`
   candidates by score. Their status is set to `"selected"`.
5. **Best update**: If the generation's best score exceeds the overall best, the
   best candidate artifact is saved to `best_candidate/`.
6. **State persistence**: `run.json` is written after every generation. This is the
   checkpoint that enables resume.
7. **Reporting**: Console, markdown log, and JSONL events are updated.
8. **Parent handoff**: Survivors become parents for the next generation. If no
   survivors (all candidates failed), parents carry forward unchanged.

### Phase 4: Completion

1. `run_state.status` is set to `"completed"` (or `"failed"` if an exception occurred).
2. `run.json` is written one final time.
3. `write_final_summary()` writes `summary.json`.
4. Markdown log footer and `run_completed` event are written.
5. Console prints the final best score and run directory path.

---

## Archive Retrieval

The archive is the system's memory. It stores every evaluated candidate and provides
three retrieval strategies that feed exemplar context into future mutation prompts.

### Storage

`InMemoryArchive` maintains a flat list of `Candidate` objects. Every candidate that
passes through the engine loop (including the baseline) is added via `archive.add()`.

### Retrieval Methods

| Method | Selector Function | Algorithm |
|--------|-------------------|-----------|
| `get_top_k(k)` | `select_top_k` | Sort all candidates by score descending, return the first k. Candidates with `None` scores are sorted last. |
| `get_recent_k(k)` | `select_recent_k` | Sort by `created_at` timestamp descending, return the first k. |
| `get_diverse_k(k)` | `select_diverse_k` | Greedy max-min distance selection. Start with the top-scoring candidate. Iteratively add the candidate whose minimum `difflib` distance to all already-selected candidates is maximized. |

### How Exemplars Enter Prompts

During candidate generation (`engine/generation.py`), the archive is queried:

```python
archive_exemplars = []
top_k = ctx.archive.get_top_k(config.strategy.archive_top_k)       # default 5
diverse_k = ctx.archive.get_diverse_k(config.strategy.archive_diverse_k)  # default 3

# Merge without duplicates
seen_ids = set()
for c in top_k + diverse_k:
    if c.id not in seen_ids:
        archive_exemplars.append(c)
        seen_ids.add(c.id)
```

These exemplars are passed into the `MutationContext`, and `prompt_builder.py` formats
them as numbered exemplar blocks within the prompt. The LLM sees the top-performing
and most-diverse prior attempts along with their scores, giving it concrete context
for what has worked and what is different.

Additionally, `archive_recent_k` candidates (default 3) are used to build a
natural-language score summary, letting the LLM reason about trends across recent
attempts.

### The `beam_archive` Strategy

This is the **default strategy** and the key differentiator from plain beam search.
`BeamArchiveStrategy` inherits from `BeamStrategy` with no override -- the archive
feedback behavior emerges naturally because `generate_candidates()` always reads from
the archive when it is populated. In early generations the archive is sparse, so
prompts have few exemplars. As the run progresses and the archive fills, prompts
become richer with exemplar context, creating a feedback loop similar to FunSearch.

---

## How Providers Plug In

LLM providers follow a simple plugin pattern: one abstract base class, one factory
function, and independent implementation files.

### The Provider Interface

```python
# llm/base.py
class Provider(ABC):
    @abstractmethod
    def generate(self, prompt: str, *, metadata: dict | None = None) -> str:
        """Send a prompt, return the response text."""

    async def agenerate(self, prompt: str, *, metadata: dict | None = None) -> str:
        """Async version. Default runs generate() in a thread executor."""
```

Every provider must implement `generate()`. The async `agenerate()` has a default
implementation that wraps `generate()` in `asyncio.run_in_executor()`, so providers
get async support for free. Override `agenerate()` only if you have a natively async
client library.

### The Factory

```python
# llm/base.py
def create_provider(name: str, config: MutatorConfig) -> Provider:
    if name == "mock":
        from autoevolve.llm.mock_provider import MockProvider
        return MockProvider(model=config.model)
    elif name == "anthropic":
        ...
```

### Adding a New Provider

1. Create `src/autoevolve/llm/my_provider.py`.
2. Implement the `Provider` interface:
   ```python
   from autoevolve.llm.base import Provider

   class MyProvider(Provider):
       def __init__(self, model: str, temperature: float = 0.7):
           self.model = model
           self.temperature = temperature

       def generate(self, prompt: str, *, metadata: dict | None = None) -> str:
           # Call your API here
           return response_text
   ```
3. Register it in `create_provider()` in `llm/base.py`:
   ```python
   elif name == "my_provider":
       from autoevolve.llm.my_provider import MyProvider
       return MyProvider(model=config.model, temperature=config.temperature)
   ```
4. Add `"my_provider"` to `VALID_PROVIDER_TYPES` in `config.py`.
5. Users can now select it in `task.yaml`:
   ```yaml
   mutator:
     provider: my_provider
     model: my-model-name
   ```

---

## How to Add a New Artifact Type

Artifact types define what autoevolve is optimizing. Today it supports `python_code`
and `prompt_text`. Here is how to add a third type -- for example, `json_schema`.

### Step 1: Create the Handler

Create `src/autoevolve/artifacts/json_schema.py`:

```python
from pathlib import Path
import json
from autoevolve.artifacts.base import Artifact
from autoevolve.errors import ArtifactError

class JsonSchemaArtifact(Artifact):
    artifact_type = "json_schema"
    file_extension = ".json"

    def load(self, path: Path) -> str:
        path = Path(path)
        if not path.is_file():
            raise ArtifactError(f"JSON schema artifact not found: {path}")
        return path.read_text(encoding="utf-8")

    def save(self, content: str, path: Path) -> Path:
        path = Path(path)
        if path.is_dir():
            path = path / f"artifact{self.file_extension}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def validate(self, content: str) -> bool:
        try:
            json.loads(content)
            return True
        except (json.JSONDecodeError, ValueError):
            return False
```

### Step 2: Register It

In `src/autoevolve/artifacts/base.py`, add to the `get_artifact_handler()` factory:

```python
from autoevolve.artifacts.json_schema import JsonSchemaArtifact

handlers: dict[str, type[Artifact]] = {
    "python_code": PythonCodeArtifact,
    "prompt_text": PromptTextArtifact,
    "json_schema": JsonSchemaArtifact,    # <-- add this
}
```

### Step 3: Update Validation

In `src/autoevolve/config.py`, add to the set:

```python
VALID_ARTIFACT_TYPES = {"python_code", "prompt_text", "json_schema"}
```

### Step 4: Update Prompt Discipline (Optional)

If your artifact type needs different output-formatting instructions for the LLM, add
a case in `prompt_builder.py`'s `_output_discipline()` function:

```python
elif artifact_type == "json_schema":
    return (
        "## Output Format\n\n"
        "Return ONLY valid JSON.\n"
        "Do NOT include markdown fences.\n"
    )
```

### Step 5: Write Tests and an Example

Add tests for the new handler in `tests/` and optionally create an example task
directory under `examples/`.

That is it. The engine, strategies, mutators, and evaluation pipeline are
artifact-type-agnostic. They operate on string content and delegate loading, saving,
and validation to the artifact handler.

---

## How to Add a New Strategy

Strategies control how each generation is structured: how many candidates are
generated, how they are evaluated, and how survivors are selected.

### The Strategy Interface

```python
# strategies/base.py
class Strategy(ABC):
    @abstractmethod
    def run_generation(
        self, generation: int, parents: list[Candidate], ctx: RunContext
    ) -> list[Candidate]:
        """Run one generation. Return evaluated candidates."""

    def select_survivors(
        self, candidates: list[Candidate], ctx: RunContext
    ) -> list[Candidate]:
        """Pick survivors. Default: top beam_width by score."""
```

### Step-by-Step: Adding a "Tournament" Strategy

1. Create `src/autoevolve/strategies/tournament.py`:

   ```python
   import random
   from autoevolve.engine.generation import generate_candidates
   from autoevolve.engine.run_context import RunContext
   from autoevolve.evaluation.runner import EvaluationRunner
   from autoevolve.models import Candidate
   from autoevolve.mutators.base import create_mutator
   from autoevolve.strategies.base import Strategy

   class TournamentStrategy(Strategy):
       """Tournament selection: random groups, best of each group survives."""

       def run_generation(
           self, generation: int, parents: list[Candidate], ctx: RunContext
       ) -> list[Candidate]:
           mutator = create_mutator(ctx.task_config.mutator.mode)
           children = generate_candidates(parents, mutator, generation, ctx)

           runner = EvaluationRunner(ctx.task_config)
           gen_dir = ctx.generation_dir(generation)
           if ctx.task_config.output.save_all_candidates:
               runner.evaluate_candidates(children, output_dir=gen_dir)
           else:
               runner.evaluate_candidates(children)

           return children

       def select_survivors(
           self, candidates: list[Candidate], ctx: RunContext
       ) -> list[Candidate]:
           scored = [c for c in candidates if c.score is not None]
           if len(scored) <= ctx.task_config.strategy.beam_width:
               return scored

           survivors = []
           pool = list(scored)
           random.shuffle(pool)
           group_size = max(2, len(pool) // ctx.task_config.strategy.beam_width)

           for i in range(0, len(pool), group_size):
               group = pool[i : i + group_size]
               winner = max(group, key=lambda c: c.score)
               winner.status = "selected"
               survivors.append(winner)
               if len(survivors) >= ctx.task_config.strategy.beam_width:
                   break

           return survivors
   ```

2. Register in `strategies/base.py`:

   ```python
   elif strategy_type == "tournament":
       from autoevolve.strategies.tournament import TournamentStrategy
       return TournamentStrategy()
   ```

3. Add `"tournament"` to `VALID_STRATEGY_TYPES` in `config.py`.

4. Users can select it:

   ```yaml
   strategy:
     type: tournament
     generations: 10
     beam_width: 4
   ```

The engine loop in `loop.py` calls `strategy.run_generation()` and
`strategy.select_survivors()` generically, so no other code needs to change.

---

## How Resume Works

Resume enables restarting an interrupted run from its last completed generation. This
is essential for long-running optimization sessions and recovery from crashes.

### What Gets Persisted

Two files are critical for resume:

1. **`run.json`** -- Written after every generation. Contains the full `RunState`:
   run ID, task config, status, current generation, list of completed generations,
   best score, and best candidate ID.

2. **`events.jsonl`** -- Append-only structured event log. Every significant action
   emits an event: `run_started`, `baseline_evaluated`, `generation_started`,
   `candidate_evaluated` (with full content, score, parent IDs, hypothesis),
   `generation_completed`, `run_completed`, etc.

### The Resume Process

When `autoevolve resume --run-dir <path>` is called, `resume_evolution()` in
`engine/loop.py` executes these steps:

```
1. Load run.json
       |
       v
2. Deserialize RunState (includes TaskConfig)
       |
       v
3. Create RunContext pointing to the existing run directory
       |
       v
4. Replay events.jsonl to reconstruct state:
   |
   |  For each "candidate_evaluated" event:
   |    - Rebuild a Candidate from event data
   |      (id, generation, parent_ids, content, mutation_mode, score, status, hypothesis)
   |    - Add to archive
   |    - Record in lineage tracker
   |    - Append to all_candidates list
   |
   |  For the "baseline_evaluated" event:
   |    - Extract baseline_score
       |
       v
5. Determine resume point:
   |  completed_generations = set(run_state.completed_generations)
   |  start_gen = max(completed_generations) + 1
   |  remaining_gens = total_generations - start_gen
   |
   |  If remaining_gens <= 0: run was already complete, return.
       |
       v
6. Seed parents from archive:
   |  parents = archive.get_top_k(beam_width)
   |  If archive is empty, re-evaluate the baseline.
       |
       v
7. Resume the generational loop from start_gen:
   |  Emit "run_resumed" event
   |  Execute the same loop as run_evolution, starting at start_gen
   |  Each generation: strategy, record, select, update best, save state
       |
       v
8. Completion: same as a fresh run (write summary, emit events)
```

### Why This Works

- **`run.json`** provides the checkpoint: which generations are done, what the config
  was, and what the best score was.
- **`events.jsonl`** provides the full history: every candidate's content and score.
  By replaying `candidate_evaluated` events, the archive and lineage tracker are
  reconstructed exactly. This means the archive exemplars and diversity computations
  pick up where they left off.
- **Parents are seeded from the archive** using `get_top_k(beam_width)`, which returns
  the highest-scoring candidates from the full history. This is equivalent to -- and
  often better than -- the survivors from the last generation, because the archive
  spans all generations.

### What Can Be Resumed

- Runs with status `"running"` (interrupted mid-execution).
- Runs with status `"failed"` (crashed, can retry remaining generations).
- Runs with status `"completed"` (will detect no remaining generations and exit).

### Limitations

- The archive is reconstructed in memory. If the `events.jsonl` is corrupted or
  truncated, some candidates may be lost.
- Budget tracking (elapsed time) resets on resume. The candidate count is carried
  forward from `run_state.total_candidates_evaluated`.

---

## Appendix: Directory Layout Reference

```
src/autoevolve/
|-- __init__.py              Package root, re-exports version
|-- __main__.py              python -m autoevolve entry point
|-- version.py               __version__ = "0.1.0"
|-- cli.py                   Argparse CLI (run/resume/inspect/validate-task/list-examples)
|-- config.py                YAML parsing, validation, TaskConfig construction
|-- models.py                Dataclasses (TaskConfig, Candidate, EvaluationResult, RunState, ...)
|-- errors.py                Exception hierarchy (AutoEvolveError and subclasses)
|-- task_loader.py           load_task() facade
|-- prompt_builder.py        All prompt templates, HYPOTHESIS parsing
|-- lineage.py               LineageTracker (parent/child graph)
|
|-- artifacts/
|   |-- base.py              Abstract Artifact, get_artifact_handler() factory
|   |-- python_code.py       PythonCodeArtifact (.py)
|   |-- prompt_text.py       PromptTextArtifact (.txt)
|
|-- archive/
|   |-- base.py              Abstract Archive
|   |-- in_memory.py         InMemoryArchive
|   |-- selectors.py         top_k, recent_k, diverse_k selector functions
|
|-- engine/
|   |-- loop.py              run_evolution(), resume_evolution() -- main orchestrator
|   |-- run_context.py       RunContext (bundles all per-run state)
|   |-- generation.py        generate_candidates() -- mutation orchestration
|   |-- selection.py         select_survivors(), select_parents_for_crossover()
|
|-- evaluation/
|   |-- sandbox.py           SandboxEvaluator (subprocess isolation)
|   |-- runner.py            EvaluationRunner (high-level evaluate interface)
|   |-- result_parser.py     Parse JSON from evaluator stdout
|
|-- llm/
|   |-- base.py              Abstract Provider, create_provider() factory
|   |-- mock_provider.py     MockProvider (testing, no API)
|   |-- anthropic_provider.py  Anthropic API
|   |-- openai_provider.py   OpenAI API
|   |-- ollama_provider.py   Ollama API (local)
|   |-- external_command_provider.py  Shell command provider
|
|-- mutators/
|   |-- base.py              Abstract Mutator, MutationContext, create_mutator() factory
|   |-- rewrite.py           RewriteMutator (full rewrite)
|   |-- patch.py             PatchMutator (targeted fix)
|   |-- nl_feedback.py       NLFeedbackMutator (score-aware feedback)
|   |-- crossover.py         CrossoverMutator (two-parent recombination)
|
|-- reporting/
|   |-- console.py           ConsoleReporter (stdout)
|   |-- markdown_log.py      MarkdownLogger (log.md)
|   |-- jsonl_log.py         JsonlLogger (events.jsonl)
|   |-- summary.py           write_final_summary(), print_run_inspection()
|
|-- strategies/
|   |-- base.py              Abstract Strategy, create_strategy() factory
|   |-- beam.py              BeamStrategy
|   |-- beam_archive.py      BeamArchiveStrategy (default)
|   |-- swarm.py             SwarmStrategy (delegates to swarm orchestrator)
|
|-- swarm/
|   |-- orchestrator.py      SwarmOrchestrator (coordinates agents)
|   |-- mutation_agent.py    MutationAgent (specialized mutator)
|   |-- critic_agent.py      CriticAgent (screens candidates)
|   |-- crossover_agent.py   CrossoverAgent (async crossover)
|   |-- diversity_agent.py   DiversityAgent (collapse detection + injection)
|
|-- utils/
    |-- files.py             File I/O helpers
    |-- hashing.py           Candidate and run ID generation
    |-- text.py              String similarity (difflib)
    |-- subprocesses.py      Subprocess runner with timeout
    |-- timeouts.py          BudgetTracker
```
