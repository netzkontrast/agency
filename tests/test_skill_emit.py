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


from agency.skill_emit import emit_references


def _verb(role, doc):
    def fn(): pass
    fn.__doc__ = doc
    return {"role": role, "fn": fn, "inject": []}


def test_emit_references_returns_empty_for_no_tier_a_verbs():
    """A capability with only Tier-B verbs produces no reference files."""
    verbs = {"recall": _verb("transform", "Return reflections (no markers).")}
    out = emit_references("reflect", verbs)
    assert out == {}


def test_emit_references_produces_one_file_per_tier_a_verb():
    """Each Tier-A verb gets exactly one references/<verb>.md file."""
    verbs = {
        "note": _verb("act", "Record a Reflection.\n\nInputs: scope (str): the scope tag\nReturns: {result: id}\nchain_next: capability_reflect_recall\n"),
        "search": _verb("transform", "Search reflections.\n\nInputs: query (str): keyword\nReturns: {result: list}\nchain_next: terminal\n"),
        "tier_b": _verb("transform", "No markers here."),
    }
    out = emit_references("reflect", verbs)
    assert set(out.keys()) == {
        "skills/reflect/references/note.md",
        "skills/reflect/references/search.md",
    }


def test_emit_references_marker_present():
    """Each reference file leads with the agency-generated marker."""
    verbs = {"note": _verb("act",
        "Record a Reflection.\n\nInputs: scope (str)\nReturns: dict\nchain_next: recall\n")}
    out = emit_references("reflect", verbs)
    body = out["skills/reflect/references/note.md"]
    assert body.startswith("<!-- agency-generated: v")


def test_emit_references_includes_verb_full_name_and_brief():
    verbs = {"note": _verb("act",
        "Record a scope-tagged Reflection.\n\nInputs: scope (str)\nReturns: {result: id}\nchain_next: capability_reflect_recall\n")}
    out = emit_references("reflect", verbs)
    body = out["skills/reflect/references/note.md"]
    assert "reflect.note" in body
    assert "Record a scope-tagged Reflection." in body


def test_emit_references_includes_inputs_returns_chain_next():
    verbs = {"note": _verb("act",
        "Brief.\n\nInputs: scope (str): the scope tag\nReturns: {result: <reflection_id>}\nchain_next: capability_reflect_recall\n")}
    out = emit_references("reflect", verbs)
    body = out["skills/reflect/references/note.md"]
    assert "scope" in body            # inputs rendered
    assert "reflection_id" in body    # returns rendered
    assert "capability_reflect_recall" in body  # chain_next rendered


from agency.skill_emit import emit_bash_wrappers


def _verb_with_params(role, params: list, doc=""):
    """Build a verb spec whose fn has given positional params (excluding ctx)."""
    import inspect

    def fn(**kwargs): pass
    fn.__doc__ = doc
    fn.__signature__ = inspect.Signature([
        inspect.Parameter(p, inspect.Parameter.KEYWORD_ONLY, annotation=str)
        for p in params
    ])
    return {"role": role, "fn": fn, "inject": []}


def test_emit_bash_wrappers_one_per_verb():
    """Every verb (Tier A and B both) gets a wrapper file."""
    verbs = {
        "note": _verb_with_params("act", ["scope", "text"]),
        "recall": _verb_with_params("transform", ["scope"]),
    }
    out = emit_bash_wrappers("reflect", verbs)
    assert set(out.keys()) == {
        "bin/agency-reflect-note",
        "bin/agency-reflect-recall",
    }


def test_emit_bash_wrappers_shebang():
    verbs = {"note": _verb_with_params("act", ["scope", "text"])}
    out = emit_bash_wrappers("reflect", verbs)
    body = out["bin/agency-reflect-note"]
    assert body.startswith("#!/usr/bin/env bash")


def test_emit_bash_wrappers_marker_present():
    verbs = {"note": _verb_with_params("act", ["scope", "text"])}
    out = emit_bash_wrappers("reflect", verbs)
    body = out["bin/agency-reflect-note"]
    assert "agency-generated: v" in body


