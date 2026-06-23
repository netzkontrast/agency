# agency-scaffold: v1
"""intent — critical-thinking methods that reason about the serving intent (Spec 026/091).

Intent is the reasoning capability: it turns the human-owned goal into structured critical-thinking scaffolds — decomposition, assumption-surfacing, premortem, first-principles, inversion, steelman, second-order, and trade-off analysis — each a deterministic method an agent fills in against the current intent.

Use when: examining a goal before committing to an approach — decomposing it, surfacing its assumptions, stress-testing it with a premortem, or weighing trade-offs.
Triggers:
- A goal whose approach is unclear and needs structured decomposition
- A plan resting on unstated assumptions worth surfacing
- A decision between options that needs an explicit trade-off pass
- A risky course where a premortem would expose failure modes early
Red flags:
- Committing to an approach without surfacing assumptions → capability_intent_assumptions
- Shipping a risky plan unexamined → run capability_intent_premortem first
"""
from __future__ import annotations

from ...capability import ArtefactSchemas, CapabilityBase, verb
from ...ontology import OntologyExtension

# An AUTHORED walkable discipline (overrides the derived <cap>-usage, Spec 081): a real
# critical-thinking pass — frame the problem, decompose it, surface assumptions,
# premortem the risk, then decide.
_CRITICAL_THINKING_SKILL = {
    "name": "critical-thinking",
    "kind": "discipline",
    "applies_when": {"kind": "pattern",
                     "pattern": r"unclear|risky|decide|trade-?off|assumption|approach|why",
                     "confidence": 0.7},
    "phases": [
        # Spec 378 — inline phase content (A1/A6) for the critical-thinking pass.
        {"index": 1, "name": "frame", "produces": ["problem_statement"], "verbs": ["decompose"],
         "goal": "State the problem precisely before reasoning about it.",
         "instructions": "Decompose the intent into a sharp problem statement — what's "
                         "actually being decided, and why now. A fuzzy frame produces fuzzy "
                         "thinking.",
         "freedom": "high"},
        {"index": 2, "name": "surface", "produces": ["assumptions"], "verbs": ["assumptions"],
         "goal": "Surface the load-bearing assumptions.",
         "instructions": "List the assumptions the approach rests on — the ones that, if "
                         "wrong, change the decision. Name them explicitly so they can be "
                         "tested.",
         "freedom": "medium"},
        {"index": 3, "name": "stress-test", "produces": ["failure_modes"],
         "verbs": ["premortem", "inversion", "brooks_lint"],
         "goal": "Stress-test the approach against failure.",
         "instructions": "Pre-mortem it (how does it fail?), invert it (what must NOT "
                         "happen?), and brooks-lint it (essential vs accidental complexity). "
                         "Collect the failure modes the methods surface.",
         "freedom": "medium"},
        {"index": 4, "name": "weigh", "produces": ["tradeoffs"], "verbs": ["tradeoffs", "second_order"],
         "goal": "Weigh the tradeoffs and second-order effects.",
         "instructions": "For each viable option, state its tradeoff and its second-order "
                         "consequence. The best first-order choice often loses on the "
                         "second order.",
         "freedom": "medium"},
        {"index": 5, "name": "decide", "produces": ["chosen_approach"], "gate": "hard",
         "goal": "Commit to an approach with its rationale.",
         "instructions": "Choose, and state WHY this option beats the alternatives given "
                         "the assumptions + tradeoffs. Confirm this gate only with a "
                         "decision, not a shortlist.",
         "freedom": "low"},
    ],
}


