"""Acceptance — ADR Definition-of-Done gate (Spec 355 Slice 1).

Behaviour through the real Engine registry:
- `adr.dod_check` returns the eight ported SPEC-001-E criteria (auto/partial/human);
- `adr.approve` blocks on a failed automated criterion, pauses for human confirm
  when no approver is present, advances to `approved` on owner confirmation, and
  honours a provenance-stamped OWNER override while rejecting an agent self-approve.
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, given, then, when

from conftest import invoke

scenarios("features/adr_dod.feature")


_GOOD = dict(
    context="the bi-temporal graph store",
    facing="cross-session persistence with full history",
    decision="a single append-only GraphQLite graph",
    neglected="a relational mirror, an event log, a document store",
    benefits="one-traversal provenance and keep-both reconciliation",
    tradeoffs="every read must be supersession-aware (as_of)",
)


def _theme(engine, intent, layer="datalayer"):
    res, _ = invoke(engine, intent, "adr", "theme", layer=layer)
    return res.get("id")


@given("a well-formed decision under a theme", target_fixture="decision_id")
def _good_decision(engine, confirmed_intent):
    theme_id = _theme(engine, confirmed_intent)
    res, _ = invoke(engine, confirmed_intent, "adr", "draft",
                    theme_id=theme_id, **_GOOD)
    return res.get("id")


@given("a decision with only one neglected alternative", target_fixture="decision_id")
def _thin_decision(engine, confirmed_intent):
    theme_id = _theme(engine, confirmed_intent)
    res, _ = invoke(engine, confirmed_intent, "adr", "draft",
                    theme_id=theme_id, **dict(_GOOD, neglected="just one thing"))
    return res.get("id")


@when("I run the DoD check", target_fixture="dod")
def _run_dod(engine, confirmed_intent, decision_id):
    res, _ = invoke(engine, confirmed_intent, "adr", "dod_check",
                    decision_id=decision_id)
    return res


@when(parsers.parse('I approve it as "{approver}"'), target_fixture="approval")
def _approve(engine, confirmed_intent, decision_id, approver):
    res, _ = invoke(engine, confirmed_intent, "adr", "approve",
                    decision_id=decision_id, approver=approver)
    return res


@when(parsers.parse('I override-approve it as "{approver}"'), target_fixture="approval")
def _override(engine, confirmed_intent, decision_id, approver):
    res, _ = invoke(engine, confirmed_intent, "adr", "approve",
                    decision_id=decision_id, approver=approver, override=True)
    return res


@when("I approve it with no approver", target_fixture="approval")
def _approve_blank(engine, confirmed_intent, decision_id):
    res, _ = invoke(engine, confirmed_intent, "adr", "approve",
                    decision_id=decision_id)
    return res


@then("the DoD auto checks pass")
def _auto_pass(dod):
    assert dod.get("auto_passed") is True, dod


@then("the DoD check lists at least one human-pending criterion")
def _human_pending(dod):
    assert dod.get("human_pending"), dod


@then("the decision is approved")
def _approved(approval):
    assert approval.get("approved") is True, approval


@then("the decision is not approved")
def _not_approved(approval):
    assert approval.get("approved") is not True, approval


@then("the approval records an override")
def _override_recorded(approval):
    assert approval.get("override") is True, approval


@then("the approval is input-required")
def _input_required(approval):
    assert approval.get("input_required") is True, approval


@then(parsers.parse('the decision status is "{status}"'))
def _status_is(engine, confirmed_intent, decision_id, status):
    res, _ = invoke(engine, confirmed_intent, "adr", "read", decision_id=decision_id)
    assert res.get("status") == status, res


@then(parsers.parse('the decision status remains "{status}"'))
def _status_remains(engine, confirmed_intent, decision_id, status):
    res, _ = invoke(engine, confirmed_intent, "adr", "read", decision_id=decision_id)
    assert res.get("status") == status, res
