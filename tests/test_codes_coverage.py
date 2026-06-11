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
- Per-call-site classification: ATTR_REF (Codes.X — where X is a real Codes
  member), STRING_LITERAL (offender — includes typo'd Codes.X), EXPR
  (computed code — counted against coverage), UNKNOWN.
- `CoverageReport` typed shape: `covered_sites`, `total_failure_sites`,
  `fraction` (= covered / (covered+offenders+expr); empty-tree convention
  1.0), `offenders` (FileLoc + literal), `orphan_codes` (defined in `Codes`
  but no real ATTR_REF call site).
- ImportFrom alias detection: `from agency.toolresult import ToolResult as TR`
  is recognized so `TR.failure(...)` does not silently slip past.
- The audit runs INFORMATIONALLY against the live tree (WARN-only per Spec
  058 pattern) — Slice 2 promotes to CI-blocking once the live registry
  reaches `fraction >= 0.9`.

Slice 2+ — monotone floor invariant (a), lint with WARN→error promotion,
shared `Codes` namespace for cross-capability drift (Spec 054 tag), full
backfill of literal-string call sites in the existing capabilities.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.check_codes_coverage import (
    CallSiteClass,
    CallSiteResult,
    CoverageReport,
    FileLoc,
    audit_source,
    audit_tree,
    codes_namespace_members,
    classify_failure_call,
)


# A hermetic Codes namespace for unit tests — keeps assertions stable
# when the live namespace evolves under other branches.
_FIXTURE_CODES = {"NOT_FOUND", "VALIDATION_FAILED", "INVALID_ARGUMENT"}


# ── pure call-site classification ───────────────────────────────────────────
def test_classifies_attr_ref_codes_namespace():
    """Codes.NOT_FOUND in the first positional is the COVERED case."""
    src = (
        "from agency.toolresult import ToolResult, Codes\n"
        "def f():\n"
        "    return ToolResult.failure(Codes.NOT_FOUND, 'gone')\n"
    )
    results = audit_source(src, path="x.py", codes_members=_FIXTURE_CODES)
    assert len(results) == 1
    assert results[0].classification == CallSiteClass.ATTR_REF
    assert results[0].code_name == "NOT_FOUND"


def test_classifies_string_literal_failure():
    """ToolResult.failure('not_found', ...) is the OFFENDER case."""
    src = (
        "from agency.toolresult import ToolResult\n"
        "def f():\n"
        "    return ToolResult.failure('not_found', 'gone')\n"
    )
    results = audit_source(src, path="x.py", codes_members=_FIXTURE_CODES)
    assert len(results) == 1
    assert results[0].classification == CallSiteClass.STRING_LITERAL
    assert results[0].literal == "not_found"


def test_classifies_computed_expr_failure():
    """A computed-expression code is OPAQUE — counted against coverage so
    it can't masquerade as a covered call site."""
    src = (
        "from agency.toolresult import ToolResult\n"
        "def f(code):\n"
        "    return ToolResult.failure(code, 'gone')\n"
    )
    results = audit_source(src, path="x.py", codes_members=_FIXTURE_CODES)
    assert results[0].classification == CallSiteClass.EXPR


def test_audit_keeps_file_loc_for_offenders():
    src = (
        "from agency.toolresult import ToolResult\n"
        "def f():\n"
        "    return ToolResult.failure('bad_input', 'msg')\n"
    )
    results = audit_source(src, path="x.py", codes_members=_FIXTURE_CODES)
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
    results = audit_source(src, path="x.py", codes_members=_FIXTURE_CODES)
    assert len(results) == 2
    classes = {r.classification for r in results}
    assert CallSiteClass.ATTR_REF in classes
    assert CallSiteClass.STRING_LITERAL in classes


# ── Codex review fixes (PR #126) ──────────────────────────────────────────
def test_typoed_codes_attr_classified_as_offender():
    """`Codes.NOT_FOND` (typo) raises AttributeError at runtime — must be
    surfaced as an offender, not silently counted as covered."""
    src = (
        "from agency.toolresult import ToolResult, Codes\n"
        "def f():\n"
        "    return ToolResult.failure(Codes.NOT_FOND, 'oops')\n"
    )
    results = audit_source(src, path="x.py", codes_members=_FIXTURE_CODES)
    assert len(results) == 1
    assert results[0].classification == CallSiteClass.STRING_LITERAL
    assert results[0].literal == "Codes.NOT_FOND"


def test_aliased_toolresult_import_is_detected():
    """`from agency.toolresult import ToolResult as TR; TR.failure(...)`
    is the documented alias path; the audit must NOT silently drop it."""
    src = (
        "from agency.toolresult import ToolResult as TR, Codes\n"
        "def f():\n"
        "    return TR.failure(Codes.NOT_FOUND, 'gone')\n"
        "def g():\n"
        "    return TR.failure('legacy', 'gone')\n"
    )
    results = audit_source(src, path="x.py", codes_members=_FIXTURE_CODES)
    assert len(results) == 2                                       # both detected
    classes = {r.classification for r in results}
    assert CallSiteClass.ATTR_REF in classes
    assert CallSiteClass.STRING_LITERAL in classes


def test_expr_sites_count_against_fraction(tmp_path):
    """An EXPR-only tree (computed code arg) must NOT report 1.0 — the
    typed coverage hasn't been proven for any site."""
    (tmp_path / "all_expr.py").write_text(
        "from agency.toolresult import ToolResult\n"
        "def f(code):\n"
        "    return ToolResult.failure(code, 'msg')\n"
        "def g(c):\n"
        "    return ToolResult.failure(c, 'msg')\n"
    )
    rep = audit_tree(tmp_path)
    assert rep.expr_sites == 2
    assert rep.covered_sites == 0
    # Previously: 1.0 (misleading). Now: 0.0 — none proven covered.
    assert rep.fraction == 0.0


def test_orphan_check_only_counts_attr_ref_call_sites(tmp_path):
    """A `Codes.VALIDATION_FAILED == "x"` comparison ALONGSIDE a covered
    Codes.NOT_FOUND failure must NOT rescue VALIDATION_FAILED from the
    orphan list — only call-site ATTR_REFs count."""
    (tmp_path / "mixed.py").write_text(
        "from agency.toolresult import ToolResult, Codes\n"
        "def f():\n"
        "    # The comparison below references Codes.VALIDATION_FAILED but it\n"
        "    # is NOT a ToolResult.failure call site — it must not\n"
        "    # rescue VALIDATION_FAILED from orphan status.\n"
        "    if 'x' == Codes.VALIDATION_FAILED:\n"
        "        pass\n"
        "    return ToolResult.failure(Codes.NOT_FOUND, 'gone')\n"
    )
    rep = audit_tree(tmp_path)
    # NOT_FOUND is the only ATTR_REF call site → only NOT_FOUND is covered.
    assert "NOT_FOUND" not in rep.orphan_codes
    assert "VALIDATION_FAILED" in rep.orphan_codes


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


def test_audit_tree_empty_yields_one_fraction(tmp_path):
    """No failure call sites at all → fraction is 1.0 by convention
    (the empty-tree case is genuinely 'nothing to cover')."""
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
    sites to attribute references. Value MUST stay uppercase to preserve
    backward compat with existing assertion strings (see
    test_invalid_argument_codes_value_matches_existing_literal)."""
    from agency.toolresult import Codes
    assert Codes.INVALID_ARGUMENT == "INVALID_ARGUMENT"


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


# ── Codex round-2 review fixes ─────────────────────────────────────────────
def test_third_party_toolresult_failure_is_ignored(tmp_path):
    """A `ToolResult.failure(...)` call in a file that does NOT import
    `agency.toolresult.ToolResult` must NOT trip the audit — the receiver
    is a third-party / fixture class with the same name."""
    (tmp_path / "thirdparty.py").write_text(
        "# No import of agency.toolresult here.\n"
        "class ToolResult:\n"
        "    @classmethod\n"
        "    def failure(cls, code, msg): return cls()\n"
        "def f():\n"
        "    return ToolResult.failure('not_an_agency_code', 'msg')\n"
    )
    rep = audit_tree(tmp_path)
    # No agency import → file is skipped entirely.
    assert rep.total_failure_sites == 0
    assert rep.offenders == []


def test_codes_alias_via_as_import_is_recognized(tmp_path):
    """`from agency.toolresult import Codes as C; ToolResult.failure(
    C.NOT_FOUND, ...)` is valid typed usage. The classifier must honor it
    and count the site as ATTR_REF (covered), not EXPR (uncovered)."""
    (tmp_path / "aliased.py").write_text(
        "from agency.toolresult import ToolResult, Codes as C\n"
        "def f():\n"
        "    return ToolResult.failure(C.NOT_FOUND, 'gone')\n"
    )
    rep = audit_tree(tmp_path)
    assert rep.covered_sites == 1
    assert rep.offenders == []
    assert "NOT_FOUND" not in rep.orphan_codes


def test_unknown_sites_count_against_fraction(tmp_path):
    """`ToolResult.failure(**payload)` returns UNKNOWN (no positional code,
    no `code=` kwarg). The site is opaque to the lint — must NOT report 1.0."""
    (tmp_path / "unknown.py").write_text(
        "from agency.toolresult import ToolResult\n"
        "def f(payload):\n"
        "    return ToolResult.failure(**payload)\n"
    )
    rep = audit_tree(tmp_path)
    assert rep.unknown_sites == 1
    assert rep.covered_sites == 0
    assert rep.fraction == 0.0                                     # not 1.0 (Codex finding)


def test_invalid_argument_codes_value_matches_existing_literal():
    """Spec 151 Slice 1 promotes the heavily-used `"INVALID_ARGUMENT"`
    literal to `Codes.INVALID_ARGUMENT`. The constant VALUE must stay
    uppercase to match the 40+ existing call sites + the assertion
    strings across tests/test_music_lifecycle.py, tests/test_novel_*.py,
    tests/test_thinking_capability.py, tests/test_prompt_capability.py —
    otherwise migrating from literal to attr-ref changes the emitted
    `TypedError.code` from `INVALID_ARGUMENT` to `invalid_argument` and
    breaks every client branching on the existing error code."""
    from agency.toolresult import Codes
    assert Codes.INVALID_ARGUMENT == "INVALID_ARGUMENT"            # NOT lowercase


# ── Codex round-3 review fixes ────────────────────────────────────────────
def test_codes_not_imported_classified_as_offender(tmp_path):
    """Codex review: a file that imports ToolResult but FORGETS to import
    Codes. `Codes.NOT_FOUND` raises NameError at runtime — must surface
    as an offender, not fall back to the bare `{"Codes"}` alias set and
    be silently counted as covered."""
    (tmp_path / "broken.py").write_text(
        "from agency.toolresult import ToolResult\n"            # No Codes import!
        "def f():\n"
        "    return ToolResult.failure(Codes.NOT_FOUND, 'gone')\n"
    )
    rep = audit_tree(tmp_path)
    assert rep.covered_sites == 0
    assert len(rep.offenders) == 1
    assert "Codes.NOT_FOUND" in rep.offenders[0].literal
    assert "not imported" in rep.offenders[0].literal


def test_cli_includes_unknown_count(capsys, tmp_path):
    """Codex review: an UNKNOWN-only tree previously printed
    `(0/0 covered; 0 offenders; 0 computed)` hiding the call site
    entirely. CLI breakdown must include `unknown`."""
    from scripts.check_codes_coverage import main
    (tmp_path / "u.py").write_text(
        "from agency.toolresult import ToolResult\n"
        "def f(payload): return ToolResult.failure(**payload)\n"
    )
    rc = main(["--root", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "1 unknown" in out                                      # breakdown surfaces it
    # The denominator counts the unknown site.
    assert "0/1 covered" in out


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
