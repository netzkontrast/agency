"""Acceptance — manage capability: generic CRUD (Spec 293)."""
from __future__ import annotations

from pytest_bdd import given, parsers, scenarios, then, when

from conftest import invoke

scenarios("features/manage.feature")


def _m(engine, intent, verb, **kw):
    r, _ = invoke(engine, intent, "manage", verb, agent_id="agent:test", **kw)
    return r


@when(parsers.parse('I manage.create a "{label}" with path "{path}" and content_sha "{sha}"'),
      target_fixture="create_result")
def _create(engine, confirmed_intent, label, path, sha):
    return _m(engine, confirmed_intent, "create",
              label=label, props={"path": path, "content_sha": sha})


@then("the create result carries an id")
def _has_id(create_result):
    assert create_result.get("id", "").startswith("document:"), create_result


@then("manage.read on that id reports it live with the path")
def _read_live(engine, confirmed_intent, create_result):
    r = _m(engine, confirmed_intent, "read", node_id=create_result["id"])
    assert r["live"] is True and r["props"]["path"] == "/x.md", r


@given('a managed "Document" node exists', target_fixture="managed_id")
def _managed(engine, confirmed_intent):
    r = _m(engine, confirmed_intent, "create",
           label="Document", props={"path": "/m.md", "content_sha": "aaaa"})
    return r["id"]


@when(parsers.parse('I manage.update that node\'s content_sha to "{sha}"'))
def _update(engine, confirmed_intent, managed_id, sha):
    _m(engine, confirmed_intent, "update", node_id=managed_id,
       props={"content_sha": sha})


@then("manage.read shows the updated content_sha")
def _read_updated(engine, confirmed_intent, managed_id):
    r = _m(engine, confirmed_intent, "read", node_id=managed_id)
    assert r["props"]["content_sha"] == "feedface", r


@when("I manage.retract that node")
def _retract(engine, confirmed_intent, managed_id):
    _m(engine, confirmed_intent, "retract", node_id=managed_id)


@then("manage.read reports it not live")
def _read_not_live(engine, confirmed_intent, managed_id):
    r = _m(engine, confirmed_intent, "read", node_id=managed_id)
    assert r["live"] is False, r


@then('manage.list of "Document" does not include that node')
def _list_excludes(engine, confirmed_intent, managed_id):
    r = _m(engine, confirmed_intent, "list", label="Document")
    assert managed_id not in {row.get("id") for row in r["rows"]}, r


@when(parsers.parse('I manage.amend that node\'s content_sha to "{sha}"'),
      target_fixture="amend_result")
def _amend(engine, confirmed_intent, managed_id, sha):
    return _m(engine, confirmed_intent, "amend", node_id=managed_id,
              changes={"content_sha": sha})


@then("the amend result carries a new id distinct from the old")
def _amend_new(amend_result, managed_id):
    assert amend_result["new_id"] != managed_id
    assert amend_result["old_id"] == managed_id


@when("I manage.create a \"Document\" with no required props",
      target_fixture="create_result")
def _create_bad(engine, confirmed_intent):
    return _m(engine, confirmed_intent, "create", label="Document", props={})


@then("the create result carries an error")
def _create_error(create_result):
    assert "error" in create_result and "Document" in create_result["error"]


# ── Spec 290 read-API folded onto manage ──────────────────────────────────────

@when("I ask manage.state", target_fixture="state_result")
def _state(engine, confirmed_intent, managed_id):
    return _m(engine, confirmed_intent, "state", for_intent_id=confirmed_intent)


@then("the state rollup reports at least one intent and the document count")
def _state_rollup(state_result):
    assert state_result["intents"] >= 1, state_result
    assert state_result["artefacts"] >= 0 and "lifecycles_by_state" in state_result
    assert state_result["serves_count"] >= 1


@when("I ask manage.open_intents", target_fixture="open_result")
def _open(engine, confirmed_intent, managed_id):
    return _m(engine, confirmed_intent, "open_intents")


@then("open_intents includes the confirmed intent with a positive serves_count")
def _open_includes(open_result, confirmed_intent):
    row = next((r for r in open_result["intents"] if r["id"] == confirmed_intent), None)
    assert row is not None and row["serves_count"] >= 1, open_result


@when("I ask manage.timeline for the confirmed intent", target_fixture="timeline_result")
def _timeline(engine, confirmed_intent, managed_id):
    return _m(engine, confirmed_intent, "timeline", for_intent_id=confirmed_intent)


@then("the timeline lists the create invocation")
def _timeline_invocation(timeline_result):
    assert timeline_result["count"] >= 1, timeline_result
    assert any(it["kind"] == "invocation" and "manage.create" in it["name"]
               for it in timeline_result["timeline"]), timeline_result
