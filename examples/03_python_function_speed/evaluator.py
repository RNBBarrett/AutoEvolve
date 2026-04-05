"""Evaluator for the Python function speed example.

Tests both correctness and execution speed.
The final score combines both factors.
"""

import importlib.util
import pathlib
import time


# Test cases for correctness
TEST_CASES = [
    ("hello world hello", {"hello": 2, "world": 1}),
    ("the cat sat on the mat", {"the": 2, "cat": 1, "sat": 1, "on": 1, "mat": 1}),
    ("", {}),
    ("one", {"one": 1}),
    ("a a a b b c", {"a": 3, "b": 2, "c": 1}),
]

# Large input for timing
TIMING_TEXT = " ".join(
    ["the", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog"] * 500
)


def evaluate(candidate_path: str, task_dir: str) -> dict:
    """Evaluate a word-counting candidate for correctness and speed.

    Args:
        candidate_path: Path to the candidate .py file.
        task_dir: Path to the task directory.

    Returns:
        Dict with score, passed, metrics, and summary.
    """
    # Load candidate module
    try:
        spec = importlib.util.spec_from_file_location("candidate", candidate_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as e:
        return {
            "score": 0.0,
            "passed": False,
            "summary": f"Failed to load candidate: {e}",
            "error": str(e),
        }

    if not hasattr(mod, "count_words"):
        return {
            "score": 0.0,
            "passed": False,
            "summary": "Missing count_words() function",
        }

    # Correctness tests
    correct_count = 0
    for text, expected in TEST_CASES:
        try:
            result = mod.count_words(text)
            if result == expected:
                correct_count += 1
        except Exception:
            pass

    correctness = correct_count / len(TEST_CASES)

    if correctness < 1.0:
        return {
            "score": round(correctness * 0.5, 4),
            "passed": False,
            "metrics": {
                "correctness": correctness,
                "tests_passed": correct_count,
                "total_tests": len(TEST_CASES),
            },
            "summary": f"Correctness: {correct_count}/{len(TEST_CASES)} tests passed",
        }

    # Timing test (only if all correctness tests pass)
    iterations = 10
    start = time.perf_counter()
    for _ in range(iterations):
        mod.count_words(TIMING_TEXT)
    elapsed = time.perf_counter() - start
    avg_ms = (elapsed / iterations) * 1000

    # Score: correctness (0.5) + speed bonus (0.5).
    # Speed bonus: 1.0 for < 1ms, scaling down to 0.0 for > 100ms.
    speed_bonus = max(0.0, min(1.0, 1.0 - (avg_ms / 100.0)))
    score = 0.5 + 0.5 * speed_bonus

    return {
        "score": round(score, 4),
        "passed": True,
        "metrics": {
            "correctness": correctness,
            "avg_ms": round(avg_ms, 2),
            "iterations": iterations,
            "speed_bonus": round(speed_bonus, 4),
        },
        "summary": f"Correct, avg {avg_ms:.2f}ms/call, score {score:.4f}",
    }
