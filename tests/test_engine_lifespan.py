"""Spec 012 Phase 8 — engine lifespan starts the Jules watcher.

`FastMCP.run()` enters the lifespan async-context-manager on startup and
exits it on shutdown. Our lifespan attaches the Watcher to the engine
(at `engine._jules_watcher`) so the Phase 7 verbs can reach it.

Tests drive the lifespan directly (don't actually start an MCP server):
- Before `__aenter__`: no watcher attached.
- Inside the lifespan: `engine._jules_watcher` is a live Watcher with
  a running poll task.
- After `__aexit__`: poll task cancelled cleanly; further calls don't raise.
"""
import asyncio
import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


async def test_lifespan_attaches_watcher_on_enter(engine):
    """Pre-lifespan: no watcher attached."""
    assert not hasattr(engine, "_jules_watcher")

    lifespan = engine._make_lifespan()
    async with lifespan(server=None) as state:
        # Inside the lifespan, the watcher is live + has a running task.
        assert hasattr(engine, "_jules_watcher")
        watcher = engine._jules_watcher
        assert watcher._task is not None
        assert not watcher._task.done()
        # Lifespan state is currently empty (we don't expose anything via it
        # — the engine is reachable via CapabilityContext.engine, not via
        # the FastMCP Context.lifespan_state path).
        assert state == {}


async def test_lifespan_stops_watcher_cleanly_on_exit(engine):
    lifespan = engine._make_lifespan()
    async with lifespan(server=None):
        watcher = engine._jules_watcher
        task = watcher._task
    # Yield to the loop so the task's cancellation finalises.
    await asyncio.sleep(0)
    # Past the lifespan, the watcher task is done (cancelled).
    assert task.done()


async def test_lifespan_is_idempotent_across_re_entry(engine):
    """If the lifespan is entered, exited, and entered again on the same
    engine instance, a fresh poll task is started and the prior cancelled
    task does not leak. This shouldn't happen in real MCP usage (FastMCP
    enters the lifespan exactly once per server.run()) but the invariant
    is cheap to verify."""
    lifespan = engine._make_lifespan()

    async with lifespan(server=None):
        first_task = engine._jules_watcher._task

    await asyncio.sleep(0)
    assert first_task.done()

    async with lifespan(server=None):
        second_task = engine._jules_watcher._task
        assert second_task is not first_task
        assert not second_task.done()

    await asyncio.sleep(0)
    assert second_task.done()


async def test_build_mcp_passes_lifespan_to_fastmcp(engine):
    """The engine's `build_mcp` wires the lifespan onto the FastMCP server.
    Without `lifespan=` set, the watcher would never start under
    `python -m agency`."""
    mcp = engine.build_mcp(codemode=False)
    # FastMCP stores the lifespan at `_lifespan` (see fastmcp/server/server.py:373).
    # We don't compare callable identity (FastMCP may wrap it), but we DO
    # verify it isn't the default no-op lifespan.
    from fastmcp.server.server import default_lifespan
    assert mcp._lifespan is not default_lifespan


async def test_verbs_reach_watcher_through_engine_after_lifespan_enter(engine):
    """End-to-end: with the lifespan entered, `jules.watch` resolves to the
    real engine-attached watcher and drains a queued event. Exercises the
    full chain CapabilityContext.engine → engine._jules_watcher → queue."""
    iid = engine.intent.capture("e2e lifespan", "watch resolves", "queue drains")
    engine.intent.confirm(iid)

    lifespan = engine._make_lifespan()
    async with lifespan(server=None):
        watcher = engine._jules_watcher
        event = {"action": "verify_pr", "session": "sess-x", "state": "COMPLETED",
                 "instruction": "...", "evidence": {}}
        watcher._put_event(iid, event)

        res, _inv = engine.registry.invoke(
            engine.memory, iid, "jules", "watch",
            agent_id="agent:claude", for_intent=iid, timeout=0,
        )
        assert res["action"] == "verify_pr"
        assert res["_for_intent"] == iid
