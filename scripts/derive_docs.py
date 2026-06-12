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
# Codex review on PR #132: parametrized test IDs can carry spaces (custom
# id like `[case a]`), so the node part is `.+` (rest of line), not `\S+`.
_TEST_NODE_RE = re.compile(r"^(?P<file>tests/[^:\s]+\.py)::(?P<node>.+)$")


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


# ── Slice 2.2 — HTML-comment fence rewrite ────────────────────────────────
# `<!-- derived:<id> -->` … `<!-- /derived:<id> -->` HTML-comment markers
# delimit a derived zone in spec.md. `rewrite_fence` replaces ONLY the
# content between the markers; everything outside is byte-preserved. An
# opening marker without a matching close raises ValueError (Slice 2.4
# promotes to `Codes.DERIVE_FENCE_BROKEN`).
def _fence_markers(fence_id: str) -> tuple[str, str]:
    return (f"<!-- derived:{fence_id} -->", f"<!-- /derived:{fence_id} -->")


def find_fence(text: str, fence_id: str) -> tuple[int, int] | None:
    """Return `(inner_start, inner_end)` byte offsets for the FIRST
    fence with the given id; None when the opening marker is absent.
    Raises ValueError when the opening marker exists but is unclosed."""
    open_m, close_m = _fence_markers(fence_id)
    open_at = text.find(open_m)
    if open_at < 0:
        return None
    # Inner content begins on the line AFTER the opening marker.
    inner_start = open_at + len(open_m)
    # Skip the newline that terminates the marker line, if any.
    if inner_start < len(text) and text[inner_start] == "\n":
        inner_start += 1
    close_at = text.find(close_m, inner_start)
    if close_at < 0:
        raise ValueError(
            f"unclosed fence: `<!-- derived:{fence_id} -->` opened at "
            f"byte {open_at} has no matching `<!-- /derived:{fence_id} -->`")
    return inner_start, close_at


def rewrite_fence(text: str, fence_id: str, new_content: str) -> str:
    """Replace the content between the fence's open + close markers with
    `new_content`. When the fence is absent, return text unchanged.
    When the opening marker is unclosed, raises ValueError.

    `new_content` SHOULD end in a newline so the closing marker stays on
    its own line; callers passing a string without a trailing newline get
    one synthesized for them (idempotence convenience)."""
    span = find_fence(text, fence_id)
    if span is None:
        return text
    inner_start, inner_end = span
    if new_content and not new_content.endswith("\n"):
        new_content = new_content + "\n"
    return text[:inner_start] + new_content + text[inner_end:]


def render_fence_content(fence_id: str, derivation: "Derivation") -> str:
    """Render the canonical content for a known fence id from a typed
    Derivation. Slice 2.2 ships ONE fence kind (`test-count`); future
    slices add more (`vision-goals`, `followup-status`, …)."""
    if fence_id == "test-count":
        affects_str = ", ".join(derivation.affects_files) or "(none)"
        return (
            f"_test_count: **{derivation.test_count}** "
            f"(derived from `affects:` {affects_str})_\n"
        )
    return ""


_KNOWN_FENCES = ("test-count",)


def apply_derivations_to_spec_text(text: str, derivation: "Derivation") -> str:
    """Walk every known fence id; rewrite the ones present in `text`.
    Unknown fence ids are left alone — the author opts in by adding a
    marker pair for the fence kinds they want derived."""
    out = text
    for fid in _KNOWN_FENCES:
        try:
            content = render_fence_content(fid, derivation)
        except Exception:
            content = ""
        if not content:
            continue
        out = rewrite_fence(out, fid, content)
    return out


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
    # Codex review (round 2): on a non-zero exit pytest may still emit
    # SOME collected nodeids before the error report. Parsing that
    # partial stdout would silently undercount affected specs; the
    # documented behavior is empty-on-failure so a transient
    # import/collection error doesn't quietly skew the derivation.
    if result.returncode != 0:
        return {}
    return parse_collect_output(result.stdout)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--plan-root", default="Plan",
                        help="root directory holding `<id>-slug/spec.md` (default: Plan)")
    parser.add_argument("--write", action="store_true",
                        help="rewrite spec.md derived zones in-place via "
                             "`<!-- derived:<id> -->` HTML fences (Slice 2.2)")
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
    if args.write:
        # Slice 2.2 — write side: rewrite derived zones in every spec.md
        # that DECLARES a fence. Hand-prose untouched; specs without
        # fences are no-op.
        plan_root = Path(args.plan_root)
        touched: list[str] = []
        per_spec = {d.spec_id: d for d in rep.derivations}
        for sp in sorted(plan_root.glob("*/spec.md")):
            spec_id = _spec_id_from_dir(sp)
            d = per_spec.get(spec_id)
            if d is None:
                continue
            src = sp.read_text(encoding="utf-8")
            try:
                out = apply_derivations_to_spec_text(src, d)
            except ValueError as e:
                print(f"  ! {sp}: {e}")
                continue
            if out != src:
                sp.write_text(out, encoding="utf-8")
                touched.append(str(sp))
        print(f"  wrote {len(touched)} spec.md files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
