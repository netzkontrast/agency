"""Spec 289 Slice 2 — the graph-authoritative typed projection.

Every graph data entity is MIRRORED into a typed row in a SQLModel
(``table=True``) table that shares graphqlite's ONE ``.db`` file. The advice
that makes this clean (Spec 289): graphqlite is a SQLite *extension* on a
standard ``sqlite3.Connection``, so a SQLAlchemy engine bound to that SAME
connection (``creator=``) writes the entity table alongside the graph's
extension tables — one database, no second store, no cross-process sync, and
the entity rows are JOIN-able to graph nodes inline (the node id IS the entity
PK). This store is the FastAPI-ready read surface (Slice 3); validation derives
from the ontology via ``EntityModels`` (Slice 1).

The graph node stays write-authoritative (provenance, bi-temporal history,
ontology enforcement); this projection is a ONE-WAY mirror FROM the graph
(graph → entity row, never the inverse) — re-derivable, never a parallel
tracking system. ``Memory`` mirrors here AFTER each authoritative graph write
(Slice 2b); a projection failure never fails the graph write.
"""
from __future__ import annotations

import sqlite3
from typing import Optional

from sqlalchemy import Column, select
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import JSON
from sqlmodel import Field, Session, SQLModel, create_engine

OPEN = 10 ** 12  # mirrors Memory.OPEN — the bi-temporal "currently valid" sentinel

# Substrate fields stamped on the graph node; the entity row carries the user
# data in `data` + the bi-temporal window in its own columns, not inside `data`.
_SUBSTRATE = ("id", "vfrom", "vto", "labels")


class EntityRecord(SQLModel, table=True):
    """One projected row per graph data entity (mirrored from the authoritative
    graph node). ``id`` == the graph node id (the link); ``data`` holds the
    validated user props as JSON; the bi-temporal window mirrors the node's.
    FastAPI models read this row."""

    __tablename__ = "agency_entity"

    id: str = Field(primary_key=True)
    label: str = Field(index=True)
    data: dict = Field(default_factory=dict, sa_column=Column(JSON))
    vfrom: int = 0
    vto: int = OPEN


# --- Spec 327 — the explicit relational typed layer (the four-concept core) ---
#
# Where ``EntityRecord`` is the generic JSON-blob mirror for ANY node, these
# ``table=True`` models give the four-concept CORE entities real columns + real
# foreign keys, so the interweave (Capability · Lifecycle · Memory → Intent) is
# queryable by SQL join, not just a Cypher traversal. They share the same engine
# / connection as ``EntityRecord`` (one DB; node id == PK). Enum VALUES are still
# enforced upstream by the ontology (``EntityModels.validate`` / ``Memory.record``)
# — rule 2: the columns stay plain ``str``, no hand-copied enum here. The new
# typed layer is the RELATIONAL structure the flat ontology can't express (the FKs).
#
# The hot FK columns (``serves_intent_id`` · ``agent_id`` · ``parent_intent_id``)
# are nullable at the schema level on purpose: a node is recorded BEFORE its edges
# (``Memory.record`` then ``Memory.link``), so the row is inserted first and the FK
# is set when the edge lands. The "every Invocation maps to an Intent" invariant is
# a DATA invariant the mirror upholds (and the acceptance suite guards), not a DB
# NOT-NULL that would break the insert-before-edge ordering.


class TypedIntent(SQLModel, table=True):
    """Intent — the human-owned root every concept edges back to (Spec 326)."""

    __tablename__ = "agency_intent"

    id: str = Field(primary_key=True)
    purpose: Optional[str] = None
    deliverable: Optional[str] = None
    acceptance: Optional[str] = None
    status: Optional[str] = Field(default=None, index=True)
    owner: Optional[str] = None
    clarity_score: Optional[float] = None              # Spec 322 (set on confirm)
    parent_intent_id: Optional[str] = Field(           # PARENT_INTENT edge
        default=None, foreign_key="agency_intent.id", index=True)
    vfrom: int = 0
    vto: int = OPEN


class TypedAgent(SQLModel, table=True):
    """Agent — the performer (Capability concept: jules / develop / subagent …).
    The ontology's discriminator field is ``runtime`` (rule 2)."""

    __tablename__ = "agency_agent"

    id: str = Field(primary_key=True)
    runtime: Optional[str] = Field(default=None, index=True)
    vfrom: int = 0
    vto: int = OPEN


