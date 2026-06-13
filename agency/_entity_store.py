"""Spec 289 Slice 2 — the canonical SQLite-backed entity store.

Every graph data entity also persists as a typed row in a SQLModel
(``table=True``) table that shares graphqlite's ONE ``.db`` file. The advice
that makes this clean (Spec 289): graphqlite is a SQLite *extension* on a
standard ``sqlite3.Connection``, so a SQLAlchemy engine bound to that SAME
connection (``creator=``) writes the entity table alongside the graph's
extension tables — one database, no second store, no cross-process sync, and
the entity rows are JOIN-able to graph nodes inline (the node id IS the entity
PK). This store is the FastAPI-ready read surface (Slice 3); validation derives
from the ontology via ``EntityModels`` (Slice 1).

This slice is ADDITIVE — ``Memory`` is not yet wired to it (Slice 2b), so the
live record path is unchanged.
"""
from __future__ import annotations

import sqlite3
from typing import Any, Optional

from sqlalchemy import Column, select
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import JSON
from sqlmodel import Field, Session, SQLModel, create_engine

OPEN = 10 ** 12  # mirrors Memory.OPEN — the bi-temporal "currently valid" sentinel

# Substrate fields stamped on the graph node; the entity row carries the user
# data in `data` + the bi-temporal window in its own columns, not inside `data`.
_SUBSTRATE = ("id", "vfrom", "vto", "labels")


class EntityRecord(SQLModel, table=True):
    """One canonical row per graph data entity. ``id`` == the graph node id
    (the link); ``data`` holds the validated user props as JSON; the
    bi-temporal window mirrors the node's. FastAPI models read this row."""

    __tablename__ = "agency_entity"

    id: str = Field(primary_key=True)
    label: str = Field(index=True)
    data: dict = Field(default_factory=dict, sa_column=Column(JSON))
    vfrom: int = 0
    vto: int = OPEN


class EntityStore:
    """OOP handle over the canonical entity table. Bind it to the SAME SQLite
    database as the graph — pass ``sqlite_connection=memory.g._conn.sqlite_connection``
    for one shared DB (incl. ``:memory:``), or a ``path`` for a standalone file.
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
        SQLModel.metadata.create_all(self._engine, tables=[EntityRecord.__table__])

    @staticmethod
    def _clean(props: dict) -> dict:
        return {k: v for k, v in props.items() if k not in _SUBSTRATE}

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

    def count(self) -> int:
        with Session(self._engine) as s:
            return len(s.exec(select(EntityRecord)).all())
