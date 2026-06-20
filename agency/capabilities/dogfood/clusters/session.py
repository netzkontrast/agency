"""dogfood.session — session-tracking: decisions, boundary audit, replay (Spec 114/195/154).

Spec 286 P3 — extracted verbatim from ``dogfood/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single DogfoodCapability.

Binds decisions to a session (record_decision), audits raw-tool bypasses
where a capability verb existed (boundary_use_audit), replays the typed
event chain serving an intent (replay_events), and pages a captured overflow
body (recall_overflow_slice).
"""
from __future__ import annotations

from agency.capability import verb


class SessionMixin:
    """Spec 114 — session-tracking: bind decisions + audit boundary uses."""

    # ════════════════════════════════════════════════════════════════════════
    # Spec 114 — session-tracking: bind decisions + audit boundary uses.
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="effect")
    def record_decision(self, subject: str, decision: str,
                         rationale: str = "",
                         next_action: str = "",
                         session_lifecycle_id: str = "") -> dict:
        """Bind a decision to the current session (effect).

        Creates a `DecisionRecord` node SERVING the intent. Optionally edges
        to a SessionLifecycle so the decision history is queryable.

        Inputs: subject (what was decided about), decision (the choice),
                rationale (why), next_action (what follows), session_lifecycle_id
                (optional — links the DecisionRecord to the session).
        Returns: ``{decision_id, subject, decision}``.
        chain_next: act on `next_action`, or `reflect.note` the rationale.
        """
        did = self.ctx.record_and_serve("DecisionRecord", {
            "subject": subject, "decision": decision,
            "rationale": rationale, "next_action": next_action,
        })
        if session_lifecycle_id:
            self.ctx.link(did, session_lifecycle_id, "RELATES_TO")
        return {"decision_id": did, "subject": subject,
                "decision": decision}

    @verb(role="transform")
    def boundary_use_audit(self,
                            for_intent_id: str = "",
                            session_lifecycle_id: str = "") -> dict:
        """Audit BoundaryUse nodes — flag raw-tool uses where a verb exists (transform).

        Reads BoundaryUse nodes (Spec 195 Slice 1: recorded by the
        engine's default hook handler when a raw Write/Edit/Bash fires
        under an active intent) and aggregates them into a typed audit
        report.

        Spec 195 invariants:
        - `bypass_count` is the sum of `by_tool` counts (no double-count).
        - When `for_intent_id` is given, only uses SERVING that intent
          are included (cross-intent contamination caught by the SERVES
          edge filter).
        - `samples` shows up to 5 representative records per tool (a
          paged audit reader can chain `dogfood.recall_overflow_slice`
          for the full set).

        Inputs: for_intent_id (str — filter to BoundaryUses serving
                this intent; "" = global).
                session_lifecycle_id (legacy alias; ignored when
                for_intent_id is set).
        Returns: ``{intent_id, bypass_count, by_tool: {Write, Edit, Bash, …},
                 samples: [{tool, target, verb_shadow, argument_summary,
                 session}], count}``.
        chain_next: ``dogfood.parse_amendment`` reads the bypass rate
                    when the dogfood loop classifies amendments.
        """
        # Suggestion mapping (Pillar 2 of Spec 114 — capability-first
        # routing). Spec 195 carries the live `verb_shadow` from the
        # BoundaryUse node; this dict is only a fallback for legacy
        # records (Slice 0 BoundaryUse nodes that pre-date Slice 1).
        _SUGGEST = {
            "Write":    "develop.scaffold_capability OR dogfood.observe",
            "Edit":     "dogfood.observe (spec edit) OR direct verb call",
            "Bash":     "shell.run OR branch.commit_smart OR develop.test",
            "WebFetch": "research.fetch (future)",
            "Grep":     "analyze.search (future)",
        }
        uses = self.ctx.find("BoundaryUse")
        # Filter by intent_id when requested. The BoundaryUse node
        # carries `intent_id` as a property; we use it directly rather
        # than walking SERVES edges to keep the filter O(N).
        if for_intent_id:
            uses = [u for u in uses
                    if u.get("intent_id") == for_intent_id]
        by_tool: dict[str, int] = {}
        samples_per_tool: dict[str, list[dict]] = {}
        for u in uses:
            tool = str(u.get("tool", ""))
            by_tool[tool] = by_tool.get(tool, 0) + 1
            bucket = samples_per_tool.setdefault(tool, [])
            if len(bucket) < 5:
                bucket.append({
                    "tool":             tool,
                    "target":           u.get("target", ""),
                    "verb_shadow":      u.get("verb_shadow")
                                          or _SUGGEST.get(tool, "(none)"),
                    "argument_summary": u.get("argument_summary", ""),
                    "session":          u.get("session", ""),
                })
        samples: list[dict] = []
        for tool in sorted(samples_per_tool):
            samples.extend(samples_per_tool[tool])
        return {
            "intent_id":    for_intent_id,
            "bypass_count": sum(by_tool.values()),
            "by_tool":      dict(sorted(by_tool.items())),
            "samples":      samples,
            "count":        sum(by_tool.values()),                 # legacy alias
        }

    @verb(role="transform")
    def replay_events(self, for_intent_id: str = "",
                       tool: str = "", limit: int = 100) -> dict:
        """Replay every Event recorded OBSERVED_DURING the given intent
        (Spec 195 Slice 2 — typed replay + monotonic chain).

        Returns the sequence of typed event rows in record order, each
        linked to its `prior_event_id` (the previous event in the same
        intent's replay; empty for the first). Slice 1 BoundaryUse nodes
        are joined in via the RECORDED_BY edge so the replay surface
        carries the moat metadata when present.

        Inputs: for_intent_id (str — required; the SERVES anchor).
                tool (str — optional filter; "" = every tool).
                limit (int — bound the row count; default 100).
        Returns: ``{intent_id, events: [{event_id, prior_event_id, name,
                  tool, session, target, verb_shadow, summary}], count}``.
        chain_next: ``dogfood.parse_amendment`` reads the replay when the
                    classifier needs the recent-event window.
        """
        intent_id = for_intent_id
        if not intent_id:
            return {"intent_id": "", "events": [], "count": 0}
        # Walk Event nodes that OBSERVED_DURING the intent; preserve
        # record-creation order (the in-graph id is a stable monotone
        # sequence per Spec 002 substrate guarantees).
        events = self.ctx.sources_via_edge(
            "OBSERVED_DURING", intent_id, "Intent", label="Event")
        # Stable order by created_at if present, else by id (record-order
        # convention). The graph appends in insertion order; we sort the
        # list explicitly to stay deterministic across query backends.
        events.sort(key=lambda p: (
            p.get("created_at", ""), str(p.get("id", ""))))
        if tool:
            events = [p for p in events if p.get("tool") == tool]
        events = events[: max(0, int(limit))]
        # Join BoundaryUse via the RECORDED_BY edge — collect every
        # BoundaryUse serving this intent, then index each by the Event id
        # it RECORDED_BY (one-hop out from the BoundaryUse).
        bu_by_event: dict[str, dict] = {}
        for bu in self.ctx.nodes_serving(intent_id, label="BoundaryUse"):
            for ev in self.ctx.neighbors(bu.get("id", ""), "RECORDED_BY",
                                         direction="out"):
                bu_by_event[str(ev.get("id", ""))] = bu
        out: list[dict] = []
        prev_id = ""
        for p in events:
            eid = str(p.get("id", ""))
            bu = bu_by_event.get(eid, {})
            out.append({
                "event_id":       eid,
                "prior_event_id": prev_id,
                "name":           p.get("name", ""),
                "tool":           p.get("tool", ""),
                "session":        p.get("session", ""),
                # FULL tool payload (no-truncate); `summary` retained for nodes
                # recorded before the rename.
                "summary":        p.get("payload") or p.get("summary", ""),
                "target":         bu.get("target", ""),
                "verb_shadow":    bu.get("verb_shadow", ""),
            })
            prev_id = eid
        return {
            "intent_id": intent_id,
            "events":    out,
            "count":     len(out),
        }

    @verb(role="transform")
    def recall_overflow_slice(self,
                                body: str = "",
                                slice: str = "full",
                                grep: str = "",
                                offset: int = 0,
                                byte_offset: int = 0,
                                max_tokens: int = 2000) -> dict:
        """Spec 154 Slice 3 — recall a paged view of a captured overflow body.

        Slice 2 of Spec 154 wired `capture_body_overflow` through the
        envelope; this verb is the read side. The caller supplies the
        full body (e.g. from a previously-stored Artefact); the verb
        delegates to the pure `_overflow.recall_overflow_slice` library
        with the configured budget. Slice 4 will add an Artefact-id-
        keyed lookup so the body never has to round-trip through the
        agent.

        Inputs: body (str — the full captured body the agent is paging).
                slice (str — "full" or "<start>:<stop>" line range).
                grep (str — pattern to filter matching lines).
                offset (int — grep paging offset).
                byte_offset (int — line slice intra-line cursor).
                max_tokens (int — budget for the returned slice).
        Returns: ``{body, slice_tokens, total_tokens, matches_returned,
                    more_available, next_match_offset, next_byte_offset}``.
        chain_next: ``dogfood.replay_events`` when the agent needs to
                    find the right body to recall first.
        """
        from agency._overflow import recall_overflow_slice as _recall

        def _proxy_counter(text: str) -> int:
            return len(text)

        # Spec 082 boundary lives on engine.token_counter; use it when
        # available, fall back to the deterministic char-proxy otherwise
        # (keeps tests hermetic without the Spec 082 backend).
        counter = _proxy_counter
        tc = getattr(self.ctx, "engine", None)
        tc = getattr(tc, "token_counter", None) if tc else None
        if tc is not None:
            counter = tc
        res = _recall(
            body, slice=slice, grep=grep, offset=offset,
            byte_offset=byte_offset, max_tokens=max_tokens,
            counter=counter,
        )
        return {
            "body":              res.body,
            "slice_tokens":      res.slice_tokens,
            "total_tokens":      res.total_tokens,
            "matches_returned":  res.matches_returned,
            "more_available":    res.more_available,
            "next_match_offset": res.next_match_offset,
            "next_byte_offset":  res.next_byte_offset,
        }
