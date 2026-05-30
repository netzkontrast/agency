"""Spec 025 Phase 1 RED — verb→skill tag wiring.

After engine build, every verb that some skill phase binds to (via the
`invoke={capability, verb}` field) carries a `skill:<name>` tag. This is the
foundation of skill-first discovery — `search(tags=["skill:brainstorm"])`
returns the verbs that participate in `brainstorm` (research confirmed
code-mode's `Search` already filters by tags natively).

Zero behaviour change at this layer: a new tag attribute on verb specs,
populated by reflection over `Capability.ontology.skills`. Phase 2 starts
USING it.
"""
from __future__ import annotations

import pytest

from agency.engine import Engine


def _verb_spec(engine, capability, verb):
    """Helper — the raw verb dict on the Capability object."""
    return engine.registry.get(capability).verbs[verb]


def test_verbs_tagged_with_their_skill():
    """Every (capability, verb) named by a skill phase's `invoke` field
    receives a `skill:<skillname>` tag at engine build.

    Concrete check: `develop.review` skill phase 2 has
    invoke={capability:"delegate", verb:"fan_out"} — so the `fan_out`
    verb on the `delegate` capability must carry `skill:review` after
    engine init.
    """
    e = Engine(":memory:")
    try:
        spec = _verb_spec(e, "delegate", "fan_out")
        assert "tags" in spec, "verb specs should expose a `tags` set"
        assert "skill:review" in spec["tags"], (
            f"delegate.fan_out should be tagged `skill:review` "
            f"(it is invoked from the `review` skill); got tags={spec['tags']!r}"
        )
    finally:
        e.memory.close()


def test_verb_can_carry_multiple_skill_tags():
    """A single verb invoked from multiple skills carries all `skill:*`
    tags simultaneously (set semantics). Today only review binds fan_out,
    so this test asserts the data structure supports multiplicity even
    when reality currently has one — guarding against a future
    last-write-wins regression."""
    e = Engine(":memory:")
    try:
        spec = _verb_spec(e, "delegate", "fan_out")
        assert isinstance(spec["tags"], (set, frozenset)), (
            f"tags should be a set for multi-skill membership; got {type(spec['tags']).__name__}"
        )
    finally:
        e.memory.close()


def test_untagged_verbs_have_empty_tag_set():
    """A verb that no skill phase invokes (e.g. `reflect.note` is called
    from skill bodies via `ctx.spawn`, not via a phase `invoke` binding)
    has an empty `tags` set — NOT missing the key (callers can iterate
    safely)."""
    e = Engine(":memory:")
    try:
        spec = _verb_spec(e, "reflect", "note")
        assert "tags" in spec
        # No skill phase binds reflect.note via `invoke`; it's called from
        # walked-skill phase implementations directly. So no skill: tag.
        skill_tags = {t for t in spec["tags"] if t.startswith("skill:")}
        assert skill_tags == set(), (
            f"reflect.note has no skill phase binding it; expected no skill:* tags, got {skill_tags!r}"
        )
    finally:
        e.memory.close()


async def test_search_finds_skill_tagged_verbs():
    """R2 (Codex review of 660d7f5): the wiring test above proves tags
    land on the internal verb spec, but the ADVERTISED contract is that
    `search(tags=["skill:review"])` finds the bound verb via the public
    MCP surface. This test exercises the consumer — without the
    `_wire`→`mcp.tool(..., tags=...)` propagation it would fail despite
    the wiring test passing."""
    e = Engine(":memory:")
    try:
        mcp = e.build_mcp(codemode=False)
        tools = await mcp._list_tools()
        bound = next(
            (t for t in tools if t.name == "capability_delegate_fan_out"),
            None,
        )
        assert bound is not None, "capability_delegate_fan_out should be a registered MCP tool"
        assert "skill:review" in bound.tags, (
            f"FastMCP Tool.tags must carry `skill:review` (R2): "
            f"propagation from verb spec → mcp.tool failed. got tags={bound.tags!r}"
        )
    finally:
        e.memory.close()


def test_skill_prefix_is_reserved():
    """`skill:` is a reserved tag prefix — the wiring path is the only
    legitimate source. A capability author cannot smuggle a fake skill
    tag by adding `tags={"skill:fake"}` to a verb spec at registration."""
    from agency.capability import Capability

    cap = Capability(
        name="rogue",
        home="capability",
        verbs={
            "act": {
                "role": "act",
                "fn": lambda **_kw: {"result": "ok"},
                "inject": [],
                "tags": {"skill:i-made-this-up"},  # should be stripped/rejected
            },
        },
    )
    e = Engine(":memory:", extra_capabilities=[cap])
    try:
        spec = _verb_spec(e, "rogue", "act")
        assert "skill:i-made-this-up" not in spec["tags"], (
            "manual `skill:*` tags must be stripped — only phase invoke "
            "bindings legitimately create them"
        )
    finally:
        e.memory.close()