class TypedInvocation(SQLModel, table=True):
    """Invocation — every capability verb call, mapped to the Intent it SERVES
    and the Agent that PERFORMED_BY it (Spec 326 §the interweave)."""

    __tablename__ = "agency_invocation"

    id: str = Field(primary_key=True)
    capability: Optional[str] = Field(default=None, index=True)
    verb: Optional[str] = Field(default=None, index=True)
    role: Optional[str] = None
    serves_intent_id: Optional[str] = Field(           # SERVES edge (the mapping)
        default=None, foreign_key="agency_intent.id", index=True)
    agent_id: Optional[str] = Field(                   # PERFORMED_BY edge
        default=None, foreign_key="agency_agent.id", index=True)
    vfrom: int = 0
    vto: int = OPEN


class TypedGate(SQLModel, table=True):
    """Gate — the recorded verdict on whether an Intent is FULFILLED (Spec 328;
    owner directive: the Gate lives in Intent). The clarity gate (capture-time,
    Spec 322), acceptance + completion gates (done-time) all key to their Intent
    via ``intent_id`` (the GATES edge). A Lifecycle-attached gate (``gate.check``)
    has no GATES edge, so its ``intent_id`` stays null — not mis-attributed."""

    __tablename__ = "agency_gate"

    id: str = Field(primary_key=True)
    intent_id: Optional[str] = Field(                  # GATES edge (Intent-owned)
        default=None, foreign_key="agency_intent.id", index=True)
    name: Optional[str] = None
    kind: Optional[str] = Field(default=None, index=True)   # clarity|acceptance|completion
    passed: Optional[bool] = None                      # the ontology's verdict bool
    score: Optional[float] = None
    threshold: Optional[float] = None
    checked_at: Optional[int] = None                   # the logical tick of the check
    vfrom: int = 0
    vto: int = OPEN


class TypedAcceptanceCriterion(SQLModel, table=True):
    """AcceptanceCriterion — what "fulfilled" MEANS (Spec 317). VALIDATES the
    Intent; ``intent_id`` is that edge as a typed FK."""

    __tablename__ = "agency_acceptance_criterion"

    id: str = Field(primary_key=True)
    intent_id: Optional[str] = Field(                  # VALIDATES edge
        default=None, foreign_key="agency_intent.id", index=True)
    text: Optional[str] = None
    gherkin: Optional[str] = None
    measurable: Optional[bool] = None
    vfrom: int = 0
    vto: int = OPEN


class TypedLifecycleState(SQLModel, table=True):
    """Lifecycle — the task/session state machine (Spec 329). Weaves to its Intent
    (``serves_intent_id`` ← SERVES) and the performer (``agent_id``)."""

    __tablename__ = "agency_lifecycle_state"

    id: str = Field(primary_key=True)
    state: Optional[str] = Field(default=None, index=True)
    phase: Optional[str] = None
    serves_intent_id: Optional[str] = Field(
        default=None, foreign_key="agency_intent.id", index=True)
    agent_id: Optional[str] = Field(
        default=None, foreign_key="agency_agent.id", index=True)
    vfrom: int = 0
    vto: int = OPEN


class TypedArtefact(SQLModel, table=True):
    """Artefact — a produced output (Spec 329, Memory). ``produced_by_id`` ←
    PRODUCES (the Invocation that produced it); ``serves_intent_id`` ← SERVES."""

    __tablename__ = "agency_artefact"

    id: str = Field(primary_key=True)
    kind: Optional[str] = Field(default=None, index=True)
    produced_by_id: Optional[str] = Field(
        default=None, foreign_key="agency_invocation.id", index=True)
    serves_intent_id: Optional[str] = Field(
        default=None, foreign_key="agency_intent.id", index=True)
    vfrom: int = 0
    vto: int = OPEN


