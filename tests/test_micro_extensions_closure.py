"""Spec 165 Slice 1 — FragmentVerdict shape + Spec 046 fragment-set invariant.

Slice 1 ships `Plan/165-…/verdicts.json` as the typed data block. Slice 2
ingests the entries into the graph as `FragmentVerdict` nodes that SERVE
Spec 046. This test pins the bedrock invariants:

- The verdict file parses + every entry has the required keys.
- The fragment_id set EQUALS {F-A, F-B, F-C, F-D, F-E, F-F} (Spec 046
  declares exactly these six; no add or drop without amending 046 first).
- Every verdict carries one of {derived, cli_folded, cancelled} with a
  non-empty pointer.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


VERDICTS_PATH = (
    Path(__file__).parent.parent
    / "Plan" / "165-micro-extensions-closure" / "verdicts.json"
)
SPEC_046_FRAGMENTS = {"F-A", "F-B", "F-C", "F-D", "F-E", "F-F"}
VALID_VERDICTS = {"derived", "cli_folded", "cancelled"}


@pytest.fixture
def verdicts():
    data = json.loads(VERDICTS_PATH.read_text(encoding="utf-8"))
    return data["verdicts"]


def test_verdicts_file_parses(verdicts):
    assert isinstance(verdicts, list)
    assert len(verdicts) >= 1


def test_fragment_id_set_equals_spec_046_declared_set(verdicts):
    ids = {v["fragment_id"] for v in verdicts}
    assert ids == SPEC_046_FRAGMENTS, (
        f"Spec 046 declares fragments {sorted(SPEC_046_FRAGMENTS)}; "
        f"verdicts.json carries {sorted(ids)}. Either fix the file or "
        f"amend Spec 046 first.")


def test_every_verdict_carries_required_keys(verdicts):
    for v in verdicts:
        assert "fragment_id" in v
        assert "verdict" in v
        assert "pointer" in v
        assert "rationale" in v


def test_every_verdict_uses_valid_enum_value(verdicts):
    bad = [v for v in verdicts if v["verdict"] not in VALID_VERDICTS]
    assert not bad, (
        f"invalid verdict values: {[(v['fragment_id'], v['verdict']) for v in bad]} "
        f"(allowed: {sorted(VALID_VERDICTS)})")


def test_every_verdict_has_non_empty_pointer(verdicts):
    for v in verdicts:
        assert v["pointer"], (
            f"{v['fragment_id']} carries empty pointer — every verdict must "
            f"cite where the resolution lives (a verb, a skill, a supersession).")


def test_every_verdict_has_non_empty_rationale(verdicts):
    for v in verdicts:
        assert v["rationale"], (
            f"{v['fragment_id']} carries empty rationale — every verdict needs "
            f"a one-line WHY for future readers.")


def test_derived_verdicts_reference_an_agency_path(verdicts):
    """A `derived` verdict's pointer should reference a `skills/` or
    `agency/` path (the source of derivation). Cheap doctrine guard."""
    for v in verdicts:
        if v["verdict"] != "derived":
            continue
        pointer = v["pointer"]
        assert any(p in pointer for p in ("skills/", "agency/")), (
            f"{v['fragment_id']} verdict is `derived` but pointer "
            f"{pointer!r} doesn't cite a skills/ or agency/ path.")


def test_cli_folded_verdicts_reference_an_agency_cli_invocation(verdicts):
    """A `cli_folded` verdict's pointer should reference `agency <cap>
    <verb>` (the Spec 079 CLI mirror entry point)."""
    for v in verdicts:
        if v["verdict"] != "cli_folded":
            continue
        assert "agency " in v["pointer"], (
            f"{v['fragment_id']} verdict is `cli_folded` but pointer "
            f"{v['pointer']!r} doesn't cite an `agency <cap> <verb>` form.")


def test_cancelled_verdicts_cite_a_supersession(verdicts):
    """A `cancelled` verdict's rationale should mention a Spec / CLAUDE.md /
    superseding-rule. Cheap doctrine guard against silent cancellation."""
    for v in verdicts:
        if v["verdict"] != "cancelled":
            continue
        text = (v["pointer"] + " " + v["rationale"]).lower()
        assert any(k in text for k in ("spec ", "claude.md", "supersed", "rule ")), (
            f"{v['fragment_id']} verdict is `cancelled` but cites neither a "
            f"Spec nor a CLAUDE.md rule for the supersession.")
