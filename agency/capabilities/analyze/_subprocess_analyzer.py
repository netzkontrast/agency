"""Spec 286 — the shared subprocess-analyzer template (Template Method).

The ruff / bandit / radon wrappers all repeated the identical scaffold:

    which-guard → ``subprocess.run(argv, capture_output, text, timeout)``
    in a TimeoutExpired/OSError guard → returncode tolerance → ``json.loads``
    in a JSONDecodeError guard → payload→Finding mapping.

The only per-tool variation is the ``argv``, the acceptable return codes, and
the payload→Finding mapping. This base owns the invariant scaffold (the
degrade-silently contract of Spec 050 §"compose, don't replace"); subclasses
supply three hooks. Each wrapper module keeps its public ``scan``/``cyclomatic``
/``maintainability`` function + module-level ``AXIS_PREFIXES`` so every call
site (the ``_quality``/``_security`` composers, ``_build_axis_registry``) is
untouched.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from typing import Any

from ._findings import Finding

# Spec 050 §"radon MI threshold" lineage — one shared timeout for every
# composed analyzer subprocess (was duplicated 3× across the wrappers).
_SUBPROCESS_TIMEOUT = 30.0


class SubprocessAnalyzer:
    """Template for a tool that shells out, emits JSON, and maps it to
    Findings. Subclasses set ``tool`` (the PATH executable) and override the
    three hooks. ``run`` owns the degrade-silently scaffold: a missing tool,
    a subprocess failure, an error return code, or unparseable output all
    yield ``[]`` (never raise) — analyze composes, it does not hard-depend."""

    #: the executable that must be on PATH for this analyzer to run
    tool: str = ""
    #: diagnostic label for stderr messages (defaults to ``tool``)
    label: str = ""

    # --- hooks -------------------------------------------------------------
    def argv(self, root: str) -> list[str]:
        """The command line to run over ``root``."""
        raise NotImplementedError

    def ok_returncode(self, rc: int) -> bool:
        """True when ``rc`` is a non-error exit (a findings-present code such
        as ruff/bandit's ``1`` still counts as OK)."""
        raise NotImplementedError

    def empty_payload(self) -> Any:
        """The value standing for 'no stdout' — ``[]`` for tools that emit a
        top-level list, ``{}`` for tools that emit a top-level object."""
        return []

    def map_payload(self, payload: Any) -> list[Finding]:
        """Map the parsed JSON payload to the agency Finding shape."""
        raise NotImplementedError

    # --- template ----------------------------------------------------------
    def run(self, root: str) -> list[Finding]:
        name = self.label or self.tool
        if shutil.which(self.tool) is None:
            return []
        try:
            result = subprocess.run(
                self.argv(root),
                capture_output=True, text=True,
                timeout=_SUBPROCESS_TIMEOUT,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            print(f"{name}: subprocess failed ({exc!r})", file=sys.stderr)
            return []
        if not self.ok_returncode(result.returncode):
            print(f"{name}: exited {result.returncode}: {result.stderr[:200]}",
                  file=sys.stderr)
            return []
        try:
            payload = (json.loads(result.stdout) if result.stdout
                       else self.empty_payload())
        except json.JSONDecodeError as exc:
            print(f"{name}: JSON parse failed ({exc})", file=sys.stderr)
            return []
        return self.map_payload(payload)
