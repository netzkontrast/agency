# agency-scaffold: v1
"""doctrine — queryable engineering principles + behavioral rules (Spec 303).

Closes the SuperClaude/superpowers port audit: PRINCIPLES + RULES were the only
unported aspect of that doctrine. Agency already *expresses* them as prose
(CLAUDE.md), skill Red flags, persona approaches and `mode` behaviors; doctrine
makes them **machine-queryable + citable**. Decidable (like `mode`/`panel`, no
LLM): a roster of engineering principles, priority-ranked behavioral rules, a
conflict-resolution hierarchy (the highest-leverage part — safety > correctness
> maintainability > speed), and a `DoctrineCitation` recording that a principle
*drove* an action (auditable provenance, the same way `mode` records a posture).

Use when: a decision must be grounded in a stated principle/rule, or two
concerns conflict and the winner must be adjudicated by the hierarchy, not
guessed.
Triggers:
- Two rules/concerns conflict and you need the priority-ranked winner
- An action was taken *because of* a principle and should be cited (provenance)
- You need the behavioral rules for a situation, filtered by priority
Red flags:
- Guessing which concern wins a safety-vs-speed tradeoff → doctrine.resolve
- Asserting "best practice" with no cited principle → doctrine.cite
"""
from __future__ import annotations

from ...capability import ArtefactSchemas, CapabilityBase, verb
from ...ontology import OntologyExtension

# ── doctrine config (small, named, overridable — NOT a frozen snapshot of live
# state; CLAUDE.md rule 8 allows documented config like `mode`'s _MODES). The
# engineering principles + behavioral rules are extracted from SuperClaude's
# core/PRINCIPLES.md + core/RULES.md and agency's own CLAUDE.md doctrine. ──

_PRINCIPLES = [
    {"name": "SOLID",
     "statement": "Single-responsibility, open-closed, Liskov, interface-"
                  "segregation, dependency-inversion — structure code so change "
                  "stays local."},
    {"name": "evidence-based",
     "statement": "Assert only what you have run; claims are grounded in "
                  "verifiable output, never memory or assumption."},
    {"name": "task-first",
     "statement": "Understand → Plan → Execute → Validate before acting; the "
                  "task drives the work, not the tooling."},
    {"name": "context-awareness",
     "statement": "Read the surrounding code + conventions before adding; match "
                  "what is there rather than imposing a new idiom."},
    {"name": "derive-dont-duplicate",
     "statement": "Authored metadata that duplicates an existing source is drift "
                  "waiting to happen — derive it from the single source of truth."},
]
_PRINCIPLES_BY_NAME = {p["name"]: p for p in _PRINCIPLES}

# Priority system (SuperClaude 🔴 CRITICAL / 🟡 IMPORTANT / 🟢 RECOMMENDED).
_PRIORITIES = ("critical", "important", "recommended")

_RULES = [
    {"rule": "safety-first", "priority": "critical", "category": "safety",
     "statement": "Security + data-integrity rules always win a conflict.",
     "triggers": ["security", "data", "destructive", "secret", "credential",
                  "delete", "overwrite"]},
    {"rule": "verify-before-claim", "priority": "critical", "category": "correctness",
     "statement": "Run the command and confirm the output before claiming done.",
     "triggers": ["done", "passing", "fixed", "complete", "works"]},
    {"rule": "no-hardcoded-values", "priority": "important", "category": "maintainability",
     "statement": "Prefer computed/derived values over magic numbers + frozen "
                  "snapshots; assert invariants, not constants.",
     "triggers": ["magic number", "snapshot", "hardcoded", "frozen"]},
    {"rule": "test-behaviour", "priority": "important", "category": "correctness",
     "statement": "Test observable behaviour via acceptance scenarios, not "
                  "implementation internals.",
     "triggers": ["test", "coverage", "acceptance"]},
    {"rule": "address-drift", "priority": "important", "category": "maintainability",
     "statement": "Keep the open-set substrate in sync; run check-drift before "
                  "commit when the capability surface changes.",
     "triggers": ["drift", "capability", "surface", "regen"]},
    {"rule": "read-before-write", "priority": "recommended", "category": "correctness",
     "statement": "Read a file before editing it; understand before you change.",
     "triggers": ["edit", "write", "modify"]},
    {"rule": "ship-when-green", "priority": "recommended", "category": "speed",
     "statement": "Once verified green, ship — do not gold-plate past the "
                  "acceptance bar.",
     "triggers": ["ship", "fast", "quick", "velocity", "merge"]},
]
_RULES_BY_NAME = {r["rule"]: r for r in _RULES}

# The conflict-resolution hierarchy — the highest-leverage part (Meadows lens):
# higher index loses. Each category carries the keywords that classify free text
# (a rule name, a category name, or a raw concern like "ship fast") into it.
_HIERARCHY = ["safety", "correctness", "maintainability", "speed"]
_CATEGORY_KEYWORDS = {
    "safety": ["safety", "secure", "security", "data", "integrity",
               "delete", "erase", "wipe", "destructive",
               "secret", "credential", "privacy", "corruption"],
    "correctness": ["correctness", "correct", "verify", "test", "accuracy",
                    "bug", "soundness", "valid"],
    "maintainability": ["maintainability", "maintain", "clean", "refactor",
                        "readability", "simplicity", "clarity", "drift"],
    "speed": ["speed", "fast", "quick", "performance", "velocity", "ship",
              "throughput", "deadline"],
}


