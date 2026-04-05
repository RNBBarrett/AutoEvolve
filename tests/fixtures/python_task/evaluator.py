"""Evaluator for the add-two-numbers task.

This evaluator imports the candidate module, runs a small test suite against
the ``add`` function, and returns a score based on how many tests pass.

Interface contract
------------------
    evaluate(candidate_path: str, task_dir: str) -> dict
        Returns a dict with keys: score (float 0-1), passed (bool), summary (str).
"""

import importlib.util
import sys
import traceback


def _load_module(path):
    """Dynamically load a Python module from *path*."""
    spec = importlib.util.spec_from_file_location("candidate_module", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_module"] = module
    spec.loader.exec_module(module)
    return module


def evaluate(candidate_path, task_dir):
    """Evaluate the candidate artifact at *candidate_path*.

    Parameters
    ----------
    candidate_path : str
        Absolute path to the candidate Python file.
    task_dir : str
        Absolute path to the task directory (unused here, but part of the
        standard evaluator interface).

    Returns
    -------
    dict
        ``{"score": float, "passed": bool, "summary": str}``
    """
    test_cases = [
        # (a, b, expected)
        (1, 2, 3),
        (0, 0, 0),
        (-1, 1, 0),
        (3.5, 2.5, 6.0),
        (100, -50, 50),
        (-7, -3, -10),
    ]

    try:
        module = _load_module(candidate_path)
    except Exception:
        return {
            "score": 0.0,
            "passed": False,
            "summary": f"Failed to import candidate: {traceback.format_exc()}",
        }

    if not hasattr(module, "add"):
        return {
            "score": 0.0,
            "passed": False,
            "summary": "Candidate module does not define an 'add' function.",
        }

    passed_count = 0
    failures = []

    for a, b, expected in test_cases:
        try:
            result = module.add(a, b)
            if result == expected:
                passed_count += 1
            else:
                failures.append(f"add({a}, {b}) = {result!r}, expected {expected!r}")
        except Exception as exc:
            failures.append(f"add({a}, {b}) raised {type(exc).__name__}: {exc}")

    total = len(test_cases)
    score = passed_count / total

    if failures:
        summary = f"{passed_count}/{total} tests passed. Failures: " + "; ".join(failures)
    else:
        summary = f"All {total} tests passed."

    return {
        "score": score,
        "passed": passed_count == total,
        "summary": summary,
    }
