"""Intent — the human-owned root (why/what merged; deliverable is an attribute).

capture -> confirm -> (amend via supersede). Everything edges back here via
SERVES. why/what are NOT two domains: a deliverable change with the purpose held
is just an attribute change on one Intent (the panel's finding).

Spec 048 — Intent chaining + owners:
  - ``parent_intent_id`` (default '') links sub-intents to roots via the
    PARENT_INTENT edge; cycle detection refuses self/loop chains.
  - ``owner`` (closed enum: user/agent/subagent/jules/system) tags WHO
    minted the intent. Default: 'user' for roots, 'agent' for children.
"""
from __future__ import annotations

from .memory import Memory


_MAX_CHAIN_DEPTH = 32          # pathological-deep guard (Spec 048 §"cycle")


class Intent:
    def __init__(self, memory: Memory):
        self.m = memory

    def capture(self, purpose: str, deliverable: str, acceptance: str,
                parent_intent_id: str = "",
                owner: str = "") -> str:
        """Mint an Intent node.

        Spec 048: ``parent_intent_id`` links to an existing parent (PARENT_INTENT
        edge + property); ``owner`` tags who minted (enum-enforced).

        Default-by-presence rule:
          - parent_intent_id == '' → owner defaults to 'user' (a root intent
            originated from a user prompt).
          - parent_intent_id != '' → owner defaults to 'agent' (a sub-intent
            scoped by the running agent).
        Explicit ``owner`` always overrides the default.
        """
        # Default owner inferred from presence of parent, then explicit wins.
        if not owner:
            owner = "agent" if parent_intent_id else "user"
        # Cycle / depth guard BEFORE recording — fail-loud is the doctrine.
        if parent_intent_id:
            # Reject typo'd / stale parent ids up front. Without this the
            # child Intent is recorded and PARENT_INTENT-linked to a
            # non-existent or non-Intent endpoint; provenance + parent-
            # chain traversals (analyze.paths, document.render) then drop
            # the new intent silently.
            parent_props = self.m.recall(parent_intent_id)
            if not parent_props:
                raise ValueError(
                    f"parent_intent_id {parent_intent_id!r} does not resolve "
                    f"to an Intent (typo, stale, or never recorded)")
            # We don't yet have a new_id; we still need a cycle check that
            # walks the parent chain up to MAX. The new_id can't be in the
            # ancestry because it doesn't exist yet, so just enforce depth.
            self._check_parent_depth(parent_intent_id)
        iid = self.m.record("Intent", {
            "purpose": purpose,
            "deliverable": deliverable,
            "acceptance": acceptance,
            "status": "draft",
            "owner": owner,
            "parent_intent_id": parent_intent_id,
        })
        if parent_intent_id:
            self.m.link(iid, parent_intent_id, "PARENT_INTENT")
        return iid

    def confirm(self, intent_id: str) -> str:
        # in place: confirming doesn't fork identity, so SERVES edges stay stable
        self.m.update(intent_id, {"status": "confirmed"})
        return intent_id

    def amend(self, intent_id: str, **changes) -> str:
        # the *what* changes while the *why* holds — one bi-temporal supersede,
        # so the prior version keeps its valid window (as-of reconstruction).
        return self.m.supersede(intent_id, changes)

    def capture_and_confirm(self, purpose: str, deliverable: str,
                            acceptance: str,
                            parent_intent_id: str = "",
                            owner: str = "") -> str:
        """Mint AND confirm an Intent in one step — the canonical bootstrap.

        Shared by the bash CLI (``agency.cli`` ``intent`` subcommand) and the
        MCP substrate tool (``intent_bootstrap`` in ``engine.build_mcp``), so
        both surfaces produce identical Intent nodes for the same inputs
        (Spec 029 §E isomorphism invariant + Spec 048 chain/owner semantics).
        """
        iid = self.capture(purpose, deliverable, acceptance,
                           parent_intent_id=parent_intent_id, owner=owner)
        self.confirm(iid)
        return iid

    # ------------------------------------------------------------------
    # Spec 048 internals — cycle detection + parent-chain traversal.
    # ------------------------------------------------------------------

    def _lookup_parent(self, intent_id: str) -> str:
        """Read an Intent's parent_intent_id property, or '' if missing."""
        props = self.m.recall(intent_id)
        if not props:
            return ""
        return props.get("parent_intent_id", "") or ""

    def _check_no_cycle(self, parent_id: str, new_id: str) -> None:
        """Walk up ``parent_id``'s PARENT_INTENT chain; raise ValueError if
        ``new_id`` appears OR the chain exceeds ``_MAX_CHAIN_DEPTH``.

        Used by amend-time mutations + tests; capture()'s pre-record path
        only needs the depth check because the new id can't be in the
        existing graph yet.
        """
        seen = {new_id}
        current = parent_id
        depth = 0
        while current and depth < _MAX_CHAIN_DEPTH:
            if current in seen:
                raise ValueError(
                    f"PARENT_INTENT cycle: {new_id!r} → ... → "
                    f"{current!r} → loops back to {new_id!r}")
            seen.add(current)
            current = self._lookup_parent(current)
            depth += 1
        if depth >= _MAX_CHAIN_DEPTH and current:
            raise ValueError(
                f"PARENT_INTENT chain too deep (>{_MAX_CHAIN_DEPTH}) "
                f"from {new_id!r} — pathological; root the new intent instead")

    def _check_parent_depth(self, parent_id: str) -> None:
        """At capture() time, the new id isn't in the graph yet, so cycle
        is impossible — only the chain-too-deep guard applies."""
        current = parent_id
        depth = 0
        while current and depth < _MAX_CHAIN_DEPTH:
            current = self._lookup_parent(current)
            depth += 1
        if depth >= _MAX_CHAIN_DEPTH and current:
            raise ValueError(
                f"PARENT_INTENT chain too deep (>{_MAX_CHAIN_DEPTH}) "
                f"from parent {parent_id!r} — pathological; root the new "
                "intent instead")
