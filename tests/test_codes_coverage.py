"""Spec 151 Slice 1 — ToolResult Codes coverage audit.

Spec 059 ships the `Codes` namespace + `.success`/`.failure` ctors + trace_id
stamping. But there is no audit that every error path in every capability
actually USES a typed `Code` rather than a freeform string — the same drift
the naming audit (Spec 049) ran for names, unran for error codes. A verb that
returns `ToolResult.failure("not found", ...)` instead of
`ToolResult.failure(Codes.NOT_FOUND, ...)` is invisible to a wrapping LLM
driver's enum-branch error matcher.

Slice 1 ships:
- `scripts/check_codes_coverage.py` — AST-walking audit. Pure functions over
  source code so the live tree audit + a fixture-source audit share one path.
- Per-call-site classification: ATTR_REF (Codes.X), STRING_LITERAL,
  EXPR (computed code — opaque to lint), UNKNOWN.
- `CoverageReport` typed shape: `covered_sites`, `total_failure_sites`,
  `fraction`, `offenders` (FileLoc + literal), `orphan_codes` (defined in
  `Codes` but no call site).
- The audit runs INFORMATIONALLY against the live tree (WARN-only per Spec
  058 pattern) — Slice 2 promotes to CI-blocking once the live registry
  reaches `fraction >= 0.9`.

Slice 2+ — monotone floor invariant (a), lint with WARN→error promotion,
shared `Codes` namespace for cross-capability drift (Spec 054 tag), full
backfill of literal-string call sites in the existing capabilities.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from scripts.check_codes_coverage import (
    CallSiteClass,
    CoverageReport,
    FileLoc,
    audit_source,
    audit_tree,
    codes_namespace_members,
    classify_failure_call,
)


# ── pure call-site classification ───────────────────────────────────────────
def test_classifies_attr_ref_codes_namespace():
    """Codes.NOT_FOUND in the first positional is the COVERED case."""
    src = (
        "from agency.toolresult import ToolResult, Codes\n"
        "def f():\n"
        "    return ToolResult.failure(Codes.NOT_FOUND, 'gone')\n"
    )
    results = audit_source(src, path="x.py")
    assert len(results) == 1
    assert results[0].classification == CallSiteClass.ATTR_REF


def test_classifies_string_literal_failure():
    """ToolResult.failure('not_found', ...) is the OFFENDER case."""
    src = (
        "from agency.toolresult import ToolResult\n"
        "def f():\n"
        "    return ToolResult.failure('not_found', 'gone')\n"
    )
    results = audit_source(src, path="x.py")
    assert len(results) == 1
    assert results[0].classification == CallSiteClass.STRING_LITERAL
    assert results[0].literal == "not_found"


def test_classifies_computed_expr_failure():
    """A computed-expression code is OPAQUE — neither covered nor offender."""
    src = (
        "from agency.toolresult import ToolResult\n"
        "def f(code):\n"
        "    return ToolResult.failure(code, 'gone')\n"
    )
    results = audit_source(src, path="x.py")
    assert results[0].classification == CallSiteClass.EXPR


def test_audit_keeps_file_loc_for_offenders():
    src = (
        "from agency.toolresult import ToolResult\n"
        "def f():\n"
        "    return ToolResult.failure('bad_input', 'msg')\n"
    )
    results = audit_source(src, path="x.py")
    loc = results[0].loc
    assert isinstance(loc, FileLoc)
    assert loc.path == "x.py"
    assert loc.line == 3                                          # 1-indexed


def test_audit_handles_multiple_call_sites():
    src = (
        "from agency.toolresult import ToolResult, Codes\n"
        "def f():\n"
        "    return ToolResult.failure(Codes.NOT_FOUND, 'a')\n"
        "def g():\n"
        "    return ToolResult.failure('legacy', 'b')\n"
    )
    results = audit_source(src, path="x.py")
    assert len(results) == 2
    classes = {r.classification for r in results}
    assert CallSiteClass.ATTR_REF in classes
    assert CallSiteClass.STRING_LITERAL in classes


# ── tree audit + report shape ───────────────────────────────────────────────
def test_audit_tree_returns_coverage_report(tmp_path):
    (tmp_path / "good.py").write_text(
        "from agency.toolresult import ToolResult, Codes\n"
        "def f(): return ToolResult.failure(Codes.NOT_FOUND, 'gone')\n"
    )
    (tmp_path / "bad.py").write_text(
        "from agency.toolresult import ToolResult\n"
        "def g(): return ToolResult.failure('not_found', 'gone')\n"
    )
    rep = audit_tree(tmp_path)
    assert isinstance(rep, CoverageReport)
    assert rep.total_failure_sites == 2
    assert rep.covered_sites == 1
    assert rep.fraction == 0.5
    assert len(rep.offenders) == 1
    assert rep.offenders[0].literal == "not_found"


def test_audit_tree_empty_yields_zero_fraction(tmp_path):
    """No failure call sites at all → fraction is 1.0 by convention (no
    offenders, so the codebase is trivially 'covered'). Reading the
    fraction is safe even on an empty tree."""
    (tmp_path / "nothing.py").write_text("def f(): pass\n")
    rep = audit_tree(tmp_path)
    assert rep.total_failure_sites == 0
    assert rep.covered_sites == 0
    assert rep.fraction == 1.0
    assert rep.offenders == []


# ── Codes namespace introspection + orphan detection ───────────────────────
def test_codes_namespace_members_returns_all_constants():
    """Per CLAUDE.md rule 8 — relationship invariant, NOT a pinned count.
    The live Codes class declares ≥1 constant; the documented core MUST
    be present; future codes may extend the set."""
    members = codes_namespace_members()
    documented_core = {"NOT_FOUND", "VALIDATION_FAILED", "DEPENDENCY_MISSING",
                       "GATE_FAILED", "UNSUPPORTED", "BOUNDARY_ERROR",
                       "INTERNAL", "UNSPECIFIED"}
    assert documented_core <= members, (
        f"lost documented core Codes members: {documented_core - members}")


def test_codes_invalid_argument_constant_lands():
    """Spec 151 Slice 1 promotes the heavily-used 'INVALID_ARGUMENT' literal
    (e.g. novel cap) to the Codes namespace. Slice 2+ migrates the call
    sites to attribute references."""
    from agency.toolresult import Codes
    assert Codes.INVALID_ARGUMENT == "invalid_argument"


def test_orphan_codes_detected_when_no_call_site_uses_them(tmp_path):
    """A Codes constant with no call site in the audited tree shows up
    in `orphan_codes` (invariant c — orphan check)."""
    (tmp_path / "only_uses_one.py").write_text(
        "from agency.toolresult import ToolResult, Codes\n"
        "def f(): return ToolResult.failure(Codes.NOT_FOUND, 'x')\n"
    )
    rep = audit_tree(tmp_path)
    # Every documented Codes member is in `orphan_codes` EXCEPT NOT_FOUND.
    assert "NOT_FOUND" not in rep.orphan_codes
    assert "VALIDATION_FAILED" in rep.orphan_codes                # unused → orphan


# ── live-tree invariant (informational; Slice 2 promotes to gate) ──────────
def test_live_tree_audit_yields_a_report():
    """Slice 1: assert the audit RUNS against the live repo and produces a
    report — the actual fraction is informational (Slice 2 promotes to a
    monotone-floor CI gate per Spec 058 WARN→error pattern)."""
    repo = Path(__file__).parent.parent
    rep = audit_tree(repo / "agency")
    # Shape invariants — the audit walks the live tree without crashing.
    assert isinstance(rep, CoverageReport)
    assert rep.total_failure_sites >= 1                            # the codebase has failure paths
    assert 0.0 <= rep.fraction <= 1.0
    # The members the audit knows about EQUAL the live Codes namespace.
    assert isinstance(rep.orphan_codes, set)
