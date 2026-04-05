# Contributing to autoevolve

Thanks for your interest in contributing to autoevolve! This project is open to
contributions of all kinds -- bug fixes, new providers, new examples, docs
improvements, and ideas. Every contribution matters.

---

## Getting Started

1. **Fork & clone** the repository:

   ```bash
   git clone https://github.com/<your-username>/autoevolve.git
   cd autoevolve
   ```

2. **Create a virtual environment** (recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux / macOS
   .venv\Scripts\activate      # Windows
   ```

3. **Install in editable mode with dev extras**:

   ```bash
   pip install -e ".[dev]"
   ```

4. **Run the tests** to make sure everything works:

   ```bash
   pytest -q
   ```

You're ready to go!

---

## Code Style

- **Type hints** on all function signatures (parameters and return types).
- **Docstrings** on every public function, class, and module. Use Google-style
  docstrings.
- **Keep files small.** If a module is growing past ~300 lines, consider
  splitting it.
- Use `snake_case` for functions and variables, `PascalCase` for classes.
- Prefer explicit imports over wildcard imports.
- No unused imports -- your editor or `ruff` will catch these.

---

## Running Tests

The full test suite:

```bash
pytest -q
```

Run a specific test file:

```bash
pytest tests/test_archive.py -q
```

Run with verbose output:

```bash
pytest -v
```

All tests should pass before you open a PR.

---

## How to Add an Example

Examples live in `examples/`. Each example is a directory containing at minimum:

1. **`task.yaml`** -- the task configuration file that autoevolve reads.
2. **`evaluate.py`** (or the evaluator specified in `task.yaml`) -- the fitness
   function.
3. Any supporting files the example needs (seed texts, data files, etc.).

Steps:

1. Create a new directory: `examples/NN_short_description/`.
2. Write `task.yaml` following the schema used by existing examples.
3. Write the evaluator script.
4. Add a brief `README.md` inside the example directory explaining what it does.
5. Verify it works end-to-end:
   ```bash
   python -m autoevolve validate-task --task examples/NN_short_description/task.yaml
   python -m autoevolve run --task examples/NN_short_description/task.yaml
   ```
6. Add a mention of the new example to the main project README if appropriate.

---

## How to Add a Provider

Providers live in `src/autoevolve/providers/`. Each provider is a Python module
that implements the provider interface.

Steps:

1. Create a new file: `src/autoevolve/providers/my_provider.py`.
2. Implement the provider interface (see existing providers like `mock.py` for
   the pattern).
3. Register the provider so it can be referenced by name in task configs.
4. Add tests in `tests/` covering at least the happy path.
5. Document the provider's required configuration (API keys, endpoints, etc.).

---

## Pull Request Process

1. **Fork** the repo and create a **feature branch** from `main`:
   ```bash
   git checkout -b my-feature
   ```
2. Make your changes, keeping commits focused and well-described.
3. Run the full test suite: `pytest -q`.
4. Push to your fork and open a **Pull Request** against `main`.
5. In the PR description, explain *what* changed and *why*.
6. Be responsive to review feedback -- we try to review PRs promptly.

### PR Checklist

- [ ] Tests pass (`pytest -q`)
- [ ] New code has type hints and docstrings
- [ ] Any new public API is documented
- [ ] Commit messages are clear and concise

---

## Reporting Bugs

Open a GitHub issue with:

- A clear title and description.
- Steps to reproduce.
- Expected vs. actual behavior.
- Python version and OS.

---

## Suggesting Features

Feature ideas are welcome! Open an issue with the **enhancement** label and
describe:

- The problem you're trying to solve.
- Your proposed solution (if any).
- Alternatives you've considered.

---

## Code of Conduct

Be kind, be respectful, be constructive. We're all here to learn and build
something useful together. Harassment or exclusionary behavior of any kind is
not tolerated.

---

Thank you for helping make autoevolve better!