class TypedEdge(SQLModel, table=True):
    """The Memory provenance SPINE (Spec 329) — every typed edge mirrored, so any
    traversal (GROUNDS · VALIDATES · SUPERSEDED_BY · DISPATCHED_TO · …) is a typed
    query, not just the hot FK columns. ``id`` is the deterministic ``src|rel|dst``
    so a re-link updates the one current row."""

    __tablename__ = "agency_edge"

    id: str = Field(primary_key=True)
    src_id: str = Field(index=True)
    dst_id: str = Field(index=True)
    rel: str = Field(index=True)
    vfrom: int = 0
    vto: int = OPEN


# label → typed model (the router's switchboard). The mirror routes a CORE label
# here IN ADDITION to the generic EntityRecord (additive — no existing reader of
# EntityRecord breaks); a non-core/domain label stays EntityRecord-only.
# AGENCY-DRIFT: typed-core-labels — the set of labels with a typed table.
CORE_TYPED: dict[str, type[SQLModel]] = {
    "Intent": TypedIntent,
    "Agent": TypedAgent,
    "Invocation": TypedInvocation,
    "Gate": TypedGate,
    "AcceptanceCriterion": TypedAcceptanceCriterion,
    "Lifecycle": TypedLifecycleState,
    "Artefact": TypedArtefact,
}

# Columns NEVER written from node props — they are derived from EDGES, set by
# ``set_fk_from_edge`` when the edge lands (so a re-upsert from props can't clobber
# a FK already set by its edge). DERIVED from each model's ``foreign_key`` columns
# (rule 2: the schema's FK declarations are the single source — no hand-copied
# parallel mapping to drift).
_FK_COLUMNS: dict[str, set[str]] = {
    label: {c.name for c in model.__table__.columns if c.foreign_keys}
    for label, model in CORE_TYPED.items()
}

# edge rel → the FK column it sets on the edge's SRC row (value := the edge's DST).
# Every SRC-projected rel is (src)-[rel]->(dst) with the FK living on the src row.
# VALIDATES + GATES both set ``intent_id`` — the src's own table (the only one
# holding a row with id == src) disambiguates which gets it.
# AGENCY-DRIFT: typed-edge-fk — the rels that project onto a typed FK column.
_EDGE_FK_SRC: dict[str, str] = {
    "SERVES": "serves_intent_id",
    "PERFORMED_BY": "agent_id",
    "PARENT_INTENT": "parent_intent_id",
    "VALIDATES": "intent_id",
    "GATES": "intent_id",
}

# edge rel → (FK column on the DST row, required SRC label). REVERSE-direction:
# ``(src)-[rel]->(dst)`` sets the FK on the DST row to ``src`` — but only when the
# src is of the required label. PRODUCES is emitted both Invocation→Artefact AND
# Intent→Artefact; only the former names a real producer, so an Intent-produced
# artefact correctly keeps ``produced_by_id`` null.
_EDGE_FK_DST: dict[str, tuple[str, str]] = {
    "PRODUCES": ("produced_by_id", "Invocation"),
}


