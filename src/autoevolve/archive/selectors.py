"""Archive selector functions for retrieving candidate subsets."""

from __future__ import annotations

from typing import Callable

from autoevolve.models import Candidate
from autoevolve.utils.text import compute_similarity


def select_top_k(candidates: list[Candidate], k: int) -> list[Candidate]:
    """Select the k highest-scoring candidates.

    Candidates with None scores are sorted to the end.

    Args:
        candidates: List of candidates to select from.
        k: Number of candidates to return.

    Returns:
        Up to k candidates, sorted by score descending.
    """
    if not candidates or k <= 0:
        return []

    scored = sorted(
        candidates,
        key=lambda c: (c.score is not None, c.score if c.score is not None else float("-inf")),
        reverse=True,
    )
    return scored[:k]


def select_recent_k(candidates: list[Candidate], k: int) -> list[Candidate]:
    """Select the k most recently created candidates.

    Args:
        candidates: List of candidates to select from.
        k: Number of candidates to return.

    Returns:
        Up to k candidates, sorted by creation time descending.
    """
    if not candidates or k <= 0:
        return []

    recent = sorted(candidates, key=lambda c: c.created_at, reverse=True)
    return recent[:k]


def select_diverse_k(
    candidates: list[Candidate],
    k: int,
    similarity_fn: Callable[[str, str], float] | None = None,
) -> list[Candidate]:
    """Select k candidates maximizing diversity using greedy max-min distance.

    Starts with the highest-scoring candidate, then iteratively adds
    the candidate most dissimilar to all already-selected candidates.

    Args:
        candidates: List of candidates to select from.
        k: Number of candidates to return.
        similarity_fn: Function(a, b) -> float in [0, 1]. Defaults to
                       difflib-based compute_similarity.

    Returns:
        Up to k candidates selected for diversity.
    """
    if not candidates or k <= 0:
        return []

    if similarity_fn is None:
        similarity_fn = compute_similarity

    if len(candidates) <= k:
        return list(candidates)

    # Start with the top-scoring candidate
    scored = select_top_k(candidates, len(candidates))
    selected = [scored[0]]
    remaining = list(scored[1:])

    while len(selected) < k and remaining:
        best_idx = 0
        best_min_distance = -1.0

        for i, candidate in enumerate(remaining):
            # Find the minimum distance from this candidate to any selected candidate
            min_distance = min(
                1.0 - similarity_fn(candidate.content, s.content)
                for s in selected
            )
            if min_distance > best_min_distance:
                best_min_distance = min_distance
                best_idx = i

        selected.append(remaining.pop(best_idx))

    return selected
