"""Beam selection logic for evolutionary search."""

from __future__ import annotations

from autoevolve.models import Candidate


def select_survivors(candidates: list[Candidate], beam_width: int) -> list[Candidate]:
    """Select the top beam_width candidates by score.

    Candidates with None scores are placed last.
    Ties are broken by candidate ID for determinism.

    Args:
        candidates: All candidates from the current generation.
        beam_width: How many to keep.

    Returns:
        Up to beam_width candidates, sorted by score descending.
    """
    if not candidates:
        return []

    sorted_candidates = sorted(
        candidates,
        key=lambda c: (
            c.score is not None,
            c.score if c.score is not None else float("-inf"),
            c.id,  # Deterministic tiebreaker
        ),
        reverse=True,
    )

    survivors = sorted_candidates[:beam_width]
    for s in survivors:
        s.status = "selected"
    return survivors


def select_parents_for_crossover(
    candidates: list[Candidate], count: int = 2
) -> list[tuple[Candidate, Candidate]]:
    """Select pairs of parents for crossover.

    Takes the top-scoring candidates and pairs them up.

    Args:
        candidates: Scored candidates to pick parents from.
        count: Number of pairs to create.

    Returns:
        List of (parent_a, parent_b) tuples.
    """
    scored = [c for c in candidates if c.score is not None]
    if len(scored) < 2:
        return []

    sorted_candidates = sorted(
        scored,
        key=lambda c: (c.score, c.id),
        reverse=True,
    )

    pairs = []
    for i in range(0, min(count * 2, len(sorted_candidates)) - 1, 2):
        pairs.append((sorted_candidates[i], sorted_candidates[i + 1]))

    return pairs[:count]
