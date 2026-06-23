# agency-scaffold: v1
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
from ...skill import phase as _phase  # Spec 286 — shared phase() builder


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
        # Spec 378 — inline phase content (A1/A6) for parallel fan-out.
        {"index": 1, "name": "partition",
         "produces": ["independent_domains"],            # 2+ NON-overlapping problem domains
         "verbs": ["delegate.dispatch_decision"],        # confirm dispatch beats inline first
         "goal": "Split the work into independent domains.",
         "instructions": "Identify 2+ NON-overlapping problem domains that can proceed "
                         "without shared state. First confirm dispatch beats inline (walk "
                         "dispatch-decision) — parallelism only pays when the domains are "
                         "genuinely independent.",
         "freedom": "medium"},
        {"index": 2, "name": "dispatch", "produces": ["delegations"],
         "verbs": ["delegate.fan_out"],
         "goal": "Fan out one worker per domain.",
         "instructions": "delegate.fan_out a worker per independent domain; each gets a "
                         "self-contained task and does not coordinate mid-flight.",
         "freedom": "medium"},
        {"index": 3, "name": "join", "produces": ["results"], "verbs": ["delegate.join"],
         "goal": "Collect every worker's result.",
         "instructions": "delegate.join — wait for ALL workers; collect results + failures. "
                         "A partial join is a failed fan-out, not a success.",
         "freedom": "low"},
        {"index": 4, "name": "synthesize", "produces": ["merged_result"], "gate": "hard",
         "goal": "Merge the results into one coherent output.",
         "instructions": "Reconcile the workers' outputs and resolve conflicts at the "
                         "seams. Confirm this gate only when the merged result is coherent "
                         "— not merely concatenated.",
         "freedom": "medium"},
    ],
}


