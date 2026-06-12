"""Spec 157 Slice 1 — typed ArchitectureReport + wire-verb invariant audit.

Spec 019 commits to EXACTLY three wire verbs at the engine boundary
(`search` / `get_schema` / `execute`); every capability verb is reached
THROUGH them, never alongside. Slice 1 audits the live engine surface
to prove this invariant holds + carries a typed report that future
slices (Slice 2 import-violations, Slice 3 cycle detection, Slice 4
fan-in/fan-out, Slice 5 baseline drift) extend.

The audit is pure over the engine handle; no graph writes. CI wires
the strict gate via `--strict`; today's CLI is informational.
"""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ArchitectureReport:
    """The typed Slice 1 audit payload.

    `wire_verbs` — the live tool names that look like wire verbs
    (`search` / `get_schema` / `execute`). Slice 1 only records names;
    Slice 2 records (name → signature) for the signature-drift gate.

    `invariant_ok` — True iff the documented three are present in
    `wire_verbs`. Per CLAUDE.md rule 8 a SUBSET invariant: an
    intentionally-shipped 4th wire verb doesn't break the invariant;
    only REMOVING a documented one does."""

    wire_verbs:      list[str] = field(default_factory=list)
    wire_verb_count: int = 0
    invariant_ok:    bool = False
    # Slice 2 will add: import_violations, cycles, fan_in, fan_out, …


_DOCUMENTED_WIRE_VERBS = ("search", "get_schema", "execute")


def audit_wire_verbs(engine) -> ArchitectureReport:
    """Walk the live MCP wire surface; return a typed ArchitectureReport.

    Spec 157 Slice 1 invariant — the documented three wire verbs
    (`search` / `get_schema` / `execute`) MUST be a subset of the
    audited tool list. Other tools may appear (capability verbs, the
    canonical wire verbs, etc.); the audit walks the FastMCP server
    + filters to the wire-verb shape (name in the documented set).
    """
    # Spec 019 — the wire verbs are CODE-MODE substrate tools (not the
    # flat per-capability tool surface). build_mcp(codemode=True) exposes
    # EXACTLY the three; codemode=False exposes the capability_<cap>_<verb>
    # surface instead.
    mcp = engine.build_mcp(codemode=True)
    try:
        tools = asyncio.run(mcp.list_tools())
    except RuntimeError:
        # Already in a running loop — schedule the coroutine.
        loop = asyncio.new_event_loop()
        try:
            tools = loop.run_until_complete(mcp.list_tools())
        finally:
            loop.close()
    except Exception:
        # Defensive: unknown MCP shape → return the empty typed report
        # rather than crash. The strict-mode CLI will exit 1.
        return ArchitectureReport(
            wire_verbs=[], wire_verb_count=0, invariant_ok=False)
    tool_names = _extract_tool_names(tools)
    wire = sorted(set(_DOCUMENTED_WIRE_VERBS) & set(tool_names))
    rep = ArchitectureReport(
        wire_verbs=wire,
        wire_verb_count=len(wire),
        invariant_ok=set(_DOCUMENTED_WIRE_VERBS).issubset(set(tool_names)),
    )
    return rep


def _extract_tool_names(tools) -> set[str]:
    """`tools` may be a dict (name → spec) or an iterable of objects
    with a `.name`. Handle both."""
    out: set[str] = set()
    if isinstance(tools, dict):
        for k in tools:
            if isinstance(k, str):
                out.add(k)
        return out
    try:
        for t in tools:
            name = getattr(t, "name", None) or (t.get("name") if isinstance(t, dict) else None)
            if isinstance(name, str):
                out.add(name)
    except TypeError:
        pass
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--db", default=":memory:",
                        help="engine DB (default: in-memory)")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 if the wire-verb invariant is broken")
    args = parser.parse_args(argv)
    from agency.engine import Engine
    e = Engine(args.db)
    try:
        rep = audit_wire_verbs(e)
    finally:
        e.memory.close()
    print(f"wire-verb audit: count={rep.wire_verb_count}  "
          f"verbs={rep.wire_verbs}  invariant_ok={rep.invariant_ok}")
    if args.strict and not rep.invariant_ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
