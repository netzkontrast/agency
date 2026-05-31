"""Spec 029 §A — intent_bootstrap MCP substrate tool.

Closes F1 (Hoch/Blocker) from the KP Fehlerbericht: a pure MCP client
must be able to mint an Intent without dropping to bash. The tool sits
alongside lifecycle_gate / memory_graph_provenance in engine.build_mcp.
"""
import asyncio
import json
import os
import subprocess
import sys
import tempfile

import pytest
from fastmcp import Client

from agency.engine import Engine

REPO_DIR = os.path.dirname(os.path.dirname(__file__))


def _sc(result):
    sc = result.structured_content
    if isinstance(sc, dict):
        return sc.get("result", sc)
    if sc is not None:
        return sc
    if result.content:
        try:
            return json.loads(result.content[0].text)
        except (ValueError, TypeError):
            return result.content[0].text
    return None


def test_intent_bootstrap_registered_and_mints_intent():
    """intent_bootstrap is a substrate tool: it does NOT require intent_id
    (the only verb that doesn't), and it returns {intent_id, status, next}.
    """
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                r = await client.call_tool("intent_bootstrap", {
                    "purpose": "ship spec 029",
                    "deliverable": "MCP bootstrap surface",
                    "acceptance": "tests green",
                })
                return _sc(r)
        out = asyncio.run(main())
        assert isinstance(out, dict)
        assert out["intent_id"].startswith("intent:")
        assert out["status"] == "confirmed"
        assert "next" in out and "call_tool" in out["next"]
        node = e.memory.recall(out["intent_id"])
        assert node is not None and node.get("purpose") == "ship spec 029"
    finally:
        e.memory.close()


def test_intent_bootstrap_rejects_empty_required_fields():
    """Empty required fields fail loud — same shape as the CLI.

    Spec 029 §A error contract (Wiegers/Nygard): ValueError with the
    field name in the message; surfaces as is_error=true on the wire."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return await client.call_tool("intent_bootstrap", {
                    "purpose": "", "deliverable": "x", "acceptance": "y",
                })
        with pytest.raises(Exception) as ei:
            asyncio.run(main())
        assert "purpose" in str(ei.value).lower()
    finally:
        e.memory.close()


def test_bootstrap_records_no_invocation():
    """Spec 029 §A (Crispin): bootstrap matches CLI — no Invocation
    node, no self-loop SERVES edge. Otherwise the bootstrap call would
    appear as an action 'performed by' nothing in provenance, which is
    misleading. Audit trail of 'who called bootstrap' lives in MCP
    server logs, not the graph."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("intent_bootstrap", {
                    "purpose": "ship", "deliverable": "X", "acceptance": "Y"}))
        asyncio.run(main())
        intents = list(e.memory.find("Intent"))
        invocations = list(e.memory.find("Invocation"))
        assert len(intents) == 1
        assert len(invocations) == 0
    finally:
        e.memory.close()


def test_intent_bootstrap_mcp_equals_bash_cli():
    """Spec 029 §E isomorphism: identical inputs produce an Intent node
    with the same purpose/deliverable/acceptance/status, regardless of
    which surface bootstraps it (only the id differs by design)."""
    db = tempfile.mktemp(suffix=".db")
    proc = subprocess.run(
        [sys.executable, "-m", "agency.cli", "--db", db, "intent",
         "--purpose", "p-bash", "--deliverable", "d-bash", "--acceptance", "a-bash"],
        cwd=REPO_DIR, capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": REPO_DIR},
    )
    assert proc.returncode == 0, proc.stderr
    cli_iid = json.loads(proc.stdout)["intent_id"]

    db2 = tempfile.mktemp(suffix=".db")
    e2 = Engine(db2)
    mcp = e2.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                r = await client.call_tool("intent_bootstrap", {
                    "purpose": "p-bash", "deliverable": "d-bash", "acceptance": "a-bash"})
                return _sc(r)
        mcp_iid = asyncio.run(main())["intent_id"]
        mcp_node = e2.memory.recall(mcp_iid)
    finally:
        e2.memory.close()

    e1 = Engine(db)
    try:
        cli_node = e1.memory.recall(cli_iid)
    finally:
        e1.memory.close()
    assert cli_node["purpose"] == mcp_node["purpose"]
    assert cli_node["deliverable"] == mcp_node["deliverable"]
    assert cli_node["acceptance"] == mcp_node["acceptance"]
    assert cli_node["status"] == mcp_node["status"] == "confirmed"