class EntityStore:
    """OOP handle over the graph-authoritative typed projection. Bind it to the
    SAME SQLite database as the graph — pass
    ``sqlite_connection=memory.g._conn.sqlite_connection`` for one shared DB
    (incl. ``:memory:``), or a ``path`` for a standalone file. Rows are mirrored
    FROM the graph (one-way); the graph node is authoritative.
    """

    def __init__(self, path: Optional[str] = None, *,
                 sqlite_connection: Optional[sqlite3.Connection] = None) -> None:
        if sqlite_connection is not None:
            # Reuse the graph's exact connection → genuinely one DB. StaticPool
            # keeps the single shared connection (the engine is logically
            # single-threaded, like Memory's clock).
            self._engine = create_engine(
                "sqlite://", creator=lambda: sqlite_connection,
                poolclass=StaticPool)
        else:
            url = "sqlite://" if path in (None, ":memory:") else f"sqlite:///{path}"
            self._engine = create_engine(
                url, connect_args={"check_same_thread": False},
                poolclass=StaticPool)
        tables = ([EntityRecord.__table__, TypedEdge.__table__]
                  + [m.__table__ for m in CORE_TYPED.values()])
        SQLModel.metadata.create_all(self._engine, tables=tables)

    @staticmethod
    def _clean(props: dict) -> dict:
        return {k: v for k, v in props.items() if k not in _SUBSTRATE}

    # --- Spec 327 — the explicit typed-core projection ---------------------
    @staticmethod
    def _row_dict(row: SQLModel) -> dict:
        return {c: getattr(row, c) for c in row.__table__.columns.keys()}

    def upsert_typed(self, node_id: str, label: str, props: dict,
                     vfrom: int = 0, vto: int = OPEN) -> Optional[str]:
        """Mirror a CORE node into its typed table (Spec 327). No-op for a
        non-core label (it stays EntityRecord-only). Props fill the value columns;
        the FK columns (``_FK_COLUMNS``) are left to ``set_fk_from_edge`` — a
        re-upsert from props never clobbers a FK already set by its edge."""
        model = CORE_TYPED.get(label)
        if model is None:
            return None
        cols = set(model.__table__.columns.keys())
        skip = _FK_COLUMNS.get(label, set()) | {"id", "vfrom", "vto"}
        payload = {k: v for k, v in props.items() if k in cols and k not in skip}
        with Session(self._engine) as s:
            row = s.get(model, node_id)
            if row is None:
                row = model(id=node_id, vfrom=vfrom, vto=vto, **payload)
            else:
                for k, v in payload.items():
                    setattr(row, k, v)
                row.vfrom, row.vto = vfrom, vto
            s.add(row)
            s.commit()
        return node_id

    def set_fk_from_edge(self, src: str, dst: str, rel: str) -> None:
        """Set the typed FK column(s) an edge projects onto (Spec 327/329).

        SRC-direction (``_EDGE_FK_SRC``): ``(src)-[rel]->(dst)`` sets the FK on the
        SRC row (value := ``dst``). Only the src's own typed table carries a row
        with ``id == src``, so exactly one row is touched.

        DST-direction (``_EDGE_FK_DST``): the FK lives on the DST row (value :=
        ``src``) — but only when ``src`` is of the required label (so an
        Intent-produced Artefact keeps ``produced_by_id`` null)."""
        col = _EDGE_FK_SRC.get(rel)
        if col is not None:
            self._set_fk(src, col, dst)
        dst_rule = _EDGE_FK_DST.get(rel)
        if dst_rule is not None:
            col, required_src_label = dst_rule
            src_model = CORE_TYPED.get(required_src_label)
            if src_model is not None and self._exists(src_model, src):
                self._set_fk(dst, col, src)

    def _exists(self, model: type[SQLModel], node_id: str) -> bool:
        with Session(self._engine) as s:
            return s.get(model, node_id) is not None

    def _set_fk(self, node_id: str, col: str, value: str) -> None:
        """Set ``col = value`` on whichever core table holds a row with this id.

        One session for the whole probe (a column may live on several tables —
        ``serves_intent_id`` on Invocation/Lifecycle/Artefact — but only the
        node's own table holds a row with ``id == node_id``); the candidate
        ``s.get`` calls are cheap PK lookups, so this is one commit per edge, not
        one per candidate table."""
        candidates = [m for m in CORE_TYPED.values()
                      if col in m.__table__.columns.keys()]
        if not candidates:
            return
        with Session(self._engine) as s:
            for model in candidates:
                row = s.get(model, node_id)
                if row is not None:
                    setattr(row, col, value)
                    s.add(row)
                    s.commit()
                    return

    # --- Spec 329 — the typed Edge spine (every edge, full traversal) ------
    def upsert_edge_row(self, src: str, dst: str, rel: str,
                        vfrom: int = 0, vto: int = OPEN) -> str:
        """Mirror one authoritative graph edge into the typed Edge spine. The id
        is the deterministic ``src|rel|dst`` so a re-link updates the one current
        row (the graph holds full bi-temporal edge history)."""
        eid = f"{src}|{rel}|{dst}"
        with Session(self._engine) as s:
            row = s.get(TypedEdge, eid)
            if row is None:
                row = TypedEdge(id=eid, src_id=src, dst_id=dst, rel=rel,
                                vfrom=vfrom, vto=vto)
            else:
                row.vfrom, row.vto = vfrom, vto
            s.add(row)
            s.commit()
        return eid

    def edge_rows(self) -> list[dict]:
        """All CURRENT (``vto == OPEN``) typed Edge rows as dicts."""
        with Session(self._engine) as s:
            rows = s.exec(select(TypedEdge).where(TypedEdge.vto == OPEN)).all()
            return [self._row_dict(r[0]) for r in rows]

    def edge_row(self, src: str, rel: str, dst: str) -> Optional[dict]:
        with Session(self._engine) as s:
            row = s.get(TypedEdge, f"{src}|{rel}|{dst}")
            return self._row_dict(row) if row is not None else None

    def carry_fks(self, old_id: str, new_id: str, label: str) -> None:
        """On ``supersede``, carry the prior version's edge-derived FK columns
        onto the new version (Spec 326 correctness).

        ``supersede`` mints a NEW node id and only links ``SUPERSEDED_BY`` to it;
        the carried SERVES/PERFORMED_BY/PRODUCES/PARENT_INTENT edges still point at
        the OLD id and are never re-projected. Without this, the new typed row
        (mirrored from props, FK columns skipped) would have NULL FKs and the live
        version would vanish from ``serves``/``provenance``/``intent_tree`` (which
        read ``vto == OPEN``). The new version inherits the same relationships —
        "the what changes while the why holds" — so the live projection stays
        faithful to the graph's SUPERSEDED_BY-chain-aware provenance."""
        model = CORE_TYPED.get(label)
        cols = _FK_COLUMNS.get(label, set())
        if model is None or not cols:
            return
        with Session(self._engine) as s:
            old, new = s.get(model, old_id), s.get(model, new_id)
            if old is None or new is None:
                return
            for c in cols:
                val = getattr(old, c, None)
                if val is not None:
                    setattr(new, c, val)
            s.add(new)
            s.commit()

    def typed_row(self, label: str, node_id: str) -> Optional[dict]:
        """The typed row for a core node as a dict, or ``None``."""
        model = CORE_TYPED.get(label)
        if model is None:
            return None
        with Session(self._engine) as s:
            row = s.get(model, node_id)
            return self._row_dict(row) if row is not None else None

    def typed_rows(self, label: str) -> list[dict]:
        """All CURRENT (``vto == OPEN``) typed rows for a core label, as dicts."""
        model = CORE_TYPED.get(label)
        if model is None:
            return []
        with Session(self._engine) as s:
            rows = s.exec(select(model).where(model.vto == OPEN)).all()
            return [self._row_dict(r[0]) for r in rows]

    def upsert(self, node_id: str, label: str, props: dict,
               vfrom: int = 0, vto: int = OPEN) -> str:
        """Insert or update the entity row keyed by the graph node id. Returns
        the id (the link the graph node carries)."""
        clean = self._clean(props)
        with Session(self._engine) as s:
            rec = s.get(EntityRecord, node_id)
            if rec is None:
                rec = EntityRecord(id=node_id, label=label, data=clean,
                                   vfrom=vfrom, vto=vto)
            else:
                rec.label, rec.data, rec.vfrom, rec.vto = label, clean, vfrom, vto
            s.add(rec)
            s.commit()
        return node_id

    def get(self, node_id: str) -> Optional[dict]:
        """The entity's user data dict, or None. (FastAPI deserialises via the
        EntityModels-derived SQLModel for the label.)"""
        with Session(self._engine) as s:
            rec = s.get(EntityRecord, node_id)
            return dict(rec.data) if rec is not None else None

    def by_label(self, label: str) -> list[dict]:
        """All current entity rows for a label (the FastAPI list surface)."""
        with Session(self._engine) as s:
            rows = s.exec(select(EntityRecord).where(
                EntityRecord.label == label, EntityRecord.vto == OPEN)).all()
            return [dict(r[0].data) for r in rows]

    def entity_join(self, node_ids: "list[str]") -> list[dict]:
        """Spec 289 Slice 2b — inline content query: given graph node ids (e.g.
        from a Cypher id-only query), return each one's mirrored entity content in
        ONE round-trip as ``[{id, label, data}, ...]``. Input order is preserved;
        an id with no row is skipped (not faked). Purely additive — the graph node
        stays authoritative; this only reads the typed mirror."""
        out: list[dict] = []
        with Session(self._engine) as s:
            for nid in node_ids:
                rec = s.get(EntityRecord, nid)
                if rec is not None:
                    out.append({"id": nid, "label": rec.label,
                                "data": dict(rec.data)})
        return out

    def count(self) -> int:
        with Session(self._engine) as s:
            return len(s.exec(select(EntityRecord)).all())


