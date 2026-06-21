"""Acceptance — Spec 355: six quality modes + develop.review seam.

Behaviour-only: assert what the verbs and pure functions DO (roles, phase structure,
return shapes, Iron Law gate predicate, merge contract). No internals, no mocks.
"""
from __future__ import annotations

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.capabilities.analyze._findings import Finding, FindingSeverity, make_finding
from agency.capabilities.analyze._review import (
    classify_remedy,
    iron_law_passed,
    merge_findings,
)
from conftest import invoke

scenarios("features/quality_review.feature")


# ── fixtures ─────────────────────────────────────────────────────────────────

@given("an engine and confirmed intent", target_fixture="engine_iid")
def _engine_iid(engine, iid):
    return engine, iid


# ── Iron Law gate — pure predicate ────────────────────────────────────────────

@given('a brooks Finding with risk_code "R1" and empty remedy',
       target_fixture="gate_findings")
def _r1_no_remedy():
    f = make_finding("Q003", "warn", "app.py", 10, "long fn", "evidence",
                     risk_code="R1", consequence="overload", remedy="")
    return [f]


@given('a brooks Finding with risk_code "R1" and empty consequence',
       target_fixture="gate_findings")
def _r1_no_consequence():
    f = make_finding("Q003", "warn", "app.py", 10, "long fn", "evidence",
                     risk_code="R1", consequence="", remedy="extract a helper")
    return [f]


@given('a brooks Finding with risk_code "R1", consequence, and remedy filled',
       target_fixture="gate_findings")
def _r1_complete():
    f = make_finding("Q003", "warn", "app.py", 10, "long fn", "evidence",
                     risk_code="R1", consequence="overload", remedy="extract a helper")
    return [f]


@given("a decidable-only Finding with no risk_code but no consequence or remedy",
       target_fixture="gate_findings")
def _decidable_only():
    f = make_finding("Q001", "info", "app.py", 1, "unused import", "evidence")
    # risk_code="", consequence="", remedy="" — decidable-only
    return [f]


@when("the iron_law_passed predicate is evaluated", target_fixture="gate_result")
def _eval_gate(gate_findings):
    return iron_law_passed(gate_findings)


@then("it returns False")
def _gate_false(gate_result):
    assert gate_result is False


@then("it returns True")
def _gate_true(gate_result):
    assert gate_result is True


@then("it returns True because only brooks findings (non-empty risk_code) are checked")
def _gate_true_decidable_only(gate_result):
    assert gate_result is True


# ── merge contract ────────────────────────────────────────────────────────────

@given('a decidable R1 Finding for file "app.py" line 10',
       target_fixture="decidable_list")
def _decidable_r1():
    f = make_finding("Q003", "warn", "app.py", 10, "long fn", "evidence",
                     risk_code="R1", consequence="overload", remedy="refactor")
    return [f]


@given('a judgment R1 Finding for the same file and line with a sharper remedy',
       target_fixture="judgment_list")
def _judgment_same_span():
    f = make_finding("Q003", "fail", "app.py", 10, "long fn (judgment)", "evidence",
                     risk_code="R1", consequence="overload (judgment)",
                     remedy="extract the nested block into a named helper function")
    return [f]


@given('a judgment R1 Finding for file "app.py" line 50 (different span)',
       target_fixture="judgment_list")
def _judgment_different_span():
    f = make_finding("Q003", "warn", "app.py", 50, "another long fn", "evidence",
                     risk_code="R1", consequence="overload", remedy="extract a helper")
    return [f]


@when("merge_findings is called with the decidable and judgment lists",
      target_fixture="merged")
def _do_merge(decidable_list, judgment_list):
    return merge_findings(decidable_list, judgment_list)


@then("there is exactly one R1 Finding in the output")
def _one_r1(merged):
    r1s = [f for f in merged if f.risk_code == "R1"]
    assert len(r1s) == 1


@then("the output Finding carries the judgment's sharper remedy")
def _sharper_remedy(merged):
    r1 = next(f for f in merged if f.risk_code == "R1")
    assert "named helper" in r1.remedy


@then("there are exactly two R1 Findings in the output")
def _two_r1(merged):
    r1s = [f for f in merged if f.risk_code == "R1"]
    assert len(r1s) == 2


# ── classify_remedy ───────────────────────────────────────────────────────────

