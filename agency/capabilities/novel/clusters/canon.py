"""novel.canon — canon provenance markers & locks (Spec 137).

The KP source-of-truth discipline: every canon fact carries a provenance
marker — ``[K]`` canonical · ``[V]`` proposal · ``[S]`` quarry (deprecated
raw stock) · ``[L]`` gap. ``canon_status`` rides as a cross-cutting property
on ANY novel-domain node (open-set substrate — marker, not node); only
``Lock`` is a new node because a lock has its own lifecycle (date, source,
supersession chain — newer wins, never deleted). ``canon_gate`` is the
hard-stop against silently canonizing speculation.

Spec 247 — the approval workflow: ``propose_canon`` → ``approve_canon`` is
the reviewed path to a Lock. A CanonProposal moves along a legal DAG only
(proposal→approved | proposal→rejected | approved→superseded); approval is
monotonic (an approved proposal never reverts — supersession is a NEW
proposal referencing the prior lock). Every approval-path Lock carries
``proposed_by + approved_by + proposal_id`` as queryable provenance; a
rejection records a Reflection; the same scope rejected ≥ CANON_CHURN_N
times mints ONE Spec-150 observation Reflection (the rule is the noise).
Approval is human-only by doctrine — a managed-agent approver is denied.
"""
from __future__ import annotations

import datetime as _dt
import json as _json

from agency.capability import verb
from agency.toolresult import Codes, ToolResult

#: [K] / [V] / [S] / [L]
CANON_STATUS = {"canonical", "proposal", "quarry", "gap"}

#: Spec 247 — source-hierarchy tier of a proposal.
PROPOSAL_TIER = {"V", "K", "author"}
#: Spec 247 — the legal status DAG (transitions checked in approve_canon).
PROPOSAL_STATUS = {"proposal", "approved", "rejected", "superseded"}
#: Spec 247 — same scope rejected this many times → dogfood signal.
CANON_CHURN_N = 3

#: Node labels the audit sweeps (those carrying a `novel` FK property).
_AUDITED_LABELS = ("CodexEntry", "Storyform", "BeatExpectation",
                   "StoryTimeEvent", "NarrativeBeat", "NovelClaim")


