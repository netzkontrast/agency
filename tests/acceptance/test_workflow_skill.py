"""Acceptance — the develop-spec repo-development workflow (Spec 358).

Behaviour: `develop.skill_walk("develop-spec", …)` walks the discipline one phase
at a time and PAUSES at the hard gates — the design improve-gate and the
ADR-approval hinge — recording each phase as provenance under the intent.
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, then, when

from conftest import invoke, served

scenarios("features/workflow_skill.feature")

# The produces keys for phases 1–8 (everything up to the improve gate).
_DESIGN_INPUTS = {k: "x" for k in (
    "intent_id", "scope", "design", "prior_art", "acceptance",
    "spec_md", "panel_findings", "brooks_findings")}


@when("I start the develop-spec walk", target_fixture="walk")
def _start(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "develop", "skill_walk",
                  name="develop-spec", inputs={})
    return r


@when("I walk develop-spec with the design inputs", target_fixture="walk")
def _walk_design(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "develop", "skill_walk",
                  name="develop-spec", inputs=dict(_DESIGN_INPUTS))
    return r


@when("I resume the walk past the improve gate", target_fixture="walk")
def _resume(engine, confirmed_intent, walk):
    inputs = dict(_DESIGN_INPUTS, design_good="yes", decision_drafts="d1")
    r, _ = invoke(engine, confirmed_intent, "develop", "skill_walk",
                  name="develop-spec", inputs=inputs,
                  resume_from=walk.get("skill_id", ""))
    return r


@then(parsers.parse('the first phase is "{phase}"'))
def _first_phase(walk, phase):
    assert walk.get("error") != "unknown skill 'develop-spec'", walk
    assert walk.get("phase") == phase, walk


@then(parsers.parse('the walk pauses at the "{phase}" hard gate'))
def _pauses(walk, phase):
    assert walk.get("status") == "input-required", walk
    assert walk.get("phase") == phase, walk


@then("the walked phases are recorded as provenance")
def _provenance(engine, confirmed_intent):
    assert served(engine, confirmed_intent, "Phase") >= 8, "expected ≥8 Phase nodes"