@given("a Finding whose remedy is \"extract constant to a named variable\"",
       target_fixture="remedy_finding")
def _safe_remedy_finding():
    return make_finding("Q003", "info", "x.py", 1, "msg", "ev",
                        remedy="extract constant to a named variable")


@given("a Finding whose remedy is \"invert dependency direction\"",
       target_fixture="remedy_finding")
def _risky_remedy_finding():
    return make_finding("A001", "fail", "x.py", 1, "cycle", "ev",
                        risk_code="R5", remedy="invert dependency direction")


@when("classify_remedy is called", target_fixture="classification")
def _do_classify(remedy_finding):
    return classify_remedy(remedy_finding)


@then('the result is "safe"')
def _is_safe(classification):
    assert classification == "safe"


@then('the result is "risky"')
def _is_risky(classification):
    assert classification == "risky"


# ── skill registry ────────────────────────────────────────────────────────────

@when("I look at the develop capability's skill registry", target_fixture="skill_registry")
def _get_skill_registry(engine_iid):
    engine, _ = engine_iid
    return engine.registry.get("develop").ontology.skills


@then(parsers.re(r'"(?P<name>[^"]+)" is a registered walkable skill'))
def _skill_registered(name, skill_registry):
    assert name in skill_registry, f"{name!r} not in {sorted(skill_registry)}"


@when("I inspect the quality-review skill", target_fixture="skill_schema")
def _get_quality_review(engine_iid):
    engine, _ = engine_iid
    skills = engine.registry.get("develop").ontology.skills
    assert "quality-review" in skills, "quality-review not registered"
    return skills["quality-review"]


@when("I inspect the quality-sweep skill", target_fixture="skill_schema")
def _get_quality_sweep(engine_iid):
    engine, _ = engine_iid
    skills = engine.registry.get("develop").ontology.skills
    assert "quality-sweep" in skills, "quality-sweep not registered"
    return skills["quality-sweep"]


def _phase_names(skill_schema: dict) -> list[str]:
    return [p.get("name", p.get("produces", ["?"])[0])
            for p in skill_schema.get("phases", [])]


@then(parsers.re(r'it has a phase named "(?P<name>[^"]+)"'))
def _has_phase(name, skill_schema):
    names = _phase_names(skill_schema)
    assert name in names, f"phase {name!r} not found; phases={names}"


# ── verb metadata ─────────────────────────────────────────────────────────────

@when("I inspect develop.review's verb metadata", target_fixture="verb_meta")
def _develop_review_meta(engine_iid):
    engine, _ = engine_iid
    cap = engine.registry.get("develop")
    v = cap.verbs.get("review")
    return {"role": v.role if v else ""} if v else {}


@when("I inspect develop.remediate's verb metadata", target_fixture="verb_meta")
def _develop_remediate_meta(engine_iid):
    engine, _ = engine_iid
    cap = engine.registry.get("develop")
    v = cap.verbs.get("remediate")
    return {"role": v.role if v else ""} if v else {}


@then(parsers.re(r'its role is "(?P<role>[^"]+)"'))
def _has_role(role, verb_meta):
    actual = (verb_meta or {}).get("role", "")
    assert actual == role, f"expected role={role!r}, got {actual!r}"


# ── verb behaviour ────────────────────────────────────────────────────────────

@when("I call develop.review with mode \"review\" and scope \".\"",
      target_fixture="review_result")
def _call_develop_review(engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "develop", "review", mode="review", scope=".")
    return result


@then("the result contains scope_line, findings, iron_law_passed, and mode")
def _review_shape(review_result):
    for key in ("scope_line", "findings", "iron_law_passed", "mode"):
        assert key in review_result, f"missing key {key!r} in result"


@then('mode is "review"')
def _mode_review(review_result):
    assert review_result["mode"] == "review"


@when("I call analyze.review with mode \"review\" and path \".\"",
      target_fixture="headless_result")
def _call_analyze_review(engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "analyze", "review", mode="review", path=".")
    return result


@then("the result contains headless=True")
def _is_headless(headless_result):
    assert headless_result.get("headless") is True


@then("risky remedies are reported in gated")
def _has_gated(headless_result):
    assert "gated" in headless_result


@then("the result contains iron_law_passed")
def _has_iron_law(headless_result):
    assert "iron_law_passed" in headless_result
