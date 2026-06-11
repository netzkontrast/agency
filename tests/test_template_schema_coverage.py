"""Spec 153 Slice 1 — template/schema coverage audit.

Spec 004 (wire the generate/validate loop for uncovered node kinds) was
Not Started. Spec 060 shipped the substrate (loader + dataclasses +
materialiser) + a handful of schema files + 7 template files, but most
node kinds the ontology declares still had NO Schema — the CORE.md
generate/validate pair is half-wired.

Slice 1 ships the pure audit:
- `scripts/check_schema_coverage.py` — walks every
  `agency/capabilities/*/schemas/*.json` AND honors inline schemas
  declared via `OntologyExtension.schemas`. Tolerates list-form JSON.
- Typed `CoverageReport{covered, uncovered, non_node_schemas, ...}` —
  Codex review on PR #128: renamed `spurious` to `non_node_schemas`
  because many schemas legitimately validate artefact / wire-payload
  shapes (e.g. `gate-outcome.json` validates `gate.check` payload).
- Library functions + CLI; informational only (Slice 2 lights up the
  WARN→error gate per Spec 058 doctrine).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.check_schema_coverage import (
    CoverageReport,
    audit_schemas,
    schema_labels,
    schema_paths,
    truly_inline_schemas,
)


# ── pure schema discovery ──────────────────────────────────────────────────
def test_schema_paths_returns_deterministic_list(tmp_path):
    """Walks `<root>/capabilities/*/schemas/*.json`; sorted (by full
    path) for deterministic output (Spec 149 idempotence)."""
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "b" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "z.json").write_text('{"title": "Z"}')
    (tmp_path / "capabilities" / "a" / "schemas" / "a.json").write_text('{"title": "A"}')
    (tmp_path / "capabilities" / "b" / "schemas" / "m.json").write_text('{"title": "M"}')
    paths1 = schema_paths(tmp_path)
    paths2 = schema_paths(tmp_path)
    assert paths1 == paths2                                        # deterministic
    assert len(paths1) == 3
    assert paths1 == sorted(paths1)                                # sorted by full path


def test_schema_paths_skips_non_json(tmp_path):
    (tmp_path / "capabilities" / "x" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "x" / "schemas" / "ok.json").write_text('{"title": "X"}')
    (tmp_path / "capabilities" / "x" / "schemas" / "readme.md").write_text('# not a schema')
    paths = schema_paths(tmp_path)
    assert len(paths) == 1
    assert paths[0].name == "ok.json"


def test_schema_labels_extracts_title_from_each_schema(tmp_path):
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "one.json").write_text(
        '{"title": "Label1"}')
    (tmp_path / "capabilities" / "a" / "schemas" / "two.json").write_text(
        '{"title": "Label2"}')
    labels = schema_labels(tmp_path)
    assert labels == {"Label1", "Label2"}


def test_schema_labels_falls_back_to_filename_when_title_missing(tmp_path):
    """Codex review on PR #128: a dict schema without `title` is not
    malformed — many simple schemas omit it. Derive the label from the
    filename (kebab-case lifted to PascalCase) rather than silently
    dropping the schema."""
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "repo-index.json").write_text(
        '{"description": "no title here"}')
    labels = schema_labels(tmp_path)
    assert labels == {"RepoIndex"}                                 # filename → PascalCase


def test_schema_labels_handles_list_form_schemas(tmp_path):
    """Codex review on PR #128: `_load_schemas_from()` accepts any JSON
    value, including list-form `["field"]` schemas. The audit must
    derive the label from the filename instead of crashing on
    `.get("title")` against a list."""
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "simple-record.json").write_text(
        '["field_a", "field_b"]')
    labels = schema_labels(tmp_path)
    assert labels == {"SimpleRecord"}


def test_schema_labels_ignores_unreadable_files(tmp_path):
    """A corrupt or unreadable schema file does NOT crash the audit."""
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "bad.json").write_text(
        "{ not valid json")
    labels = schema_labels(tmp_path)
    assert labels == set()


def test_schema_labels_includes_inline_schemas(tmp_path):
    """Codex review on PR #128: inline schemas declared via
    `OntologyExtension.schemas` (e.g. document cap's `repo-index`) must
    enter the audit. The CLI boots an engine to read them; library
    callers pass them via `inline_schemas=`."""
    # No file-based schemas in tmp_path — only inline.
    (tmp_path / "capabilities").mkdir(parents=True, exist_ok=True)
    inline = {"repo-index": {"required": ["path"]},
              "intent-yaml": {"required": ["purpose"]}}
    labels = schema_labels(tmp_path, inline_schemas=inline)
    assert labels == {"RepoIndex", "IntentYaml"}                   # both lifted to PascalCase


def test_schema_labels_merges_file_and_inline_sources(tmp_path):
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "file.json").write_text(
        '{"title": "FromFile"}')
    inline = {"from-inline": {}}
    labels = schema_labels(tmp_path, inline_schemas=inline)
    assert labels == {"FromFile", "FromInline"}


# ── coverage report ────────────────────────────────────────────────────────
def test_audit_schemas_returns_coverage_report(tmp_path):
    """`audit_schemas(repo_root, ontology_labels=...)` returns a typed report."""
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "intent.json").write_text(
        '{"title": "Intent"}')
    rep = audit_schemas(tmp_path, ontology_labels={"Intent", "Reflection", "Artefact"})
    assert isinstance(rep, CoverageReport)
    assert rep.covered == {"Intent"}
    assert rep.uncovered == {"Reflection", "Artefact"}
    assert rep.coverage_fraction == 1 / 3


def test_audit_returns_one_for_empty_ontology(tmp_path):
    """Convention: an empty ontology has nothing to cover → 1.0."""
    rep = audit_schemas(tmp_path, ontology_labels=set())
    assert rep.coverage_fraction == 1.0
    assert rep.covered == set()
    assert rep.uncovered == set()


def test_audit_records_non_node_schema(tmp_path):
    """Codex review on PR #128: a Schema whose label is NOT in the
    ontology is NOT spurious — it likely validates an artefact or
    wire-payload shape (e.g. `gate-outcome.json` validates the
    `gate.check` payload). Surface in `non_node_schemas` so the audit
    doesn't tell authors to remove legitimate files."""
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "wire.json").write_text(
        '{"title": "GateOutcome"}')
    rep = audit_schemas(tmp_path, ontology_labels={"Gate"})
    assert rep.non_node_schemas == {"GateOutcome"}
    # The non-node schema does NOT inflate covered.
    assert rep.covered == set()
    assert rep.coverage_fraction == 0.0


