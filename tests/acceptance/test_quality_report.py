"""Acceptance — Spec 382 §4: the Iron-Law report render path.

Behaviour-only: the report projects structured findings — sorted by tier, each as
the Iron Law block, empty tiers omitted, mermaid in audit mode only. Through
analyze.report.
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, given, then, when

from conftest import invoke

scenarios("features/quality_report.feature")


@given("an engine and confirmed intent", target_fixture="engine_iid")
def _engine_iid(engine, iid):
    return engine, iid


@given("findings of one R5 critical and one R1 warning", target_fixture="findings")
def _findings():
    return [
        {"rule": "A001", "severity": "fail", "file": "m.py", "line": 3,
         "message": "import cycle a->b->a", "evidence": "e", "risk_code": "R5",
         "source": "Martin - ADP", "consequence": "cycles rot the build",
         "remedy": "invert the dependency"},
        {"rule": "Q003", "severity": "warn", "file": "u.py", "line": 9,
         "message": "long function", "evidence": "e", "risk_code": "R1",
         "source": "Fowler", "consequence": "overload", "remedy": "extract"},
    ]


@when(parsers.re(r'I render the report for mode "(?P<mode>[^"]+)" with score (?P<score>\d+)'),
      target_fixture="report")
def _render(mode, score, findings, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "analyze", "report",
                       findings=findings, mode=mode, score=int(score))
    return result["report"]


@then(parsers.re(r"the report header shows score (?P<score>\d+)"))
def _header_score(score, report):
    # Spec 384 — rendered from quality-report.md; the Health Score is in the header
    # region (assert the value, not a pinned line index — rule 8).
    head = report.splitlines()[:8]
    assert any(f"{score}/100" in line for line in head), head


@then("the critical finding appears before the warning finding")
def _tier_order(report):
    assert "R5" in report and "R1" in report
    assert report.index("R5") < report.index("R1"), "warning before critical"


@then("the report shows Symptom, Source, Consequence, and Remedy for the R5 finding")
def _iron_law(report):
    for piece in ("import cycle a->b->a", "Martin - ADP",
                  "cycles rot the build", "invert the dependency"):
        assert piece in report, f"missing {piece!r}"
    for label in ("Symptom", "Source", "Consequence", "Remedy"):
        assert label in report, f"missing label {label!r}"


@then("the suggestion tier is omitted")
def _no_suggestion(report):
    assert "Suggestion" not in report and "suggestion" not in report.lower().split("summary")[0], report


@then("the report contains a mermaid block")
def _has_mermaid(report):
    assert "```mermaid" in report, "no mermaid block in audit report"


@then("the report contains no mermaid block")
def _no_mermaid(report):
    assert "```mermaid" not in report, "mermaid block present in review report"
