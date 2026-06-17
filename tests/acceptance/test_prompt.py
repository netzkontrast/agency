"""Acceptance — prompt capability (Spec 109/127/129).

Converted from tests/test_prompt_capability.py, tests/test_dynamic_prompt_assembly.py,
tests/test_dramatica_prompt_fragments.py.

Dropped as implementation/structural (not behaviour):
- test_prompt_capability_slice1_founding_verbs_present: surface-count inventory, not behaviour
- test_prompt_capability_registers_two_walkable_skills: surface inventory
- test_prompt_capability_lint_clean_in_block_mode: internal lint check
- test_dossier_author_skill_is_five_phased: skill shape inspection (structural)
- test_prompt_engineering_pass_skill_is_six_phased: skill shape inspection (structural)
- test_dossier_author_skill_walks_through_finalize: SkillRun internal walker
- test_research_intent_deliverable_enum_bites_at_record_time: internal record API
- test_unimplemented_sections_flag_their_dependency: implementation detail of placeholder body
- test_section_budget_truncates_long_sections: internal budget math / placeholder size assumptions
- test_total_budget_drops_lowest_priority: internal budget math / placeholder size assumptions
- test_rendered_prompt_is_markdown_with_sections: structural string shape inspection
- test_register_fragment_round_trip: tests overlay write path (needs monkeypatch + tmp_path)
- test_register_fragment_overlay_overrides_vendored: same
- test_register_fragment_unknown_slug: same
- test_fragment_verbs_registered: surface inventory
- test_verb_registered: surface inventory
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import invoke
from agency.engine import Engine

scenarios("features/prompt.feature")


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


@pytest.fixture
def confirmed_intent(engine):
    iid = engine.intent.capture("prompt acceptance", "behaviour", "verified")
    engine.intent.confirm(iid)
    return iid


def _call(engine, confirmed_intent, verb, **kw):
    return invoke(engine, confirmed_intent, "prompt", verb, **kw)


# ── shared Given steps ────────────────────────────────────────────────────────

@given("a fresh agency engine in code-mode", target_fixture="engine")
def _given_engine(engine):
    return engine


@given("a confirmed intent", target_fixture="confirmed_intent")
def _given_intent(confirmed_intent):
    return confirmed_intent


# ── intent_capture ────────────────────────────────────────────────────────────

@when(parsers.parse('I capture a research intent with topic "{topic}" and deliverable "{deliverable}"'),
      target_fixture="capture_result")
def _capture(engine, confirmed_intent, topic, deliverable):
    res, inv = _call(engine, confirmed_intent, "intent_capture",
                     seed_query="test query", topic=topic, deliverable=deliverable,
                     success_criteria="primary cites")
    return res, inv


@then("a ResearchIntent node is created")
def _ri_created(capture_result):
    res, inv = capture_result
    assert res is not None
    assert res["intent_id"].startswith("researchintent:")


@then("it SERVES the confirmed intent")
def _ri_serves(engine, confirmed_intent, capture_result):
    res, inv = capture_result
    rows = engine.memory.g.query(
        "MATCH (r)-[:SERVES]->(i) WHERE r.id=$rid AND i.id=$iid RETURN r",
        {"rid": res["intent_id"], "iid": confirmed_intent})
    assert rows


@when(parsers.parse('I capture a research intent with deliverable "{deliverable}"'),
      target_fixture="capture_bad")
def _capture_bad(engine, confirmed_intent, deliverable):
    res, inv = _call(engine, confirmed_intent, "intent_capture",
                     seed_query="x", topic="t", deliverable=deliverable)
    return res, inv


@then(parsers.parse('the captured intent is null with error "{code}"'))
def _capture_error(engine, capture_bad, code):
    res, inv = capture_bad
    assert res is None
    assert code in engine.memory.recall(inv).get("error", "")


# ── catalog_list ──────────────────────────────────────────────────────────────

@when("I list the prompt module catalogue", target_fixture="catalogue")
def _catalogue(engine, confirmed_intent):
    res, _ = _call(engine, confirmed_intent, "catalog_list")
    return res


@then(parsers.parse("the catalogue has {n:d} modules across categories A, B, C"))
def _catalogue_shape(catalogue, n):
    assert catalogue["count"] == n
    cats = {m["category"] for m in catalogue["modules"]}
    assert cats == {"A", "B", "C"}


@when(parsers.parse('I list the prompt module catalogue filtered by category "{cat}"'),
      target_fixture="catalogue_filtered")
def _catalogue_filtered(engine, confirmed_intent, cat):
    res, inv = _call(engine, confirmed_intent, "catalog_list", category=cat)
    return res, inv


@then(parsers.parse('every returned module belongs to category "{cat}"'))
def _all_in_cat(catalogue_filtered, cat):
    res, inv = catalogue_filtered
    assert all(m["category"] == cat for m in res["modules"])


@then(parsers.parse('the catalogue list is null with error "{code}"'))
def _catalogue_error(engine, catalogue_filtered, code):
    res, inv = catalogue_filtered
    assert res is None
    assert code in engine.memory.recall(inv).get("error", "")


# ── brief_render ──────────────────────────────────────────────────────────────

@when('I render a brief from a captured intent with modules "M01,M03,M06"',
      target_fixture="brief_result")
def _render_brief(engine, confirmed_intent):
    ri, _ = _call(engine, confirmed_intent, "intent_capture",
                  seed_query="x", topic="modems", deliverable="dossier",
                  success_criteria="primary cites")
    br, _ = _call(engine, confirmed_intent, "brief_render",
                  research_intent_id=ri["intent_id"], module_ids="M01,M03,M06")
    return br, ri


@then('the brief artefact kind is "research-dossier"')
def _brief_kind(brief_result):
    br, ri = brief_result
    assert br["artefact"]["kind"] == "research-dossier"


@then("the brief body mentions the topic and the module ids")
def _brief_body(brief_result):
    br, ri = brief_result
    body = br["result"]
    assert "modems" in body
    assert "M01" in body and "M03" in body and "M06" in body


@then("a RENDERS_FROM edge links the brief to the research intent")
def _renders_from(engine, brief_result):
    br, ri = brief_result
    rows = engine.memory.g.query(
        "MATCH (b:ResearchBrief)-[:RENDERS_FROM]->(i:ResearchIntent) WHERE i.id=$iid RETURN b",
        {"iid": ri["intent_id"]})
    assert rows


@when("I render a brief for an unknown research intent id", target_fixture="brief_unknown")
def _render_unknown(engine, confirmed_intent):
    res, inv = _call(engine, confirmed_intent, "brief_render",
                     research_intent_id="bogus:does-not-exist")
    return res, inv


@then(parsers.parse('the brief render is null with error "{code}"'))
def _brief_not_found(engine, brief_unknown, code):
    res, inv = brief_unknown
    assert res is None
    assert code in engine.memory.recall(inv).get("error", "")


# ── rendered brief helper ──────────────────────────────────────────────────────

@pytest.fixture
def rendered_brief(engine, confirmed_intent):
    ri, _ = invoke(engine, confirmed_intent, "prompt", "intent_capture",
                   seed_query="x", topic="t", deliverable="dossier")
    br, _ = invoke(engine, confirmed_intent, "prompt", "brief_render",
                   research_intent_id=ri["intent_id"])
    return br, ri


# ── brief_audit ───────────────────────────────────────────────────────────────

@when("I audit a rendered brief", target_fixture="audit_result")
def _audit_brief(engine, confirmed_intent, rendered_brief):
    br, ri = rendered_brief
    res, _ = _call(engine, confirmed_intent, "brief_audit",
                   brief_id=br["artefact"]["brief_id"])
    return res, br


@then("the audit result has a clarity_score and a status")
def _audit_shape(audit_result):
    res, br = audit_result
    assert "clarity_score" in res
    assert res["status"] in {"passed", "failed"}
    assert res["audit_id"].startswith("briefaudit:")


@then("an AUDITS edge links the audit to the brief")
def _audits_edge(engine, audit_result):
    res, br = audit_result
    rows = engine.memory.g.query(
        "MATCH (a)-[:AUDITS]->(b:ResearchBrief) WHERE b.id=$bid RETURN a",
        {"bid": br["artefact"]["brief_id"]})
    assert rows


# ── brief_finalize ────────────────────────────────────────────────────────────

@when("I finalize a rendered brief", target_fixture="finalize_result")
def _finalize_brief(engine, confirmed_intent, rendered_brief):
    br, ri = rendered_brief
    res, _ = _call(engine, confirmed_intent, "brief_finalize",
                   brief_id=br["artefact"]["brief_id"])
    return res


@then("the finalize result reports finalized true")
def _finalized(finalize_result):
    assert finalize_result["finalized"] is True


# ── engineer ──────────────────────────────────────────────────────────────────

@when(parsers.parse('I engineer a "{kind}" with normal context'),
      target_fixture="engineer_result")
def _engineer(engine, confirmed_intent, kind):
    res, inv = _call(engine, confirmed_intent, "engineer",
                     builder_kind=kind,
                     context="A phreaker dialing into BBS",
                     constraints="[under 100 words; period setting]")
    return res, inv


@then(parsers.parse('the artefact kind is "{kind}"'))
def _artefact_kind(engineer_result, kind):
    res, inv = engineer_result
    assert res["artefact"]["kind"] == kind


@then("the artefact reports a positive token count")
def _positive_tokens(engineer_result):
    res, inv = engineer_result
    assert res["artefact"]["approx_tokens"] > 0


@when(parsers.parse('I engineer a "{kind}" with a very tight max_tokens budget'),
      target_fixture="engineer_over")
def _engineer_over(engine, confirmed_intent, kind):
    res, inv = _call(engine, confirmed_intent, "engineer",
                     builder_kind=kind,
                     context="x " * 200,
                     constraints="y " * 200,
                     max_tokens=10)
    return res, inv


@then(parsers.parse('the engineer result is null with error "{code}"'))
def _engineer_null(engine, engineer_over, code):
    res, inv = engineer_over
    assert res is None
    assert code in engine.memory.recall(inv).get("error", "")


# ── prompt audit ──────────────────────────────────────────────────────────────

@when("I audit a prompt body with clear structure", target_fixture="audit_clear")
def _audit_clear_struct(engine, confirmed_intent):
    res, _ = _call(engine, confirmed_intent, "audit",
                   prompt_body="# Sample prompt\n[constraint A]\n[constraint B]\n")
    return res


@then("the audit reports a clarity_score and a status")
def _audit_report(audit_clear):
    assert "clarity_score" in audit_clear
    assert audit_clear["status"] in {"passed", "failed"}


@when("I audit a vague prompt body", target_fixture="vague_score")
def _audit_vague(engine, confirmed_intent):
    res, _ = _call(engine, confirmed_intent, "audit",
                   prompt_body="Maybe write something really kind of cool about modems.")
    return res["clarity_score"]


@when("I audit a clear prompt body", target_fixture="clear_score")
def _audit_clear2(engine, confirmed_intent):
    res, _ = _call(engine, confirmed_intent, "audit",
                   prompt_body="Write a poem [tight, sharp] about modems.")
    return res["clarity_score"]


@then("the vague prompt scores lower than the clear one")
def _vague_lower(vague_score, clear_score):
    assert vague_score < clear_score


# ── token_budget_gate ─────────────────────────────────────────────────────────

@when("I check the token budget gate with a short prompt and limit 100",
      target_fixture="tbg_pass")
def _tbg_short(engine, confirmed_intent):
    lc = engine.lifecycle.open(confirmed_intent)
    res, _ = _call(engine, confirmed_intent, "token_budget_gate",
                   lifecycle_id=lc, prompt_body="short prompt", max_tokens=100)
    return res, lc


@then("the token budget gate reports passed true")
def _tbg_passed(tbg_pass):
    res, lc = tbg_pass
    assert res["passed"] is True


@when("I check the token budget gate with a long prompt and limit 10",
      target_fixture="tbg_blocked")
def _tbg_long(engine, confirmed_intent):
    lc = engine.lifecycle.open(confirmed_intent)
    res, inv = _call(engine, confirmed_intent, "token_budget_gate",
                     lifecycle_id=lc, prompt_body="x " * 200, max_tokens=10)
    return res, lc


@then("the token budget gate reports blocked")
def _tbg_blocked_check(tbg_blocked):
    res, lc = tbg_blocked
    assert res is None


@then(parsers.parse('the lifecycle state is "{state}"'))
def _lifecycle_state(engine, tbg_blocked, state):
    res, lc = tbg_blocked
    assert engine.memory.recall(lc).get("state") == state


# ── audit_gate ────────────────────────────────────────────────────────────────

@when("I check the audit gate with a vague prompt and min_score 70",
      target_fixture="audit_gate_blocked")
def _audit_gate(engine, confirmed_intent):
    lc = engine.lifecycle.open(confirmed_intent)
    res, inv = _call(engine, confirmed_intent, "audit_gate",
                     lifecycle_id=lc,
                     prompt_body="Just maybe write something kind of like that.",
                     min_score=70)
    return res, lc


@then("the audit gate reports blocked")
def _audit_gate_check(audit_gate_blocked):
    res, lc = audit_gate_blocked
    assert res is None


# ── assemble_scene_brief ──────────────────────────────────────────────────────

@given("a scene is created in the graph", target_fixture="scene_id")
def _scene(engine, confirmed_intent):
    nv, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                   title="Test Novel", author="A. Author", genre="literary")
    ch, _ = invoke(engine, confirmed_intent, "novel", "create_chapter",
                   novel_id=nv["novel_id"], number=3, title="The Crossing")
    sc, _ = invoke(engine, confirmed_intent, "novel", "create_scene",
                   chapter_id=ch["chapter_id"], slug="bridge", pov="third-limited")
    return sc["scene_id"]


@when("I assemble a scene brief", target_fixture="brief")
def _assemble_brief(engine, confirmed_intent, scene_id):
    res, _ = invoke(engine, confirmed_intent, "prompt", "assemble_scene_brief",
                    scene_id=scene_id)
    return res


@then("the brief has keys prompt, sections, token_count, sources, brief_id")
def _brief_keys(brief):
    for k in ("prompt", "sections", "token_count", "sources", "brief_id"):
        assert k in brief, f"brief missing key {k}"


@then("the token count is positive")
def _positive_token_count(brief):
    assert brief["token_count"] > 0


@when(parsers.parse('I assemble a brief for scene "{scene_id_str}"'),
      target_fixture="brief_error")
def _assemble_unknown(engine, confirmed_intent, scene_id_str):
    res, _ = invoke(engine, confirmed_intent, "prompt", "assemble_scene_brief",
                    scene_id=scene_id_str)
    return res


@then(parsers.parse('the result error is "{error}"'))
def _result_error(brief_error, error):
    assert brief_error.get("error") == error


@when("I assemble a scene brief with generous budget", target_fixture="brief_full")
def _assemble_full(engine, confirmed_intent, scene_id):
    res, _ = invoke(engine, confirmed_intent, "prompt", "assemble_scene_brief",
                    scene_id=scene_id, max_tokens=10000, section_budget=2000)
    return res


@then("all seven expected sections are present")
def _seven_sections(brief_full):
    expected = {"storyform", "pov_card", "scene_cast", "world_rules",
                "continuity", "foreshadowing", "voice_constraints"}
    assert expected <= set(brief_full["sections"].keys())


@then('the pov_card section contains "third-limited"')
def _pov_card(brief):
    assert "third-limited" in brief["sections"]["pov_card"]


@then("the storyform section is non-empty")
def _storyform_nonempty(brief):
    assert brief["sections"]["storyform"]


@then(parsers.parse('the brief artefact is recorded with kind "{kind}"'))
def _brief_artefact_recorded(engine, brief, kind):
    node = engine.memory.g.get_node(brief["brief_id"])
    assert node is not None
    assert node["properties"]["kind"] == kind


@then("the brief artefact SERVES the confirmed intent")
def _brief_serves(engine, confirmed_intent, brief):
    rows = engine.memory.g.query(
        "MATCH (a:Artefact)-[:SERVES]->(i:Intent) WHERE a.id=$aid AND i.id=$iid RETURN a",
        {"aid": brief["brief_id"], "iid": confirmed_intent})
    assert len(rows) == 1


# ── Dramatica fragment verbs ──────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _reset_frag_cache():
    from agency.capabilities.prompt import _main as p
    p._load_fragments.cache_clear()
    yield
    p._load_fragments.cache_clear()


@when(parsers.parse('I look up fragment "{slug}"'), target_fixture="frag")
def _fragment(engine, confirmed_intent, slug):
    res, _ = invoke(engine, confirmed_intent, "prompt", "fragment", slug=slug)
    return res


@then("the fragment text is non-empty")
def _frag_text(frag):
    assert frag.get("text"), f"fragment text empty: {frag}"


@then(parsers.parse('the fragment canonical_id is "{cid}"'))
def _frag_cid(frag, cid):
    assert frag["canonical_id"] == cid


@then(parsers.parse('the fragment kind is "{kind}"'))
def _frag_kind(frag, kind):
    assert frag["kind"] == kind


@then("the fragment has a positive token count")
def _frag_tokens(frag):
    assert frag["tokens"] > 0


@then(parsers.parse('the fragment error is "{err}"'))
def _frag_error(frag, err):
    assert frag.get("error") == err


@when("I call fragments_for with a standard scope", target_fixture="frags_result")
def _frags_standard(engine, confirmed_intent):
    scope = {
        "throughline": "mc",
        "class_id": "class.universe",
        "concern_id": "type.past",
        "problem_id": "el.self-interest",
        "solution_id": "el.morality",
    }
    res, _ = invoke(engine, confirmed_intent, "prompt", "fragments_for", scope=scope)
    return res


@then("the result contains fragments for throughline.main and class.universe")
def _frags_contain_keys(frags_result):
    ids = [f["canonical_id"] for f in frags_result["fragments"]]
    assert "throughline.main" in ids
    assert "class.universe" in ids


@then("the total_tokens is positive")
def _frags_tokens(frags_result):
    assert frags_result["total_tokens"] > 0


@then("truncated_at is null")
def _frags_not_truncated(frags_result):
    assert frags_result["truncated_at"] is None


@when("I call fragments_for with a tight max_tokens budget", target_fixture="frags_tight")
def _frags_tight(engine, confirmed_intent):
    scope = {
        "throughline": "mc",
        "class_id": "class.universe",
        "concern_id": "type.past",
        "problem_id": "el.self-interest",
    }
    res, _ = invoke(engine, confirmed_intent, "prompt", "fragments_for",
                    scope=scope, max_tokens=120)
    return res


@then("the truncated_at field is set")
def _frags_truncated(frags_tight):
    assert frags_tight["truncated_at"] is not None


@then("the total tokens fit within the budget")
def _frags_within_budget(frags_tight):
    assert frags_tight["total_tokens"] <= 120


@when("I call fragments_for with an unknown class_id", target_fixture="frags_unknown")
def _frags_unknown(engine, confirmed_intent):
    scope = {"throughline": "mc", "class_id": "class.bogus"}
    res, _ = invoke(engine, confirmed_intent, "prompt", "fragments_for", scope=scope)
    return res


@then("the unknown slug appears in skipped_no_fragment")
def _skipped_unknown(frags_unknown):
    assert "class.bogus" in frags_unknown["skipped_no_fragment"]


# ── Prompt-framework library (Spec 304) ──────────────────────────────────────

@pytest.fixture(autouse=True)
def _reset_framework_cache():
    from agency.capabilities.prompt import _main as p
    from agency.capabilities.prompt.clusters import frameworks as fw
    saved = fw._DEFAULT_FW_OVERLAY_PATH
    p._load_frameworks.cache_clear()
    yield
    fw._DEFAULT_FW_OVERLAY_PATH = saved
    p._load_frameworks.cache_clear()


@when(parsers.parse('I look up framework "{slug}"'), target_fixture="fw")
def _framework(engine, confirmed_intent, slug):
    res, _ = invoke(engine, confirmed_intent, "prompt", "framework", slug=slug)
    return res


@then(parsers.parse('the framework name is "{name}"'))
def _fw_name(fw, name):
    assert fw["name"] == name


@then("the framework template is non-empty")
def _fw_template(fw):
    assert fw.get("template")


@then(parsers.parse('the framework intent_category is "{cat}"'))
def _fw_intent(fw, cat):
    assert fw["intent_category"] == cat


@then("the framework has a positive token count")
def _fw_tokens(fw):
    assert fw["tokens"] > 0


@then(parsers.parse('the framework error is "{err}"'))
def _fw_error(fw, err):
    assert fw.get("error") == err


@when("I list every framework intent category present", target_fixture="cat_coverage")
def _cat_coverage(engine, confirmed_intent):
    from agency.capabilities.prompt._main import _load_frameworks
    from agency.capabilities.prompt.ontology import INTENT_CATEGORY
    store = _load_frameworks()
    present = {e["intent_category"] for e in store.values()
               if e.get("audience", "user") == "user"}
    return present, INTENT_CATEGORY


@then("every user intent category has at least one framework")
def _every_cat_covered(cat_coverage):
    present, expected = cat_coverage
    # Derived from the live enum + JSON (rule 8) — no hardcoded count.
    assert expected <= present, f"uncovered: {expected - present}"


@when(parsers.parse('I list frameworks for intent "{intent}"'), target_fixture="ffor")
def _ffor(engine, confirmed_intent, intent):
    res, _ = invoke(engine, confirmed_intent, "prompt", "frameworks_for", intent=intent)
    return res


@then(parsers.parse('every returned framework belongs to intent "{intent}"'))
def _ffor_all(engine, confirmed_intent, ffor, intent):
    from agency.capabilities.prompt._main import _load_frameworks
    store = _load_frameworks()
    for f in ffor["frameworks"]:
        assert store[f["slug"]]["intent_category"] == intent


@then("the frameworks_for total_tokens is positive")
def _ffor_tokens(ffor):
    assert ffor["total_tokens"] > 0


@when(parsers.parse('I list frameworks for intent "{intent}" with a tight budget'),
      target_fixture="ffor_tight")
def _ffor_tight(engine, confirmed_intent, intent):
    res, _ = invoke(engine, confirmed_intent, "prompt", "frameworks_for",
                    intent=intent, max_tokens=40)
    return res


@then("the frameworks_for truncated_at field is set")
def _ffor_truncated(ffor_tight):
    assert ffor_tight["truncated_at"] is not None


@when(parsers.parse('I register a custom framework "{slug}" with a template'),
      target_fixture="reg_fw")
def _register_fw(engine, confirmed_intent, slug, tmp_path):
    overlay = str(tmp_path / "fw-overlay.yaml")
    res, _ = invoke(engine, confirmed_intent, "prompt", "register_framework",
                    slug=slug,
                    payload={"name": "My Framework", "intent_category": "create",
                             "template": "GOAL: [x]\nCONTEXT: [y]"},
                    overlay_path=overlay)
    # Point the loader at the same overlay for the subsequent lookup.
    from agency.capabilities.prompt import clusters
    clusters.frameworks._DEFAULT_FW_OVERLAY_PATH = overlay
    clusters.frameworks._load_frameworks.cache_clear()
    return res


@when(parsers.parse('I register a custom framework "{slug}" with no template'),
      target_fixture="fw")
def _register_fw_bad(engine, confirmed_intent, slug):
    res, _ = invoke(engine, confirmed_intent, "prompt", "register_framework",
                    slug=slug, payload={"name": "Bad"})
    return res


# ── Framework routing + render + evaluate (Spec 305) ──────────────────────────

@when(parsers.parse('I route the draft "{draft}"'), target_fixture="route")
def _route(engine, confirmed_intent, draft):
    res, _ = invoke(engine, confirmed_intent, "prompt", "route_framework", draft=draft)
    return res


@when(parsers.parse('I route the draft "{draft}" with intent hint "{hint}"'),
      target_fixture="route")
def _route_hint(engine, confirmed_intent, draft, hint):
    res, _ = invoke(engine, confirmed_intent, "prompt", "route_framework",
                    draft=draft, intent_hint=hint)
    return res


@then(parsers.parse('the routed intent is "{intent}"'))
def _routed_intent(route, intent):
    assert route["intent"] == intent


@then("the routed framework is present")
def _routed_fw(route):
    assert route["framework"] and route["framework"]["slug"]


@then("the route scaffold is non-empty")
def _route_scaffold(route):
    assert route["scaffold"]


@then("the route rationale is non-empty")
def _route_rationale(route):
    assert route["rationale"]


@then("the route returns at most two frameworks total")
def _route_efficient(route):
    total = (1 if route["framework"] else 0) + len(route["alts"])
    assert total <= 2


@then(parsers.parse('that is fewer than the frameworks_for candidate list for intent "{intent}"'))
def _route_fewer(engine, confirmed_intent, route, intent):
    cand, _ = invoke(engine, confirmed_intent, "prompt", "frameworks_for",
                     intent=intent, max_tokens=100000)
    total = (1 if route["framework"] else 0) + len(route["alts"])
    assert total < len(cand["frameworks"])


@then("a Recommendation node serves the intent")
def _route_recommendation(engine, confirmed_intent, route):
    rows = engine.memory.g.query(
        "MATCH (r:Recommendation)-[:SERVES]->(i) WHERE i.id=$iid RETURN r",
        {"iid": confirmed_intent})
    assert rows


@when("I render framework \"ape\" with action, purpose and expectation fields",
      target_fixture="rendered")
def _render_ape(engine, confirmed_intent):
    res, _ = invoke(engine, confirmed_intent, "prompt", "render",
                    framework_slug="ape",
                    fields={"action": "Summarize the quarterly report",
                            "purpose": "exec briefing",
                            "expectation": "three tight bullets"})
    return res


@then("the rendered body mentions the field values")
def _rendered_body(rendered):
    body = rendered["result"]
    assert "Summarize the quarterly report" in body
    assert "three tight bullets" in body


@then("a FILLS_FRAMEWORK edge links the instance to a PromptFramework node")
def _fills_edge(engine, rendered):
    iid = rendered["artefact"]["instance_id"]
    rows = engine.memory.g.query(
        "MATCH (i:PromptInstance)-[:FILLS_FRAMEWORK]->(f:PromptFramework) "
        "WHERE i.id=$iid RETURN f", {"iid": iid})
    assert rows and rows[0]["f"]["properties"]["slug"] == "ape"


@when("I render framework \"co-star\" with a huge field and a tight budget",
      target_fixture="render_over")
def _render_over(engine, confirmed_intent):
    res, inv = invoke(engine, confirmed_intent, "prompt", "render",
                      framework_slug="co-star",
                      fields={"context": "x " * 500}, max_tokens=10)
    return res, inv


@then(parsers.parse('the render result is null with error "{code}"'))
def _render_null(engine, render_over, code):
    res, inv = render_over
    assert res is None
    assert code in engine.memory.recall(inv).get("error", "")


@when(parsers.parse('I render framework "{slug}" with empty fields'),
      target_fixture="render_unknown")
def _render_unknown(engine, confirmed_intent, slug):
    res, _ = invoke(engine, confirmed_intent, "prompt", "render",
                    framework_slug=slug, fields={})
    return res


@then(parsers.parse('the render error is "{err}"'))
def _render_err(render_unknown, err):
    assert render_unknown.get("error") == err


@when("I evaluate a well-formed user prompt", target_fixture="evald")
def _evaluate_good(engine, confirmed_intent):
    res, _ = invoke(engine, confirmed_intent, "prompt", "evaluate",
                    prompt_body="Write a detailed 800-word blog post about "
                    "machine learning in healthcare for non-technical readers "
                    "in a friendly, professional tone.")
    return res


@then("the evaluation has five dimension scores")
def _eval_five(evald):
    assert set(evald["scores"]) == {
        "clarity", "specificity", "context", "completeness", "structure"}


@then("the evaluation has a status and an overall score")
def _eval_status(evald):
    assert evald["status"] in {"passed", "failed"}
    assert isinstance(evald["overall"], (int, float))


@when(parsers.parse('I evaluate with target "{target}"'), target_fixture="evald")
def _evaluate_target(engine, confirmed_intent, target):
    res, _ = invoke(engine, confirmed_intent, "prompt", "evaluate",
                    prompt_body="some body", target=target)
    return res


@then(parsers.parse('the evaluation error is "{err}"'))
def _eval_err(evald, err):
    assert evald.get("error") == err


@when("I evaluate a vague user prompt", target_fixture="vague_eval")
def _eval_vague(engine, confirmed_intent):
    res, _ = invoke(engine, confirmed_intent, "prompt", "evaluate",
                    prompt_body="maybe do something with that stuff")
    return res["overall"]


@when("I evaluate a clear user prompt", target_fixture="clear_eval")
def _eval_clear(engine, confirmed_intent):
    res, _ = invoke(engine, confirmed_intent, "prompt", "evaluate",
                    prompt_body="Write a 500-word report analyzing Q4 sales "
                    "data for the finance team, structured with sections.")
    return res["overall"]


@then("the vague overall is below the clear overall")
def _vague_below(vague_eval, clear_eval):
    assert vague_eval < clear_eval
