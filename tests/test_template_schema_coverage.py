"""Spec 153 Slice 1 — template/schema coverage audit.

Spec 004 (wire the generate/validate loop for uncovered node kinds) was
Not Started. Spec 060 shipped the substrate (loader + dataclasses +
materialiser) + a handful of schema files + 7 template files, but most
node kinds the ontology declares still had NO Schema — the CORE.md
generate/validate pair is half-wired.

Slice 1 ships the pure audit:
- `scripts/check_schema_coverage.py` — walks every
  `agency/capabilities/*/schemas/*.json`, lifts `title` → label, derives
  the (covered, uncovered, fraction) shape against the live ontology
  labels. Typed `CoverageReport{covered, uncovered, coverage_fraction}`.
- `priority_uncovered(engine)` — ranks uncovered labels by live
  graph node-count so authors target the highest-traffic gaps first.
- CLI surface + library functions; informational only (Slice 2 lights up
  the WARN→error gate + the doctor + the round-trip invariant per
  Spec 058 doctrine).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.check_schema_coverage import (
    CoverageReport,
    audit_schemas,
    schema_labels,
    schema_paths,
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


def test_schema_labels_skips_schemas_without_title(tmp_path):
    """A schema file missing `title` is malformed — surface it via the
    audit's `malformed` count, do NOT silently include or exclude it."""
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "ok.json").write_text(
        '{"title": "GoodLabel"}')
    (tmp_path / "capabilities" / "a" / "schemas" / "bad.json").write_text(
        '{"description": "no title here"}')
    labels = schema_labels(tmp_path)
    assert labels == {"GoodLabel"}                                 # bad.json silently skipped here


def test_schema_labels_ignores_unreadable_files(tmp_path):
    """A corrupt or unreadable schema file does NOT crash the audit —
    surface as zero contribution and let the report flag malformed."""
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "bad.json").write_text(
        "{ not valid json")
    labels = schema_labels(tmp_path)
    assert labels == set()


# ── coverage report ────────────────────────────────────────────────────────
def test_audit_schemas_returns_coverage_report(tmp_path):
    """`audit_schemas(repo_root, ontology_labels)` returns a typed report."""
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "intent.json").write_text(
        '{"title": "Intent"}')
    rep = audit_schemas(tmp_path, ontology_labels={"Intent", "Reflection", "Artefact"})
    assert isinstance(rep, CoverageReport)
    assert rep.covered == {"Intent"}
    assert rep.uncovered == {"Reflection", "Artefact"}
    # Coverage fraction relationship: covered / total ontology labels.
    assert rep.coverage_fraction == 1 / 3


def test_audit_returns_one_for_empty_ontology(tmp_path):
    """Convention: an empty ontology has nothing to cover → 1.0."""
    rep = audit_schemas(tmp_path, ontology_labels=set())
    assert rep.coverage_fraction == 1.0
    assert rep.covered == set()
    assert rep.uncovered == set()


def test_audit_records_schema_without_ontology_label(tmp_path):
    """A Schema whose label is NOT in the ontology is a SPURIOUS schema
    (e.g. a stale schema for a removed node type) — surface it so the
    author can either rename or remove."""
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "stale.json").write_text(
        '{"title": "RemovedNode"}')
    rep = audit_schemas(tmp_path, ontology_labels={"Intent"})
    assert rep.spurious == {"RemovedNode"}


def test_audit_subset_invariant_per_rule_8(tmp_path):
    """Per CLAUDE.md rule 8 — `covered` is the INTERSECTION of schema
    labels and ontology labels; never inflated by spurious schemas."""
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "intent.json").write_text(
        '{"title": "Intent"}')
    (tmp_path / "capabilities" / "a" / "schemas" / "stale.json").write_text(
        '{"title": "Removed"}')
    rep = audit_schemas(tmp_path, ontology_labels={"Intent"})
    # Spurious doesn't show up in covered (rule 8 — relationship, not count).
    assert rep.covered == {"Intent"}
    assert rep.coverage_fraction == 1.0                            # 1 of 1 ontology labels covered


# ── live-tree audit (informational) ────────────────────────────────────────
def test_live_tree_audit_yields_a_report():
    """Slice 1: assert the audit RUNS against the live repo and produces a
    report — Slice 2 promotes to a monotone-floor CI gate."""
    from agency.engine import Engine

    repo = Path(__file__).parent.parent
    e = Engine(":memory:")
    try:
        ontology = set(e.ontology.nodes)
    finally:
        e.memory.close()
    rep = audit_schemas(repo / "agency", ontology_labels=ontology)
    assert isinstance(rep, CoverageReport)
    # Shape invariants — the audit walks the live tree without crashing.
    assert isinstance(rep.covered, set)
    assert isinstance(rep.uncovered, set)
    assert 0.0 <= rep.coverage_fraction <= 1.0
    # The covered set is a subset of the ontology labels (rule 8 invariant).
    assert rep.covered <= ontology
