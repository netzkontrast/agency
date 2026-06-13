"""Contract / acceptance suite for the Spec-286 four-pillar OOP refactor.

OWNED BY the Vision-owner / Review-partner session. GitHub CI is disabled
(owner directive, 2026-06-13); this suite is the gate. Every assertion is
derived from **docs/vision/CORE.md §"Four complete pillars"** + the refactor
agent's **proposed seam contracts** in `refactor.md` — NOT from reading the
implementation. Invariants are computed from the live tree/registry (rule 8 —
relationships, never frozen snapshots).

Two kinds:
- **Behaviour-preserving guards** — GREEN today, must stay green across the
  refactor (zero contract/wire/verb-name drift).
- **Refactor targets** — `xfail(strict=True)` today; they flip to a hard PASS
  (and announce "XPASS") the moment the refactor satisfies them, so the gate is
  self-reporting.
"""
from __future__ import annotations

import asyncio
import pathlib
import re

import pytest

from agency.engine import Engine

REPO = pathlib.Path(__file__).resolve().parents[2]
CAPS = REPO / "agency" / "capabilities"


def _tool_names(codemode: bool) -> set[str]:
    """The live wire surface a real MCP client sees."""
    from fastmcp import Client

    eng = Engine(__import__("tempfile").mktemp(suffix=".db"))
    mcp = eng.build_mcp(codemode=codemode)

    async def _list():
        async with Client(mcp) as c:
            return {t.name for t in await c.list_tools()}

    try:
        return asyncio.run(_list())
    finally:
        eng.memory.close()


# ───────────────────────── behaviour-preserving guards (GREEN) ─────────────────────────


def test_wire_contract_is_exactly_the_three_verbs() -> None:
    """CORE.md: 'Code-mode IS the contract' — the wire surface is search /
    get_schema / execute (+ the substrate onboarding tools), and per-capability
    verbs are NEVER exposed at the wire (they are reached inside `execute`)."""
    names = _tool_names(codemode=True)
    assert {"search", "get_schema", "execute"} <= names, names
    leaked = {n for n in names if n.startswith("capability_")}
    assert not leaked, f"capability verbs must not leak to the wire: {sorted(leaked)[:5]}"


def test_live_verb_surface_is_substantial_and_nonzero() -> None:
    """Behaviour-preservation: the refactor must not drop the verb surface.
    Counted live (relationship, not a frozen number) — codemode-off exposes one
    tool per capability verb."""
    verbs = {n for n in _tool_names(codemode=False) if n.startswith("capability_")}
    assert len(verbs) > 50, f"verb surface collapsed to {len(verbs)} (<=50)"


def test_agency_doctor_runs_and_reports_health() -> None:
    """Behaviour-preservation: the doctor substrate tool stays callable and
    returns a health mapping (field-set guarded loosely — presence, not a
    frozen snapshot)."""
    from fastmcp import Client

    eng = Engine(__import__("tempfile").mktemp(suffix=".db"))
    mcp = eng.build_mcp(codemode=False)

    async def _call():
        async with Client(mcp) as c:
            r = await c.call_tool("agency_doctor", {})
            sc = r.structured_content
            return sc.get("result", sc) if isinstance(sc, dict) else sc

    try:
        out = asyncio.run(_call())
    finally:
        eng.memory.close()
    assert isinstance(out, dict) and out, "agency_doctor must return a non-empty health dict"


# ───────────────────────── refactor targets (xfail → flip on success) ─────────────────────────


@pytest.mark.xfail(strict=True, reason="A1 GraphStore port not landed — capabilities still reach raw .g")
def test_no_raw_graph_access_in_capabilities() -> None:
    """A1 read-pillar invariant (refactor agent's proposed seam): raw graph
    access (`.g.query` / `.g.get_node`) lives ONLY in agency/memory.py; zero
    hits under agency/capabilities/. Flips GREEN when A1 lands."""
    pat = re.compile(r"\.g\.(query|get_node)\b")
    hits = []
    for f in CAPS.rglob("*.py"):
        for i, line in enumerate(f.read_text().splitlines(), 1):
            if pat.search(line):
                hits.append(f"{f.relative_to(REPO)}:{i}")
    assert not hits, f"{len(hits)} raw-graph sites remain in capabilities (first: {hits[:3]})"


@pytest.mark.xfail(strict=True, reason="capability-per-folder not complete — intent/shell/skills are bare modules")
def test_every_capability_lives_in_its_own_folder() -> None:
    """Goal 4 (open set): a capability is a FOLDER under agency/capabilities/.
    No bare-module capabilities (excluding __init__ and _private helpers).
    Flips GREEN when intent/shell/skills are foldered."""
    bare = [p.name for p in CAPS.glob("*.py")
            if p.name != "__init__.py" and not p.name.startswith("_")]
    assert not bare, f"bare-module capabilities remain (not foldered): {bare}"
