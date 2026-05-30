"""Phase 3 RED — engine tightens MCP tool descriptions to the brief slice.

The token-economy lever for Spec 023's ≤120-token search budget. Each
registered capability verb gets its FastMCP tool `description` set to the
brief slice (the first-paragraph one-liner) instead of the full docstring.

- Compliant-docstring verbs (Spec 016 Hint #7) — brief = the one-line gist.
- Legacy-docstring verbs — brief = first paragraph (fallback in render.py).

The full docstring stays reachable via get_schema (which uses the verb's
original __doc__ through fastmcp's parameter schema rendering).
"""
from __future__ import annotations

from agency.engine import Engine
from agency.render import parse_slices


async def test_registered_tool_description_is_brief_slice():
    """The most verbose docstring in the registry (e.g. capability_jules_dispatch)
    must be tightened in the FastMCP tool description."""
    e = Engine(":memory:")
    try:
        mcp = e.build_mcp(codemode=False)
        tools_list = await mcp._list_tools()
        tools = {t.name: t for t in tools_list}
        # find one heavy verb
        heavy = "capability_jules_dispatch"
        assert heavy in tools, f"verb {heavy} not registered; registered: {sorted(tools)[:5]}..."
        described = tools[heavy].description or ""
        # the BRIEF slice from the source docstring
        src_doc = e.registry.get("jules").verbs["dispatch"]["fn"].__doc__ or ""
        brief = parse_slices(src_doc)["brief"]
        assert brief, "source docstring should yield a non-empty brief"
        # the registered description IS the brief; it does NOT include the
        # verbose body
        assert described == brief, (
            f"description mismatch.\n"
            f"described ({len(described)}b): {described[:120]}…\n"
            f"brief     ({len(brief)}b): {brief[:120]}…"
        )
    finally:
        e.memory.close()


async def test_brief_descriptions_save_significant_tokens():
    """Cumulative description tokens across the registry drop by ≥50%."""
    e = Engine(":memory:")
    try:
        mcp = e.build_mcp(codemode=False)
        tools_list = await mcp._list_tools()
        tools = {t.name: t for t in tools_list}
        # cap-verb tools only (skip lifecycle_gate / memory_graph_provenance
        # which are engine-substrate)
        cap_tools = {n: t for n, t in tools.items() if n.startswith("capability_")}
        # tightened descriptions:
        tight = sum(len(t.description or "") for t in cap_tools.values())
        # what the legacy verbose path would have emitted:
        legacy = 0
        for cap_name in e.registry.names():
            for verb, spec in e.registry.get(cap_name).verbs.items():
                doc = (spec["fn"].__doc__ or "").strip()
                legacy += len(doc)
        assert tight < legacy // 2, (
            f"tight={tight} legacy={legacy}; tight should be <half of legacy"
        )
    finally:
        e.memory.close()