class IntentCapability(CapabilityBase):
    name = "intent"
    home = "capability"
    # Spec 381 §4 — triage is an intent judgment about a Finding (a Finding SERVES
    # an intent). The Suppression/Acknowledgement nodes live here; the SUPPRESSES /
    # ACKNOWLEDGES edges cross to the analyze Finding (one shared graph).
    ontology = OntologyExtension(
        skills={"critical-thinking": _CRITICAL_THINKING_SKILL},
        nodes={
            # ``glob`` not ``pattern`` — graphqlite reserves ``pattern`` (it
            # round-trips as ``Pattern``, breaking case-sensitive reads).
            "Suppression": ["risk", "glob"],
            "Acknowledgement": ["risk", "glob"],
        },
        edges={"SUPPRESSES", "ACKNOWLEDGES"},
    )
    # Spec 153 Slice 6 — the engine loads + enforces the Intent/Invocation
    # provenance-spine schemas from schemas/ (declared, not glob-discovered).
    artefact_schemas = ArtefactSchemas.from_module(__file__)

    # ── the subject defaults to the serving intent (ambient), so a bare call reasons
    #    about the current goal; an explicit `subject` overrides. ──
    def _subject(self, explicit: str) -> str:
        if explicit:
            return explicit
        node = self.ctx.memory.recall(self.ctx.intent_id) or {}
        return (node.get("deliverable") or node.get("purpose") or "the current goal").strip()

    @verb(role="transform")
    def decompose(self, subject: str = "") -> dict:
        """Decompose a goal into MECE sub-problems — the structured break-down method.

        Inputs: subject (defaults to the serving intent's deliverable).
        Returns: ``{method, subject, steps, output}`` — a scaffold to fill in.
        chain_next: ``intent.assumptions`` on the riskiest sub-problem.
        """
        subject = self._subject(subject)
        return {"method": "decompose", "subject": subject, "steps": [
            f"State '{subject}' as a single sentence — the one thing that must be true.",
            "Split it into 3-6 sub-problems that are mutually exclusive + collectively exhaustive.",
            "For each sub-problem: is it necessary? is it sufficient on its own? what does it depend on?",
            "Mark the ONE sub-problem that, if wrong, sinks the whole goal.",
        ], "output": "a MECE sub-problem tree with the critical path flagged"}

    @verb(role="transform")
    def assumptions(self, subject: str = "") -> dict:
        """Surface + classify the implicit assumptions a goal rests on (load-bearing vs not).

        Inputs: subject (defaults to the serving intent).
        Returns: a scaffold separating assumptions you can test cheaply now.
        chain_next: ``intent.premortem`` on the load-bearing ones.
        """
        subject = self._subject(subject)
        return {"method": "assumptions", "subject": subject, "steps": [
            f"List everything that must be TRUE for '{subject}' to work — including the obvious.",
            "Tag each: LOAD-BEARING (the goal fails if false) vs incidental.",
            "For each load-bearing assumption: how would you cheaply test it BEFORE building?",
            "Flag any assumption you're believing because it's convenient, not because it's checked.",
        ], "output": "load-bearing assumptions, each with a cheap pre-test"}

    @verb(role="transform")
    def premortem(self, subject: str = "") -> dict:
        """Premortem — assume the goal FAILED, reason backward to causes + mitigations.

        Inputs: subject (defaults to the serving intent).
        Returns: a scaffold that elicits specific (not generic) failure modes.
        chain_next: fold the top mitigations into the plan.
        """
        subject = self._subject(subject)
        return {"method": "premortem", "subject": subject, "steps": [
            f"It's the deadline and '{subject}' failed badly. Write the post-mortem headline.",
            "List the most likely SPECIFIC causes (no generic 'ran out of time').",
            "For each: was it foreseeable? what early signal would have revealed it?",
            "Name the 2-3 highest-leverage mitigations to start NOW.",
        ], "output": "ranked, specific failure modes + the mitigations to start now"}

    @verb(role="transform")
    def first_principles(self, subject: str = "") -> dict:
        """Strip a goal to fundamental truths and rebuild — bypassing inherited assumptions.

        Inputs: subject (defaults to the serving intent).
        Returns: a scaffold separating physics from convention.
        chain_next: ``intent.tradeoffs`` on the rebuilt options.
        """
        subject = self._subject(subject)
        return {"method": "first_principles", "subject": subject, "steps": [
            f"What is '{subject}' REALLY trying to achieve — the underlying need, not the asked solution?",
            "List the facts that are true by physics/math/contract (cannot be argued away).",
            "List the constraints that are merely convention/habit/'how it's done'.",
            "Rebuild the simplest solution from the true facts only — ignore the conventions.",
        ], "output": "the goal rebuilt from first principles, conventions dropped"}

    @verb(role="transform")
    def inversion(self, subject: str = "") -> dict:
        """Invert the goal — ask what would GUARANTEE failure, then avoid exactly that.

        Inputs: subject (defaults to the serving intent).
        Returns: a scaffold of failure-guarantees to design against.
        chain_next: ``intent.premortem`` for likelihoods.
        """
        subject = self._subject(subject)
        return {"method": "inversion", "subject": subject, "steps": [
            f"How would you GUARANTEE '{subject}' fails? List the surest ways to wreck it.",
            "Which of those are you currently at risk of doing (even partly)?",
            "Invert each into a rule: 'never ___' / 'always ___'.",
            "Pick the single avoid-this that buys the most safety.",
        ], "output": "failure-guarantees inverted into design rules"}

    @verb(role="transform")
    def steelman(self, subject: str = "") -> dict:
        """Build the STRONGEST version of the opposing or alternative position.

        Inputs: subject (the position/approach to steelman; defaults to the intent).
        Returns: a scaffold that forces the best counter-case, not a strawman.
        chain_next: ``intent.tradeoffs`` between your view and the steelman.
        """
        subject = self._subject(subject)
        return {"method": "steelman", "subject": subject, "steps": [
            f"State the BEST case AGAINST '{subject}' (or for the leading alternative) — charitably.",
            "Add the strongest evidence/argument a smart proponent of it would give.",
            "What would have to be true for the alternative to be the right call?",
            "After steelmanning: does your original choice still hold, or did it move?",
        ], "output": "the strongest counter-case + whether your choice survives it"}

    @verb(role="transform")
    def second_order(self, subject: str = "") -> dict:
        """Trace second- and third-order consequences — 'and then what?' past the first effect.

        Inputs: subject (the action/decision; defaults to the intent).
        Returns: a scaffold that pushes past the immediate effect.
        chain_next: feed the downstream effects into ``intent.tradeoffs``.
        """
        subject = self._subject(subject)
        return {"method": "second_order", "subject": subject, "steps": [
            f"What is the immediate, intended effect of '{subject}'? (first order)",
            "And THEN what? — the effects of that effect (second order).",
            "And then what? — third order, incl. how people/systems adapt + game it.",
            "Which downstream effect is the one you'd regret missing?",
        ], "output": "the consequence chain past the first-order effect"}

    @verb(role="transform")
    def brooks_lint(self, target: str = "", kind: str = "spec") -> dict:
        """BROOKS-LINT — the 9th critical-thinking method: a conceptual-integrity
        pass grounded in Fred Brooks (*Mythical Man-Month* / *No Silver Bullet*).
        Unlike the scaffold methods, this one ANALYSES a target and returns
        decidable, evidence-anchored findings across five principles —
        conceptual-integrity · essential-vs-accidental · second-system ·
        no-silver-bullet · plan-to-throw-one-away. Catches the spec that is
        *clever but incoherent* (a class spec-panel's market lens misses). Decidable
        with NO API key; advisory — `block` is reserved for conceptual-integrity /
        irreversible-surface violations (the owner overrides in the improve-loop).

        Inputs: target (a spec Document id, raw spec/design text, or "" → the
                serving intent's deliverable), kind (label — default "spec").
        Returns: ``{target, kind, findings: [{principle, severity, msg, evidence}],
                 conceptual_integrity_ok, summary}``.
        chain_next: fold the findings into the spec's "## Brooks-lint findings
                    folded in" section (workflow 358 improve-loop).
        """
        from ._brooks import brooks_findings
        body = self._brooks_target(target)
        findings = brooks_findings(body)
        ok = not any(f["severity"] == "block" for f in findings)
        counts: dict[str, int] = {}
        for f in findings:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1
        head = ("conceptual integrity OK" if ok
                else "BLOCK — conceptual-integrity/irreversible violation")
        return {"target": target or "intent", "kind": kind, "findings": findings,
                "conceptual_integrity_ok": ok,
                "summary": f"{head}; {len(findings)} finding(s) {counts}"}

    def _brooks_target(self, target: str) -> str:
        """Resolve a brooks_lint target to body text: a Document id → its latest
        revision body; "" → the serving intent's deliverable; else raw text."""
        if not target:
            node = self.ctx.memory.recall(self.ctx.intent_id) or {}
            return (node.get("deliverable") or node.get("purpose") or "").strip()
        if self.ctx.recall_typed(target, "Document"):
            from agency.capabilities.document._interconnect import latest_revision_text
            return latest_revision_text(
                self.ctx.neighbors(target, "REVISION_OF", direction="in"))
        return target

    @verb(role="transform")
    def suggests(self, called_capability: str = "", called_verb: str = "",
                 called_state: str = "", floor: float = 0.5) -> dict:
        """Project the serving intent + the last verb's state to the next applicable
        skill (Spec 026 Part B — Intent owns the intent→skill projection; a
        RECOMMENDATION, not a dispatch). Evaluates each skill's optional
        ``applies_when`` Matcher across the whole registry.

        Matcher kinds: ``pattern`` (regex over the context); ``verb_code`` (invoke a
        decider verb returning ``{matches, confidence}`` — cycle-checked against the
        verb in flight); ``llm_select`` (ask the ``llm`` Driver — Spec 092 G3 — whether
        the skill applies; skipped when no LLM seam is configured).

        Inputs: called_capability / called_verb / called_state (the last step's
                context); floor (min confidence, default 0.5). The serving intent is
                read ambiently from ``ctx.intent_id``.
        Returns: ``{skill, mode, confidence, cue, matched_by}`` for the best match, or
                 ``{skill: None, reason}`` when nothing clears the floor.
        chain_next: ``develop.skill_walk`` the recommended skill, or ``skills.render`` it.
        """
        import re

        from ..skills import _all_skills          # reuse the registry-scan helper (DRY)
        parts = [called_capability, called_verb, called_state]
        node = self.ctx.memory.recall(self.ctx.intent_id) or {}
        parts += [node.get("purpose", ""), node.get("deliverable", ""),
                  node.get("acceptance", "")]
        context = " ".join(p for p in parts if p).lower()

        best = None
        for meta in _all_skills(self.ctx.registry).values():
            matcher = meta["_schema"].get("applies_when")
            if not matcher:
                continue
            kind = matcher.get("kind")
            matched, conf = False, 0.0
            if kind == "pattern":
                if re.search(matcher.get("pattern", ""), context, re.I):
                    matched, conf = True, float(matcher.get("confidence", 1.0))
            elif kind == "verb_code":
                vc = matcher.get("verb_code", {})
                cap, vb = vc.get("capability"), vc.get("verb")
                if (cap, vb) == (called_capability, called_verb):
                    continue                              # cycle-check: skip the verb in flight
                try:
                    rr = self.ctx.call(cap, vb, **(vc.get("args") or {}))
                    rr = rr.get("result", rr) if isinstance(rr, dict) else {}
                    matched, conf = bool(rr.get("matches")), float(rr.get("confidence", 0.0))
                except Exception:
                    matched, conf = False, 0.0
            elif kind == "llm_select":
                # Spec 092 G3 — ask the LLM-decider Driver whether this skill applies.
                from ...capability import DriverMissing
                try:
                    llm = self.ctx.get_driver("llm")
                except DriverMissing:
                    continue                              # no LLM seam configured → skip
                question = matcher.get("llm_select", {}).get("prompt", "Does this apply?")
                prompt = (f"Context: {context}\n\nSkill: {meta['name']}\n{question}")
                try:
                    rr = llm.decide(prompt, ["match", "skip"])
                    matched = rr.get("choice") == "match"
                    conf = float(rr.get("confidence", 0.0))
                except Exception:
                    matched, conf = False, 0.0
            if matched and conf >= floor and (best is None or conf > best["confidence"]):
                best = {"skill": meta["name"], "mode": kind, "confidence": conf,
                        "cue": meta["phases"][0] if meta["phases"] else "",
                        "matched_by": f"{kind}:{meta['name']}"}
        return best or {"skill": None, "reason": f"no matcher cleared the floor ({floor})"}

    @verb(role="transform")
    def tradeoffs(self, options: str = "", criteria: str = "") -> dict:
        """Build an explicit trade-off matrix — options × criteria — for a decision.

        Inputs: options (comma-separated; '' → elicit them); criteria (comma-separated;
                '' → suggest defaults). Defaults the subject to the serving intent.
        Returns: a matrix scaffold + the tie-breaking discipline.
        chain_next: ``intent.steelman`` the option you're about to reject.
        """
        opts = [o.strip() for o in options.split(",") if o.strip()] or ["<list the real options>"]
        crit = [c.strip() for c in criteria.split(",") if c.strip()] or \
            ["cost", "time", "risk", "reversibility", "maintenance"]
        return {"method": "tradeoffs", "options": opts, "criteria": crit, "steps": [
            f"Score each option {opts} against each criterion {crit} (concrete, not vibes).",
            "Mark which criteria are MUST-HAVE (a fail there eliminates the option).",
            "Weight the remaining criteria; the highest weighted-score wins.",
            "Name the tie-breaker you'd use, and the option you'd pick if forced now.",
        ], "output": "a scored options × criteria matrix with a decision + tie-breaker"}

    @verb(role="act")
    def triage(self, finding_id: str = "", action: str = "skip",
               reason: str = "", expires: str = "") -> dict:
        """Triage a Finding — the intent's stance on it (Spec 381 §4). A Finding
        SERVES an intent, so accept/dismiss/defer is a judgment the intent owns
        (beside assumptions / tradeoffs).

        - ``dismiss`` → records a ``Suppression{risk, pattern, reason}`` SERVING the
          intent + SUPPRESSES the Finding; the next scan drops a matching finding
          from the score (analyze reads it cross-capability).
        - ``defer`` → a Suppression with an expiry (default +90d); the finding
          resurfaces once expired.
        - ``accept`` → an ``Acknowledgement`` ACKNOWLEDGES the Finding ("known,
          won't fix" — queryable).
        - ``skip`` → no-op.

        ``risk`` + ``pattern`` are READ from the Finding node by ``finding_id`` (one
        source, no caller duplication). Keep-both: the Finding is never deleted; a
        Suppression only changes its tier on the scoring read (Spec 292).

        Inputs: finding_id (str), action (dismiss|defer|accept|skip), reason (str),
                expires (str — epoch; defer defaults +90d).
        Returns: {action, finding_id, node_id, risk, pattern} (or {action: skip}).
        chain_next: analyze.score / analyze.record_run — honoured on the next run.
        """
        import time
        if action == "skip" or not finding_id:
            return {"action": "skip", "finding_id": finding_id}
        finding = self.ctx.recall(finding_id) or {}
        risk = finding.get("risk_code", "")
        glob = finding.get("file", "")
        if action == "accept":
            node_id = self.ctx.record_and_serve(
                "Acknowledgement", {"risk": risk, "glob": glob, "reason": reason})
            self.ctx.link(node_id, finding_id, "ACKNOWLEDGES")
            return {"action": "accept", "finding_id": finding_id, "node_id": node_id,
                    "risk": risk, "glob": glob}
        props = {"risk": risk, "glob": glob, "reason": reason}
        if action == "defer":
            props["expires"] = expires or (time.time() + 90 * 86400)
        elif expires:
            props["expires"] = expires
        node_id = self.ctx.record_and_serve("Suppression", props)
        self.ctx.link(node_id, finding_id, "SUPPRESSES")
        return {"action": action, "finding_id": finding_id, "node_id": node_id,
                "risk": risk, "glob": glob}
