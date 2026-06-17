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


# ── Spec 290 read-API completion: whats_next + research_state ─────────────────

@when("I ask manage.whats_next for the confirmed intent", target_fixture="next_result")
def _whats_next(engine, confirmed_intent):
    return _m(engine, confirmed_intent, "whats_next", for_intent_id=confirmed_intent)


@then("whats_next echoes the intent acceptance and lists at least one next action")
def _whats_next_acceptance(next_result):
    assert next_result["acceptance"] == "verified", next_result
    assert next_result["done"] is False, next_result
    assert len(next_result["next"]) >= 1, next_result


@given("a research lead with one citation exists", target_fixture="research_ids")
def _research_lead(engine, confirmed_intent):
    lead = _m(engine, confirmed_intent, "create", label="Research",
              props={"question": "what is the state of X", "depth": "standard",
                     "started_at": 0, "status": "planning"})
    rid = lead["id"]
    _m(engine, confirmed_intent, "create", label="Citation",
       props={"source_kind": "codebase", "source_url_or_path": "agency/x.py",
              "evidence_text": "found", "confidence": 0.5,
              "claim_supported": "X holds", "research_id": rid})
    return {"research_id": rid}


@when("I ask manage.research_state", target_fixture="research_state_result")
def _research_state(engine, confirmed_intent, research_ids):
    return _m(engine, confirmed_intent, "research_state")


@then("research_state totals report at least one lead and one citation")
def _research_totals(research_state_result):
    t = research_state_result["totals"]
    assert t["leads"] >= 1 and t["citations"] >= 1, research_state_result


@then("research_state lists the lead as pending")
def _research_pending(research_state_result, research_ids):
    assert research_ids["research_id"] in research_state_result["pending"], \
        research_state_result


# ── wire-schema regression (Spec 293): dict params must cross the MCP wire ─────
# The acceptance scenarios above use the in-process registry path, which bypasses
# the wire schema. This guards the bug the CLI system test caught: a `props`
# param with no type annotation was typed as STRING on the wire, so a dict was
# rejected. Exercises build_mcp's per-verb schema directly.

# ── Spec 290 Slice 2: the markdown dashboard projection (rule 2) ─────────────

@when("I ask manage.render for the confirmed intent", target_fixture="render_result")
def _render(engine, confirmed_intent, managed_id):
    return _m(engine, confirmed_intent, "render", for_intent_id=confirmed_intent)


@then("the dashboard markdown has a heading and an open-intents section")
def _render_structure(render_result):
    md = render_result["markdown"]
    assert md.lstrip().startswith("#"), render_result
    assert "Open intents" in md, md
    assert render_result["view"] == "dashboard", render_result


@then("the dashboard echoes the intent acceptance and a next action")
def _render_intent(render_result):
    md = render_result["markdown"]
    assert "verified" in md, md          # the confirmed intent's acceptance
    assert "Next" in md, md


# ── Spec 290 invariant: the read-API is read-only ────────────────────────────
# Invoking any read verb records an Invocation (the provenance moat) but must add
# NO domain node — it reads the graph, never mutates it. Asserted against the
# live domain labels the read-suite touches, not a frozen total (rule 8).

def test_manage_read_api_adds_no_domain_node(engine):
    from conftest import invoke

    iid = engine.intent.capture("p", "d", "a")
    engine.intent.confirm(iid)

    domain_labels = ("Intent", "Lifecycle", "Gate", "Research", "Citation",
                     "ResearchClaim", "Verification", "Artefact", "Reflection")

    def census():
        return {lbl: len(engine.memory.find(lbl)) for lbl in domain_labels}

    before = census()
    for verb, kw in (("whats_next", {"for_intent_id": iid}),
                     ("research_state", {}),
                     ("state", {"for_intent_id": iid}),
                     ("open_intents", {}),
                     ("timeline", {"for_intent_id": iid}),
                     ("artefacts", {"for_intent_id": iid}),
                     ("render", {"for_intent_id": iid})):
        invoke(engine, iid, "manage", verb, agent_id="agent:test", **kw)
    assert census() == before


def test_manage_create_accepts_a_dict_props_through_the_wire(engine):
    from conftest import call_tool
    iid = call_tool(engine, "intent_bootstrap",
                    {"purpose": "w", "deliverable": "w", "acceptance": "w"})["intent_id"]
    r = call_tool(engine, "capability_manage_create",
                  {"intent_id": iid, "agent_id": "a", "label": "Document",
                   "props": {"path": "/w.md", "content_sha": "abc"}})
    assert r["id"].startswith("document:"), r
