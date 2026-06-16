# agency-scaffold: v1
"""persona — specialist engineering personas, first-class (Spec 297).

A native reimplementation of SuperClaude's specialist agents (architects,
engineers, analysts, mentors) as a built-in, dispatchable persona registry —
NOT ingested prompt files. Decidable: a task is matched to the right specialist
by domain, and a dispatch brief (role + focus + approach + task) is composed and
recorded as provenance. Pairs with `panel` (business experts) and `subagent`
(the dispatch machinery).

Use when: a task needs a specific engineering specialist's lens — architecture,
security, performance, quality, refactoring, requirements, or teaching.
Triggers:
- A task that maps to a named specialist (architect, security, performance, QA)
- An ambiguous task that should be routed to the right expert first
- Composing a focused subagent dispatch from a specialist role
Red flags:
- Generic dispatch for a security-critical task → summon the security-engineer
- Building before requirements are concrete → summon the requirements-analyst
"""
from __future__ import annotations

from ...capability import CapabilityBase, verb
from ...ontology import OntologyExtension


# name · domain keywords (decidable matching) · focus · approach (signature
# method). Extracted from SuperClaude agents/, authored as native data.
_PERSONAS = [
    {"name": "backend-architect", "domain": ["backend", "api", "database", "data", "service", "server", "integrity", "transaction"],
     "focus": "Reliable backend systems — data integrity, security, fault tolerance.",
     "approach": "Design for failure; enforce invariants at the boundary; idempotency + observability."},
    {"name": "frontend-architect", "domain": ["frontend", "ui", "ux", "component", "accessibility", "react", "interface", "render"],
     "focus": "Accessible, performant user interfaces.",
     "approach": "Accessibility-first; measure render/interaction cost; component contracts."},
    {"name": "devops-architect", "domain": ["devops", "deploy", "infra", "ci", "cd", "pipeline", "observability", "kubernetes"],
     "focus": "Automated, reliable infrastructure + deployment.",
     "approach": "Automate everything; reliability + observability as first-class; reproducible envs."},
    {"name": "system-architect", "domain": ["architecture", "system", "scalable", "design", "boundaries", "coupling", "maintainability"],
     "focus": "Scalable architecture + long-term maintainability.",
     "approach": "Decompose by change rate; minimize coupling; defer irreversible decisions."},
    {"name": "security-engineer", "domain": ["security", "vulnerability", "auth", "crypto", "compliance", "threat", "exploit", "secret"],
     "focus": "Vulnerabilities + compliance with security standards.",
     "approach": "Threat-model first; least privilege; verify, don't trust input."},
    {"name": "performance-engineer", "domain": ["performance", "latency", "throughput", "bottleneck", "optimize", "profile", "memory", "speed"],
     "focus": "Measurement-driven performance optimization.",
     "approach": "Measure before optimizing; attack the dominant bottleneck; verify the gain."},
    {"name": "quality-engineer", "domain": ["quality", "test", "coverage", "edge case", "regression", "qa", "validation"],
     "focus": "Comprehensive testing + systematic edge-case detection.",
     "approach": "Test behaviour not implementation; enumerate edge cases; guard invariants."},
    {"name": "python-expert", "domain": ["python", "pythonic", "typing", "async", "packaging", "solid"],
     "focus": "Production-ready, secure, high-performance Python (SOLID).",
     "approach": "Idiomatic + typed; SOLID; profile hot paths; secure defaults."},
    {"name": "refactoring-expert", "domain": ["refactor", "tech debt", "clean", "smell", "simplify", "duplication", "readability"],
     "focus": "Code quality + technical-debt reduction.",
     "approach": "Small safe steps under test; remove duplication; name for intent."},
    {"name": "requirements-analyst", "domain": ["requirements", "spec", "ambiguous", "scope", "acceptance", "stakeholder", "discovery"],
     "focus": "Ambiguous ideas → concrete specifications.",
     "approach": "Surface hidden requirements; define acceptance; resolve ambiguity before build."},
    {"name": "root-cause-analyst", "domain": ["debug", "root cause", "investigate", "failure", "incident", "trace", "diagnose"],
     "focus": "Systematic, evidence-based problem investigation.",
     "approach": "Gather evidence at boundaries; form + test hypotheses; trace to the true cause."},
    {"name": "technical-writer", "domain": ["documentation", "docs", "writing", "readme", "guide", "audience", "explain"],
     "focus": "Clear documentation tailored to a specific audience.",
     "approach": "Know the audience; structure for least effort; show, then tell."},
    {"name": "learning-guide", "domain": ["learn", "teach", "tutorial", "concept", "beginner", "understand", "progressive"],
     "focus": "Teaching programming concepts via progressive learning.",
     "approach": "Build from first principles; worked examples; scaffold then fade."},
    {"name": "socratic-mentor", "domain": ["socratic", "mentor", "question", "discover", "reasoning", "guide"],
     "focus": "Socratic, discovery-driven learning.",
     "approach": "Ask, don't tell; strategic questions; let the learner derive the answer."},
]