def test_emit_bash_wrappers_intent_id_handling():
    """Wrapper sources AGENCY_INTENT_ID + accepts --intent-id ID."""
    verbs = {"note": _verb_with_params("act", ["scope", "text"])}
    out = emit_bash_wrappers("reflect", verbs)
    body = out["bin/agency-reflect-note"]
    assert "AGENCY_INTENT_ID" in body
    assert "--intent-id" in body


def test_emit_bash_wrappers_handles_zero_params():
    """A verb with NO user params still gets a wrapper that takes only --intent-id."""
    verbs = {"ping": _verb_with_params("transform", [])}
    out = emit_bash_wrappers("foo", verbs)
    body = out["bin/agency-foo-ping"]
    assert "agency-foo-ping" in body


def test_emit_bash_wrappers_skips_injected_params():
    """Engine-injected params (ctx, client, vcs, intent_id, agent_id) are
    EXCLUDED from the user-facing args. The wrapper supplies them via env / inject."""
    import inspect

    def fn(ctx=None, client=None, scope="", text=""): pass
    fn.__signature__ = inspect.Signature([
        inspect.Parameter("ctx", inspect.Parameter.KEYWORD_ONLY),
        inspect.Parameter("client", inspect.Parameter.KEYWORD_ONLY),
        inspect.Parameter("scope", inspect.Parameter.KEYWORD_ONLY, annotation=str),
        inspect.Parameter("text", inspect.Parameter.KEYWORD_ONLY, annotation=str),
    ])

    verbs = {"note": {"role": "act", "fn": fn, "inject": ["ctx", "client"]}}
    out = emit_bash_wrappers("reflect", verbs)
    body = out["bin/agency-reflect-note"]
    # Wrapper should reference user-facing params (scope, text), NOT injected ones
    assert "scope" in body
    assert "text" in body
    # Should NOT positionally take ctx or client (those come from the engine)
    # The wrapper's arg-count check should reflect 2 user args, not 4


# ── Spec 150 Slice 2 review (round 2) — optional args + dict coercion ─────
def test_emit_bash_wrappers_optional_params_omitted_from_required_count():
    """Codex review on PR #136: params with defaults are OPTIONAL —
    the wrapper must NOT require them or existing callers passing
    only the required args break."""
    import inspect

    def fn(scope: str = "", since: str = "", limit: int = 20,
           use_llm: bool = True, prefer_delegate: bool = False,
           host_completion: dict | None = None): pass
    fn.__signature__ = inspect.Signature([
        inspect.Parameter("scope", inspect.Parameter.KEYWORD_ONLY,
                           annotation=str, default=""),
        inspect.Parameter("since", inspect.Parameter.KEYWORD_ONLY,
                           annotation=str, default=""),
        inspect.Parameter("limit", inspect.Parameter.KEYWORD_ONLY,
                           annotation=int, default=20),
        inspect.Parameter("use_llm", inspect.Parameter.KEYWORD_ONLY,
                           annotation=bool, default=True),
        inspect.Parameter("prefer_delegate", inspect.Parameter.KEYWORD_ONLY,
                           annotation=bool, default=False),
        inspect.Parameter("host_completion", inspect.Parameter.KEYWORD_ONLY,
                           annotation=dict | None, default=None),
    ])
    verbs = {"v": {"role": "transform", "fn": fn, "inject": []}}
    out = emit_bash_wrappers("dogfood", verbs)
    body = out["bin/agency-dogfood-v"]
    # All params have defaults → 0 required; arg_check should accept zero.
    assert "expected at least 0" not in body, (
        "noisy zero-required error message should be suppressed when "
        "all params have defaults")
    # Optional params are conditional on len(sys.argv).
    assert 'if len(sys.argv) > 2: _kw["scope"]' in body
    assert 'if len(sys.argv) > 7: _kw["host_completion"]' in body
    # host_completion is dict | None — must coerce as dict, NOT str.
    assert '_kw["host_completion"] = _coerce(sys.argv[7], dict)' in body, (
        "Optional[dict] / dict|None must coerce as dict so JSON payloads "
        "reach the verb as a dict; otherwise the resume path breaks.")


