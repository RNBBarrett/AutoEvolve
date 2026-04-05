"""Evaluator for the sentiment-classification prompt task.

This evaluator reads the candidate prompt file and applies heuristic checks
to estimate how well the prompt would guide an LLM at sentiment classification.

No live LLM call is made — the evaluator scores based on structural quality
signals that correlate with good prompts.

Interface contract
------------------
    evaluate(candidate_path: str, task_dir: str) -> dict
        Returns a dict with keys: score (float 0-1), passed (bool), summary (str).
"""

import json
import os


def evaluate(candidate_path, task_dir):
    """Evaluate the candidate prompt at *candidate_path*.

    Parameters
    ----------
    candidate_path : str
        Absolute path to the candidate prompt text file.
    task_dir : str
        Absolute path to the task directory (used to locate the dataset).

    Returns
    -------
    dict
        ``{"score": float, "passed": bool, "summary": str}``
    """
    # ------------------------------------------------------------------
    # 1. Read the candidate prompt
    # ------------------------------------------------------------------
    try:
        with open(candidate_path, "r", encoding="utf-8") as f:
            prompt = f.read()
    except Exception as exc:
        return {
            "score": 0.0,
            "passed": False,
            "summary": f"Could not read candidate file: {exc}",
        }

    if not prompt.strip():
        return {
            "score": 0.0,
            "passed": False,
            "summary": "Candidate prompt is empty.",
        }

    # ------------------------------------------------------------------
    # 2. Load dataset (for reference / label-awareness check)
    # ------------------------------------------------------------------
    dataset_path = os.path.join(task_dir, "dataset.jsonl")
    labels = set()
    if os.path.isfile(dataset_path):
        with open(dataset_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    record = json.loads(line)
                    labels.add(record.get("label", ""))

    # ------------------------------------------------------------------
    # 3. Heuristic scoring
    # ------------------------------------------------------------------
    checks = []
    prompt_lower = prompt.lower()

    # Check 1: mentions all expected labels
    expected_labels = {"positive", "negative", "neutral"}
    mentioned_labels = {lab for lab in expected_labels if lab in prompt_lower}
    label_ratio = len(mentioned_labels) / len(expected_labels) if expected_labels else 0
    checks.append(("mentions_all_labels", label_ratio))

    # Check 2: contains a placeholder for the input text
    has_placeholder = 1.0 if ("{text}" in prompt or "{input}" in prompt or "text:" in prompt_lower) else 0.0
    checks.append(("has_input_placeholder", has_placeholder))

    # Check 3: instructs single-label output
    single_label_cues = ["one of", "exactly one", "only the label", "respond with only"]
    has_single_label = 1.0 if any(cue in prompt_lower for cue in single_label_cues) else 0.0
    checks.append(("single_label_instruction", has_single_label))

    # Check 4: reasonable length (not too short, not too long)
    word_count = len(prompt.split())
    if 20 <= word_count <= 300:
        length_score = 1.0
    elif 10 <= word_count < 20 or 300 < word_count <= 500:
        length_score = 0.5
    else:
        length_score = 0.0
    checks.append(("reasonable_length", length_score))

    # Check 5: contains the word "sentiment" or "classify"
    has_task_keyword = 1.0 if ("sentiment" in prompt_lower or "classify" in prompt_lower) else 0.0
    checks.append(("task_keyword_present", has_task_keyword))

    # ------------------------------------------------------------------
    # 4. Aggregate
    # ------------------------------------------------------------------
    total = sum(score for _, score in checks)
    max_possible = len(checks)
    final_score = total / max_possible if max_possible > 0 else 0.0

    details = ", ".join(f"{name}={val:.1f}" for name, val in checks)
    passed = final_score >= 0.6

    return {
        "score": round(final_score, 4),
        "passed": passed,
        "summary": f"Heuristic score {final_score:.2f} ({details}). "
                   f"Word count: {word_count}.",
    }