_BY_NAME = {p["name"]: p for p in _PERSONAS}


# Spec 301 — extend with the superpowers pattern: a walkable DISCIPLINE that
# wraps specialist dispatch in subagent-driven-development + verification
# (recommend → summon → dispatch → verify[hard gate]).
_SPECIALIST_DISPATCH_SKILL = {
    "name": "specialist-dispatch", "kind": "discipline",
    "phases": [
        {"index": 1, "name": "match", "produces": ["persona", "task"]},
        {"index": 2, "name": "brief", "produces": ["brief"]},
        {"index": 3, "name": "dispatch", "produces": ["child"]},
        {"index": 4, "name": "verify", "produces": ["verified"], "gate": "hard"},
    ],
}


class PersonaCapability(CapabilityBase):
    name = "persona"
    home = "lifecycle"   # a persona parameterizes a dispatched agent's role
    ontology = OntologyExtension(
        nodes={"PersonaBrief": ["persona", "task"]},
        enums={("PersonaBrief", "persona"): set(_BY_NAME)},
        skills={"specialist-dispatch": _SPECIALIST_DISPATCH_SKILL},
    )

    @verb(role="act")
    def list(self) -> dict:
        """The specialist-persona roster — name · focus · approach.

        Returns: ``{count, personas: [...]}``.
        chain_next: persona.recommend(task) or persona.summon(name, task).
        """
        return {"count": len(_PERSONAS),
                "personas": [{k: p[k] for k in ("name", "focus", "approach")}
                             for p in _PERSONAS]}

    def _score(self, task: str) -> list[tuple[int, dict]]:
        low = task.lower()
        scored = [(sum(1 for d in p["domain"] if d in low), p) for p in _PERSONAS]
        scored = [(n, p) for n, p in scored if n > 0]
        scored.sort(key=lambda x: -x[0])
        return scored

    @verb(role="act")
    def recommend(self, task: str, top: int = 3) -> dict:
        """Recommend the specialist persona(s) best matched to a ``task`` by
        decidable domain overlap (read-only).

        Returns: ``{task, top, matches: [{persona, score, focus}]}``.
        chain_next: persona.summon(top, task) to compose the dispatch brief.
        """
        scored = self._score(task)
        return {"task": task, "top": scored[0][1]["name"] if scored else "",
                "matches": [{"persona": p["name"], "score": n, "focus": p["focus"]}
                            for n, p in scored[:top]]}

    @verb(role="effect")
    def summon(self, persona: str = "auto", task: str = "") -> dict:
        """Summon a specialist — compose a dispatch brief + record provenance
        (Spec 297).

        ``persona="auto"`` picks the best match for ``task`` via ``recommend``.
        Composes a brief (role + focus + approach + task) ready for the Agent
        tool / ``subagent.develop``, and records a ``PersonaBrief`` node SERVING
        the intent.

        Inputs: persona (auto | one of the roster names), task (str).
        Returns: ``{persona, brief, persona_brief_id}`` or ``{error}``.
        chain_next: hand ``brief`` to subagent.develop / the Agent tool.
        """
        if persona == "auto":
            scored = self._score(task)
            resolved = scored[0][1]["name"] if scored else ""
            if not resolved:
                return {"error": "no persona matches the task; name one explicitly",
                        "task": task}
        else:
            resolved = persona
        spec = _BY_NAME.get(resolved)
        if spec is None:
            return {"error": f"unknown persona {persona!r}; one of {sorted(_BY_NAME)}",
                    "persona": persona}
        brief = (f"# Role — {resolved}\n\n"
                 f"**Focus:** {spec['focus']}\n"
                 f"**Approach:** {spec['approach']}\n\n"
                 f"---\n# Task\n\n{task}\n")
        brief_id = self.ctx.record_and_serve("PersonaBrief",
                                             {"persona": resolved, "task": task[:200]})
        return {"persona": resolved, "brief": brief, "persona_brief_id": brief_id}
