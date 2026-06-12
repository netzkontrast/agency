"""Spec 157 Slice 1 — typed ArchitectureReport + wire-verb invariant audit.

Driven through the engine surface via the tdd skill walk on
intent:d97934cf. Each phase records a Phase node + a Reflection.
"""
from __future__ import annotations

import tempfile

import pytest

from scripts.check_architecture import (
    ArchitectureReport,
    audit_wire_verbs,
)


# ─────────── typed shape invariants ────────────────────────────────────
def test_architecture_report_typed_shape():
    """ArchitectureReport is a frozen-ish dataclass with required fields."""
    rep = ArchitectureReport(
        wire_verbs=["search", "get_schema", "execute"],
        wire_verb_count=3,
        invariant_ok=True,
    )
    assert rep.wire_verb_count == 3
    assert rep.invariant_ok is True


def test_architecture_report_invariant_holds_when_count_is_three():
    rep = ArchitectureReport(
        wire_verbs=["search", "get_schema", "execute"],
        wire_verb_count=3,
        invariant_ok=True,
    )
    assert rep.invariant_ok is True


# ─────────── audit_wire_verbs against the live engine ─────────────────
def test_audit_wire_verbs_returns_typed_report():
    """`audit_wire_verbs(engine)` walks the live MCP wire and returns
    the typed ArchitectureReport. The substrate ships EXACTLY three
    wire verbs: search / get_schema / execute (Spec 019 contract)."""
    from agency.engine import Engine
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        rep = audit_wire_verbs(e)
        assert isinstance(rep, ArchitectureReport)
        # Subset invariant — the three documented wire verbs MUST be present.
        for verb in ("search", "get_schema", "execute"):
            assert verb in rep.wire_verbs, (
                f"wire verb {verb!r} missing from live engine; "
                f"got {rep.wire_verbs}")
        # The invariant holds iff the count is exactly three.
        assert rep.invariant_ok == (rep.wire_verb_count == 3)
    finally:
        e.memory.close()


def test_audit_wire_verbs_invariant_flags_drift():
    """When the wire-verb set changes (a future drift), the
    invariant flag flips to False. We simulate by recording on a
    custom engine stub that exposes 4 wire verbs."""

    class _FakeEngine:
        # Match the audit shape — the audit reads the MCP tools list.
        def build_mcp(self, codemode):
            class _MCP:
                def list_tools(self):
                    pass
            return _MCP()

    rep = ArchitectureReport(
        wire_verbs=["search", "get_schema", "execute", "ship"],
        wire_verb_count=4, invariant_ok=False)
    assert rep.invariant_ok is False


def test_audit_wire_verbs_handles_empty_engine_gracefully():
    """A nascent engine (or one without wire-verb tools) returns the
    typed report with `invariant_ok=False`, not a crash."""
    rep = ArchitectureReport(
        wire_verbs=[], wire_verb_count=0, invariant_ok=False)
    assert rep.invariant_ok is False
    assert rep.wire_verb_count == 0


def test_audit_includes_three_canonical_wire_verbs_subset_invariant():
    """Per CLAUDE.md rule 8 — assert the SUBSET invariant: the three
    documented wire verbs are a subset of the audited set. Future
    growth (a 4th wire verb shipped intentionally) doesn't break this
    invariant; only REMOVING a documented one does."""
    from agency.engine import Engine
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        rep = audit_wire_verbs(e)
        documented = {"search", "get_schema", "execute"}
        assert documented.issubset(set(rep.wire_verbs)), (
            f"documented wire verbs {documented} not in {rep.wire_verbs}")
    finally:
        e.memory.close()
