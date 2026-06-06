"""Spec 031 §A — SkillDoc + WalkerSkills dataclasses + bootstrap validation."""
from agency.capability import SkillDoc, WalkerSkills, CapabilityBase


def test_skilldoc_fields_present():
    doc = SkillDoc(
        description="Use when X",
        overview="Y",
        triggers=["t1", "t2"],
        canonical_example="agency-foo-bar baz",
    )
    assert doc.description == "Use when X"
    assert doc.red_flags == []
    assert doc.required_subskills == []
    assert doc.verb_briefs == {}


def test_walkerskills_fields_present():
    ws = WalkerSkills(schemas={"foo": {"name": "foo", "kind": "discipline", "phases": []}})
    assert "foo" in ws.schemas


def test_capabilitybase_attrs_default_to_none():
    class _Cap(CapabilityBase):
        name = "test"
        home = "capability"
    assert _Cap.skill_doc is None
    assert _Cap.walker_skills is None


import pytest

from agency.capability import Capability
from agency.engine import Engine


def test_bootstrap_rejects_capability_with_verbs_but_no_skill_doc(monkeypatch):
    """Spec 080 — a capability declaring verbs MUST declare (or derive) a skill_doc;
    the requirement is ALWAYS on (no env opt-in). The synthetic cap below has no
    module docstring to derive from, so it must fail bootstrap.

    Isolation: monkey-patch `discover` to return [] so the validation pass sees
    ONLY the test capability.
    """
    monkeypatch.setattr("agency.engine.discover", lambda: [])
    bad = Capability(
        name="badcap", home="capability",
        verbs={"ping": {"role": "transform", "fn": lambda: {"result": "ok"}, "inject": []}},
    )
    with pytest.raises(ValueError) as ei:
        Engine(":memory:", extra_capabilities=[bad])
    msg = str(ei.value)
    assert "badcap" in msg
    assert "skill_doc" in msg


def test_bootstrap_allows_capability_without_verbs(monkeypatch):
    """A capability with no verbs needs no skill_doc (isolated from shipped caps)."""
    monkeypatch.setattr("agency.engine.discover", lambda: [])
    empty = Capability(name="emptycap", home="capability", verbs={})
    e = Engine(":memory:", extra_capabilities=[empty])
    try:
        assert "emptycap" in e.registry.names()
    finally:
        e.memory.close()


def test_require_skill_doc_false_bypasses_the_gate(monkeypatch):
    """The internal `_require_skill_doc=False` flag bypasses the requirement —
    used by lint probes / fixtures that build an engine to test OTHER concerns."""
    monkeypatch.setattr("agency.engine.discover", lambda: [])
    bad = Capability(
        name="bad2", home="capability",
        verbs={"ping": {"role": "transform", "fn": lambda: {"result": "ok"}, "inject": []}},
    )
    e = Engine(":memory:", extra_capabilities=[bad], _require_skill_doc=False)
    try:
        assert "bad2" in e.registry.names()
    finally:
        e.memory.close()


from agency.capability import SkillDoc
from agency.capabilities.plugin import lint_skill_doc


def _verbs(*names):
    return {n: {"role": "transform", "fn": lambda: None, "inject": []} for n in names}


def test_lint_passes_clean_skilldoc():
    doc = SkillDoc(
        description="Use when capturing a cross-session insight tagged by scope.",
        overview="Reflect is the cross-session memory layer.",
        triggers=["you learned something a later session shouldn't re-learn",
                  "you want a doctrine observation alongside a code change"],
        canonical_example="agency-reflect-note --intent-id $IID 'observation' 'X → Y'",
        red_flags=["narrative form → re-note in <symptom> → <counter> shape"],
        verb_briefs={"note": "record one"},
    )
    out = lint_skill_doc("reflect", doc, _verbs("note"))
    assert out["ok"], out["violations"]


