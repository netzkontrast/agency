"""Shared fixtures + helpers for the Gherkin acceptance suite.

Phase C — the flat `tests/test_*.py` are converted into behaviour scenarios
here (owner directive). Every area's `test_<area>.py` binds its
`features/<area>.feature` via `scenarios(...)` and defines its Given/When/Then
steps, reusing these fixtures + helpers so the suite stays coherent (no
conflicting step modules). Behaviour only — assert what the system DOES
(observable: wire surface, provenance, returned values, graph state), never
internal call shapes. Prefer relationships over pinned tool names so the suite
survives the Spec-291 rename.
"""
from __future__ import annotations

import asyncio
import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    """A fresh engine on a throwaway DB."""
    eng = Engine(tempfile.mktemp(suffix=".db"))
    yield eng
    eng.memory.close()


@pytest.fixture
def confirmed_intent(engine):
    """A confirmed Intent every verb can SERVE."""
    iid = engine.intent.capture("acceptance", "behaviour preserved", "verified")
    engine.intent.confirm(iid)
    return iid


# ── helpers (import into step modules) ────────────────────────────────────────

def tool_names(engine, codemode: bool = True) -> set[str]:
    """The wire surface a real MCP client sees."""
    from fastmcp import Client

    mcp = engine.build_mcp(codemode=codemode)

    async def _l():
        async with Client(mcp) as c:
            return {t.name for t in await c.list_tools()}

    return asyncio.run(_l())


def call_tool(engine, name: str, args: dict, codemode: bool = False):
    """Call a wire tool by name; return the unwrapped structured result."""
    from fastmcp import Client

    mcp = engine.build_mcp(codemode=codemode)

    async def _c():
        async with Client(mcp) as c:
            r = await c.call_tool(name, args)
            sc = r.structured_content
            return sc.get("result", sc) if isinstance(sc, dict) else sc

    return asyncio.run(_c())


def invoke(engine, intent_id: str, cap: str, verb: str, **kw):
    """In-process capability invocation (records provenance). Returns (result, inv_id)."""
    return engine.registry.invoke(engine.memory, intent_id, cap, verb, **kw)


def served(engine, intent_id: str, label: str = "Invocation") -> int:
    """Count nodes of `label` that SERVE the intent (provenance check)."""
    rows = engine.memory.g.query(
        f"MATCH (n:{label})-[:SERVES]->(t) WHERE t.id = $iid RETURN n",
        {"iid": intent_id})
    return len(rows)


# ── shared Given steps (available to every feature module) ────────────────────
from pytest_bdd import given  # noqa: E402


@given("a fresh agency engine in code-mode")
def _given_fresh_engine(engine):
    return engine


@given("a confirmed intent")
def _given_confirmed_intent(confirmed_intent):
    return confirmed_intent
