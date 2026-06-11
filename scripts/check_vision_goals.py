"""Spec 149 Slice 1 — `vision_goals:` frontmatter validator.

The drift-derivation chain anchor (`Plan/_planning/charter.md`) wants every spec
to declare its Vision-goal mapping in frontmatter so the alignment matrix
(Spec 191), per-spec Followup (Spec 269), and closing audit (Spec 261) can
all derive from one source. This script ships first because every later piece
of 149 depends on the frontmatter being machine-readable.

Pattern follows Spec 054 (drift management): a BASELINE file
(`Plan/_planning/vision-goals-baseline.txt`) tracks the existing gap so CI
gates on REGRESSION only — adding a new spec without `vision_goals:` fails;
the historical gaps are documented, not blocked. Backfill of the original
specs is a separate follow-up.

Exit codes (per Spec 169 CI-gate doctrine):
- 0 — no regressions; baseline OK; optionally `baseline_shrinkable` listed
  for the author to trim
- 1 — at least one regression (a non-baseline spec lacks valid `vision_goals:`)
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

# GOALS.md ships exactly 8 Vision goals. The validator does not silently widen.
_VALID_GOALS = frozenset(range(1, 9))


def valid_goals() -> set[int]:
    """The set of legal Goal IDs per `docs/vision/GOALS.md`."""
    return set(_VALID_GOALS)


# ── frontmatter parsing ──────────────────────────────────────────────────────
def parse_frontmatter(body: str) -> dict:
    """Parse the YAML frontmatter block at the top of a spec file. Returns the
    parsed dict; returns `{}` when there's no frontmatter or when YAML parsing
    fails (a malformed spec is treated as missing — Spec 058 fail-closed)."""
    if not body.startswith("---\n"):
        return {}
    end = body.find("\n---\n", 4)
    if end == -1:
        return {}
    raw = body[4:end]
    try:
        import yaml                                                            # pyyaml is a core dep
        loaded = yaml.safe_load(raw)
    except Exception:
        return {}
    return loaded if isinstance(loaded, dict) else {}


# ── per-spec rules ───────────────────────────────────────────────────────────
@dataclass
class SpecResult:
    spec_id: str
    path: Path
    ok: bool
    code: str                                                                  # "ok"|"missing"|"empty"|"invalid"
    detail: str = ""

    def __post_init__(self):
        # Allow `path` to be either Path or string for ergonomic construction.
        if isinstance(self.path, str):
            self.path = Path(self.path)


def _spec_id_from_dir(path: Path) -> str:
    """Extract the NNN spec-id from `Plan/NNN-slug/spec.md`. Falls back to the
    parent dir name if the parse fails (better than a crash on weird folders)."""
    parent = path.parent.name
    head = parent.split("-", 1)[0]
    return head if head.isdigit() else parent


def check_spec(path: Path) -> SpecResult:
    """Audit one spec.md. The rule:
    - `vision_goals:` must be present in the YAML frontmatter
    - it must be a non-empty list of unique integers in {1..8}
    """
    spec_id = _spec_id_from_dir(path)
    try:
        body = path.read_text()
    except OSError as exc:
        return SpecResult(spec_id, path, False, "missing", f"read failed: {exc}")
    fm = parse_frontmatter(body)
    if "vision_goals" not in fm:
        return SpecResult(spec_id, path, False, "missing",
                          "no `vision_goals:` field in frontmatter")
    val = fm["vision_goals"]
    if not isinstance(val, list):
        return SpecResult(spec_id, path, False, "invalid",
                          f"vision_goals must be a list, got {type(val).__name__}")
    if not val:
        return SpecResult(spec_id, path, False, "empty",
                          "vision_goals is an empty list")
    if len(val) != len(set(val)):
        return SpecResult(spec_id, path, False, "invalid",
                          f"duplicate goal IDs: {val}")
    for g in val:
        if not isinstance(g, int):
            return SpecResult(spec_id, path, False, "invalid",
                              f"non-int entry: {g!r}")
        if g not in _VALID_GOALS:
            return SpecResult(spec_id, path, False, "invalid",
                              f"goal {g} not in {{1..8}} (GOALS.md)")
    return SpecResult(spec_id, path, True, "ok")


def check_tree(root: Path) -> list[SpecResult]:
    """Audit every `*/spec.md` directly under `root`. Sorted by spec_id for
    deterministic output (Spec 149 idempotence invariant)."""
    paths = sorted(root.glob("*/spec.md"))
    return [check_spec(p) for p in paths]


# ── baseline + CI gate (Spec 054 drift pattern) ──────────────────────────────
@dataclass
class CheckReport:
    """The `GoalsCheck.run()` payload. `regressions` is the CI-fail list;
    `baseline_shrinkable` is an author-facing prompt to clean the baseline."""

    regressions: list[str] = field(default_factory=list)
    baseline_missing: set[str] = field(default_factory=set)
    baseline_shrinkable: set[str] = field(default_factory=set)
    results: list[SpecResult] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return 1 if self.regressions else 0


@dataclass
class GoalsCheck:
    root: Path
    baseline: set[str]

    def run(self) -> CheckReport:
        results = check_tree(self.root)
        rep = CheckReport(results=results)
        for r in results:
            if r.ok:
                # If a spec was in the baseline but is now fixed, surface it so
                # the author can trim the baseline (the "shrinkable" prompt).
                if r.spec_id in self.baseline:
                    rep.baseline_shrinkable.add(r.spec_id)
                continue
            # Failed audit: either a baseline-tracked gap or a real regression.
            if r.spec_id in self.baseline:
                rep.baseline_missing.add(r.spec_id)
            else:
                rep.regressions.append(r.spec_id)
        rep.regressions.sort()
        return rep


def load_baseline(path: Path) -> set[str]:
    """Read a baseline file. One spec_id per line; `#` comments + blank lines
    ignored. Missing file returns an empty set."""
    if not path.exists():
        return set()
    out: set[str] = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.add(line)
    return out


# ── CLI entry point ──────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", default="Plan",
                        help="root directory holding `<id>-slug/spec.md` (default: Plan)")
    parser.add_argument("--baseline", default="Plan/_planning/vision-goals-baseline.txt",
                        help="baseline file path")
    args = parser.parse_args(argv)
    root = Path(args.root)
    baseline = load_baseline(Path(args.baseline))
    chk = GoalsCheck(root=root, baseline=baseline)
    rep = chk.run()
    if rep.regressions:
        print(f"REGRESSION — {len(rep.regressions)} spec(s) lack valid "
              f"`vision_goals:` and are NOT in the baseline:")
        for sid in rep.regressions:
            for r in rep.results:
                if r.spec_id == sid:
                    print(f"  {sid}  {r.code:8}  {r.detail}")
                    break
        print("\nFix: add `vision_goals: [int, ...]` (Goal IDs 1..8 per GOALS.md) "
              "to each spec's frontmatter.")
    else:
        print(f"OK — no regressions ({len(rep.baseline_missing)} baseline-tracked "
              f"gaps; {len(rep.baseline_shrinkable)} shrinkable from baseline).")
        if rep.baseline_shrinkable:
            print("Baseline-shrinkable (now have valid vision_goals — remove from "
                  "Plan/_planning/vision-goals-baseline.txt):")
            for sid in sorted(rep.baseline_shrinkable):
                print(f"  {sid}")
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
