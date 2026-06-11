"""Spec 153 Slice 1 — template/schema coverage audit.

Walks every `agency/capabilities/*/schemas/*.json` AND collects inline
schemas declared via `OntologyExtension.schemas` (the engine merges both
into `e.ontology.schemas`). Derives the coverage report against the live
ontology labels: `covered` (intersection), `uncovered` (ontology −
schemas), `non_node_schemas` (schemas − ontology — these typically
validate ARTEFACT or WIRE-PAYLOAD shapes, NOT a bug), and a
`coverage_fraction = |covered| / |ontology|`.

Slice 1 is INFORMATIONAL (returns 0). Slice 2 promotes to a CI gate
per Spec 058 WARN→error pattern; Slice 3 adds the doctor metric +
priority ranking by live graph node-count; Slice 4 lights up the
generate→validate round-trip invariant (CORE.md proven-runnable
extended to every covered label).

Per CLAUDE.md rule 8: the report carries RELATIONSHIPS (subset, fraction
of total ontology) — never a pinned count of schemas.

Codex review on PR #128:
- Tolerate non-dict / list-form JSON files. A simple `["field"]` schema
  is accepted by the engine and must not crash the audit; the label is
  derived from the filename instead.
- Include inline schemas from `OntologyExtension.schemas` (e.g.
  `document/_main.py` declares `repo-index` as a dict, not a file).
  The audit boots a minimal Engine to read `e.ontology.schemas` keys.
- Don't call schemas that don't match a node label "spurious" — many
  legitimately validate artefact / wire-payload shapes (e.g.
  `gate-outcome.json` validates the `gate.check` payload). Renamed to
  `non_node_schemas` so the audit no longer tells authors to remove
  valid files.
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
    non_node_schemas: set[str] = field(default_factory=set)         # schemas − ontology (artefact / wire-payload — NOT a bug)
    total_ontology_labels: int = 0

    @property
    def coverage_fraction(self) -> float:
        """`|covered| / |ontology|`. Empty ontology is `1.0` by convention
        — trivially covered. `non_node_schemas` are NEITHER subtracted
        nor added (they validate artefact / wire-payload shapes; not
        every schema is for a node)."""
        if self.total_ontology_labels == 0:
            return 1.0
        return len(self.covered) / self.total_ontology_labels


# ── schema discovery ──────────────────────────────────────────────────────
def _kebab_to_pascal(s: str) -> str:
    """`repo-index` → `RepoIndex`. The engine's inline schema keys are
    kebab-case; the ontology labels are PascalCase. Normalize so the
    set comparison hits the right side of the discrepancy."""
    return "".join(part[:1].upper() + part[1:] for part in s.split("-") if part)


def schema_paths(repo_root: Path) -> list[Path]:
    """Sorted list of every `*.json` under `<root>/capabilities/*/schemas/`.
    Sorted for deterministic output (Spec 149 idempotence)."""
    root = Path(repo_root)
    return sorted((root / "capabilities").glob("*/schemas/*.json"))


def schema_labels(repo_root: Path,
                  *, inline_schemas: dict | None = None) -> set[str]:
    """Extract the label each schema covers.

    File-form schemas: prefer `title` (PascalCase); fall back to the
    filename (kebab-case) lifted to PascalCase. Non-dict JSON (the
    accepted `["field"]` list-form) is also fine — label comes from
    the filename. Malformed / unreadable JSON is silently skipped here.

    Inline schemas (`e.ontology.schemas`): keys are kebab-case; lifted
    to PascalCase to compare against ontology labels.

    Codex review on PR #128: this method must NOT crash on list-form
    JSON and must include the inline-declared schemas (e.g. document
    cap's `repo-index` lives in `OntologyExtension.schemas`, not in a
    `schemas/*.json` file).
    """
    out: set[str] = set()
    for path in schema_paths(repo_root):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            title = data.get("title")
            if isinstance(title, str) and title:
                out.add(title)
                continue
        # Either non-dict (list-form) or dict without title — derive
        # the label from the filename. `schemas/repo-index.json` →
        # `RepoIndex`.
        out.add(_kebab_to_pascal(path.stem))
    if inline_schemas:
        for key in inline_schemas.keys():
            if isinstance(key, str) and key:
                out.add(_kebab_to_pascal(key))
    return out


def audit_schemas(repo_root: Path, *,
                  ontology_labels: set[str],
                  ontology_schemas: dict | None = None) -> CoverageReport:
    """Compose the typed CoverageReport for `<repo_root>` against the
    given ontology labels + (optional) inline-declared schemas. Pure
    function over the schema files + the supplied ontology — caller
    is responsible for booting an Engine if `ontology_schemas` is
    needed (see `main()` for the live-tree path)."""
    schemas = schema_labels(repo_root, inline_schemas=ontology_schemas)
    covered = schemas & ontology_labels
    uncovered = ontology_labels - schemas
    non_node = schemas - ontology_labels
    return CoverageReport(
        covered=covered,
        uncovered=uncovered,
        non_node_schemas=non_node,
        total_ontology_labels=len(ontology_labels),
    )


# ── CLI entry ─────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", default="agency",
                        help="repo subdirectory holding `capabilities/` "
                             "(default: agency)")
    args = parser.parse_args(argv)
    # Boot the engine just long enough to read the live ontology labels
    # AND the merged inline-schema keys (so the audit sees every Schema
    # the engine knows about, file-backed or inline-declared).
    from agency.engine import Engine
    e = Engine(":memory:")
    try:
        ontology = set(e.ontology.nodes)
        inline = dict(e.ontology.schemas)
    finally:
        e.memory.close()
    rep = audit_schemas(Path(args.root), ontology_labels=ontology,
                        ontology_schemas=inline)
    print(f"schema coverage: {rep.coverage_fraction:.3f}  "
          f"({len(rep.covered)}/{rep.total_ontology_labels} labels covered; "
          f"{len(rep.uncovered)} uncovered; "
          f"{len(rep.non_node_schemas)} artefact/payload schemas)")
    if rep.uncovered:
        print(f"  uncovered ({len(rep.uncovered)}):")
        for label in sorted(rep.uncovered)[:20]:
            print(f"    {label}")
        if len(rep.uncovered) > 20:
            print(f"    ... and {len(rep.uncovered) - 20} more")
    if rep.non_node_schemas:
        print(f"  non-node schemas ({len(rep.non_node_schemas)}; "
              f"validate artefact/wire-payload shapes): "
              f"{', '.join(sorted(rep.non_node_schemas)[:10])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
