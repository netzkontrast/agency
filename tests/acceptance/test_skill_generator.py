"""Acceptance — skill_generator capability: author + lint a SKILL.md (Spec 028)."""
from __future__ import annotations

from pytest_bdd import scenarios, then, when

from conftest import invoke

scenarios("features/skill_generator.feature")


def _gen(engine, intent, **kw):
    r, _ = invoke(engine, intent, "skill_generator", "generate",
                  agent_id="agent:test", **kw)
    return r["result"] if isinstance(r, dict) and "result" in r else r


@when("I generate a skill with a well-formed description and body",
      target_fixture="gen")
def _gen_good(engine, confirmed_intent):
    return _gen(engine, confirmed_intent, name="widget-helper",
                description=("Use when building a widget, before wiring it up, "
                             "to scaffold the parts."),
                body="# Widget Helper\n\nDo the thing.\n")


@when("I generate a skill with a malformed name and a vague description",
      target_fixture="gen")
def _gen_bad(engine, confirmed_intent):
    return _gen(engine, confirmed_intent, name="BadName",
                description="helps with stuff", body="x")


@then("the generate result carries the skill_md")
def _has_md(gen):
    assert gen.get("skill_md"), gen


@then("the generate result is deploy-ready with no violations")
def _deploy_ready(gen):
    assert gen["ok"] is True and gen["violations"] == [], gen


@then("the generate result is not deploy-ready")
def _not_ready(gen):
    assert gen["ok"] is False, gen


@then("the generate result lists at least one violation")
def _has_violations(gen):
    assert len(gen["violations"]) >= 1, gen