class IntentStore:
    """Spec 330 — the typed-join READ API over the four-concept tables.

    Reads the interweave (Capability · Lifecycle · Memory → Intent) as typed SQL
    queries, not hand-written Cypher — the consumer that makes the FK columns +
    the Edge spine load-bearing (dormant-surface audit). Returns plain dicts
    (FastAPI-serialisable — Goal 5). It is a PROJECTION of the authoritative
    graph; the acceptance suite's parity gate guarantees each method's result
    equals the equivalent Cypher traversal, so the typed read can never silently
    diverge from the moat.
    """

    def __init__(self, store: EntityStore) -> None:
        self._store = store
        self._engine = store._engine

    def _rows(self, model: type[SQLModel], **eq) -> list[dict]:
        with Session(self._engine) as s:
            stmt = select(model).where(model.vto == OPEN)
            for col, val in eq.items():
                stmt = stmt.where(getattr(model, col) == val)
            return [EntityStore._row_dict(r[0]) for r in s.exec(stmt).all()]

    def serves(self, intent_id: str) -> list[dict]:
        """Every capability Invocation mapped to this Intent (the directive's
        core) — one indexed `WHERE serves_intent_id = :id`."""
        return self._rows(TypedInvocation, serves_intent_id=intent_id)

    def intent_tree(self, root_id: str) -> list[dict]:
        """The PARENT_INTENT sub-intent tree rooted at ``root_id`` (inclusive),
        walked over the typed ``parent_intent_id`` FK."""
        root = self._store.typed_row("Intent", root_id)
        if root is None:
            return []
        out, frontier = [root], [root_id]
        seen = {root_id}
        while frontier:
            parent = frontier.pop()
            for child in self._rows(TypedIntent, parent_intent_id=parent):
                if child["id"] not in seen:
                    seen.add(child["id"])
                    out.append(child)
                    frontier.append(child["id"])
        return out

    def provenance(self, intent_id: str) -> dict:
        """The cross-concern join CORE.md names — invocations + their agents +
        produced/serving artefacts + lifecycle state — as one typed query set,
        not a Cypher traversal."""
        invs = self.serves(intent_id)
        inv_ids = {i["id"] for i in invs}
        agent_ids = {i["agent_id"] for i in invs if i.get("agent_id")}
        agents = self._rows_in(TypedAgent, "id", agent_ids)   # one batched query
        artefacts = {a["id"]: a for a in self._rows(TypedArtefact,
                                                    serves_intent_id=intent_id)}
        for a in self._rows_in(TypedArtefact, "produced_by_id", inv_ids):
            artefacts.setdefault(a["id"], a)
        lifecycle = self._rows(TypedLifecycleState, serves_intent_id=intent_id)
        return {"invocations": invs, "agents": agents,
                "artefacts": list(artefacts.values()), "lifecycle": lifecycle}

    def _rows_in(self, model: type[SQLModel], col: str,
                 values: set) -> list[dict]:
        if not values:
            return []
        with Session(self._engine) as s:
            stmt = select(model).where(model.vto == OPEN,
                                       getattr(model, col).in_(values))
            return [EntityStore._row_dict(r[0]) for r in s.exec(stmt).all()]

    def fulfilment(self, intent_id: str) -> dict:
        """Is the Intent fulfilled? The latest Intent-owned Gate verdict (an
        acceptance/completion gate wins over a clarity gate) + the
        AcceptanceCriterion satisfaction (Spec 328) — the typed answer to "are we
        there yet?"."""
        from .ontology import DONE_GATE_KINDS
        gates = self._rows(TypedGate, intent_id=intent_id)
        criteria = self._rows(TypedAcceptanceCriterion, intent_id=intent_id)
        measurable = [c for c in criteria if c.get("measurable")]
        done_gates = [g for g in gates if g.get("kind") in DONE_GATE_KINDS]
        pool = done_gates or gates
        latest = max(pool, key=lambda g: g.get("vfrom") or 0) if pool else None
        return {
            "intent_id": intent_id,
            "fulfilled": bool(latest and latest.get("passed")),
            "verdict_gate": latest,
            "criteria": len(criteria),
            "measurable_criteria": len(measurable),
        }