def _classify(term: str) -> str:
    """Map a rule name / category / free-text concern to a hierarchy category.

    A known rule name resolves to its declared category; otherwise the term is
    matched against each category's keywords in HIERARCHY order — so a concern
    naming keywords from two categories resolves to the higher-priority one
    (e.g. 'fast but correct' → correctness > speed). Unknown terms rank
    lowest (``""``)."""
    low = term.lower().strip()
    rule = _RULES_BY_NAME.get(low)
    if rule is not None:
        return rule["category"]
    if low in _HIERARCHY:
        return low
    for cat in _HIERARCHY:  # hierarchy order = tie-break toward higher priority
        for kw in _CATEGORY_KEYWORDS[cat]:
            if kw in low:
                return cat
    return ""


class DoctrineCapability(CapabilityBase):
    name = "doctrine"
    home = "capability"   # a reference surface consulted during work; no new pillar
    artefact_schemas = ArtefactSchemas.from_module(__file__)
    ontology = OntologyExtension(
        nodes={"DoctrineCitation": ["name"]},
    )

    @verb(role="act")
    def principles(self) -> dict:
        """The engineering-principles roster — name · statement (Spec 303).

        Inputs: (none).
        Returns: ``{count, principles: [{name, statement}]}``.
        chain_next: doctrine.cite(name) once a principle drives an action.
        """
        return {"count": len(_PRINCIPLES), "principles": list(_PRINCIPLES)}

    @verb(role="act")
    def rules(self, priority: str = "") -> dict:
        """The behavioral rules, optionally filtered by priority (Spec 303).

        Inputs: priority (str — '' for all, or critical|important|recommended).
        Returns: ``{count, priority, rules: [{rule, priority, category,
                   statement, triggers}]}``.
        chain_next: doctrine.resolve(a, b) when two rules conflict.
        """
        rows = _RULES
        if priority:
            rows = [r for r in _RULES if r["priority"] == priority]
        return {"count": len(rows), "priority": priority, "rules": list(rows)}

    @verb(role="act")
    def resolve(self, a: str, b: str) -> dict:
        """Adjudicate two conflicting concerns by the conflict hierarchy
        (safety > correctness > maintainability > speed) — read-only (Spec 303).

        Each side (a rule name, a category, or free-text like 'ship fast') is
        classified into a hierarchy category; the higher-ranked category wins.
        Equal categories are a tie (no winner — the caller decides).

        Inputs: a (str — one concern), b (str — the other).
        Returns: ``{winner, winner_category, loser, loser_category, tie,
                   rationale}``.
        chain_next: gate.adjudicate wraps this; doctrine.cite the winning rule.
        """
        ca, cb = _classify(a), _classify(b)
        ra = _HIERARCHY.index(ca) if ca in _HIERARCHY else len(_HIERARCHY)
        rb = _HIERARCHY.index(cb) if cb in _HIERARCHY else len(_HIERARCHY)
        if ra == rb:
            return {"winner": "", "winner_category": ca, "loser": "",
                    "loser_category": cb, "tie": True,
                    "rationale": f"{a!r} and {b!r} both map to "
                                 f"{ca or 'unknown'!r} — no hierarchy winner."}
        if ra < rb:
            winner, wcat, loser, lcat = a, ca, b, cb
        else:
            winner, wcat, loser, lcat = b, cb, a, ca
        return {"winner": winner, "winner_category": wcat, "loser": loser,
                "loser_category": lcat, "tie": False,
                "rationale": f"{wcat!r} outranks {lcat or 'unknown'!r} in the "
                             "conflict hierarchy (safety > correctness > "
                             "maintainability > speed)."}

    @verb(role="effect")
    def cite(self, name: str, rationale: str = "") -> dict:
        """Record that a principle or rule DROVE an action — a DoctrineCitation
        SERVING the intent (auditable provenance, Spec 303).

        Inputs: name (str — a known principle or rule name), rationale (str —
                why it applied; optional).
        Returns: ``{citation_id, name, kind}`` or ``{error}`` for an unknown name.
        chain_next: the cited principle is now queryable provenance on the intent.
        """
        if name in _PRINCIPLES_BY_NAME:
            kind = "principle"
        elif name in _RULES_BY_NAME:
            kind = "rule"
        else:
            return {"error": f"unknown principle/rule {name!r}; principles="
                             f"{sorted(_PRINCIPLES_BY_NAME)}, rules="
                             f"{sorted(_RULES_BY_NAME)}", "name": name}
        cid = self.ctx.record_and_serve(
            "DoctrineCitation",
            {"name": name, "kind": kind, "rationale": rationale})
        return {"citation_id": cid, "name": name, "kind": kind}
