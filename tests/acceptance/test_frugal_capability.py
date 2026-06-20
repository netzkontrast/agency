"""Acceptance — frugal capability (Spec 348 Slice 1, the ponytail port).

Behaviour: the discipline is a discoverable capability whose verbs wrap the core
_frugal module — read/switch the level, pull the ruleset (the MCP port), show the
help card. Config is isolated to a temp path so set_level never pollutes the repo.
"""
from __future__ import annotations

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency import _frugal
from conftest import invoke, served

scenarios("features/frugal_capability.feature")


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENCY_CONFIG", str(tmp_path / ".agency" / "config.yaml"))
    monkeypatch.delenv("AGENCY_FRUGAL_LEVEL", raising=False)
    monkeypatch.delenv("AGENCY_FRUGAL_SESSION_INJECT", raising=False)


def _f(engine, intent, verb, **kw):
    r, _ = invoke(engine, intent, "frugal", verb, agent_id="agent:test", **kw)
    return r


@when("I read the frugal capability level", target_fixture="fr")
def _level(engine, confirmed_intent):
    return _f(engine, confirmed_intent, "level")


@when(parsers.parse('I set the frugal capability level to "{level}"'), target_fixture="fr")
def _set(engine, confirmed_intent, level):
    return _f(engine, confirmed_intent, "set_level", level=level)


@when(parsers.parse('I get the frugal instructions at "{level}"'), target_fixture="fr")
def _instr(engine, confirmed_intent, level):
    return _f(engine, confirmed_intent, "instructions", level=level)


@when("I get the frugal help", target_fixture="fr")
def _help(engine, confirmed_intent):
    return _f(engine, confirmed_intent, "help")


@then(parsers.parse('the reported frugal level is "{level}"'))
def _level_is(fr, level):
    assert fr["level"] == level, fr


@then("the frugal instructions name every safety-floor marker")
def _floor(fr):
    for m in _frugal.SAFETY_FLOOR_MARKERS:
        assert m in fr["instructions"], m


@then("the frugal instructions are empty")
def _instr_empty(fr):
    assert fr["instructions"] == "", fr


@then(parsers.parse('the frugal help contains "{needle}"'))
def _help_has(fr, needle):
    assert needle in fr["help"], fr["help"][:200]


# ── debt + gain (Slice 2) ─────────────────────────────────────────────────────


@given("a source tree with frugal markers", target_fixture="debt_path")
def _tree(tmp_path):
    (tmp_path / "a.py").write_text(
        "x = 1  # frugal: global lock, per-account locks if throughput matters\n")
    (tmp_path / "b.html").write_text(
        "<div><!-- frugal: inline style, extract to CSS when reused --></div>\n")
    (tmp_path / "c.js").write_text("// frugal: naive O(n^2) scan\n")
    # a markdown heading is NOT a code comment — must be skipped (no 4th marker)
    (tmp_path / "notes.md").write_text("# frugal: this is a heading, not a marker\n")
    return str(tmp_path)


@given("a source file with a frugal string literal", target_fixture="debt_path")
def _strlit(tmp_path):
    (tmp_path / "d.py").write_text('msg = "frugal: this is not a comment marker"\n')
    return str(tmp_path)


@when("I harvest the frugal debt for that tree", target_fixture="fr")
def _debt(engine, confirmed_intent, debt_path):
    return _f(engine, confirmed_intent, "debt", paths=debt_path)


@when("I get the frugal gain scoreboard", target_fixture="fr")
def _gain(engine, confirmed_intent):
    return _f(engine, confirmed_intent, "gain")


@then(parsers.parse("the debt ledger has {n:d} markers"))
def _ledger_n(fr, n):
    assert fr["markers"] == n, fr


@then(parsers.parse("{n:d} marker has no upgrade trigger"))
def _no_trig(fr, n):
    assert fr["no_trigger"] == n, fr


@then("a DebtMarker node serves the intent")
def _served(engine, confirmed_intent, fr):
    assert served(engine, confirmed_intent, "DebtMarker") >= 1


@then("the scoreboard names the ponytail benchmark source")
def _bench_src(fr):
    assert "ponytail" in fr["benchmark"]["source"].lower()


@then("the scoreboard points to frugal.debt for the only real per-repo number")
def _points_debt(fr):
    assert fr["this_repo"]["use"] == "frugal.debt", fr


# ── review (Slice 3) ──────────────────────────────────────────────────────────


@given("a python file with over-engineering bloat", target_fixture="review_path")
def _bloat(tmp_path):
    # unused import (delete) + a very long line (shrink) — both decidable by analyze.quality
    (tmp_path / "bloat.py").write_text("import os\nx = " + "1 + " * 80 + "1\n")
    return str(tmp_path)


@given("a lean python source tree", target_fixture="review_path")
def _lean(tmp_path):
    (tmp_path / "clean.py").write_text("x = 1\n")
    return str(tmp_path)


@when("I review that tree for over-engineering", target_fixture="fr")
def _review(engine, confirmed_intent, review_path):
    return _f(engine, confirmed_intent, "review", scope="repo", paths=review_path)


@then("the review flags a decidable cut")
def _flags(fr):
    assert fr["decidable_findings"], fr
    # the unused import → 'delete' tag — guards the analyze rule-code → tag mapping
    assert any(f["tag"] == "delete" for f in fr["decidable_findings"]), fr


@then("the review flags no decidable cuts")
def _noflags(fr):
    assert fr["decidable_findings"] == [], fr


@then("the review names the over-engineering tags")
def _rtags(fr):
    assert set(fr["tags"]) >= {"stdlib", "native", "yagni"}, fr


@then("a FrugalReview node serves the intent")
def _rserved(engine, confirmed_intent, fr):
    assert served(engine, confirmed_intent, "FrugalReview") >= 1
