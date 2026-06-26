"""Spec 191 — live vision-alignment matrix derivation.

Spec 072 produced the SPEC-VISION-ALIGNMENT matrix by hand; it goes stale
the first time a spec ships. With `vision_goals:` + `status:` on every
spec's frontmatter (Spec 149), the matrix should DERIVE from source: each
spec's Goal mapping comes from its frontmatter, each Goal's status from
its specs' shipped/partial/draft state.

Pure functions importable as `scripts.vision_matrix`; a thin CLI prints
the rendered matrix (`--write PATH` rewrites it into a
`<!-- derived:vision-matrix -->` fence, reusing Spec 149's fence engine).

The goal catalogue is DERIVED from `docs/vision/GOALS.md` (rule 8 — never
a hardcoded `range(1, 9)`; GOALS.md already carries 9 goals, so any frozen
count would lie).
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from scripts.check_vision_goals import parse_frontmatter

# ── named tunables (rule 8) — shipped-fraction thresholds for Goal status ─────
GREEN_FLOOR = 0.80
YELLOW_FLOOR = 0.50


# ── goal catalogue (derived from GOALS.md) ────────────────────────────────────
# A goal line looks like:  `1. **Token-efficient agentic loops.** ...`
_GOAL_RE = re.compile(r"^(\d+)\.\s+\*\*(.+?)\.?\*\*", re.MULTILINE)


def _goals_section(goals_md: str) -> str:
    """The text under the `## Goals` heading up to the next `## ` heading,
    so the numbered `## Non-goals` list never leaks into the catalogue."""
    start = goals_md.find("\n## Goals")
    if start == -1:
        return goals_md
    rest = goals_md[start + 1:]
    nxt = rest.find("\n## ", 1)
    return rest if nxt == -1 else rest[:nxt]


def parse_goals(goals_md: str) -> dict[int, str]:
    """`{goal_id: title}` parsed from GOALS.md's numbered bold list."""
    out: dict[int, str] = {}
    for m in _GOAL_RE.finditer(_goals_section(goals_md)):
        out[int(m.group(1))] = m.group(2).strip()
    return out


# ── status source: the TODO.md binding index (CLAUDE.md rule 4) ───────────────
# Spec status's source of truth is TODO.md's verdict roll-up, NOT each spec's
# frontmatter `status:` (which goes stale — most shipped specs still read
# "draft" in frontmatter). The matrix sources status from TODO and falls back
# to frontmatter only for specs the index doesn't mention.
_SHIPPED_ROW_RE = re.compile(r"^\|\s*\*\*Shipped\*\*\s*\|\s*\d+\s*\|(.+)\|\s*$", re.MULTILINE)
_PARTIAL_ROW_RE = re.compile(r"^\|\s*\*\*Partial[^|]*\*\*\s*\|\s*\d+\s*\|(.+)\|\s*$", re.MULTILINE)
_ID_RE = re.compile(r"\b(\d{3})\b")


def parse_status_index(todo_md: str) -> dict[str, str]:
    """`{spec_id: shipped|partial}` from TODO.md's verdict-count rows.
    Partial is applied first so a spec listed in BOTH resolves to shipped."""
    idx: dict[str, str] = {}
    m = _PARTIAL_ROW_RE.search(todo_md)
    if m:
        for sid in _ID_RE.findall(m.group(1)):
            idx[sid] = "partial"
    m = _SHIPPED_ROW_RE.search(todo_md)
    if m:
        for sid in _ID_RE.findall(m.group(1)):
            idx[sid] = "shipped"
    return idx


# ── status normalization ──────────────────────────────────────────────────────
def normalize_status(raw: str) -> str:
    """Bucket a free-form frontmatter `status:` into shipped|partial|not_started.

    Frontmatter carries values like ``shipped``, ``Partial (Slice 6 …)``,
    ``draft``, ``not started`` — normalize to the three matrix buckets.
    Unknown / missing → ``not_started`` (fail-closed, Spec 058)."""
    s = (raw or "").strip().lower()
    if s.startswith("shipped"):
        return "shipped"
    if "partial" in s:
        return "partial"
    return "not_started"


# ── typed shapes ──────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class SpecRef:
    """One spec's contribution to the matrix."""
    spec_id: str
    slug: str
    status: str            # normalized: shipped|partial|not_started
    goals: tuple[int, ...]


