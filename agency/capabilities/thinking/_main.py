# agency-scaffold: v1
"""thinking — critical-thinking capability (Spec 110 Slice 1).

10 method verbs (8 founding + 2 net-new: red_team + socratic) + 1 composite
(apply_full_review) + 1 walkable skill (critical-thinking).

Each method is a transform: returns a structured scaffold the agent fills
out. Methods compose; apply_full_review runs the 8 founding methods in
sequence + records a thinking-analysis artefact.

Slice 2 adds: pre_commitment / bayesian_update / if_then_else /
analogy_map (4 more methods), apply_decision_discipline + apply_design_review
(2 more composites), red-team-pass + decision-discipline walkable skills,
intent capability migration to thin wrappers (per Spec 111).

Use when: structured rigor needed before commit; binding decisions need tradeoff + premortem + red-team; an assumption stack needs surfacing.
Triggers:
- About to commit to a decision: run apply_decision_discipline first
- About to merge a complex spec: run apply_full_review
- Suspect a load-bearing assumption is unstated: run assumptions
Red flags:
- Hand-rolling decision rationales without the discipline → call thinking verbs
- Claiming a steelman without testing the inverse → call inversion + steelman
"""
from __future__ import annotations

from agency.capability import ArtefactSchemas, CapabilityBase, verb
from agency.ontology import OntologyExtension
from agency.toolresult import ToolResult, Codes


# ─────────────────────────── enums ───────────────────────────
ANALYSIS_DEPTH = {"shallow", "standard", "deep"}
SEVERITY = {"low", "medium", "high", "critical"}


# ─────────────────────────── walkable skill ───────────────────────────
CRITICAL_THINKING_SKILL = {
    "name": "critical-thinking-pass", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "decompose",
         "produces": ["sub_problems_listed"]},
        {"index": 2, "name": "surface-assumptions",
         "produces": ["load_bearing_marked"]},
        {"index": 3, "name": "premortem",
         "produces": ["failure_causes_listed"]},
        {"index": 4, "name": "steelman-and-inversion",
         "produces": ["counter_argument_tested"]},
        {"index": 5, "name": "synthesize",
         "produces": ["recommendation"], "gate": "hard"},
    ],
}


# ─────────────────────────── ontology ───────────────────────────
thinking_ontology = OntologyExtension(
    nodes={
        "ThinkingMethod":  ["method", "subject"],
        "ThinkingFinding": ["method", "subject", "severity"],
    },
    enums={
        ("ThinkingFinding", "severity"): SEVERITY,
    },
    edges={
        "ANALYZES",       # ThinkingMethod / ThinkingFinding → subject node
    },
    skills={"critical-thinking-pass": CRITICAL_THINKING_SKILL},
    schemas={
        "thinking-analysis":  ["subject", "methods", "recommendation"],
        "thinking-finding":   ["method", "subject", "severity"],
        "thinking-method":    ["method", "subject"],
    },
)


# ─────────────────────────── private helpers ───────────────────────────
def _subject_or_default(ctx, subject: str) -> str:
    """Default subject to the serving intent's deliverable (Spec 091 pattern)."""
    if subject:
        return subject
    node = ctx.recall(ctx.intent_id)
    if not node:
        return "the current goal"
    return (node.get("deliverable") or node.get("purpose")
            or "the current goal").strip()


