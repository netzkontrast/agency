"""Spec 073 — the toolchain `runner` boundary.

A thin, stubbable boundary (like `JulesClient` / `GitClient`) so `dogfood`'s
toolchain verbs can be exercised in tests without shelling out. The engine
injects the real `SubprocessRunner`; tests inject a stub. The one method is
``run(argv, timeout) -> {exit_code, stdout, stderr, duration_s}``.
"""
from __future__ import annotations

import subprocess
import time


class SubprocessRunner:
    """Runs an argv list as a subprocess and captures its result. Never sees a
    raw shell string — callers pass an argv built from the allowlist, so there is
    no shell-injection surface."""

    def run(self, argv: list, timeout: int = 600) -> dict:
        t0 = time.time()
        try:
            p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
            return {"exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr,
                    "duration_s": round(time.time() - t0, 2)}
        except subprocess.TimeoutExpired:
            return {"exit_code": 124, "stdout": "", "stderr": f"timeout after {timeout}s",
                    "duration_s": round(time.time() - t0, 2)}
        except OSError as e:
            return {"exit_code": 127, "stdout": "", "stderr": str(e),
                    "duration_s": round(time.time() - t0, 2)}
