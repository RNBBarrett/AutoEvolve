"""Subprocess execution utilities for autoevolve."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SubprocessResult:
    """Result of a subprocess execution."""

    returncode: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    duration_seconds: float = 0.0


def run_subprocess(
    cmd: list[str],
    *,
    timeout: float | None = None,
    cwd: Path | None = None,
    capture: bool = True,
    env: dict[str, str] | None = None,
) -> SubprocessResult:
    """Run a subprocess with timeout and output capture.

    Args:
        cmd: Command and arguments to execute.
        timeout: Maximum execution time in seconds. None for no timeout.
        cwd: Working directory for the subprocess.
        capture: Whether to capture stdout/stderr.
        env: Optional environment variables (added to current env).

    Returns:
        SubprocessResult with returncode, stdout, stderr, and timing info.
    """
    import os
    import time

    run_env = None
    if env:
        run_env = {**os.environ, **env}

    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=run_env,
        )
        duration = time.monotonic() - start
        return SubprocessResult(
            returncode=result.returncode,
            stdout=result.stdout if capture else "",
            stderr=result.stderr if capture else "",
            timed_out=False,
            duration_seconds=duration,
        )
    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start
        return SubprocessResult(
            returncode=-1,
            stdout="",
            stderr=f"Process timed out after {timeout}s",
            timed_out=True,
            duration_seconds=duration,
        )
    except FileNotFoundError as e:
        duration = time.monotonic() - start
        return SubprocessResult(
            returncode=-1,
            stdout="",
            stderr=str(e),
            timed_out=False,
            duration_seconds=duration,
        )
