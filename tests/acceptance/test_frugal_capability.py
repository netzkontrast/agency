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


# ── develop cross-link: the heavy how-to on demand (Spec 348 §7) ───────────────


@when(parsers.parse('I fetch the develop reference for "{topic}"'), target_fixture="ref")
def _develop_reference(engine, confirmed_intent, topic):
    r, _ = invoke(engine, confirmed_intent, "develop", "reference", topic=topic)
    return r["result"]


@then("the frugal reference names every safety-floor marker")
def _ref_floor(ref):
    # derived from _frugal (single source) — so it carries the floor for free
    for m in _frugal.SAFETY_FLOOR_MARKERS:
        assert m in ref["doc"], (m, ref["doc"][:200])


@then("the frugal reference points to the frugal capability verbs")
def _ref_verbs(ref):
    # the reference is the how-to, not just the discipline: it surfaces the actionable verbs
    assert "frugal.review" in ref["doc"] and "frugal.debt" in ref["doc"], ref["doc"][-400:]


@then('"frugal" is listed among the available develop references')
def _ref_available(engine, confirmed_intent):
    # discoverability: a miss reports the available set, which must include frugal
    r, _ = invoke(engine, confirmed_intent, "develop", "reference", topic="__nope__")
    assert "frugal" in r["result"]["available"], r["result"]


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


@then("every finding is a durable FrugalFinding node serving the intent")
def _findings_durable(engine, confirmed_intent, fr):
    # the moat: the FULL judgment is in the graph, not just the FrugalReview count
    # (Jules Sev1). The node count equals the reported full findings count, NOT the
    # token-bounded wire slice — computed, not a pinned magic number (rule 8).
    n = served(engine, confirmed_intent, "FrugalFinding")
    assert n == fr["findings"] >= 1, (n, fr.get("findings"))


# ── event bus first-use-once (Spec 349a) ──────────────────────────────────────


@pytest.fixture
def ev_session():
    """A unique session per test so the first-use dedup (store-backed, may persist)
    is always fresh — both PreToolUse steps share this one value."""
    import uuid
    return "evs-" + uuid.uuid4().hex[:8]


@when(parsers.parse('a PreToolUse fires for "{tool}" the first time'), target_fixture="ev_ctx")
def _ev_first(engine, ev_session, tool):
    out = engine.dispatch_hook({"hook_event_name": "PreToolUse",
                                "session_id": ev_session, "tool_name": tool, "tool_input": {}})
    return (out.get("hookSpecificOutput") or {}).get("additionalContext", "")


@when(parsers.parse('a PreToolUse fires for "{tool}" again'), target_fixture="ev_ctx")
def _ev_again(engine, ev_session, tool):
    out = engine.dispatch_hook({"hook_event_name": "PreToolUse",
                                "session_id": ev_session, "tool_name": tool, "tool_input": {}})
    return (out.get("hookSpecificOutput") or {}).get("additionalContext", "")


@then("the injected context contains the frugal first-use hint")
def _has_hint(ev_ctx):
    assert "[frugal]" in ev_ctx, ev_ctx


@then("the injected context omits the frugal first-use hint")
def _no_hint(ev_ctx):
    assert "[frugal]" not in ev_ctx, ev_ctx


# ── SessionStart deep inject, delivered once per session (Spec 348/349a) ───────


@pytest.fixture
def injects():
    """SessionStart inject(s) captured per session id, in order — a list so a
    repeated SessionStart for ONE session shows the once-per-session dedup."""
    return {}


@when(parsers.parse('a SessionStart hook fires for session "{sid}"'))
def _session_start(engine, injects, sid):
    out = engine.dispatch_hook({"hook_event_name": "SessionStart", "session_id": sid})
    injects.setdefault(sid, []).append(out.get("inject", ""))


def _first_inject(injects, sid):
    got = injects.get(sid, [])
    return got[0] if got else ""


@then(parsers.parse('the session "{sid}" inject names every safety-floor marker'))
def _ss_floor(injects, sid):
    inj = _first_inject(injects, sid)
    for m in _frugal.SAFETY_FLOOR_MARKERS:
        assert m in inj, (m, inj[:200])


@then(parsers.parse('the session "{sid}" inject teaches the ladder, the rules, and the output pattern'))
def _ss_depth(injects, sid):
    # the DEPTH guard: shallow bullets fail this — ladder + rules + output pattern
    inj = _first_inject(injects, sid).lower()
    assert "yagni" in inj and "stdlib" in inj, "ladder missing"
    assert "no unrequested abstractions" in inj or "deletion over addition" in inj, "rules missing"
    assert "skipped:" in inj, "output pattern missing"


@then(parsers.parse('the session "{sid}" inject is far deeper than the one-line per-verb stamp'))
def _ss_deeper(injects, sid):
    inj = _first_inject(injects, sid)
    stamp = _frugal.render(mode="compact")
    assert len(inj) > 3 * len(stamp), (len(inj), len(stamp))


@then(parsers.parse('the session "{sid}" discipline is injected exactly once'))
def _ss_once(injects, sid):
    got = injects.get(sid, [])
    disciplined = [i for i in got if "FRUGAL DISCIPLINE" in i]
    assert len(disciplined) == 1, [len(i) for i in got]


@then(parsers.parse('the second session "{sid}" inject is empty'))
def _ss_second_empty(injects, sid):
    got = injects.get(sid, [])
    assert len(got) >= 2 and got[1] == "", got


@then(parsers.parse('the session "{sid}" inject carries the frugal discipline'))
def _ss_carries(injects, sid):
    assert "FRUGAL DISCIPLINE" in _first_inject(injects, sid), injects.get(sid)


@then(parsers.parse('the session "{sid}" inject is empty'))
def _ss_empty(injects, sid):
    assert _first_inject(injects, sid) == "", injects.get(sid)


@given(parsers.parse('the frugal level is "{level}"'))
def _set_level(level):
    _frugal.set_frugal_level(level)


@then("the tool-call capture stats carry no event-bus marker")
def _clean_capture(engine, confirmed_intent):
    # the bus dedup marker lives in a SEPARATE table — never a captured tool-call
    r, _ = invoke(engine, confirmed_intent, "toolcalls", "stats", agent_id="agent:test")
    phases = r.get("by_phase", {})
    assert not any("first_use" in p or "session" in p for p in phases), phases
