"""Ephemeral tool-call store — Spec 336 S2.

Pre/post tool calls are high-volume and full-payload (no-truncate, Spec 336 S1).
Keeping them as `Event` nodes in the durable bi-temporal graph bloated
`session.db` (~95% of nodes were Events). This is a SEPARATE, local, **gitignored**
SQLite store: the FULL capture lives here, OFF the durable provenance graph; the
Stop-hook export (S4) distils the durable signal (top calls + spec suggestions)
out of it before it is pruned.

No graph dependency — this never touches the provenance write path, so a capture
failure can never break a graph write. Append-only; `record()` commits eagerly so
no explicit `close()` is required for durability.
"""
from __future__ import annotations

import os
import sqlite3
import time

_SCHEMA = """
CREATE TABLE IF NOT EXISTS toolcall (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  ts          REAL    NOT NULL,
  session     TEXT    DEFAULT '',
  intent      TEXT    DEFAULT '',
  phase       TEXT,                 -- 'pre' | 'post'
  tool        TEXT,
  input_json  TEXT    DEFAULT '',   -- FULL tool_input (keep_full)
  output_json TEXT    DEFAULT '',   -- FULL tool_response (keep_full)
  filtered    TEXT    DEFAULT ''    -- Spec 336 S3 shell-filtered view (bash)
);
CREATE INDEX IF NOT EXISTS toolcall_tool ON toolcall(tool);
CREATE INDEX IF NOT EXISTS toolcall_session ON toolcall(session);
-- Spec 349a — the event-bus "once" dedup marker. A SEPARATE table so a
-- control-plane marker (the bus delivered subscriber X once for this session)
-- never pollutes the captured tool-call rows above (toolcalls.stats/recent/top/
-- export read only `toolcall`). The (session, scope) PK makes a concurrent
-- first-occurrence deterministic: exactly one INSERT wins, the rest conflict.
CREATE TABLE IF NOT EXISTS event_marker (
  session TEXT NOT NULL,
  scope   TEXT NOT NULL,
  ts      REAL NOT NULL,
  PRIMARY KEY (session, scope)
);
"""


def resolve_path(graph_db_path: str | None = None) -> str:
    """Where ``toolcalls.db`` lives: ``AGENCY_TOOLCALLS_DB`` env wins; else beside
    the graph db (``.agency/toolcalls.db``); else ``:memory:`` for an in-memory
    engine (tests). A SEPARATE file from the graph db — that is the whole point."""
    env = os.environ.get("AGENCY_TOOLCALLS_DB")
    if env:
        return env
    if graph_db_path and graph_db_path != ":memory:":
        return os.path.join(os.path.dirname(graph_db_path) or ".", "toolcalls.db")
    return ":memory:"


class ToolcallStore:
    """A thread-safe append-only SQLite store for full pre/post tool-call capture."""

    def __init__(self, path: str):
        self.path = path
        if path != ":memory:":
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        # check_same_thread=False mirrors Memory: FastMCP/code-mode run in worker
        # threads; the engine is logically single-threaded.
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def record(self, *, phase: str, tool: str = "", session: str = "",
               intent: str = "", input_json: str = "", output_json: str = "",
               filtered: str = "") -> int:
        """Append one full tool-call row; commits eagerly. Returns the row id."""
        cur = self._conn.execute(
            "INSERT INTO toolcall(ts, session, intent, phase, tool, input_json, "
            "output_json, filtered) VALUES (?,?,?,?,?,?,?,?)",
            (time.time(), session, intent, phase, tool, input_json, output_json,
             filtered))
        self._conn.commit()
        return int(cur.lastrowid)

    def mark_seen(self, *, scope: str, session: str) -> bool:
        """Spec 349a — atomic first-occurrence dedup for the event bus, in the
        SEPARATE ``event_marker`` table so it never pollutes the captured tool-call
        rows. ``True`` the FIRST time ``(session, scope)`` is seen; the (session,
        scope) PK conflict makes a concurrent double deterministic (one wins → one
        ``True``). Survives the per-event fresh-process model because the store is
        the persistent ``.agency/toolcalls.db``. Only the "already seen" conflict
        is caught here; any OTHER sqlite error propagates so the caller decides the
        fail-open direction (emit-anyway for a mandatory inject, skip for a hint)."""
        if not scope or not session:
            return False
        try:
            self._conn.execute(
                "INSERT INTO event_marker(session, scope, ts) VALUES (?,?,?)",
                (session, scope, time.time()))
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def count(self) -> int:
        return int(self._conn.execute("SELECT count(*) FROM toolcall").fetchone()[0])

    def rows(self, *, where: str = "", params: tuple = ()) -> list[dict]:
        """All rows (optionally filtered) as dicts, oldest first — FULL data."""
        sql = ("SELECT id, ts, session, intent, phase, tool, input_json, "
               "output_json, filtered FROM toolcall")
        if where:
            sql += f" WHERE {where}"
        sql += " ORDER BY id"
        cols = ["id", "ts", "session", "intent", "phase", "tool", "input_json",
                "output_json", "filtered"]
        return [dict(zip(cols, r)) for r in self._conn.execute(sql, params).fetchall()]

    def top_calls(self, n: int = 20) -> list[dict]:
        """The top ``n`` tool-call shapes by frequency × payload cost (Spec 336 S4).

        Groups identical (tool, input) calls — so a command run 30× ranks above a
        one-off — and ranks by ``calls`` then total ``bytes``. ``sample`` carries
        a representative (filtered-or-raw) output so the export shows the response.
        """
        rows = self._conn.execute(
            "SELECT tool, "
            "  coalesce(nullif(filtered,''), input_json) AS shape, "
            "  count(*) AS calls, "
            "  sum(length(coalesce(output_json,'')) + length(coalesce(input_json,''))) AS bytes, "
            "  max(coalesce(nullif(filtered,''), output_json)) AS sample "
            "FROM toolcall GROUP BY tool, shape "
            "ORDER BY calls DESC, bytes DESC LIMIT ?", (max(1, int(n)),)).fetchall()
        return [{"tool": r[0], "shape": r[1] or "", "calls": int(r[2]),
                 "bytes": int(r[3] or 0), "sample": r[4] or ""} for r in rows]

    def prune(self) -> int:
        """Delete all captured rows (post-export). Returns the tool-call count
        removed. Also clears the Spec 349a event markers (session-scoped, so they
        are dead weight once a session's capture is distilled and pruned)."""
        n = self.count()
        self._conn.execute("DELETE FROM toolcall")
        self._conn.execute("DELETE FROM event_marker")
        self._conn.commit()
        return n

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:                                       # noqa: BLE001
            pass
