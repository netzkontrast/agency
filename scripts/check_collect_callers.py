"""Spec 159 Slice 1 — derived audit of `dogfood.collect` callers.

Spec 150 closed the dogfood-loop pipeline (Slices 1+2: parse_amendment +
apply_amendment shipped). The legacy `dogfood.collect` verb is reached
from a shrinking set of callers; Spec 159 deprecates it by deriving the
caller count from the live tree + enforcing the monotonic-decrease
invariant once Slice 2 wires the gate.

This slice ships the pure audit + the typed report; Slice 2 promotes
to a CI gate (`scripts/check-drift` integration; caller_count must
not grow across PRs).
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path


_CALL_PATTERN = re.compile(r"dogfood\s*\.\s*collect\s*\(")


@dataclass(frozen=True)
class CallerSite:
    """One `dogfood.collect(...)` call site."""

    file: str
    line: int
    text: str


@dataclass
class CollectCallersReport:
    """Slice 1 audit payload. `callers` enumerates every
    `dogfood.collect(...)` call site found under the audited root,
    sorted by `(file, line)` for deterministic output. Slice 2 adds a
    `baseline` field + the monotone-decrease invariant."""

    callers:      list[CallerSite] = field(default_factory=list)

    @property
    def caller_count(self) -> int:
        return len(self.callers)


_SKIP_DIRS = ("__pycache__", "tests")


def audit_collect_callers(root: Path) -> CollectCallersReport:
    """Walk `<root>/**/*.py`; record every line matching the call
    pattern (`dogfood.collect(`). Skips `__pycache__` (build noise) +
    `tests/` (test fixtures legitimately reference the deprecated
    verb). Returns the typed CollectCallersReport sorted by file:line."""
    root = Path(root)
    rep = CollectCallersReport()
    if not root.exists():
        return rep
    for py in sorted(root.rglob("*.py")):
        if any(part in _SKIP_DIRS for part in py.parts):
            continue
        try:
            text = py.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            # Skip lines that are clearly comments / docstrings without
            # a call form. A bare `dogfood.collect` inside a comment isn't
            # a caller; require the `(`.
            stripped = line.lstrip()
            if stripped.startswith("#") or stripped.startswith('"""'):
                continue
            if _CALL_PATTERN.search(line):
                rep.callers.append(CallerSite(
                    file=str(py), line=i, text=line.strip()[:200]))
    rep.callers.sort(key=lambda c: (c.file, c.line))
    return rep


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", default="agency",
                        help="root dir to audit (default: agency)")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 if any caller remains (Slice 2 gate)")
    args = parser.parse_args(argv)
    rep = audit_collect_callers(Path(args.root))
    print(f"dogfood.collect callers: {rep.caller_count}")
    for c in rep.callers[:10]:
        print(f"  {c.file}:{c.line}  {c.text!r}")
    if len(rep.callers) > 10:
        print(f"  ... and {len(rep.callers) - 10} more")
    if args.strict and rep.callers:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
