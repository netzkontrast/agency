"""workflow — the repo-development lifecycle: specs as first-class Lifecycles.

Use when: a spec must move through its development stages (draft → open →
inprogress → done, or superseded) as a TRACKED, queryable Lifecycle — not a
hand-edited status field. The spec's state IS a Lifecycle on the pillar
(Spec 339/345 ``spec`` machine), advanced ONLY via ``ctx.lifecycle.move``; the
/open→/inprogress transition is gated by the ADR-approval hinge
(``adr.spec_decisions_ready`` — Spec 356/355).
Triggers:
- A new spec needs a state machine → open_spec
- A spec advances a stage and the transition must be guarded + recorded → move_spec
- "What's in /inprogress?" → board, answered from the graph
Red flags:
- Hand-editing a spec's ``status:`` / folder without advancing the Lifecycle → drift
- Moving open→inprogress before its ADR decisions are approved → the gate refuses
- Writing ``Lifecycle.state`` directly → only ``ctx.lifecycle.move`` may (Spec 339)

Spec 357 — the spec-state lifecycle. This slice lands the **lifecycle
integration** the owner asked for: the SpecLifecycle on the ``spec`` machine
(``open_spec`` · ``move_spec`` with the ADR-hinge guard · ``board``). The
physical ``Plan/`` state folders + ``state:`` frontmatter index + the
``check-drift`` spec-state gate are a follow-up slice (the human surface over
this spine).
"""
from __future__ import annotations

from agency.capability import CapabilityBase, verb
from agency.memory import OPEN as _OPEN
from agency.toolresult import ToolResult

from .ontology import SPEC_STATES, workflow_ontology


class WorkflowCapability(CapabilityBase):
    name = "workflow"
    home = "lifecycle"          # drives the Lifecycle pillar's `spec` machine
    ontology = workflow_ontology

    def _spec_lifecycle(self, doc_id: str) -> dict | None:
        """The (live) SpecLifecycle TRACKING this spec Document, if any."""
        lcs = [lc for lc in self.ctx.neighbors(doc_id, "TRACKS", direction="in")
               if lc.get("vto", _OPEN) >= _OPEN]
        return lcs[0] if lcs else None

    @verb(role="act")
    def open_spec(self, spec_id: str, title: str = "") -> ToolResult:
        """OPEN_SPEC — mint a SpecLifecycle (machine ``spec``, state ``draft``) for
        a spec ``Document``, ``TRACKS``-bound to it and SERVING the intent.
        Idempotent: returns the existing lifecycle if one already tracks the spec.

        Inputs: spec_id (the spec's Document id), title (str — optional label).
        Returns: ``{spec_id, lifecycle_id, state, created}`` or ``{error}``.
        chain_next: workflow.move_spec(spec_id, "open") once design is done.
        """
        if not self.ctx.recall_typed(spec_id, "Document"):
            return ToolResult.success(data={"error": f"no spec Document {spec_id!r}",
                                            "spec_id": spec_id})
        existing = self._spec_lifecycle(spec_id)
        if existing:
            return ToolResult.success(data={"spec_id": spec_id,
                                            "lifecycle_id": existing.get("id"),
                                            "state": existing.get("state"),
                                            "created": False})
        lid = self.ctx.lifecycle.open(self.ctx.intent_id, kind="spec", machine="spec")
        self.ctx.link(lid, spec_id, "TRACKS")
        return ToolResult.success(data={"spec_id": spec_id, "lifecycle_id": lid,
                                        "state": "draft", "created": True})

    @verb(role="effect", param_enums={"to_state": SPEC_STATES})
    def move_spec(self, spec_id: str, to_state: str,
                  override: bool = False) -> ToolResult:
        """MOVE_SPEC — advance the spec's Lifecycle to ``to_state`` via
        ``ctx.lifecycle.move`` (the SOLE state writer — Spec 339; an illegal edge
        is rejected by the ``spec`` machine's transition table). The
        **open→inprogress** transition is GATED by the ADR hinge:
        ``adr.spec_decisions_ready(spec)`` must be true (every extracted decision
        approved — Spec 356/355), unless a provenance-stamped owner ``override``.

        Inputs: spec_id (the spec Document id), to_state (a ``spec`` machine state),
                override (bool — owner bypass of the ADR gate).
        Returns: ``{spec_id, lifecycle_id, moved, state, …}``; on the gate,
                 ``{moved: False, blocked: True, reason, blocking}``; on an illegal
                 edge / no-op, ``{moved: False, error}``.
        chain_next: workflow.board to see the spec's new column.
        """
        if to_state not in SPEC_STATES:
            return ToolResult.success(data={
                "error": f"unknown spec state {to_state!r}; valid: {sorted(SPEC_STATES)}",
                "spec_id": spec_id, "moved": False})
        lc = self._spec_lifecycle(spec_id)
        if not lc:
            return ToolResult.success(data={
                "error": f"no SpecLifecycle for {spec_id!r} — open_spec first",
                "spec_id": spec_id, "moved": False})
        lid, current = lc.get("id"), lc.get("state")
        # The ADR hinge — open→inprogress requires approved decisions (Spec 356/355).
        if current == "open" and to_state == "inprogress" and not override:
            ready = self.ctx.call("adr", "spec_decisions_ready", spec_id=spec_id)
            if not ready.get("ready"):
                return ToolResult.success(data={
                    "spec_id": spec_id, "lifecycle_id": lid, "moved": False,
                    "blocked": True, "state": current,
                    "reason": ready.get("reason", "decisions-unapproved"),
                    "blocking": ready.get("blocking", [])})
        try:
            state = self.ctx.lifecycle.move(lid, to_state,
                                            evidence=f"move_spec {spec_id}")
        except Exception as exc:                              # noqa: BLE001
            # Illegal edge (IllegalTransition) / no-op / unknown state → typed error.
            return ToolResult.success(data={"error": str(exc), "spec_id": spec_id,
                                            "moved": False, "state": current})
        return ToolResult.success(data={"spec_id": spec_id, "lifecycle_id": lid,
                                        "moved": True, "state": state,
                                        "override": bool(override)})

    @verb(role="transform")
    def board(self, state: str = "") -> ToolResult:
        """BOARD — the graph-native spec board: live SpecLifecycles grouped by
        their ``spec``-machine state (optionally filtered to one ``state``).

        Inputs: state (str — optional filter to one spec state).
        Returns: ``{board: {state: [{lifecycle_id, spec_id}]}, states, total}``.
        chain_next: workflow.move_spec to advance one; adr.hints at inprogress.
        """
        board: dict[str, list[dict]] = {}
        for lc in self.ctx.query_nodes("Lifecycle", where={"machine": "spec"}):
            if lc.get("vto", _OPEN) < _OPEN:
                continue
            st = lc.get("state", "?")
            if state and st != state:
                continue
            tracked = self.ctx.neighbors(lc.get("id"), "TRACKS", direction="out")
            board.setdefault(st, []).append({
                "lifecycle_id": lc.get("id"),
                "spec_id": tracked[0].get("id") if tracked else ""})
        return ToolResult.success(data={"board": board, "states": sorted(board),
                                        "total": sum(len(v) for v in board.values())})
