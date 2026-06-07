"""delegate — agent orchestration: fan-out + quota + join.

Delegate weighs the token-economics and safety signals of dispatching, fans a task out to one or more drivers, and reduces their results back into a single answer.

Use when: a task might be better handled by a subagent (local, Jules, or another driver) and the choice to dispatch versus stay inline must be weighed, then work fanned out and the results joined.
Triggers:
- A task large or parallelizable enough to consider delegating
- Several independent sibling tasks that could run concurrently
- Uncertainty whether to dispatch a subagent or work inline
Red flags:
- Dispatching without weighing the cost → check capability_delegate_dispatch_decision first
- Spawning siblings then losing their results → reduce with capability_delegate_join
"""
from __future__ import annotations

from ...capability import ArtefactSchemas, CapabilityBase, verb
from ...ontology import OntologyExtension


def _phase(idx: int, name: str, produces: list[str], gate: str = "") -> dict:
    p: dict = {"index": idx, "name": name, "produces": produces}
    if gate:
        p["gate"] = gate
    return p


# The dispatch-decision skill: the token-economics heuristic, walked as a
# Lifecycle template every time the orchestrator considers a fan-out. Doctrine
# about Jules's behaviour lives in AGENCY_PROTOCOL.md; this skill is about
# the orchestrator's decision, so it lives here on `delegate` (the capability
# that owns the dispatch abstraction) — not on the protocol doc.
#
# Spec 040 extension: the 5-phase walk surfaces the eleven signals + two
# budget models. Phase 0 captures the new return-token-budget + cache + role
# signals (S1, S6, S7, S8, S9, S10, S11); the human-readable discipline lives
# in skills/dispatch-decision/SKILL.md + references/.
# Spec 041 — the parallel-fan-out discipline (Superpowers `dispatching-parallel-agents`,
# agency-flavoured): partition into INDEPENDENT domains, fan out, join, synthesize. The
# dispatch/join phases bind to `delegate`'s real verbs so walking it executes.
_DISPATCHING_PARALLEL_SKILL = {
    "name": "dispatching-parallel-agents",
    "kind": "discipline",
    "applies_when": {"kind": "pattern",
                     "pattern": r"parallel|independent|fan.?out|multiple (domains|tasks)",
                     "confidence": 0.7},
    "phases": [
        {"index": 1, "name": "partition",
         "produces": ["independent_domains"],            # 2+ NON-overlapping problem domains
         "verbs": ["delegate.dispatch_decision"]},       # confirm dispatch beats inline first
        {"index": 2, "name": "dispatch", "produces": ["delegations"],
         "verbs": ["delegate.fan_out"]},
        {"index": 3, "name": "join", "produces": ["results"], "verbs": ["delegate.join"]},
        {"index": 4, "name": "synthesize", "produces": ["merged_result"], "gate": "hard"},
    ],
}


_DISPATCH_DECISION_SKILL = {
    "name": "dispatch-decision",
    "kind": "discipline",
    "phases": [
        _phase(1, "estimate-tokens-and-cache", [
            "expected_return_tokens",  # int — subagent return-payload tokens (Spec 040 S1)
            "mutates",                 # bool — task writes graph/disk/external state (S6)
            "read_only",               # bool — orthogonal to mutates (S7)
            "driver_hint",             # str — caller preference: inline|local|jules|mcp (S8)
            "context_overlap",         # float 0..1 — parent already-loaded fraction (S9)
            "cache_warmth",            # float 0..1 — prompt-cache hit ratio (S10)
            "local_budget_relevant",   # bool — does this dispatch consume local budget (S11)
        ]),
        _phase(2, "estimate-shape", [
            "file_count",          # int — files the orchestrator has NOT seen (S2)
            "exploration_needed",  # bool — repeated grep/find through unfamiliar subtree (S3)
            "parallelism",         # int — sibling tasks that would dispatch together (S4)
            "est_duration_min",    # int — wall-clock when done inline (S5)
        ]),
        _phase(3, "apply-heuristic", [
            "recommendation",      # "inline" | "dispatch"
            "driver",              # "inline" | "local" | "jules" | "mcp"
            "rationale",           # one-paragraph why
            "signals_fired",       # list[str] — which of the 11 swung the decision
        ]),
        _phase(4, "assemble-bash-hints", [
            "bash_hints",          # list[str] — grep/sed/find cmds; empty when inline
        ]),
        _phase(5, "decide", ["decision"], gate="hard"),  # "inline" | "dispatch"
    ],
}


