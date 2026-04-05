"""Centralized prompt templates for all mutation and swarm operations.

All prompts are built here to avoid scattering template strings across modules.
"""

from __future__ import annotations

from autoevolve.models import Candidate


# Delimiters used by the mock provider to extract artifact content from prompts
ARTIFACT_START = "--- CURRENT ARTIFACT ---"
ARTIFACT_END = "--- END ARTIFACT ---"


def build_mutation_prompt(
    *,
    mode: str,
    artifact_content: str,
    goal: str,
    artifact_type: str,
    archive_exemplars: list[Candidate] | None = None,
    best_candidate: Candidate | None = None,
    score_summary: str | None = None,
    specialization: str | None = None,
) -> str:
    """Build a prompt for generating a mutated candidate.

    Args:
        mode: Mutation mode ('rewrite', 'patch', or 'nl_feedback').
        artifact_content: Current artifact text.
        goal: The optimization goal description.
        artifact_type: 'python_code' or 'prompt_text'.
        archive_exemplars: Prior strong/diverse candidates for context.
        best_candidate: The current best candidate.
        score_summary: Summary of recent scores.
        specialization: Swarm agent specialization instruction.

    Returns:
        Complete prompt string.
    """
    sections = []

    # Goal
    sections.append(f"## Goal\n\n{goal}")

    # Specialization (swarm agent instruction)
    if specialization:
        sections.append(f"## Specialization\n\n{specialization}")

    # Mode-specific instructions
    if mode == "rewrite":
        sections.append(
            "## Task\n\n"
            "Produce a complete, improved version of the artifact below. "
            "Think carefully about what could be improved and rewrite the entire artifact."
        )
    elif mode == "patch":
        sections.append(
            "## Task\n\n"
            "Make a focused, targeted improvement to the artifact below. "
            "Identify one specific weakness and fix it. "
            "Return the complete artifact with your change applied."
        )
    elif mode == "nl_feedback":
        sections.append(
            "## Task\n\n"
            "Based on the prior attempts and their scores shown below, "
            "generate an improved version. Analyze what worked and what didn't, "
            "then produce a better artifact."
        )

    # Score summary and prior attempts (for nl_feedback / archive modes)
    if score_summary:
        sections.append(f"## Prior Attempts and Scores\n\n{score_summary}")

    if archive_exemplars:
        exemplar_text = _format_exemplars(archive_exemplars)
        sections.append(f"## Archive Exemplars\n\n{exemplar_text}")

    if best_candidate and best_candidate.content != artifact_content:
        sections.append(
            f"## Current Best (score: {best_candidate.score})\n\n"
            f"```\n{best_candidate.content}\n```"
        )

    # Current artifact (with delimiters for mock provider parsing)
    sections.append(
        f"## Current Artifact\n\n"
        f"{ARTIFACT_START}\n{artifact_content}\n{ARTIFACT_END}"
    )

    # Hypothesis request
    sections.append(
        "## Instructions\n\n"
        "On the FIRST line of your response, write a one-sentence hypothesis "
        "starting with 'HYPOTHESIS:' explaining what improvement you are making and why.\n"
        "Then provide the complete artifact."
    )

    # Output discipline
    sections.append(_output_discipline(artifact_type))

    return "\n\n".join(sections)


def build_crossover_prompt(
    parent_a: Candidate,
    parent_b: Candidate,
    goal: str,
    artifact_type: str,
) -> str:
    """Build a prompt for crossover between two parent candidates."""
    sections = [
        f"## Goal\n\n{goal}",
        "## Task\n\n"
        "You are given two parent artifacts. Intelligently combine the best "
        "parts of both to produce a child artifact that is better than either parent. "
        "Do NOT naively splice text. Think about what makes each parent strong "
        "and combine those strengths semantically.",
        f"## Parent A (score: {parent_a.score})\n\n"
        f"{ARTIFACT_START}\n{parent_a.content}\n{ARTIFACT_END}",
        f"## Parent B (score: {parent_b.score})\n\n"
        f"```\n{parent_b.content}\n```",
        "## Instructions\n\n"
        "On the FIRST line, write 'HYPOTHESIS:' followed by a one-sentence explanation.\n"
        "Then provide the complete combined artifact.",
        _output_discipline(artifact_type),
    ]
    return "\n\n".join(sections)