@dataclass(frozen=True)
class GoalRow:
    """One Goal's derived row — counts + fraction + status are COMPUTED."""
    goal_id: int
    title: str
    specs: tuple[SpecRef, ...]

    @property
    def shipped(self) -> int:
        return sum(s.status == "shipped" for s in self.specs)

    @property
    def partial(self) -> int:
        return sum(s.status == "partial" for s in self.specs)

    @property
    def not_started(self) -> int:
        return sum(s.status == "not_started" for s in self.specs)

    @property
    def shipped_fraction(self) -> float:
        return self.shipped / len(self.specs) if self.specs else 0.0

    @property
    def status(self) -> str:
        return goal_status(self.shipped_fraction)


def goal_status(frac: float) -> str:
    """green/yellow/red from the named shipped-fraction thresholds."""
    if frac >= GREEN_FLOOR:
        return "green"
    if frac >= YELLOW_FLOOR:
        return "yellow"
    return "red"


# ── collection + rollup ───────────────────────────────────────────────────────
def _spec_id(path: Path) -> str:
    head = path.parent.name.split("-", 1)[0]
    return head if head.isdigit() else path.parent.name


def collect_specs(plan_root: Path,
                  status_index: dict[str, str] | None = None) -> list[SpecRef]:
    """Every `Plan/*/spec.md` carrying a non-empty `vision_goals:` list.
    Specs without `vision_goals:` are skipped (the Spec 149 baseline gap);
    they surface in `check_vision_goals`, not here.

    ``status_index`` (from :func:`parse_status_index`) is the authoritative
    status source; a spec absent from it falls back to its frontmatter
    `status:`. Pass ``None`` to use frontmatter only (testing / no TODO).

    Spec 357 — specs live in physical STATE folders
    (``Plan/<state>/<NNN-slug>/spec.md``), so the collector globs RECURSIVELY
    (``**/spec.md``). The prior one-level glob (``*/spec.md``) silently matched
    ZERO specs post-migration, rendering an all-red all-zeros matrix."""
    refs: list[SpecRef] = []
    for sp in sorted(Path(plan_root).glob("**/spec.md")):
        fm = parse_frontmatter(sp.read_text(encoding="utf-8"))
        goals = fm.get("vision_goals")
        if not isinstance(goals, list):
            continue
        gids = tuple(g for g in goals if isinstance(g, int))
        if not gids:
            continue
        spec_id = str(fm.get("spec_id") or _spec_id(sp))
        status = (status_index or {}).get(spec_id) or normalize_status(str(fm.get("status", "")))
        refs.append(SpecRef(
            spec_id=spec_id,
            slug=str(fm.get("slug") or sp.parent.name.split("-", 1)[-1]),
            status=status,
            goals=gids,
        ))
    return refs


def build_rows(specs: list[SpecRef], goals: dict[int, str]) -> list[GoalRow]:
    """One GoalRow per catalogue goal, in id order; a spec joins every
    goal it lists. Goals with zero specs render an empty (red) row."""
    rows: list[GoalRow] = []
    for gid in sorted(goals):
        members = tuple(s for s in specs if gid in s.goals)
        rows.append(GoalRow(goal_id=gid, title=goals[gid], specs=members))
    return rows


def biggest_gaps(rows: list[GoalRow], n: int = 3) -> list[GoalRow]:
    """The `n` populated goals with the lowest shipped fraction (ties broken
    by goal id for determinism). Empty goals are excluded — a goal with no
    specs has no fraction to rank."""
    populated = [r for r in rows if r.specs]
    return sorted(populated, key=lambda r: (r.shipped_fraction, r.goal_id))[:n]


def coverage_report(specs: list[SpecRef], rows: list[GoalRow]) -> dict:
    """Rule-8 invariant evidence: no spec with `vision_goals:` is dropped,
    and no spec references a goal id absent from the catalogue."""
    placed = {s.spec_id for r in rows for s in r.specs}
    known = {r.goal_id for r in rows}
    orphan_specs = sorted({s.spec_id for s in specs} - placed)
    unknown_goal_refs = sorted(
        (s.spec_id, g) for s in specs for g in s.goals if g not in known
    )
    return {"orphan_specs": orphan_specs, "unknown_goal_refs": unknown_goal_refs}


# ── typed cell projection (Spec 191 Slice 2 — consume the AlignmentCell shape) ─
_STATUS_TO_ALIGNMENT = {"shipped": "aligned", "partial": "partial",
                        "not_started": "missing"}