# ---------------------------------------------------------------------------
# Estimator helpers (Spec 040 §"Decision algorithm" line 322–325).
# Deterministic — pinned constants documented in the skill's
# cache-and-budget-model.md reference.
# ---------------------------------------------------------------------------

_LOCAL_SUBAGENT_ENVELOPE = 700        # Open Q1: pin via measurement; v1 estimate
_JULES_ENVELOPE = 500                 # bigger payload than local; less framing
_JULES_RETURN_SUMMARY = 500           # PR/diff summary back to parent
_CACHED_INPUT_RATIO = 0.10            # Anthropic 5-min cache: 10% of fresh (Spec 040 §"prompt-cache signal")
_SUBAGENT_RETURN_CAP = 2000           # Subagent summary cap before parent sees it
_MCP_PLACEHOLDER_COST = 1000          # F6 driver doesn't ship yet


def _estimate_local_tokens(s1_tokens: int, s9_overlap: float,
                           s10_warmth: float, driver: str) -> int:
    """Tokens that come out of the LOCAL interactive agent's budget."""
    if driver == "inline":
        # Overlap means parent already paid for that fraction; cache_warmth
        # discounts the rest at 10% per Anthropic prompt-cache pricing.
        effective = max(0.0, s1_tokens * (1.0 - s9_overlap))
        fresh = effective * (1.0 - s10_warmth)
        cached = effective * s10_warmth * _CACHED_INPUT_RATIO
        return int(fresh + cached)
    if driver == "local":
        # Subagent dispatch: envelope + bounded return summary; cold cache.
        return _LOCAL_SUBAGENT_ENVELOPE + min(s1_tokens, _SUBAGENT_RETURN_CAP)
    if driver == "jules":
        # Jules runs OUTSIDE the local budget; only the framing crosses back.
        return 0
    return _MCP_PLACEHOLDER_COST


def _estimate_total_work_tokens(s1_tokens: int, s5_dur_min: int, driver: str) -> int:
    """Total tokens spent across all parties (local + remote)."""
    if driver == "inline":
        return max(s1_tokens, 0)
    if driver == "local":
        return _LOCAL_SUBAGENT_ENVELOPE + max(s1_tokens, 0) + 200
    if driver == "jules":
        # Jules's full work is roughly proportional to duration; ~1k tok/min
        # as a coarse v1 estimate (Open Q1 — measure and pin).
        return _JULES_ENVELOPE + max(s1_tokens, s5_dur_min * 1000) + _JULES_RETURN_SUMMARY
    return 2 * _MCP_PLACEHOLDER_COST


def _is_effect_with_provenance(driver_hint: str) -> bool:
    """v1 stub. The S6 disqualifier needs to know whether the dispatched verb
    is an ``effect``-tagged verb that records ``PRODUCES``d artefacts. The
    dispatch_decision call site doesn't carry the verb's role tag today;
    until a future enhancement passes it through, the safer default is
    False — mutating tasks always stay inline. Spec 040 Open Q (implicit)."""
    return False


def _conflicts_with(driver_hint: str, signals: list[str]) -> bool:
    """Does the caller's driver_hint disagree with the fired signals?"""
    if not driver_hint:
        return False
    if driver_hint == "inline":
        # Caller hinted inline but our heuristic wants to dispatch → conflict.
        return True
    if driver_hint in ("local", "jules", "mcp"):
        # Caller hinted dispatch and we agree (signals fired); no conflict.
        return False
    return True   # unknown hint string → conflict (ignore the hint)


def _interactive_required(driver_hint: str = "") -> bool:
    """v1 stub. True means the user is waiting; false means async-OK and Jules
    can pick up long-runners. The driver_hint of `inline` is treated as a
    user-waiting signal; otherwise async is acceptable. Spec 040 Open Q
    (implicit — needs a future caller-provided ``interactive: bool`` param)."""
    return driver_hint == "inline"


