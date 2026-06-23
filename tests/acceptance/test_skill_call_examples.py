"""Acceptance — Spec 390: generated skills teach the CALL (code-mode examples).

A fresh agent following a SKILL.md must learn not just WHEN to use a capability
but HOW to call it through the MCP — the prefixed `capability_<cap>_<verb>` wire
name, threaded with the serving `intent_id`, inside a code-mode block. The
examples are DERIVED from the capability's live verbs (no hand-editing), so every
generated skill gains them at once.
"""
from __future__ import annotations

import tempfile


def _render(cap_name: str) -> tuple[str, list[str]]:
    from agency.engine import Engine
    from agency.skill_emit import emit_skill

    eng = Engine(tempfile.mktemp(suffix=".db"))
    try:
        c = eng.registry.get(cap_name)
        files = emit_skill(cap_name, c.skill_doc, c.verbs,
                           getattr(c.ontology, "skills", None))
        md = next(v for k, v in files.items() if k.endswith("/SKILL.md"))
        verbs = sorted(c.verbs)
    finally:
        eng.memory.close()
    return md, verbs


def test_generated_skill_contains_code_mode_call_examples():
    md, verbs = _render("reflect")
    assert "call_tool(" in md, "skill must show a code-mode call example"
    # uses the REAL prefixed wire name for a real verb of this capability (D3)
    assert any(f"capability_reflect_{v}" in md for v in verbs), md
    # threads the serving intent_id (the SERVES discipline)
    assert "intent_id" in md
    # a bootstrap/chaining example: bootstrap an intent, then call a verb
    assert "intent_bootstrap" in md, "skill must show the bootstrap→verb chain"


def test_call_examples_use_the_underscored_wire_name_for_underscored_caps():
    # The wire prefix is `capability_skill_generator_` (underscores) — NOT the
    # hyphenated skill-folder name. The example must be a RESOLVABLE wire name.
    md, verbs = _render("skill_generator")
    assert any(f"capability_skill_generator_{v}" in md for v in verbs), md
    assert "capability_skill-generator_" not in md, "hyphenated wire name is unresolvable"


def test_using_agency_teaches_the_wire_naming_rule():
    """Spec 390 D4 — the meta-skill must distinguish the BARE substrate tools from
    the prefixed `capability_<cap>_<verb>` verbs, and tell the agent to get_schema
    an unfamiliar verb before the first call (the OBSERVE worst-gap C1/C2)."""
    from agency.install import _USING_AGENCY_SKILL_MD as md
    # names the bare substrate tools explicitly
    for bare in ("agency_welcome", "intent_bootstrap", "agency_doctor",
                 "memory_graph_provenance"):
        assert bare in md, f"using-agency must name the bare tool {bare!r}"
    # states the capability_<cap>_<verb> rule for everything else
    assert "capability_<cap>_<verb>" in md
    # distinguishes bare vs prefixed explicitly
    assert "bare" in md.lower() and "prefix" in md.lower()
    # tells the agent to get_schema an unfamiliar verb (detail="full" for objects)
    assert "get_schema" in md and "full" in md
