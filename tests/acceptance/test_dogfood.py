"""Acceptance — dogfood capability: graph-native ledgers, export/import,
amendment pipeline. Converted from:
  tests/test_dogfood_graph_native.py
  tests/test_dogfood_and_batch_note.py
  tests/test_dogfood_export.py
  tests/test_dogfood_import.py
  tests/test_dogfood_amendment_classifier.py

Dropped as implementation/structural (not observable behaviour):
  - test_collect_docstring_marks_deprecated — inspects __doc__ string content
    (internal method metadata, not a verb output)
  - test_dogfood_has_session_tracking_verbs — structural verb inventory
    (cap.verbs membership assertion)
  - test_export_verb_registered / test_import_verb_registered — structural
    (cap.verbs membership assertion)
  - test_codes_amendment_constants_are_defined — asserts internal Codes class
    constants, not verb return behaviour
"""
from __future__ import annotations

import json
import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine
from agency.skill import SkillRun

scenarios("features/dogfood.feature")


# ── helpers ──────────────────────────────────────────────────────────────────

def _call(engine, iid, cap, v, **kw):
    r, _ = engine.registry.invoke(engine.memory, iid, cap, v,
                                  agent_id="agent:test", **kw)
    return r


# ─────────────────────────────────────────────────────────────────────────────
# dogfood.note
# ─────────────────────────────────────────────────────────────────────────────

@when('I call dogfood.note with observation "dispatch hardcodes driver" and plan_slug "040-test"',
      target_fixture="note_result")
def _note(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "dogfood", "note",
                 observation="dispatch hardcodes driver",
                 plan_slug="040-test")


@then("the response contains a reflection_id")
def _note_has_rid(note_result):
    assert "reflection_id" in note_result and note_result["reflection_id"]


@then('the Reflection node in the graph has the plan_slug "040-test"')
def _note_plan_slug(engine, note_result):
    refs = engine.memory.find("Reflection")
    me = next(r for r in refs if r["id"] == note_result["reflection_id"])
    assert me["plan_slug"] == "040-test"


@then('the Reflection node has scope "observation"')
def _note_scope(engine, note_result):
    refs = engine.memory.find("Reflection")
    me = next(r for r in refs if r["id"] == note_result["reflection_id"])
    assert me["scope"] == "observation"


@when('I call dogfood.note with observation "some observation" and plan_slug "017-test"',
      target_fixture="note_serves_result")
def _note_serves(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "dogfood", "note",
                 observation="some observation",
                 plan_slug="017-test")


@then("a SERVES edge connects the Reflection to the intent")
def _serves_edge(engine, confirmed_intent, note_serves_result):
    rows = engine.memory.g.query(
        "MATCH (r:Reflection)-[:SERVES]->(i:Intent) "
        "WHERE r.id = $rid RETURN i",
        {"rid": note_serves_result["reflection_id"]})
    assert len(rows) == 1
    assert rows[0]["i"]["properties"]["id"] == confirmed_intent


# ─────────────────────────────────────────────────────────────────────────────
# dogfood.render
# ─────────────────────────────────────────────────────────────────────────────

@given('two observations noted under plan_slug "048-test"')
def _two_obs(engine, confirmed_intent):
    _call(engine, confirmed_intent, "dogfood", "note",
          observation="first observation about analyze.paths",
          plan_slug="048-test")
    _call(engine, confirmed_intent, "dogfood", "note",
          observation="second observation about IP002 threshold",
          plan_slug="048-test")


@when(parsers.parse('I render plan_slug "{slug}"'), target_fixture="render_result")
def _render(engine, confirmed_intent, slug):
    return _call(engine, confirmed_intent, "dogfood", "render", plan_slug=slug)


@then('the content contains "# DOGFOOD-NOTES"')
def _render_header(render_result):
    assert "# DOGFOOD-NOTES" in render_result["content"]


@then("the content contains both observation texts")
def _render_both_obs(render_result):
    assert "first observation about analyze.paths" in render_result["content"]
    assert "second observation about IP002 threshold" in render_result["content"]


@then("the content includes the plan_slug")
def _render_includes_slug(render_result):
    assert "999-nonexistent" in render_result["content"]


@then("the content indicates no observations yet")
def _render_none_yet(render_result):
    assert "none yet" in render_result["content"].lower()


@given('one observation under plan_slug "plan-A" and one under "plan-B"')
def _obs_ab(engine, confirmed_intent):
    _call(engine, confirmed_intent, "dogfood", "note",
          observation="plan A obs", plan_slug="plan-A")
    _call(engine, confirmed_intent, "dogfood", "note",
          observation="plan B obs", plan_slug="plan-B")


@then("the content contains the plan-A observation")
def _render_a_obs(render_result):
    assert "plan A obs" in render_result["content"]


@then("the content does not contain the plan-B observation")
def _render_no_b(render_result):
    assert "plan B obs" not in render_result["content"]


@given('one observation under plan_slug "pure-test"')
def _one_obs_pure(engine, confirmed_intent):
    _call(engine, confirmed_intent, "dogfood", "note",
          observation="x", plan_slug="pure-test")


@then("the Reflection count in the graph is unchanged")
def _render_pure_no_write(engine):
    # count AFTER the render step runs
    after = len(list(engine.memory.find("Reflection")))
    assert after == 1  # just the one seeded above


@given('30 large observations under plan_slug "big-plan"')
def _big_plan(engine, confirmed_intent):
    long_obs = "lorem ipsum dolor sit amet " * 40
    for _ in range(30):
        _call(engine, confirmed_intent, "dogfood", "note",
              observation=long_obs, plan_slug="big-plan")


@when('I render plan_slug "big-plan" with max_tokens 500',
      target_fixture="render_result")
def _render_big(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "dogfood", "render",
                 plan_slug="big-plan", max_tokens=500)


@then("the returned token count is within budget")
def _within_budget(render_result):
    assert render_result["tokens"] <= 700


