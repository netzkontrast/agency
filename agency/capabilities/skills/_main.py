# agency-scaffold: v1
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

from dataclasses import asdict, dataclass
from typing import Literal

from ...capability import ArtefactSchemas, CapabilityBase, verb
from ...ontology import OntologyExtension

_VALID_GATES = {"hard", "soft"}


# ── Spec 162 Slice 1 — typed MatcherResult shape ─────────────────────────
# `intent.suggests` ships pattern + verb_code + llm_select matchers (Spec 026).
# Slice 1 of Spec 162 defines the typed return shape they all coerce to so
# downstream consumers (the wet LLM path in Slice 2; the Skills-API publisher;
# any future matcher kind) speak ONE protocol.
MatcherKind = Literal["llm", "pattern", "verb_code", "none"]


@dataclass(frozen=True)
class MatcherResult:
    """Typed return of a matcher run for ONE skill candidate.

    `rationale` ≤ 200 chars (Slice 1 invariant — Spec 162 §"typed shape").
    `confidence` in [0.0, 1.0]. `matcher` discriminates the source. When the
    LLM driver is absent, `matcher` MUST NOT be `"llm"` — Spec 162 invariant
    (Spec 050 graceful-degradation pattern)."""

    skill_id:   str
    confidence: float
    rationale:  str
    matcher:    MatcherKind

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence must be in [0.0, 1.0]; got {self.confidence}")
        if len(self.rationale) > 200:
            raise ValueError(
                f"rationale must be ≤ 200 chars; got {len(self.rationale)}")
        if self.matcher not in ("llm", "pattern", "verb_code", "none"):
            raise ValueError(
                f"matcher must be one of llm/pattern/verb_code/none; "
                f"got {self.matcher!r}")

    @classmethod
    def from_legacy(cls, legacy: dict) -> "MatcherResult":
        """Convert the existing `intent.suggests` output (`{skill, mode,
        confidence, cue, matched_by}`) to a typed MatcherResult. The
        legacy `mode` maps to `matcher`; `matched_by` becomes the rationale
        prefix (trimmed to 200 chars)."""
        sk    = legacy.get("skill") or ""
        mode  = legacy.get("mode") or "none"
        if mode == "llm_select":
            mode = "llm"
        if mode not in ("llm", "pattern", "verb_code"):
            mode = "none"
        conf  = float(legacy.get("confidence", 0.0))
        cue   = str(legacy.get("matched_by") or legacy.get("cue") or "")
        return cls(
            skill_id=sk, confidence=max(0.0, min(1.0, conf)),
            rationale=cue[:200], matcher=mode)

    def to_dict(self) -> dict:
        return asdict(self)

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
    """Map skill_name → metadata: every capability's ontology.skills PLUS the
    committed concept pillars (Spec 375 Slice 2).

    Ownership is per-capability (each cap's deepcopied ontology holds only its own
    authored + derived skills), so the owning capability is recoverable here — which
    the merged engine ontology loses. The concept pillars (intent · lifecycle ·
    memory) are not owned by a capability; they carry kind="pillar" +
    capability="(pillar)" so the walkable-discipline filters (`find(kind=…)`,
    `find(capability=…)`) never pick them up by accident, while a bare `find()` /
    `rank()` lists them alongside the disciplines. A walkable skill of the same
    name wins the listing slot (pillars are additive, never clobbering).
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
    from ..._pillars import load_pillars
    for schema in load_pillars():
        sname = schema.get("name", "")
        if not sname or sname in out:
            continue
        out[sname] = {"name": sname, "kind": schema.get("kind", "pillar"),
                      "capability": "(pillar)", "phases": [],
                      "phase_count": 0, "_schema": schema}
    return out


def _find(registry, skill_name: str) -> dict | None:
    return _all_skills(registry).get(skill_name)


class SkillsCapability(CapabilityBase):
    name = "skills"
    home = "capability"
    ontology = OntologyExtension(skills={"skills-triage": _TRIAGE_SKILL})
    artefact_schemas = ArtefactSchemas.from_module(__file__)

    @verb(role="transform")
    def find(self, kind: str = "", capability: str = "") -> dict:
        """Enumerate the skills across all capabilities — walkable disciplines AND
        the concept pillars (Spec 375) — with light filters.

        Inputs: kind (filter by skill kind, e.g. 'usage'/'discipline'/'pillar';
                '' = any); capability (filter by owning capability, '(pillar)' for
                the concept pillars; '' = any).
        Returns: ``{candidates: [{name, kind, capability, phases, phase_count}], total}``.
        chain_next: ``skills.render`` one candidate, or ``develop.skill_walk`` to walk
        it (a pillar has 0 phases — read its concept skill rather than walking).
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

    @verb(role="transform")
    def rank(self, query: str = "") -> dict:
        """Rank walkable skills against a free-text query (Spec 161 Slice 1).

        Slice 1 is a deterministic keyword scorer: tokenize the query,
        normalise to lowercase, count substring hits across each skill's
        `name`, `capability`, `kind`, and phase names. Ties broken by
        `(capability, name)` for stability. Slice 2 swaps in an LLM
        ranker via the Spec 147 AnthropicDriver behind the same shape.

        An empty query falls through to the `find`-style listing (no
        ranking applied; same alphabetic sort).

        Inputs: query (free text; empty = list all).
        Returns: ``{candidates: [{name, kind, capability, phases,
                  phase_count, score}], total, scorer}``.
        chain_next: ``skills.render`` the top candidate, then
                    ``develop.skill_walk`` it.
        """
        skills = list(_all_skills(self.ctx.registry).values())
        if not query.strip():
            skills.sort(key=lambda m: (m["capability"], m["name"]))
            return {
                "candidates": [
                    {k: m[k] for k in ("name", "kind", "capability",
                                        "phases", "phase_count")}
                    | {"score": 0.0}
                    for m in skills
                ],
                "total":  len(skills),
                "scorer": "keyword",
            }
        tokens = [t for t in query.lower().split() if t]
        scored: list[tuple[float, dict]] = []
        for m in skills:
            phase_names = " ".join(
                p.get("name", "") if isinstance(p, dict) else str(p)
                for p in m.get("phases", []))
            hay = " ".join([
                str(m["name"]), str(m["capability"]),
                str(m["kind"]), phase_names,
            ]).lower()
            score = 0.0
            for tok in tokens:
                if not tok:
                    continue
                # Bigger boost for exact word match on the skill name; a
                # plain substring elsewhere still scores.
                if tok == m["name"].lower():
                    score += 2.0
                elif tok in m["name"].lower():
                    score += 1.0
                if tok in hay:
                    score += 0.5
            scored.append((score, m))
        scored.sort(key=lambda t: (-t[0], t[1]["capability"], t[1]["name"]))
        return {
            "candidates": [
                {k: m[k] for k in ("name", "kind", "capability",
                                    "phases", "phase_count")}
                | {"score": round(s, 3)}
                for s, m in scored
            ],
            "total":  len(scored),
            "scorer": "keyword",
        }

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
