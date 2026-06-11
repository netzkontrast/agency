"""Spec 149 Slice 2 — `derive-docs` core derivation library.

Spec 149 Slice 1 shipped the `vision_goals:` frontmatter validator + 129-
spec baseline. Slice 2 ships the DERIVATION engine that closes the drift
gap: per-spec test counts derived from `pytest --collect-only` keyed by
`affects:` test files, so the alignment matrix stops carrying hand-
authored counts that rot on every PR.

This slice (2.1) ships:
- Pure functions: `parse_affects(path)`, `parse_collect_output(text)`,
  `derive_test_counts(affects, counts)`.
- Typed shapes: `Derivation(spec_id, test_count, affects_files)`,
  `DeriveReport(derivations)`.
- `derive_tree(plan_root, counts)` rollup walking `<plan>/*/spec.md`.
- CLI: `python -m scripts.derive_docs --dry-run` runs
  `pytest --collect-only -q` against the live tree, derives every spec,
  prints the per-spec test count list (informational only — Slice 2.2
  rewrites spec.md derived zones).

Slice 2.2+: write derived zones via `<!-- derived:<section> -->` fences;
Slice 2.3 — `check-doc-drift` integration (CI gate); Slice 2.4 — Codes
additions (`DERIVE_AMBIGUOUS`, `DERIVE_MISSING_GOAL`, `DERIVE_FENCE_BROKEN`).

Pattern follows Spec 149 Slice 1 — pure functions importable as
`scripts.derive_docs`, typed shapes, CLI exit codes per Spec 169 doctrine.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ── parse_affects ──────────────────────────────────────────────────────────
def parse_affects(spec_path: Path) -> list[str]:
    """Read the `affects:` field from a spec.md frontmatter block.
    Returns the list of strings; absent / malformed → empty list.
    Non-string entries are silently dropped (Slice 2.4 will surface them
    via `Codes.DERIVE_AMBIGUOUS`)."""
    try:
        body = spec_path.read_text(encoding="utf-8")
    except OSError:
        return []
    if not body.startswith("---\n"):
        return []
    end = body.find("\n---\n", 4)
    if end == -1:
        return []
    raw = body[4:end]
    try:
        import yaml
        fm = yaml.safe_load(raw)
    except Exception:
        return []
    if not isinstance(fm, dict):
        return []
    raw_list = fm.get("affects") or []
    if not isinstance(raw_list, list):
        return []
    return [v for v in raw_list if isinstance(v, str)]


# ── parse_collect_output ───────────────────────────────────────────────────
# `pytest --collect-only -q` emits one line per test as
# `tests/test_foo.py::test_bar`. Summary footers and blank lines are ignored.
_TEST_NODE_RE = re.compile(r"^(?P<file>tests/[^:\s]+\.py)::(?P<node>\S+)$")


def parse_collect_output(text: str) -> dict[str, int]:
    """Turn `pytest --collect-only -q` output into a {test_file: count}
    map. Parametrized tests show up with `[param]` suffixes — counted as
    distinct tests per the pytest convention."""
    counts: dict[str, int] = {}
    for line in text.split("\n"):
        m = _TEST_NODE_RE.match(line.strip())
        if not m:
            continue
        counts[m.group("file")] = counts.get(m.group("file"), 0) + 1
    return counts


# ── per-spec + tree-wide derivation ────────────────────────────────────────
@dataclass(frozen=True)
class Derivation:
    """The Slice 2 derivation payload for ONE spec."""

    spec_id: str
    test_count: int
    affects_files: tuple[str, ...] = ()


@dataclass
class DeriveReport:
    """Tree-wide derivation rollup. Slice 2.3 adds drift detection."""

    derivations: list[Derivation] = field(default_factory=list)


def derive_test_counts(*, affects: list[str], counts: dict[str, int]) -> int:
    """Sum the test counts of every `affects:` file; missing files
    contribute 0 (a spec may legitimately list a test file with no
    @pytest.mark yet)."""
    return sum(counts.get(f, 0) for f in affects)


def _spec_id_from_dir(path: Path) -> str:
    """Extract NNN from `Plan/NNN-slug/spec.md` (falls back to parent name)."""
    head = path.parent.name.split("-", 1)[0]
    return head if head.isdigit() else path.parent.name


def derive_spec(spec_path: Path, *, counts: dict[str, int]) -> Derivation:
    """Derive ONE spec's typed payload from the live test-count map."""
    spec_id = _spec_id_from_dir(spec_path)
    affects = parse_affects(spec_path)
    test_count = derive_test_counts(affects=affects, counts=counts)
    return Derivation(spec_id=spec_id, test_count=test_count,
                      affects_files=tuple(affects))


def derive_tree(plan_root: Path, *, counts: dict[str, int]) -> DeriveReport:
    """Walk `<plan_root>/*/spec.md` deterministically; derive each spec."""
    paths = sorted(Path(plan_root).glob("*/spec.md"))
    return DeriveReport(
        derivations=[derive_spec(p, counts=counts) for p in paths])


# ── CLI entry ──────────────────────────────────────────────────────────────
def _collect_live_test_counts(repo_root: Path) -> dict[str, int]:
    """Run `pytest --collect-only -q` and parse its output into a
    test-file → count map. Returns an empty map when pytest collection
    fails (e.g. import error in tests/) so the CLI can still render the
    structural derivation without crashing."""
    try:
        result = subprocess.run(
            # Codex review on PR #132: use sys.executable so direct venv
            # invocation (`.venv/bin/python -m scripts.derive_docs`)
            # collects against the same environment that has the project
            # deps installed — not the ambient `python` on PATH which
            # may lack `fastmcp`, etc. and silently exit with all counts
            # zero.
            [sys.executable, "-m", "pytest", "--collect-only", "-q",
             "-p", "no:warnings"],
            cwd=str(repo_root),
            capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    return parse_collect_output(result.stdout)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--plan-root", default="Plan",
                        help="root directory holding `<id>-slug/spec.md` (default: Plan)")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="print derived payload without rewriting spec.md "
                             "(Slice 2.2 ships --write)")
    parser.add_argument("--repo-root", default=".",
                        help="repo root (for the pytest collect call)")
    args = parser.parse_args(argv)
    counts = _collect_live_test_counts(Path(args.repo_root))
    rep = derive_tree(Path(args.plan_root), counts=counts)
    print(f"derive-docs: {len(rep.derivations)} specs, "
          f"{sum(d.test_count for d in rep.derivations)} test count total")
    # Sort by test_count desc to surface the highest-leverage specs first.
    sorted_d = sorted(rep.derivations,
                      key=lambda d: -d.test_count)
    for d in sorted_d[:20]:
        if not d.test_count:
            continue
        print(f"  {d.spec_id}  {d.test_count:>4}  ({len(d.affects_files)} affects)")
    # Slice 2.1: informational only. Slice 2.3 will gate via
    # check-doc-drift; for now always returns 0 unless `--repo-root`
    # was misconfigured.
    return 0


if __name__ == "__main__":
    sys.exit(main())