def _compose_rationale(signals: list[str], driver: str) -> str:
    if driver == "inline":
        return ("clear in-context task; dispatch overhead "
                f"(~{_LOCAL_SUBAGENT_ENVELOPE} tokens preamble + review-cycle) "
                "exceeds inline cost.")
    if not signals:
        return f"dispatching to {driver} on caller request."
    return (f"dispatching to {driver} — signals fired: {', '.join(signals)}; "
            "subagent context-isolation + token amortisation justify the envelope.")




class DelegateCapability(CapabilityBase):
    name = "delegate"
    home = "lifecycle"
    artefact_schemas = ArtefactSchemas.from_module(__file__)
    ontology = OntologyExtension(
        nodes={"Delegation": ["driver", "driver_verb", "count", "quota"]},
        edges={"DELEGATES_TO", "REDUCES_INTO"},
        skills={"dispatch-decision": _DISPATCH_DECISION_SKILL,
                "dispatching-parallel-agents": _DISPATCHING_PARALLEL_SKILL},
    )

    @verb(role="transform")
    def dispatch_decision(
        self,
        # Existing four signals (Spec 040 S2-S5).
        file_count: int = 0,
        exploration_needed: bool = False,
        parallelism: int = 1,
        est_duration_min: int = 0,
        # New seven signals (Spec 040 §"eleven signals").
        expected_return_tokens: int = 0,         # S1 — subagent return-payload size
        mutates: bool = False,                   # S6 — disqualifier without provenance
        read_only: bool = True,                  # S7 — amplifies positive signals
        driver_hint: str = "",                   # S8 — caller preference (tie-breaker)
        context_overlap: float = 0.0,            # S9 — fraction already in parent context
        cache_warmth: float = 0.0,               # S10 — fraction prompt-cached at parent
        local_budget_relevant: bool = True,      # S11 — Jules sidesteps local budget
    ) -> dict:
        """Apply the dispatch-vs-inline heuristic and return a recommendation.

        Inputs: file_count (S2), exploration_needed (S3), parallelism (S4),
                est_duration_min (S5), expected_return_tokens (S1),
                mutates (S6 disqualifier), read_only (S7), driver_hint (S8),
                context_overlap (S9), cache_warmth (S10),
                local_budget_relevant (S11).
        Returns: ``{recommendation, driver, rationale, token_cost_estimate,
                 local_budget_token_estimate, signals_fired}`` — the six-field
                 payload documented in Spec 040 §"Done When". ``signals_fired``
                 reports which of the 11 swung the decision (incl. disqualifiers).
        chain_next: when ``recommendation == 'dispatch'``, call ``delegate.fan_out``
                    (driver=, driver_verb=, items=, quota=); when ``inline``,
                    execute in-process.

        See ``skills/dispatch-decision/references/heuristics.md`` for the full
        eleven-signal rule table + the two budget models (local vs. Jules).
        """
        signals: list[str] = []

        # ----- Disqualifier 1: mutating + not-effect-with-provenance → inline.
        if mutates and not _is_effect_with_provenance(driver_hint):
            return self._inline(
                rationale=("mutating task without effect-with-provenance discipline; "
                           "inline keeps the provenance edge intact."),
                signals=["S6:mutates"],
                s1_tokens=expected_return_tokens,
                s9_overlap=context_overlap,
                s10_warmth=cache_warmth,
            )

        # ----- Disqualifier 2: local-budget penalties (S9 / S10).
        # Only fires when the LOCAL budget matters — Jules sidesteps both.
        if local_budget_relevant:
            if context_overlap >= 0.7 and expected_return_tokens < 5000:
                return self._inline(
                    rationale=("parent context already holds the working set "
                               "(overlap ≥ 0.7) and return payload is small; "
                               "subagent would re-load cold."),
                    signals=["S9:overlap-high"],
                    s1_tokens=expected_return_tokens,
                    s9_overlap=context_overlap,
                    s10_warmth=cache_warmth,
                )
            if cache_warmth >= 0.6 and est_duration_min < 30:
                return self._inline(
                    rationale=("parent prompt-cache is hot (cached input ≈ 10% cost) "
                               "and inline duration is short; cache amortises faster "
                               "than dispatch envelope pays back."),
                    signals=["S10:cache-hot"],
                    s1_tokens=expected_return_tokens,
                    s9_overlap=context_overlap,
                    s10_warmth=cache_warmth,
                )

        # ----- Positive signals.
        if expected_return_tokens >= 5000 and local_budget_relevant:
            signals.append("S1:tokens")
        if file_count >= 4 and context_overlap < 0.5:
            signals.append("S2:files")
        if exploration_needed:
            signals.append("S3:explore")
        if parallelism >= 3:
            signals.append("S4:parallel")
        if est_duration_min >= 15:
            signals.append("S5:duration")
        if read_only and signals:
            signals.append("S7:read_only_amplifies")
        # Jules-specific positive: heavy task that doesn't touch local budget.
        if not local_budget_relevant and (expected_return_tokens >= 2000
                                          or est_duration_min >= 30):
            signals.append("S11:jules-budget-free")

        if not signals:
            return self._inline(
                rationale=("no positive signals; dispatch overhead "
                           f"(~{_LOCAL_SUBAGENT_ENVELOPE} tokens preamble + "
                           "review-cycle) exceeds inline cost."),
                signals=[],
                s1_tokens=expected_return_tokens,
                s9_overlap=context_overlap,
                s10_warmth=cache_warmth,
            )

        # ----- Driver selection (cost-model aware).
        if not local_budget_relevant:
            driver = "jules"                       # caller opted out of local budget
        elif parallelism >= 3:
            driver = "local"                       # fan-out, isolated contexts
        elif est_duration_min >= 45 and not _interactive_required(driver_hint):
            driver = "jules"                       # heavy + async-OK → offload
        elif driver_hint and not _conflicts_with(driver_hint, signals):
            driver = driver_hint
            if driver_hint and not any(s.startswith("S8") for s in signals):
                signals.append(f"S8:driver_hint={driver_hint}")
        else:
            driver = "local"

        local_cost = _estimate_local_tokens(
            expected_return_tokens, context_overlap, cache_warmth, driver)
        total_cost = _estimate_total_work_tokens(
            expected_return_tokens, est_duration_min, driver)

        return {
            "recommendation": "dispatch",
            "driver": driver,
            "rationale": _compose_rationale(signals, driver),
            "token_cost_estimate": total_cost,
            "local_budget_token_estimate": local_cost,
            "signals_fired": signals,
        }

    def _inline(self, rationale: str, signals: list[str],
                s1_tokens: int, s9_overlap: float, s10_warmth: float) -> dict:
        local = _estimate_local_tokens(s1_tokens, s9_overlap, s10_warmth, "inline")
        return {
            "recommendation": "inline",
            "driver": "inline",
            "rationale": rationale,
            "token_cost_estimate": local,
            "local_budget_token_estimate": local,
            "signals_fired": signals,
        }

    @verb(role="transform")
    def dispatch_bash_hints(self, paths: str = "", symbols: str = "") -> dict:
        """Compose the bash-hint context block for a dispatch prompt.

        Inputs: paths (comma-separated dirs/globs), symbols (comma-separated
                grep terms). Both empty → empty hints.
        Returns: ``{hints: [str], block: str}`` where ``block`` is the
                 ready-to-paste markdown.
        chain_next: paste ``block`` into the dispatched agent's prompt.

        When the orchestrator decides to dispatch (per ``dispatch_decision``),
        hand the agent the exact bash commands that surface the right files
        — cheap on orchestrator tokens, fast for the agent.
        """
        import shlex
        ps = [s.strip() for s in paths.split(",") if s.strip()] if paths else []
        ss = [s.strip() for s in symbols.split(",") if s.strip()] if symbols else []
        hints: list[str] = []
        # shlex.quote so a path containing a space / a symbol containing
        # a single quote remains DATA — the dispatched agent runs these
        # hints, so unquoted interpolation is a real injection vector.
        for p in ps:
            hints.append(f"find {shlex.quote(p)} -type f | head -50")
        for s in ss:
            hints.append(
                f"grep -rn {shlex.quote(s)} agency/ tests/ "
                f"2>/dev/null | head -30")
        if not hints:
            return {"hints": [], "block": ""}
        body = "\n".join(hints)
        block = (
            "Context — read these first, in this order:\n\n"
            f"```bash\n{body}\n```\n"
        )
        return {"hints": hints, "block": block}

    @verb(role="effect")
    def fan_out(self, driver: str, driver_verb: str, items: list, quota: int = 8) -> dict:
        """Open one child Lifecycle per item (capped at `quota`), dispatch the driver
        for each, and record a Delegation that DELEGATES_TO every child.

        Inputs: driver (capability name), driver_verb (str), items (list[dict] —
                each dict unpacked as driver kwargs), quota (int — admission cap).
        Returns: ``{delegation, dispatched, skipped, children: [{lifecycle, result}]}``
                 (wire shape); ``{error, quota|offending}`` on validation fail.
        chain_next: ``delegate.join(delegation=)`` after children complete.

        Children start ``working`` (dispatched ≠ done).
        """
        if quota < 0:                                          # negative slicing would over-admit
            return {"result": {"error": "quota must be >= 0", "quota": quota}}
        nonmap = [it for it in items if not isinstance(it, dict)]
        if nonmap:                                             # each item is unpacked as driver kwargs
            return {"result": {"error": "every item must be a mapping of driver kwargs",
                               "offending": nonmap[:3]}}
        admitted = items[:quota]
        d = self.ctx.record("Delegation", {"driver": driver, "driver_verb": driver_verb,
                                            "count": len(admitted), "quota": quota})
        self.ctx.link(d, self.ctx.intent_id, "SERVES")
        aid = f"agent:{driver}"
        if self.ctx.recall(aid) is None:
            self.ctx.record("Agent", {"runtime": "delegated"}, node_id=aid)
        children = []
        for item in admitted:
            lc = self.ctx.record("Lifecycle", {"state": "working", "phase": 0})
            self.ctx.link(lc, self.ctx.intent_id, "SERVES")
            self.ctx.link(lc, aid, "DISPATCHED_TO")        # an agent IS a Lifecycle parameterization
            self.ctx.link(d, lc, "DELEGATES_TO")
            result, inv = self.ctx.spawn(driver, driver_verb, **item)
            self.ctx.link(lc, inv, "DRIVES")               # the child Lifecycle drives its dispatch
            children.append({"lifecycle": lc, "result": result})
        return {"result": {"delegation": d, "dispatched": len(admitted),
                           "skipped": len(items) - len(admitted), "children": children}}

    @verb(role="act")
    def join(self, delegation: str) -> dict:
        """Reduce a delegation over its children's Lifecycle state.

        Inputs: delegation (Delegation node id from ``fan_out``).
        Returns: ``{children, states, done, reduction}`` (wire shape);
                 ``done=True`` iff every child Lifecycle is ``completed``;
                 ``{error, delegation}`` on cross-intent rejection.
        chain_next: when ``done=False``, walk the child lifecycles and
                    address ``input-required`` pauses; re-call ``join``.

        Writes a REDUCES_INTO reduction (so it is an ``act``, not a pure
        read).
        """
        if not self.ctx.memory.g.query(                        # no cross-intent reductions
                "MATCH (d:Delegation)-[:SERVES]->(i:Intent) WHERE d.id = $d AND i.id = $i RETURN i",
                {"d": delegation, "i": self.ctx.intent_id}):
            return {"result": {"error": "delegation does not serve the current intent",
                               "delegation": delegation}}
        rows = self.ctx.memory.g.query(
            "MATCH (d:Delegation)-[:DELEGATES_TO]->(lc:Lifecycle) WHERE d.id = $id RETURN lc",
            {"id": delegation})
        states: dict[str, int] = {}
        for r in rows:
            s = r["lc"]["properties"].get("state", "?")
            states[s] = states.get(s, 0) + 1
        children = len(rows)
        done = children > 0 and states.get("completed", 0) == children
        red = self.ctx.record("Artefact", {"kind": "reduction", "children": children})
        self.ctx.link(delegation, red, "REDUCES_INTO")
        self.ctx.link(red, self.ctx.intent_id, "SERVES")
        return {"result": {"children": children, "states": states, "done": done, "reduction": red}}