@then("the response reports omitted observations")
def _omitted_reported(render_result):
    assert render_result["omitted"] > 0
    assert "omitted" in render_result["content"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# dogfood.collect
# ─────────────────────────────────────────────────────────────────────────────

_SAMPLE_NOTES = """# DOGFOOD-NOTES

Running record.

## 2026-05-30 — first dispatch

**Observation 1 — dispatch hardcodes require_plan_approval=False.**
I had to dispatch without the plan-approval gate.

Subsequent paragraph about something else.

**Observation 2 — provenance is a one-graph traversal.**
The moat is real even for tactical dispatches.

## 2026-05-30 (later) — codex review

**Dogfood lesson 5 (architectural):** the probe is a stop-gap for the watcher.
"""


@given("a plan tree with a DOGFOOD-NOTES.md containing 3 entries",
       target_fixture="plan_tree_3")
def _plan_tree_3(tmp_path):
    plan_root = tmp_path / "Plan"
    plan_subdir = plan_root / "012-some-spec"
    plan_subdir.mkdir(parents=True)
    (plan_subdir / "DOGFOOD-NOTES.md").write_text(_SAMPLE_NOTES)
    return plan_root, "012-some-spec"


@when("I collect from that plan tree", target_fixture="collect_result")
def _collect_tree(engine, confirmed_intent, plan_tree_3):
    plan_root, _ = plan_tree_3
    return _call(engine, confirmed_intent, "dogfood", "collect",
                 plan_dir=str(plan_root))


@then("the collect result count is 3")
def _collect_count_3(collect_result):
    assert collect_result["count"] == 3


@then("the plans list contains the plan subdirectory name")
def _collect_plans(collect_result, plan_tree_3):
    _, subdir = plan_tree_3
    assert subdir in collect_result["plans"]


@then("the texts list matches the observation texts")
def _collect_texts(collect_result):
    obs = collect_result["observations"]
    assert collect_result["texts"] == [o["text"] for o in obs]


@when("I collect from a non-existent directory", target_fixture="collect_result")
def _collect_missing(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "dogfood", "collect",
                 plan_dir="/nonexistent/path")


@then("the collect result count is 0")
def _collect_count_0(collect_result):
    assert collect_result["count"] == 0


@then("the warnings mention the missing directory")
def _collect_missing_warn(collect_result):
    assert any("not found" in w for w in collect_result["warnings"])


@given("a plan tree where one subdirectory has DOGFOOD-NOTES.md and one does not",
       target_fixture="plan_tree_mixed")
def _plan_tree_mixed(tmp_path):
    plan_root = tmp_path / "Plan"
    (plan_root / "001-no-notes").mkdir(parents=True)
    (plan_root / "002-with-notes").mkdir()
    (plan_root / "002-with-notes" / "DOGFOOD-NOTES.md").write_text(
        "**Observation 1 — x.** body."
    )
    return plan_root


@when("I collect from the mixed plan tree", target_fixture="collect_result")
def _collect_mixed(engine, confirmed_intent, plan_tree_mixed):
    return _call(engine, confirmed_intent, "dogfood", "collect",
                 plan_dir=str(plan_tree_mixed))


@then("only the subdirectory with the file appears in the plans list")
def _collect_mixed_plans(collect_result):
    assert collect_result["plans"] == ["002-with-notes"]


# ─────────────────────────────────────────────────────────────────────────────
# dogfood.export
# ─────────────────────────────────────────────────────────────────────────────

@when("I export the graph to a file", target_fixture="export_result")
def _export(engine, confirmed_intent, tmp_path):
    target = tmp_path / "export.json"
    r = _call(engine, confirmed_intent, "dogfood", "export", path=str(target))
    return r, target


@then("the file exists and parses as JSON")
def _export_json(export_result):
    _, target = export_result
    assert target.exists()
    json.loads(target.read_text())


@then('the JSON has keys "version", "nodes", and "edges"')
def _export_keys(export_result):
    _, target = export_result
    data = json.loads(target.read_text())
    assert "version" in data
    assert "nodes" in data and isinstance(data["nodes"], list)
    assert "edges" in data and isinstance(data["edges"], list)


@then('the response has "path", "nodes", "edges", and "bytes" fields')
def _export_shape(export_result):
    r, target = export_result
    assert r["path"] == str(target)
    assert isinstance(r["nodes"], int)
    assert isinstance(r["edges"], int)
    assert isinstance(r["bytes"], int)


@given('a noted observation "round-trip text" under plan_slug "rt"')
def _noted_rt(engine, confirmed_intent):
    _call(engine, confirmed_intent, "dogfood", "note",
          observation="round-trip text", plan_slug="rt")


@then('the exported JSON contains a Reflection node with text "round-trip text"')
def _export_has_reflection(export_result):
    _, target = export_result
    data = json.loads(target.read_text())
    reflections = [n for n in data["nodes"] if n.get("label") == "Reflection"]
    assert any(n["properties"].get("text") == "round-trip text"
               for n in reflections)


@given("a child intent under the confirmed intent", target_fixture="child_iid")
def _child_intent(engine, confirmed_intent):
    return engine.intent.capture_and_confirm("child", "x", "x",
                                             parent_intent_id=confirmed_intent)


@then("the exported JSON includes the child intent with its owner and parent_intent_id")
def _export_intent_fields(engine, confirmed_intent, child_iid, export_result):
    _, target = export_result
    data = json.loads(target.read_text())
    intents = [n for n in data["nodes"] if n.get("label") == "Intent"]
    child_node = next((i for i in intents if i["id"] == child_iid), None)
    assert child_node is not None
    assert child_node["properties"]["owner"] == "agent"
    assert child_node["properties"]["parent_intent_id"] == confirmed_intent


@given('a noted observation under plan_slug "edge-test"')
def _noted_edge(engine, confirmed_intent):
    _call(engine, confirmed_intent, "dogfood", "note",
          observation="x", plan_slug="edge-test")


@then("the exported edges include at least one of SERVES or OBSERVED_DURING")
def _export_edges(export_result):
    _, target = export_result
    data = json.loads(target.read_text())
    edge_types = {e.get("type") for e in data["edges"]}
    assert "OBSERVED_DURING" in edge_types or "SERVES" in edge_types


@given('a noted observation under plan_slug "purity"')
def _noted_purity(engine, confirmed_intent):
    _call(engine, confirmed_intent, "dogfood", "note",
          observation="x", plan_slug="purity")


@then("the Reflection count and Intent count are unchanged after export")
def _export_pure(engine, export_result):
    # export already ran; counts captured before in the Given step (1 Reflection)
    after_r = len(list(engine.memory.find("Reflection")))
    after_i = len(list(engine.memory.find("Intent")))
    assert after_r == 1   # one seeded Reflection
    assert after_i >= 1   # at least the bootstrap Intent


@when("I export the graph twice with no explicit path",
      target_fixture="two_export_results")
def _export_twice(engine, confirmed_intent, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".agency").mkdir()
    r1 = _call(engine, confirmed_intent, "dogfood", "export", path="")
    r2 = _call(engine, confirmed_intent, "dogfood", "export", path="")
    return r1, r2


@then("the two export paths differ")
def _two_paths_differ(two_export_results):
    r1, r2 = two_export_results
    assert r1["path"] != r2["path"]


# ─────────────────────────────────────────────────────────────────────────────
# dogfood.import
# ─────────────────────────────────────────────────────────────────────────────

def _do_export_then_import(engine, confirmed_intent, tmp_path):
    """Helper used by several import scenarios."""
    target = tmp_path / "export.json"
    _call(engine, confirmed_intent, "dogfood", "export", path=str(target))
    src_data = json.loads(target.read_text())
    src_ids = {n["id"] for n in src_data["nodes"]}

    fresh = Engine(tempfile.mktemp(suffix=".db"))
    fresh_iid = fresh.intent.capture_and_confirm("r", "x", "x", owner="user")
    import_r, _ = fresh.registry.invoke(
        fresh.memory, fresh_iid, "dogfood", "import",
        agent_id="agent:test", path=str(target))
    return import_r, fresh, src_ids, target, src_data


@when("I export then import into a fresh engine", target_fixture="export_import_bundle")
def _export_import(engine, confirmed_intent, tmp_path):
    return _do_export_then_import(engine, confirmed_intent, tmp_path)


@then('the import response has "imported_nodes", "imported_edges", and "version" fields')
def _import_shape(export_import_bundle):
    import_r, _, _, _, _ = export_import_bundle
    assert "imported_nodes" in import_r and isinstance(import_r["imported_nodes"], int)
    assert "imported_edges" in import_r and isinstance(import_r["imported_edges"], int)
    assert "version" in import_r


@then("at least one node is imported")
def _import_one_node(export_import_bundle):
    import_r, _, _, _, _ = export_import_bundle
    assert import_r["imported_nodes"] >= 1


@when("I import a JSON file with version 999", target_fixture="bad_version_path")
def _import_bad_version(tmp_path):
    target = tmp_path / "bad.json"
    target.write_text(json.dumps(
        {"version": 999, "generated_at": 0, "nodes": [], "edges": []}))
    return target


@then('a ValueError mentioning "version" is raised')
def _version_error(engine, confirmed_intent, bad_version_path):
    with pytest.raises(ValueError, match="version"):
        _call(engine, confirmed_intent, "dogfood", "import",
              path=str(bad_version_path))


@when("I import a non-existent file path", target_fixture="missing_file_path")
def _missing_file_path(tmp_path):
    return tmp_path / "does-not-exist.json"


@then("a FileNotFoundError is raised")
def _file_not_found(engine, confirmed_intent, missing_file_path):
    with pytest.raises(FileNotFoundError):
        _call(engine, confirmed_intent, "dogfood", "import",
              path=str(missing_file_path))


@then("every source node id is present in the fresh graph")
def _all_ids_present(export_import_bundle):
    _, fresh, src_ids, _, _ = export_import_bundle
    after_rows = fresh.memory.g.query("MATCH (n) RETURN n")
    after_ids = {r["n"].get("properties", {}).get("id") for r in after_rows}
    missing = src_ids - after_ids
    assert not missing, f"missing imported ids: {missing}"


@given('a noted observation "preserve me" under plan_slug "020-prop"')
def _noted_preserve(engine, confirmed_intent):
    _call(engine, confirmed_intent, "dogfood", "note",
          observation="preserve me", plan_slug="020-prop")


@then("the fresh graph contains a Reflection with text \"preserve me\" and the plan_slug \"020-prop\"")
def _preserved_reflection(export_import_bundle):
    _, fresh, _, _, _ = export_import_bundle
    reflections = fresh.memory.find("Reflection")
    matched = [r for r in reflections if r.get("text") == "preserve me"]
    assert matched
    assert matched[0].get("plan_slug") == "020-prop"


@then("the fresh graph contains SERVES or OBSERVED_DURING edges")
def _edges_recreated(export_import_bundle):
    _, fresh, _, _, _ = export_import_bundle
    erows = fresh.memory.g.query("MATCH (a)-[e]->(b) RETURN a, e, b")

    def _etype(r):
        e = r["e"]
        return (e.get("type") or e.get("rel_type") or e.get("relationship") or "")

    types = {_etype(r) for r in erows}
    assert "SERVES" in types or "OBSERVED_DURING" in types


@given("two noted observations for round-trip")
def _two_rt_obs(engine, confirmed_intent):
    _call(engine, confirmed_intent, "dogfood", "note",
          observation="rt-1", plan_slug="rt")
    _call(engine, confirmed_intent, "dogfood", "note",
          observation="rt-2", plan_slug="rt")


@when("I export, import into a fresh engine, then re-export",
      target_fixture="round_trip_ids")
def _round_trip(engine, confirmed_intent, tmp_path):
    first = tmp_path / "first.json"
    _call(engine, confirmed_intent, "dogfood", "export", path=str(first))
    src_ids = {n["id"] for n in json.loads(first.read_text())["nodes"]}

    fresh = Engine(tempfile.mktemp(suffix=".db"))
    fresh_iid = fresh.intent.capture_and_confirm("fresh", "x", "x", owner="user")
    fresh.registry.invoke(
        fresh.memory, fresh_iid, "dogfood", "import",
        agent_id="agent:test", path=str(first))
    second = tmp_path / "second.json"
    fresh.registry.invoke(
        fresh.memory, fresh_iid, "dogfood", "export",
        agent_id="agent:test", path=str(second))
    dst_ids = {n["id"] for n in json.loads(second.read_text())["nodes"]}
    return src_ids, dst_ids


@then("every original node id appears in the re-exported JSON")
def _round_trip_ids(round_trip_ids):
    src_ids, dst_ids = round_trip_ids
    missing = src_ids - dst_ids
    assert not missing, f"round-trip dropped node ids: {missing}"


@then("the fresh engine's next tick exceeds the maximum vfrom seen in the import")
def _clock_advanced(export_import_bundle, tmp_path):
    _, fresh, _, target, src_data = export_import_bundle
    max_tick = max(
        (n["properties"].get("vfrom", 0)
         for n in src_data["nodes"]
         if isinstance(n["properties"].get("vfrom"), int)),
        default=0
    )
    next_tick = fresh.memory._now()
    assert next_tick > max_tick


# ─────────────────────────────────────────────────────────────────────────────
# Stubs for amendment tests
# ─────────────────────────────────────────────────────────────────────────────

class _FakeCapableDriver:
    def __init__(self, parsed):
        self._parsed = parsed
        self.calls = []

    def backend(self):
        return "anthropic"

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        from agency._drivers._anthropic import Completion
        return Completion(
            text=json.dumps(self._parsed),
            stop_reason="end_turn",
            parsed=self._parsed,
            model="claude-test",
        )


class _NoBackend:
    def backend(self):
        return "none"


class _AngryDriver:
    def backend(self):
        return "anthropic"

    def complete(self, **_kwargs):
        raise RuntimeError("network: simulated outage")


def _seed_reflections(engine, iid):
    _call(engine, iid, "dogfood", "note",
          plan_slug="146-engine-output-prefix-discipline",
          observation="The agency_welcome response should add a "
                      "cache_control hint pointing at the prefix.")
    _call(engine, iid, "dogfood", "note",
          plan_slug="147-anthropic-driver-boundary",
          observation="Refine: typo in the boundary error mapping.")


def _get_seeded_refls(engine):
    rows = engine.memory.g.query(
        "MATCH (r:Reflection) WHERE r.scope = $scope RETURN r",
        {"scope": "observation"})
    return [r["r"]["properties"] for r in rows]


def _valid_payload(source_reflections=("r1", "r2"), spec_id="146",
                   rationale=("The reflections show a pattern that needs codifying "
                              "into the spec so downstream code derives from it.")):
    return {
        "spec_id": spec_id,
        "section": "Done When",
        "op": "add-done-when",
        "before": "- [ ] existing item",
        "after": "- [ ] new proposed item",
        "rationale": rationale,
        "source_reflections": list(source_reflections),
        "confidence": 0.7,
    }


# ─────────────────────────────────────────────────────────────────────────────
# dogfood.parse_amendment
# ─────────────────────────────────────────────────────────────────────────────

@when("I call parse_amendment with default args", target_fixture="amend_result")
def _parse_amend_default(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "dogfood", "parse_amendment",
                 scope="", limit=20)


@then("the proposals list is empty")
def _proposals_empty(amend_result):
    assert amend_result["proposals"] == []


@given("a proposal-shaped observation and a neutral observation recorded")
def _seed_proposal_and_neutral(engine, confirmed_intent):
    _call(engine, confirmed_intent, "dogfood", "note",
          plan_slug="146-engine-output-prefix-discipline",
          observation="The agency_welcome response should add a "
                      "cache_control hint pointing at the prefix.")
    _call(engine, confirmed_intent, "dogfood", "note",
          plan_slug="146-engine-output-prefix-discipline",
          observation="Just a neutral observation about timestamps.")


@then("at least one proposal is returned")
def _at_least_one_proposal(amend_result):
    assert len(amend_result["proposals"]) >= 1


@then("each proposal has the required ProposalPayload fields")
def _proposal_shape(amend_result):
    required = {"spec_id", "section", "op", "before", "after",
                "rationale", "source_reflections", "confidence"}
    for p in amend_result["proposals"]:
        assert required.issubset(p.keys()), f"missing keys: {required - p.keys()}"


@then("each proposal's source_reflections is non-empty")
def _source_non_empty(amend_result):
    for p in amend_result["proposals"]:
        assert len(p["source_reflections"]) >= 1


@then("each proposal's confidence is in [0, 1]")
def _confidence_range(amend_result):
    for p in amend_result["proposals"]:
        assert 0.0 <= p["confidence"] <= 1.0


@given("two neutral observations recorded")
def _neutral_obs(engine, confirmed_intent):
    _call(engine, confirmed_intent, "dogfood", "note",
          plan_slug="146-engine-output-prefix-discipline",
          observation="Spec ships fine. No changes needed.")
    _call(engine, confirmed_intent, "dogfood", "note",
          plan_slug="147-anthropic-driver-boundary",
          observation="The driver boundary works as expected today.")


@given('a proposal observation for plan "146" and one for plan "147"')
def _obs_146_147(engine, confirmed_intent):
    _call(engine, confirmed_intent, "dogfood", "note",
          plan_slug="146-engine-output-prefix-discipline",
          observation="Should add a cache_control hint for the prefix.")
    _call(engine, confirmed_intent, "dogfood", "note",
          plan_slug="147-anthropic-driver-boundary",
          observation="Should add a retry policy to the boundary.")


@when('I call parse_amendment scoped to "146"', target_fixture="amend_result")
def _parse_amend_146(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "dogfood", "parse_amendment",
                 scope="146", limit=20)


@then('the proposals only reference spec_id "146"')
def _only_146(amend_result):
    spec_ids = {p["spec_id"] for p in amend_result["proposals"]}
    assert "146" in spec_ids


@then('spec_id "147" is absent')
def _no_147(amend_result):
    spec_ids = {p["spec_id"] for p in amend_result["proposals"]}
    assert "147" not in spec_ids


@given("5 proposal-shaped observations each referencing a different spec")
def _five_proposals(engine, confirmed_intent):
    for i in range(5):
        _call(engine, confirmed_intent, "dogfood", "note",
              plan_slug=f"15{i}-some-spec",
              observation=f"Spec 15{i} should add a typed error code.")


@when("I call parse_amendment with limit 2", target_fixture="amend_result")
def _parse_amend_limit_2(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "dogfood", "parse_amendment",
                 scope="", limit=2)


@then("at most 2 proposals are returned")
def _at_most_2(amend_result):
    assert len(amend_result["proposals"]) <= 2


@given("two seeded reflections and a capable Anthropic driver stub",
       target_fixture="capable_stub")
def _seed_capable(engine, confirmed_intent):
    _seed_reflections(engine, confirmed_intent)
    refls = _get_seeded_refls(engine)
    rid = refls[0].get("id") or ""
    spec_id = refls[0].get("plan_slug", "").split("-", 1)[0]
    fake_parsed = {"proposals": [{
        "reflection_id": rid,
        "spec_id": spec_id,
        "section": "Done When",
        "op": "add-done-when",
        "after": "driver-derived proposal",
        "rationale": ("LLM classifier promoted this reflection into a "
                      "concrete amendment over the keyword path (Spec 150 Slice 2)."),
        "confidence": 0.92,
    }]}
    stub = _FakeCapableDriver(parsed=fake_parsed)
    engine.drivers.register("anthropic", stub)
    return stub


@then('the response classifier is "llm"')
def _classifier_llm(amend_result):
    assert amend_result.get("classifier") == "llm"


@then("the driver was called exactly once")
def _driver_called_once(capable_stub):
    assert len(capable_stub.calls) == 1


@given("two seeded reflections and a no-backend driver stub")
def _seed_no_backend(engine, confirmed_intent):
    _seed_reflections(engine, confirmed_intent)
    engine.drivers.register("anthropic", _NoBackend())


@then('the response classifier is "keyword"')
def _classifier_keyword(amend_result):
    assert amend_result.get("classifier") == "keyword"


@when("I call parse_amendment preferring delegation", target_fixture="amend_result")
def _parse_amend_delegate(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "dogfood", "parse_amendment",
                 scope="", limit=10, prefer_delegate=True)


@then('the response classifier is "llm-delegate"')
def _classifier_llm_delegate(amend_result):
    assert amend_result.get("classifier") == "llm-delegate"


@then('the response kind is "llm_delegate"')
def _kind_llm_delegate(amend_result):
    assert amend_result.get("kind") == "llm_delegate"


@then("the request envelope carries messages and output_schema")
def _envelope_shape(amend_result):
    req = amend_result.get("request") or {}
    assert "messages" in req and isinstance(req["messages"], list)
    assert "output_schema" in req


@given("two seeded reflections and a pre-built host_completion payload",
       target_fixture="host_payload")
def _seed_host_completion(engine, confirmed_intent):
    _seed_reflections(engine, confirmed_intent)
    refls = _get_seeded_refls(engine)
    rid = refls[0].get("id") or ""
    spec_id = refls[0].get("plan_slug", "").split("-", 1)[0]
    return {"text": "<host-text>",
            "parsed": {"proposals": [{
                "reflection_id": rid,
                "spec_id": spec_id,
                "section": "Open questions",
                "op": "add-open-q",
                "after": "Host-LLM proposal text",
                "rationale": ("Host-LLM classified this as an open question "
                              "(Spec 279 resume path verified through dogfood)."),
                "confidence": 0.85,
            }]}}


@when("I call parse_amendment with the host_completion payload",
      target_fixture="amend_result")
def _parse_amend_host(engine, confirmed_intent, host_payload):
    return _call(engine, confirmed_intent, "dogfood", "parse_amendment",
                 scope="", limit=10, host_completion=host_payload)


@then('the response classifier is "host"')
def _classifier_host(amend_result):
    assert amend_result.get("classifier") == "host"


@given("two seeded reflections and a driver stub returning a ghost reflection id")
def _seed_ghost_driver(engine, confirmed_intent):
    _seed_reflections(engine, confirmed_intent)
    fake_parsed = {"proposals": [{
        "reflection_id": "ghost-id-does-not-exist",
        "spec_id": "146",
        "section": "Done When",
        "op": "add-done-when",
        "after": "Hallucinated proposal",
        "rationale": ("This is the hallucination defense test — the "
                      "classifier must drop proposals citing unknown ids."),
        "confidence": 0.5,
    }]}
    engine.drivers.register("anthropic", _FakeCapableDriver(parsed=fake_parsed))


@when("I call parse_amendment with use_llm false", target_fixture="amend_result")
def _parse_amend_no_llm(engine, confirmed_intent, capable_stub):
    return _call(engine, confirmed_intent, "dogfood", "parse_amendment",
                 scope="", limit=10, use_llm=False)


@then("the driver was not called")
def _driver_not_called(capable_stub):
    assert capable_stub.calls == []


@given("two seeded reflections and a driver stub that raises on complete")
def _seed_angry_driver(engine, confirmed_intent):
    _seed_reflections(engine, confirmed_intent)
    engine.drivers.register("anthropic", _AngryDriver())


@given('two seeded reflections and a host_completion with op "delete-everything"',
       target_fixture="host_payload")
def _seed_bad_op(engine, confirmed_intent):
    _seed_reflections(engine, confirmed_intent)
    refls = _get_seeded_refls(engine)
    rid = refls[0].get("id") or ""
    spec_id = refls[0].get("plan_slug", "").split("-", 1)[0]
    return {"text": "<host-text>",
            "parsed": {"proposals": [{
                "reflection_id": rid, "spec_id": spec_id,
                "section": "Done When", "op": "delete-everything",
                "after": "bad", "rationale": "x" * 50, "confidence": 0.9,
            }]}}


@given('two seeded reflections and a host_completion with section "Random Made Up Section"',
       target_fixture="host_payload")
def _seed_bad_section(engine, confirmed_intent):
    _seed_reflections(engine, confirmed_intent)
    refls = _get_seeded_refls(engine)
    rid = refls[0].get("id") or ""
    spec_id = refls[0].get("plan_slug", "").split("-", 1)[0]
    return {"text": "<host-text>",
            "parsed": {"proposals": [{
                "reflection_id": rid, "spec_id": spec_id,
                "section": "Random Made Up Section", "op": "add-done-when",
                "after": "x",
                "rationale": "Rationale long enough to satisfy the 40-char floor for validation.",
                "confidence": 0.9,
            }]}}


@given("two seeded reflections and a host_completion with confidence 5.0",
       target_fixture="host_payload")
def _seed_bad_confidence(engine, confirmed_intent):
    _seed_reflections(engine, confirmed_intent)
    refls = _get_seeded_refls(engine)
    rid = refls[0].get("id") or ""
    spec_id = refls[0].get("plan_slug", "").split("-", 1)[0]
    return {"text": "<host-text>",
            "parsed": {"proposals": [{
                "reflection_id": rid, "spec_id": spec_id,
                "section": "Done When", "op": "add-done-when",
                "after": "x",
                "rationale": "Rationale long enough to satisfy the 40-char floor for validation.",
                "confidence": 5.0,
            }]}}


@given("two seeded reflections and a host_completion with a rationale shorter than 40 chars",
       target_fixture="host_payload")
def _seed_short_rationale(engine, confirmed_intent):
    _seed_reflections(engine, confirmed_intent)
    refls = _get_seeded_refls(engine)
    rid = refls[0].get("id") or ""
    spec_id = refls[0].get("plan_slug", "").split("-", 1)[0]
    return {"text": "<host-text>",
            "parsed": {"proposals": [{
                "reflection_id": rid, "spec_id": spec_id,
                "section": "Done When", "op": "add-done-when",
                "after": "x", "rationale": "too short", "confidence": 0.5,
            }]}}


@given('two seeded reflections and a driver stub returning spec_id "999" for a "146" reflection')
def _seed_spec_mismatch(engine, confirmed_intent):
    _seed_reflections(engine, confirmed_intent)
    refls = _get_seeded_refls(engine)
    refl_146 = next(r for r in refls if r.get("plan_slug", "").startswith("146"))
    rid = refl_146.get("id") or ""
    fake_parsed = {"proposals": [{
        "reflection_id": rid, "spec_id": "999",
        "section": "Done When", "op": "add-done-when",
        "after": "mismatch",
        "rationale": ("Even with a valid reflection_id, a spec_id that "
                      "doesn't match the reflection's plan_slug must be dropped."),
        "confidence": 0.8,
    }]}
    engine.drivers.register("anthropic", _FakeCapableDriver(parsed=fake_parsed))


@given('two seeded reflections and a driver stub returning an empty spec_id for a "146" reflection')
def _seed_empty_spec_id(engine, confirmed_intent):
    _seed_reflections(engine, confirmed_intent)
    refls = _get_seeded_refls(engine)
    refl_146 = next(r for r in refls if r.get("plan_slug", "").startswith("146"))
    rid = refl_146.get("id") or ""
    fake_parsed = {"proposals": [{
        "reflection_id": rid, "spec_id": "",
        "section": "Done When", "op": "add-done-when",
        "after": "derived spec_id",
        "rationale": ("The verb derives spec_id from the cited "
                      "reflection's plan_slug when the model omits it."),
        "confidence": 0.75,
    }]}
    engine.drivers.register("anthropic", _FakeCapableDriver(parsed=fake_parsed))


@then("the proposal's spec_id is \"146\"")
def _derived_spec_id(amend_result):
    assert len(amend_result["proposals"]) == 1
    assert amend_result["proposals"][0]["spec_id"] == "146"


# ─────────────────────────────────────────────────────────────────────────────
# dogfood.apply_amendment
# ─────────────────────────────────────────────────────────────────────────────

@when("I call apply_amendment in dry-run mode with a valid payload",
      target_fixture="apply_result")
def _apply_dry_run(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "dogfood", "apply_amendment",
                 payload=_valid_payload(), dry_run=True)


@then('the response contains a "diff" field with "---" and "+++" markers')
def _diff_present(apply_result):
    diff = apply_result["diff"]
    assert "---" in diff and "+++" in diff


@then('no "written_path" is returned')
def _no_written_path(apply_result):
    assert "written_path" not in apply_result or not apply_result["written_path"]


@given("two cited Reflection nodes", target_fixture="two_reflections")
def _two_reflections(engine, confirmed_intent):
    r1 = _call(engine, confirmed_intent, "dogfood", "note",
               plan_slug="146-engine-output-prefix-discipline",
               observation="Should add a cache hint")["reflection_id"]
    r2 = _call(engine, confirmed_intent, "dogfood", "note",
               plan_slug="146-engine-output-prefix-discipline",
               observation="Should add a budget cap")["reflection_id"]
    return r1, r2


@when("I call apply_amendment citing those reflections in dry-run mode",
      target_fixture="apply_prov_result")
def _apply_provenance(engine, confirmed_intent, two_reflections):
    r1, r2 = two_reflections
    r = _call(engine, confirmed_intent, "dogfood", "apply_amendment",
              payload=_valid_payload(source_reflections=[r1, r2]),
              dry_run=True)
    return r, r1, r2


@then('an Artefact of kind "amendment-proposal" is recorded')
def _artefact_recorded(engine, apply_prov_result):
    r, _, _ = apply_prov_result
    assert "artefact_id" in r and r["artefact_id"]
    artefacts = engine.memory.find("Artefact")
    art = next(a for a in artefacts if a["id"] == r["artefact_id"])
    assert art["kind"] == "amendment-proposal"


@then("PRODUCES_FROM edges connect the Artefact to each cited Reflection")
def _produces_from_edges(engine, apply_prov_result):
    r, r1, r2 = apply_prov_result
    sourced = set()
    for rid in (r1, r2):
        edges = engine.memory.g.query(
            "MATCH (a)-[e:PRODUCES_FROM]->(rf) "
            "WHERE a.id = $art AND rf.id = $rid RETURN e",
            {"art": r["artefact_id"], "rid": rid})
        if edges:
            sourced.add(rid)
    assert sourced == {r1, r2}


@when('I call apply_amendment with spec_id "9999" in dry-run mode')
def _noop_bad_spec(engine, confirmed_intent):
    pass  # assertion happens in the Then step


@then('an exception containing "AMENDMENT_BAD_SPEC" is raised')
def _bad_spec_error(engine, confirmed_intent):
    with pytest.raises(Exception) as excinfo:
        _call(engine, confirmed_intent, "dogfood", "apply_amendment",
              payload=_valid_payload(spec_id="9999"), dry_run=True)
    assert ("AMENDMENT_BAD_SPEC" in str(excinfo.value) or
            "amendment_bad_spec" in str(excinfo.value))


@when("I call apply_amendment with empty source_reflections in dry-run mode")
def _noop_no_source(engine, confirmed_intent):
    pass


@then('an exception containing "AMENDMENT_NO_SOURCE" is raised')
def _no_source_error(engine, confirmed_intent):
    with pytest.raises(Exception) as excinfo:
        _call(engine, confirmed_intent, "dogfood", "apply_amendment",
              payload=_valid_payload(source_reflections=[]), dry_run=True)
    assert ("AMENDMENT_NO_SOURCE" in str(excinfo.value) or
            "amendment_no_source" in str(excinfo.value))


@when("I call apply_amendment with short rationale in dry-run mode")
def _noop_vague(engine, confirmed_intent):
    pass


@then('an exception containing "AMENDMENT_VAGUE" is raised')
def _vague_error(engine, confirmed_intent):
    with pytest.raises(Exception) as excinfo:
        _call(engine, confirmed_intent, "dogfood", "apply_amendment",
              payload=_valid_payload(rationale="too short"), dry_run=True)
    assert ("AMENDMENT_VAGUE" in str(excinfo.value) or
            "amendment_vague" in str(excinfo.value))


@when("I call apply_amendment with dry_run false and a wrong confirm_token")
def _noop_wrong_token(engine, confirmed_intent):
    pass


@then('an exception mentioning "confirm_token" or "amendment_unconfirmed" is raised')
def _wrong_token_error(engine, confirmed_intent, monkeypatch, tmp_path):
    from agency.capabilities.dogfood.clusters import amendment as amod
    spec = tmp_path / "Plan" / "146-engine-output-prefix-discipline" / "spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text("# Spec 146\n\n## Done When\n\n- [x] existing\n", encoding="utf-8")
    monkeypatch.setattr(amod, "_resolve_spec_path",
                        lambda sid: str(spec) if sid == "146" else None)
    with pytest.raises(Exception) as excinfo:
        _call(engine, confirmed_intent, "dogfood", "apply_amendment",
              payload=_valid_payload(), dry_run=False,
              confirm_token="wrong-token")
    msg = str(excinfo.value).lower()
    assert "confirm_token" in msg or "amendment_unconfirmed" in msg


# ─────────────────────────────────────────────────────────────────────────────
# reflect.batch_note
# ─────────────────────────────────────────────────────────────────────────────

@when("I call reflect.batch_note with two texts", target_fixture="batch_result")
def _batch_two(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "reflect", "batch_note",
                 scope="observation",
                 texts=["dispatch raced the gate", "ssl flakiness blocks status"])


@then("the batch response count is 2")
def _batch_count_2(batch_result):
    assert batch_result["count"] == 2


@then("2 Reflection nodes exist in the graph")
def _batch_2_nodes(engine, batch_result):
    rows = engine.memory.g.query(
        "MATCH (r:Reflection) WHERE r.scope = $sc RETURN r",
        {"sc": "observation"})
    assert len(rows) == 2


@when("I call reflect.batch_note with one real text one empty string and one None",
      target_fixture="batch_skip_result")
def _batch_skip(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "reflect", "batch_note",
                 scope="observation",
                 texts=["one real entry", "", None])


@then("the batch response count is 1")
def _batch_count_1(batch_skip_result):
    assert batch_skip_result["count"] == 1


@when("I call reflect.batch_note with an invalid scope")
def _noop_batch_bad_scope(engine, confirmed_intent):
    pass


@then('a ValueError mentioning "scope" is raised')
def _batch_scope_error(engine, confirmed_intent):
    with pytest.raises(ValueError, match="scope"):
        _call(engine, confirmed_intent, "reflect", "batch_note",
              scope="dogfood", texts=["x"])


# ─────────────────────────────────────────────────────────────────────────────
# jules-self-improvement skill
# ─────────────────────────────────────────────────────────────────────────────

@given("a plan tree with two DOGFOOD-NOTES.md observations",
       target_fixture="self_improve_plan_tree")
def _self_improve_tree(tmp_path):
    plan_root = tmp_path / "Plan"
    plan_subdir = plan_root / "999-fixture"
    plan_subdir.mkdir(parents=True)
    (plan_subdir / "DOGFOOD-NOTES.md").write_text(
        "**Observation 1 — alpha.** alpha body.\n\n"
        "**Observation 2 — beta.** beta body.\n"
    )
    return plan_root


@when("I walk the jules-self-improvement skill through both phases")
def _walk_self_improve(engine, confirmed_intent, self_improve_plan_tree):
    plan_root = self_improve_plan_tree
    sk = engine.ontology.skill("jules-self-improvement")
    run = SkillRun(engine.memory, confirmed_intent, sk, registry=engine.registry)
    res = run.submit({"plan_dir": str(plan_root)})
    assert res["status"] == "working"
    collection = _call(engine, confirmed_intent, "dogfood", "collect",
                       plan_dir=str(plan_root))
    run.submit({"scope": "observation", "texts": collection["texts"]})


@then("both observation texts appear as Reflection nodes in the graph")
def _both_obs_in_graph(engine):
    rows = engine.memory.g.query(
        "MATCH (r:Reflection) WHERE r.scope = $sc RETURN r",
        {"sc": "observation"})
    texts = [r["r"]["properties"]["text"] for r in rows]
    assert any("alpha body" in t for t in texts)
    assert any("beta body" in t for t in texts)


# ─────────────────────────────────────────────────────────────────────────────
# dogfood.apply_amendment — live-write (Spec 150, closes Goal 6)
# ─────────────────────────────────────────────────────────────────────────────

@given("a temp spec file with a Done-When section", target_fixture="temp_spec")
def _temp_spec(tmp_path, monkeypatch):
    from agency.capabilities.dogfood.clusters import amendment as amod
    spec = tmp_path / "Plan" / "987-x" / "spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "# Spec 987\n\n## Done-When\n\n- [x] existing item\n\n## Next steps\n\nmore\n",
        encoding="utf-8")
    monkeypatch.setattr(amod, "_resolve_spec_path",
                        lambda sid: str(spec) if sid == "987" else None)
    return spec


