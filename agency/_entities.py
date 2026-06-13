"""Spec 288 — SQLModel typed entities derived from the graph ontology.

The ontology (`Ontology.nodes` = label→required fields, `Ontology.enums` =
(label,field)→allowed set) is the schema authority. This module DERIVES a
SQLModel model per node label from it — rule 2 (derive, don't duplicate): no
hand-authored parallel schema. Slice 1 is the validation layer (``table=False``
Pydantic models — the typed, FastAPI-ready surface); ``validate`` has parity
with ``Ontology.violations``. The canonical ``table=True`` store on graphqlite's
shared SQLite connection is Slice 2 (the graph node id is the entity PK).
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import create_model
from sqlmodel import SQLModel

# Stamped by Memory; not user data. The derived models allow extras (a node
# carries optional fields + these), so validation keys only off the ontology.
SUBSTRATE_FIELDS = ("id", "vfrom", "vto", "labels")


class EntityModels:
    """Registry that derives + caches one SQLModel validation model per ontology
    node label. The OOP handle over the typed entity surface:

    - ``model_for(label)`` → the derived ``SQLModel`` class (FastAPI-ready).
    - ``validate(label, props)`` → violation strings, parity with
      ``Ontology.violations`` (the established schema semantics).
    - ``dump(label, props)`` → validated dict (raises on violation) — the
      typed-construction entrypoint a writer uses before ``Memory.record``.
    """

    def __init__(self, ont: Any) -> None:
        self._ont = ont
        self._cache: dict[str, type[SQLModel]] = {}

    # --- derivation --------------------------------------------------------
    def _enums_for(self, label: str) -> dict[str, set]:
        return {fld: set(allowed)
                for (lbl, fld), allowed in self._ont.enums.items() if lbl == label}

    def model_for(self, label: str) -> type[SQLModel]:
        """The cached ``SQLModel`` (``table=False``) for ``label`` — required
        fields from ``ontology.nodes``, enum fields ``Literal``-typed from
        ``ontology.enums``. Unknown label still yields a permissive model."""
        if label not in self._cache:
            self._cache[label] = self._build(label)
        return self._cache[label]

    def _build(self, label: str) -> type[SQLModel]:
        required = list(self._ont.nodes.get(label, []))
        enums = self._enums_for(label)
        fields: dict[str, tuple] = {}
        for f in required:
            if f in enums:                                 # required + closed enum
                fields[f] = (Literal[tuple(sorted(enums[f]))], ...)
            else:                                          # required, untyped value
                fields[f] = (Any, ...)
        for fld, allowed in enums.items():                 # optional enum fields
            if fld not in fields:
                fields[fld] = (Optional[Literal[tuple(sorted(allowed))]], None)
        model: type[SQLModel] = create_model(           # type: ignore[call-overload]
            f"{label}Entity", __base__=SQLModel, **fields)
        # a graph node legitimately carries optional + substrate fields
        model.model_config["extra"] = "allow"
        model.__agency_label__ = label                  # type: ignore[attr-defined]
        model.__agency_required__ = required            # type: ignore[attr-defined]
        model.__agency_enums__ = enums                  # type: ignore[attr-defined]
        return model

    # --- validation (parity with Ontology.violations) ----------------------
    def validate(self, label: str, props: dict) -> list[str]:
        """Violation strings ([] = valid). Parity with ``Ontology.violations``:
        an unknown label, a missing/empty required field (ontology treats
        ``""``/``None`` as missing), and an out-of-enum value each emit one
        string. The derived model is the typed surface; this enforces the
        established ontology semantics on top of it."""
        if label not in self._ont.nodes:
            return [f"unknown node label {label!r} (not in the ontology)"]
        self.model_for(label)                            # ensure derivable
        out = [f"missing required {f!r}"
               for f in self._ont.nodes.get(label, []) if props.get(f) in (None, "")]
        for fld, allowed in self._enums_for(label).items():
            if fld in props and props[fld] not in allowed:
                out.append(f"{fld}={props[fld]!r} not in {sorted(allowed)}")
        return out

    def dump(self, label: str, props: dict) -> dict:
        """Validate + return the cleaned dict (raises ``ValueError`` on
        violation) — the typed-construction entrypoint before ``Memory.record``."""
        bad = self.validate(label, props)
        if bad:
            raise ValueError(f"{label} entity violates ontology: {bad}")
        return dict(props)
