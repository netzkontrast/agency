"""Acceptance — intent capability: critical-thinking methods, chaining,
owners, path analysis, and skill projection. Converted from:
  tests/test_intent_capability.py
  tests/test_intent_chain.py
  tests/test_intent_owners.py
  tests/test_intent_path_analysis.py
  tests/test_intent_suggests.py

Dropped as implementation/structural (not observable behaviour):
  - test_intent_registers_with_critical_thinking_methods — inspects cap.verbs
    (internal registry structure, not observable output)
  - test_authored_critical_thinking_discipline_overrides_and_walks — asserts
    ontology.skills membership and skills/lint verb (structural audit)
  - test_analyze_has_paths_verb — inspects cap.verbs (structural)
  - test_paths_in_analysis_axis_enum — inspects engine.ontology.enums (structural)
  - test_pathological_depth_fails_loud — calls private _check_no_cycle method
  - test_cycle_detection_two_intent_loop — calls private _check_no_cycle method
  - test_cycle_detection_self_loop — calls private _check_no_cycle method
  - test_intent_bootstrap_defaults_user_owner — the wire call makes no assertion
    on the actual returned value in the original test
  - test_no_dangling_cue (from intent_cues) — inspects internal verb lists
"""
from __future__ import annotations

import asyncio
import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.capability import CapabilityBase, verb
from agency.engine import Engine
from agency.ontology import OntologyExtension

from conftest import invoke

scenarios("features/intent.feature")


# ── helpers ──────────────────────────────────────────────────────────────────

def _res(r):
    """Unwrap the result wrapper if present."""
    return r["result"] if isinstance(r, dict) and "result" in r else r


def _call(engine, iid, cap, v, **kw):
    result, _ = engine.registry.invoke(engine.memory, iid, cap, v, **kw)
    return _res(result)


# ── step fixtures shared across scenarios ────────────────────────────────────

@pytest.fixture
def root_iid(engine):
    return engine.intent.capture_and_confirm("root", "x", "x", owner="user")


# ─────────────────────────────────────────────────────────────────────────────
# Critical-thinking methods
# ─────────────────────────────────────────────────────────────────────────────

@when("I invoke the premortem method with no subject override",
      target_fixture="premortem_result")
def _premortem(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "intent", "premortem")


@then("the result method is \"premortem\"")
def _method_is_premortem(premortem_result):
    assert premortem_result["method"] == "premortem"


@then("the result subject contains the intent deliverable")
def _subject_contains_deliverable(premortem_result):
    # The confirmed_intent fixture creates an intent with deliverable "behaviour preserved"
    assert "behaviour preserved" in premortem_result["subject"]


@then("the result has at least 3 steps")
def _at_least_3_steps(premortem_result):
    assert len(premortem_result["steps"]) >= 3


@when('I invoke decompose with subject "migrate the database"',
      target_fixture="decompose_result")
def _decompose_explicit(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "intent", "decompose",
                 subject="migrate the database")


@then('the result subject is "migrate the database"')
def _subject_explicit(decompose_result):
    assert decompose_result["subject"] == "migrate the database"


@when('I invoke tradeoffs with options "postgres, sqlite" and criteria "cost, risk"',
      target_fixture="tradeoffs_result")
def _tradeoffs_explicit(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "intent", "tradeoffs",
                 options="postgres, sqlite", criteria="cost, risk")


@then('the result options list is ["postgres", "sqlite"]')
def _options_parsed(tradeoffs_result):
    assert tradeoffs_result["options"] == ["postgres", "sqlite"]


@then('the result criteria list is ["cost", "risk"]')
def _criteria_parsed(tradeoffs_result):
    assert tradeoffs_result["criteria"] == ["cost", "risk"]


@when("I invoke tradeoffs with no options or criteria",
      target_fixture="tradeoffs_defaults")
def _tradeoffs_defaults(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "intent", "tradeoffs")


