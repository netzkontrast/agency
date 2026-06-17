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
from ...memory import OPEN as _OPEN  # the substrate's bi-temporal "currently-valid" sentinel


def _strip_temporal(props: dict) -> dict:
    """A node's user properties without the bi-temporal window fields."""
    return {k: v for k, v in props.items() if k not in ("vfrom", "vto")}


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
    def create(self, label: str, props: dict | None = None) -> dict:
        """CREATE a node of any ontology ``label`` that SERVES the intent (Spec 293).

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
        live = props.get("vto", _OPEN) >= _OPEN
        return {"id": node_id, "labels": self.ctx.labels_of(node_id),
                "live": live, "props": _strip_temporal(props)}

    @verb(role="act")
    def list(self, label: str, where: dict | None = None, live_only: bool = True) -> dict:
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
            rows = [r for r in rows if r.get("vto", _OPEN) >= _OPEN]
        clean = [_strip_temporal(r) for r in rows]
        return {"label": label, "count": len(clean), "rows": clean}

    @verb(role="effect")
    def update(self, node_id: str, props: dict | None = None) -> dict:
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
    def amend(self, node_id: str, changes: dict | None = None) -> dict:
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

    # ── Spec 290 read-API, folded onto manage (read + write, one capability) ──

    def _live(self, rows: list[dict]) -> list[dict]:
        return [r for r in rows if r.get("vto", _OPEN) >= _OPEN]

    @verb(role="act")
    def state(self, for_intent_id: str = "") -> dict:
        """STATE rollup — the "where are we" dashboard (Spec 290, on manage).

        Cross-pillar current state: live counts of Intents / Reflections /
        Artefacts and Lifecycles grouped by state. With ``intent_id``, also the
        size of its ``SERVES`` subtree + artefacts produced under it.

        Inputs: for_intent_id (str — optional; scopes the rollup to one intent).
        Returns: ``{intents, reflections, artefacts, lifecycles_by_state, …}``.
        chain_next: manage.open_intents / manage.timeline to drill in.
        """
        lc_by_state: dict = {}
        for lc in self._live(self.ctx.find("Lifecycle")):
            st = lc.get("state", "?")
            lc_by_state[st] = lc_by_state.get(st, 0) + 1
        out = {
            "intents": len(self._live(self.ctx.find("Intent"))),
            "reflections": len(self._live(self.ctx.find("Reflection"))),
            "artefacts": len(self._live(self.ctx.find("Artefact"))),
            "lifecycles_by_state": lc_by_state,
        }
        if for_intent_id and self.ctx.recall_typed(for_intent_id, "Intent") is not None:
            out["intent_id"] = for_intent_id
            out["serves_count"] = len(self.ctx.nodes_serving(for_intent_id))
            out["artefacts_under"] = len(self.ctx.artefacts_produced_under(for_intent_id))
        return out

    @verb(role="act")
    def open_intents(self, top: int = 20) -> dict:
        """OPEN-INTENTS — live intents + acceptance + SERVES subtree size,
        busiest first (Spec 290, Intent pillar).

        Inputs: top (int — how many busiest intents to return).
        Returns: ``{count, intents: [{id, purpose, acceptance, status,
                   serves_count}]}``.
        chain_next: manage.timeline(intent_id) for an intent's event order.
        """
        rows = []
        for i in self._live(self.ctx.find("Intent")):
            iid = i["id"]
            rows.append({"id": iid, "purpose": i.get("purpose", ""),
                         "acceptance": i.get("acceptance", ""),
                         "status": i.get("status", ""),
                         "serves_count": len(self.ctx.nodes_serving(iid))})
        rows.sort(key=lambda r: r["serves_count"], reverse=True)
        return {"count": len(rows), "intents": rows[:top]}

    @verb(role="act")
    def timeline(self, for_intent_id: str, limit: int = 100) -> dict:
        """TIMELINE — the ordered Event + Invocation history for an intent
        (Spec 290, Lifecycle · Memory).

        Inputs: for_intent_id (str — the Intent id), limit (int — max events).
        Returns: ``{intent_id, count, timeline: [{kind, name, at}]}`` ordered
        by valid-time.
        chain_next: manage.artefacts(intent_id) for what it produced.
        """
        if self.ctx.recall_typed(for_intent_id, "Intent") is None:
            return {"error": f"{for_intent_id!r} is not an Intent id",
                    "intent_id": for_intent_id, "count": 0, "timeline": []}
        items = []
        for e in self.ctx.sources_via_edge("OBSERVED_DURING", for_intent_id,
                                           "Intent", label="Event"):
            items.append({"kind": "event", "name": e.get("name", ""),
                          "tool": e.get("tool", ""), "at": e.get("vfrom", 0)})
        for v in self.ctx.nodes_serving(for_intent_id, "Invocation"):
            items.append({"kind": "invocation",
                          "name": f"{v.get('capability', '')}.{v.get('verb', '')}",
                          "at": v.get("vfrom", 0)})
        items.sort(key=lambda x: x["at"])
        return {"intent_id": for_intent_id, "count": len(items),
                "timeline": items[:limit]}

    @verb(role="act")
    def artefacts(self, for_intent_id: str) -> dict:
        """ARTEFACTS produced under an intent + their source invocations
        (Spec 290, Memory pillar).

        Inputs: for_intent_id (str — the Intent id).
        Returns: ``{intent_id, count, artefacts: [props]}``.
        chain_next: manage.read(id) for one artefact's full state.
        """
        if self.ctx.recall_typed(for_intent_id, "Intent") is None:
            return {"error": f"{for_intent_id!r} is not an Intent id",
                    "intent_id": for_intent_id, "count": 0, "artefacts": []}
        arts = self.ctx.artefacts_produced_under(for_intent_id)
        clean = [_strip_temporal(a) for a in arts]
        return {"intent_id": for_intent_id, "count": len(clean), "artefacts": clean}
