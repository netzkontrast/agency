"""skills — the first-class registry over every capability's walkable skills (Spec 026).

Skills makes the skill surface itself a capability: one home to find, render, and lint the phase-graph skills each capability ships on its ontology, instead of reaching them only through the merged ontology dict or the walker.

Use when: discovering which walkable skills exist, reading one skill's phases at a chosen depth, or validating a skill's phase-graph shape — before walking, emitting, or authoring a skill.
Triggers:
- An unknown skill surface you need to enumerate before walking
- A skill whose phases you want to read without loading the whole ontology
- A skill schema of uncertain shape, before it is walked or emitted
Red flags:
- Guessing a skill's phases from memory → render it via capability_skills_render
- Walking a skill of unknown shape → lint it first via capability_skills_lint
"""
from __future__ import annotations

from ..capability import CapabilityBase, verb
from ..ontology import OntologyExtension

_VALID_GATES = {"hard", "soft"}

# Spec 026 / 081 — an AUTHORED discipline (not the derived role-cluster scaffold): a
# real skill-triage workflow that teaches how to drive this capability's verbs toward
# a decision. Authored skills override the derived `<cap>-usage` (Spec 081).
_TRIAGE_SKILL = {
    "name": "skills-triage",
    "kind": "discipline",
    # Spec 026 Part B — a Matcher: this discipline applies when the intent/last-state
    # mentions skill triage. `intent.suggests` projects intent → this skill.
    "applies_when": {"kind": "pattern",
                     "pattern": r"skill|walkable|discipline|which.*(walk|skill)",
                     "confidence": 0.8},
    "phases": [
        {"index": 1, "name": "enumerate", "produces": ["skill_inventory"], "verbs": ["find"]},
        {"index": 2, "name": "read", "produces": ["phase_graph"], "verbs": ["render"]},
        {"index": 3, "name": "validate", "produces": ["lint_report"], "verbs": ["lint"],
         "gate": "soft"},
        {"index": 4, "name": "decide", "produces": ["chosen_skill"], "gate": "hard"},
    ],
}


def _all_skills(registry) -> dict:
    """Map skill_name → metadata, scanning every capability's ontology.skills.

    Ownership is per-capability (each cap's deepcopied ontology holds only its own
    authored + derived skills), so the owning capability is recoverable here — which
    the merged engine ontology loses.
    """
    out: dict[str, dict] = {}
    for cap_name in registry.names():
        cap = registry.get(cap_name)
        skills = getattr(getattr(cap, "ontology", None), "skills", {}) or {}
        for sname, schema in skills.items():
            phases = [p.get("name", "?") for p in schema.get("phases", [])]
            out[sname] = {"name": sname, "kind": schema.get("kind", "skill"),
                          "capability": cap_name, "phases": phases,
                          "phase_count": len(phases), "_schema": schema}
    return out


def _find(registry, skill_name: str) -> dict | None:
    return _all_skills(registry).get(skill_name)