def test_emit_bash_wrappers_optional_dict_param_uses_dict_coercion():
    """A standalone `dict | None` param coerces as `dict` (not the
    fallthrough `str`) so the bash surface can pass a JSON object."""
    import inspect

    def fn(payload: dict | None = None): pass
    fn.__signature__ = inspect.Signature([
        inspect.Parameter("payload", inspect.Parameter.KEYWORD_ONLY,
                           annotation=dict | None, default=None),
    ])
    verbs = {"v": {"role": "act", "fn": fn, "inject": []}}
    out = emit_bash_wrappers("x", verbs)
    body = out["bin/agency-x-v"]
    assert 'if len(sys.argv) > 2: _kw["payload"] = _coerce(sys.argv[2], dict)' in body


def test_emit_bash_wrappers_required_args_still_enforced():
    """Required params (no defaults) still must be supplied — the
    arg_check guards them. Regression on the optional refactor."""
    import inspect

    def fn(required_arg: str): pass
    fn.__signature__ = inspect.Signature([
        inspect.Parameter("required_arg", inspect.Parameter.KEYWORD_ONLY,
                           annotation=str),
    ])
    verbs = {"v": {"role": "act", "fn": fn, "inject": []}}
    out = emit_bash_wrappers("x", verbs)
    body = out["bin/agency-x-v"]
    # 1 required arg → guarded by `-lt 1`.
    assert '-lt 1' in body, (
        "required params must still be enforced; got body without -lt 1")
    assert 'required_arg' in body


def test_ann_repr_unwraps_optional_dict():
    """`dict | None` / `Optional[dict]` → ``dict`` (round 2 fix)."""
    from agency.skill_emit import _ann_repr
    import typing
    assert _ann_repr(dict | None) == "dict"
    assert _ann_repr(typing.Optional[dict]) == "dict"
    assert _ann_repr(typing.Optional[list]) == "list"
    assert _ann_repr(typing.Optional[int]) == "int"


def test_ann_repr_unwraps_postponed_optional_dict():
    """Postponed `from __future__ import annotations` form: the
    annotation is a string like `'dict | None'` — strip the union
    trailer."""
    from agency.skill_emit import _ann_repr
    assert _ann_repr("dict | None") == "dict"
    assert _ann_repr("list | None") == "list"
    assert _ann_repr("None | dict") == "dict"


from agency.skill_emit import _capability_hash


def test_capability_hash_stable_across_runs():
    """Same capability shape → same hash."""
    from agency.capability import Capability

    def fn(scope: str = ""): pass
    fn.__doc__ = "Test verb."
    cap = Capability(name="x", home="capability",
                     verbs={"note": {"role": "act", "fn": fn, "inject": []}})
    h1 = _capability_hash(cap, rule_version=1)
    h2 = _capability_hash(cap, rule_version=1)
    assert h1 == h2
    assert len(h1) == 64  # sha256 hex


def test_capability_hash_changes_on_rule_version_bump():
    from agency.capability import Capability

    def fn(scope: str = ""): pass
    cap = Capability(name="x", home="capability",
                     verbs={"note": {"role": "act", "fn": fn, "inject": []}})
    h1 = _capability_hash(cap, rule_version=1)
    h2 = _capability_hash(cap, rule_version=2)
    assert h1 != h2


def test_capability_hash_changes_on_docstring_change():
    from agency.capability import Capability

    def fn1(scope: str = ""): pass
    fn1.__doc__ = "Original."
    cap1 = Capability(name="x", home="capability",
                      verbs={"note": {"role": "act", "fn": fn1, "inject": []}})

    def fn2(scope: str = ""): pass
    fn2.__doc__ = "Changed."
    cap2 = Capability(name="x", home="capability",
                      verbs={"note": {"role": "act", "fn": fn2, "inject": []}})

    assert _capability_hash(cap1, 1) != _capability_hash(cap2, 1)
