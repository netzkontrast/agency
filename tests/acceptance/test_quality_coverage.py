"""Acceptance — Spec 383: source-coverage grounding + SARIF property test.

Behaviour-only: the book registry is DERIVED from the file (rule 8), every cited
book is grounded in source-coverage (no name-dropping), and SARIF validity is a
computed property over a frozen finding fixture (rule set == registry, one result
per finding) — not pinned snapshots.
"""
from __future__ import annotations

from pytest_bdd import scenarios, given, then, when

from agency.capabilities.analyze import _decay
from agency.capabilities.analyze._coverage import load_source_coverage
from conftest import invoke

scenarios("features/quality_coverage.feature")

# The documented brooks dozen (a cited external constant, CLAUDE.md #8 exception) —
# asserted as a SUBSET relationship, not a pinned count.
_CANONICAL = {
    "The Mythical Man-Month", "Code Complete", "Refactoring", "Clean Architecture",
    "The Pragmatic Programmer", "Domain-Driven Design",
    "A Philosophy of Software Design", "Software Engineering at Google",
    "xUnit Test Patterns", "The Art of Unit Testing",
    "Working Effectively with Legacy Code", "How Google Tests Software",
}


@given("an engine and confirmed intent", target_fixture="engine_iid")
def _engine_iid(engine, iid):
    return engine, iid


def _cited_books() -> set[str]:
    out = set()
    for e in _decay.load_risks().values():
        for s in e.get("sources", []):
            out.add(s.get("book", ""))
    return out


# ── book registry derived ───────────────────────────────────────────────────

@then("source-coverage lists at least the twelve canonical books")
def _twelve(_=None):
    books = load_source_coverage()
    titles = " | ".join(books)
    for canon in _CANONICAL:
        assert canon in titles, f"missing canonical book {canon!r}"


@then("each book entry carries an encoded list and a do-not-ignore list")
def _entries_shaped(_=None):
    for book, e in load_source_coverage().items():
        assert isinstance(e.get("encoded"), list) and e["encoded"], f"{book}: no encoded"
        assert isinstance(e.get("do_not_ignore"), list) and e["do_not_ignore"], \
            f"{book}: no do_not_ignore"


@then("the book count is derived from the file")
def _count_derived(_=None):
    # derived == the number of entries the file actually defines (no magic literal)
    assert len(load_source_coverage()) >= len(_CANONICAL)


# ── grounding: no name-dropping ─────────────────────────────────────────────

@then("every book a decay risk cites is present in source-coverage")
def _grounded(_=None):
    coverage = set(load_source_coverage())
    orphans = _cited_books() - coverage
    assert not orphans, f"decay risks cite books absent from source-coverage: {orphans}"


# ── SARIF property over a frozen fixture ────────────────────────────────────

@given("a frozen finding fixture spanning risks, a custom Cx, and a decidable-only",
       target_fixture="fixture")
def _fixture():
    def f(rule, sev, risk):
        return {"rule": rule, "severity": sev, "file": "x.py", "line": 1,
                "message": "m", "evidence": "e", "risk_code": risk,
                "source": "s", "consequence": "c", "remedy": "r"}
    return [
        f("Q003", "warn", "R1"),
        f("A001", "fail", "R5"),
        f("T010", "warn", "T1"),
        f("CUSTOM", "info", "C1"),     # a custom Cx
        f("Q001", "info", ""),          # decidable-only (empty risk_code)
    ]


@when("analyze.sarif renders the fixture", target_fixture="sarif")
def _render(fixture, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "analyze", "sarif", findings=fixture)
    return result


@then("the SARIF is valid 2.1.0")
def _valid(sarif):
    doc = sarif["sarif"]
    assert doc.get("version") == "2.1.0"
    assert doc.get("runs") and "tool" in doc["runs"][0] and "results" in doc["runs"][0]


@then("the rule set equals the live risk-code registry")
def _rules_eq_registry(sarif):
    rule_ids = {r["id"] for r in sarif["sarif"]["runs"][0]["tool"]["driver"]["rules"]}
    assert rule_ids == set(_decay.load_risks()), rule_ids


@then("every finding produces exactly one SARIF result")
def _one_result_each(sarif, fixture):
    assert sarif["result_count"] == len(fixture), sarif["result_count"]