class CanonMixin:
    """Canon cluster — provenance markers, locks, the master index + gate."""

    def _novel_nodes(self, novel_id: str) -> list[dict]:
        nodes: list[dict] = []
        for label in _AUDITED_LABELS:
            nodes.extend(n for n in self.ctx.find(label)
                         if n.get("novel") == novel_id)
        return nodes

    @verb(role="effect")
    def set_canon_status(self, node_id: str, status: str) -> ToolResult:
        """Stamp any node with a ``CANON_STATUS`` marker (effect).

        Inputs: node_id (any novel-domain node), status
                (canonical | proposal | quarry | gap).
        Returns: ``{node_id, canon_status, was}``.
        chain_next: ``novel.canon_audit(novel_id)`` for the census.
        """
        if status not in CANON_STATUS:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"status={status!r} not in {sorted(CANON_STATUS)}")
        node = self.ctx.recall(node_id)
        if node is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"node {node_id!r} not found")
        was = node.get("canon_status", "")
        self.ctx.memory.update(node_id, {"canon_status": status})
        return ToolResult.success(data={
            "node_id": node_id, "canon_status": status, "was": was})

    @verb(role="effect")
    def record_lock(self, novel_id: str, topic: str, content: str,
                    source: str, locked_on: str = "",
                    supersedes: str = "") -> ToolResult:
        """Mint a ``Lock`` — a canonized decision (effect). Superseding never
        deletes: the older lock gets ``superseded_by`` (audit chain).

        Inputs: novel_id, topic, content (the locked statement, verbatim),
                source (originating doc/log), locked_on (ISO date; default
                today UTC), supersedes (optional earlier Lock id).
        Returns: ``{lock_id, topic, locked_on, supersedes,
                 supersedes_chain}``.
        chain_next: ``novel.lock_index(novel_id)`` — the Master-Index.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chain: list[str] = []
        if supersedes:
            older = self.ctx.recall(supersedes)
            if older is None:
                return ToolResult.failure(
                    Codes.NOT_FOUND, f"supersedes {supersedes!r} not found")
            cur = older
            while cur is not None:
                chain.append(cur["id"])
                nxt = cur.get("supersedes", "")
                cur = self.ctx.recall(nxt) if nxt else None
        lid = self.ctx.record("Lock", {
            "novel": novel_id, "topic": topic, "content": content,
            "locked_on": locked_on or _dt.date.today().isoformat(),
            "source": source, "supersedes": supersedes,
            "superseded_by": "",
        })
        if supersedes:
            self.ctx.memory.update(supersedes, {"superseded_by": lid})
        self.ctx.link(lid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "lock_id": lid, "topic": topic,
            "locked_on": self.ctx.recall(lid).get("locked_on"),
            "supersedes": supersedes, "supersedes_chain": chain})

    @verb(role="transform")
    def lock_index(self, novel_id: str, topic: str = "") -> ToolResult:
        """The Master-Index of active locks (transform) — consulted before
        any contested drafting decision. Superseded locks excluded; sorted
        newest-first (newer = higher authority).

        Inputs: novel_id, topic (optional filter).
        Returns: ``{locks, count, by_topic}``.
        chain_next: ``novel.resolve_canon_conflict`` on competing facts.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        locks = [l for l in self.ctx.find("Lock")
                 if l.get("novel") == novel_id
                 and not l.get("superseded_by")
                 and (not topic or l.get("topic") == topic)]
        locks.sort(key=lambda l: l.get("locked_on", ""), reverse=True)
        by_topic: dict[str, int] = {}
        for l in locks:
            by_topic[l.get("topic", "")] = by_topic.get(l.get("topic", ""),
                                                        0) + 1
        rows = [{"id": l["id"], "topic": l.get("topic", ""),
                 "content": l.get("content", ""),
                 "locked_on": l.get("locked_on", ""),
                 "source": l.get("source", "")} for l in locks]
        return ToolResult.success(data={
            "locks": rows, "count": len(rows), "by_topic": by_topic})

    @verb(role="transform")
    def resolve_canon_conflict(self, candidates: list) -> ToolResult:
        """Apply the ONE conflict rule (transform): any canonical/proposal
        beats every quarry; among non-quarry the later ``source_date`` wins;
        exact ties return ``tied=True``.

        Inputs: candidates ([{node_id, canon_status, source_date}]).
        Returns: ``{winner, losers, reason}`` or ``{tied: True,
                 candidates}``.
        chain_next: ``novel.set_canon_status`` on the loser(s) if demoting.
        """
        if not candidates:
            return ToolResult.failure(Codes.INVALID_ARGUMENT,
                                      "no candidates supplied")
        non_quarry = [c for c in candidates
                      if c.get("canon_status") != "quarry"]
        pool = non_quarry or candidates
        best_date = max(c.get("source_date", "") for c in pool)
        winners = [c for c in pool if c.get("source_date", "") == best_date]
        if len(winners) > 1:
            return ToolResult.success(data={
                "tied": True,
                "candidates": [c.get("node_id") for c in winners]})
        winner = winners[0]
        losers = [c.get("node_id") for c in candidates
                  if c.get("node_id") != winner.get("node_id")]
        reason = ("newer-wins" if len(pool) == len(candidates)
                  else "newer-wins; quarry loses to non-quarry")
        return ToolResult.success(data={
            "winner": winner.get("node_id"), "losers": losers,
            "reason": reason, "tied": False})

    @verb(role="transform")
    def quarry_filter(self, novel_id: str, kind: str = "") -> ToolResult:
        """List the Steinbruch (transform): quarry-status nodes — deprecated
        material an author may still mine, never auto-canon.

        Inputs: novel_id, kind (optional node-kind filter).
        Returns: ``{nodes: [{node_id, kind, name_or_slug, canon_status}],
                 count}``.
        chain_next: ``novel.promote_from_quarry(node_id, source)``.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        rows = []
        for n in self._novel_nodes(novel_id):
            if n.get("canon_status") != "quarry":
                continue
            if kind and n.get("kind", "") != kind:
                continue
            rows.append({"node_id": n["id"], "kind": n.get("kind", ""),
                         "name_or_slug": n.get("name") or n.get("slug", ""),
                         "canon_status": "quarry"})
        return ToolResult.success(data={"nodes": rows, "count": len(rows)})

    @verb(role="effect")
    def promote_from_quarry(self, node_id: str, source: str,
                            topic: str = "") -> ToolResult:
        """Flip a quarry node → proposal + mint the Lock recording the
        promotion (effect). Only quarry nodes are promotable.

        Inputs: node_id, source (what authorizes the promotion), topic
                (defaults to ``promote:<kind>:<slug>``).
        Returns: ``{node_id, new_status, lock_id}``.
        chain_next: validation, then ``novel.set_canon_status(node_id,
                    'canonical')`` when it locks.
        """
        node = self.ctx.recall(node_id)
        if node is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"node {node_id!r} not found")
        if node.get("canon_status") != "quarry":
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"node {node_id!r} is {node.get('canon_status', 'unmarked')!r}"
                f", not 'quarry'")
        self.ctx.memory.update(node_id, {"canon_status": "proposal"})
        topic = topic or (f"promote:{node.get('kind', 'node')}:"
                          f"{node.get('slug') or node.get('name', node_id)}")
        lock = self.record_lock(node.get("novel", ""), topic,
                                f"promoted from quarry: {node_id}", source)
        lock_id = lock.data.get("lock_id", "") if lock.ok else ""
        if lock_id:
            self.ctx.link(lock_id, node_id, "LOCKS")
        return ToolResult.success(data={
            "node_id": node_id, "new_status": "proposal",
            "lock_id": lock_id})

    @verb(role="transform")
    def canon_audit(self, novel_id: str) -> ToolResult:
        """Census + open-work surface (transform): counts per status, the
        ``[L]`` gaps still to set, the unmarked nodes (decide!), and the 5
        newest locks.

        Inputs: novel_id.
        Returns: ``{counts, gaps, unmarked, latest_locks}``.
        chain_next: ``novel.set_canon_status`` per unmarked node.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        counts = {s: 0 for s in sorted(CANON_STATUS)}
        counts["unmarked"] = 0
        gaps: list[dict] = []
        unmarked: list[dict] = []
        for n in self._novel_nodes(novel_id):
            status = n.get("canon_status", "")
            row = {"node_id": n["id"], "kind": n.get("kind", ""),
                   "slug_or_name": n.get("slug") or n.get("name", "")}
            if not status:
                counts["unmarked"] += 1
                unmarked.append(row)
            else:
                counts[status] = counts.get(status, 0) + 1
                if status == "gap":
                    gaps.append(row)
        locks = sorted((l for l in self.ctx.find("Lock")
                        if l.get("novel") == novel_id),
                       key=lambda l: l.get("locked_on", ""), reverse=True)
        latest = [{"lock_id": l["id"], "topic": l.get("topic", ""),
                   "locked_on": l.get("locked_on", "")} for l in locks[:5]]
        return ToolResult.success(data={
            "counts": counts, "gaps": gaps, "unmarked": unmarked,
            "latest_locks": latest})

    # ── Spec 247 — approval workflow ─────────────────────────────────────

    @verb(role="effect", param_enums={"tier": PROPOSAL_TIER})
    def propose_canon(self, novel_id: str, scope: str, payload: dict,
                      rationale: str, tier: str = "V",
                      evidence: str = "", proposed_by: str = "",
                      author_override: bool = False,
                      supersedes_lock: str = "") -> ToolResult:
        """Open a CanonProposal — the reviewed path toward a Lock (effect).

        The source-hierarchy gate runs at propose-time: a ``tier="K"``
        proposal MUST cite an APPROVED lock as ``evidence``; ``tier=
        "author"`` requires ``author_override=True``. A non-dict payload is
        rejected (schema mismatch is signal, not noise). Every proposal
        mints a serving sub-Intent (Spec 176 — the approval request
        survives the proposal's lifecycle). ``supersedes_lock`` names an
        active Lock this proposal, once approved, will supersede.

        Inputs: novel_id, scope (what the canon claim governs), payload
                (the claim, dict), rationale, tier (V | K | author),
                evidence (approved lock id — required for K), proposed_by,
                author_override (required True for tier=author),
                supersedes_lock (optional active Lock id).
        Returns: ``{proposal_id, scope, tier, status, intent_id}``.
        chain_next: ``novel.approve_canon(proposal_id, approver, decision)``.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        if not isinstance(payload, dict) or not payload:
            return ToolResult.failure(
                Codes.VALIDATION_FAILED,
                "payload must be a non-empty dict — schema mismatch is "
                "signal (log it to the rule via reflect.note)")
        if tier == "K":
            ev = self.ctx.recall(evidence) if evidence else None
            ev_ok = bool(ev is not None and (
                ev.get("proposal_id")            # approval-path lock
                or ev.get("topic") is not None))  # any Lock counts as cite
            if not ev_ok:
                return ToolResult.failure(
                    Codes.VALIDATION_FAILED,
                    f"tier='K' requires evidence naming an existing Lock; "
                    f"got {evidence!r}")
        if tier == "author" and not author_override:
            return ToolResult.failure(
                Codes.VALIDATION_FAILED,
                "tier='author' requires author_override=True (explicit "
                "author authority)")
        if supersedes_lock:
            old = self.ctx.recall(supersedes_lock)
            if old is None or old.get("superseded_by"):
                return ToolResult.failure(
                    Codes.NOT_FOUND,
                    f"supersedes_lock {supersedes_lock!r} not an active Lock")
        # Spec 176 — the approval request is a captured sub-Intent.
        sub_iid = self.ctx.record("Intent", {
            "purpose": f"canon approval: {scope}",
            "deliverable": "an approve/reject CanonDecision",
            "acceptance": "decision recorded with provenance",
            "status": "draft", "owner": "agent",
            "parent_intent_id": self.ctx.intent_id})
        self.ctx.link(sub_iid, self.ctx.intent_id, "PARENT_INTENT")
        pid = self.ctx.record("CanonProposal", {
            "novel": novel_id, "scope": scope,
            "payload": _json.dumps(payload, sort_keys=True),
            "rationale": rationale, "tier": tier,
            "status": "proposal", "evidence": evidence,
            "proposed_by": proposed_by or "unknown",
            "proposed_at": _dt.date.today().isoformat(),
            "supersedes_lock": supersedes_lock,
            "lock_id": "", "decided_by": "", "decided_at": "",
            "reflection_id": "", "intent_id": sub_iid})
        self.ctx.link(pid, sub_iid, "SERVES")
        self.ctx.link(pid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "proposal_id": pid, "scope": scope, "tier": tier,
            "status": "proposal", "intent_id": sub_iid})

    @verb(role="effect", param_enums={"decision": {"approve", "reject"}})
    def approve_canon(self, proposal_id: str, approver: str,
                      decision: str = "approve", reason: str = "",
                      approver_kind: str = "human") -> ToolResult:
        """Decide a CanonProposal (effect) — approval is the ONLY path that
        mints an approval-provenance Lock. Monotonic: an approved proposal
        never reverts (a repeat approve is idempotent and returns the
        existing decision); a decided proposal rejects further flips.
        Approval is human-only — ``approver_kind="managed_agent"`` is
        denied (the Driver may propose, never approve). A rejection records
        a Reflection with the reason; the same scope rejected ≥
        CANON_CHURN_N times mints ONE observation Reflection (Spec 150
        feed) per scope.

        Inputs: proposal_id, approver (who decides — required), decision
                (approve | reject), reason (required for reject),
                approver_kind (human | managed_agent — the latter denied).
        Returns: ``{proposal_id, decision, lock_id, decided_by, decided_at,
                 dogfood_reflection_id, idempotent}``.
        chain_next: ``novel.lock_index`` — the new Lock is live; or
                    re-propose after a rejection.
        """
        if not approver.strip():
            return ToolResult.failure(
                Codes.APPROVAL_DENIED, "approver is required")
        if approver_kind == "managed_agent":
            return ToolResult.failure(
                Codes.APPROVAL_DENIED,
                "approval is human-only by doctrine — a managed agent may "
                "propose, never approve")
        prop = self.ctx.recall(proposal_id)
        if prop is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"proposal {proposal_id!r} not found")
        status = prop.get("status", "proposal")
        if status == "approved":
            if decision == "approve":     # concurrent approve — idempotent
                return ToolResult.success(data={
                    "proposal_id": proposal_id, "decision": "approve",
                    "lock_id": prop.get("lock_id", ""),
                    "decided_by": prop.get("decided_by", ""),
                    "decided_at": prop.get("decided_at", ""),
                    "dogfood_reflection_id": "", "idempotent": True})
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                "approval is monotonic — an approved proposal cannot be "
                "rejected; supersede it with a NEW proposal instead")
        if status in ("rejected", "superseded"):
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"proposal is terminal ({status}) — re-propose instead")
        today = _dt.date.today().isoformat()
        if decision == "reject":
            rid = self.ctx.record("Reflection", {
                "scope": "technical", "kind": "canon-rejection",
                "novel": prop.get("novel", ""),
                "proposal_id": proposal_id,
                "text": f"canon proposal {proposal_id} for scope "
                        f"{prop.get('scope', '')!r} rejected by {approver}: "
                        f"{reason or 'no reason given'}"})
            self.ctx.link(rid, self.ctx.intent_id, "SERVES")
            self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
            self.ctx.memory.update(proposal_id, {
                "status": "rejected", "decided_by": approver,
                "decided_at": today, "reflection_id": rid})
            churn_rid = self._mint_churn_reflection(prop)
            return ToolResult.success(data={
                "proposal_id": proposal_id, "decision": "reject",
                "lock_id": "", "decided_by": approver, "decided_at": today,
                "dogfood_reflection_id": rid,
                "churn_reflection_id": churn_rid, "idempotent": False})
        # approve — mint the Lock with full provenance.
        lock = self.record_lock(
            prop.get("novel", ""), topic=prop.get("scope", ""),
            content=prop.get("payload", ""),
            source=f"proposal:{proposal_id}",
            supersedes=prop.get("supersedes_lock", ""))
        if not lock.ok:
            return lock
        lock_id = lock.data["lock_id"]
        self.ctx.memory.update(lock_id, {
            "proposed_by": prop.get("proposed_by", ""),
            "approved_by": approver, "proposal_id": proposal_id,
            "tier": prop.get("tier", "V")})
        self.ctx.memory.update(proposal_id, {
            "status": "approved", "lock_id": lock_id,
            "decided_by": approver, "decided_at": today})
        # supersession flips the PRIOR proposal approved → superseded.
        old_lock_id = prop.get("supersedes_lock", "")
        if old_lock_id:
            old_lock = self.ctx.recall(old_lock_id) or {}
            old_pid = old_lock.get("proposal_id", "")
            if old_pid and (self.ctx.recall(old_pid) or {}).get(
                    "status") == "approved":
                self.ctx.memory.update(old_pid, {"status": "superseded"})
        return ToolResult.success(data={
            "proposal_id": proposal_id, "decision": "approve",
            "lock_id": lock_id, "decided_by": approver,
            "decided_at": today, "dogfood_reflection_id": "",
            "idempotent": False})

    def _mint_churn_reflection(self, prop: dict) -> str:
        """Spec 247 × Spec 150 — a scope rejected ≥ CANON_CHURN_N times is
        a rule problem, not a proposer problem. One observation Reflection
        per (novel, scope) cluster, idempotent."""
        novel_id = prop.get("novel", "")
        scope = prop.get("scope", "")
        rejected = [p for p in self.ctx.find("CanonProposal")
                    if p.get("novel") == novel_id
                    and p.get("scope") == scope
                    and p.get("status") == "rejected"]
        # +1: the caller is mid-flight — its status update may not be
        # visible in this find() snapshot.
        count = len(rejected) + (0 if any(
            p["id"] == prop.get("id") for p in rejected) else 1)
        if count < CANON_CHURN_N:
            return ""
        already = any(r.get("kind") == "canon-churn"
                      and r.get("novel") == novel_id
                      and r.get("cluster") == scope
                      for r in self.ctx.find("Reflection"))
        if already:
            return ""
        rid = self.ctx.record("Reflection", {
            "scope": "observation", "kind": "canon-churn",
            "novel": novel_id, "cluster": scope,
            "text": f"canon scope {scope!r} rejected {count}x (threshold "
                    f"{CANON_CHURN_N}) — the governing rule keeps "
                    f"triggering propose/reject churn; consider amending "
                    f"it (Spec 150 parse_amendment picks this up)"})
        self.ctx.link(rid, self.ctx.intent_id, "SERVES")
        self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
        return rid

    @verb(role="transform")
    def list_canon_proposals(self, novel_id: str, status: str = "",
                             scope: str = "") -> ToolResult:
        """List CanonProposals for a novel (transform), optionally filtered
        by status / scope. Newest first.

        Inputs: novel_id, status (optional — one of PROPOSAL_STATUS),
                scope (optional exact filter).
        Returns: ``{proposals: [{proposal_id, scope, tier, status,
                 proposed_by, decided_by, lock_id}], count}``.
        chain_next: ``novel.approve_canon`` on the open ones.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        if status and status not in PROPOSAL_STATUS:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"status={status!r} not in {sorted(PROPOSAL_STATUS)}")
        rows = [{"proposal_id": p["id"], "scope": p.get("scope", ""),
                 "tier": p.get("tier", ""), "status": p.get("status", ""),
                 "proposed_by": p.get("proposed_by", ""),
                 "decided_by": p.get("decided_by", ""),
                 "lock_id": p.get("lock_id", "")}
                for p in self.ctx.find("CanonProposal")
                if p.get("novel") == novel_id
                and (not status or p.get("status") == status)
                and (not scope or p.get("scope") == scope)]
        rows.sort(key=lambda r: r["proposal_id"], reverse=True)
        return ToolResult.success(data={
            "proposals": rows, "count": len(rows)})

    @verb(role="transform")
    def canon_gate(self, node_id: str, allow: str = "canonical",
                   override: bool = False) -> ToolResult:
        """The drafting hard-stop (transform): refuse to treat a
        proposal/quarry/gap node as fact without an explicit author override
        — the KP "check the Master-Index first" rule, chainable from any
        drafting skill.

        Inputs: node_id, allow (csv of acceptable statuses; default
                'canonical'), override (author's explicit go-ahead).
        Returns: ``{passed, status, advice}``.
        chain_next: ``novel.lock_index`` when blocked (consult, then decide).
        """
        node = self.ctx.recall(node_id)
        if node is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"node {node_id!r} not found")
        status = node.get("canon_status", "")
        allowed = {a.strip() for a in allow.split(",") if a.strip()}
        passed = override or status in allowed
        return ToolResult.success(data={
            "passed": passed, "status": status or "unmarked",
            "advice": ("" if passed else
                       f"status {status or 'unmarked'!r} not in {sorted(allowed)}"
                       f" — consult novel.lock_index before drafting on it, "
                       f"or pass override=True with author authority"),
        })
