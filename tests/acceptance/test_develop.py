"""Acceptance — develop capability: scaffolding, linting, authoring discipline
walk, discipline cues for intent methods. Converted from:
  tests/test_develop_authoring.py
  tests/test_develop_intent_cues.py

Dropped as implementation/structural (not observable behaviour):
  - test_no_dangling_cue — inspects internal verb list (cap.verbs) to check
    cue resolution; the cued-verb-invokes scenario covers the observable
    consequence instead
  - test_lint_consumer_contract_search_finds_under_budget — tests MCP
    _list_tools() internal method directly (async unit-test of internal
    engine wiring, not a verb output)
  - test_lint_role_tag_transform_with_network_imports_flags (parametrised
    over httpx/subprocess) — already covered by the requests case; one
    representative scenario suffices for the observable rule-fires behaviour
  - test_lint_render_slice_first_sentence_cleaves_on_first_sentence_helper
    — imports and calls _first_sentence internal helper directly
  - test_lint_render_slice_legacy_body_drift_flags — calls parse_slices
    internal helper directly, not a verb output
  - test_phase_2_scaffold_invokes_develop_scaffold_capability_via_skillrun —
    duplicate of the observable "phase 2 creates the scaffold file" scenario
  - test_phase_4_lint_invokes_plugin_lint_capability_via_skillrun — the
    skill_walk advancing-phase assertion overlaps with the authoring-walk
    end-to-end scenario
  - test_hard_gate_phase_6_blocks_until_reflection_recorded — covered by the
    "phase 6 blocks without confirmation" scenario
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
import textwrap

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.capability import CapabilityBase
from conftest import invoke

scenarios("features/develop.feature")


# ── capability source fixtures ───────────────────────────────────────────────

SCAFFOLDED_CLEAN = textwrap.dedent('''\
    # agency-scaffold: v1
    """clean — a one-line scaffolded capability with one compliant verb."""
    from agency.capability import CapabilityBase, verb
    from agency.ontology import OntologyExtension


    class CleanCapability(CapabilityBase):
        name = "clean"
        home = "capability"
        ontology = OntologyExtension()

        @verb(role="transform")
        def ping(self) -> dict:
            """Return a sentinel for liveness checks.

            Inputs: (none).
            Returns: {result: "pong"}.
            chain_next: (terminal).
            """
            return {"result": "pong"}
    ''')


SCAFFOLDED_BROKEN = textwrap.dedent('''\
    # agency-scaffold: v1
    """broken — has the scaffold marker but the verb violates the contract."""
    from agency.capability import CapabilityBase, verb
    from agency.ontology import OntologyExtension


    class BrokenCapability(CapabilityBase):
        name = "broken"
        home = "capability"
        ontology = OntologyExtension()

        @verb(role="transform")
        def do_it(self) -> dict:
            "no markers; first sentence is fine but the docstring is bare."
            return {"result": 1}
    ''')


LEGACY_BROKEN = textwrap.dedent('''\
    """legacy — NO scaffold marker; same violations as SCAFFOLDED_BROKEN."""
    from agency.capability import CapabilityBase, verb
    from agency.ontology import OntologyExtension


    class LegacyCapability(CapabilityBase):
        name = "legacy"
        home = "capability"
        ontology = OntologyExtension()

        @verb(role="transform")
        def do_it(self) -> dict:
            "no markers; legacy capability that predates the contract."
            return {"result": 1}
    ''')

LEGACY_NET = textwrap.dedent('''\
    """transform-role verb that imports requests — role_tag violation."""
    import requests  # noqa: F401
    from agency.capability import CapabilityBase, verb
    from agency.ontology import OntologyExtension


    class NetCapability(CapabilityBase):
        name = "net"
        home = "capability"
        ontology = OntologyExtension()

        @verb(role="transform")
        def fetch(self, url: str) -> dict:
            """Fetch a URL.

            Inputs: url (str).
            Returns: {result: <body>}.
            chain_next: (terminal).
            """
            return {"result": "fake"}
    ''')

EMPTY_DOC = textwrap.dedent('''\
    # agency-scaffold: v1
    from agency.capability import CapabilityBase, verb
    from agency.ontology import OntologyExtension

    class EmptyBriefCapability(CapabilityBase):
        name = "empty-brief"
        home = "capability"
        ontology = OntologyExtension()

        @verb(role="transform")
        def ping(self) -> dict:
            ""
            return {"result": 1}
    ''')


def _load_cap_from_source(src: str, tmp_path, name: str):
    p = tmp_path / f"{name}.py"
    p.write_text(src)
    spec = importlib.util.spec_from_file_location(f"_lint_test_{name}", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    for v in vars(mod).values():
        import inspect as _i
        if _i.isclass(v) and issubclass(v, CapabilityBase) and v is not CapabilityBase:
            return v.as_capability(), str(p)
    raise RuntimeError(f"no Capability found in source")


def _kinds_fired(result):
    return ({v["kind"] for v in result["violations"]}
            | {w["kind"] for w in result["warnings"]})


# ─────────────────────────────────────────────────────────────────────────────
# develop.scaffold_capability
# ─────────────────────────────────────────────────────────────────────────────

@when('I scaffold a capability named "mycap" with kind "light"',
      target_fixture="scaffold_light")
def _scaffold_light(tmp_path):
    from agency.capabilities.develop import scaffold_capability
    return scaffold_capability("mycap", kind="light", base_dir=str(tmp_path)), tmp_path


@then('a file named "mycap.py" is created in the output directory')
def _light_file_exists(scaffold_light):
    _, tmp_path = scaffold_light
    assert (tmp_path / "mycap.py").is_file()


@when('I scaffold a capability named "midcap" with kind "medium"',
      target_fixture="scaffold_medium")
def _scaffold_medium(tmp_path):
    from agency.capabilities.develop import scaffold_capability
    return scaffold_capability("midcap", kind="medium", base_dir=str(tmp_path)), tmp_path


@then('the output file contains "nodes="')
def _medium_nodes(scaffold_medium):
    _, tmp_path = scaffold_medium
    body = (tmp_path / "midcap.py").read_text()
    assert "nodes=" in body


@when('I scaffold a capability named "bigcap" with kind "heavy"',
      target_fixture="scaffold_heavy")
def _scaffold_heavy(tmp_path):
    from agency.capabilities.develop import scaffold_capability
    return scaffold_capability("bigcap", kind="heavy", base_dir=str(tmp_path)), tmp_path


@then('a folder named "bigcap" is created')
def _heavy_folder(scaffold_heavy):
    _, tmp_path = scaffold_heavy
    assert (tmp_path / "bigcap").is_dir()


@then('the folder contains "__init__.py"')
def _heavy_init(scaffold_heavy):
    _, tmp_path = scaffold_heavy
    assert (tmp_path / "bigcap" / "__init__.py").is_file()


@then('the folder contains "bigcap.py"')
def _heavy_main(scaffold_heavy):
    _, tmp_path = scaffold_heavy
    assert (tmp_path / "bigcap" / "bigcap.py").is_file()


@when('I scaffold capabilities with kind "light" and kind "medium"',
      target_fixture="scaffold_marker_pair")
def _scaffold_marker_pair(tmp_path):
    from agency.capabilities.develop import scaffold_capability
    scaffold_capability("m_light", kind="light", base_dir=str(tmp_path))
    scaffold_capability("m_medium", kind="medium", base_dir=str(tmp_path))
    return tmp_path


@then('each output file\'s first non-blank line is "# agency-scaffold: v1"')
def _marker_present(scaffold_marker_pair):
    tmp_path = scaffold_marker_pair
    for name in ("m_light", "m_medium"):
        first = (tmp_path / f"{name}.py").read_text().lstrip().split("\n", 1)[0]
        assert first == "# agency-scaffold: v1", \
            f"{name}: got {first!r}"


@when('I scaffold a capability named "acap" with kind "light"',
      target_fixture="scaffold_artefact")
def _scaffold_artefact(tmp_path):
    from agency.capabilities.develop import scaffold_capability
    return scaffold_capability("acap", kind="light", base_dir=str(tmp_path))


@then('the response has a "result" field with the file path')
def _artefact_result(scaffold_artefact):
    assert "result" in scaffold_artefact


@then('the response "artefact" has kind "capability-scaffold"')
def _artefact_kind(scaffold_artefact):
    assert scaffold_artefact["artefact"]["kind"] == "capability-scaffold"


@then("the artefact scaffold_version is 1")
def _artefact_version(scaffold_artefact):
    assert scaffold_artefact["artefact"].get("scaffold_version") == 1


@when('I scaffold a capability named "ucap" with kind "WRONG"',
      target_fixture="scaffold_unknown")
def _scaffold_unknown(tmp_path):
    from agency.capabilities.develop import scaffold_capability
    return scaffold_capability("ucap", kind="WRONG", base_dir=str(tmp_path))


@then('the scaffold response status is "input-required"')
def _input_required(scaffold_unknown):
    assert scaffold_unknown.get("status") == "input-required"


@then('"kind" is listed in resume_with')
def _kind_in_resume(scaffold_unknown):
    assert "kind" in (scaffold_unknown.get("resume_with") or [])


# ─────────────────────────────────────────────────────────────────────────────
# plugin.lint_capability
# ─────────────────────────────────────────────────────────────────────────────

@when("I lint a broken scaffolded capability", target_fixture="lint_result")
def _lint_broken(tmp_path):
    from agency.capabilities.plugin import lint_capability
    cap, _ = _load_cap_from_source(SCAFFOLDED_BROKEN, tmp_path, "b")
    return lint_capability(cap)


@then('the lint mode is "block"')
def _mode_block(lint_result):
    assert lint_result["mode"] == "block"


@then("lint ok is false")
def _ok_false(lint_result):
    assert lint_result["ok"] is False


@then('at least one "structural" violation is reported')
def _structural_violation(lint_result):
    kinds = {v["kind"] for v in lint_result["violations"]}
    assert "structural" in kinds


@when("I lint a clean scaffolded capability", target_fixture="lint_result")
def _lint_clean(tmp_path):
    from agency.capabilities.plugin import lint_capability
    cap, _ = _load_cap_from_source(SCAFFOLDED_CLEAN, tmp_path, "clean")
    return lint_capability(cap)


@then("lint ok is true")
def _ok_true(lint_result):
    assert lint_result["ok"] is True


@then("no violations are reported")
def _no_violations(lint_result):
    assert lint_result["violations"] == []


@when("I lint a legacy capability with violations", target_fixture="lint_result")
def _lint_legacy(tmp_path):
    from agency.capabilities.plugin import lint_capability
    cap, _ = _load_cap_from_source(LEGACY_BROKEN, tmp_path, "legacy")
    return lint_capability(cap)


@then('the lint mode is "warn"')
def _mode_warn(lint_result):
    assert lint_result["mode"] == "warn"


@then("the warnings list is non-empty")
def _warnings_non_empty(lint_result):
    assert lint_result["warnings"]


@then("the violations list is empty")
def _violations_empty(lint_result):
    assert lint_result["violations"] == []


@when("I lint a transform capability that imports requests", target_fixture="lint_result")
def _lint_net(tmp_path):
    from agency.capabilities.plugin import lint_capability
    cap, _ = _load_cap_from_source(LEGACY_NET, tmp_path, "net_r")
    return lint_capability(cap)


@then('"role_tag" appears in the lint findings')
def _role_tag_fired(lint_result):
    assert "role_tag" in _kinds_fired(lint_result)


@when("I lint a scaffolded capability with an empty verb docstring",
      target_fixture="lint_result")
def _lint_empty_doc(tmp_path):
    from agency.capabilities.plugin import lint_capability
    cap, _ = _load_cap_from_source(EMPTY_DOC, tmp_path, "empty_doc")
    return lint_capability(cap)


@then('"render_slice" appears in the lint findings')
def _render_slice_fired(lint_result):
    assert "render_slice" in _kinds_fired(lint_result)


@when("I lint any capability", target_fixture="lint_result")
def _lint_any(tmp_path):
    from agency.capabilities.plugin import lint_capability
    cap, _ = _load_cap_from_source(SCAFFOLDED_CLEAN, tmp_path, "any_cap")
    return lint_capability(cap)


@then('the lint result has keys "ok", "violations", "warnings", "skipped", and "mode"')
def _lint_keys(lint_result):
    assert set(lint_result.keys()) >= {"ok", "violations", "warnings", "skipped", "mode"}


@when('I scaffold a capability named "zcap" with kind "light"',
      target_fixture="scaffold_zcap")
def _scaffold_zcap(tmp_path):
    from agency.capabilities.develop import scaffold_capability
    scaffold_capability("zcap", kind="light", base_dir=str(tmp_path))
    return tmp_path


@when("I lint the scaffolded capability", target_fixture="lint_result")
def _lint_zcap(scaffold_zcap):
    from agency.capabilities.plugin import lint_capability
    tmp_path = scaffold_zcap
    cap, _ = _load_cap_from_source(
        (tmp_path / "zcap.py").read_text(), tmp_path, "zcap_loader")
    return lint_capability(cap)


# ─────────────────────────────────────────────────────────────────────────────
# authoring-capabilities discipline walk (Spec 024)
# ─────────────────────────────────────────────────────────────────────────────

def _call(engine, iid, cap, v, **kw):
    r, _ = engine.registry.invoke(engine.memory, iid, cap, v,
                                  agent_id="agent:test", **kw)
    return r


def _drive_authoring_discipline(engine, iid, tmp_path):
    """Walk authoring-capabilities through SkillRun. Returns (run, cap_name, rid)."""
    from agency.skill import SkillRun
    from agency.capabilities.develop import scaffold_capability

    schema = engine.registry.get("develop").ontology.skills["authoring-capabilities"]
    run = SkillRun(engine.memory, iid, schema, registry=engine.registry)

    run.submit(outputs={"read_doctrine": "yes"})

    cap_name = "e2ecap"
    run.submit(outputs={"name": cap_name, "kind": "light", "base_dir": str(tmp_path)})
    run.submit(outputs={"verbs_written": "yes"})

    scaffold_path = tmp_path / f"{cap_name}.py"
    scaffold_capability(cap_name, kind="light", base_dir=str(tmp_path))
    cap, _ = _load_cap_from_source(scaffold_path.read_text(), tmp_path, "e2e_loader")
    engine.registry.register(cap)

    run.submit(outputs={"name": cap_name})
    run.submit(outputs={"budget_ok": "yes"})

    record_result, _ = engine.registry.invoke(
        engine.memory, iid, "develop", "record_authoring_outcome",
        name=cap_name, kind="light")
    rid = record_result["result"] if isinstance(record_result, dict) else record_result

    run.submit(outputs={"reflection_recorded": rid}, confirmed=True)
    return run, cap_name, rid


@when("I walk the authoring-capabilities discipline to completion",
      target_fixture="authoring_walk")
def _authoring_walk(engine, confirmed_intent, tmp_path):
    return _drive_authoring_discipline(engine, confirmed_intent, tmp_path)


@then("a Reflection node exists in the graph")
def _reflection_exists(engine, authoring_walk):
    _, _, rid = authoring_walk
    reflections = engine.memory.find("Reflection")
    assert any(r["id"] == rid for r in reflections)


@then("its text mentions both the capability name and the discipline name")
def _reflection_text(engine, authoring_walk):
    _, cap_name, rid = authoring_walk
    rec = engine.memory.recall(rid)
    text = rec.get("text", "")
    assert cap_name in text and "authoring-capabilities" in text


@when("I walk the authoring-capabilities discipline through phase 2",
      target_fixture="phase2_walk")
def _walk_phase2(engine, confirmed_intent, tmp_path):
    from agency.skill import SkillRun
    schema = engine.registry.get("develop").ontology.skills["authoring-capabilities"]
    run = SkillRun(engine.memory, confirmed_intent, schema, registry=engine.registry)
    run.submit(outputs={"read_doctrine": "yes"})
    run.submit(outputs={"name": "p2cap", "kind": "light", "base_dir": str(tmp_path)})
    return tmp_path


@then("the scaffolded file exists on disk")
def _phase2_file_exists(phase2_walk):
    tmp_path = phase2_walk
    assert (tmp_path / "p2cap.py").is_file()


@when("I walk to phase 6 of the authoring-capabilities discipline without confirming",
      target_fixture="phase6_result")
def _walk_to_phase6(engine, confirmed_intent, tmp_path):
    from agency.skill import SkillRun
    from agency.capabilities.develop import scaffold_capability

    schema = engine.registry.get("develop").ontology.skills["authoring-capabilities"]
    run = SkillRun(engine.memory, confirmed_intent, schema, registry=engine.registry)

    cap_name = "hgcap"
    scaffold_capability(cap_name, kind="light", base_dir=str(tmp_path))
    cap, _ = _load_cap_from_source(
        (tmp_path / f"{cap_name}.py").read_text(), tmp_path, "hg_loader")
    engine.registry.register(cap)

    run.submit(outputs={"read_doctrine": "yes"})
    run.submit(outputs={"name": cap_name, "kind": "light", "base_dir": str(tmp_path)})
    run.submit(outputs={"verbs_written": "yes"})
    run.submit(outputs={"name": cap_name})
    run.submit(outputs={"budget_ok": "yes"})
    # Phase 6 without confirmed=True
    return run.submit(outputs={"reflection_recorded": "rid_placeholder"})


@then('the response status is "input-required"')
def _phase6_blocked(phase6_result):
    assert phase6_result.get("status") == "input-required"


# ─────────────────────────────────────────────────────────────────────────────
# Discipline cues for intent methods (Spec 092 G4)
# ─────────────────────────────────────────────────────────────────────────────

def _cued_verbs(engine, skill):
    sk = engine.registry.get("develop").ontology.skills[skill]
    return {v for p in sk["phases"] for v in p.get("verbs", [])}


@when('I inspect the cued verbs in the "plan" discipline',
      target_fixture="plan_cues")
def _plan_cues(engine, confirmed_intent):
    return _cued_verbs(engine, "plan")


@then('"intent.premortem" is in the cue set')
def _premortem_cued(plan_cues):
    assert "intent.premortem" in plan_cues


@when('I inspect the cued verbs in the "spec-panel" discipline',
      target_fixture="spec_panel_cues")
def _spec_panel_cues(engine, confirmed_intent):
    return _cued_verbs(engine, "spec-panel")


@then('"intent.steelman" is in the cue set')
def _steelman_cued(spec_panel_cues):
    assert "intent.steelman" in spec_panel_cues


@when('I inspect the cued verbs in the "brainstorm" discipline',
      target_fixture="brainstorm_cues")
def _brainstorm_cues(engine, confirmed_intent):
    return _cued_verbs(engine, "brainstorm")


@then('"intent.tradeoffs" is in the cue set')
def _tradeoffs_cued(brainstorm_cues):
    assert "intent.tradeoffs" in brainstorm_cues


@when("I invoke the premortem method cued by the plan discipline",
      target_fixture="premortem_cue_result")
def _invoke_premortem_cue(engine, confirmed_intent):
    res, _ = engine.registry.invoke(engine.memory, confirmed_intent,
                                    "intent", "premortem")
    return res["result"] if isinstance(res, dict) and "result" in res else res


@then('the result method is "premortem"')
def _premortem_method(premortem_cue_result):
    assert premortem_cue_result["method"] == "premortem"


@then("the result has at least one step")
def _at_least_one_step(premortem_cue_result):
    assert premortem_cue_result["steps"]


@when('I walk each of the "plan", "spec-panel", and "brainstorm" disciplines',
      target_fixture="discipline_walk_results")
def _walk_disciplines(engine, confirmed_intent):
    results = {}
    for skill in ("plan", "spec-panel", "brainstorm"):
        res, _ = engine.registry.invoke(
            engine.memory, confirmed_intent, "develop", "skill_walk",
            name=skill, inputs={})
        out = res["result"] if isinstance(res, dict) and "result" in res else res
        results[skill] = out
    return results


@then("each walk returns a valid terminal status")
def _valid_terminal_status(discipline_walk_results):
    valid = {"completed", "input-required", "blocked", "failed"}
    for skill, out in discipline_walk_results.items():
        assert out.get("status") in valid, \
            f"{skill}: unexpected status {out.get('status')!r}"


# ── develop.index — ported indexer (Spec 292) ─────────────────────────────────

@when("I call develop.index on the agency repo", target_fixture="dev_index_result")
def _develop_index(engine, confirmed_intent):
    import os
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    r, _ = engine.registry.invoke(engine.memory, confirmed_intent, "develop", "index",
                                  agent_id="agent:test", path=repo, apply=False)
    return r


@then("the develop index result carries an index_id")
def _dev_index_id(dev_index_result):
    assert dev_index_result.get("index_id", "").startswith("repoindex:")


@then("the develop index token count is positive")
def _dev_index_tokens(dev_index_result):
    assert dev_index_result.get("tokens", 0) > 0
