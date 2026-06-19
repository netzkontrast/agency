"""Session-graph snapshot — portable SQLModel export/import (user directive 2026-06-19).

Instead of committing the live binary ``.agency/session.db`` (it churns every
session, is 96% ephemeral Event noise, and embeds this machine's absolute paths),
snapshot the DURABLE graph to portable SQL in ``.agency/sql/`` — diff-able,
re-importable, and version-controlled by git (git history IS the migration trail).
Run periodically (``scripts/session-snapshot export``), NOT every turn.

The ephemeral tool-call Events (now captured in ``.agency/toolcalls.db``, Spec 336)
are excluded by default, so a snapshot is the small durable signal:
Intents · Invocations · Gates · Artefacts · Reflections · the edges between them.

``SnapNode`` / ``SnapEdge`` are SQLModel models — the typed snapshot schema; the
export emits matching SQL, the import replays it through the ``Memory`` API so the
restored graph is fully queryable.
"""
from __future__ import annotations

import json
import os
import sqlite3

from sqlmodel import Field, SQLModel


class SnapNode(SQLModel, table=True):
    __tablename__ = "snap_node"
    id: str = Field(primary_key=True)
    label: str = ""
    data: str = "{}"                    # full node props as JSON
    vfrom: int = 0
    vto: int = 0


class SnapEdge(SQLModel, table=True):
    __tablename__ = "snap_edge"
    id: str = Field(primary_key=True)
    src: str = ""
    dst: str = ""
    rel: str = ""
    vfrom: int = 0
    vto: int = 0


_DEFAULT_SQL = os.path.join(".agency", "sql", "session-snapshot.sql")
# Excluded by default — "only export what has value": ephemeral tool-call Events
# (now in toolcalls.db) and regenerable RepoIndex briefings (document.index_repo).
# What's kept is the DURABLE provenance: Intent · Invocation · Gate · Agent ·
# Reflection · Artefact · Session and the edges between them.
_EPHEMERAL_LABELS = frozenset({"Event", "RepoIndex"})
_EPHEMERAL_EDGES = frozenset({"IN_SESSION"})


def _read_graph(graph_db: str, include_events: bool):
    """Read the graph's authoritative nodes/edges (the `agency_entity`/`agency_edge`
    SQLModel projection) into SnapNode/SnapEdge, dropping ephemera by default."""
    con = sqlite3.connect(graph_db)
    try:
        nodes = [SnapNode(id=r[0], label=r[1] or "", data=r[2] or "{}",
                          vfrom=r[3] or 0, vto=r[4] or 0)
                 for r in con.execute(
                     "SELECT id, label, data, vfrom, vto FROM agency_entity")
                 if include_events or (r[1] not in _EPHEMERAL_LABELS)]
        keep = {n.id for n in nodes}
        edges = [SnapEdge(id=r[0], src=r[1], dst=r[2], rel=r[3] or "",
                          vfrom=r[4] or 0, vto=r[5] or 0)
                 for r in con.execute(
                     "SELECT id, src_id, dst_id, rel, vfrom, vto FROM agency_edge")
                 if (include_events or r[3] not in _EPHEMERAL_EDGES)
                 and r[1] in keep and r[2] in keep]
        return nodes, edges
    finally:
        con.close()


def _q(s) -> str:
    return "'" + str(s).replace("'", "''") + "'"


