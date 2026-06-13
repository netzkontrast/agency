"""Spec 029 §A — agency_welcome MCP substrate tool.

Closes F6 (Mittel/DX) + the three-doc-read tax on first contact: one
call returns the bootstrap example, the install example, the capability
map, and the resolved DB path. Token-budget invariant: ≤ 1 KB on the
current core registry.
"""
import asyncio
import json
import tempfile

from fastmcp import Client

from agency.engine import Engine


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


def test_welcome_payload_shape():
    """agency_welcome returns the four onboarding fields + an ordered next list."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_welcome", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    assert isinstance(out, dict)
    assert "bootstrap_example" in out and "intent_bootstrap" in out["bootstrap_example"]
    assert "install_example" in out and "agency_install" in out["install_example"]
    assert "capabilities" in out and isinstance(out["capabilities"], list)
    assert "db_path" in out
    # Spec 030 §C — `next` is now state-aware (2 steps per branch; the
    # third "search" step moved into the in_progress branch).
    assert "next" in out and isinstance(out["next"], list) and len(out["next"]) >= 2
    assert "state" in out


def test_welcome_capabilities_is_deterministic():
    """Capability list iterates in stable (sorted) order. Per Spec 029
    OQ-3 the welcome carries names only (verbs reachable via
    capability_plugin_help / search) — token-budget bit."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_welcome", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    caps = out["capabilities"]
    assert isinstance(caps, list)
    assert caps == sorted(caps)
    # at least the core caps the engine loads at boot
    for required in ("plugin", "reflect"):
        assert required in caps


def test_welcome_works_on_fresh_target(tmp_path, monkeypatch):
    """Spec 029 §A (Cockburn A1 actor): welcome is purely introspective
    — it must not require the DB file to exist. resolve_db_path(None)
    returns the WOULD-BE path on an empty target."""
    monkeypatch.setenv("AGENCY_DB", str(tmp_path / "missing" / "session.db"))
    e = Engine(tempfile.mktemp(suffix=".db"))   # the engine's own DB stays separate
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_welcome", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    assert "session.db" in out["db_path"]


def test_welcome_token_budget_under_2kb():
    """Regression invariant — Spec 029 OQ-3, raised to 2 KB by Spec 068. The
    welcome payload now carries the tier-0 `capability_tier` (one line per
    capability) — a DELIBERATE, net-token-positive enrichment: it lets the agent
    drill in instead of dumping every verb (~1471 tokens), so paying ~500 tokens
    once on welcome saves far more on discovery. The bound stays tight (2 KB); a
    future capability that pushes it over must trim, not raise again blindly."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_welcome", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    payload = json.dumps(out)
    # Flexible budget (CLAUDE.md no-hardcoded rule): the tier scales with the
    # capability count, so the bound is per-capability, not a frozen 2 KB. This
    # still catches BLOAT (a gist that balloons) without breaking when a
    # capability is added.
    ncaps = len(out["capabilities"])
    # Spec 146 Slice 1 raised the constant overhead from 600 → 1000: the
    # prefix half of the envelope carries `schema_version` + two SHA-256
    # hashes (`capability_set_hash`, `ontology_hash`) + the `_prefix_keys`
    # list — ~340 bytes of fixed overhead that buys cache-friendly
    # substrate-tool responses (the wrapping driver applies
    # `cache_control: {type:"ephemeral"}` on the prefix). The per-cap
    # coefficient is unchanged so the bound still catches gist BLOAT.
    # Spec 282 G + user directive (2026-06-13): constant overhead 1000 → 1300
    # to carry the `sandbox_constraints` onboarding field (≤50 call_tool/block,
    # no-file-IO, partial-write persistence) — a CONSTANT-size, high-value field
    # that prevented the ingest's batching failures. The per-cap coefficient
    # (150) is unchanged, so the bound still catches gist BLOAT.
    budget = 150 * ncaps + 1300
    assert len(payload) <= budget, (
        f"welcome payload {len(payload)} bytes exceeds {budget} ({ncaps} caps × 150 + 1300); "
        f"trim the capability_tier gists (Spec 068), don't raise the coefficient")
