"""Evaluator for the text compression example.

Scores candidates based on:
1. Round-trip correctness (compress then decompress must equal original)
2. Compression ratio (smaller compressed output = higher score)
"""

import importlib.util
import pathlib
import sys


def evaluate(candidate_path: str, task_dir: str) -> dict:
    """Evaluate a compression candidate.

    Args:
        candidate_path: Path to the candidate .py file.
        task_dir: Path to the task directory containing poem.txt.

    Returns:
        Dict with score, passed, metrics, and summary.
    """
    task_dir = pathlib.Path(task_dir)
    poem_path = task_dir / "poem.txt"

    if not poem_path.is_file():
        return {
            "score": 0.0,
            "passed": False,
            "summary": "poem.txt not found",
            "error": f"Missing file: {poem_path}",
        }

    poem = poem_path.read_text(encoding="utf-8")

    # Load candidate module
    try:
        spec = importlib.util.spec_from_file_location("candidate", candidate_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as e:
        return {
            "score": 0.0,
            "passed": False,
            "summary": "Failed to load candidate",
            "error": str(e),
        }

    # Check that compress and decompress exist
    if not hasattr(mod, "compress") or not hasattr(mod, "decompress"):
        return {
            "score": 0.0,
            "passed": False,
            "summary": "Missing compress() or decompress() function",
        }

    # Test round-trip correctness
    try:
        compressed = mod.compress(poem)
        decompressed = mod.decompress(compressed)
    except Exception as e:
        return {
            "score": 0.0,
            "passed": False,
            "summary": f"Runtime error: {e}",
            "error": str(e),
        }

    if not isinstance(compressed, bytes):
        return {
            "score": 0.0,
            "passed": False,
            "summary": "compress() must return bytes",
        }

    if decompressed != poem:
        return {
            "score": 0.0,
            "passed": False,
            "summary": "Round-trip failed: decompress(compress(text)) != text",
            "metrics": {
                "compressed_bytes": len(compressed),
                "original_bytes": len(poem.encode("utf-8")),
            },
        }

    # Calculate compression ratio
    original_bytes = len(poem.encode("utf-8"))
    compressed_bytes = len(compressed)
    ratio = compressed_bytes / original_bytes

    # Score: higher is better. 1.0 - ratio means smaller compression = higher score.
    # Clamp to [0, 1].
    score = max(0.0, min(1.0, 1.0 - ratio))

    return {
        "score": round(score, 4),
        "passed": True,
        "metrics": {
            "compressed_bytes": compressed_bytes,
            "original_bytes": original_bytes,
            "ratio": round(ratio, 4),
        },
        "summary": f"Compression ratio: {ratio:.4f} ({compressed_bytes}/{original_bytes} bytes)",
    }
