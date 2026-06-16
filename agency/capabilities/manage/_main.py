# agency-scaffold: v1
"""manage — generic CRUD over every graph node type (Spec 293).

The write/read management surface that completes the Memory pillar: a single,
capability-AGNOSTIC CRUD over EVERY ontology label, so every aspect of the
graph — Document, Intent, Track, Novel, Reflection, Session, … — has Create,
Read, Update, Amend and Retract without per-capability code. Complements the
read-only Spec 290 read-API; this is the write half the four pillars need.

Use when: an agent must directly create / read / update / amend / soft-delete a
graph node of any type, without dropping to raw Cypher or a bespoke verb.
Triggers:
- A node's state must change but no domain verb covers it
- A typed entity must be created or queried generically
- An obsolete node must be retracted without destroying history
Red flags:
- Hand-writing `ctx.memory.g.query` in a verb → use manage.list / manage.read
- Destructively deleting a node → use manage.retract (bi-temporal soft delete)
"""
from __future__ import annotations

import json

from ...capability import CapabilityBase, verb


def _parse_props(props) -> dict:
    """Accept a dict or a JSON string (the CLI/wire passes strings)."""
    if isinstance(props, dict):
        return props
    if isinstance(props, str) and props.strip():
        try:
            loaded = json.loads(props)
            return loaded if isinstance(loaded, dict) else {}
        except ValueError:
            return {}
    return {}


class ManageCapability(CapabilityBase):
    name = "manage"
    home = "memory"   # reads/writes the existing graph; no new node types

    @verb(role="effect")
    def create(self, label: str, props=None) -> dict:
        """CREATE a node of any ontology ``label``; SERVES the intent (Spec 293).

        Inputs: label (str — an ontology node label), props (dict|json-str —
                the node's properties; validated against the ontology).
        Returns: ``{id, label}`` or ``{error}`` on an ontology violation.
        chain_next: manage.read(id) to confirm; manage.update to mutate.
        """
        p = _parse_props(props)
        try:
            nid = self.ctx.record_and_serve(label, p)
        except ValueError as exc:
            return {"error": str(exc), "label": label}
        return {"id": nid, "label": label}

    @verb(role="act")
    def read(self, node_id: str) -> dict:
        """READ a node by id — its current properties + a ``live`` flag
        (False once retracted; Spec 293).

        Inputs: node_id (str).
        Returns: ``{id, labels, live, props}`` or ``{error}`` if absent.
        chain_next: manage.update / manage.amend / manage.retract.
        """
        props = self.ctx.recall(node_id)
        if props is None:
            return {"error": f"no node {node_id!r}", "id": node_id}
        live = props.get("vto", 10 ** 12) >= 10 ** 12
        return {"id": node_id, "labels": self.ctx.labels_of(node_id),
                "live": live,
                "props": {k: v for k, v in props.items()
                          if k not in ("vfrom", "vto")}}

    @verb(role="act")
    def list(self, label: str, where=None, live_only: bool = True) -> dict:
        """LIST nodes of a ``label``, optionally filtered by exact-match
        ``where`` (Spec 293). ``live_only`` drops retracted/closed versions.

        Inputs: label (str), where (dict|json-str — exact property match),
                live_only (bool — current-valid only).
        Returns: ``{label, count, rows}``.
        chain_next: manage.read(id) for one, or manage.update to mutate.
        """
        w = _parse_props(where) or None
        rows = self.ctx.query_nodes(label, where=w)
        if live_only:
            rows = [r for r in rows if r.get("vto", 10 ** 12) >= 10 ** 12]
        clean = [{k: v for k, v in r.items() if k not in ("vfrom", "vto")}
                 for r in rows]
        return {"label": label, "count": len(clean), "rows": clean}

    @verb(role="effect")
    def update(self, node_id: str, props=None) -> dict:
        """UPDATE a node in place — a bi-temporal revision, stable id (Spec 293).

        Inputs: node_id (str), props (dict|json-str — merged onto the node).
        Returns: ``{id, updated}`` or ``{error}``.
        chain_next: manage.read(id) to confirm.
        """
        p = _parse_props(props)
        try:
            self.ctx.update(node_id, p)
        except (KeyError, ValueError) as exc:
            return {"error": str(exc), "id": node_id}
        return {"id": node_id, "updated": sorted(p)}

    @verb(role="effect")
    def amend(self, node_id: str, changes=None) -> dict:
        """AMEND append-only — close the old version, create a new one linked
        ``SUPERSEDED_BY`` (Spec 293). For entities that must keep full history.

        Inputs: node_id (str), changes (dict|json-str).
        Returns: ``{old_id, new_id}`` or ``{error}``.
        chain_next: manage.read(new_id); the old id remains queryable as history.
        """
        c = _parse_props(changes)
        try:
            new_id = self.ctx.supersede(node_id, c)
        except (KeyError, ValueError) as exc:
            return {"error": str(exc), "id": node_id}
        return {"old_id": node_id, "new_id": new_id}

    @verb(role="effect")
    def retract(self, node_id: str) -> dict:
        """RETRACT — bi-temporal SOFT delete: close the node's valid window so
        current reads drop it, history retained (Spec 293). Never destructive.

        Inputs: node_id (str).
        Returns: ``{id, retracted, as_of}`` or ``{error}``.
        chain_next: manage.read(id) → ``live: False``; manage.list excludes it.
        """
        try:
            tick = self.ctx.retract(node_id)
        except KeyError as exc:
            return {"error": str(exc), "id": node_id}
        return {"id": node_id, "retracted": True, "as_of": tick}
