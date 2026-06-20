"""Spec 269 — per-spec Followup Implementation Status: derived FollowupBlock.

Per CLAUDE.md rule 4 the per-spec deep state lives in each spec.md's
`## Followup — Implementation Status` section. Its COMPUTED metrics are
drift-prone when hand-authored: a test file moves, a box gets checked, a
commit lands. This derives them from the same live source as the TODO row:

  - test_count    — from `affects:` + a pytest collection (Spec 149 deriver)
  - done_when_*   — parsed `- [ ]` / `- [x]` checkbox state in `## Done When`
  - recent_commits— `git log` filtered by `affects:` paths (live, never frozen)
  - status        — frontmatter `status:`

Hand-written Done/Still prose is preserved untouched in a `<!-- hand -->`
zone; only the `<!-- derived:followup -->` fence carries the derived block
(reuses Spec 149 Slice 2.2's fence engine). Pure functions importable as
`scripts.followup_derive`.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from scripts.derive_docs import (
    derive_test_counts, find_fence, parse_affects, rewrite_fence,
    _spec_id_from_dir,
)
from scripts.check_vision_goals import parse_frontmatter

# named tunable (OQ1) — bounded recent-commit window for the rendered block.
RECENT_COMMITS_N = 5

_DONE_WHEN_RE = re.compile(r"^##\s+Done When\s*$", re.MULTILINE)
_NEXT_HEADING_RE = re.compile(r"^##\s+", re.MULTILINE)
_CHECKBOX_RE = re.compile(r"^\s*-\s*\[([ xX])\]", re.MULTILINE)


# ── Done-When checkbox parse ──────────────────────────────────────────────────
def parse_done_when(spec_text: str) -> tuple[int, int]:
    """`(checked, total)` for the `- [ ]`/`- [x]` boxes in the `## Done When`
    section ONLY (boxes elsewhere are ignored). `(0, 0)` when the section is
    absent — a spec with no Done-When list contributes no ratio."""
    m = _DONE_WHEN_RE.search(spec_text)
    if not m:
        return (0, 0)
    rest = spec_text[m.end():]
    nxt = _NEXT_HEADING_RE.search(rest)
    section = rest[: nxt.start()] if nxt else rest
    boxes = _CHECKBOX_RE.findall(section)
    checked = sum(1 for b in boxes if b.lower() == "x")
    return (checked, len(boxes))


# ── recent commits (live git log over affects paths) ──────────────────────────
def recent_commits(affects: list[str], *, n: int = RECENT_COMMITS_N,
                   cwd: Path | None = None) -> list[str]:
    """Last `n` `git log --oneline` lines touching ANY `affects:` path. Live,
    re-derived each run; `[]` when affects is empty or git is unavailable."""
    paths = [a for a in affects if a]
    if not paths:
        return []
    try:
        out = subprocess.run(
            ["git", "log", f"-{int(n)}", "--oneline", "--", *paths],
            cwd=str(cwd) if cwd else None,
            capture_output=True, text=True, timeout=20, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


# ── typed shape ───────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class FollowupBlock:
    """The derived, computed metrics for one spec's Followup section. `done_pct`
    is derived (never stored); a timestamp is intentionally OMITTED so re-running
    produces a byte-identical block (the determinism invariant)."""
    spec_id: str
    status: str
    test_files: tuple[str, ...]
    test_count: int
    done_when_checked: int
    done_when_total: int
    recent_commits: tuple[str, ...]

    @property
    def done_pct(self) -> float:
        return (self.done_when_checked / self.done_when_total
                if self.done_when_total else 0.0)


def status_consistent(block: FollowupBlock) -> bool:
    """Audit invariant: `done_pct == 1.0 ⇔ status == 'shipped'`. A spec with
    every Done-When box checked should be shipped, and a shipped spec should
    have them all checked. Specs with NO boxes (total 0) are exempt — there is
    nothing to check. (Slice 1 exposes this as an audit helper; gating the live
    tree on it is Slice 2 — many shipped specs leave the boxes unchecked.)"""
    if block.done_when_total == 0:
        return True
    return (block.done_pct == 1.0) == (block.status == "shipped")


# ── derivation ────────────────────────────────────────────────────────────────
def _test_files(affects: list[str]) -> list[str]:
    return [a for a in affects if a.startswith("tests/")]


def _repo_root(spec_path: Path) -> Path:
    # Plan/NNN-slug/spec.md -> repo root is three parents up.
    p = spec_path.resolve()
    return p.parents[2] if len(p.parents) >= 3 else p.parent


def derive_block(spec_path: Path, *, counts: dict[str, int],
                 with_commits: bool = True) -> FollowupBlock:
    """Compute one spec's FollowupBlock from the live sources. `counts` is the
    `parse_collect_output` map (Spec 149); pass `{}` to skip test counting."""
    text = spec_path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    affects = parse_affects(spec_path)
    checked, total = parse_done_when(text)
    commits = (recent_commits(affects, cwd=_repo_root(spec_path))
               if with_commits else [])
    return FollowupBlock(
        spec_id=str(fm.get("spec_id") or _spec_id_from_dir(spec_path)),
        status=str(fm.get("status", "draft")),
        test_files=tuple(_test_files(affects)),
        test_count=derive_test_counts(affects=affects, counts=counts),
        done_when_checked=checked,
        done_when_total=total,
        recent_commits=tuple(commits),
    )


# ── render ────────────────────────────────────────────────────────────────────
def render_block(block: FollowupBlock) -> str:
    """Deterministic markdown for the `<!-- derived:followup -->` fence. No
    timestamp (determinism); hand-prose lives outside the fence."""
    pct = f"{block.done_pct * 100:.0f}%"
    lines = [
        f"- **status:** {block.status}",
        f"- **Done-When:** {block.done_when_checked}/{block.done_when_total} "
        f"checked ({pct})",
        f"- **test files:** {', '.join(block.test_files) or '(none)'}",
        f"- **test count:** {block.test_count}",
    ]
    if block.recent_commits:
        lines.append("- **recent commits:**")
        lines += [f"  - {c}" for c in block.recent_commits]
    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────────
def _collect_counts(plan_root: Path) -> dict[str, int]:
    """Run `pytest --collect-only -q` once and parse it into {test_file: count}.
    Empty on failure — test_count degrades to 0, never crashes the deriver."""
    from scripts.derive_docs import parse_collect_output
    try:
        out = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            cwd=str(plan_root.parent if plan_root.name == "Plan" else plan_root),
            capture_output=True, text=True, timeout=300, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    return parse_collect_output(out.stdout)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--spec", type=Path, default=None,
                        help="one spec.md; default walks --plan-root")
    parser.add_argument("--plan-root", type=Path, default=Path("Plan"))
    parser.add_argument("--no-counts", action="store_true",
                        help="skip the pytest collection (test_count = 0)")
    parser.add_argument("--write", action="store_true",
                        help="rewrite each spec's `<!-- derived:followup -->` "
                             "fence in place (only specs that declare one)")
    args = parser.parse_args(argv)

    counts = {} if args.no_counts else _collect_counts(args.plan_root)
    specs = ([args.spec] if args.spec
             else sorted(args.plan_root.glob("*/spec.md")))

    written = 0
    for sp in specs:
        block = derive_block(sp, counts=counts)
        rendered = render_block(block)
        if not args.write:
            print(f"# {block.spec_id}\n{rendered}\n")
            continue
        text = sp.read_text(encoding="utf-8")
        if find_fence(text, "followup") is None:
            continue   # opt-in: only specs that declare the fence
        sp.write_text(rewrite_fence(text, "followup", rendered), encoding="utf-8")
        written += 1
    if args.write:
        print(f"updated {written} followup fence(s)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