@when("I apply a live amendment with the matching confirm_token",
      target_fixture="live_result")
def _apply_live(engine, confirmed_intent, temp_spec):
    from agency.capabilities.dogfood.clusters.amendment import _payload_hash
    rid = _call(engine, confirmed_intent, "dogfood", "note",
                plan_slug="987-x",
                observation="Should add a budget cap")["reflection_id"]
    payload = {
        "spec_id": "987", "section": "Done When", "op": "add-done-when",
        "before": "", "after": "- [ ] new folded item",
        "rationale": ("The reflection shows a pattern that needs codifying "
                      "into the spec text so downstream derives from it."),
        "source_reflections": [rid], "confidence": 0.7,
    }
    token = _payload_hash(payload)
    return _call(engine, confirmed_intent, "dogfood", "apply_amendment",
                 payload=payload, dry_run=False, confirm_token=token)


@then("the spec file gains the new Done-When bullet")
def _spec_gained_bullet(temp_spec):
    body = temp_spec.read_text(encoding="utf-8")
    assert "- [ ] new folded item" in body, body
    # appended INSIDE the Done-When section (before the next heading)
    assert body.index("new folded item") < body.index("## Next steps"), body


@then("the response carries a written_path")
def _carries_written_path(live_result):
    assert live_result.get("written_path", "").endswith("spec.md"), live_result


