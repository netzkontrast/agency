"""Spec 153 Slice 1 — template/schema coverage audit.

Walks every `agency/capabilities/*/schemas/*.json`, lifts each schema's
`title` field as the node-label it covers, and derives the coverage
report against the live ontology labels: `covered` (intersection),
`uncovered` (ontology − schemas), `spurious` (schemas − ontology),
`coverage_fraction = |covered| / |ontology|`.

Slice 1 is INFORMATIONAL (returns 0). Slice 2 promotes to a CI gate
per Spec 058 WARN→error pattern; Slice 3 adds the doctor metric +
priority ranking by live graph node-count; Slice 4 lights up the
generate→validate round-trip invariant (CORE.md proven-runnable
extended to every covered label).

Per CLAUDE.md rule 8: the report carries RELATIONSHIPS (subset, fraction
of total ontology) — never a pinned count of schemas. A spurious schema
(no matching ontology label) does NOT inflate `covered`; it shows up
under `spurious` so the author can rename or remove.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CoverageReport:
    """The Slice 1 audit payload. Slice 2 adds `floor`, `monotone_ok`,
    `priority_uncovered: list[(label, node_count)]`."""

    covered: set[str] = field(default_factory=set)                  # ontology ∩ schemas
    uncovered: set[str] = field(default_factory=set)                # ontology − schemas
    spurious: set[str] = field(default_factory=set)                 # schemas − ontology
    total_ontology_labels: int = 0

    @property
    def coverage_fraction(self) -> float:
        """`|covered| / |ontology|`. Empty ontology is `1.0` by convention
        — trivially covered. Spurious schemas do NOT inflate the fraction
        (rule 8: relationship invariant)."""
        if self.total_ontology_labels == 0:
            return 1.0
        return len(self.covered) / self.total_ontology_labels


# ── schema discovery ──────────────────────────────────────────────────────
def schema_paths(repo_root: Path) -> list[Path]:
    """Sorted list of every `*.json` under `<root>/capabilities/*/schemas/`.
    Sorted for deterministic output (Spec 149 idempotence)."""
    root = Path(repo_root)
    return sorted((root / "capabilities").glob("*/schemas/*.json"))


def schema_labels(repo_root: Path) -> set[str]:
    """Extract the `title` field from every schema. Malformed JSON or
    missing `title` is silently skipped here; Slice 2 surfaces them via
    a `malformed` field on the report."""
    out: set[str] = set()
    for path in schema_paths(repo_root):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        title = data.get("title")
        if isinstance(title, str) and title:
            out.add(title)
    return out


def audit_schemas(repo_root: Path, *, ontology_labels: set[str]) -> CoverageReport:
    """Compose the typed CoverageReport for `<repo_root>` against the
    given `ontology_labels` set. Pure function over the schema files +
    the supplied ontology — no engine boot."""
    schemas = schema_labels(repo_root)
    covered = schemas & ontology_labels
    uncovered = ontology_labels - schemas
    spurious = schemas - ontology_labels
    return CoverageReport(
        covered=covered,
        uncovered=uncovered,
        spurious=spurious,
        total_ontology_labels=len(ontology_labels),
    )


# ── CLI entry ─────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", default="agency",
                        help="repo subdirectory holding `capabilities/` "
                             "(default: agency)")
    args = parser.parse_args(argv)
    # Boot the engine just long enough to read the live ontology labels.
    from agency.engine import Engine
    e = Engine(":memory:")
    try:
        ontology = set(e.ontology.nodes)
    finally:
        e.memory.close()
    rep = audit_schemas(Path(args.root), ontology_labels=ontology)
    print(f"schema coverage: {rep.coverage_fraction:.3f}  "
          f"({len(rep.covered)}/{rep.total_ontology_labels} labels covered; "
          f"{len(rep.uncovered)} uncovered; {len(rep.spurious)} spurious)")
    if rep.uncovered:
        print(f"  uncovered ({len(rep.uncovered)}):")
        for label in sorted(rep.uncovered)[:20]:
            print(f"    {label}")
        if len(rep.uncovered) > 20:
            print(f"    ... and {len(rep.uncovered) - 20} more")
    if rep.spurious:
        print(f"  spurious schemas ({len(rep.spurious)}): "
              f"{', '.join(sorted(rep.spurious))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
