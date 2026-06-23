"""Spec 392 — auto-append a per-intent session ACTIVITY log on every invocation.

A post-invocation hook (registered on the Spec 286-A3 ``ResultProcessor`` seam)
appends ONE line per Invocation to ``<db-dir>/sessions/<intent>.activity.md`` — a
live, grow-only record of what the session did, updated with each capability call
(owner directive 2026-06-23: "the file gets auto-appended with each call").

Append-only (CLAUDE.md rule 9 — the captured record is never truncated) and
best-effort (a write failure NEVER fails a load-bearing verb). It writes a
SEPARATE file from ``document.session``'s on-demand full snapshot, so the live log
and the rendered Document never clobber each other.
"""
from __future__ import annotations

import os
import time
from typing import Any, Optional

from .memory import Memory


def _sessions_dir(memory: Memory) -> str:
    """The sessions directory — sibling of the graph DB (mirrors
    ``document._sessions_dir`` so both archive into the same ``.agency/sessions/``)."""
    base = os.path.abspath(".agency")
    try:
        conn = memory.g._conn
        conn = getattr(conn, "sqlite_connection", conn)
        for _seq, name, dbfile in conn.execute("PRAGMA database_list").fetchall():
            if name == "main" and dbfile:
                base = os.path.dirname(os.path.abspath(dbfile))
                break
    except Exception:                                           # noqa: BLE001
        pass
    return os.path.join(base, "sessions")


def activity_log_path(memory: Memory, intent_id: str) -> str:
    """Where the per-intent append-only activity log lives."""
    return os.path.join(_sessions_dir(memory),
                        f"{intent_id.replace(':', '_')}.activity.md")


def session_append_hook(memory: Memory, invocation_id: str, intent_id: str,
                        label: Optional[str], result: Any) -> None:
    """Append one line for this invocation. Best-effort; never raises.

    Registered via ``ResultProcessor.register_post_invocation`` (so it runs AFTER
    the Invocation's outcome is stamped). The line names the capability.verb, its
    role, and a non-``completed`` outcome when present."""
    if not intent_id:
        return
    try:
        inv = memory.recall(invocation_id) or {}
        cap = inv.get("capability", "?")
        verb = inv.get("verb", "?")
        role = inv.get("role", "")
        outcome = inv.get("outcome", "")
        path = activity_log_path(memory, intent_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fresh = not os.path.exists(path)
        with open(path, "a", encoding="utf-8") as f:
            if fresh:
                f.write(f"# Session activity — {intent_id}\n\n"
                        "_Append-only; one line per capability call (Spec 392)._\n\n")
            line = f"- {time.strftime('%H:%M:%S')} `{cap}.{verb}`"
            if role:
                line += f" ({role})"
            if outcome and outcome != "completed":
                line += f" → {outcome}"
            f.write(line + "\n")
    except Exception:                                           # noqa: BLE001
        pass    # best-effort notification; a write error must never fail a verb
