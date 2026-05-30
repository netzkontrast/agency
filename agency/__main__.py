"""`python -m agency` — start the Agency MCP server (stdio).

The plugin's `.mcp.json` points the Claude Code MCP launcher at the
`bin/agency-mcp` wrapper, which execs this module. We build the engine over a
persistent SQLite (`$AGENCY_DB`, default `~/.agency.db`), build the FastMCP
server with code-mode enabled (the public surface is `search`/`get_schema`/
`execute`), and `run()` it on stdio.

`JULES_API_KEY` is read lazily by the `jules` capability when invoked, so it's
not required at startup.
"""
from __future__ import annotations

import os

from .engine import Engine


def main() -> None:
    db_path = os.environ.get("AGENCY_DB") or os.path.expanduser("~/.agency.db")
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    engine = Engine(db_path)
    mcp = engine.build_mcp(codemode=True)
    mcp.run()                    # default transport = stdio (the Claude Code plugin contract)


if __name__ == "__main__":
    main()
