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

    @verb(role="effect")
    def finish_spec(self, spec_id: str, approver: str = "", root: str = "Plan",
                    rebuild_architecture: bool = True) -> ToolResult:
        """FINISH_SPEC — the owner-triggered done-cascade as ONE trigger (Spec 388).
        "This spec is done" bundled: move the spec to ``/done`` across ALL THREE
        state representations kept in sync (physical ``Plan/<state>/`` folder +
        ``state:`` frontmatter + the SpecLifecycle node — the agreement check-drift
        gates), APPROVE any ADR decisions the spec REFINES (owner authority — an
        agent never self-approves), and rebuild ``architecture.md``. The folder is
        authoritative ("code/folder is the final decision"); the node + ADR steps
        are best-effort so a not-yet-ingested spec still finishes cleanly.

        Inputs: spec_id (the spec number/id), approver (the human owner's identity
                — authorizes decision approval; '' skips it; 'agent' is rejected by
                the gate), root (the Plan dir), rebuild_architecture (rebuild
                ``architecture.md`` after — default True).
        Returns: ``{spec_id, moved, from_state, folder, decisions_approved,
                 node_synced, architecture_rebuilt}`` or ``{error}``.
        chain_next: workflow.board to see the spec in /done; review the PR.
        """
        import re
        import shutil
        from agency.capabilities.document import _interconnect

        base = os.path.abspath(root)
        # 1. Locate the spec folder by `<spec_id>-…` dir name under a non-terminal
        #    state (the folder IS the authoritative state — Spec 357).
        src = from_state = folder_name = ""
        for state in ("draft", "open", "inprogress"):
            d = os.path.join(base, state)
            if not os.path.isdir(d):
                continue
            for name in sorted(os.listdir(d)):
                p = os.path.join(d, name)
                if (name.split("-", 1)[0] == str(spec_id)
                        and os.path.isfile(os.path.join(p, "spec.md"))):
                    src, from_state, folder_name = p, state, name
                    break
            if src:
                break
        if not src:
            return ToolResult.success(data={
                "spec_id": spec_id, "moved": False,
                "error": f"no spec {spec_id!r} under {root}/(draft|open|inprogress)"})

        spec_md = os.path.join(src, "spec.md")
        fm = _interconnect.parse_frontmatter(
            _interconnect.extract_anchor(open(spec_md, encoding="utf-8").read())[1])
        fid = str(fm.get("spec_id", "")).strip().strip('"') or str(spec_id)

        # 2. Approve the spec's ADR decisions (owner authority), best-effort.
        approved: list[str] = []
        if approver:
            try:
                ready = self.ctx.call("adr", "spec_decisions_ready", spec_id=fid)
                for dec in ready.get("decisions", []) or []:
                    res = self.ctx.call("adr", "approve", decision_id=dec.get("id"),
                                        approver=approver, override=True)
                    if res.get("approved"):
                        approved.append(dec.get("id"))
            except Exception:                                  # noqa: BLE001
                pass

        # 3. Sync the SpecLifecycle node to `done` (best-effort — folder is the
        #    authority; a not-yet-ingested spec simply has no node to sync).
        node_synced = False
        try:
            docs = self.ctx.query_nodes("Document", where={"path": spec_md})
            if docs:
                doc_id = docs[0].get("id")
                self.ctx.call("workflow", "open_spec", spec_id=doc_id)   # idempotent
                cur = (self._spec_lifecycle(doc_id) or {}).get("state", "draft")
                walk = {"draft": ["open", "inprogress", "done"],
                        "open": ["inprogress", "done"],
                        "inprogress": ["done"]}.get(cur, [])
                for st in walk:
                    self.ctx.call("workflow", "move_spec", spec_id=doc_id,
                                  to_state=st, override=True)
                node_synced = True
        except Exception:                                      # noqa: BLE001
            pass

        # 4. Move the physical folder to /done + reconcile the frontmatter (the
        #    authoritative state change — keeps folder == frontmatter).
        dst_parent = os.path.join(base, "done")
        os.makedirs(dst_parent, exist_ok=True)
        dst = os.path.join(dst_parent, folder_name)
        if os.path.exists(dst):
            return ToolResult.success(data={
                "spec_id": spec_id, "moved": False,
                "error": f"target already exists: {os.path.relpath(dst, base)}"})
        shutil.move(src, dst)
        new_md = os.path.join(dst, "spec.md")
        txt = open(new_md, encoding="utf-8").read()
        txt = re.sub(r"(?m)^(state:\s*).*$", r"\1done", txt)
        txt = re.sub(r"(?m)^(status:\s*).*$", r"\1done", txt)
        open(new_md, "w", encoding="utf-8").write(txt)

        # 5. Rebuild the architecture digest (DERIVED — Spec 360), best-effort.
        arch = False
        if rebuild_architecture:
            try:
                self.ctx.call("adr", "architecture", apply=True)
                arch = True
            except Exception:                                  # noqa: BLE001
                pass

        return ToolResult.success(data={
            "spec_id": spec_id, "moved": True, "from_state": from_state,
            "folder": os.path.relpath(dst, base), "decisions_approved": approved,
            "node_synced": node_synced, "architecture_rebuilt": arch})

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
            # Strip a leading Spec-292 anchor (`<!-- agency-node: … -->`) so an
            # anchored spec's frontmatter still parses — parse_frontmatter wants
            # `---` at byte 0, and an interconnected Document carries the anchor first.
            _anchor, fm_body = _interconnect.extract_anchor(body)
            fm = _interconnect.parse_frontmatter(fm_body)
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

    @verb(role="effect")
    def mark_done(self, spec_id: str, approver: str, apply: bool = True,
                  override: bool = False) -> ToolResult:
        """MARK_DONE — phase 14, the owner's done-cascade. The owner declaring a
        spec done IS the approval (an agent never self-approves — panel B2.1). In
        one effect: (1) `adr.approve` every decision that REFINES the spec;
        (2) move the spec ``inprogress→done`` (the SOLE state writer); (3) APPEND/
        UPDATE the affected theme ADR files (`adr.publish` → ``docs/adr/<layer>.md``);
        (4) rebuild the root ``architecture.md`` digest (`adr.architecture`). Steps
        3–4 write the working tree, so they run only when ``apply`` (tests pass
        False to assert the graph cascade without touching the repo).

        Inputs: spec_id, approver (owner identity — agent is rejected), apply (do
                the file writes), override (owner bypass of a skeleton-decision gate).
        Returns: ``{spec_id, done, approved, themes_written, architecture_rebuilt,
                 decisions}`` or, when the done move is illegal, ``{done: False, error}``.
        chain_next: workflow.board to see the spec in /done.
        """
        appr = self.ctx.call("workflow", "approve_decisions", spec_id=spec_id,
                             approver=approver, override=override)
        mv = self.ctx.call("workflow", "move_spec", spec_id=spec_id,
                           to_state="done", override=override)
        if not mv.get("moved"):
            return ToolResult.success(data={
                "spec_id": spec_id, "done": False,
                "approved": appr.get("approved", []),
                "error": mv.get("error") or mv.get("reason"),
                "blocking": mv.get("blocking", [])})
        themes_written: list[str] = []
        architecture_rebuilt = False
        decisions = None
        if apply:
            # (3) append/update each theme the spec's decisions belong to.
            ready = self.ctx.call("adr", "spec_decisions_ready", spec_id=spec_id)
            theme_ids: list[str] = []
            for d in ready.get("decisions", []):
                for nb in self.ctx.neighbors(d["id"], "PART_OF", direction="out"):
                    tid = nb.get("id")
                    if tid and tid not in theme_ids:
                        theme_ids.append(tid)
            for tid in theme_ids:
                pub = self.ctx.call("adr", "publish", theme_id=tid)
                if pub.get("written"):
                    themes_written.append(pub.get("path"))
            # (4) rebuild the architecture digest from the published ADRs.
            arch = self.ctx.call("adr", "architecture", apply=True)
            architecture_rebuilt = bool(arch.get("written"))
            decisions = arch.get("decisions")
        return ToolResult.success(data={
            "spec_id": spec_id, "done": True, "approved": appr.get("approved", []),
            "themes_written": themes_written,
            "architecture_rebuilt": architecture_rebuilt, "decisions": decisions})