class ThinkingCapability(CapabilityBase):
    name = "thinking"
    home = "capability"
    artefact_schemas = ArtefactSchemas.from_module(__file__)
    ontology = thinking_ontology

    # ════════════════════════════════════════════════════════════════════════
    # 8 founding methods (Spec 091 lineage; thin scaffold-returning transforms)
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="transform")
    def decompose(self, subject: str = "") -> ToolResult:
        """MECE sub-problem decomposition (transform).

        Inputs: subject (defaults to the serving intent's deliverable).
        Returns: ``{method, subject, steps, output_schema}``.
        chain_next: ``thinking.assumptions`` on the riskiest sub-problem.
        """
        s = _subject_or_default(self.ctx, subject)
        return ToolResult.success(data={
            "method": "decompose", "subject": s,
            "steps": [
                f"State '{s}' as a single sentence — the one thing that must be true.",
                "Split it into 3-6 sub-problems that are mutually exclusive + collectively exhaustive.",
                "For each sub-problem: necessary? sufficient on its own? what does it depend on?",
                "Mark the ONE sub-problem that, if wrong, sinks the whole goal.",
            ],
            "output_schema": "{sub_problems: list, coverage_score: 0.0-1.0, residual: list}",
        })

    @verb(role="transform")
    def assumptions(self, subject: str = "") -> ToolResult:
        """Surface + classify implicit assumptions (load-bearing vs not) (transform).

        Inputs: subject.
        Returns: ``{method, subject, steps, output_schema}``.
        chain_next: ``thinking.premortem`` on the load-bearing ones.
        """
        s = _subject_or_default(self.ctx, subject)
        return ToolResult.success(data={
            "method": "assumptions", "subject": s,
            "steps": [
                f"List 5-10 implicit assumptions {s!r} rests on (don't filter).",
                "Mark each as load-bearing (failure sinks the goal) OR not.",
                "For each load-bearing one: cheapest test to refute or confirm? Run it.",
                "For each refuted assumption: name what it implies for the goal.",
            ],
            "output_schema": "{assumptions: [{claim, load_bearing: bool, status: held|refuted, evidence}]}",
        })

    @verb(role="transform")
    def premortem(self, subject: str = "") -> ToolResult:
        """Prospective failure analysis (transform).

        Inputs: subject.
        Returns: ``{method, subject, steps, output_schema}``.
        chain_next: ``thinking.tradeoffs`` to weigh mitigations.
        """
        s = _subject_or_default(self.ctx, subject)
        return ToolResult.success(data={
            "method": "premortem", "subject": s,
            "steps": [
                f"Assume it's 6 months from now and '{s}' has failed catastrophically.",
                "List 5-7 plausible causes (technical, social, organizational).",
                "Rank causes by severity AND probability.",
                "For top 3 causes: design a mitigation; for top 1: implement now.",
            ],
            "output_schema": "{assume_failed_cause: str, causes: list, mitigations: list}",
        })

    @verb(role="transform")
    def first_principles(self, subject: str = "") -> ToolResult:
        """Strip the goal to fundamentals + reconstruct (transform).

        Inputs: subject.
        Returns: ``{method, subject, steps, output_schema}``.
        chain_next: ``thinking.decompose`` from the reconstructed core.
        """
        s = _subject_or_default(self.ctx, subject)
        return ToolResult.success(data={
            "method": "first_principles", "subject": s,
            "steps": [
                f"Strip '{s}' to physical/mathematical/social fundamentals.",
                "Discard every assumption that's a convention or analogy.",
                "Reconstruct the goal from fundamentals — does it survive?",
                "If yes: what does the reconstruction reveal that convention hid?",
            ],
            "output_schema": "{fundamentals: list, derived: list, irreducible_core: str}",
        })

    @verb(role="transform")
    def inversion(self, subject: str = "") -> ToolResult:
        """Look for what guarantees failure rather than what guarantees success.

        Inputs: subject.
        Returns: ``{method, subject, steps, output_schema}``.
        chain_next: ``thinking.red_team`` for adversarial review.
        """
        s = _subject_or_default(self.ctx, subject)
        return ToolResult.success(data={
            "method": "inversion", "subject": s,
            "steps": [
                f"Instead of asking how to succeed at '{s}': what GUARANTEES failure?",
                "List 5+ failure-guarantee patterns. Be specific.",
                "For each: is it currently true of your plan?",
                "Eliminate the worst one. Re-plan around its absence.",
            ],
            "output_schema": "{what_guarantees_failure: list}",
        })

    @verb(role="transform")
    def steelman(self, subject: str = "", position: str = "") -> ToolResult:
        """Build the strongest possible argument against a position (transform).

        Inputs: subject, position (the claim being defended).
        Returns: ``{method, subject, position, steps, output_schema}``.
        chain_next: respond on the strongest objection's merits OR change position.
        """
        s = _subject_or_default(self.ctx, subject)
        return ToolResult.success(data={
            "method": "steelman", "subject": s, "position": position,
            "steps": [
                f"State {position!r} as charitably as possible.",
                "Now build the STRONGEST argument someone could make against it.",
                "Make it specific, not vague. Use their best framing, not yours.",
                "Respond to that argument on its merits, OR adjust your position.",
            ],
            "output_schema": "{strongest_counter_argument: str, response: str}",
        })

    @verb(role="transform")
    def second_order(self, subject: str = "",
                      n_steps: int = 3) -> ToolResult:
        """Trace consequences N steps downstream (transform).

        Inputs: subject, n_steps (default 3).
        Returns: ``{method, subject, n_steps, steps, output_schema}``.
        chain_next: ``thinking.tradeoffs`` if multiple consequence chains compete.
        """
        s = _subject_or_default(self.ctx, subject)
        return ToolResult.success(data={
            "method": "second_order", "subject": s, "n_steps": n_steps,
            "steps": [
                f"For '{s}': what's the immediate (first-order) consequence?",
                f"What does THAT cause? (second-order)",
                f"And THAT? (continue for {n_steps} steps total)",
                "Mark any step that contradicts the original goal's spirit.",
            ],
            "output_schema": "{consequence_chain: [{step, claim, downstream}]}",
        })

    @verb(role="transform")
    def tradeoffs(self, subject: str = "",
                   options: str = "",
                   criteria: str = "") -> ToolResult:
        """Multi-criteria option scoring (transform).

        Inputs: subject, options (comma-separated), criteria (comma-separated).
        Returns: ``{method, subject, options, criteria, steps, output_schema}``.
        chain_next: a recommendation based on the highest-weighted criterion.
        """
        s = _subject_or_default(self.ctx, subject)
        opt_list = [o.strip() for o in options.split(",") if o.strip()]
        crit_list = [c.strip() for c in criteria.split(",") if c.strip()]
        return ToolResult.success(data={
            "method": "tradeoffs", "subject": s,
            "options": opt_list, "criteria": crit_list,
            "steps": [
                f"For '{s}': list the credible options (you supplied {len(opt_list)}).",
                "Pick 3-5 criteria that actually matter (you supplied {0}).".format(len(crit_list)),
                "Score each option against each criterion (1-5 scale).",
                "The winner usually obvious post-scoring; if not, weight the criteria.",
            ],
            "output_schema": "{matrix: dict, recommendation: str}",
        })

    # ════════════════════════════════════════════════════════════════════════
    # 2 NEW methods (Spec 110 net-additions): red_team + socratic
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="transform")
    def red_team(self, subject: str = "",
                  n_attacks: int = 5) -> ToolResult:
        """Adversarial review — adopt an attacker's stance + find failure paths (transform).

        Distinct from steelman: steelman finds the strongest argument AGAINST
        your position; red_team finds the strongest path to your SYSTEM's
        failure.

        Inputs: subject, n_attacks (default 5).
        Returns: ``{method, subject, n_attacks, steps, output_schema}``.
        chain_next: prioritize the highest-severity attack + design mitigation.
        """
        s = _subject_or_default(self.ctx, subject)
        return ToolResult.success(data={
            "method": "red_team", "subject": s, "n_attacks": n_attacks,
            "steps": [
                f"Adopt the stance of an attacker who wants '{s}' to fail.",
                f"Identify {n_attacks} distinct attack vectors — technical, social, supply-chain.",
                "For each: weakness exploited, exploit path, severity (low/medium/high/critical).",
                "Rank by severity × ease; address the top one BEFORE shipping.",
            ],
            "output_schema": "{attacks: [{name, weakness, exploit_path, severity}], top_recommendation: str}",
        })

    @verb(role="transform")
    def socratic(self, subject: str = "",
                  n_questions: int = 5) -> ToolResult:
        """Five-whys-deeper Socratic questioning (transform).

        Recursively asks "why" / "what does that assume" to surface the
        root assumption.

        Inputs: subject, n_questions (default 5; the "five whys" depth).
        Returns: ``{method, subject, n_questions, steps, output_schema}``.
        chain_next: ``thinking.assumptions`` on the surfaced root.
        """
        s = _subject_or_default(self.ctx, subject)
        return ToolResult.success(data={
            "method": "socratic", "subject": s, "n_questions": n_questions,
            "steps": [
                f"Start with: 'why {s!r}?'",
                "Take the answer, then ask 'why that?' OR 'what does that assume?'",
                f"Continue for {n_questions} levels of recursion.",
                "The final-level answer surfaces the root assumption — examine it directly.",
            ],
            "output_schema": "{question_chain: [{level, question, answer}], root_assumption: str}",
        })

    # ════════════════════════════════════════════════════════════════════════
    # 1 composite (Slice 1)
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="act")
    def apply_full_review(self, subject: str = "",
                           depth: str = "standard") -> ToolResult:
        """Run the 8 founding thinking methods in sequence, producing a thinking-analysis artefact (act).

        Inputs: subject (defaults to serving intent), depth (one of
                ANALYSIS_DEPTH; documents the rigor level).
        Returns: ``{result, artefact}`` thinking-analysis artefact.
        chain_next: ``thinking.tradeoffs`` if multiple recommendations
                    compete, OR commit + ``dogfood.record_decision``.
        """
        if depth not in ANALYSIS_DEPTH:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"depth={depth!r} not in {sorted(ANALYSIS_DEPTH)}")
        s = _subject_or_default(self.ctx, subject)
        # Run each method (each returns a ToolResult; we extract the .data
        # field). The composite records the SEQUENCE — the actual reasoning
        # is the agent's job after this verb returns the scaffolds.
        methods = ["decompose", "assumptions", "premortem",
                   "first_principles", "inversion", "steelman",
                   "second_order", "tradeoffs"]
        scaffolds = []
        for m in methods:
            res = getattr(self, m)(subject=s)
            if res.ok:
                scaffolds.append({"method": m, "scaffold": res.data})
        body = (f"# Critical analysis: {s}\n\n"
                f"Depth: {depth}\n"
                f"Methods applied: {', '.join(methods)}\n")
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "thinking-analysis",
                         "subject": s,
                         "methods": methods,
                         "depth": depth,
                         "scaffolds": scaffolds,
                         "recommendation": "(agent fills based on scaffolds)",
                         "body": body},
        })
