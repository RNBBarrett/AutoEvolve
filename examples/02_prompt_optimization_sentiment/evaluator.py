"""Evaluator for the prompt optimization sentiment example.

Uses deterministic pattern-based scoring heuristics.
Does NOT require any external API calls.

The score reflects how well-structured the prompt is for a
classification task, based on known good prompt patterns.
"""

import json
import pathlib


def evaluate(candidate_path: str, task_dir: str) -> dict:
    """Evaluate a prompt candidate using heuristic scoring.

    Args:
        candidate_path: Path to the candidate .txt file.
        task_dir: Path to the task directory.

    Returns:
        Dict with score, passed, metrics, and summary.
    """
    task_dir = pathlib.Path(task_dir)

    # Read the candidate prompt
    try:
        prompt_template = pathlib.Path(candidate_path).read_text(encoding="utf-8")
    except Exception as e:
        return {
            "score": 0.0,
            "passed": False,
            "summary": f"Could not read candidate: {e}",
            "error": str(e),
        }

    if not prompt_template.strip():
        return {
            "score": 0.0,
            "passed": False,
            "summary": "Empty prompt",
        }

    # Load dataset for reference (not used for LLM calls, just for context)
    dataset_path = task_dir / "dataset.jsonl"
    if dataset_path.is_file():
        dataset = [
            json.loads(line)
            for line in dataset_path.read_text(encoding="utf-8").strip().splitlines()
        ]
    else:
        dataset = []

    # Heuristic scoring: each check adds points
    prompt_lower = prompt_template.lower()
    checks_passed = 0
    max_checks = 9

    # 1. Contains classification-related keywords
    if "classify" in prompt_lower or "sentiment" in prompt_lower or "categorize" in prompt_lower:
        checks_passed += 1

    # 2. Contains {text} placeholder (critical for template usage)
    if "{text}" in prompt_template:
        checks_passed += 2  # Worth more since it's essential

    # 3. Mentions the target labels
    if "positive" in prompt_lower:
        checks_passed += 1
    if "negative" in prompt_lower:
        checks_passed += 1

    # 4. Reasonable length (not too short, not too long)
    if 20 <= len(prompt_template) <= 500:
        checks_passed += 1

    # 5. Asks for a structured single-word response
    format_phrases = ["one word", "single word", "respond with", "answer with", "output only"]
    if any(phrase in prompt_lower for phrase in format_phrases):
        checks_passed += 1

    # 6. Contains few-shot examples (up to 2 bonus points)
    example_indicators = ["example", "for instance", "e.g.", "->", "→"]
    example_count = sum(1 for ind in example_indicators if ind in prompt_lower)
    checks_passed += min(example_count, 2)

    score = checks_passed / max_checks

    return {
        "score": round(score, 4),
        "passed": score > 0.3,
        "metrics": {
            "checks_passed": checks_passed,
            "max_checks": max_checks,
            "prompt_length": len(prompt_template),
            "has_placeholder": "{text}" in prompt_template,
            "has_labels": "positive" in prompt_lower and "negative" in prompt_lower,
        },
        "summary": f"Heuristic score: {score:.2f} ({checks_passed}/{max_checks} checks passed)",
    }