def test_audit_subset_invariant_per_rule_8(tmp_path):
    """Per CLAUDE.md rule 8 — `covered` is the INTERSECTION of schema
    labels and ontology labels; non-node schemas never enter `covered`."""
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "intent.json").write_text(
        '{"title": "Intent"}')
    (tmp_path / "capabilities" / "a" / "schemas" / "wire.json").write_text(
        '{"title": "GateOutcome"}')
    rep = audit_schemas(tmp_path, ontology_labels={"Intent"})
    # Non-node schema doesn't show up in covered (rule 8 — relationship, not count).
    assert rep.covered == {"Intent"}
    assert rep.coverage_fraction == 1.0                            # 1 of 1 ontology labels covered


def test_audit_honors_inline_schemas_against_ontology_labels():
    """The CLI passes the engine's merged inline schemas; this asserts
    `audit_schemas` honors them as covered when the lifted label matches."""
    inline = {"repo-index": {}, "intent-yaml": {}}
    # `RepoIndex` is in the live ontology; `IntentYaml` is not (it's an artefact form).
    rep = audit_schemas(Path("agency"), ontology_labels={"RepoIndex"},
                        ontology_schemas=inline)
    assert "RepoIndex" in rep.covered
    assert "IntentYaml" in rep.non_node_schemas


# ── truly-inline schema separation (Codex round-2) ────────────────────────
def test_truly_inline_schemas_excludes_file_backed_keys(tmp_path):
    """Codex review on PR #128: `e.ontology.schemas` is the MERGED dict
    (engine loads file schemas + merges OntologyExtension.schemas). The
    audit must split off the file-backed ones so a file with a stale
    `title` ISN'T silently re-covered via its filename."""
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "repo-index.json").write_text(
        '{"title": "RepoIndex"}')
    merged = {
        "repo-index": {"required": ["path"]},                      # file-backed
        "intent-yaml": {"required": ["purpose"]},                  # inline-only
    }
    inline_only = truly_inline_schemas(tmp_path, merged)
    assert set(inline_only.keys()) == {"intent-yaml"}              # file-backed excluded


def test_audit_via_truly_inline_surfaces_title_label_drift(tmp_path):
    """A file `repo-index.json` whose `title` is stale ("OldName")
    should NOT be silently rescued by the filename via the merged
    inline dict. The audit reports `OldName` only."""
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "repo-index.json").write_text(
        '{"title": "OldName"}')
    merged = {"repo-index": {"required": ["path"]}}                # file-backed key
    inline_only = truly_inline_schemas(tmp_path, merged)            # → {}
    # Now audit using truly-inline only:
    rep = audit_schemas(tmp_path, ontology_labels={"RepoIndex"},
                        ontology_schemas=inline_only)
    # OldName surfaces as a non-node schema (drift); RepoIndex is uncovered.
    assert "RepoIndex" in rep.uncovered
    assert "OldName" in rep.non_node_schemas


# ── live-tree audit (informational) ────────────────────────────────────────
def test_live_tree_audit_yields_a_report():
    """Slice 1: assert the audit RUNS against the live repo and produces a
    report — Slice 2 promotes to a monotone-floor CI gate."""
    from agency.engine import Engine

    repo = Path(__file__).parent.parent
    e = Engine(":memory:")
    try:
        ontology = set(e.ontology.nodes)
        merged = dict(e.ontology.schemas)
    finally:
        e.memory.close()
    inline = truly_inline_schemas(repo / "agency", merged)
    rep = audit_schemas(repo / "agency", ontology_labels=ontology,
                        ontology_schemas=inline)
    assert isinstance(rep, CoverageReport)
    # Shape invariants — the audit walks the live tree without crashing.
    assert isinstance(rep.covered, set)
    assert isinstance(rep.uncovered, set)
    assert 0.0 <= rep.coverage_fraction <= 1.0
    # The covered set is a subset of the ontology labels (rule 8 invariant).
    assert rep.covered <= ontology
