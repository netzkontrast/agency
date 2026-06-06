"""Spec 080 — Agent Skills spec coverage: every capability is a complete Skill.

All 15 capabilities declare a lint-clean SkillDoc, so the Spec 031/032 emit
pipeline renders a full Agent Skill per capability (SKILL.md L1 frontmatter + L2
body + references/ + scripts/). `develop.validate_skill` is the dogfooded
validation surface; `skill_doc` is REQUIRED at bootstrap.

Behaviour-first: derived from the live registry, no pinned counts.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.capability import Capability
from agency.engine import Engine


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        yield e
    finally:
        e.memory.close()


def _call(e, iid, cap, verb, **kw):
    res, _ = e.registry.invoke(e.memory, iid, cap, verb, **kw)
    return res["result"] if isinstance(res, dict) and "result" in res else res


@pytest.fixture
def iid(engine):
    i = engine.intent.capture("skill-docs", "every cap is a complete Agent Skill", "lint clean")
    engine.intent.confirm(i)
    return i


# --- coverage: every capability declares a lint-clean SkillDoc ----------------

def test_every_capability_has_a_skill_doc(engine):
    missing = [n for n in engine.registry.names()
               if engine.registry.get(n).verbs
               and getattr(engine.registry.get(n), "skill_doc", None) is None]
    assert missing == [], f"capabilities without skill_doc: {missing}"


def test_validate_skill_reports_all_clean(engine, iid):
    out = _call(engine, iid, "develop", "validate_skill")
    assert out["ok"] is True, [r for r in out["results"].items() if not r[1]["ok"]]
    # every verb-bearing capability is represented
    assert "shell" in out["results"] and out["results"]["shell"]["ok"]


def test_validate_skill_single_capability(engine, iid):
    out = _call(engine, iid, "develop", "validate_skill", name="reflect")
    assert out["ok"] is True
    assert set(out["results"]) == {"reflect"}


def test_validate_skill_unknown_capability(engine, iid):
    out = _call(engine, iid, "develop", "validate_skill", name="no-such-cap")
    assert out["ok"] is False
    assert out["results"]["no-such-cap"]["violations"][0]["rule"] == "unknown-capability"


# --- capability names obey the Agent Skills spec name constraint --------------

def test_capability_names_are_spec_legal(engine):
    import re
    for n in engine.registry.names():
        assert re.fullmatch(r"[a-z0-9_]+", n), f"{n!r} not lowercase/digits/underscore"
        assert "claude" not in n and "anthropic" not in n, f"{n!r} uses a reserved word"
        assert len(n) <= 64


# --- the emit pipeline produces the full Skill triad (L1/L2/L3) ---------------

def test_emit_produces_skill_md_with_required_frontmatter():
    from agency import install
    e = Engine(":memory:")
    try:
        files = install.generate(e)
    finally:
        e.memory.close()
    md = files.get("skills/shell/SKILL.md")
    assert md, "per-capability SKILL.md must be emitted now that shell has a skill_doc"
    # Level-1 required frontmatter: name + description
    assert "name: shell" in md
    assert "description:" in md
    # Level-3 progressive disclosure: at least one references/<verb>.md emitted
    assert any(p.startswith("skills/shell/references/") for p in files), \
        "Tier-A verbs must emit references/<verb>.md (Agent Skills L3)"


# --- enforcement: skill_doc REQUIRED at bootstrap -----------------------------

def test_skilldoc_derives_from_module_docstring():
    """Spec 080 — the module docstring is the single source: a SkillDoc reflects
    out of `Use when:`/`Triggers:`/`Red flags:` sections; overview from the prose;
    the example synthesized from the primary verb. No literal needed."""
    from agency.capability import SkillDoc
    import types
    mod = types.ModuleType("demo")
    mod.__doc__ = (
        "demo — a demo capability.\n\n"
        "Demo is a token-tiny example of docstring-derived skills.\n\n"
        "Use when: a demo of derivation is needed.\n"
        "Triggers:\n"
        "- A docstring that should define its own skill\n"
        "- A capability authored without a separate literal\n"
        "Red flags:\n"
        "- Duplicating the overview into a literal → derive it from the docstring\n"
    )
    doc = SkillDoc.from_module(mod, "demo", ["beta", "alpha"])
    assert doc is not None
    assert doc.description == "Use when a demo of derivation is needed."
    assert doc.overview == "Demo is a token-tiny example of docstring-derived skills."
    assert len(doc.triggers) == 2 and doc.triggers[0].startswith("A docstring")
    assert doc.red_flags and "→" in doc.red_flags[0]
    # example synthesized from the sorted-first verb
    assert "capability_demo_alpha" in doc.canonical_example


def test_docstring_without_use_when_yields_no_skill():
    """No `Use when:` marker → derivation returns None (the cap must then set a
    skill_doc explicitly). Keeps derivation opt-in + explicit."""
    from agency.capability import SkillDoc
    import types
    mod = types.ModuleType("plain")
    mod.__doc__ = "plain — just a normal module docstring, no skill sections.\n"
    assert SkillDoc.from_module(mod, "plain", ["v"]) is None


def test_bootstrap_rejects_verb_capability_without_skill_doc():
    """A verb-bearing capability lacking a skill_doc fails engine bootstrap
    (Spec 080 — skill_doc is no longer opt-in)."""
    nodoc = Capability(
        name="nodoc", home="capability",
        verbs={"ping": {"role": "transform", "fn": lambda: {"result": "pong"}, "inject": []}},
    )
    with pytest.raises(ValueError, match="skill_doc"):
        Engine(":memory:", extra_capabilities=[nodoc])