def test_lint_rejects_description_without_use_when():
    doc = SkillDoc(
        description="Records a reflection node.",
        overview="x",
        triggers=["a", "b"],
        canonical_example="agency-reflect-note 'x' 'y'",
    )
    out = lint_skill_doc("reflect", doc, _verbs("note"))
    assert not out["ok"]
    assert any(v["rule"] == "description-trigger-first" for v in out["violations"])


def test_lint_rejects_workflow_summary_in_description():
    doc = SkillDoc(
        description="Use when you want to first call X, then Y, then Z.",
        overview="x",
        triggers=["a", "b"],
        canonical_example="agency-reflect-note 'x' 'y'",
    )
    out = lint_skill_doc("reflect", doc, _verbs("note"))
    assert not out["ok"]
    assert any(v["rule"] == "description-no-workflow-summary" for v in out["violations"])


def test_lint_rejects_triggers_with_procedural_verbs():
    doc = SkillDoc(
        description="Use when capturing insights.",
        overview="x",
        triggers=["call reflect.note", "create a reflection"],
        canonical_example="agency-reflect-note 'x' 'y'",
    )
    out = lint_skill_doc("reflect", doc, _verbs("note"))
    assert not out["ok"]
    assert any(v["rule"] == "triggers-named-symptoms" for v in out["violations"])


def test_lint_rejects_triggers_count_outside_2_5():
    doc = SkillDoc(
        description="Use when X.", overview="x",
        triggers=["only-one"],
        canonical_example="agency-reflect-note 'x' 'y'",
    )
    out = lint_skill_doc("reflect", doc, _verbs("note"))
    assert not out["ok"]
    assert any(v["rule"] == "triggers-count" for v in out["violations"])


def test_lint_rejects_example_not_referencing_real_verb():
    doc = SkillDoc(
        description="Use when X.", overview="x",
        triggers=["a", "b"],
        canonical_example="agency-foo-bar 'x' 'y'",  # 'bar' isn't a verb of reflect
    )
    out = lint_skill_doc("reflect", doc, _verbs("note", "recall"))
    assert not out["ok"]
    assert any(v["rule"] == "example-uses-real-verb" for v in out["violations"])


def test_lint_requires_red_flags_when_3plus_verbs():
    doc = SkillDoc(
        description="Use when X.", overview="x",
        triggers=["a", "b"],
        canonical_example="agency-reflect-note 'x' 'y'",
        red_flags=[],
    )
    out = lint_skill_doc("reflect", doc, _verbs("note", "recall", "search"))
    assert not out["ok"]
    assert any(v["rule"] == "red-flags-required" for v in out["violations"])


def test_lint_rejects_verb_briefs_with_unknown_verb():
    doc = SkillDoc(
        description="Use when X.", overview="x",
        triggers=["a", "b"],
        canonical_example="agency-reflect-note 'x' 'y'",
        verb_briefs={"note": "record one", "phantom": "does not exist"},
    )
    out = lint_skill_doc("reflect", doc, _verbs("note"))
    assert not out["ok"]
    assert any(v["rule"] == "verb-briefs-resolve" for v in out["violations"])


def test_lint_rejects_workflow_summary_in_overview():
    """Rule overview-no-workflow-summary fires when overview narrates steps."""
    doc = SkillDoc(
        description="Use when X happens.",
        overview="First the system probes, then it commits.",
        triggers=["a", "b"],
        canonical_example="agency-reflect-note 'x' 'y'",
    )
    out = lint_skill_doc("reflect", doc, _verbs("note"))
    assert not out["ok"]
    assert any(v["rule"] == "overview-no-workflow-summary" for v in out["violations"])


def test_lint_rejects_red_flag_without_symptom_counter_delimiter():
    """Rule red-flags-format fires when a red_flag lacks '→' or ' - '."""
    doc = SkillDoc(
        description="Use when X happens.",
        overview="x",
        triggers=["a", "b"],
        canonical_example="agency-reflect-note 'x' 'y'",
        red_flags=["just a free-form thought without a delimiter"],
    )
    out = lint_skill_doc("reflect", doc, _verbs("note"))
    assert not out["ok"]
    assert any(v["rule"] == "red-flags-format" for v in out["violations"])