def _emit_sql(nodes, edges) -> str:
    """The committed artefact: portable SQL (CREATE + INSERT). FULL, never truncated."""
    out = ["-- agency session-graph snapshot (SQLModel: snap_node / snap_edge).",
           "-- Durable provenance only (ephemeral Events excluded). Re-import with",
           "-- `scripts/session-snapshot import`.",
           "BEGIN;",
           "DROP TABLE IF EXISTS snap_node;",
           "DROP TABLE IF EXISTS snap_edge;",
           "CREATE TABLE snap_node (id TEXT PRIMARY KEY, label TEXT, data TEXT, vfrom INTEGER, vto INTEGER);",
           "CREATE TABLE snap_edge (id TEXT PRIMARY KEY, src TEXT, dst TEXT, rel TEXT, vfrom INTEGER, vto INTEGER);"]
    for n in sorted(nodes, key=lambda x: x.id):
        out.append(f"INSERT INTO snap_node VALUES "
                   f"({_q(n.id)},{_q(n.label)},{_q(n.data)},{n.vfrom},{n.vto});")
    for e in sorted(edges, key=lambda x: x.id):
        out.append(f"INSERT INTO snap_edge VALUES "
                   f"({_q(e.id)},{_q(e.src)},{_q(e.dst)},{_q(e.rel)},{e.vfrom},{e.vto});")
    out.append("COMMIT;")
    return "\n".join(out) + "\n"


def export(graph_db: str | None = None, out: str = _DEFAULT_SQL,
           include_events: bool = False) -> dict:
    """Snapshot the durable graph to portable SQL. Returns ``{exported, path,
    nodes, edges}``. Deterministic (sorted) so git diffs are minimal."""
    from ._db_path import resolve_db_path
    graph_db = graph_db or resolve_db_path(None)
    if not os.path.exists(graph_db):
        return {"exported": False, "reason": "no graph db", "path": out}
    nodes, edges = _read_graph(graph_db, include_events)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(_emit_sql(nodes, edges))
    return {"exported": True, "path": out, "nodes": len(nodes), "edges": len(edges)}


def import_snapshot(sql: str = _DEFAULT_SQL, target_db: str | None = None) -> dict:
    """Replay a snapshot into a (fresh or existing) graph via the Memory API, so
    the restored graph is queryable. Best-effort per row. Returns counts."""
    from ._db_path import resolve_db_path
    from .memory import Memory
    target_db = target_db or resolve_db_path(None)
    if not os.path.exists(sql):
        return {"imported": False, "reason": "no snapshot", "path": sql}
    scratch = sqlite3.connect(":memory:")
    with open(sql, encoding="utf-8") as f:
        scratch.executescript(f.read())
    nodes = scratch.execute(
        "SELECT id, label, data FROM snap_node").fetchall()
    edges = scratch.execute("SELECT src, dst, rel FROM snap_edge").fetchall()
    scratch.close()
    mem = Memory(target_db)
    n = e = 0
    for nid, label, data in nodes:
        try:
            # record() writes BOTH the graph node and the typed projection, with the
            # id preserved (replay_node skips the projection). Re-ticked window is
            # fine for a restore; best-effort per row.
            mem.record(label or "Entity", json.loads(data or "{}"), node_id=nid)
            n += 1
        except Exception:                                       # noqa: BLE001
            pass
    for src, dst, rel in edges:
        try:
            mem.link(src, dst, rel)
            e += 1
        except Exception:                                       # noqa: BLE001
            pass
    mem.close()
    return {"imported": True, "target": target_db, "nodes": n, "edges": e}


def main(argv=None) -> int:
    """CLI entrypoint — usable as `python -m agency._session_snapshot {export,import}`
    (the SessionStart hook restores via this) or through `scripts/session-snapshot`."""
    import argparse
    p = argparse.ArgumentParser(prog="session-snapshot")
    sub = p.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("export", help="snapshot the durable graph → SQL")
    ex.add_argument("--all", action="store_true",
                    help="include ephemeral Events/RepoIndex (default: value-only)")
    ex.add_argument("--out", default=_DEFAULT_SQL)
    ex.add_argument("--db", default=None)
    im = sub.add_parser("import", help="replay a SQL snapshot → graph")
    im.add_argument("--sql", default=_DEFAULT_SQL)
    im.add_argument("--db", default=None)
    a = p.parse_args(argv)
    if a.cmd == "export":
        r = export(graph_db=a.db, out=a.out, include_events=a.all)
    else:
        r = import_snapshot(sql=a.sql, target_db=a.db)
    print(json.dumps(r, indent=2))
    return 0 if (r.get("exported") or r.get("imported")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
