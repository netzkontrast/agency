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

Spec 357 — the spec-state lifecycle. Lands the **lifecycle integration** the
owner asked for: the SpecLifecycle on the ``spec`` machine (``open_spec`` ·
``move_spec`` with the ADR-hinge guard · ``board``), plus the **human surface** —
the physical ``Plan/<state>/`` folders + the ``index`` indexer (folder vs
``state:`` frontmatter vs node, "alle Specs indiziert / korrekte Frontmatter").
Wiring ``index.ok`` into the ``check-drift`` spec-state gate is the remaining
follow-up.
"""
from __future__ import annotations

import os

from agency.capability import CapabilityBase, verb
from agency.memory import OPEN as _OPEN
from agency.toolresult import ToolResult

from .ontology import SPEC_STATES, workflow_ontology

# Drift-worthy flags (a legacy flat spec is reported, NOT a failure — Spec 357
# grandfathers the 339 flat specs; only specs IN a state folder must agree).
_DRIFT_FLAGS = {"drift", "missing-state", "invalid-state", "node-drift"}


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

    @verb(role="transform")
    def index(self, root: str = "Plan") -> ToolResult:
        """INDEX — the "alle Specs sind indiziert, korrekte Frontmatter" guarantee
        (Spec 357). Walks ``root`` for ``*/spec.md`` and reports each spec with its
        THREE state readings — ``folder_state`` (the ``Plan/<state>/`` parent),
        ``frontmatter_state`` (the ``state:`` field), ``node_state`` (the
        SpecLifecycle, best-effort) — and flags any disagreement. Legacy flat specs
        (Spec 339, grandfathered) are reported with a ``legacy`` flag, NOT failed —
        only specs filed under a state folder must have all three agree.

        Inputs: root (str — the Plan dir to index; default "Plan").
        Returns: ``{root, count, rows: [{spec, spec_id, folder_state,
                 frontmatter_state, node_state, flags}], drift, ok}`` — ``ok`` is
                 True iff no spec carries a drift flag (the check-drift predicate).
        chain_next: workflow.move_spec to reconcile a drifted spec; the check-drift
                    spec-state gate consumes ``ok`` (follow-up).
        """
        from agency.capabilities.document import _interconnect
        base = os.path.abspath(root)
        rows: list[dict] = []
        for dirpath, _dirs, files in os.walk(base):
            if "spec.md" not in files:
                continue
            spec_path = os.path.join(dirpath, "spec.md")
            rel = os.path.relpath(spec_path, base)
            top = rel.split(os.sep)[0]
            folder_state = top if top in SPEC_STATES else ""
            try:
                with open(spec_path, encoding="utf-8") as f:
                    body = f.read()
            except OSError:
                continue
            fm = _interconnect.parse_frontmatter(body)
            fstate = str(fm.get("state", "")).strip().strip('"')
            spec_id = str(fm.get("spec_id", "")).strip().strip('"')
            node_state = ""
            docs = self.ctx.query_nodes("Document", where={"path": spec_path})
            if docs:
                lc = self._spec_lifecycle(docs[0].get("id"))
                node_state = lc.get("state", "") if lc else ""
            flags: list[str] = []
            if not folder_state:
                flags.append("legacy")
            else:
                if not fstate:
                    flags.append("missing-state")
                elif fstate != folder_state:
                    flags.append("drift")
                if node_state and node_state != folder_state:
                    flags.append("node-drift")
            if fstate and fstate not in SPEC_STATES:
                flags.append("invalid-state")
            rows.append({"spec": rel, "spec_id": spec_id,
                         "folder_state": folder_state, "frontmatter_state": fstate,
                         "node_state": node_state, "flags": flags})
        drift = [r["spec"] for r in rows if _DRIFT_FLAGS & set(r["flags"])]
        return ToolResult.success(data={"root": base, "count": len(rows),
                                        "rows": rows, "drift": drift,
                                        "ok": not drift})