@then('"cost" and "reversibility" are among the default criteria')
def _default_criteria(tradeoffs_defaults):
    assert "cost" in tradeoffs_defaults["criteria"]
    assert "reversibility" in tradeoffs_defaults["criteria"]


# ── suggests ────────────────────────────────────────────────────────────────

@when('I call suggests with state "which skill should I walk"',
      target_fixture="suggests_result")
def _suggests_skill(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "intent", "suggests",
                 called_state="which skill should I walk")


@then('a skill is projected with mode "pattern"')
def _projected_pattern(suggests_result):
    assert suggests_result["skill"] is not None
    assert suggests_result["mode"] == "pattern"


@then("the projected confidence is 0.8")
def _confidence_08(suggests_result):
    assert suggests_result["confidence"] == 0.8


@when('I call suggests with state "totally unrelated xyzzy"',
      target_fixture="suggests_none")
def _suggests_none(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "intent", "suggests",
                 called_state="totally unrelated xyzzy")


@then("no skill is projected")
def _no_skill(suggests_none):
    assert suggests_none["skill"] is None


@when('I call suggests with state "which skill should I walk" and floor 0.9',
      target_fixture="suggests_floor")
def _suggests_floor(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "intent", "suggests",
                 called_state="which skill should I walk", floor=0.9)


@then("no skill is projected and the reason mentions the floor")
def _no_skill_floor(suggests_floor):
    assert suggests_floor["skill"] is None
    assert "floor" in suggests_floor["reason"]


# ─────────────────────────────────────────────────────────────────────────────
# Intent chaining
# ─────────────────────────────────────────────────────────────────────────────

@when("I capture and confirm a root intent", target_fixture="a_root_iid")
def _capture_root(engine):
    iid = engine.intent.capture("a root", "x", "x")
    engine.intent.confirm(iid)
    return iid


@then("that intent has no parent_intent_id")
def _no_parent(engine, a_root_iid):
    rows = engine.memory.find("Intent")
    me = next(r for r in rows if r["id"] == a_root_iid)
    assert me.get("parent_intent_id", "") == ""


@when("I capture a child intent under a parent", target_fixture="parent_child_pair")
def _capture_parent_child(engine):
    parent = engine.intent.capture("parent", "x", "x")
    engine.intent.confirm(parent)
    child = engine.intent.capture("child", "x", "x", parent_intent_id=parent)
    engine.intent.confirm(child)
    return parent, child


@then("the child's parent_intent_id matches the parent")
def _child_parent_id(engine, parent_child_pair):
    parent, child = parent_child_pair
    rows = engine.memory.find("Intent")
    me = next(r for r in rows if r["id"] == child)
    assert me["parent_intent_id"] == parent


@then("a PARENT_INTENT edge exists from the child to the parent in the graph")
def _parent_edge(engine, parent_child_pair):
    parent, child = parent_child_pair
    rows = engine.memory.g.query(
        "MATCH (c:Intent)-[:PARENT_INTENT]->(p:Intent) "
        "WHERE c.id = $cid RETURN p",
        {"cid": child})
    assert len(rows) == 1
    assert rows[0]["p"]["properties"]["id"] == parent


@when("I build a three-level intent chain", target_fixture="chain_ids")
def _build_three_level(engine):
    grand = engine.intent.capture("grand", "x", "x")
    engine.intent.confirm(grand)
    parent = engine.intent.capture("parent", "x", "x", parent_intent_id=grand)
    engine.intent.confirm(parent)
    child = engine.intent.capture("child", "x", "x", parent_intent_id=parent)
    engine.intent.confirm(child)
    return grand, parent, child


@then("the leaf can reach the root via PARENT_INTENT edges in the graph")
def _three_level_traversable(engine, chain_ids):
    grand, _, child = chain_ids
    rows = engine.memory.g.query(
        "MATCH (c:Intent)-[:PARENT_INTENT*1..3]->(g:Intent) "
        "WHERE c.id = $cid AND g.id = $gid RETURN g",
        {"cid": child, "gid": grand})
    assert len(rows) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# Owner rules
