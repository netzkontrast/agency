"""`python -m agency` — start the Agency MCP server (stdio).

Three console-script entry points (Spec 039):
  `agency`        — CLI for bash callers (see ``agency.cli:main``).
  `agency-mcp`    — MCP server entry; this module's :func:`main`.
  `agency-doctor` — bare-CLI health check; this module's
                    :func:`doctor_main`. Same payload shape as the
                    `agency_doctor` substrate tool; exit 0 if ok, 1 if
                    degraded — scriptable.

The plugin's `.mcp.json` template points at the discovery shim
``bin/agency-mcp``, which resolves PATH > .venv > bin/. The shim
ultimately execs THIS module via the picked Python.

`JULES_API_KEY` is read lazily by the `jules` capability when invoked,
so it's not required at startup.
"""
from __future__ import annotations

import json
import os
import sys

from ._db_path import resolve_db_path
from .engine import Engine


def main() -> None:
    """MCP server entry — builds the engine over the persistent DB and
    `run()`s the FastMCP server on stdio (the Claude Code plugin
    contract). Code-mode is the WIRE contract; substrate tools come
    through `execute`."""
    _warn_on_install_collision()
    # Spec 020: --db > AGENCY_DB env > ./.agency/session.db > ~/.agency.db
    db_path = resolve_db_path()
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    engine = Engine(db_path)
    # Spec 117: this is the production runtime — let the music capability
    # lazily auto-wire its production drivers (FileStateDriver + SqliteDBDriver
    # + the rest) the first time a verb needs them, bootstrapping a default
    # config + fresh content root if the repo has none yet. Unit tests build a
    # bare Engine without this flag and keep the typed-DEPENDENCY_MISSING
    # contract, so the blast radius stays bounded.
    engine._music_production = True
    mcp = engine.build_mcp(codemode=True)
    mcp.run()                    # default transport = stdio


def _warn_on_install_collision() -> None:
    """Spec 055 (pipx-only) collision guard — vestigial.

    The legacy ``.venv`` bootstrap path was removed. There is no
    longer a marketplace-bootstrap vs pipx collision to guard
    against — pipx is the only install path; the bin/agency-mcp
    shim is a thin PATH router. This stub is kept so callers'
    error paths and tests don't break; future cleanup can drop it.
    """
    return


def doctor_main(argv: list[str] | None = None) -> int:
    """Bare-CLI agency-doctor — Spec 039 §"Distribution" line 72-76.

    Builds an ephemeral ``Engine(":memory:")``, invokes the
    ``agency_doctor`` substrate tool, prints the JSON payload to stdout
    (token-safe + scriptable — pipe through ``jq``, parse from shell).
    Exit code: 0 if ``ok=True``, 1 otherwise.

    The same logic ships as the ``agency_doctor`` MCP tool inside a
    running server. The CLI variant covers the "I can't even start the
    MCP server, what's wrong?" path — runs on system Python, doesn't
    need a venv, doesn't open the persistent DB.
    """
    # In-memory engine — no disk side effects.
    engine = Engine(":memory:")
    try:
        mcp = engine.build_mcp(codemode=False)
        report = _call_doctor(mcp)
    finally:
        engine.memory.close()
    print(json.dumps(report))
    return 0 if report.get("ok") else 1


def _call_doctor(mcp) -> dict:
    """Invoke the registered `agency_doctor` MCP tool and unwrap the
    structured payload. Decoupled from `doctor_main` for testability."""
    import asyncio
    from fastmcp import Client

    async def _go():
        async with Client(mcp) as client:
            result = await client.call_tool("agency_doctor", {})
            sc = result.structured_content
            if isinstance(sc, dict) and "result" in sc:
                return sc["result"]
            if isinstance(sc, dict):
                return sc
            if result.content:
                try:
                    return json.loads(result.content[0].text)
                except (ValueError, TypeError):
                    return {"ok": False, "error": "doctor_main: cannot parse payload"}
            return {"ok": False, "error": "doctor_main: empty payload"}

    return asyncio.run(_go())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "doctor":
        sys.exit(doctor_main(sys.argv[2:]))
    main()