# pure section-surgery invariants (the decidable core; rule 8 — assert relations)

def test_apply_amendment_to_text_appends_bullet_in_section():
    from agency.capabilities.dogfood.clusters.amendment import apply_amendment_to_text
    text = "# S\n\n## Done-When\n\n- [x] a\n\n## Next\n"
    out = apply_amendment_to_text(text, section="Done When",
                                  op="add-done-when", after="b")
    assert "- [ ] b" in out
    assert out.index("- [x] a") < out.index("- [ ] b") < out.index("## Next")


def test_apply_amendment_to_text_missing_section_raises():
    from agency.capabilities.dogfood.clusters.amendment import apply_amendment_to_text
    with pytest.raises(ValueError, match="amendment_no_section"):
        apply_amendment_to_text("# S\n\n## Other\n", section="Done When",
                                op="add-done-when", after="b")


def test_apply_amendment_to_text_edit_replaces_target_line():
    from agency.capabilities.dogfood.clusters.amendment import apply_amendment_to_text
    text = "## Done-When\n\n- [ ] old line\n\n## End\n"
    out = apply_amendment_to_text(text, section="Done When", op="edit-done-when",
                                  before="old line", after="- [x] new line")
    assert "new line" in out and "old line" not in out


def test_apply_amendment_to_text_no_fuse_when_section_lacks_trailing_newline():
    """Blocking bug (self-review #1): a section at EOF whose last line has no
    trailing newline must NOT fuse the new bullet onto it."""
    from agency.capabilities.dogfood.clusters.amendment import apply_amendment_to_text
    text = "# S\n\n## Done When\n- [x] a"            # no trailing newline
    out = apply_amendment_to_text(text, section="Done When",
                                  op="add-done-when", after="x")
    lines = out.splitlines()
    assert "- [x] a" in lines, out                    # original bullet intact
    assert "- [ ] x" in lines, out                    # new bullet on its own line
    assert "- [x] a- [ ] x" not in out, out           # not fused


