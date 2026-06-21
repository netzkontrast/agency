"""Acceptance — ADR ontology + capability, author & validate (Spec 354 Slice 1).

Behaviour through the real Engine registry (records provenance like any verb):
- the `adr` capability registers (drop-in bar);
- `adr.draft` mints a WH(Y) `Decision` that SERVES the intent;
- the ontology rejects a malformed Decision (missing WH(Y) field / bad status);
- `adr.validate` returns decidable WHY findings (WHY-001 / WHY-003) and an ok flag.
"""
from __future__ import annotations

import pytest
from pytest_bdd import parsers, scenarios, given, then, when

from conftest import invoke, served, tool_names

scenarios("features/adr.feature")


_GOOD = dict(
    context="the bi-temporal graph store",
    facing="cross-session persistence with full history",
    decision="a single append-only GraphQLite graph",
    neglected="a relational mirror, an event log, a document store",
    benefits="one-traversal provenance and keep-both reconciliation",
    tradeoffs="every read must be supersession-aware (as_of)",
)


@given(parsers.parse('an adr theme "{layer}"'), target_fixture="theme_id")
def _theme(engine, confirmed_intent, layer):
    res, _ = invoke(engine, confirmed_intent, "adr", "theme",
                    layer=layer, title=f"{layer} decisions", scope=layer)
    return res.get("id")


@when("I draft a well-formed decision under that theme",
      target_fixture="decision_ctx")
def _draft_good(engine, confirmed_intent, theme_id):
    res, _ = invoke(engine, confirmed_intent, "adr", "draft",
                    theme_id=theme_id, **_GOOD)
    return res


@when(parsers.parse('I draft a decision with an empty "{field}" field under that theme'),
      target_fixture="decision_ctx")
def _draft_empty(engine, confirmed_intent, theme_id, field):
    fields = dict(_GOOD)
    fields[field] = ""
    res, _ = invoke(engine, confirmed_intent, "adr", "draft",
                    theme_id=theme_id, **fields)
    return res


@when(parsers.parse('I draft a decision whose "{field}" field is "{value}" under that theme'),
      target_fixture="decision_ctx")
def _draft_value(engine, confirmed_intent, theme_id, field, value):
    fields = dict(_GOOD)
    fields[field] = value
    res, _ = invoke(engine, confirmed_intent, "adr", "draft",
                    theme_id=theme_id, **fields)
    return res


@when(parsers.parse('I draft a decision with an over-long "{field}" field under that theme'),
      target_fixture="decision_ctx")
def _draft_overlong(engine, confirmed_intent, theme_id, field):
    fields = dict(_GOOD)
    fields[field] = "x" * 500          # well over any WH(Y) maxLength budget
    res, _ = invoke(engine, confirmed_intent, "adr", "draft",
                    theme_id=theme_id, **fields)
    return res


@when(parsers.parse('I create a Decision node missing the "{field}" field'),
      target_fixture="adr_result")
def _create_missing(engine, confirmed_intent, field):
    props = dict(_GOOD, status="proposed")
    props.pop(field, None)
    res, _ = invoke(engine, confirmed_intent, "manage", "create",
                    label="Decision", props=props)
    return res


@when(parsers.parse('I create a Decision node with status "{status}"'),
      target_fixture="adr_result")
def _create_bad_status(engine, confirmed_intent, status):
    props = dict(_GOOD, status=status)
    res, _ = invoke(engine, confirmed_intent, "manage", "create",
                    label="Decision", props=props)
    return res


@when("I validate that decision", target_fixture="validate_result")
def _validate(engine, confirmed_intent, decision_ctx):
    res, _ = invoke(engine, confirmed_intent, "adr", "validate",
                    decision_id=decision_ctx.get("id"))
    return res


@then(parsers.parse('a wire tool name contains "{frag}"'))
def _wire_contains(engine, frag):
    # The full per-verb wire surface is the non-code-mode build (code-mode
    # deliberately exposes only search/get_schema/execute — Goal 5).
    names = tool_names(engine, codemode=False)
    assert any(frag in n for n in names), sorted(names)


@then(parsers.parse('the decision result has status "{status}"'))
def _status_is(decision_ctx, status):
    assert decision_ctx.get("status") == status, decision_ctx


@then("the decision serves the intent")
def _serves(engine, confirmed_intent):
    assert served(engine, confirmed_intent, "Decision") >= 1


@then("the adr result is an error")
def _is_error(adr_result):
    assert adr_result.get("error"), adr_result


@then("the decision result is an error")
def _decision_is_error(decision_ctx):
    assert decision_ctx.get("error"), decision_ctx


@then(parsers.parse('the validate findings include rule "{rule}" with severity "{sev}"'))
def _finding_present(validate_result, rule, sev):
    findings = validate_result.get("findings") or []
    assert any(f.get("rule") == rule and f.get("severity") == sev for f in findings), findings


@then("the validate result is not ok")
def _not_ok(validate_result):
    assert validate_result.get("ok") is False, validate_result


@then("the validate result is ok")
def _ok(validate_result):
    assert validate_result.get("ok") is True, validate_result
