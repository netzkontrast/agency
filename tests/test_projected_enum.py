"""Spec 284 — projected-enum substrate.

Covers the pure ``project_enum`` primitive (agency/_enums.py) and the engine
wire surfacing (`param_enums` → JSON `enum` + description hint, without
wire-level rejection of rich free text).
"""
from __future__ import annotations

import asyncio
import tempfile

from agency._enums import project_enum
from agency.engine import Engine

MEMBERS = ["first", "second", "third-limited", "third-omniscient"]
ALIASES = {
    "omniscient": "third-omniscient",
    "auktorial": "third-omniscient",
    "third": "third-limited",
    "personal": "third-limited",
}


# ─────────────────────── project_enum primitive ───────────────────────


def test_exact_member_no_detail() -> None:
    assert project_enum("third-limited", MEMBERS) == ("third-limited", "")


def test_case_insensitive_exact_keeps_original_as_detail() -> None:
    canonical, detail = project_enum("Third-Limited", MEMBERS)
    assert canonical == "third-limited"
    assert detail == "Third-Limited"


def test_alias_substring_longest_first_precedence() -> None:
    # "third" (→limited) AND "omniscient" (→omniscient) both substring-match;
    # the longer, more specific key wins.
    canonical, detail = project_enum(
        "third-person omniscient narrator", MEMBERS, aliases=ALIASES)
    assert canonical == "third-omniscient"
    assert detail == "third-person omniscient narrator"


def test_rich_description_projects_and_preserves() -> None:
    canonical, detail = project_enum(
        "auktorialer Erzähler", MEMBERS, aliases=ALIASES)
    assert canonical == "third-omniscient"
    assert detail == "auktorialer Erzähler"


def test_no_signal_returns_none() -> None:
    assert project_enum("left-handed narration", MEMBERS, aliases=ALIASES) == (
        None, "left-handed narration")


def test_default_fallback() -> None:
    canonical, detail = project_enum(
        "weird", MEMBERS, aliases=ALIASES, default="third-limited")
    assert canonical == "third-limited"
    assert detail == "weird"


# ─────────────────────── engine wire surfacing ───────────────────────


def _wired_tool(engine: Engine, mcp, name: str):
    for provider in getattr(mcp, "providers", ()):
        for key, tool in getattr(provider, "_components", {}).items():
            if key.startswith("tool:") and getattr(tool, "name", "") == name:
                return tool
    return None


def test_wire_surfaces_enum_in_json_schema_and_description() -> None:
    eng = Engine(tempfile.mktemp(suffix=".db"))
    mcp = eng.build_mcp(codemode=True)
    tool = _wired_tool(eng, mcp, "capability_novel_create_scene")
    assert tool is not None
    pov = tool.parameters["properties"]["pov"]
    # JSON inputSchema carries `enum`; `type` stays string (no strictness).
    assert set(pov["enum"]) == {
        "first", "second", "third-limited", "third-omniscient"}
    assert pov["type"] == "string"
    # The description hint (the renderer-visible surface) lists the members.
    assert "Enums:" in (tool.description or "")
    assert "third-omniscient" in (tool.description or "")
    eng.memory.close()


def test_rich_pov_flows_through_wire_unrejected() -> None:
    # `json_schema_extra` enum is schema-only — pydantic must NOT reject a
    # rich non-member value at the wire; the verb projects it.
    eng = Engine(tempfile.mktemp(suffix=".db"))
    mcp = eng.build_mcp(codemode=True)
    iid = eng.intent.capture("spec 284", "scene", "verified")
    eng.intent.confirm(iid)
    novel, _ = eng.registry.invoke(eng.memory, iid, "novel", "create_novel",
                                   title="X", author="Y")
    chap, _ = eng.registry.invoke(eng.memory, iid, "novel", "create_chapter",
                                  novel_id=novel["novel_id"], number=1,
                                  title="A")

    async def main():
        return await mcp.call_tool("capability_novel_create_scene", {
            "intent_id": iid, "chapter_id": chap["chapter_id"],
            "slug": "rich", "pov": "auktorialer Erzähler (allwissend)"})

    result = asyncio.run(main())
    sc = result.structured_content
    assert sc.get("ok", True) is not False, sc
    assert sc["pov"] == "third-omniscient"
    assert sc["pov_detail"] == "auktorialer Erzähler (allwissend)"
    eng.memory.close()


# ─────────────────── B audit: every named closed enum is surfaced ───────────────────


def test_evidence_enums_surface_in_get_schema() -> None:
    """Spec 284 / Workstream B audit — the closed enums named in the error
    report (the failure buckets: capture_claim.domain 60×, create_codex_entry.kind
    49×, plus statuses/severity/scope) must surface their members in get_schema,
    so a caller discovers the valid set instead of learning it by failing."""
    import tempfile
    from agency.engine import Engine
    from agency.capabilities.novel._main import (
        RESEARCH_DOMAINS, CODEX_ENTRY_KIND, NOVEL_STATUS, CHAPTER_STATUS,
        WORLD_AXIOM_SEVERITY,
    )
    from agency.capabilities.reflect._main import REFLECT_SCOPES

    eng = Engine(tempfile.mktemp(suffix=".db"))
    mcp = eng.build_mcp(codemode=True)

    def _params(tool_name):
        for provider in getattr(mcp, "providers", ()):
            for key, tool in getattr(provider, "_components", {}).items():
                if key.startswith("tool:") and getattr(tool, "name", "") == tool_name:
                    return tool.parameters["properties"], (tool.description or "")
        return None, ""

    cases = [
        ("capability_novel_capture_claim", "domain", RESEARCH_DOMAINS),
        ("capability_novel_create_codex_entry", "kind", CODEX_ENTRY_KIND),
        ("capability_novel_set_novel_status", "status", NOVEL_STATUS),
        ("capability_novel_set_chapter_status", "status", CHAPTER_STATUS),
        ("capability_novel_create_world_axiom", "severity", WORLD_AXIOM_SEVERITY),
        ("capability_reflect_note", "scope", REFLECT_SCOPES),
    ]
    for tool_name, param, members in cases:
        props, desc = _params(tool_name)
        assert props is not None, tool_name
        assert set(props[param]["enum"]) == set(members), tool_name
        assert "Enums:" in desc, tool_name
    eng.memory.close()
