"""Acceptance — codes-coverage audit behaviour (Spec 151).

Grounds the Slice 2 gate that `.github/workflows/test.yml` runs (`--baseline
--strict`). The schema-coverage twin (`test_template_schema.py`) had a
live-baseline-sync scenario; the codes audit had none, which is why its
baseline silently drifted to advisory after the Spec 286 module split. The
final scenario closes that hole: it fails in the suite the moment the
committed baseline and the live offender set diverge.

Behaviour only (CLAUDE.md rule 7) — the AST helpers (`_agency_aliases`,
`_module_matches_toolresult`) are internal; what matters is the classification
of a call site and the baseline-comparison verdict.
"""
from __future__ import annotations

from pathlib import Path

from pytest_bdd import scenarios, then, when

from scripts.check_codes_coverage import (
    CallSiteClass,
    CoverageReport,
    OffenderBaselineEntry,
    audit_source,
    audit_tree,
    compare_offenders_to_baseline,
    load_codes_baseline,
)

scenarios("features/codes_coverage.feature")

_IMPORT = "from agency.toolresult import ToolResult, Codes\n"


def _offenders(sites):
    return [s for s in sites if s.classification == CallSiteClass.STRING_LITERAL]


def _covered(sites):
    return [s for s in sites if s.classification == CallSiteClass.ATTR_REF]


# ── When steps ────────────────────────────────────────────────────────────────

@when("I audit a source with one Codes.NOT_FOUND call and one \"NOT_FOUND\" literal",
      target_fixture="sites")
def _mixed_source():
    src = (_IMPORT
           + "def a():\n    return ToolResult.failure(Codes.NOT_FOUND, 'x')\n"
           + "def b():\n    return ToolResult.failure('NOT_FOUND', 'y')\n")
    return audit_source(src, path="m.py")


@when("I audit a source whose failure call uses a Codes typo", target_fixture="sites")
def _typo_source():
    # Codes.NOT_FOND is not a real member → reclassified as an offender so the
    # runtime AttributeError doesn't hide behind an inflated covered count.
    src = _IMPORT + "def a():\n    return ToolResult.failure(Codes.NOT_FOND, 'x')\n"
    return audit_source(src, path="typo.py")


@when("I shift the offender down by inserting blank lines above it",
      target_fixture="shift_ctx")
def _shift_offender():
    src = _IMPORT + "def b():\n    return ToolResult.failure('NOT_FOUND', 'y')\n"
    original = _offenders(audit_source(src, path="m.py"))
    baseline = {OffenderBaselineEntry(path=o.loc.path, line=o.loc.line,
                                      literal=o.literal) for o in original}
    shifted_src = "\n\n\n\n\n" + src  # same code, every line number bumped
    shifted = audit_source(shifted_src, path="m.py")
    rep = CoverageReport(offenders=_offenders(shifted))
    return {"rep": rep, "baseline": baseline, "original": original}


@when("I audit a source with no failure call sites", target_fixture="report")
def _empty_source():
    rep = CoverageReport()
    rep.total_failure_sites = 0
    return rep


@when("I run the live codes audit and compare to the committed baseline",
      target_fixture="regression")
def _live_baseline(monkeypatch):
    repo = Path(__file__).parent.parent.parent
    monkeypatch.chdir(repo)
    rep = audit_tree(Path("agency"))
    baseline = load_codes_baseline(
        Path("Plan/_planning/codes-coverage-baseline.txt"))
    return compare_offenders_to_baseline(rep, baseline)


# ── Then steps ────────────────────────────────────────────────────────────────

@then("exactly one call site is covered")
def _one_covered(sites):
    assert len(_covered(sites)) == 1, sites


@then("exactly one call site is an offender")
def _one_offender(sites):
    assert len(_offenders(sites)) == 1, sites


@then("the typo call site is an offender")
def _typo_offender(sites):
    offs = _offenders(sites)
    assert len(offs) == 1 and "NOT_FOND" in offs[0].literal, sites
    assert _covered(sites) == [], sites


@then("the baseline comparison reports no new offenders")
def _no_new_after_shift(shift_ctx):
    res = compare_offenders_to_baseline(shift_ctx["rep"], shift_ctx["baseline"])
    # the offender moved lines but kept its (path, literal) key → no regression
    assert res.ok and res.new_offenders == [], res
    assert shift_ctx["rep"].offenders[0].loc.line != next(
        iter(shift_ctx["original"])).loc.line  # the line actually shifted


@then("the codes coverage fraction is 1.0")
def _empty_fraction(report):
    assert report.fraction == 1.0


@then("there are no new codes offenders")
def _no_new_offenders(regression):
    assert regression.new_offenders == [], (
        "live audit produced offenders NOT in the baseline — refresh "
        "Plan/_planning/codes-coverage-baseline.txt:\n"
        + "\n".join(f"  + {o.loc.path}:{o.loc.line}  {o.literal!r}"
                    for o in regression.new_offenders))


@then("there are no fixed baseline entries to trim")
def _no_fixed_offenders(regression):
    assert regression.fixed_offenders == [], (
        "baseline lists offenders no longer present — trim them:\n"
        + "\n".join(f"  - {b.path}:{b.line}  {b.literal!r}"
                    for b in regression.fixed_offenders))
