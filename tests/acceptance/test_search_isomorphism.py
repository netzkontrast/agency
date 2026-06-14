"""Acceptance — MCP/CLI search isomorphism (Spec 023 §F3.1).

Converted from tests/test_search_isomorphism.py. Behaviour: the search
result from the MCP wire and the CLI must be structurally identical after
JSON parse. This guards the "isomorphic over MCP / Skills / bash CLI" canon.
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import tempfile

from pytest_bdd import parsers, scenarios, then, when

from agency.engine import Engine

scenarios("features/search_isomorphism.feature")


def _mcp_search(db: str, query: str) -> str:
    e = Engine(db)
    try:
        mcp = e.build_mcp(codemode=True)

        async def _run():
            result = await mcp.call_tool("search", {"query": query})
            return result.content[0].text

        return asyncio.run(_run())
    finally:
        e.memory.close()


def _cli_search(db: str, query: str) -> str:
    raw = subprocess.check_output(
        [sys.executable, "-m", "agency.cli", "--db", db, "search", query],
        text=True,
    )
    parsed = json.loads(raw.strip())
    return parsed


# ── When step ──────────────────────────────────────────────────────────────

@when(parsers.parse('I search for "{query}" via MCP and via CLI on the same database'),
      target_fixture="iso_results")
def _iso_search(query):
    db = tempfile.mktemp(suffix=".db")
    mcp_body = _mcp_search(db, query)
    cli_body = _cli_search(db, query)
    return mcp_body, cli_body


# ── Then step ──────────────────────────────────────────────────────────────

@then("the MCP result and CLI result are structurally identical")
def _identical(iso_results):
    mcp_body, cli_body = iso_results
    assert cli_body == mcp_body, (
        f"isomorphism failed:\n"
        f"MCP ({len(mcp_body)}b): {mcp_body[:200]!r}\n"
        f"CLI ({len(cli_body)}b): {cli_body[:200]!r}"
    )