# ─────────────────────────────────────────────────────────────────────────────

@then("that intent's owner is \"user\"")
def _owner_user(engine, a_root_iid):
    rows = engine.memory.find("Intent")
    me = next(r for r in rows if r["id"] == a_root_iid)
    assert me["owner"] == "user"


@then("the child's owner is \"agent\"")
def _child_owner_agent(engine, parent_child_pair):
    _, child = parent_child_pair
    rows = engine.memory.find("Intent")
    me = next(r for r in rows if r["id"] == child)
    assert me["owner"] == "agent"


@when("I capture a child intent under a parent with owner \"subagent\"",
      target_fixture="parent_child_subagent_pair")
def _capture_child_subagent(engine):
    parent = engine.intent.capture("p", "x", "x")
    engine.intent.confirm(parent)
    child = engine.intent.capture("c", "x", "x",
                                  parent_intent_id=parent,
                                  owner="subagent")
    engine.intent.confirm(child)
    return parent, child


@then("the child's owner is \"subagent\"")
def _child_owner_subagent(engine, parent_child_subagent_pair):
    _, child = parent_child_subagent_pair
    rows = engine.memory.find("Intent")
    me = next(r for r in rows if r["id"] == child)
    assert me["owner"] == "subagent"


@when("I capture an intent with each of the five owner values",
      target_fixture="owner_map")
def _all_five_owners(engine):
    owners = {"user", "agent", "subagent", "jules", "system"}
    result = {}
    for owner in sorted(owners):
        iid = engine.intent.capture(f"o-{owner}", "x", "x", owner=owner)
        engine.intent.confirm(iid)
        result[owner] = iid
    return result


@then("each intent's stored owner matches the value used to create it")
def _all_owners_match(engine, owner_map):
    rows = engine.memory.find("Intent")
    id_to_row = {r["id"]: r for r in rows}
    for owner, iid in owner_map.items():
        assert id_to_row[iid]["owner"] == owner


# ── owner via wire tool ──────────────────────────────────────────────────────

def _bootstrap_via_wire(engine, **kwargs):
    from fastmcp import Client
    mcp = engine.build_mcp(codemode=False)

    async def _go():
        async with Client(mcp) as c:
            r = await c.call_tool("intent_bootstrap", kwargs)
            sc = r.structured_content
            return sc.get("result", sc) if isinstance(sc, dict) else sc

    return asyncio.run(_go())


@when("I bootstrap an intent via the wire tool with no parent",
      target_fixture="bootstrap_root")
def _wire_root(engine):
    return _bootstrap_via_wire(engine,
                               purpose="p", deliverable="d", acceptance="a")


@then('the bootstrap response carries owner "user"')
def _wire_root_owner_user(bootstrap_root):
    assert bootstrap_root["owner"] == "user"


@when("I bootstrap a child intent via the wire tool under a root",
      target_fixture="bootstrap_child")
def _wire_child(engine):
    root = _bootstrap_via_wire(engine,
                               purpose="root", deliverable="x", acceptance="x")
    child = _bootstrap_via_wire(engine,
                                purpose="child", deliverable="x", acceptance="x",
                                parent_intent_id=root["intent_id"])
    return child


@then('the bootstrap response carries owner "agent"')
def _wire_child_owner_agent(bootstrap_child):
    assert bootstrap_child["owner"] == "agent"


@when('I bootstrap an intent via the wire tool with owner "jules"',
      target_fixture="bootstrap_jules")
def _wire_jules(engine):
    return _bootstrap_via_wire(engine,
                               purpose="p", deliverable="d", acceptance="a",
                               owner="jules")


@then('the bootstrap response carries owner "jules"')
def _wire_jules_owner(bootstrap_jules):
    assert bootstrap_jules["owner"] == "jules"


# ─────────────────────────────────────────────────────────────────────────────
# Path analysis (analyze.paths)
# ─────────────────────────────────────────────────────────────────────────────