class SkillsCapability(CapabilityBase):
    name = "skills"
    home = "capability"
    ontology = OntologyExtension(skills={"skills-triage": _TRIAGE_SKILL})

    @verb(role="transform")
    def find(self, kind: str = "", capability: str = "") -> dict:
        """Enumerate the walkable skills across all capabilities, with light filters.

        Inputs: kind (filter by skill kind, e.g. 'usage'/'discipline'; '' = any);
                capability (filter by owning capability; '' = any).
        Returns: ``{candidates: [{name, kind, capability, phases, phase_count}], total}``.
        chain_next: ``skills.render`` one candidate, or ``develop.skill_walk`` to walk it.
        The intent→next-skill projection lives on ``intent.suggests`` (Spec 026 B).
        """
        rows = []
        for meta in _all_skills(self.ctx.registry).values():
            if kind and meta["kind"] != kind:
                continue
            if capability and meta["capability"] != capability:
                continue
            rows.append({k: meta[k] for k in
                         ("name", "kind", "capability", "phases", "phase_count")})
        rows.sort(key=lambda m: (m["capability"], m["name"]))
        return {"candidates": rows, "total": len(rows)}

    @verb(role="transform")
    def render(self, skill_name: str, depth: str = "brief", phase_index: int = -1) -> dict:
        """Render one skill to markdown at a chosen depth (progressive disclosure).

        Inputs: skill_name (the skill to render); depth ('brief' = header + phase
                chain; 'full' = every phase with produces + gate); phase_index (≥0 →
                render only that one phase, full detail).
        Returns: ``{markdown}`` — or ``{error}`` when the skill is unknown.
        chain_next: ``skills.lint`` to validate shape, or ``develop.skill_walk`` to drive it.
        """
        meta = _find(self.ctx.registry, skill_name)
        if meta is None:
            return {"error": f"unknown skill {skill_name!r}"}
        schema = meta["_schema"]
        phases = schema.get("phases", [])

        def _phase_md(p: dict) -> str:
            produces = ", ".join(p.get("produces", [])) or "—"
            gate = f" · gate: **{p['gate']}**" if p.get("gate") else ""
            verbs = (" · verbs: " + ", ".join(p["verbs"])) if p.get("verbs") else ""
            return f"{p.get('index', '?')}. **{p.get('name', '?')}** — produces: {produces}{gate}{verbs}"

        if phase_index >= 0:
            match = next((p for p in phases if p.get("index") == phase_index), None)
            if match is None:
                return {"error": f"skill {skill_name!r} has no phase index {phase_index}"}
            return {"markdown": _phase_md(match)}

        header = (f"# {meta['name']}\n- kind: {meta['kind']}\n"
                  f"- capability: {meta['capability']}\n"
                  f"- phases: {' → '.join(meta['phases']) or '—'}\n")
        if depth == "brief":
            return {"markdown": header}
        return {"markdown": header + "\n" + "\n".join(_phase_md(p) for p in phases) + "\n"}

    @verb(role="transform")
    def lint(self, skill_name: str) -> dict:
        """Validate a skill's phase-graph shape — the structural contract a walk relies on.

        Inputs: skill_name (the skill to validate).
        Returns: ``{ok, violations: [str]}`` — non-empty phases, every phase has a
                 unique integer index + a name, and any gate is 'hard'/'soft'.
        chain_next: fix the schema where it is authored, then re-lint.
        """
        meta = _find(self.ctx.registry, skill_name)
        if meta is None:
            return {"ok": False, "violations": [f"unknown skill {skill_name!r}"]}
        phases = meta["_schema"].get("phases", [])
        v: list[str] = []
        if not phases:
            v.append("skill has no phases")
        seen = set()
        for i, p in enumerate(phases):
            idx = p.get("index")
            if not isinstance(idx, int):
                v.append(f"phase #{i} has no integer index")
            elif idx in seen:
                v.append(f"duplicate phase index {idx}")
            else:
                seen.add(idx)
            if not p.get("name"):
                v.append(f"phase #{i} has no name")
            gate = p.get("gate")
            if gate is not None and gate not in _VALID_GATES:
                v.append(f"phase {p.get('name', i)!r} has invalid gate {gate!r} "
                         f"(want one of {sorted(_VALID_GATES)})")
        return {"ok": not v, "violations": v}

    @verb(role="effect")
    def index(self) -> dict:
        """Promote walkable skills into the graph as Skill + Phase nodes (Spec 026).

        Writes a `Skill` node per skill + a `Phase` node per phase (with `HAS_PHASE`
        edges), so skills are queryable like any other node via `analyze.graph`.
        Idempotent: deterministic node ids (`skill:<name>`, `phase:<name>:<index>`) make
        re-indexing an upsert, not a duplicate. (Auto-promotion at bootstrap is deferred
        — bootstrap is write-free today; this keeps promotion explicit.)

        Inputs: none.
        Returns: ``{skills, phases}`` — counts of nodes written/updated.
        chain_next: ``analyze.graph`` (node_type='Skill') to read the promoted nodes.
        """
        mem = self.ctx.memory
        skills = phases = 0
        for meta in _all_skills(self.ctx.registry).values():
            sid = f"skill:{meta['name']}"
            mem.record("Skill", {"name": meta["name"], "kind": meta["kind"]}, node_id=sid)
            skills += 1
            for p in meta["_schema"].get("phases", []):
                pid = f"phase:{meta['name']}:{p.get('index')}"
                mem.record("Phase", {"skill": meta["name"], "index": p.get("index", 0),
                                     "name": p.get("name", ""),
                                     "produces": p.get("produces", [])}, node_id=pid)
                mem.link(sid, pid, "HAS_PHASE")
                phases += 1
        return {"skills": skills, "phases": phases}
