"""Acceptance — load_skill + skill_source (Spec 371 Slices 2-3).

A capability's v2 Skill DERIVES from its docstring SkillDoc (the back-compat
shim, owner=auto) unless the capability SHIPS a `skill.yaml` (the A6 authored
override, owner=capability). `skill_source` reads back WHERE the data came from.
"""
from __future__ import annotations

import textwrap

from pytest_bdd import parsers, scenarios, then, when

scenarios("features/skill_load.feature")


@when("I derive a v2 skill from a capability docstring", target_fixture="loaded")
def _derive_from_doc():
    from agency._skill_load import derive_skill_dict, load_skill
    from agency._skill_parse import parse_skill
    from agency.capability import SkillDoc

    doc = SkillDoc(
        description="Use when navigating code — symbols, calls, blast radius.",
        overview="codegraph is the pre-built symbol/call-graph index.",
        triggers=["a where-is-X question", "a blast-radius question"],
        canonical_example="codegraph explore 'parse_skill'",
        red_flags=["grepping when codegraph exists"],
    )
    derived = derive_skill_dict(doc, "code_graph")
    return {"dict": derived, "parsed": parse_skill(derived),
            "loaded": load_skill("code_graph", doc, capabilities_root="/nonexistent")}


@then('the derived skill parses clean with type "capability" and owner "auto"')
def _derived_clean(loaded):
    res = loaded["parsed"]
    assert res.ok, f"derived skill failed parse: {res.message}"
    assert res.value.type == "capability"
    assert res.value.owner == "auto"
    # the name is spec-legal (hyphens, no underscores — Spec 080)
    assert res.value.name == "code-graph"
    # load_skill with no skill.yaml takes the same derive path
    assert loaded["loaded"].ok


@then("every capability with a skill_doc loads a schema-valid v2 Skill")
def _every_cap_loads(engine):
    from agency._skill_load import load_skill

    reg = engine.registry
    checked = 0
    failures = []
    for cap_name in reg.names():
        cap = reg.get(cap_name)
        doc = getattr(cap, "skill_doc", None)
        if doc is None:
            continue
        checked += 1
        res = load_skill(cap_name, doc, capabilities_root="/nonexistent")
        if not res.ok:
            failures.append((cap_name, res.code, res.message[:160]))
    assert checked > 0, "expected at least one capability with a skill_doc"
    assert failures == [], (
        "capabilities failed the v2 derive-shim load:\n"
        + "\n".join(f"  {n}  {c}  {m}" for n, c, m in failures))


@when("I load a capability that ships a skill.yaml override", target_fixture="loaded")
def _load_yaml_override(tmp_path):
    from agency._skill_load import load_skill

    cap_dir = tmp_path / "myskill"
    cap_dir.mkdir()
    (cap_dir / "skill.yaml").write_text(textwrap.dedent("""\
        name: myskill
        kind: discipline
        type: discipline
        description: "Use when authoring a custom capability skill by hand (A6)."
        common_mistakes:
          - symptom: "duplicating the module docstring"
            counter: "derive it instead (rule 2)"
        phases:
          - index: 1
            name: design
            produces: [plan]
            goal: "shape the authored skill"
            instructions: "1. State the trigger.\\n2. List the phases."
            freedom: medium
    """))
    return {"loaded": load_skill("myskill", None, capabilities_root=str(tmp_path))}


@then('the loaded skill is owner "capability" and round-trips its authored phases')
def _yaml_override_loaded(loaded):
    res = loaded["loaded"]
    assert res.ok, f"skill.yaml override failed to load: {res.message}"
    sk = res.value
    assert sk.owner == "capability"
    assert sk.type == "discipline"
    d = sk.to_dict()
    assert d["phases"][0]["instructions"].startswith("1. State the trigger.")
    assert d["phases"][0]["freedom"] == "medium"


@when("I check skill source for a capability with and without a skill.yaml",
      target_fixture="sources")
def _check_sources(tmp_path):
    from agency._skill_load import skill_source

    (tmp_path / "bare").mkdir()
    authored = tmp_path / "authored"
    authored.mkdir()
    (authored / "skill.yaml").write_text("name: authored\nkind: capability\n")
    return {
        "bare": skill_source("bare", capabilities_root=str(tmp_path)),
        "authored": skill_source("authored", capabilities_root=str(tmp_path)),
    }


@then('the bare capability reports source "derived" owner "auto"')
def _bare_derived(sources):
    assert sources["bare"]["source"] == "derived"
    assert sources["bare"]["owner"] == "auto"


@then('the skill.yaml capability reports source "authored" owner "capability"')
def _authored_source(sources):
    assert sources["authored"]["source"] == "authored"
    assert sources["authored"]["owner"] == "capability"


@when(parsers.parse('I read skill source for the "{cap}" capability via the verb'),
      target_fixture="verb_source")
def _verb_source(engine, confirmed_intent, cap):
    raw, _ = engine.registry.invoke(
        engine.memory, confirmed_intent, "skills", "source", capability=cap)
    return raw.data if hasattr(raw, "data") else raw


@then('the verb reports a derived skill owned by "auto"')
def _verb_source_derived(verb_source):
    assert verb_source.get("source") == "derived", verb_source
    assert verb_source.get("owner") == "auto"
    assert verb_source.get("name") == "develop"
