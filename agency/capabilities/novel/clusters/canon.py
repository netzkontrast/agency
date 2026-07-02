"""novel.canon — canon provenance markers & locks (Spec 137).

The KP source-of-truth discipline: every canon fact carries a provenance
marker — ``[K]`` canonical · ``[V]`` proposal · ``[S]`` quarry (deprecated
raw stock) · ``[L]`` gap. ``canon_status`` rides as a cross-cutting property
on ANY novel-domain node (open-set substrate — marker, not node); only
``Lock`` is a new node because a lock has its own lifecycle (date, source,
supersession chain — newer wins, never deleted). ``canon_gate`` is the
hard-stop against silently canonizing speculation.
"""
from __future__ import annotations

import datetime as _dt

from agency.capability import verb
from agency.toolresult import Codes, ToolResult

#: [K] / [V] / [S] / [L]
CANON_STATUS = {"canonical", "proposal", "quarry", "gap"}

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
