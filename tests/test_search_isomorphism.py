"""Phase 6 — Spec 023 isomorphism gate.

The MCP form (`mcp.call_tool('search', ...)`) and the CLI form
(`python -m agency.cli search ...`) MUST return structurally identical
results after JSON parse (panel F3.1 — not byte-identical; MCP ships
Python dicts via wire, CLI ships stringified JSON via stdout).

This is the load-bearing guarantee that the canon's "isomorphic over
MCP / Skills / bash CLI" claim holds for the search surface specifically.
"""
from __future__ import annotations

import json
import subprocess
import sys

import pytest

from agency.engine import Engine


@pytest.mark.parametrize("query", ["reflect note", "dispatch", "graph"])
async def test_mcp_and_cli_search_are_isomorphic(query, tmp_path):
    db = tmp_path / "iso.db"

    # MCP form — call through the FastMCP catalog. NO `limit` passed:
    # the CLI does not yet expose --limit (Phase 5 follow-up), so for the
    # isomorphism gate both forms use the FastMCP default. Once --limit
    # lands, this test parametrizes over (query, limit) pairs.
    e = Engine(str(db))
    try:
        mcp = e.build_mcp(codemode=True)
        result = await mcp.call_tool("search", {"query": query})
        mcp_body = result.content[0].text
    finally:
        e.memory.close()

    # CLI form — subprocess agency.cli search
    cli_out = subprocess.check_output(
        [sys.executable, "-m", "agency.cli", "--db", str(db), "search", query],
        text=True,
    )

    # The CLI wraps results as JSON-stringified; strip that wrapper.
    cli_parsed = json.loads(cli_out.strip())
    # The MCP form returns the raw string body (the rendered tool list).
    # The CLI's JSON-loaded form should match (panel F3.1).
    assert cli_parsed == mcp_body, (
        f"isomorphism failed for query={query!r}:\n"
        f"MCP form ({len(mcp_body)}b):\n{mcp_body[:300]}…\n"
        f"CLI form ({len(cli_parsed)}b):\n{cli_parsed[:300]}…"
    )
