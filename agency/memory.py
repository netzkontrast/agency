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

    # --- write axis: record · link · supersede -------------------------------
    def record(self, label: str, props: dict[str, Any], node_id: Optional[str] = None) -> str:
        bad = self.ont.violations(label, props)
        if bad:
            raise ValueError(f"{label} record violates ontology: {bad}")
        nid = node_id or f"{label.lower()}:{uuid.uuid4().hex[:8]}"
        data = {**props, "vfrom": self._now(), "vto": OPEN}
        self.g.upsert_node(nid, data, label=label)
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
        self.g.upsert_node(node_id, merged, label=label)

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
        self.g.upsert_node(node_id, {**old, "vto": now}, label=label)
        new_id = f"{node_id}#{now}"
        new_props.update({"vfrom": now, "vto": OPEN})
        self.g.upsert_node(new_id, new_props, label=label)
        self.link(node_id, new_id, "SUPERSEDED_BY")
        return new_id

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

    def close(self) -> None:
        self.g.close()
