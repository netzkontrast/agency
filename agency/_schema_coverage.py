"""Spec 153 — template/schema coverage audit (engine-side core).

Moved out of ``scripts/check_schema_coverage.py`` (Spec 153 Slice 3) so the
engine — ``agency_doctor`` — can import the audit WITHOUT depending on the
dev-only ``scripts/`` tree (the wheel packages only ``agency``). The CLI shim
in ``scripts/check_schema_coverage.py`` re-exports every name + keeps ``main()``
so ``python -m scripts.check_schema_coverage`` is unchanged.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CoverageReport:
    """The Slice 1 audit payload. Slice 2 adds `floor`, `monotone_ok`,
    `priority_uncovered: list[(label, node_count)]`.
    Slice 4 adds `dormant_schemas`: files matching an ontology label but
    not declared by the owning capability (engine never loads them)."""

    covered: set[str] = field(default_factory=set)                  # ontology ∩ schemas [∩ engine_loaded]
    uncovered: set[str] = field(default_factory=set)                # ontology − schemas
    non_node_schemas: set[str] = field(default_factory=set)         # schemas − ontology (artefact / wire-payload — NOT a bug)
    dormant_schemas: set[str] = field(default_factory=set)          # (ontology ∩ schemas) − engine_loaded
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
                  ontology_schemas: dict | None = None,
                  engine_loaded_titles: set[str] | None = None) -> CoverageReport:
    """Compose the typed CoverageReport for `<repo_root>` against the
    given ontology labels + (optional) inline-declared schemas.

    When `engine_loaded_titles` is supplied (Slice 4), only schemas that
    are BOTH on disk AND loaded by the engine count as ``covered``.
    Schemas on disk matching an ontology label but absent from
    ``engine_loaded_titles`` land in ``dormant_schemas`` — they are
    file-backed but the owning capability never declared ``artefact_schemas``
    so the engine never loads them.  Callers obtain ``engine_loaded_titles``
    by booting an Engine and extracting title fields from ``e.ontology.schemas``.
    """
    schemas = schema_labels(repo_root, inline_schemas=ontology_schemas)
    node_schemas = schemas & ontology_labels          # on disk + in ontology
    if engine_loaded_titles is not None:
        covered = node_schemas & engine_loaded_titles
        dormant = node_schemas - engine_loaded_titles
    else:
        covered = node_schemas
        dormant = set()
    uncovered = ontology_labels - schemas
    non_node = schemas - ontology_labels
    return CoverageReport(
        covered=covered,
        uncovered=uncovered,
        non_node_schemas=non_node,
        dormant_schemas=dormant,
        total_ontology_labels=len(ontology_labels),
    )


# ── engine-loaded extraction (Slice 4) ───────────────────────────────────────
def engine_loaded_schema_titles(merged_schemas: dict) -> set[str]:
    """Extract the PascalCase label set for schemas the engine actually loaded.

    Mirrors the ``schema_labels()`` extraction logic applied to the engine's
    *already-loaded* ``ontology.schemas`` dict (``e.ontology.schemas``):

    * Dict-form with ``title`` key → use the title (standard file-backed form).
    * Dict-form WITHOUT ``title`` → derive label from the kebab-case key
      (inline dict schema declared without a title field).
    * List-form → derive label from the kebab-case key
      (inline ``OntologyExtension.schemas = {"foo-bar": ["field1", ...]}``)

    Any schema present in ``merged_schemas`` is engine-loaded; this function
    normalises each to its PascalCase ontology-label counterpart.
    """
    out: set[str] = set()
    for key, val in merged_schemas.items():
        if isinstance(val, dict):
            title = val.get("title")
            out.add(title if isinstance(title, str) and title
                    else _kebab_to_pascal(key))
        elif isinstance(val, list):
            out.add(_kebab_to_pascal(key))
    return out


# ── CLI entry ─────────────────────────────────────────────────────────────
def truly_inline_schemas(repo_root: Path, merged: dict) -> dict:
    """Return only the schemas declared inline via `OntologyExtension.schemas`
    — NOT the ones the engine loaded from `*.json` files.

    Codex review on PR #128: `e.ontology.schemas` is the MERGED dict
    (engine loads file schemas + merges OntologyExtension.schemas). If
    the audit blindly passes it back as `inline_schemas=`, every
    file-backed schema is re-added via its filename — so a file whose
    `title` is stale or mismatched is still counted as covered by the
    PascalCased filename, hiding the exact title/label drift the audit
    is meant to surface.
    """
    file_keys = {p.stem for p in schema_paths(repo_root)}
    return {k: v for k, v in merged.items() if k not in file_keys}


# ── Slice 2: uncovered baseline + WARN→error gate ─────────────────────────
@dataclass
class SchemaRegressionReport:
    """Slice 2 gate payload — `ok` flips False on ANY new uncovered
    label not present in the baseline. `fixed_uncovered` lists labels
    that are now covered (or removed from ontology) so author trims
    the baseline."""

    new_uncovered: set[str] = field(default_factory=set)
    fixed_uncovered: set[str] = field(default_factory=set)
    ok: bool = True


def load_schema_baseline(path: Path) -> set[str]:
    """Parse one label per line; blank + `#`-comment lines tolerated."""
    path = Path(path)
    if not path.exists():
        return set()
    out: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.add(line)
    return out


def compare_uncovered_to_baseline(rep: CoverageReport,
                                    baseline: set[str]) -> SchemaRegressionReport:
    """Set difference. live − baseline = REGRESSIONS (gate-fail).
    baseline − live = FIXED (label is now covered, trim baseline)."""
    new_uncovered = rep.uncovered - baseline
    fixed_uncovered = baseline - rep.uncovered
    return SchemaRegressionReport(
        new_uncovered=new_uncovered,
        fixed_uncovered=fixed_uncovered,
        ok=(len(new_uncovered) == 0),
    )
