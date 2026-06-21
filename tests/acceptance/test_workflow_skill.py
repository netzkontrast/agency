"""Acceptance — the develop-spec repo-development workflow (Spec 358).

Behaviour: `develop.skill_walk("develop-spec", …)` walks the discipline one phase
at a time and PAUSES at the hard gates — the design improve-gate and the
ADR-approval hinge — recording each phase as provenance under the intent.
"""
from __future__ import annotations

from pytest_bdd import given, parsers, scenarios, then, when

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


# ── Slice 2 — the ADR-hinge step verbs (end-to-end) ───────────────────────────

_SPEC_WITH_DECISIONS = """---
spec_id: "WF-E2E"
domain: datalayer
---
# E2E spec

## Why
The store needs cross-session persistence.

## Design
We decided for a single append-only GraphQLite graph instead of a relational mirror.
We chose bi-temporal versioning rather than destructive overwrites.

## Failure modes
Reads must be supersession-aware.
"""


@given("an ingested spec with decisions", target_fixture="spec_id")
def _ingested_spec(engine, confirmed_intent, tmp_path):
    p = tmp_path / "e2e.md"
    p.write_text(_SPEC_WITH_DECISIONS, encoding="utf-8")
    res, _ = invoke(engine, confirmed_intent, "document", "ingest", path=str(p))
    return res.get("document_id")


@when("I open the spec to extract its decisions")
def _to_open(engine, confirmed_intent, spec_id):
    invoke(engine, confirmed_intent, "workflow", "to_open", spec_id=spec_id)


@when("I attempt to begin implementation", target_fixture="begin")
def _begin(engine, confirmed_intent, spec_id):
    res, _ = invoke(engine, confirmed_intent, "workflow", "begin_impl", spec_id=spec_id)
    return res


@when(parsers.parse('I approve the spec decisions as owner "{approver}"'))
def _approve_decisions(engine, confirmed_intent, spec_id, approver):
    invoke(engine, confirmed_intent, "workflow", "approve_decisions",
           spec_id=spec_id, approver=approver, override=True)


@then("implementation is blocked on unapproved decisions")
def _impl_blocked(begin):
    assert begin.get("begun") is False, begin
    assert begin.get("blocked") is True, begin


@then("implementation begins with hints loaded")
def _impl_begins(begin):
    assert begin.get("begun") is True, begin
    assert begin.get("state") == "inprogress", begin
    assert begin.get("hint_count", 0) >= 1, begin


@when(parsers.parse('I mark the spec done as owner "{approver}"'),
      target_fixture="done_result")
def _mark_done(engine, confirmed_intent, spec_id, approver):
    # apply=False — assert the graph cascade (approve + move→done) without
    # writing architecture.md / docs/adr into the working tree during tests.
    res, _ = invoke(engine, confirmed_intent, "workflow", "mark_done",
                    spec_id=spec_id, approver=approver, apply=False, override=True)
    return res


@then("the spec is recorded done")
def _is_done(done_result):
    assert done_result.get("done") is True, done_result
