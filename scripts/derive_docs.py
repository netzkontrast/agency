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

from agency.toolresult import Codes
from scripts._spec_tree import spec_files


class DeriveError(ValueError):
    """Typed derive-docs failure (Spec 149 Slice 2.4).
    Subclasses ValueError for backwards-compatible ``except ValueError`` sites.
    ``code`` is a ``Codes.DERIVE_*`` constant value."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


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
    """Walk every lifecycle `spec.md` deterministically; derive each spec.
    Spec 357 — the shared `spec_files` walker handles the state-folder nesting."""
    paths = spec_files(plan_root)
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
        raise DeriveError(
            Codes.DERIVE_FENCE_BROKEN,
            f"unclosed fence: `<!-- derived:{fence_id} -->` opened at "
            f"byte {open_at} has no matching `<!-- /derived:{fence_id} -->`",
        )
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


# ── Spec 389: code-introspection fences for hand-authored reference docs ──────
# The Spec 149 fence engine derives per-spec facts (`test-count`) from a typed
# `Derivation`. Spec 389 adds a SECOND family: fences whose content is derived
# from the LIVE engine, not a per-spec object — the mechanically-derivable
# fragments a hand doc copies from code (the `SUBSTRATE_TOOLS` roster, a
# capability's verb list, the driver-boundary set). An author opts a fragment in
# by wrapping it in `<!-- derived:<kind> -->` … `<!-- /derived:<kind> -->`;
# `--write-docs` regenerates the fence from code, prose outside stays byte-exact.

_DOC_FENCE_OPEN_RE = re.compile(r"<!--\s*derived:([A-Za-z0-9:_-]+)\s*-->")

_LIVE_ENGINE = None


def _live_engine():
    """A throwaway in-process Engine for live introspection, built once and
    cached. Lazy: only the boundary/verb fences need it; the `substrate-tools`
    fence reads a module-level tuple, so a doc that only uses that fence never
    pays the Engine-build cost."""
    global _LIVE_ENGINE
    if _LIVE_ENGINE is None:
        import tempfile

        from agency.engine import Engine
        _LIVE_ENGINE = Engine(tempfile.mktemp(suffix=".db"),
                              _require_skill_doc=False)
    return _LIVE_ENGINE


def _inline_code(names: list[str]) -> str:
    """`a`, `b`, `c` — names rendered as inline code, comma-joined."""
    return ", ".join(f"`{n}`" for n in names)


def render_substrate_tools() -> str:
    """The wire-name roster of `SUBSTRATE_TOOLS` (the engine's non-verb tools),
    in declaration order. Source: `agency/_substrate_tools.py`."""
    from agency._substrate_tools import SUBSTRATE_TOOLS
    names = [t.name for t in SUBSTRATE_TOOLS]
    return (f"The **{len(names)}** substrate tools (`SUBSTRATE_TOOLS`): "
            f"{_inline_code(names)}.\n")


def render_driver_boundaries() -> str:
    """The named driver/boundary set the engine registers (Spec 002), sorted.
    Source: `agency/engine.py::_boundary_defaults` (read live via the registry)."""
    names = sorted(_live_engine().drivers.names())
    return f"The **{len(names)}** driver boundaries: {_inline_code(names)}.\n"


def render_capability_verbs(cap: str) -> str:
    """A capability's verb roster, sorted. Source: the live registry."""
    verbs = sorted(_live_engine().registry.get(cap).verbs.keys())
    return f"`{cap}` — **{len(verbs)}** verbs: {_inline_code(verbs)}.\n"


#: Fixed-id code-introspection fences. Parametrised kinds (e.g.
#: `capability-verbs:<cap>`) are resolved by `doc_fence_content`.
DOC_FENCE_RENDERERS = {
    "substrate-tools": render_substrate_tools,
    "driver-boundaries": render_driver_boundaries,
}


def doc_fence_content(fence_id: str) -> str | None:
    """Render the canonical content for a code-introspection fence id, or None
    when the id is not a known code-introspection kind (so callers leave
    spec-only fences like `test-count` and unknown ids untouched)."""
    if fence_id in DOC_FENCE_RENDERERS:
        return DOC_FENCE_RENDERERS[fence_id]()
    if fence_id.startswith("capability-verbs:"):
        return render_capability_verbs(fence_id.split(":", 1)[1])
    return None


def doc_fence_ids(text: str) -> list[str]:
    """Every code-introspection fence id opened in `text`, in order, de-duped.
    Only OPEN markers (`<!-- derived:X -->`) match — the close marker
    (`<!-- /derived:X -->`) carries a leading `/` the regex excludes. Spec-only
    fences (`test-count`) and unknown ids are NOT returned — this family is the
    code-introspection one."""
    seen: list[str] = []
    for m in _DOC_FENCE_OPEN_RE.finditer(text):
        fid = m.group(1)
        if fid not in seen and (fid in DOC_FENCE_RENDERERS
                                or fid.startswith("capability-verbs:")):
            seen.append(fid)
    return seen


def apply_doc_fences(text: str) -> str:
    """Regenerate every code-introspection fence present in `text` from live
    code. Prose outside the fences is byte-preserved. Raises ``DeriveError``
    (``Codes.DERIVE_FENCE_BROKEN``) on an opened-but-unclosed fence — reusing
    the Spec 149 fence contract."""
    out = text
    for fid in doc_fence_ids(text):
        content = doc_fence_content(fid)
        if content is None:
            continue
        out = rewrite_fence(out, fid, content)
    return out


def doc_has_derived_drift(text: str) -> bool:
    """True iff regenerating `text`'s code-introspection fences would change it
    — i.e. a fence is stale. The discriminator behind Spec 389's `check-doc-drift`
    integration: a stale doc this returns True for is AUTO-resolvable (run
    `--write-docs`); a stale doc with no derived drift is genuine prose drift
    (hand-review). A doc with no derived fences is never derived-drifting."""
    if not doc_fence_ids(text):
        return False
    return apply_doc_fences(text) != text


def derive_docs_pass(docs_root: Path, *, write: bool = False
                     ) -> tuple[list[Path], list[tuple[Path, str]]]:
    """Walk `<docs_root>/**/*.md`; regenerate code-introspection fences. Returns
    `(changed, broken)` — docs whose fences were stale (rewritten when
    `write=True`) and docs with a fence error. Docs without derived fences are
    skipped untouched."""
    changed: list[Path] = []
    broken: list[tuple[Path, str]] = []
    for doc in sorted(docs_root.rglob("*.md")):
        text = doc.read_text(encoding="utf-8")
        if not doc_fence_ids(text):
            continue
        try:
            out = apply_doc_fences(text)
        except ValueError as e:
            broken.append((doc, str(e)))
            continue
        if out != text:
            changed.append(doc)
            if write:
                doc.write_text(out, encoding="utf-8")
    return changed, broken


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


def spec_has_drift(text: str, derivation: "Derivation") -> str | None:
    """Return a compact unified-diff hint string if the spec text's derived
    zones are stale (i.e. `--write` would change them); None when the zones
    are up to date OR the spec declares no known fences (opt-in model).

    Raises ValueError when a fence is opened-but-unclosed (same as
    `apply_derivations_to_spec_text`).
    """
    has_fence = any(f"<!-- derived:{fid} -->" in text for fid in _KNOWN_FENCES)
    if not has_fence:
        return None
    expected = apply_derivations_to_spec_text(text, derivation)
    if expected == text:
        return None
    import difflib
    diff = list(difflib.unified_diff(
        text.splitlines(keepends=True),
        expected.splitlines(keepends=True),
        fromfile="current",
        tofile="derived",
        n=2,
    ))
    return "".join(diff[:40])


def check_derivation_drift(plan_root: Path, *,
                           counts: dict[str, int]) -> list[tuple[Path, str]]:
    """Walk `<plan_root>/*/spec.md`; return `(path, diff_hint)` for every
    spec whose derived zones diverge from the live derivation. Empty list =
    all clean (or no specs declare derived fences)."""
    rep = derive_tree(plan_root, counts=counts)
    per_spec = {d.spec_id: d for d in rep.derivations}
    stale: list[tuple[Path, str]] = []
    for sp in spec_files(plan_root):
        spec_id = _spec_id_from_dir(sp)
        d = per_spec.get(spec_id)
        if d is None:
            continue
        src = sp.read_text(encoding="utf-8")
        try:
            hint = spec_has_drift(src, d)
        except ValueError as e:
            stale.append((sp, f"FENCE ERROR: {e}"))
            continue
        if hint is not None:
            stale.append((sp, hint))
    return stale


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
    parser.add_argument("--check", action="store_true",
                        help="check derived zones for drift; exit 1 if any "
                             "spec has stale content (Slice 2.3 CI gate)")
    parser.add_argument("--repo-root", default=".",
                        help="repo root (for the pytest collect call)")
    parser.add_argument("--docs-root", default="docs",
                        help="root for the Spec 389 code-introspection doc fences "
                             "(default: docs)")
    parser.add_argument("--write-docs", action="store_true",
                        help="Spec 389 — regenerate code-introspection fences "
                             "(`substrate-tools`/`driver-boundaries`/`capability-verbs:<cap>`) "
                             "in `<docs-root>/**/*.md` from live code")
    parser.add_argument("--check-docs", action="store_true",
                        help="Spec 389 — check doc fences for drift; exit 1 if any "
                             "`<docs-root>` fence is stale (CI gate)")
    args = parser.parse_args(argv)

    # Spec 389 — code-introspection fences over docs/ (independent of the
    # per-spec test-count derivation, which needs the pytest collect).
    if args.check_docs or args.write_docs:
        changed, broken = derive_docs_pass(Path(args.docs_root),
                                           write=args.write_docs)
        for doc, err in broken:
            print(f"  ! {doc}: {err}")
        if args.write_docs:
            for doc in changed:
                print(f"  wrote {doc}")
            print(f"derive-docs --write-docs: {len(changed)} doc(s) regenerated"
                  + (f", {len(broken)} broken" if broken else ""))
            return 1 if broken else 0
        # --check-docs
        if changed or broken:
            print(f"DOC-FENCE DRIFT: {len(changed)} doc(s) have stale derived "
                  f"fences — run `--write-docs` to regenerate")
            for doc in changed:
                print(f"    STALE  {doc}")
            return 1
        print("derive-docs --check-docs: all doc fences up to date")
        return 0

    counts = _collect_live_test_counts(Path(args.repo_root))
    if args.check:
        stale = check_derivation_drift(Path(args.plan_root), counts=counts)
        if stale:
            print(f"DERIVED-ZONE DRIFT: {len(stale)} spec(s) have stale "
                  f"derived zones — run `--write` to update")
            for sp, hint in stale:
                print(f"\n--- {sp}")
                if hint:
                    print(hint[:800])
            return 1
        print("derive-docs --check: all derived zones up to date (or no "
              "specs declare derived fences)")
        return 0
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
        for sp in spec_files(plan_root):
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