_DISPATCH_DECISION_SKILL = {
    "name": "dispatch-decision",
    "kind": "discipline",
    "phases": [
        # Spec 378 — inline phase content (A1/A6) for the 11-signal heuristic.
        _phase(1, "estimate-tokens-and-cache", [
            "expected_return_tokens",  # int — subagent return-payload tokens (Spec 040 S1)
            "mutates",                 # bool — task writes graph/disk/external state (S6)
            "read_only",               # bool — orthogonal to mutates (S7)
            "driver_hint",             # str — caller preference: inline|local|jules|mcp (S8)
            "context_overlap",         # float 0..1 — parent already-loaded fraction (S9)
            "cache_warmth",            # float 0..1 — prompt-cache hit ratio (S10)
            "local_budget_relevant",   # bool — does this dispatch consume local budget (S11)
        ],
            goal="Estimate the token + cost-model signals (S1, S6–S11).",
            instructions="Estimate the return-token size, whether the task mutates / is "
                         "read-only, any driver hint, and the cache signals (context "
                         "overlap, cache warmth, local-budget relevance). These feed the "
                         "cost half of the heuristic.",
            freedom="low"),
        _phase(2, "estimate-shape", [
            "file_count",          # int — files the orchestrator has NOT seen (S2)
            "exploration_needed",  # bool — repeated grep/find through unfamiliar subtree (S3)
            "parallelism",         # int — sibling tasks that would dispatch together (S4)
            "est_duration_min",    # int — wall-clock when done inline (S5)
        ],
            goal="Estimate the work-shape signals (S2–S5).",
            instructions="Count the unfamiliar files, whether repeated exploration is "
                         "needed, parallel siblings, and the inline wall-clock. These are "
                         "the work-shape inputs.",
            freedom="low"),
        _phase(3, "apply-heuristic", [
            "recommendation",      # "inline" | "dispatch"
            "driver",              # "inline" | "local" | "jules" | "mcp"
            "rationale",           # one-paragraph why
            "signals_fired",       # list[str] — which of the 11 swung the decision
        ],
            goal="Apply the eleven-signal heuristic.",
            instructions="Run the two disqualifiers FIRST, then score the signals → a "
                         "recommendation + driver + rationale + which signals fired. Name "
                         "the signals; don't hand-wave the call.",
            freedom="low"),
        _phase(4, "assemble-bash-hints", [
            "bash_hints",          # list[str] — grep/sed/find cmds; empty when inline
        ],
            goal="Assemble bash hints for the chosen path.",
            instructions="If dispatching, assemble the grep/sed/find hints the worker "
                         "needs to find its way; leave empty when the call is inline.",
            freedom="low"),
        _phase(5, "decide", ["decision"], gate="hard",  # "inline" | "dispatch"
            goal="Commit to inline vs dispatch.",
            instructions="State the final decision (inline | dispatch) with its driver. "
                         "Confirm this gate only when the rationale is grounded in the "
                         "fired signals, not a hunch.",
            freedom="low"),
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
        # S12 — optional LLM tie-breaker via the OpenRouter free-model driver.
        use_llm: bool = False,                   # S12 — consult LLMClient when True
        task_description: str = "",              # plain-text description fed to the LLM
        llm_confidence_threshold: float = 0.75, # minimum confidence to accept LLM override
    ) -> dict:
        """Apply the dispatch-vs-inline heuristic and return a recommendation.

        Inputs: file_count (S2), exploration_needed (S3), parallelism (S4),
                est_duration_min (S5), expected_return_tokens (S1),
                mutates (S6 disqualifier), read_only (S7), driver_hint (S8),
                context_overlap (S9), cache_warmth (S10),
                local_budget_relevant (S11),
                use_llm (S12 — optional; consult the ``llm`` Driver after the
                heuristic; requires OPENROUTER_API_KEY),
                task_description (plain text fed to the LLM when use_llm=True),
                llm_confidence_threshold (float, default 0.75; LLM override only
                applied when its confidence exceeds this value).
        Returns: ``{recommendation, driver, rationale, token_cost_estimate,
                 local_budget_token_estimate, signals_fired}`` — the six-field
                 payload documented in Spec 040 §"Done When". ``signals_fired``
                 reports which of the 11 (+ optional S12) swung the decision.
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

        # ----- S12 — optional LLM tie-breaker (OpenRouter free-model driver).
        # Fires AFTER the heuristic so the LLM has a concrete initial decision
        # to validate or override.  Silently skips if the driver is unavailable
        # or if the LLM call fails — the heuristic result stands in that case.
        if use_llm:
            llm_override = self._llm_dispatch_signal(
                task_description=task_description,
                heuristic_driver=driver,
                signals_fired=signals,
                confidence_threshold=llm_confidence_threshold,
            )
            if llm_override:
                driver, signals = llm_override["driver"], llm_override["signals"]

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

    @staticmethod
    def _generate_dispatch_system_prompt(
        heuristic_driver: str,
        signals_fired: list[str],
    ) -> str:
        """Build a rich, context-aware system prompt for the S12 dispatch LLM decision.

        Includes driver trade-offs, heuristic context, signals that fired, and explicit
        decision criteria — giving the model enough signal to make a high-quality override
        decision without hallucinating routing logic.
        """
        signals_block = (
            "\n".join(f"  - {s}" for s in signals_fired) if signals_fired else "  (none)"
        )
        return (
            "You are a dispatch-routing advisor for the agency agentic framework.\n"
            "Your role: validate or override a deterministic heuristic routing decision\n"
            "for a software engineering task by choosing the best execution driver.\n\n"
            "DRIVER OPTIONS:\n"
            "  local  — spawn an isolated local subagent (fast, bounded context, in-process)\n"
            "  jules  — send to Jules async coding agent (long-running, offline, high budget)\n"
            "  inline — handle in the current agent without dispatch (lowest overhead)\n\n"
            f"HEURISTIC RESULT: {heuristic_driver!r}\n\n"
            "SIGNALS THAT FIRED:\n"
            f"{signals_block}\n\n"
            "DECISION CRITERIA (apply in order):\n"
            "  1. Return tokens >= 5000 or >= 4 unfamiliar files → prefer local or jules\n"
            "  2. Wall-clock >= 15 min or task is async/offline → prefer jules\n"
            "  3. Task mutates shared state (S6) without provenance → local or jules only\n"
            "  4. Read-only + context overlap < 0.7 + cache warm → prefer inline\n"
            "  5. When uncertain, confirm the heuristic; only override with high confidence.\n\n"
            'Reply ONLY with JSON: {"choice": "<local|jules|inline>", "confidence": <0.0-1.0>}\n'
            "Set confidence >= 0.75 only when you are confident the heuristic needs overriding."
        )

    def _llm_dispatch_signal(
        self,
        task_description: str,
        heuristic_driver: str,
        signals_fired: list[str],
        confidence_threshold: float,
    ) -> dict | None:
        """Consult the ``llm`` Driver (OpenRouter free model) to validate or
        override the heuristic driver choice.  Returns ``{driver, signals}``
        when the LLM answer meets the confidence threshold, else ``None``."""
        from ...capability import DriverMissing
        try:
            llm = self.ctx.get_driver("llm")
        except DriverMissing:
            return None
        options = ["local", "jules", "inline"]
        system_prompt = self._generate_dispatch_system_prompt(
            heuristic_driver=heuristic_driver,
            signals_fired=signals_fired,
        )
        prompt = (
            f"Task description: {task_description or '(no description provided)'}\n\n"
            f"The heuristic picked {heuristic_driver!r}. "
            f"Should it be confirmed or overridden? Choose one of: local, jules, inline."
        )
        try:
            result = llm.decide(prompt, options, system=system_prompt)
        except Exception:
            return None
        choice = result.get("choice", "")
        confidence = float(result.get("confidence", 0.0))
        if choice not in options or confidence < confidence_threshold:
            return None
        new_signals = list(signals_fired)
        if choice != heuristic_driver:
            new_signals.append(f"S12:llm_override={choice}(conf={confidence:.2f})")
        else:
            new_signals.append(f"S12:llm_confirms={choice}(conf={confidence:.2f})")
        return {"driver": choice, "signals": new_signals}

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
    def fan_out(self, driver: str, driver_verb: str, items: list, quota: int = 8,
                parameterization: str = "") -> dict:
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
        # Spec 342 — an agent IS a Lifecycle parameterization. The child's machine
        # comes from the DRIVER's declared `parameterization` (jules → "remote-async",
        # enforcing verify), not a hardcoded constant — so a local driver (no attr)
        # runs the default a2a machine and a remote one inserts its observer state.
        # An explicit `parameterization=` argument (e.g. subagent → "reviewed") wins.
        driver_cap = self.ctx.registry._caps.get(driver)
        param = parameterization or (getattr(driver_cap, "parameterization", "") if driver_cap else "")
        d = self.ctx.record_and_serve("Delegation", {"driver": driver, "driver_verb": driver_verb,
                                                      "count": len(admitted), "quota": quota})
        aid = f"agent:{driver}"
        if self.ctx.recall(aid) is None:
            self.ctx.record("Agent", {"runtime": "delegated"}, node_id=aid)
        children = []
        for item in admitted:
            # Spec 339 — mint the child through the Lifecycle PILLAR substrate
            # (ctx.lifecycle.open) instead of hand-rolling record_and_serve(
            # "Lifecycle", {state}). open mints the machine's initial state +
            # SERVES the intent + DISPATCHED_TO the agent; dispatch then advances
            # it to `working` via the SOLE state writer.
            lc = self.ctx.lifecycle.open(self.ctx.intent_id, agent=driver,
                                         parameterization=param,
                                         machine=param or "a2a")
            # Spec 342 — stamp the observer context the parameterization needs at
            # advance time (e.g. the branch jules.verify re-checks on origin).
            if isinstance(item, dict) and item.get("branch"):
                self.ctx.lifecycle.annotate(lc, branch=item["branch"])
            self.ctx.lifecycle.move(lc, "working")         # submitted → working at dispatch
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
        if not self.ctx.has_edge(delegation, self.ctx.intent_id, "SERVES",  # no cross-intent reductions
                                 src_label="Delegation", dst_label="Intent"):
            return {"result": {"error": "delegation does not serve the current intent",
                               "delegation": delegation}}
        child_lcs = self.ctx.neighbors(delegation, "DELEGATES_TO", direction="out")
        # Spec 342 — close the N3 disconnect: run each child's declared observer
        # through the ONE reducer (ctx.lifecycle.advance) BEFORE reducing. For a
        # remote-async child in `verify`, advance runs jules.verify and moves
        # verify→completed|input-required — so join's "done" IS the observer's
        # "done", not the raw `completed`. A default child (no observer) → no-op.
        for lc in child_lcs:
            cid = lc.get("id", "")
            if cid:
                self.ctx.lifecycle.advance(cid)
        # Re-read post-advance: the observer may have moved children.
        child_lcs = self.ctx.neighbors(delegation, "DELEGATES_TO", direction="out")
        states: dict[str, int] = {}
        for lc in child_lcs:
            s = lc.get("state", "?")
            states[s] = states.get(s, 0) + 1
        children = len(child_lcs)
        done = children > 0 and states.get("completed", 0) == children
        red = self.ctx.record("Artefact", {"kind": "reduction", "children": children})
        self.ctx.link(delegation, red, "REDUCES_INTO")
        self.ctx.link(red, self.ctx.intent_id, "SERVES")
        return {"result": {"children": children, "states": states, "done": done, "reduction": red}}
