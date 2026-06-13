"""dogfood.portage — JSON export + replay for merge-conflict recovery (Spec 020).

Spec 286 P3 — extracted verbatim from ``dogfood/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single DogfoodCapability.

The export → import pair is the merge-conflict recovery fallback: dump the
full bi-temporal provenance store to portable JSON, then replay it (ids +
validity windows preserved) into a fresh DB on the merged branch.
"""
from __future__ import annotations

import json
import os
import time

from ....memory import OPEN


_EXPORT_VERSION = 1   # bump on shape changes


from agency.capability import verb


class PortageMixin:
    """Spec 020 — JSON export + replay (merge-conflict recovery fallback)."""

    # -----------------------------------------------------------------
    # Spec 020 — JSON export (merge-conflict recovery fallback).
    # -----------------------------------------------------------------

    @verb(role="effect")
    def export(self, path: str = "") -> dict:
        """Dump the provenance store to a portable JSON file.

        Inputs: path (str — destination; empty → ``.agency/export-<ns>.json``
                  with a nanosecond-precision timestamp to avoid path
                  collisions between exports in the same second).
        Returns: ``{path, nodes, edges, bytes}``.

        Snapshot semantics: this export captures the FULL bi-temporal
        history (all nodes regardless of vto), not just the
        current-as-of-now snapshot. Replay against a fresh DB
        therefore reconstructs the entire append-only timeline —
        which is the right behaviour for merge-conflict recovery.

        Use case: merge-conflict recovery (Spec 020 line 69-73). When
        two branches both write to ``.agency/session.db`` and merge,
        the binary conflict can't be resolved. Recovery: export each
        branch's graph to JSON, then replay both JSONs against a fresh
        DB on the merged branch. The export is portable + diff-able
        (JSON is indent=2 + sort_keys=True).

        v1 scope: this verb ONLY emits the export. A matching
        ``dogfood.import`` verb that replays the JSON (preserving
        original node ids + vfrom/vto windows) is a v2 follow-up.

        chain_next: caller can rsync, commit, or replay the JSON.
        """
        graph_path = path or self._default_export_path()
        os.makedirs(os.path.dirname(graph_path) or ".", exist_ok=True)
        nodes = self._collect_all_nodes()
        edges = self._collect_all_edges()
        payload = {
            "version": _EXPORT_VERSION,
            "generated_at": int(time.time()),
            "nodes": nodes,
            "edges": edges,
        }
        with open(graph_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
        return {
            "path": graph_path,
            "nodes": len(nodes),
            "edges": len(edges),
            "bytes": os.path.getsize(graph_path),
        }

    def _default_export_path(self) -> str:
        """``.agency/export-<unix-ns>.json`` in the CWD; mirrors the
        Spec 020 ``.agency/`` convention.

        Uses nanosecond precision (review F6) so two exports in the
        same second don't clobber each other. Returned absolute so
        the caller doesn't need to track CWD."""
        ns = time.time_ns()
        return os.path.abspath(
            os.path.join(".agency", f"export-{ns}.json"))

    def _collect_all_nodes(self) -> list[dict]:
        """Every node in the graph — FULL bi-temporal history (per F1
        review finding + the merge-recovery use case). The MATCH (n)
        pattern returns superseded nodes alongside current ones, which
        is exactly what replay needs to reconstruct the timeline."""
        return self.ctx.memory.all_nodes()

    # -----------------------------------------------------------------
    # Spec 020 v2 — JSON replay (the matching reverse of export).
    # -----------------------------------------------------------------

    @verb(role="effect", name="import")
    def import_(self, path: str) -> dict:
        """Replay a JSON export into this graph, preserving ids + windows.

        Inputs: path (str — JSON file written by ``dogfood.export``).
        Returns: ``{imported_nodes, imported_edges, version}``.
        Raises: FileNotFoundError on missing path; ValueError on
        unsupported export version.

        Closes Spec 020's merge-conflict recovery loop: each branch's
        DB is exported, the binary conflict is discarded, and both
        JSONs replay into a fresh DB on the merged branch.

        Preservation discipline: nodes land at their original ids with
        the original ``vfrom``/``vto`` window — bypassing ``record()``'s
        clock tick so bi-temporal history is exact. After replay, the
        memory's logical clock advances past every imported tick so new
        writes cannot collide with imported windows.

        chain_next: terminal — caller can verify with
                    ``MATCH (n) RETURN count(n)`` or ``reflect.search``.
        """
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        version = payload.get("version")
        if version != _EXPORT_VERSION:
            raise ValueError(
                f"unsupported export version {version!r}; "
                f"this build reads version {_EXPORT_VERSION}")

        nodes = payload.get("nodes", [])
        edges = payload.get("edges", [])

        max_tick = 0
        existing = self.ctx.memory.node_ids()
        for n in nodes:
            nid = n.get("id")
            if not nid or nid in existing:
                continue
            label = n.get("label") or "Entity"
            props = dict(n.get("properties", {}))
            # Direct replay — bypass record()'s clock tick + ontology
            # gate so the original vfrom/vto window survives intact.
            self.ctx.memory.replay_node(nid, props, label=label)
            for k in ("vfrom", "vto"):
                v = props.get(k)
                if isinstance(v, int) and v != OPEN and v > max_tick:
                    max_tick = v

        imported_edges = 0
        for e in edges:
            src, dst = e.get("from"), e.get("to")
            rel = e.get("type") or "RELATED"
            if not src or not dst:
                continue
            self.ctx.memory.replay_edge(
                src, dst, dict(e.get("properties") or {}), rel_type=rel)
            v = e.get("properties", {}).get("vfrom")
            if isinstance(v, int) and v != OPEN and v > max_tick:
                max_tick = v
            imported_edges += 1

        # Advance the logical clock past every imported tick so a
        # subsequent record()/link() can't reuse a stale vfrom.
        self.ctx.memory.advance_clock(max_tick)

        return {
            "imported_nodes": sum(
                1 for n in nodes
                if n.get("id") and n["id"] not in existing),
            "imported_edges": imported_edges,
            "version": version,
        }

    def _collect_all_edges(self) -> list[dict]:
        """Every edge in the graph with type + endpoints + properties."""
        return self.ctx.memory.all_edges()
