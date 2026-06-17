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
from ..._overflow import budget_take  # Spec 286 P3 — shared priority-ordered token-budget split
from ..._tokens import count_tokens   # Spec 082 — the one TokenCounter boundary


def _query_tokens(text: str) -> set:
    import re
    return {t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if t}


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
    def project(self, label: str, query: str = "", budget: int = 2000) -> dict:
        """PROJECT — a query-ranked, token-budgeted slice of a label's live nodes
        (Spec 290/293: the `project(query, budget)` read primitive, Goal 1).

        Ranks live ``label`` nodes by overlap with ``query`` (most-relevant
        first; recency breaks ties), then returns the highest-priority prefix
        that fits under ``budget`` tokens — a bounded delta, never a raw dump
        (rule 2). Read-only; composes the shared ``budget_take`` split + the
        Spec 082 token counter.

        A budget smaller than the single highest-ranked row yields ``rows: []``
        with ``truncated: True`` (the bounded-delta contract — the caller raises
        the budget or reads the row by id); it never partial-writes a node.

        Inputs: label (str — ontology label), query (str — optional relevance
                terms), budget (int — max tokens of returned rows).
        Returns: ``{label, query, budget, total, returned, returned_tokens,
                   truncated, rows}``.
        chain_next: manage.read(id) for one row's full state.
        """
        rows = [_strip_temporal(r) for r in self._live(self.ctx.find(label))]
        qt = _query_tokens(query)
        if qt:
            def _overlap(r):
                blob = " ".join(str(v) for v in r.values())
                return len(qt & _query_tokens(blob))
            rows.sort(key=lambda r: (-_overlap(r), -int(r.get("vfrom", 0) or 0)))
        else:
            rows.sort(key=lambda r: -int(r.get("vfrom", 0) or 0))

        def _cost(r):
            return count_tokens(json.dumps(r, default=str, sort_keys=True))

        kept, skipped = budget_take(rows, _cost, budget)
        returned_tokens = sum(_cost(r) for r in kept)
        return {"label": label, "query": query, "budget": budget,
                "total": len(rows), "returned": len(kept),
                "returned_tokens": returned_tokens,
                "truncated": bool(skipped), "rows": kept}

    @verb(role="act")
    def render(self, for_intent_id: str = "", top: int = 5) -> dict:
        """RENDER the read-API as a compact markdown dashboard — the "where are
        we" view, rule-2 graph→markdown on demand (Spec 290 Slice 2).

        Composes ``state`` + ``open_intents`` (and, when an intent is named,
        ``whats_next``) into one human-readable projection. Read-only: it calls
        the sibling read verbs, never writes.

        Inputs: for_intent_id (str — optional; adds the intent's next/blocked
                section), top (int — open-intents rows to list).
        Returns: ``{view, markdown}``.
        chain_next: manage.timeline(intent_id) / manage.artefacts(intent_id).
        """
        st = self.state(for_intent_id=for_intent_id)
        lc = st.get("lifecycles_by_state", {})
        lc_line = ", ".join(f"{k}: {v}" for k, v in sorted(lc.items())) or "none"
        lines = [
            "# Agency Dashboard",
            "",
            f"**State:** {st['intents']} intents · {st['reflections']} "
            f"reflections · {st['artefacts']} artefacts",
            f"**Lifecycles:** {lc_line}",
            "",
            f"## Open intents (top {top})",
        ]
        opened = self.open_intents(top=top)
        if opened["intents"]:
            for i in opened["intents"]:
                purpose = i.get("purpose", "") or "(no purpose)"
                lines.append(f"- `{i['id']}` — {purpose} "
                             f"(serves {i['serves_count']})")
        else:
            lines.append("- (none)")

        if for_intent_id and self.ctx.recall_typed(for_intent_id, "Intent") is not None:
            nxt = self.whats_next(for_intent_id=for_intent_id)
            lines += ["", f"## Intent `{for_intent_id}`",
                      f"**Acceptance:** {nxt.get('acceptance', '')}",
                      f"**Status:** {nxt.get('status', '')} · "
                      f"done: {nxt.get('done', False)}", "", "**Next:**"]
            actions = nxt.get("next", [])
            if actions:
                for a in actions:
                    lines.append(f"- {a.get('action') or a.get('phase') or a.get('state') or a}")
            else:
                lines.append("- (nothing pending)")
            blocked = nxt.get("blocked", [])
            if blocked:
                lines.append("")
                lines.append("**Blocked:**")
                for b in blocked:
                    lines.append(f"- {b.get('name') or b.get('state') or b.get('kind')}")
        return {"view": "dashboard", "markdown": "\n".join(lines)}

    @verb(role="act")
    def whats_next(self, for_intent_id: str) -> dict:
        """WHATS-NEXT — blocked items + the next actions against an intent's
        acceptance (Spec 290, Lifecycle pillar; the navigate core).

        Reads the Lifecycles + Gates serving the intent: anything awaiting
        input/auth or failed (or an explicit ``BLOCKED_ON`` dependency) is
        ``blocked``; anything still submitted/working is in flight; with
        neither and the acceptance unmet, the acceptance itself is surfaced as
        the next action.

        Inputs: for_intent_id (str — the Intent id).
        Returns: ``{intent_id, acceptance, status, done, blocked, next}``.
        chain_next: manage.timeline(intent_id) for the full event order.
        """
        intent = self.ctx.recall_typed(for_intent_id, "Intent")
        if intent is None:
            return {"error": f"{for_intent_id!r} is not an Intent id",
                    "intent_id": for_intent_id, "blocked": [], "next": []}
        lifecycles = self._live(self.ctx.nodes_serving(for_intent_id, "Lifecycle"))
        gates = self._live(self.ctx.nodes_serving(for_intent_id, "Gate"))

        blocked_states = {"input-required", "auth-required", "failed"}
        active_states = {"submitted", "working"}
        done_states = {"completed", "canceled"}

        blocked: list = []
        for lc in lifecycles:
            if lc.get("state") in blocked_states:
                blocked.append({"kind": "lifecycle", "id": lc.get("id"),
                                "state": lc.get("state"), "phase": lc.get("phase", "")})
        for g in gates:
            if not g.get("passed"):
                blocked.append({"kind": "gate", "id": g.get("id"),
                                "name": g.get("name", "")})
        for dep in self.ctx.neighbors(for_intent_id, "BLOCKED_ON", direction="out"):
            blocked.append({"kind": "dependency", "id": dep.get("id")})

        nxt: list = []
        for lc in lifecycles:
            if lc.get("state") in active_states:
                nxt.append({"kind": "lifecycle", "id": lc.get("id"),
                            "state": lc.get("state"), "phase": lc.get("phase", "")})

        done = intent.get("status") in done_states or (
            bool(lifecycles) and all(lc.get("state") in done_states for lc in lifecycles))

        if not nxt and not done:
            acc = intent.get("acceptance", "")
            nxt.append({"kind": "acceptance",
                        "action": f"satisfy acceptance: {acc}" if acc
                        else "define acceptance for this intent"})

        return {"intent_id": for_intent_id,
                "acceptance": intent.get("acceptance", ""),
                "status": intent.get("status", ""),
                "done": done, "blocked": blocked, "next": nxt}

    @verb(role="act")
    def research_state(self, domain: str = "", top: int = 20) -> dict:
        """RESEARCH-STATE — open research leads with their claims, citations and
        verification status, grouped (Spec 290, Memory pillar).

        Composes the research sub-graph (`Research` · `ResearchClaim` ·
        `Citation` · `Verification`) into one rollup. ``pending`` lists leads
        not yet ``ready``/``published`` — the verifications still owed.

        Inputs: domain (str — optional case-insensitive filter on a lead's
                question; scopes the children too), top (int — leads returned).
        Returns: ``{domain, totals, leads: [{research_id, question, status,
                   claims, citations, verifications}], pending}``.
        chain_next: manage.read(research_id) for one lead's full props.
        """
        leads = self._live(self.ctx.find("Research"))
        if domain:
            d = domain.lower()
            leads = [r for r in leads if d in r.get("question", "").lower()]
        claims = self._live(self.ctx.find("ResearchClaim"))
        citations = self._live(self.ctx.find("Citation"))
        verifications = self._live(self.ctx.find("Verification"))

        if domain:
            lead_ids = {lead["id"] for lead in leads}
            claims = [c for c in claims if c.get("research_id") in lead_ids]
            citations = [c for c in citations if c.get("research_id") in lead_ids]
            verifications = [v for v in verifications if v.get("research_id") in lead_ids]

        def _for(rid, rows):
            return [r for r in rows if r.get("research_id") == rid]

        done_statuses = {"ready", "published"}
        rows: list = []
        pending: list = []
        for lead in leads:
            rid = lead["id"]
            status = lead.get("status", "")
            vsummary: dict = {}
            for v in _for(rid, verifications):
                st = v.get("status", "?")
                vsummary[st] = vsummary.get(st, 0) + 1
            rows.append({"research_id": rid, "question": lead.get("question", ""),
                         "status": status, "claims": len(_for(rid, claims)),
                         "citations": len(_for(rid, citations)),
                         "verifications": vsummary})
            if status not in done_statuses:
                pending.append(rid)
        rows.sort(key=lambda r: r["citations"], reverse=True)
        return {"domain": domain,
                "totals": {"leads": len(leads), "claims": len(claims),
                           "citations": len(citations),
                           "verifications": len(verifications)},
                "leads": rows[:top], "pending": pending}

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
