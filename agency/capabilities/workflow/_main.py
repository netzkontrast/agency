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
                  override: bool = False, superseded_by: str = "") -> ToolResult:
        """MOVE_SPEC — advance the spec's Lifecycle to ``to_state`` via
        ``ctx.lifecycle.move`` (the SOLE state writer — Spec 339; an illegal edge
        is rejected by the ``spec`` machine's transition table). The
        **open→inprogress** transition is GATED by the ADR hinge:
        ``adr.spec_decisions_ready(spec)`` must be true (every extracted decision
        approved — Spec 356/355), unless a provenance-stamped owner ``override``.
        Moving to ``superseded`` with ``superseded_by`` set records the forward
        reference (the core ``SUPERSEDED_BY`` edge: this spec → its replacement).

        Inputs: spec_id (the spec Document id), to_state (a ``spec`` machine state),
                override (bool — owner bypass of the ADR gate), superseded_by (the
                replacing spec's Document id — only when to_state="superseded").
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
        # SPEC-001-C supersession: record the forward reference to the replacement
        # spec (the core SUPERSEDED_BY edge — this spec → its replacement).
        superseded_by_recorded = ""
        if state == "superseded" and superseded_by and \
                self.ctx.recall_typed(superseded_by, "Document"):
            self.ctx.link(spec_id, superseded_by, "SUPERSEDED_BY")
            superseded_by_recorded = superseded_by
        return ToolResult.success(data={"spec_id": spec_id, "lifecycle_id": lid,
                                        "moved": True, "state": state,
                                        "override": bool(override),
                                        "superseded_by": superseded_by_recorded})

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

    # ── Spec 358 Slice 2 — the ADR-hinge step verbs (composable sugar over the
    #    walker's phases 10–12; each routes through the real caps so provenance is
    #    recorded identically — the moat is never bypassed).

    @verb(role="effect")
    def to_open(self, spec_id: str) -> ToolResult:
        """TO_OPEN — phase 10: move the spec ``draft→open`` and extract its
        decisions into ``proposed`` drafts (`adr.extract_decisions apply=True`).
        Idempotent: opens the SpecLifecycle if absent; skips the move if already
        past draft.

        Inputs: spec_id (the spec Document id).
        Returns: ``{spec_id, state, drafted: [decision_ids], candidates}``.
        chain_next: workflow.approve_decisions then workflow.begin_impl.
        """
        if not self._spec_lifecycle(spec_id):
            self.ctx.call("workflow", "open_spec", spec_id=spec_id)
        lc = self._spec_lifecycle(spec_id)
        if lc and lc.get("state") == "draft":
            self.ctx.call("workflow", "move_spec", spec_id=spec_id, to_state="open")
        ext = self.ctx.call("adr", "extract_decisions", spec_id=spec_id, apply=True)
        cur = self._spec_lifecycle(spec_id) or {}
        return ToolResult.success(data={"spec_id": spec_id, "state": cur.get("state"),
                                        "drafted": ext.get("drafted", []),
                                        "candidates": len(ext.get("candidates", []))})

    @verb(role="effect")
    def approve_decisions(self, spec_id: str, approver: str,
                          override: bool = False) -> ToolResult:
        """APPROVE_DECISIONS — phase 11: run `adr.approve` over every decision that
        `REFINES` the spec (the ADR hinge's human step). Only the intent OWNER may
        approve (agent self-approve is rejected by `adr.approve`).

        Inputs: spec_id, approver (owner identity), override (owner bypass of the
                automated DoD gate for a skeleton decision).
        Returns: ``{spec_id, approved: [{id, approved}], ready}`` — ``ready`` is the
                 post-approval /open→/inprogress predicate.
        chain_next: workflow.begin_impl(spec_id).
        """
        ready = self.ctx.call("adr", "spec_decisions_ready", spec_id=spec_id)
        approved = []
        for d in ready.get("decisions", []):
            r = self.ctx.call("adr", "approve", decision_id=d["id"],
                              approver=approver, override=override)
            approved.append({"id": d["id"], "approved": r.get("approved")})
        after = self.ctx.call("adr", "spec_decisions_ready", spec_id=spec_id)
        return ToolResult.success(data={"spec_id": spec_id, "approved": approved,
                                        "ready": after.get("ready")})

    @verb(role="effect")
    def begin_impl(self, spec_id: str, budget: int = 2000) -> ToolResult:
        """BEGIN_IMPL — phase 12: the guarded ``open→inprogress`` move (BLOCKED by
        the ADR hinge until every decision is approved — `spec_decisions_ready`),
        then load the approved decisions' `adr.hints` into the build context.

        Inputs: spec_id, budget (hint token budget).
        Returns: ``{spec_id, begun, state, hints, hint_count}`` or, when the hinge
                 blocks, ``{begun: False, blocked: True, reason, blocking}``.
        chain_next: implement against the hints; workflow.move_spec(→done) when verified.
        """
        mv = self.ctx.call("workflow", "move_spec", spec_id=spec_id,
                           to_state="inprogress")
        if not mv.get("moved"):
            return ToolResult.success(data={"spec_id": spec_id, "begun": False,
                                            "blocked": mv.get("blocked", False),
                                            "reason": mv.get("reason") or mv.get("error"),
                                            "blocking": mv.get("blocking", [])})
        hints = self.ctx.call("adr", "hints", spec_id=spec_id, budget=budget)
        return ToolResult.success(data={"spec_id": spec_id, "begun": True,
                                        "state": "inprogress",
                                        "hints": hints.get("hints", []),
                                        "hint_count": len(hints.get("hints", []))})