def test_apply_amendment_to_text_multiline_after_stays_within_the_bullet():
    """Blocking bug (self-review #2): a multi-line `after` must not leave a bare
    non-bullet line at the list margin."""
    from agency.capabilities.dogfood.clusters.amendment import apply_amendment_to_text
    text = "## Done When\n\n- [x] a\n\n## End\n"
    out = apply_amendment_to_text(text, section="Done When",
                                  op="add-done-when", after="line1\nline2")
    section = out.split("## End")[0]
    for ln in section.splitlines():
        if "line2" in ln:
            assert ln.startswith(" "), f"continuation not indented: {ln!r}"
    # line1 carries the checkbox bullet
    assert any(ln.strip().startswith("- [ ] line1") for ln in section.splitlines()), out


# ─────────────────────────────────────────────────────────────────────────────
# dogfood spec lifecycle verbs
# ─────────────────────────────────────────────────────────────────────────────

@when(parsers.parse('I call spec_status for spec "{spec_id}"'),
      target_fixture="spec_status_result")
def _call_spec_status(engine, confirmed_intent, spec_id):
    return _call(engine, confirmed_intent, "dogfood", "spec_status",
                 spec_id=spec_id)


@then(parsers.parse('the status result shows spec_id "{spec_id}" on disk'))
def _status_on_disk(spec_status_result, spec_id):
    assert spec_status_result.get("spec_id") == spec_id.zfill(3), spec_status_result
    assert spec_status_result.get("on_disk") is True, spec_status_result


