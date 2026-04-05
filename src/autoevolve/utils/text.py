"""Text comparison and manipulation utilities for autoevolve."""

from __future__ import annotations

import difflib


def compute_similarity(a: str, b: str) -> float:
    """Compute text similarity using difflib SequenceMatcher.

    Returns a float between 0.0 (completely different) and 1.0 (identical).
    """
    return difflib.SequenceMatcher(None, a, b).ratio()


def tokenize_simple(text: str) -> set[str]:
    """Split text into a set of lowercase whitespace-delimited tokens."""
    return set(text.lower().split())


def jaccard_similarity(a: str, b: str) -> float:
    """Compute Jaccard similarity between two texts based on token sets.

    Returns a float between 0.0 (no overlap) and 1.0 (identical token sets).
    """
    tokens_a = tokenize_simple(a)
    tokens_b = tokenize_simple(b)
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def truncate(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length characters, appending '...' if truncated."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