def build_critic_prompt(
    candidate_content: str,
    goal: str,
    artifact_type: str,
) -> str:
    """Build a prompt for the swarm critic agent."""
    output_type = "Python code" if artifact_type == "python_code" else "prompt text"
    return (
        f"## Goal\n\n{goal}\n\n"
        f"## Candidate {output_type}\n\n"
        f"```\n{candidate_content}\n```\n\n"
        "## Task\n\n"
        "Review this candidate. Is it valid, on-task, and not obviously broken?\n\n"
        "Respond with EXACTLY one of:\n"
        "- APPROVE: <one sentence reason>\n"
        "- REJECT: <one sentence reason>\n\n"
        "Be conservative — only reject candidates that are clearly invalid, "
        "broken, or completely off-task. When in doubt, approve."
    )


def build_diversity_prompt(
    current_candidates: list[Candidate],
    goal: str,
    artifact_type: str,
    artifact_content: str,
) -> str:
    """Build a prompt for the swarm diversity agent."""
    candidate_summaries = "\n".join(
        f"- Candidate {c.id} (score: {c.score}): {_truncate(c.content, 100)}"
        for c in current_candidates[:5]
    )

    sections = [
        f"## Goal\n\n{goal}",
        f"## Current Candidates\n\n{candidate_summaries}",
        "## Task\n\n"
        "The current candidates are too similar to each other. "
        "Generate a DELIBERATELY DIFFERENT approach. "
        "Explore a radically different strategy, algorithm, or structure. "
        "The goal is diversity, not incremental improvement.",
        f"## Base Artifact\n\n"
        f"{ARTIFACT_START}\n{artifact_content}\n{ARTIFACT_END}",
        _output_discipline(artifact_type),
    ]
    return "\n\n".join(sections)


def build_score_summary(candidates: list[Candidate]) -> str:
    """Build a natural-language summary of recent candidate scores."""
    if not candidates:
        return "No prior candidates evaluated yet."

    lines = []
    for c in candidates:
        score_str = f"{c.score:.4f}" if c.score is not None else "N/A"
        mode = c.mutation_mode
        hypothesis = c.hypothesis or "no hypothesis"
        lines.append(f"- {c.id} (mode: {mode}, score: {score_str}): {hypothesis}")

    return "\n".join(lines)


def parse_hypothesis_and_content(raw_response: str) -> tuple[str | None, str]:
    """Parse hypothesis and artifact content from a model response.

    Looks for a first line starting with 'HYPOTHESIS:'. If found, extracts it
    and returns the remainder as the artifact content. If not found, the entire
    response is treated as the artifact.

    Returns:
        Tuple of (hypothesis, artifact_content).
    """
    lines = raw_response.split("\n", 1)
    first_line = lines[0].strip()

    if first_line.upper().startswith("HYPOTHESIS:"):
        hypothesis = first_line[len("HYPOTHESIS:"):].strip()
        content = lines[1].strip() if len(lines) > 1 else ""
        return hypothesis, content

    return None, raw_response.strip()


def _output_discipline(artifact_type: str) -> str:
    """Return output formatting rules for the given artifact type."""
    if artifact_type == "python_code":
        return (
            "## Output Format\n\n"
            "Return ONLY the complete Python code.\n"
            "Do NOT include markdown fences (```).\n"
            "Do NOT include explanation or commentary.\n"
            "The response must be valid, runnable Python."
        )
    else:
        return (
            "## Output Format\n\n"
            "Return ONLY the prompt text.\n"
            "Do NOT include markdown fences (```).\n"
            "Do NOT include explanation or commentary.\n"
            "The response must be the raw prompt text only."
        )


def _format_exemplars(exemplars: list[Candidate]) -> str:
    """Format archive exemplars for prompt inclusion."""
    parts = []
    for i, c in enumerate(exemplars):
        score_str = f"{c.score:.4f}" if c.score is not None else "N/A"
        parts.append(
            f"### Exemplar {i + 1} (score: {score_str})\n"
            f"```\n{_truncate(c.content, 500)}\n```"
        )
    return "\n\n".join(parts)


def _truncate(text: str, max_length: int) -> str:
    """Truncate text to max_length, appending '...' if truncated."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