def to_alignment_cells(rows: "list[GoalRow]") -> list:
    """Project the derived rows into the typed `AlignmentCell{spec_id, goal_id,
    status}` (one per spec×goal). The single matrix source feeds the typed shape
    — no second derivation. Goals beyond the shape's 1..8 range are skipped
    (``AlignmentCell`` caps ``goal_id`` at 8; Goal 9 renders in the table)."""
    from agency._typed_shapes_waves4_12 import AlignmentCell
    cells = []
    for row in rows:
        if not (1 <= row.goal_id <= 8):
            continue
        for spec in row.specs:
            cells.append(AlignmentCell(
                spec_id=spec.spec_id, goal_id=row.goal_id,
                status=_STATUS_TO_ALIGNMENT[spec.status]))
    return cells


def alignment_summary(plan_root: "Path | str" = "Plan",
                      goals_md: "Path | str" = "docs/vision/GOALS.md",
                      todo: "Path | str | None" = "TODO.md") -> dict:
    """A doctor-friendly roll-up of the live matrix: per-Goal status + the three
    biggest gaps + the coverage invariant. `ready` iff every spec with
    `vision_goals:` lands in a row (no orphans) and no goal ref is unknown."""
    plan_root = Path(plan_root)
    goals = parse_goals(Path(goals_md).read_text(encoding="utf-8"))
    todo_p = Path(todo) if todo else None
    status_index = (parse_status_index(todo_p.read_text(encoding="utf-8"))
                    if todo_p and todo_p.exists() else None)
    specs = collect_specs(plan_root, status_index)
    rows = build_rows(specs, goals)
    rep = coverage_report(specs, rows)
    gaps = biggest_gaps(rows, 3)
    cells = to_alignment_cells(rows)
    return {
        "specs": len(specs),
        "cells": len(cells),
        "goals": len([r for r in rows if r.specs]),
        "biggest_gaps": [g.goal_id for g in gaps],
        "rows": [{"goal_id": r.goal_id, "shipped": r.shipped,
                  "partial": r.partial, "not_started": r.not_started,
                  "shipped_fraction": round(r.shipped_fraction, 3),
                  "status": r.status} for r in rows],
        "ready": not rep["orphan_specs"] and not rep["unknown_goal_refs"],
    }


# ── render ────────────────────────────────────────────────────────────────────
def render_matrix(rows: list[GoalRow], *, gaps_n: int = 3) -> str:
    """Deterministic markdown table + a recomputed 'biggest gaps' line."""
    lines = [
        "| Goal | Title | Specs | Shipped | Partial | Not started | Shipped % | Status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        pct = f"{r.shipped_fraction * 100:.0f}%"
        lines.append(
            f"| {r.goal_id} | {r.title} | {len(r.specs)} | {r.shipped} | "
            f"{r.partial} | {r.not_started} | {pct} | {r.status} |"
        )
    gaps = biggest_gaps(rows, gaps_n)
    gap_txt = ", ".join(
        f"Goal {g.goal_id} ({g.shipped_fraction * 100:.0f}%)" for g in gaps
    )
    lines += ["", f"**Three biggest gaps:** {gap_txt}"]
    return "\n".join(lines)


def render_from_sources(plan_root: Path, goals_md: Path,
                        todo: Path | None = None, *, gaps_n: int = 3) -> str:
    goals = parse_goals(goals_md.read_text(encoding="utf-8"))
    status_index = (parse_status_index(todo.read_text(encoding="utf-8"))
                    if todo and todo.exists() else None)
    specs = collect_specs(plan_root, status_index)
    return render_matrix(build_rows(specs, goals), gaps_n=gaps_n)


# ── CLI ───────────────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--plan-root", default="Plan", type=Path)
    parser.add_argument("--goals", default="docs/vision/GOALS.md", type=Path)
    parser.add_argument("--todo", default="TODO.md", type=Path,
                        help="binding status index (CLAUDE.md rule 4); "
                             "frontmatter status is the per-spec fallback")
    parser.add_argument(
        "--write", type=Path, default=None,
        help="rewrite the matrix into a `<!-- derived:vision-matrix -->` "
             "fence in PATH (Spec 149 Slice 2.2 fence engine)",
    )
    args = parser.parse_args(argv)

    rendered = render_from_sources(args.plan_root, args.goals, args.todo)
    if args.write is None:
        print(rendered)
        return 0

    from scripts.derive_docs import find_fence, rewrite_fence
    text = args.write.read_text(encoding="utf-8")
    if find_fence(text, "vision-matrix") is None:
        print(
            f"no `<!-- derived:vision-matrix -->` fence in {args.write}; "
            "add one to enable in-place rewrite, or use stdout.",
            file=sys.stderr,
        )
        print(rendered)
        return 1
    args.write.write_text(rewrite_fence(text, "vision-matrix", rendered),
                          encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
