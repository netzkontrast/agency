"""DB path resolution per Spec 020 — central .agency/session.db.

Resolution order (Spec 020 Done When item):
  1. ``explicit`` (e.g. the ``--db <path>`` CLI flag).
  2. ``AGENCY_DB`` env var (set by .mcp.json to
     ``${CLAUDE_PLUGIN_DATA}/agency.db`` when installed as a plugin).
  3. ``./.agency/session.db`` (CWD-local — the default in any project
     that has been scaffolded by ``python -m agency.install --scaffold-db``).
  4. ``~/.agency.db`` (system fallback — only when neither env nor CWD
     resolves; e.g. running ``python -m agency`` from $HOME directly).

The CWD-local check looks for the ``.agency/`` directory existence so
the resolver doesn't silently create a DB in arbitrary working
directories (must opt in via the install scaffold).
"""
from __future__ import annotations

import os


def resolve_db_path(explicit: str | None = None) -> str:
    """Return the DB path per Spec 020's resolution order.

    Inputs: explicit (str or None — typically the ``--db`` CLI flag).
    Returns: an absolute or user-expanded path string; the caller is
             responsible for ``os.makedirs(os.path.dirname(...), ...)``
             before opening if the path is in a fresh directory.
    chain_next: Engine(path=...) consumes this.
    """
    if explicit:
        return explicit
    env = os.environ.get("AGENCY_DB")
    if env:
        return env
    cwd_agency = os.path.join(os.getcwd(), ".agency")
    if os.path.isdir(cwd_agency):
        return os.path.join(cwd_agency, "session.db")
    return os.path.expanduser("~/.agency.db")