def _call_paths(engine, iid, **kw):
    r, _ = engine.registry.invoke(
        engine.memory, iid, "analyze", "paths",
        agent_id="agent:test", **kw)
    return r


@given("a user root intent with a 6-deep sub-intent chain beneath it",
       target_fixture="deep_chain_root")
def _deep_chain(engine, confirmed_intent):
    root = engine.intent.capture_and_confirm("root", "x", "x", owner="user")
    prev = root
    for _ in range(6):
        prev = engine.intent.capture_and_confirm("level", "x", "x",
                                                 parent_intent_id=prev)
    return root


@when("I run analyze.paths", target_fixture="paths_result")
def _run_paths(engine, confirmed_intent, request):
    # Use a scope fixture if it was set; fall back to confirmed_intent as SERVES anchor
    root = request.node.funcargs.get("deep_chain_root") or \
           request.node.funcargs.get("shallow_chain_root") or \
           request.node.funcargs.get("many_invocations_root") or \
           request.node.funcargs.get("few_invocations_root") or \
           request.node.funcargs.get("repeated_verb_root")
    iid = root if root else confirmed_intent
    return _call_paths(engine, iid)


@then('finding IP001 is present with severity "info"')
def _ip001_present(paths_result):
    ip001 = [f for f in paths_result["findings"] if f["rule"] == "IP001"]
    assert ip001, "IP001 should fire"
    assert ip001[0]["severity"] == "info"


@then("the finding references the root intent")
def _ip001_references_root(paths_result, deep_chain_root):
    ip001 = [f for f in paths_result["findings"] if f["rule"] == "IP001"]
    assert any(deep_chain_root in f["file"] for f in ip001)


@then("finding IP001 is absent")
def _ip001_absent(paths_result):
    assert not [f for f in paths_result["findings"] if f["rule"] == "IP001"]


@given("a user root intent with only 2 levels beneath it",
       target_fixture="shallow_chain_root")
def _shallow_chain(engine, confirmed_intent):
    root = engine.intent.capture_and_confirm("root", "x", "x", owner="user")
    a = engine.intent.capture_and_confirm("a", "x", "x", parent_intent_id=root)
    engine.intent.capture_and_confirm("b", "x", "x", parent_intent_id=a)
    return root


@given("a user root intent with 14 Invocations serving it",
       target_fixture="many_invocations_root")
def _many_invocations(engine, confirmed_intent):
    root = engine.intent.capture_and_confirm("root", "x", "x", owner="user")
    for i in range(14):
        inv_id = engine.memory.record("Invocation", {
            "capability": "reflect", "verb": "note", "role": "act"})
        engine.memory.link(inv_id, root, "SERVES")
    return root


@then('finding IP002 is present with severity "warn"')
def _ip002_present(paths_result):
    ip002 = [f for f in paths_result["findings"] if f["rule"] == "IP002"]
    assert ip002, "IP002 should fire"
    assert ip002[0]["severity"] == "warn"


@then("finding IP002 is absent")
def _ip002_absent(paths_result):
    assert not [f for f in paths_result["findings"] if f["rule"] == "IP002"]


@given("a user root intent with 5 Invocations serving it",
       target_fixture="few_invocations_root")
def _few_invocations(engine, confirmed_intent):
    root = engine.intent.capture_and_confirm("root", "x", "x", owner="user")
    for i in range(5):
        inv_id = engine.memory.record("Invocation", {
            "capability": "x", "verb": "y", "role": "transform"})
        engine.memory.link(inv_id, root, "SERVES")
    return root


@given('a user root intent with 5 invocations of "analyze.quality" and 3 of "document.render"',
       target_fixture="repeated_verb_root")
def _repeated_verb(engine, confirmed_intent):
    root = engine.intent.capture_and_confirm("root", "x", "x", owner="user")
    for _ in range(5):
        inv = engine.memory.record("Invocation", {
            "capability": "analyze", "verb": "quality", "role": "transform"})
        engine.memory.link(inv, root, "SERVES")
    for _ in range(3):
        inv = engine.memory.record("Invocation", {
            "capability": "document", "verb": "render", "role": "transform"})
        engine.memory.link(inv, root, "SERVES")
    return root


