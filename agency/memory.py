"""Memory — the moat. One bi-temporal, append-only graph on real GraphQLite.

Every node (Intent, Invocation, Lifecycle, Agent, Artefact, Gate) and every edge
(SERVES, BY, PRODUCES, DISPATCHED_TO, PASSED, SUPERSEDED_BY) lives here. Reads go
through `project()` (ranked, budget-capped). Cross-concern provenance is a single
Cypher traversal from an Intent — the one thing a flat SDK+memory-tool stack
cannot answer in one hop.
"""
from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Optional

from graphqlite import Graph, connect

from . import ontology
from ._entity_store import EntityStore

OPEN = 10 ** 12  # sentinel valid_to for the currently-valid version


class Memory:
    def __init__(self, path: str, ont: Optional["ontology.Ontology"] = None):
        # Build the Graph with a thread-safe SQLite connection: FastMCP and the
        # code-mode (Monty) sandbox run tools in worker threads, and the engine is
        # logically single-threaded, so check_same_thread=False is safe here.
        self.g = Graph.__new__(Graph)
        self.g._conn = connect(str(path), check_same_thread=False)
        self.g.namespace = "default"
        # the EFFECTIVE ontology (core + capability extensions), injected by the
        # engine. A standalone Memory falls back to the bare core.
        self.ont = ont if ont is not None else ontology.Ontology.core()
        # the logical clock is shared across worker threads (check_same_thread=False);
        # serialize it, and seed it from persisted state so ticks stay monotonic
        # across reopens (the bash CLI opens a fresh Engine per call).
        self._lock = threading.Lock()
        self._tick = self._max_persisted_tick()
        # Spec 289 Slice 2b — the graph-authoritative typed projection. EntityStore
        # binds to the graph's EXACT raw sqlite3 connection (one shared `.db`, even
        # for `:memory:`), so the entity rows live in the same database as the graph
        # nodes and are JOIN-able by node id. One-way mirror (graph → row): every
        # authoritative write below mirrors AFTER the graph upsert succeeds. sqlmodel
        # is a core dep, so no optional guard.
        self.entities = EntityStore(
            sqlite_connection=self.g._conn.sqlite_connection)

    def _max_persisted_tick(self) -> int:
        # Spec 006 #1 — O(1) clock seed: NO unconstrained full scan. Every tick ever
        # assigned appears as some row's `vfrom` (vto is only ever a prior tick or OPEN),
        # so two server-side `max(vfrom)` aggregations — one over nodes, one over edges —
        # and take the larger. (Scanning nodes alone under-counts when the last write
        # before a reopen was an edge, letting new writes reuse stale ticks.)
        def _agg(query: str) -> int:
            try:
                rows = self.g.query(query)
            except Exception:
                return 0
            v = (rows[0] or {}).get("m", 0) if rows else 0
            return v if isinstance(v, int) and v != OPEN else 0

        return max(_agg("MATCH (n) RETURN max(n.vfrom) AS m"),
                   _agg("MATCH ()-[r]->() RETURN max(r.vfrom) AS m"))

    def _now(self) -> int:
        with self._lock:
            self._tick += 1
            return self._tick

    def _mirror(self, node_id: str, label: str, props: dict[str, Any],
                vfrom: int, vto: int = OPEN) -> None:
        """Mirror one authoritative graph node into the typed projection
        (Spec 289 Slice 2b). One-way: graph → entity row, keyed by node id.

        The graph is the source of truth and is ALWAYS written first; this is
        a derived, re-derivable view, so a projection failure must NEVER fail
        the authoritative write that already succeeded. Best-effort: swallow
        any error (the row can be re-derived from the graph)."""
        try:
            self.entities.upsert(node_id, label, props, vfrom=vfrom, vto=vto)
        except Exception:                                   # noqa: BLE001
            # projection is re-derivable from the authoritative graph; never
            # let a mirror error escape the graph write. (Optionally observable
            # via a monitor; no hard dependency added here.)
            pass

    # --- write axis: record · link · supersede -------------------------------
    def record(self, label: str, props: dict[str, Any], node_id: Optional[str] = None) -> str:
        bad = self.ont.violations(label, props)
        if bad:
            raise ValueError(f"{label} record violates ontology: {bad}")
        nid = node_id or f"{label.lower()}:{uuid.uuid4().hex[:8]}"
        tick = self._now()
        data = {**props, "vfrom": tick, "vto": OPEN}
        self.g.upsert_node(nid, data, label=label)         # graph is authoritative
        self._mirror(nid, label, props, vfrom=tick, vto=OPEN)
        return nid

    def link(self, src: str, dst: str, rel: str, props: Optional[dict] = None) -> None:
        if not self.ont.is_known_edge(rel):
            raise ValueError(f"unknown edge type {rel!r}; not in the effective ontology's edge set")
        # Spec 282 Workstream C — durable edge write. graphqlite's upsert_edge is
        # NON-atomic (MERGE then a separate SET r.vfrom); under concurrent
        # MCP+CLI writes the SET raises `Failed to set property 'vfrom' on edge
        # N`, which silently dropped 85 of 97 PRECEDES edges in the evidence run.
        # Retry the TRANSIENT contention (Spec 282 classifies it) with a fresh
        # tick each attempt; a non-transient error still fails fast (no storm).
        from .toolresult import Severity, classify_severity
        attempts = 4
        for i in range(attempts):
            try:
                self.g.upsert_edge(src, dst, {**(props or {}), "vfrom": self._now()}, rel_type=rel)
                return
            except Exception as e:                          # noqa: BLE001
                sev = classify_severity("", exc=e, message=str(e))
                if sev != Severity.TRANSIENT or i == attempts - 1:
                    raise
                time.sleep(0.05 * (2 ** i))

    def update(self, node_id: str, changes: dict[str, Any]) -> None:
        """In-place mutation (keeps id + edges stable). For mutable state like a
        Lifecycle's current phase; use `supersede` for append-only entities."""
        node = self.g.get_node(node_id)
        if node is None:
            raise KeyError(node_id)
        label = node["labels"][0] if node.get("labels") else "Entity"
        merged = {**node["properties"], **changes}
        bad = self.ont.violations(label, {k: v for k, v in merged.items()
                                          if k not in ("vfrom", "vto", "id")})
        if bad:
            raise ValueError(f"{label} update violates ontology: {bad}")
        self.g.upsert_node(node_id, merged, label=label)   # graph is authoritative
        # mirror the merged user props; preserve the node's bi-temporal window
        # (update is in-place — id + window are stable).
        self._mirror(node_id, label, merged,
                     vfrom=merged.get("vfrom", 0), vto=merged.get("vto", OPEN))

    def supersede(self, node_id: str, changes: dict[str, Any]) -> str:
        node = self.g.get_node(node_id)
        if node is None:
            raise KeyError(node_id)
        old = dict(node["properties"])
        label = node["labels"][0] if node.get("labels") else "Entity"
        new_props = {k: v for k, v in old.items() if k not in ("vfrom", "vto", "id")}
        new_props.update(changes)
        bad = self.ont.violations(label, new_props)            # validate BEFORE mutating:
        if bad:                                                # a rejected amend must leave
            raise ValueError(f"{label} supersede violates ontology: {bad}")   # history intact
        now = self._now()
        # close the old version (append-only: it keeps its valid window)
        closed_old = {**old, "vto": now}
        self.g.upsert_node(node_id, closed_old, label=label)   # graph authoritative
        new_id = f"{node_id}#{now}"
        new_props.update({"vfrom": now, "vto": OPEN})
        self.g.upsert_node(new_id, new_props, label=label)
        self.link(node_id, new_id, "SUPERSEDED_BY")
        # mirror BOTH: close the old row's window, then project the new version.
        self._mirror(node_id, label, closed_old,
                     vfrom=closed_old.get("vfrom", 0), vto=now)
        self._mirror(new_id, label, new_props, vfrom=now, vto=OPEN)
        return new_id

    def retract(self, node_id: str) -> int:
        """Bi-temporal SOFT delete (Spec 293): close the node's valid window
        (``vto = now``) so as-of/`find` reads drop it, while history is retained
        — the append-only graph never destructively deletes. Returns the close
        tick. Idempotent-ish: re-retracting just re-closes at a later tick.
        Raises ``KeyError`` for an unknown id."""
        node = self.g.get_node(node_id)
        if node is None:
            raise KeyError(node_id)
        props = dict(node["properties"])
        label = node["labels"][0] if node.get("labels") else "Entity"
        now = self._now()
        props["vto"] = now
        self.g.upsert_node(node_id, props, label=label)        # graph authoritative
        self._mirror(node_id, label,
                     {k: v for k, v in props.items() if k not in ("vfrom", "vto", "id")},
                     vfrom=props.get("vfrom", 0), vto=now)
        return now

    # --- read axis: recall · find · validate ---------------------------------
    def recall(self, node_id: str, as_of: Optional[int] = None) -> Optional[dict]:
        node = self.g.get_node(node_id)
        if node is None:
            return None
        props = node["properties"]
        if as_of is not None and not (props["vfrom"] <= as_of < props["vto"]):
            return None
        return props

    def recall_typed(self, node_id: str, label: str) -> Optional[dict]:
        """Return a node's properties iff it exists AND carries ``label``.

        Spec 056 — the type-safe node-id guard. A verb that takes a ``<label>_id``
        parameter must verify the endpoint's LABEL, not just its existence:
        ``recall(id)`` passes for ANY node, so an ``intent_id`` typo'd as a
        ``research_id`` would silently anchor edges at the wrong endpoint and
        later label-filtered traversals drop them. Returns ``None`` for the three
        caller-recoverable misses (empty id, missing node, wrong label) and a
        COPY of the properties otherwise (mutation-safe). Pure read.
        """
        if not node_id:
            return None
        node = self.g.get_node(node_id)
        if node is None:
            return None
        if label not in (node.get("labels") or []):
            return None
        return dict(node.get("properties", {}))

    def find(self, label: str, as_of: Optional[int] = None) -> list[dict]:
        rows = self.g.query(f"MATCH (n:{label}) RETURN n")
        out = []
        for r in rows:
            p = r["n"]["properties"]
            if as_of is None:
                if p["vto"] == OPEN:
                    out.append(p)
            elif p["vfrom"] <= as_of < p["vto"]:
                out.append(p)
        return out

    def labels_of(self, node_id: str) -> list[str]:
        """The label set of a node (Spec 286 A1 — GraphStore read surface).

        A capability that has a property dict (from ``find``/``neighbors``)
        but needs the node's TYPE asks here rather than reaching into
        ``g.get_node``. Returns ``[]`` for a missing/empty id.
        """
        if not node_id:
            return []
        node = self.g.get_node(node_id)
        if node is None:
            return []
        return list(node.get("labels") or [])

    # --- GraphStore read surface (Spec 286 A1) -------------------------------
    # Typed, edge-aware reads so capabilities never hand-write Cypher. Each
    # returns property dicts (or lists of them), never a raw CypherResult/row.
    # Raw `.g.query`/`.g.get_node` lives ONLY here. The Management read-API
    # builds on this surface.

    def neighbors(self, node_id: str, edge: str, direction: str = "in",
                  limit: int = 100) -> list[dict]:
        """One-hop edge traversal (Spec 125, promoted from CapabilityContext).

        Returns property dicts of nodes connected to ``node_id`` via an
        ``edge``-typed relationship. ``direction="in"`` (default) finds nodes
        pointing AT ``node_id`` (e.g. children via CHAPTER_OF); ``"out"`` finds
        nodes ``node_id`` points at (e.g. the parent). Returns ``[]`` for
        unknown ids or no matching edges; ``limit`` caps the row count.
        """
        if direction not in ("in", "out"):
            raise ValueError(
                f"direction must be 'in' or 'out', got {direction!r}")
        if direction == "in":
            q = (f"MATCH (n)-[:{edge}]->(t) WHERE t.id = $id "
                 f"RETURN n LIMIT {int(limit)}")
            key = "n"
        else:
            q = (f"MATCH (n)-[:{edge}]->(t) WHERE n.id = $id "
                 f"RETURN t LIMIT {int(limit)}")
            key = "t"
        return [r[key]["properties"] for r in self.g.query(q, {"id": node_id})]

    def query_nodes(self, label: str, where: Optional[dict] = None) -> list[dict]:
        """Labeled nodes filtered by exact property match (Spec 286 A1).

        ``where`` maps property name → required exact value; ``None`` / empty
        returns every node carrying ``label`` (full history, like the raw
        ``MATCH (n:Label)`` — NOT current-version-filtered; use ``find`` for the
        valid-now slice). Returns a list of property dicts.
        """
        rows = self.g.query(f"MATCH (n:{label}) RETURN n")
        out = [r["n"]["properties"] for r in rows]
        if where:
            out = [p for p in out
                   if all(p.get(k) == v for k, v in where.items())]
        return out

    def nodes_serving(self, intent_id: str, label: Optional[str] = None,
                      where: Optional[dict] = None) -> list[dict]:
        """Nodes with a SERVES edge to an intent (Spec 286 A1).

        The provenance read every concern shares: Invocations, Lifecycles,
        SessionLifecycles, JulesSessions, Artefacts that SERVE an intent. With
        ``label`` set, restricts to that source label; ``where`` adds exact
        property filters on the source node. ``intent_id`` may be a single id
        or a collection of ids (the SUPERSEDED_BY chain) — pass the chain to
        keep amended-intent provenance whole. Returns source property dicts.
        """
        return self._sources_via_edge("SERVES", intent_id, "Intent",
                                       label=label, where=where)

    def sources_via_edge(self, edge: str, target_id, target_label: str,
                          label: Optional[str] = None,
                          where: Optional[dict] = None) -> list[dict]:
        """Nodes that point at ``target_id`` via ``edge`` (Spec 286 A1).

        Generalizes ``nodes_serving`` to any edge type: ``HAS_FINDING`` from an
        Analysis, ``CITES`` from a Research, ``OBSERVED_DURING`` to an Intent,
        ``DELEGATES_TO`` from a Delegation. ``target_id`` may be one id or a
        collection (matched with ``IN``). ``label``/``where`` filter the SOURCE
        node. Returns source property dicts.
        """
        return self._sources_via_edge(edge, target_id, target_label,
                                      label=label, where=where)

    def _sources_via_edge(self, edge: str, target_id, target_label: str,
                          label: Optional[str], where: Optional[dict]) -> list[dict]:
        src_pat = f"(s:{label})" if label else "(s)"
        ids = list(target_id) if isinstance(target_id, (list, set, tuple)) else [target_id]
        q = (f"MATCH {src_pat}-[:{edge}]->(t:{target_label}) "
             f"WHERE t.id IN $ids RETURN s")
        out = [r["s"]["properties"] for r in self.g.query(q, {"ids": ids})]
        if where:
            out = [p for p in out
                   if all(p.get(k) == v for k, v in where.items())]
        return out

    def edge_pairs(self, edge: str, src_label: Optional[str] = None,
                   dst_label: Optional[str] = None) -> list[tuple[dict, dict]]:
        """Every ``edge``-typed relationship as (src_props, dst_props) pairs.

        Spec 286 A1 — for global edge reads that aren't anchored to a single
        node (e.g. the PRECEDES graph for a topo-sort). ``src_label`` /
        ``dst_label`` optionally constrain the endpoints. Returns a list of
        (source-property-dict, destination-property-dict) tuples.
        """
        sp = f"(a:{src_label})" if src_label else "(a)"
        dp = f"(b:{dst_label})" if dst_label else "(b)"
        q = f"MATCH {sp}-[:{edge}]->{dp} RETURN a, b"
        return [(r["a"]["properties"], r["b"]["properties"])
                for r in self.g.query(q)]

    def artefacts_produced_under(self, intent_id) -> list[dict]:
        """Artefacts PRODUCED by an Invocation that SERVES ``intent_id``
        (Spec 286 A1 — the two-hop provenance read).

        The standard registry path: every ``effect`` verb records an
        Invocation SERVING the intent and a PRODUCES edge to its Artefact.
        Distinct from ``nodes_serving(intent, "Artefact")`` which is the
        DIRECT Artefact-SERVES-Intent path (delegations/reductions). Callers
        that want both union the two (mirrors ``provenance``). ``intent_id``
        may be one id or a collection (the SUPERSEDED_BY chain).
        """
        ids = list(intent_id) if isinstance(intent_id, (list, set, tuple)) else [intent_id]
        q = ("MATCH (it:Intent)<-[:SERVES]-(:Invocation)-[:PRODUCES]->(a:Artefact) "
             "WHERE it.id IN $ids RETURN a")
        return [r["a"]["properties"] for r in self.g.query(q, {"ids": ids})]

    def session_analytics(self, session_id: str = "", top: int = 10) -> dict:
        """Spec 292 — extensive Cypher analytics over the Session Graph.

        ``session_id`` set → a DEEP single-session report (event timeline
        breakdown, tool usage, raw-tool bypass profile, attached Documents,
        intents touched, tick-span). Empty → a CROSS-session aggregate
        (session counts by status, busiest sessions, top tools/events,
        bypass totals). Raw Cypher lives here per the Management read-API
        doctrine (capability verbs delegate to this method).
        """
        g = self.g

        def q(cypher: str, params: Optional[dict] = None) -> list[dict]:
            try:
                return g.query(cypher, params or {})
            except Exception:                                   # noqa: BLE001
                return []

        if session_id:
            sid = session_id if session_id.startswith("session:") else f"session:{session_id}"
            sess = q("MATCH (s:Session) WHERE s.id=$id "
                     "RETURN s.session_id AS sid, s.status AS status", {"id": sid})
            if not sess:
                return {"session_id": session_id, "found": False}
            bare = sess[0]["sid"]
            total = q("MATCH (e:Event)-[:IN_SESSION]->(s:Session) WHERE s.id=$id "
                      "RETURN count(e) AS n", {"id": sid})
            by_event = q("MATCH (e:Event)-[:IN_SESSION]->(s:Session) WHERE s.id=$id "
                         "RETURN e.name AS name, count(e) AS n ORDER BY n DESC", {"id": sid})
            by_tool = q("MATCH (e:Event)-[:IN_SESSION]->(s:Session) "
                        "WHERE s.id=$id AND e.tool IS NOT NULL "
                        "RETURN e.tool AS tool, count(e) AS n ORDER BY n DESC", {"id": sid})
            span = q("MATCH (e:Event)-[:IN_SESSION]->(s:Session) WHERE s.id=$id "
                     "RETURN min(e.vfrom) AS lo, max(e.vfrom) AS hi", {"id": sid})
            bypass = q("MATCH (b:BoundaryUse) WHERE b.session=$s "
                       "RETURN b.verb_shadow AS verb_shadow, count(b) AS n ORDER BY n DESC",
                       {"s": bare})
            docs = q("MATCH (d:Document)-[:IN_SESSION]->(s:Session) WHERE s.id=$id "
                     "RETURN d.id AS id, d.path AS path", {"id": sid})
            intents = q("MATCH (e:Event)-[:IN_SESSION]->(s:Session) WHERE s.id=$id "
                        "MATCH (e)-[:OBSERVED_DURING]->(i:Intent) "
                        "RETURN DISTINCT i.id AS id, i.purpose AS purpose", {"id": sid})
            sp = span[0] if span else {}
            lo, hi = sp.get("lo") or 0, sp.get("hi") or 0
            return {
                "session_id": bare, "status": sess[0]["status"], "found": True,
                "event_count": total[0]["n"] if total else 0,
                "events_by_type": by_event, "tools_used": by_tool,
                "bypass_by_verb_shadow": bypass,
                "bypass_count": sum(r["n"] for r in bypass),
                "documents": docs, "intents": intents,
                "tick_span": {"first": lo, "last": hi, "ticks": hi - lo},
            }

        # cross-session aggregate
        sessions = q("MATCH (s:Session) RETURN s.status AS status, count(s) AS n ORDER BY n DESC")
        busiest = q("MATCH (e:Event)-[:IN_SESSION]->(s:Session) "
                    "RETURN s.session_id AS session_id, count(e) AS n ORDER BY n DESC "
                    f"LIMIT {int(top)}")
        top_tools = q("MATCH (e:Event) WHERE e.tool IS NOT NULL "
                      "RETURN e.tool AS tool, count(e) AS n ORDER BY n DESC "
                      f"LIMIT {int(top)}")
        by_event = q("MATCH (e:Event) RETURN e.name AS name, count(e) AS n ORDER BY n DESC")
        total_bypass = q("MATCH (b:BoundaryUse) RETURN count(b) AS n")
        bypass_by_tool = q("MATCH (b:BoundaryUse) WHERE b.tool IS NOT NULL "
                           "RETURN b.tool AS tool, count(b) AS n ORDER BY n DESC")
        return {
            "session_id": "", "scope": "all-sessions",
            "session_count": sum(r["n"] for r in sessions),
            "sessions_by_status": sessions,
            "busiest_sessions": busiest,
            "top_tools": top_tools, "events_by_type": by_event,
            "total_bypasses": total_bypass[0]["n"] if total_bypass else 0,
            "bypass_by_tool": bypass_by_tool,
        }

    def has_edge(self, src_id: str, dst_id, edge: str,
                 src_label: Optional[str] = None,
                 dst_label: Optional[str] = None) -> bool:
        """True iff a ``src_id`` --``edge``--> ``dst_id`` relationship exists.

        Spec 286 A1 — the boolean guard several verbs run before recording a
        cross-edge (delegate.join's "serves the current intent", gate's
        lifecycle-serves-intent). ``dst_id`` may be one id or a collection
        (e.g. the SUPERSEDED_BY chain). Optional endpoint labels tighten the
        match.
        """
        sp = f"(a:{src_label})" if src_label else "(a)"
        dp = f"(b:{dst_label})" if dst_label else "(b)"
        ids = list(dst_id) if isinstance(dst_id, (list, set, tuple)) else [dst_id]
        q = (f"MATCH {sp}-[:{edge}]->{dp} "
             f"WHERE a.id = $src AND b.id IN $dst RETURN b LIMIT 1")
        return bool(self.g.query(q, {"src": src_id, "dst": ids}))

    def validate(self, node_id: str, predicate) -> bool:
        props = self.recall(node_id)
        return bool(props) and bool(predicate(props))

    def validate_schema(self, node_id: str, schema_id: str) -> bool:
        """Check a node against a Schema node's `required` fields (comma-joined).
        The typed layer: a Schema powers `validate`; pairs with a Template that
        powers `act` (generate). Both are ordinary nodes in the one graph."""
        node = self.recall(node_id)
        schema = self.recall(schema_id)
        if not node or not schema:
            return False
        required = [f.strip() for f in str(schema.get("required", "")).split(",") if f.strip()]
        return all(node.get(f) not in (None, "") for f in required)

    def validate_schema_draft07(self, node_id: str, schema_id: str) -> bool:
        """Validate a node against a draft-07 schema stored on a Schema node.

        Spec 032 §C (panel F-3 resolution — two methods, not internal dispatch).
        The Schema node MUST carry a `schema_json` field holding the JSON-encoded
        draft-07 schema; if absent, raises RuntimeError (caller used the wrong
        tool for the schema shape — should call `validate_schema` for simple
        `{required: csv}` shapes).

        Returns True iff the node's properties satisfy the draft-07 schema.
        False on missing node/schema OR on validation failure (ValidationError
        is caught + converted; the boolean IS the verdict).

        Inputs:
          - node_id: graph node id to validate
          - schema_id: Schema node id (must carry schema_json field)
        Returns: bool
        Raises: RuntimeError if schema node lacks schema_json.
        chain_next: terminal — the boolean is the verdict.
        """
        node = self.recall(node_id)
        schema = self.recall(schema_id)
        if not node or not schema:
            return False
        schema_json_str = schema.get("schema_json")
        if not schema_json_str:
            raise RuntimeError(
                f"schema {schema_id!r} lacks `schema_json` field — call "
                f"`validate_schema` instead (simple-shape schemas) OR add a "
                f"`schema_json` field to the Schema node (draft-07 shape)"
            )
        import json
        try:
            from jsonschema import Draft7Validator, ValidationError
        except ImportError as e:
            raise RuntimeError(
                "validate_schema_draft07 requires the jsonschema library "
                "(pip install jsonschema) — install via `pip install -e .[novel]`"
            ) from e
        try:
            schema_obj = json.loads(schema_json_str)
            validator = Draft7Validator(schema_obj)
            # Strip internal graph fields (id, vfrom, vto, labels) before
            # validating — they're substrate, not user data.
            user_props = {k: v for k, v in node.items()
                          if k not in ("id", "vfrom", "vto", "labels")}
            validator.validate(user_props)
            return True
        except ValidationError:
            return False
        except json.JSONDecodeError:
            return False

    def project(self, label: str, budget: int, as_of: Optional[int] = None) -> list[dict]:
        """Ranked, budget-capped deltas — never raw history. Recency rank here."""
        rows = self.find(label, as_of=as_of)
        rows.sort(key=lambda p: p["vfrom"], reverse=True)
        return rows[:budget]

    def _intent_chain(self, intent_id: str) -> set:
        """All versions of one logical Intent — `amend` forks a new id linked by
        SUPERSEDED_BY, so provenance must gather across the whole chain (both
        directions) or it fragments after an amend."""
        seen, frontier = {intent_id}, [intent_id]
        while frontier:
            cur = frontier.pop()
            for cy in ("MATCH (a:Intent)-[:SUPERSEDED_BY]->(b:Intent) WHERE a.id = $id RETURN b",
                       "MATCH (b:Intent)-[:SUPERSEDED_BY]->(a:Intent) WHERE a.id = $id RETURN b"):
                for r in self.g.query(cy, {"id": cur}):
                    bid = r["b"]["properties"].get("id")
                    if bid and bid not in seen:
                        seen.add(bid)
                        frontier.append(bid)
        return seen

    # --- the moat: cross-concern provenance in one traversal -----------------
    def provenance(self, intent_id: str) -> dict[str, list[dict]]:
        chain = self._intent_chain(intent_id)

        def collect(cypher: str, key: str) -> list[dict]:
            out, seen = [], set()
            for iid in chain:
                for r in self.g.query(cypher, {"iid": iid}):
                    p = r[key]["properties"]
                    k = p.get("id") or id(p)
                    if k not in seen:
                        seen.add(k)
                        out.append(p)
            return out

        def dedup(items: list[dict]) -> list[dict]:
            out, seen = [], set()
            for p in items:
                k = p.get("id") or id(p)
                if k not in seen:
                    seen.add(k)
                    out.append(p)
            return out

        serves = collect("MATCH (i:Intent)<-[:SERVES]-(x) WHERE i.id = $iid RETURN x", "x")
        # an agent reaches an intent two ways: it PERFORMED_BY an invocation, or a
        # Lifecycle was DISPATCHED_TO it before any invocation recorded — collect both.
        agents = dedup(
            collect("MATCH (i:Intent)<-[:SERVES]-(x)-[:PERFORMED_BY]->(a:Agent) "
                    "WHERE i.id = $iid RETURN a", "a")
            + collect("MATCH (i:Intent)<-[:SERVES]-(:Lifecycle)-[:DISPATCHED_TO]->(a:Agent) "
                      "WHERE i.id = $iid RETURN a", "a"))
        # an artefact is either PRODUCED by an invocation or linked to the intent
        # directly via SERVES (e.g. a delegation reduction) — collect both.
        artefacts = dedup(
            collect("MATCH (i:Intent)<-[:SERVES]-(x)-[:PRODUCES]->(p:Artefact) "
                    "WHERE i.id = $iid RETURN p", "p")
            + collect("MATCH (i:Intent)<-[:SERVES]-(p:Artefact) WHERE i.id = $iid RETURN p", "p"))
        # both gate outcomes: PASSED and BLOCKED_ON (a rejected gate is provenance too)
        gates = collect("MATCH (i:Intent)<-[:SERVES]-(:Lifecycle)-[:PASSED]->(g:Gate) "
                        "WHERE i.id = $iid RETURN g", "g")
        gates += collect("MATCH (i:Intent)<-[:SERVES]-(:Lifecycle)-[:BLOCKED_ON]->(g:Gate) "
                         "WHERE i.id = $iid RETURN g", "g")
        return {"serves": serves, "agents": agents, "artefacts": artefacts, "gates": gates}

    # --- whole-graph surgery (Spec 286 A1 — the dogfood export/import surface)
    # These expose the FULL bi-temporal graph (every label, every version) +
    # bi-temporal-EXACT writes that bypass record()'s clock tick. Used only by
    # dogfood.export/import for merge-conflict recovery; raw `.g` access for
    # them lives here, not in the capability.

    def all_nodes(self) -> list[dict]:
        """Every node in the graph as ``{id, label, properties}`` (Spec 286 A1).

        FULL bi-temporal history — superseded versions alongside current ones,
        which is what replay needs to reconstruct the timeline. ``properties``
        excludes the redundant ``id`` key (it's lifted to the top level).
        """
        out: list[dict] = []
        for r in self.g.query("MATCH (n) RETURN n"):
            n = r["n"]
            props = n.get("properties", {})
            labels = n.get("labels")
            label = (labels[0] if isinstance(labels, list) and labels
                     else n.get("label", ""))
            out.append({
                "id": props.get("id", ""),
                "label": label,
                "properties": {k: v for k, v in props.items() if k != "id"},
            })
        return out

    def all_edges(self) -> list[dict]:
        """Every edge as ``{from, to, type, properties}`` (Spec 286 A1)."""
        out: list[dict] = []
        for r in self.g.query("MATCH (a)-[e]->(b) RETURN a, e, b"):
            edge = r["e"]
            props = edge.get("properties", {}) if isinstance(edge, dict) else {}
            edge_type = (edge.get("type") or edge.get("rel_type")
                         or (edge.get("relationship") if isinstance(edge, dict) else "")
                         or "")
            out.append({
                "from": r["a"].get("properties", {}).get("id", ""),
                "to": r["b"].get("properties", {}).get("id", ""),
                "type": edge_type,
                "properties": props,
            })
        return out

    def node_ids(self) -> set[str]:
        """The set of every node id present (Spec 286 A1 — the import
        de-dup probe)."""
        return {r["n"].get("properties", {}).get("id")
                for r in self.g.query("MATCH (n) RETURN n")}

    def replay_node(self, node_id: str, props: dict, label: str = "Entity") -> None:
        """Direct node write preserving id + bi-temporal window (Spec 286 A1).

        Bypasses ``record()``'s clock tick + ontology gate so an imported
        ``vfrom``/``vto`` survives intact. Replay-only — ordinary writes go
        through ``record``/``update``/``supersede``.
        """
        self.g.upsert_node(node_id, dict(props), label=label)

    def replay_edge(self, src: str, dst: str, props: dict,
                    rel_type: str = "RELATED") -> None:
        """Direct edge write preserving the imported window (Spec 286 A1).
        Replay-only; ordinary edges go through ``link``."""
        self.g.upsert_edge(src, dst, dict(props), rel_type=rel_type)

    def advance_clock(self, tick: int) -> None:
        """Advance the logical clock so it never falls at/behind ``tick``
        (Spec 286 A1). Called after a replay so a subsequent ``record``/``link``
        can't reuse an imported ``vfrom``. Serialized on the same lock."""
        with self._lock:
            if tick >= self._tick:
                self._tick = tick

    def close(self) -> None:
        self.g.close()
