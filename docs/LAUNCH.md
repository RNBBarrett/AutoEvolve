# Launch Playbook -- autoevolve v0.1.0

---

## Positioning Statement

autoevolve is an open-source, general-purpose evolutionary optimization
framework that uses large language models as intelligent mutation operators.
Instead of hand-crafting crossover and mutation functions, autoevolve delegates
those operations to LLMs -- enabling it to evolve arbitrary text artifacts
(prompts, code, prose) using strategies inspired by beam search, quality-
diversity archives, and swarm-based agent coordination.  It is a proof of
concept that demonstrates a practical, extensible approach to LLM-guided
evolutionary search.

---

## What Makes This Different

- **LLMs as mutation operators.** Traditional evolutionary algorithms need
  domain-specific mutation functions.  autoevolve replaces them with LLM calls,
  making the same framework work for code, prompts, and natural language.
- **Multiple search strategies in one tool.** Beam search, archive-augmented
  beam search, and swarm mode are all built in and selectable from a single
  task config.
- **OPRO-style natural language feedback.** The optimizer summarizes past
  results in plain English and feeds that context into the next mutation prompt,
  letting the LLM learn from history without gradient updates.
- **Pluggable providers.** Swap between Anthropic, OpenAI, Ollama, a shell
  command, or a deterministic mock -- no code changes required.
- **Beginner-friendly.** Three bundled examples, a clear CLI, YAML-based
  configuration, and readable run logs make it easy to get started.

---

## Launch Checklist

- [ ] All tests pass (`pytest -q`)
- [ ] README is polished and free of placeholder text
- [ ] CHANGELOG.md is up to date
- [ ] CITATION.cff is present
- [ ] CONTRIBUTING.md is present
- [ ] LICENSE file is present (MIT)
- [ ] `pip install -e .` works cleanly
- [ ] All three bundled examples run end-to-end with `--provider mock`
- [ ] `social_preview.png` is in `assets/`
- [ ] GitHub release is tagged as `v0.1.0`
- [ ] Repository description and topics are set
- [ ] Social preview image is uploaded in repo settings

---

## GitHub Repository Settings

### Suggested Repository Description

> General-purpose evolutionary optimization framework using LLMs as intelligent mutation operators.  Evolve code, prompts, and text with beam search, archives, and swarm strategies.

### Suggested Repository Topics

```
evolutionary-optimization, llm, genetic-algorithm, prompt-optimization,
python, ai, beam-search, quality-diversity, swarm, mutation, code-evolution,
prompt-engineering, optimization, evolutionary-algorithm, automl
```

### GitHub Discoverability Checklist

- [ ] Description is set (see above)
- [ ] Topics are added (see above)
- [ ] Social preview image uploaded (`assets/social_preview.png`)
- [ ] A GitHub Release is created for `v0.1.0`
- [ ] Repository is pinned to your profile
- [ ] GitHub Discussions are enabled (optional but recommended)

---

## Release

### Suggested Release Title

```
v0.1.0 -- Initial Release
```

### Suggested Release Note Outline

```
## autoevolve v0.1.0

First public release of autoevolve -- an evolutionary optimization framework
powered by LLM-guided mutation.

### Highlights
- Evolve Python code, prompts, or any text artifact
- Three built-in strategies: beam, beam_archive, swarm
- Four mutation modes: rewrite, patch, nl_feedback, crossover
- Five LLM providers: mock, anthropic, openai, ollama, external_command
- OPRO-style natural language feedback for history-aware mutation
- Subprocess-based evaluator sandboxing
- Archive with top-k, recent-k, and diverse-k selection
- Run resume support
- Three bundled examples with step-by-step documentation
- Comprehensive test suite

### Getting Started
pip install -e .
python -m autoevolve run --task examples/01_text_compression_poem/task.yaml

See the README for full documentation.
```

---

## Community Posts

### Suggested Show HN Title

```
Show HN: autoevolve -- Evolve code and prompts using LLMs as mutation operators
```

### Suggested HN Intro Comment

```
Hi HN, I built autoevolve as a proof-of-concept for using LLMs as the mutation
and crossover operators inside an evolutionary optimization loop.

The idea is simple: instead of writing domain-specific mutation functions, you
describe the task in a YAML file, provide a fitness evaluator (a script that
returns a score), and let the LLM figure out how to improve candidates
generation over generation.

It ships with three strategies (beam search, archive-augmented beam search,
and a swarm mode with specialized agents), four mutation modes, and five
provider backends (including a deterministic mock for testing).

This is a POC, not a production system -- but the core loop works and the
architecture is designed to be extended.  I'd love feedback on the approach,
the interface, and whether this is useful for your workflows.

GitHub: https://github.com/RNBBarrett/AutoEvolve
```

### Suggested Reddit Post Template

```
Title: autoevolve -- Open-source framework for evolving code & prompts with LLMs

I open-sourced autoevolve, a proof-of-concept evolutionary optimization
framework that uses LLMs (Anthropic, OpenAI, Ollama, etc.) as intelligent
mutation operators.

Instead of hand-coding crossover/mutation, you write a YAML task file and a
fitness evaluator script.  autoevolve handles the rest: beam search, archive
management, OPRO-style feedback, and swarm-based agent coordination.

It's early-stage but the architecture is clean, tested, and designed to be
extended.  Three bundled examples included.

GitHub: https://github.com/RNBBarrett/AutoEvolve

Would love to hear your thoughts -- especially if you've tried similar
approaches or have ideas for new use cases.
```

### Suggested LinkedIn / X Post Template

```
I just open-sourced autoevolve -- a framework for evolutionary optimization
using LLMs as mutation operators.

Instead of hand-coded crossover functions, autoevolve uses language models to
evolve code, prompts, and text artifacts.  It supports beam search, quality-
diversity archives, and swarm-based agent strategies.

It's a proof of concept, but the results are promising and the architecture
is designed to be extended.

Check it out: https://github.com/RNBBarrett/AutoEvolve

#opensource #llm #optimization #evolutionary #ai #python
```

---

## Press / Outreach Checklist

- [ ] Publish GitHub release before any announcements
- [ ] Post to Hacker News (Show HN)
- [ ] Post to relevant subreddits (r/MachineLearning, r/Python, r/LocalLLaMA)
- [ ] Share on X / LinkedIn
- [ ] Reach out to newsletter curators if appropriate (TLDR, Python Weekly, etc.)
- [ ] Consider a short blog post explaining the motivation and architecture

---

## Credit Guidance

- Mention [autoresearch](https://github.com/karpathy/autoresearch) by Andrej Karpathy as the primary inspiration.
- Tag @karpathy respectfully when appropriate (once, not repeatedly).
- Do not spam-tag other projects or researchers in social media posts.
- Do not claim endorsement from any person or organization.
- Be honest about what this is: a proof of concept that demonstrates a
  promising approach, not a production-grade system.
- Credit specific papers or projects that inspired the design (OPRO, MAP-Elites,
  ELM, etc.) in the README or docs.

---

## Honesty Note

This is a proof of concept.  Lead with what is actually new and useful:

- The framework design that makes LLM-guided evolution easy to set up and extend.
- The combination of multiple search strategies in a single, configurable tool.
- The beginner-friendly interface (YAML config, CLI, bundled examples).

Do not overstate capabilities.  Do not claim state-of-the-art results.  Let
the code speak for itself.
