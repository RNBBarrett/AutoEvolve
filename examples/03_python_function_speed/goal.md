# Goal: Optimize Word Frequency Counter for Speed

Improve the `count_words()` function in `artifact.py` to run as fast as possible
while maintaining correctness.

## Requirements

1. `count_words(text: str) -> dict[str, int]` must return correct word frequencies.
2. Words are split on whitespace and compared case-insensitively.
3. All correctness tests must pass before speed is measured.

## What makes a good solution

- Use efficient data structures (e.g., dict, collections.Counter)
- Avoid unnecessary repeated scans of the word list
- The baseline is O(n^2) — an O(n) solution is straightforward
- Further optimizations might use specialized counting techniques
