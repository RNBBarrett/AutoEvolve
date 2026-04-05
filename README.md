<p align="center">
  <img src="assets/logo.png" alt="autoevolve" width="600">
</p>

**A general-purpose evolutionary optimization framework that uses LLMs as intelligent mutation operators.**

autoevolve takes any artifact you want to improve -- a Python function, a prompt template, a compression algorithm -- and iteratively evolves better versions of it using large language models. You define what "better" means with a simple evaluator script, and autoevolve handles the rest: generating candidates, scoring them, selecting survivors, and feeding the best results back into the next generation.

### Why this is interesting

Most optimization tools either require you to hand-tune things manually or rely on random search that wastes your compute budget. autoevolve sits in a sweet spot: it uses LLMs to make *intelligent*, *targeted* mutations instead of random ones, and it wraps this capability inside a clean evolutionary loop with beam search, archive feedback, and optional swarm parallelism. The result is a framework that can improve code, prompts, and other text artifacts automatically -- and that gets smarter as it goes, because every generation's results inform the next.

---

## Why This Exists and What It Improves

This section explains the motivation behind autoevolve in plain English. If you are new to evolutionary search or LLM-based optimization, start here.

### The inspiration: autoresearch

[autoresearch](https://github.com/karpathy/autoresearch) by Andrej Karpathy pioneered a compelling idea: let an AI agent run an autonomous research loop. It reads a goal, writes code, runs experiments, evaluates results, and iterates. This workflow is powerful because it closes the loop between "generate an idea" and "test if it worked" without a human in the middle.

autoevolve is inspired by that workflow, but it broadens the idea. Instead of being a single research agent tied to one kind of task, autoevolve is a *generic optimization framework*. You can point it at any artifact (Python code, a prompt, or any text-based thing you can score numerically), define a scoring function, and let the evolutionary loop find better versions.

### How classic genetic algorithms work

To understand what autoevolve does, it helps to understand the basics of evolutionary computation:

1. **Population.** You start with a set of candidate solutions (the "population"). In autoevolve, these are versions of the artifact you want to improve.

2. **Mutation.** Each generation, you create new candidates by modifying existing ones. In a classic genetic algorithm (GA), mutation is often random -- flip a bit, change a number, swap two elements.

3. **Crossover.** You can also combine two good candidates to produce a child that inherits strengths from both parents. This is like breeding in biology.

4. **Evaluation.** Every candidate is scored by a fitness function. In autoevolve, this is your evaluator script -- it runs the candidate and returns a number.

5. **Selection.** The highest-scoring candidates survive to become parents of the next generation. Lower-scoring candidates are discarded.

6. **Diversity.** Good evolutionary search balances exploitation (refining what works) with exploration (trying something genuinely different). Without diversity pressure, the population can "collapse" to a single solution and stop improving.

7. **Generations.** This cycle repeats for a fixed number of generations, or until a budget is exhausted.

Classic genetic algorithms have been around for decades and work well on many numerical optimization problems. But they have a significant weakness when applied to software and text artifacts.

### Why random mutation wastes your budget on software tasks

In a traditional GA applied to code, a "mutation" might randomly change a token, swap two lines, or alter a constant. The vast majority of these random changes produce broken code or meaningless variations. The search space is enormous, and random exploration is extraordinarily inefficient.

If you are trying to improve a compression algorithm, for example, randomly shuffling lines of code will almost never produce a valid program, let alone a better one. You would burn through your entire compute budget generating candidates that fail to even run.

### How autoevolve improves on classic GAs

autoevolve replaces random mutation with **LLM-powered mutation**. Instead of making blind changes, it asks a large language model to:

- Read the current artifact and the optimization goal
- Understand *what the code does* and *why it scores the way it does*
- Generate a *targeted, hypothesis-driven improvement*

This is dramatically more efficient. The LLM brings world knowledge about algorithms, coding patterns, and optimization strategies to bear on each mutation. It does not flip random bits -- it reasons about the problem and proposes specific changes.

### How beam search keeps strong directions alive

autoevolve uses **beam search** as its default selection strategy. In beam search, only the top `beam_width` candidates survive each generation. This keeps the search focused on the most promising directions without collapsing to a single solution (which would happen with greedy search).

For example, with `beam_width=3`, the top three candidates from each generation become parents of the next. This means three distinct approaches can evolve in parallel, and the framework can discover which direction is most productive over multiple generations.

### How archive feedback improves future generations

One of autoevolve's most important features is **archive feedback**. The archive stores every candidate that has ever been evaluated, along with its score. When building prompts for the LLM, autoevolve retrieves:

- **Top-scoring exemplars**: The best candidates found so far, so the LLM can see what works.
- **Diverse exemplars**: Candidates chosen to be maximally different from each other, so the LLM sees a range of approaches.

This creates a **feedback loop**: as the archive fills with scored examples, the LLM gets richer context about what has been tried and what worked. Early generations have sparse context, but later generations benefit from a deep history of experiments. This is inspired by the "exemplar database" concept in [FunSearch](https://deepmind.google/blog/funsearch-making-new-discoveries-in-mathematical-sciences-using-large-language-models/).

### How OPRO-style feedback differs from raw mutation

autoevolve supports a mutation mode called **nl_feedback** (natural-language feedback), inspired by [OPRO](https://arxiv.org/abs/2309.03409) (Optimization by PROmpting). In this mode, instead of just asking the LLM to "rewrite this code to be better," the prompt includes:

- Previous candidates and their scores
- A natural-language summary of score trends
- The optimization goal

The LLM is essentially asked: "Here are five attempts at this problem and how they scored. Generate the next attempt." This turns the LLM into a meta-optimizer that reasons about the *trajectory* of the search, not just the current artifact.

This is fundamentally different from raw code-diff mutation. A rewrite mutator sees one artifact and tries to improve it. An nl_feedback mutator sees the *history* of the optimization and tries to identify patterns in what works.

### How swarm mode adds specialized exploration

For more complex tasks, autoevolve offers **swarm mode**. Instead of one mutator generating all candidates, swarm mode launches multiple specialized agents in parallel:

- **Algorithmic agent**: focuses on algorithmic improvements
- **Optimization agent**: focuses on performance tuning
- **Architectural agent**: focuses on structural redesign
- **Hybrid agent**: combines multiple approaches

Additionally, swarm mode can include:
- A **critic agent** that screens candidates before evaluation, filtering out obviously broken ones
- A **diversity agent** that detects when all candidates look too similar (beam collapse) and injects a deliberately different solution
- A **crossover agent** that combines the two best candidates

Swarm mode costs more (more LLM calls per generation) but produces more diverse candidates and is less likely to get stuck in local optima.

---

## What autoevolve Is

autoevolve is a **generic evolutionary optimization framework**. You give it:

1. An **artifact** to improve (a Python file, a prompt, or any text-based artifact)
2. A **goal** describing what "better" means (a Markdown file)
3. An **evaluator** that scores candidates numerically (a Python script)

autoevolve then runs an evolutionary loop: it generates improved candidates using an LLM, scores them, selects the best, and feeds the results back to produce even better candidates in the next generation.

In version 0.1, autoevolve ships with two first-class artifact types:

- **`python_code`**: Optimize a Python function or module (compression algorithms, data processing, etc.)
- **`prompt_text`**: Optimize a prompt template (classification prompts, instruction prompts, etc.)

The architecture is designed so that new artifact types (JSON schemas, SQL queries, YAML configs) can be added with minimal changes to the core.

---

## Who It Is For

- **Solo builders** who want to automatically improve a function or prompt without hand-tuning
- **AI engineers** experimenting with prompt optimization, code generation, or evaluator-driven search
- **Researchers** exploring LLM-as-mutation-operator, evolutionary computation, or meta-optimization
- **Tinkerers** who want to understand how evolutionary search works by running real examples
- **Teams** looking for a lightweight, extensible framework for evaluator-driven optimization

If you can write a Python scoring function and describe what "better" means, you can use autoevolve.

---

## Core Idea in One Picture

Here is the autoevolve loop in a single diagram:

```
    +-------------------+
    |   baseline        |    Your starting artifact (artifact.py or prompt.txt)
    |   artifact        |
    +--------+----------+
             |
             v
    +--------+----------+
    |   LLM-powered     |    The LLM reads the goal, current artifact, and
    |   mutation        |    archive exemplars, then generates improved versions
    +--------+----------+
             |
             v
    +--------+----------+
    |   evaluator       |    Your scoring script runs each candidate in a
    |   (subprocess)    |    sandboxed subprocess and returns a numeric score
    +--------+----------+
             |
             v
    +--------+----------+
    |   selection       |    Top beam_width candidates survive to become
    |   (beam search)   |    parents of the next generation
    +--------+----------+
             |
             v
    +--------+----------+
    |   archive         |    Every scored candidate is stored; top and diverse
    |   (feedback)      |    exemplars are fed into future prompts
    +--------+----------+
             |
             v
        next generation
        (repeat for N generations)
```

Or, more compactly:

```
baseline --> mutate --> evaluate --> select --> archive --> next generation
```

---

## How It Works

Each optimization run follows this numbered sequence:

1. **Load the task.** autoevolve reads your `task.yaml`, resolves file paths, and validates the configuration.

2. **Evaluate the baseline.** The starting artifact is scored by the evaluator to establish a baseline score.

3. **For each generation:**

   a. **Generate candidates.** The LLM reads the goal, current parent artifacts, and archive exemplars. It produces `children_per_parent` new candidates for each surviving parent.

   b. **Crossover (optional).** The two highest-scoring parents are combined to produce a hybrid child.

   c. **Evaluate all candidates.** Each candidate is written to a temporary file and scored by the evaluator in a sandboxed subprocess with a timeout.

   d. **Select survivors.** The top `beam_width` candidates (by score) survive to become parents of the next generation.

   e. **Update the archive.** Every evaluated candidate is stored in the archive for future reference.

   f. **Log everything.** Scores, lineage, and artifacts are recorded in `events.jsonl`, `log.md`, and `run.json`.

4. **Save the best.** The highest-scoring candidate found across all generations is saved to `best_candidate/`.

5. **Write a summary.** A final summary with improvement deltas, candidate counts, and the best artifact path is written to `summaries/`.

---

## Core Concepts

These are the building blocks of autoevolve. Understanding them makes everything else click.

**Task** -- A complete optimization job, defined in a `task.yaml` file. Contains the artifact to improve, the goal description, the evaluator script, and all configuration settings (strategy, provider, budget, etc.).

**Artifact** -- The thing being optimized. In v1, this is either a Python file (`python_code`) or a text prompt (`prompt_text`). The baseline artifact is your starting point; the framework generates improved versions of it.

**Evaluator** -- A Python script that scores a candidate artifact numerically. It takes a candidate file path and the task directory, and returns a dictionary with a `score`, `passed` flag, and optional `metrics`. Higher scores are better. The evaluator runs in a subprocess, never in the main process.

**Mutator** -- The component that generates new candidates. autoevolve ships with four mutation modes: `rewrite` (full rewrite), `patch` (targeted fix), `nl_feedback` (score-aware optimization), and `crossover` (combine two parents). Each mode builds a different kind of prompt for the LLM.

**Strategy** -- Controls how the evolutionary loop runs. `beam` is a simple beam search. `beam_archive` adds archive feedback (the default). `swarm` uses parallel specialized agents.

**Archive** -- The system's memory. Stores every evaluated candidate with its score. Provides three retrieval methods: `top_k` (highest scores), `diverse_k` (maximally different), and `recent_k` (most recent). These are used to enrich future prompts.

**Candidate** -- One generated version of the artifact. Tracks its content, score, parent(s), mutation mode, hypothesis, generation number, and status.

**Run directory** -- The output folder for one optimization run. Contains `run.json` (checkpoint state), `events.jsonl` (structured event log), `log.md` (human-readable log), `best_candidate/` (winning artifact), `generations/` (all candidates), and `summaries/` (final results).

---

## Installation

### Requirements

- Python 3.11 or later
- `pip` (comes with Python)
- Git (to clone the repository)

### Steps

```bash
# Clone the repository
git clone https://github.com/RNBBarrett/AutoEvolve.git
cd autoevolve

# Install in editable mode (core only -- no API keys needed)
pip install -e .

# For Anthropic (Claude) provider support:
pip install -e ".[anthropic]"

# For OpenAI provider support:
pip install -e ".[openai]"

# For development (pytest, coverage):
pip install -e ".[dev]"

# For everything:
pip install -e ".[all]"
```

After installation, verify it works:

```bash
autoevolve --version
autoevolve list-examples
```

You can also run autoevolve as a Python module:

```bash
python -m autoevolve --version
```

---

## Quick Start

Run these commands from the repository root to try autoevolve in under two minutes:

```bash
# 1. See what examples are available
autoevolve list-examples

# 2. Validate an example task (checks files, config, no LLM calls)
autoevolve validate-task --task examples/01_text_compression_poem/task.yaml

# 3. Run the optimization (uses the mock provider by default -- no API key needed)
autoevolve run --task examples/01_text_compression_poem/task.yaml

# 4. Inspect the results
autoevolve inspect --run-dir runs/<run_dir_name>

# 5. Resume a run if it was interrupted
autoevolve resume --run-dir runs/<run_dir_name>
```

The mock provider generates deterministic candidates without calling any external API, so you can explore the entire framework immediately with no setup beyond `pip install -e .`.

---

## Detailed User Walkthrough

This section walks you through a complete first experience with autoevolve, step by step. It is intentionally long and explicit so you can follow along without guessing.

### Step 1: Pick an example

autoevolve ships with three examples. Start with the first one:

```
examples/01_text_compression_poem/
```

This example optimizes a Python text compression algorithm against a short poem.

### Step 2: Read the goal

Open `examples/01_text_compression_poem/goal.md`:

```markdown
# Goal: Optimize Text Compression

Improve the `compress()` and `decompress()` functions in `artifact.py` to achieve
a better compression ratio on the poem stored in `poem.txt`.

## Requirements
1. `compress(text: str) -> bytes` must accept a string and return compressed bytes.
2. `decompress(data: bytes) -> str` must accept compressed bytes and return the original string.
3. Round-trip correctness: `decompress(compress(text)) == text` must always hold.
4. The score is based on the compression ratio -- smaller compressed output scores higher.
```

This goal file is what the LLM reads when generating improvements. It describes *what* to optimize and *what constraints* to respect.

### Step 3: Inspect the task configuration

Open `examples/01_text_compression_poem/task.yaml`:

```yaml
name: text_compression_poem
artifact_type: python_code
artifact_path: artifact.py
goal_path: goal.md
evaluator_path: evaluator.py

strategy:
  type: beam_archive
  generations: 3
  beam_width: 2
  children_per_parent: 2
  crossover_enabled: true
  archive_top_k: 3
  archive_diverse_k: 2

mutator:
  provider: mock
  mode: rewrite
  model: mock-deterministic
  temperature: 0.2
  max_candidates_per_call: 1

budget:
  max_total_candidates: 30
  max_runtime_seconds: 300
  eval_timeout_seconds: 10

output:
  save_all_candidates: true
  write_markdown_log: true
  write_jsonl_events: true
```

Key things to notice:
- `artifact_type: python_code` tells autoevolve this is a Python file.
- `artifact_path: artifact.py` is the file being optimized.
- `strategy.type: beam_archive` uses beam search with archive feedback.
- `mutator.provider: mock` means no API key is needed -- candidates are generated deterministically.
- `budget.max_total_candidates: 30` caps the total number of candidates.

### Step 4: Understand the baseline artifact

Open `examples/01_text_compression_poem/artifact.py`:

```python
def compress(text: str) -> bytes:
    """Compress text using naive run-length encoding."""
    encoded = []
    i = 0
    while i < len(text):
        count = 1
        while i + count < len(text) and text[i + count] == text[i] and count < 255:
            count += 1
        encoded.append(count)
        encoded.append(ord(text[i]))
        i += count
    return bytes(encoded)

def decompress(data: bytes) -> str:
    """Decompress data produced by compress()."""
    result = []
    for i in range(0, len(data), 2):
        count = data[i]
        char = chr(data[i + 1])
        result.append(char * count)
    return "".join(result)
```

This is a deliberately weak baseline. Naive run-length encoding (RLE) stores each character as a `(count, char_code)` pair. For natural-language text with few repeated characters, this is very inefficient -- the "compressed" output is actually *larger* than the original. A good optimizer should find a better approach (e.g., using `zlib`, dictionary coding, or Huffman-like techniques).

### Step 5: Understand the evaluator

Open `examples/01_text_compression_poem/evaluator.py`. The evaluator:

1. Loads `poem.txt` from the task directory
2. Calls `compress(poem)` on the candidate
3. Calls `decompress(compressed)` and checks that it equals the original
4. Computes `score = 1.0 - (compressed_bytes / original_bytes)`
5. Returns a dict with `score`, `passed`, `metrics`, and `summary`

A perfect compressor (0 bytes) would score 1.0. The naive RLE baseline will score close to 0 (or even negative, since it expands the text). Any compression that actually shrinks the output will score positively.

### Step 6: Run the optimization

```bash
autoevolve run --task examples/01_text_compression_poem/task.yaml
```

You will see console output showing:
- The run starting with its configuration
- Each generation's candidates and their scores
- The best score found
- The run directory path

### Step 7: Inspect the run directory

After the run completes, look inside the generated run directory:

```
runs/<timestamp>_text_compression_poem/
  run.json              # Machine-readable run state (for resume)
  events.jsonl          # Structured event log (every candidate, every score)
  log.md                # Human-readable markdown log
  best_candidate/
    artifact.py         # The highest-scoring artifact found
  generations/
    gen_000/            # All candidates from generation 0
    gen_001/            # All candidates from generation 1
    gen_002/            # All candidates from generation 2
  summaries/
    summary.json        # Final summary with scores and metadata
```

- Read `log.md` for a formatted view of the run with per-generation tables.
- Read `best_candidate/artifact.py` to see the winning code.
- Read `events.jsonl` to see the full structured history (one JSON object per line).
- Read `run.json` to see the checkpoint state that enables resume.

You can also use the CLI:

```bash
autoevolve inspect --run-dir runs/<timestamp>_text_compression_poem
```

### Step 8: Change the LLM provider

To use a real LLM instead of the mock provider, set an API key and override the provider:

**Anthropic (Claude):**

```bash
pip install -e ".[anthropic]"
export ANTHROPIC_API_KEY="sk-ant-..."

autoevolve run \
  --task examples/01_text_compression_poem/task.yaml \
  --provider anthropic
```

**OpenAI:**

```bash
pip install -e ".[openai]"
export OPENAI_API_KEY="sk-..."

autoevolve run \
  --task examples/01_text_compression_poem/task.yaml \
  --provider openai
```

When using a real LLM, the candidates will be genuinely creative improvements rather than deterministic mock outputs.

### Step 9: Change the strategy

You can override the strategy from the command line:

```bash
# Simple beam search (no archive feedback)
autoevolve run --task examples/01_text_compression_poem/task.yaml --strategy beam

# Beam search with archive feedback (default)
autoevolve run --task examples/01_text_compression_poem/task.yaml --strategy beam_archive

# Swarm mode with parallel agents
autoevolve run --task examples/01_text_compression_poem/task.yaml --strategy swarm
```

You can also combine overrides:

```bash
autoevolve run \
  --task examples/01_text_compression_poem/task.yaml \
  --provider anthropic \
  --strategy swarm \
  --generations 10 \
  --beam-width 4
```

### Step 10: Create your own task from scratch

To create a custom optimization task:

**1. Create a task directory:**

```bash
mkdir -p examples/my_custom_task
```

**2. Write your baseline artifact** (`artifact.py` or `prompt.txt`):

```python
# examples/my_custom_task/artifact.py
def sort_strings(items: list[str]) -> list[str]:
    """A deliberately slow bubble sort."""
    result = list(items)
    for i in range(len(result)):
        for j in range(len(result) - 1):
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]
    return result
```

**3. Write your goal** (`goal.md`):

```markdown
# Goal: Optimize String Sorting

Improve the `sort_strings()` function to be as fast as possible
while maintaining correctness. The function must return strings
in lexicographic order.
```

**4. Write your evaluator** (`evaluator.py`):

```python
import importlib.util
import time

def evaluate(candidate_path: str, task_dir: str) -> dict:
    spec = importlib.util.spec_from_file_location("candidate", candidate_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Correctness test
    test_input = ["banana", "apple", "cherry", "date"]
    expected = sorted(test_input)
    result = mod.sort_strings(test_input)
    if result != expected:
        return {"score": 0.0, "passed": False, "summary": "Incorrect output"}

    # Speed test
    big_input = [f"word_{i}" for i in range(1000, 0, -1)]
    start = time.perf_counter()
    for _ in range(100):
        mod.sort_strings(big_input)
    elapsed = time.perf_counter() - start

    # Score: faster is better (inverse of time, clamped to [0, 1])
    score = min(1.0, 1.0 / (1.0 + elapsed))
    return {"score": round(score, 4), "passed": True, "summary": f"Time: {elapsed:.4f}s"}
```

**5. Write your task file** (`task.yaml`):

```yaml
name: my_sort_optimization
artifact_type: python_code
artifact_path: artifact.py
goal_path: goal.md
evaluator_path: evaluator.py

strategy:
  type: beam_archive
  generations: 5
  beam_width: 3
  children_per_parent: 2

mutator:
  provider: mock              # Change to anthropic/openai for real LLM
  mode: rewrite
  model: mock-deterministic
  temperature: 0.7

budget:
  max_total_candidates: 50
  max_runtime_seconds: 300
  eval_timeout_seconds: 10

output:
  save_all_candidates: true
  write_markdown_log: true
  write_jsonl_events: true
```

**6. Validate and run:**

```bash
autoevolve validate-task --task examples/my_custom_task/task.yaml
autoevolve run --task examples/my_custom_task/task.yaml
```

That is it. The framework handles mutation, evaluation, selection, archiving, logging, and output for you.

---

## Task File Walkthrough

Every autoevolve task is defined by a `task.yaml` file. Here is a complete reference with every field explained.

You can also copy `autoevolve.example.yaml` from the repository root as a starting template.

```yaml
# Required: Identifies the task
name: my_task

# Required: What type of artifact is being optimized
# Options: python_code, prompt_text
artifact_type: python_code

# Required: Path to the baseline artifact (relative to this file's directory)
artifact_path: artifact.py

# Required: Path to the goal description (relative to this file's directory)
goal_path: goal.md

# Required: Path to the evaluator script (relative to this file's directory)
evaluator_path: evaluator.py

# Optional: Path to a dataset file used by the evaluator
dataset_path: dataset.jsonl

# Strategy settings -- control the evolutionary search
strategy:
  # Which strategy to use
  # beam:          Simple beam search. Fast, predictable.
  # beam_archive:  Beam search with archive feedback. Recommended default.
  # swarm:         Parallel specialized agents. More diversity, higher cost.
  type: beam_archive

  # How many generations to run
  generations: 5

  # How many top candidates survive each generation
  beam_width: 3

  # How many children each surviving parent produces
  children_per_parent: 2

  # Whether to attempt crossover between top parents
  crossover_enabled: true

  # How many top-scoring archive exemplars to include in prompts
  archive_top_k: 5

  # How many diverse archive exemplars to include in prompts
  archive_diverse_k: 3

# Mutator settings -- control how candidates are generated
mutator:
  # Which LLM provider to use
  # mock:             No API needed. Deterministic, for testing.
  # anthropic:        Anthropic API (Claude models).
  # openai:           OpenAI API (GPT models).
  # ollama:           Local Ollama server.
  # external_command: Bridge to any external tool.
  provider: mock

  # Mutation mode (used as the default mode for non-swarm strategies)
  # rewrite:     Full artifact rewrite from scratch.
  # patch:       Focused improvement on specific areas.
  # nl_feedback: OPRO-style, includes prior candidates + scores as context.
  mode: rewrite

  # Model name (provider-specific)
  # For mock: mock-deterministic, mock-malformed, mock-noop
  # For anthropic: claude-sonnet-4-20250514, etc.
  # For openai: gpt-4o, etc.
  model: mock-deterministic

  # Sampling temperature (higher = more creative, lower = more focused)
  temperature: 0.7

  # Maximum candidates to request per LLM call
  max_candidates_per_call: 1

# Swarm settings (only used when strategy.type is 'swarm')
swarm:
  enabled: false                # Must be true for swarm mode
  mutation_agents: 4            # Number of parallel mutation agents
  use_critic: true              # Enable critic agent to screen candidates
  use_diversity_agent: true     # Enable diversity injection on beam collapse
  max_concurrent_calls: 4       # Concurrency limit for LLM calls

# Budget limits -- prevent runaway runs
budget:
  max_total_candidates: 100     # Stop after generating this many candidates
  max_runtime_seconds: 300      # Stop after this many wall-clock seconds
  eval_timeout_seconds: 30      # Timeout for each individual evaluation

# Output settings
output:
  save_all_candidates: true     # Save every candidate artifact to disk
  write_markdown_log: true      # Write human-readable log.md
  write_jsonl_events: true      # Write structured events.jsonl
```

### What you typically edit

For most tasks, you will only change these fields:

- `name`, `artifact_type`, `artifact_path`, `goal_path`, `evaluator_path` -- these define your task
- `mutator.provider` and `mutator.model` -- to use a real LLM
- `strategy.generations` and `strategy.beam_width` -- to control search depth and breadth
- `budget` -- to set your time and candidate limits

Everything else has sensible defaults that work well for most tasks.

---

## Choosing a Strategy

autoevolve ships with three search strategies. Each makes a different tradeoff between cost, diversity, and predictability.

### beam

The simplest strategy. Each generation:
1. Each parent produces `children_per_parent` candidates via the configured mutator
2. Optionally, top parents are crossed over to produce a hybrid child
3. All candidates are evaluated
4. The top `beam_width` candidates survive

**When to use:** Quick experiments, low-budget runs, tasks where you want predictable behavior.

### beam_archive (recommended default)

Identical to `beam`, but with an important addition: archive feedback. When generating candidates, the prompt includes:
- Top-scoring exemplars from all prior generations
- Diverse exemplars that represent different approaches
- A summary of recent score trends

This creates a feedback loop where the LLM gets better context as the run progresses. Early generations have sparse context, but later generations benefit from a rich history of what has been tried.

**When to use:** Most tasks. This is the default for a reason -- it is the best balance of cost and effectiveness.

### swarm

The most powerful strategy. Each generation launches multiple specialized mutation agents in parallel, each with a different focus (algorithmic, optimization, architectural, hybrid). Additionally:
- A **critic agent** can screen candidates before evaluation
- A **crossover agent** can combine top parents
- A **diversity agent** can inject novel candidates if beam collapse is detected

**When to use:** Complex tasks where you want maximum diversity and are willing to spend more on LLM calls.

### Comparison

| Feature | beam | beam_archive | swarm |
|---|---|---|---|
| LLM calls per generation | Low | Low | High |
| Archive feedback | No | Yes | Yes |
| Parallel agents | No | No | Yes |
| Critic screening | No | No | Optional |
| Diversity injection | No | No | Optional |
| Predictability | High | High | Medium |
| Recommended for | Quick tests | Most tasks | Complex tasks |

---

## Mutation Modes

autoevolve supports four ways of generating new candidates from existing ones.

### rewrite

The LLM receives the current artifact and the goal, and is asked to produce a complete improved version from scratch. This is the most straightforward mode and works well as a starting point.

**Best for:** Early exploration, when you want the LLM to take creative leaps.

### patch

The LLM is asked to make a *focused, targeted* improvement rather than a full rewrite. The prompt frames the request as a constrained change -- fix one thing, optimize one bottleneck, address one weakness.

**Best for:** Later generations where you want incremental refinement rather than wholesale changes.

### nl_feedback

This is the OPRO-style mode. The LLM receives not just the current artifact, but a natural-language summary of prior candidates and their scores. It sees what has been tried, what scored well, and what scored poorly. It is asked to generate the *next* attempt based on this trajectory.

**Best for:** Tasks where the optimization landscape has subtle patterns that benefit from seeing the full history of attempts.

### crossover

Given two parent candidates, the LLM is asked to intelligently combine their best parts into a single child. This is not naive text splicing -- the LLM understands the semantics of both parents and creates a coherent hybrid.

**Best for:** When two good candidates take different approaches and you want to see if their strengths can be combined. Crossover is typically used automatically alongside other modes when `crossover_enabled: true`.

---

## Provider Setup

Providers are the LLM backends that generate candidates. autoevolve supports five providers out of the box.

### mock (no API needed)

The mock provider generates deterministic candidates without calling any external API. It is used for testing and for exploring the framework without spending money.

```yaml
mutator:
  provider: mock
  model: mock-deterministic    # Always produces a valid candidate
  # model: mock-malformed      # Produces malformed output (for error-handling tests)
  # model: mock-noop           # Produces empty output (for edge-case tests)
```

No setup required.

### anthropic (Claude)

Uses the Anthropic API to generate candidates with Claude models.

**Setup:**

```bash
pip install -e ".[anthropic]"
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**Task config:**

```yaml
mutator:
  provider: anthropic
  model: claude-sonnet-4-20250514    # or any supported Claude model
  temperature: 0.7
```

### openai (GPT)

Uses the OpenAI API to generate candidates with GPT models.

**Setup:**

```bash
pip install -e ".[openai]"
export OPENAI_API_KEY="sk-your-key-here"
```

**Task config:**

```yaml
mutator:
  provider: openai
  model: gpt-4o                # or any supported OpenAI model
  temperature: 0.7
```

### ollama (local models)

Uses a local Ollama server to generate candidates. No API key needed, but you need Ollama running locally.

**Setup:**

```bash
# Install and start Ollama (see https://ollama.com)
ollama serve
ollama pull codellama          # or any model you prefer
```

If your Ollama server is not at the default address, set:

```bash
export OLLAMA_HOST="http://localhost:11434"
```

**Task config:**

```yaml
mutator:
  provider: ollama
  model: codellama
  temperature: 0.7
```

### external_command (bridge to any tool)

The external_command provider shells out to an arbitrary CLI command. It passes the prompt via stdin or a temp file and reads the response from stdout. This lets you integrate any external tool, coding agent, or workflow.

**Task config:**

```yaml
mutator:
  provider: external_command
  model: my-custom-tool        # Used as metadata, not directly by the command
```

The command and communication mode are configured in the provider settings. See `src/autoevolve/llm/external_command_provider.py` for details.

---

## Examples

autoevolve ships with three bundled examples, each demonstrating a different use case.

### 01_text_compression_poem

**Path:** `examples/01_text_compression_poem/`

**What it does:** Optimizes a Python text compression algorithm to achieve a better compression ratio on a short Emily Dickinson poem ("Hope is the thing with feathers").

**Artifact:** `artifact.py` -- a naive run-length encoding implementation that is correct but inefficient.

**Evaluator:** Checks round-trip correctness (`decompress(compress(text)) == text`), then scores based on compression ratio. Smaller compressed output = higher score.

**Why it is interesting:** The baseline RLE is terrible for natural language text -- it actually *expands* the data. The optimizer has a lot of room to improve, and there are many valid strategies (dictionary coding, zlib wrapping, frequency analysis, etc.).

### 02_prompt_optimization_sentiment

**Path:** `examples/02_prompt_optimization_sentiment/`

**What it does:** Optimizes a prompt template for sentiment classification (positive vs. negative).

**Artifact:** `prompt.txt` -- a minimal prompt: "Classify the following text as positive or negative sentiment."

**Evaluator:** Uses a small local dataset (`dataset.jsonl`) with labeled examples. Scores the prompt based on how well a deterministic rule-based classifier interprets it. No external API calls required.

**Why it is interesting:** Demonstrates that autoevolve is not just for code -- prompt optimization is a first-class use case. The evaluator is entirely local, so this example runs without any API keys.

### 03_python_function_speed

**Path:** `examples/03_python_function_speed/`

**What it does:** Optimizes a Python word-frequency counter for speed while maintaining correctness.

**Artifact:** `artifact.py` -- a deliberately inefficient O(n^2) implementation that counts word frequencies by scanning the entire list for every word.

**Evaluator:** First checks correctness (output must match expected word counts), then measures execution speed over repeated runs. Score combines both correctness and speed.

**Why it is interesting:** Demonstrates code optimization for performance rather than output quality. The baseline has an obvious O(n^2) bottleneck that an O(n) approach using a dictionary or `collections.Counter` would easily beat.

---

## Architecture Deep Dive

This section gives you a solid understanding of how autoevolve is built internally. For the full implementer-level details, see [ARCHITECTURE.md](ARCHITECTURE.md).

### Top-level repository layout

```
autoevolve/
  src/autoevolve/       # The framework source code
  tests/                # Unit, integration, and live tests
  examples/             # Three bundled example tasks
  runs/                 # Output directory (created at runtime)
  docs/                 # Additional documentation
  assets/               # Images and media
  pyproject.toml        # Package configuration
  ARCHITECTURE.md       # Detailed architecture guide
  CONTRIBUTING.md       # Contribution guidelines
```

### Module responsibilities

The source code in `src/autoevolve/` is organized into these modules:

| Module | Purpose |
|---|---|
| `cli.py` | Argparse-based CLI: `run`, `resume`, `inspect`, `validate-task`, `list-examples` |
| `config.py` | Parses `task.yaml`, validates fields, builds `TaskConfig` |
| `task_loader.py` | High-level facade: resolves paths, calls config parsing |
| `models.py` | Dataclasses: `TaskConfig`, `Candidate`, `EvaluationResult`, `RunState`, etc. |
| `errors.py` | Exception hierarchy: `AutoEvolveError`, `TaskValidationError`, etc. |
| `prompt_builder.py` | Centralized prompt templates for all mutation modes |
| `lineage.py` | Tracks parent-child relationships between candidates |
| `artifacts/` | Artifact handlers: `PythonCodeArtifact`, `PromptTextArtifact` |
| `archive/` | In-memory archive with top-k, diverse-k, and recent-k selectors |
| `engine/` | Main loop, candidate generation, selection, run context |
| `evaluation/` | Sandbox evaluator (subprocess), result parser |
| `llm/` | LLM providers: mock, anthropic, openai, ollama, external_command |
| `mutators/` | Mutation modes: rewrite, patch, nl_feedback, crossover |
| `strategies/` | Search strategies: beam, beam_archive, swarm |
| `swarm/` | Swarm orchestrator, mutation/critic/crossover/diversity agents |
| `reporting/` | Console output, markdown log, JSONL events, summary |
| `utils/` | File I/O, hashing, text similarity, subprocess runner, budget tracker |

### Run lifecycle

A complete run proceeds through four phases:

1. **Initialization.** The CLI parses arguments, `task_loader` reads and validates `task.yaml`, and `create_run_context()` sets up the run directory with all subdirectories and reporters.

2. **Baseline evaluation.** The starting artifact is evaluated in the sandbox to establish a baseline score. This candidate (with `id="baseline"` and `generation=-1`) is the seed for the archive and the starting parent.

3. **Generational loop.** For each generation: the strategy generates candidates (via the mutator and LLM), evaluates them in the sandbox, selects survivors, updates the archive and lineage, persists state to `run.json`, and logs to all reporters. Survivors become parents for the next generation.

4. **Completion.** The final summary is written, the best artifact is saved, and the run status is set to `"completed"`.

### Prompt building

All prompts are built by `prompt_builder.py`. A typical mutation prompt includes:

- The optimization goal (from `goal.md`)
- The current artifact content
- Archive exemplars with their scores (top-k and diverse-k)
- A score summary of recent candidates
- Output formatting instructions specific to the artifact type
- Mutation-mode-specific instructions (rewrite vs. patch vs. nl_feedback)

The builder uses `ARTIFACT_START` and `ARTIFACT_END` delimiters to clearly mark where the artifact content begins and ends in the LLM's response.

### Archive retrieval

The archive uses three selection strategies:

- **top_k**: Sort by score descending, return the best k
- **recent_k**: Sort by timestamp descending, return the most recent k
- **diverse_k**: Greedy max-min selection using `difflib` similarity -- iteratively pick the candidate most different from all already-selected candidates

These are combined (deduplicated) and injected into prompts. As the archive fills over generations, prompts get richer context, creating the FunSearch-style feedback loop.

### Strategy differences

- **BeamStrategy** runs the standard loop: mutate, evaluate, select.
- **BeamArchiveStrategy** inherits from BeamStrategy with no override -- the archive feedback happens automatically in `generate_candidates()` because it reads from the archive when available.
- **SwarmStrategy** delegates to `SwarmOrchestrator`, which launches mutation agents concurrently (via `asyncio`), optionally runs critic screening, crossover, and diversity injection.

### Swarm orchestration

The swarm orchestrator coordinates four types of agents:

1. **Mutation agents** (4 by default) run concurrently, each with a different specialization focus (algorithmic, optimization, architectural, hybrid). Concurrency is bounded by a semaphore.
2. **Critic agent** reviews each candidate and responds APPROVE or REJECT. Conservative: approves on error.
3. **Crossover agent** combines the two top-scoring parents asynchronously.
4. **Diversity agent** computes pairwise similarity among candidates. If all similarities exceed 0.85 (beam collapse), it generates a deliberately different candidate.

### Evaluator sandboxing

Candidate code is **never** imported into the main autoevolve process. The `SandboxEvaluator`:

1. Writes the candidate artifact to a file
2. Generates a Python wrapper script that imports the evaluator and calls `evaluate(candidate_path, task_dir)`
3. Runs the wrapper in a **child subprocess** with a configurable timeout
4. Captures stdout and stderr
5. Parses the JSON result from stdout

If the subprocess times out, crashes, or produces malformed output, the candidate is marked as failed with a score of `None`.

### Logs and lineage

Every run produces three log outputs:

- **`events.jsonl`**: One JSON object per line, covering every significant event (run started, candidate evaluated, generation completed, etc.). This is the foundation for resume -- replaying events reconstructs the full archive and lineage.
- **`log.md`**: Human-readable markdown with per-generation tables showing candidate IDs, parents, scores, and mutations.
- **`run.json`**: Checkpoint state written after every generation. Contains the run ID, task config, status, completed generations, and best score.

The `LineageTracker` records parent-child relationships as a directed graph. It supports ancestor and descendant traversal and is serialized to `events.jsonl` via candidate events.

For the complete architecture reference, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## How to Extend

autoevolve is designed to be extended. Here are the most common extension points.

### Add a new artifact type

Suppose you want to optimize JSON schemas.

1. **Create the handler.** Add `src/autoevolve/artifacts/json_schema.py`:

   ```python
   from pathlib import Path
   import json
   from autoevolve.artifacts.base import Artifact
   from autoevolve.errors import ArtifactError

   class JsonSchemaArtifact(Artifact):
       artifact_type = "json_schema"
       file_extension = ".json"

       def load(self, path: Path) -> str:
           if not Path(path).is_file():
               raise ArtifactError(f"Not found: {path}")
           return Path(path).read_text(encoding="utf-8")

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

2. **Register it** in `src/autoevolve/artifacts/base.py`'s `get_artifact_handler()` factory.

3. **Add validation** in `src/autoevolve/config.py` by adding `"json_schema"` to `VALID_ARTIFACT_TYPES`.

4. **Optionally update prompt discipline** in `prompt_builder.py` if your artifact type needs different output instructions.

### Add a new LLM provider

1. **Create the provider.** Add `src/autoevolve/llm/my_provider.py` implementing the `Provider` interface:

   ```python
   from autoevolve.llm.base import Provider

   class MyProvider(Provider):
       def __init__(self, model: str, temperature: float = 0.7):
           self.model = model
           self.temperature = temperature

       def generate(self, prompt: str, *, metadata: dict | None = None) -> str:
           # Call your API here and return the response text
           ...
   ```

2. **Register it** in `create_provider()` in `src/autoevolve/llm/base.py`.

3. **Add validation** by adding the provider name to `VALID_PROVIDER_TYPES` in `config.py`.

### Add a new strategy

1. **Create the strategy.** Add `src/autoevolve/strategies/my_strategy.py` implementing the `Strategy` interface:

   ```python
   from autoevolve.strategies.base import Strategy
   from autoevolve.models import Candidate
   from autoevolve.engine.run_context import RunContext

   class MyStrategy(Strategy):
       def run_generation(
           self, generation: int, parents: list[Candidate], ctx: RunContext
       ) -> list[Candidate]:
           # Generate and evaluate candidates
           ...

       def select_survivors(
           self, candidates: list[Candidate], ctx: RunContext
       ) -> list[Candidate]:
           # Pick which candidates survive to the next generation
           ...
   ```

2. **Register it** in `create_strategy()` in `src/autoevolve/strategies/base.py`.

3. **Add validation** by adding the strategy name to `VALID_STRATEGY_TYPES` in `config.py`.

### Write a new evaluator

An evaluator is a Python script that exposes a single function:

```python
def evaluate(candidate_path: str, task_dir: str) -> dict:
    """Score a candidate artifact.

    Args:
        candidate_path: Path to the candidate file (.py or .txt).
        task_dir: Path to the task directory (for loading datasets, etc.).

    Returns:
        dict with keys:
            score (float): Numeric score. Higher is better.
            passed (bool): Whether the candidate is valid.
            metrics (dict, optional): Additional metrics.
            summary (str, optional): Human-readable summary.
            error (str, optional): Error message if failed.
    """
```

The evaluator runs in a subprocess, so it can import the candidate safely. It receives the candidate file path and the task directory, and returns a JSON-serializable dict.

### Add a new example

1. Create a directory under `examples/` (e.g., `examples/04_my_example/`).
2. Add: `artifact.py` (or `prompt.txt`), `goal.md`, `evaluator.py`, `task.yaml`, `README.md`.
3. Set `mutator.provider: mock` in `task.yaml` so it works without API keys.
4. Test: `autoevolve validate-task --task examples/04_my_example/task.yaml`
5. Run: `autoevolve run --task examples/04_my_example/task.yaml`

---

## Safety Note

autoevolve evaluates candidate code by running it in a **subprocess** with a configurable timeout. This provides practical isolation:

- Candidate code is **never imported into the main autoevolve process**. It runs in a separate child process.
- Each evaluation has a **timeout** (`eval_timeout_seconds`). If the candidate hangs or runs forever, the subprocess is killed.
- Stdout and stderr are captured, so candidates cannot pollute the main process's output.

**Important caveats:**

- Subprocess isolation is a **practical guardrail**, not a full security sandbox. It prevents accidental crashes from taking down the framework, but it does not prevent a malicious candidate from accessing the file system or network within the subprocess.
- **Always review your evaluator code** before running it on untrusted tasks. The evaluator defines what code gets executed and how.
- If you are running autoevolve on sensitive systems, consider additional isolation measures (containers, VMs, restricted user accounts).

---

## Testing

autoevolve has a thorough test suite using pytest.

### Running tests

```bash
# Run all tests
pytest -q

# Run only unit tests
pytest tests/unit -q

# Run only integration tests
pytest tests/integration -q

# Run with coverage
pytest --cov=autoevolve -q
```

### Test structure

- **Unit tests** (`tests/unit/`): Test individual components in isolation -- config loading, archive selectors, beam selection, prompt building, artifact handling, sandbox behavior, mock provider, lineage tracking.

- **Integration tests** (`tests/integration/`): Test end-to-end flows -- CLI smoke tests, full beam runs with mock provider on both Python code and prompt text tasks, swarm mode with mock provider, output artifact creation, resume behavior.

- **Live tests** (`tests/live/`): Test with real LLM providers. These are **skipped** unless the corresponding API key environment variable is set (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`). They are not part of the default test suite and are not required for CI to pass.

### Mock provider for testing

The mock provider (`mock-deterministic`) generates predictable candidates without any API calls. This means:

- The entire default test suite runs **without any API keys**
- Tests are **deterministic** and **reproducible**
- CI pipelines can run the full test suite for free

---

## Project Structure

```
autoevolve/
  src/autoevolve/          Core framework source code
    artifacts/             Artifact type handlers (python_code, prompt_text)
    archive/               Candidate archive with top/diverse/recent selectors
    engine/                Main evolutionary loop, generation, selection
    evaluation/            Sandbox evaluator, result parsing
    llm/                   LLM provider implementations
    mutators/              Mutation modes (rewrite, patch, nl_feedback, crossover)
    strategies/            Search strategies (beam, beam_archive, swarm)
    swarm/                 Swarm orchestrator and specialized agents
    reporting/             Console, markdown, JSONL, and summary reporters
    utils/                 File I/O, hashing, text similarity, subprocesses, budgets
  tests/                   Test suite
    unit/                  Component-level tests
    integration/           End-to-end flow tests
    live/                  Live LLM provider tests (skipped without API keys)
    fixtures/              Test task configurations and data
  examples/                Three bundled example tasks
    01_text_compression_poem/
    02_prompt_optimization_sentiment/
    03_python_function_speed/
  runs/                    Output directory for optimization runs (created at runtime)
  docs/                    Additional documentation (LAUNCH.md)
  assets/                  Images and media for documentation
  .github/workflows/       CI configuration
```

---

## Roadmap

These are potential future directions for autoevolve. They are not commitments -- they are ideas that feel natural given the architecture.

- **Multi-objective optimization.** Support tasks with multiple scoring dimensions (e.g., speed *and* correctness *and* memory usage) with Pareto-front selection.

- **Persistent archive across runs.** Allow the archive to be saved to disk and loaded into future runs, so knowledge accumulates across sessions.

- **Web UI for run inspection.** A simple browser-based viewer for exploring run histories, candidate lineage, and score progressions.

- **Additional artifact types.** JSON schemas, YAML configurations, SQL queries, Markdown documents -- the architecture supports these with minimal changes.

- **Distributed evaluation.** Run evaluations across multiple machines for tasks with expensive scoring functions.

- **Automated hyperparameter tuning.** Meta-optimize the framework's own settings (beam width, temperature, children per parent) to find the best configuration for a given task.

---

## Credits and Inspiration

autoevolve draws inspiration from several lines of work:

- **[autoresearch](https://github.com/karpathy/autoresearch)** by Andrej Karpathy -- The primary inspiration for autoevolve's autonomous improvement loop. autoresearch demonstrated that an AI agent can autonomously run research experiments, evaluate results, and iterate. autoevolve generalizes this workflow into a reusable, generic optimization framework.

- **[OPRO](https://arxiv.org/abs/2309.03409)** (Optimization by PROmpting) -- The idea of feeding prior candidates and their scores back to the LLM as natural-language optimization context. autoevolve's `nl_feedback` mutation mode is directly inspired by this.

- **[FunSearch](https://deepmind.google/blog/funsearch-making-new-discoveries-in-mathematical-sciences-using-large-language-models/)** -- The concept of maintaining an archive of strong programs and using them as exemplars for future generations. autoevolve's archive feedback mechanism follows this principle.

- **Evolutionary computation research** -- Decades of work on genetic algorithms, evolution strategies, and neuroevolution provide the theoretical foundation for population-based search with mutation, crossover, selection, and diversity.

This project is not affiliated with or endorsed by any of the above projects or organizations. It is an independent, open-source effort.

---

## License

MIT. See [LICENSE](LICENSE) for details.
