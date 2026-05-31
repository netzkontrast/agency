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
