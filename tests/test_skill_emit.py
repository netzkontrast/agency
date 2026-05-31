"""Spec 031 Task 2.1 — skill_emit.emit_skill (renders per-cap SKILL.md)."""
import pytest

from agency.capability import SkillDoc
from agency.skill_emit import emit_skill, _classify_tier


def _verbs(*verb_specs):
    """verb_specs: list of (name, role, docstring) tuples → verbs dict."""
    out = {}
    for name, role, doc in verb_specs:
        def make_fn(d=doc):
            def fn(): pass
            fn.__doc__ = d
            return fn
        out[name] = {"role": role, "fn": make_fn(), "inject": []}
    return out


def test_classify_tier_a_full_markers():
    def fn():
        """Brief.

        Inputs: x (str)
        Returns: dict
        chain_next: foo
        """
    assert _classify_tier(fn) == "A"


def test_classify_tier_b_missing_marker():
    def fn():
        """Brief only — no markers."""
    assert _classify_tier(fn) == "B"


def test_classify_tier_a_terminal_chain_next():
    """chain_next: (terminal) or (none) counts as A."""
    def fn():
        """Brief.

        Inputs: x
        Returns: y
        chain_next: (terminal)
        """
    assert _classify_tier(fn) == "A"


def test_emit_skill_returns_path_keyed_dict():
    doc = SkillDoc(
        description="Use when capturing a cross-session insight tagged by scope.",
        overview="Reflect is the cross-session memory layer.",
        triggers=["you learned something a later session shouldn't re-learn",
                  "you want a doctrine observation alongside a code change"],
        canonical_example="agency-reflect-note --intent-id $IID 'observation' 'X → Y'",
        red_flags=["narrative form → re-note in <symptom> → <counter> shape"],
        verb_briefs={"note": "record one"},
    )
    verbs = _verbs(("note", "act",
                    "Record a scope-tagged Reflection.\n\nInputs: scope (str), text (str)\nReturns: {result: id}\nchain_next: capability_reflect_recall\n"))
    out = emit_skill("reflect", doc, verbs)
    assert "skills/reflect/SKILL.md" in out
    body = out["skills/reflect/SKILL.md"]
    assert "name: reflect" in body
    assert "Use when capturing" in body


def test_emit_skill_renders_tier_a_link():
    """Verbs with full markers link to references/<verb>.md."""
    doc = SkillDoc(
        description="Use when X happens.",
        overview="y",
        triggers=["a", "b"],
        canonical_example="agency-reflect-note 'x'",
        red_flags=["narrative → tight"],
    )
    verbs = _verbs(("note", "act",
                    "Note brief.\n\nInputs: x\nReturns: y\nchain_next: bar\n"))
    out = emit_skill("reflect", doc, verbs)
    body = out["skills/reflect/SKILL.md"]
    assert "[details](references/note.md)" in body


def test_emit_skill_renders_tier_b_anchor():
    """Verbs without full markers link to #<verb> anchor in same SKILL.md."""
    doc = SkillDoc(
        description="Use when X happens.",
        overview="y",
        triggers=["a", "b"],
        canonical_example="agency-reflect-recall 'x'",
        red_flags=["narrative → tight"],
        verb_briefs={"recall": "return reflections"},
    )
    # No Inputs/Returns/chain_next markers → Tier B
    verbs = _verbs(("recall", "transform", "Return reflections newest-first."))
    out = emit_skill("reflect", doc, verbs)
    body = out["skills/reflect/SKILL.md"]
    assert "[details](#recall)" in body
    # Tier B anchor section appended at bottom
    assert "## recall" in body


def test_emit_skill_aborts_on_lint_failure():
    """A SkillDoc with bad description fails lint_skill_doc and emit raises."""
    doc = SkillDoc(
        description="This is just narrative without Use when.",  # fails description-trigger-first
        overview="y",
        triggers=["a", "b"],
        canonical_example="agency-reflect-note 'x'",
    )
    verbs = _verbs(("note", "act", "brief"))
    with pytest.raises(ValueError) as ei:
        emit_skill("reflect", doc, verbs)
    msg = str(ei.value)
    assert "description-trigger-first" in msg or "Use when" in msg


def test_emit_skill_includes_canonical_example_in_body():
    doc = SkillDoc(
        description="Use when X.",
        overview="y",
        triggers=["a", "b"],
        canonical_example="agency-foo-bar 'arg1' 'arg2'",
        red_flags=["x → y"],
    )
    verbs = _verbs(("bar", "act",
                    "brief.\n\nInputs: a\nReturns: b\nchain_next: c\n"))
    out = emit_skill("foo", doc, verbs)
    body = out["skills/foo/SKILL.md"]
    assert "agency-foo-bar 'arg1' 'arg2'" in body


def test_emit_skill_includes_red_flags_section():
    doc = SkillDoc(
        description="Use when X.",
        overview="y",
        triggers=["a", "b"],
        canonical_example="agency-foo-bar 'x'",
        red_flags=[
            "narrative → tight pattern form",
            "wrong scope → check the enum",
        ],
    )
    verbs = _verbs(("bar", "act",
                    "brief.\n\nInputs: x\nReturns: y\nchain_next: z\n"))
    out = emit_skill("foo", doc, verbs)
    body = out["skills/foo/SKILL.md"]
    assert "## Red flags" in body
    assert "narrative → tight pattern form" in body
    assert "wrong scope → check the enum" in body


def test_emit_skill_marker_present():
    """Generated SKILL.md leads with `<!-- agency-generated: v$gen_version -->`."""
    doc = SkillDoc(
        description="Use when X.",
        overview="y",
        triggers=["a", "b"],
        canonical_example="agency-foo-bar 'x'",
        red_flags=["x → y"],
    )
    verbs = _verbs(("bar", "act",
                    "brief.\n\nInputs: x\nReturns: y\nchain_next: z\n"))
    out = emit_skill("foo", doc, verbs)
    body = out["skills/foo/SKILL.md"]
    assert body.startswith("<!-- agency-generated: v")