@then(parsers.parse('the status field is "{expected}"'))
def _status_field(spec_status_result, expected):
    assert spec_status_result.get("status") == expected, spec_status_result


@then(parsers.parse('the status result shows spec_id "{spec_id}" as shipped'))
def _status_shipped(spec_status_result, spec_id):
    assert spec_status_result.get("spec_id") == spec_id.zfill(3), spec_status_result
    assert spec_status_result.get("status") == "shipped", spec_status_result


@then("on_disk is false")
def _not_on_disk(spec_status_result):
    assert spec_status_result.get("on_disk") is False, spec_status_result


@then(parsers.parse('the status result shows status "{expected}"'))
def _status_unknown(spec_status_result, expected):
    assert spec_status_result.get("status") == expected, spec_status_result


@when("I call specs with no filter", target_fixture="specs_result")
def _call_specs(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "dogfood", "specs")


@then("the specs list has more than 100 entries")
def _specs_over_100(specs_result):
    assert specs_result.get("count", 0) > 100, specs_result


@then("every entry has spec_id slug and status fields")
def _specs_shape(specs_result):
    for entry in specs_result.get("specs", []):
        assert "spec_id" in entry and "slug" in entry and "status" in entry, entry


@when(parsers.parse('I call spec_refs for spec "{spec_id}"'),
      target_fixture="spec_refs_result")
def _call_spec_refs(engine, confirmed_intent, spec_id):
    return _call(engine, confirmed_intent, "dogfood", "spec_refs",
                 spec_id=spec_id)


@then("the refs list is non-empty")
def _refs_nonempty(spec_refs_result):
    assert spec_refs_result.get("count", 0) > 0, spec_refs_result


@then("every ref has file line and text fields")
def _refs_shape(spec_refs_result):
    for ref in spec_refs_result.get("refs", []):
        assert "file" in ref and "line" in ref and "text" in ref, ref