@then('finding IP003 names "analyze.quality"')
def _ip003_names_aq(paths_result):
    ip003 = [f for f in paths_result["findings"] if f["rule"] == "IP003"]
    assert any("analyze.quality" in f["message"] for f in ip003)


@then('finding IP003 does not name "document.render"')
def _ip003_no_dr(paths_result):
    ip003 = [f for f in paths_result["findings"] if f["rule"] == "IP003"]
    assert not any("document.render" in f["message"] for f in ip003)


@given("5 user root intents each with a 6-deep chain",
       target_fixture="many_roots")
def _many_roots(engine, confirmed_intent):
    roots = []
    for _ in range(5):
        root = engine.intent.capture_and_confirm("r", "x", "x", owner="user")
        roots.append(root)
        prev = root
        for _ in range(6):
            prev = engine.intent.capture_and_confirm("l", "x", "x",
                                                     parent_intent_id=prev)
    return roots


@when("I run analyze.paths with max_paths 2", target_fixture="paths_max_2")
def _paths_max_2(engine, confirmed_intent, many_roots):
    use = engine.intent.capture_and_confirm("u", "x", "x")
    return _call_paths(engine, use, max_paths=2)


@then("at most 2 IP001 findings are returned")
def _max_2_ip001(paths_max_2):
    ip001 = [f for f in paths_max_2["findings"] if f["rule"] == "IP001"]
    assert len(ip001) <= 2


# ─────────────────────────────────────────────────────────────────────────────
# Substrate clarity gate (Spec 307 §Refinement — the gate lives on `confirm`)
# ─────────────────────────────────────────────────────────────────────────────


@given("a captured-and-confirmed intent", target_fixture="clar_iid")
def _clar_iid(engine):
    return engine.intent.capture_and_confirm(
        "ship a feature", "a working feature", "tests pass", owner="user")


@then("the intent node carries a clarity_score between 0 and 1")
def _records_clarity(engine, clar_iid):
    node = engine.memory.recall(clar_iid)
    assert "clarity_score" in node, "confirm did not record clarity_score"
    assert 0.0 <= float(node["clarity_score"]) <= 1.0


@given("a freshly captured shallow intent", target_fixture="shallow_iid")
def _shallow_iid(engine):
    # capture only (status draft) — a bare triple, no grounding/scope/acceptance.
    return engine.intent.capture("vague", "something", "done", owner="user")


@when("I confirm it requiring clarity", target_fixture="gate_outcome")
def _confirm_requiring_clarity(engine, shallow_iid):
    try:
        engine.intent.confirm(shallow_iid, require_clarity=True)
        return {"refused": False}
    except ValueError as e:
        return {"refused": True, "error": str(e)}


@then("the confirm is refused for low clarity")
def _confirm_refused(gate_outcome, engine, shallow_iid):
    assert gate_outcome["refused"], "shallow intent should not clear the gate"
    # still a draft — the gate did not confirm it
    assert engine.memory.recall(shallow_iid)["status"] == "draft"


@then("confirming it with an override token succeeds")
def _override_succeeds(engine, shallow_iid):
    engine.intent.confirm(shallow_iid, require_clarity=True,
                          override_token="forced-by-test")
    assert engine.memory.recall(shallow_iid)["status"] == "confirmed"


@then("the substrate clarity score equals discover clarity's score")
def _scores_agree(engine, clar_iid):
    from agency import _clarity
    substrate = _clarity.clarity_score(engine.memory, clar_iid)
    verb_res = _call(engine, clar_iid, "discover", "clarity", for_intent_id=clar_iid)
    assert abs(round(substrate, 3) - verb_res["score"]) < 1e-9, (
        f"divergent clarity sources: substrate={substrate} verb={verb_res['score']}")
