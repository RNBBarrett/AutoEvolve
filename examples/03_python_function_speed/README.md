# Example 03: Python Function Speed Optimization

## What is being optimized

A word frequency counter function (`count_words` in `artifact.py`). The goal is to make it as fast as possible while keeping it correct.

## The baseline

The baseline uses an O(n^2) algorithm: for each word, it scans the entire word list to count occurrences. This is correct but extremely slow for large inputs.

## How scoring works

The evaluator has two phases:
1. **Correctness** (must pass all 5 test cases to proceed)
2. **Speed** (timed over 10 iterations on a large input)

Score = 0.5 (correctness) + 0.5 * speed_bonus

The speed bonus ranges from 1.0 (< 1ms per call) to 0.0 (> 100ms per call).

## What improvements are plausible

- Using a dictionary to accumulate counts in O(n)
- Using `collections.Counter` for a one-liner O(n) solution
- Avoiding the `.lower()` call on every comparison

## Running this example

```bash
autoevolve run --task examples/03_python_function_speed/task.yaml
```
