---
spec_id: "081"
slug: walkable-usage-skills
status: design
last_updated: 2026-06-06
owner: "@agency"
depends_on: ["080", "018"]   # docstring-derived Agent Skills + the atomic skill walker
research_first: true
domain: capability
wave: 5
---

# Spec 081 — Walkable usage-skills (teach how to drive each capability's MCP verbs)

## Why

Spec 080 made every capability a **descriptive** Agent Skill (L1/L2/L3 — what it is,
when to use it). The missing axis is **procedural**: a *walkable* skill that teaches
an agent how to actually drive the capability's MCP verbs to an outcome — the way
`develop`'s `tdd` discipline walks RED→GREEN→REFACTOR→verify. User directive
(2026-06-06): *"extend all capabilities with real skills that take the knowledge on
how to use the mcp surface — and has walkable skills."*

The machinery exists: `ontology.skills` holds phase-graph schemas, and
`develop.skill_walk(name, inputs, resume_from)` (Spec 018 Win 1) walks one to its
first hard gate, recording every phase as provenance. Today only `develop`, `music`,
`analyze` (`code-analysis`), `jules`, etc. own walkable skills; most capabilities
ship none. This spec gives **every** capability a `<cap>-usage` walkable skill so a
fresh agent can learn the capability by walking it.

## Research first

- Inventory which capabilities already declare `ontology.skills` and the shape of
  those phase-graphs (`develop.DEV_SKILLS`, `music.ALBUM_CONCEPT_SKILL`,
  `analyze` `code-analysis`). Record as a graph reflection.
- Decide DERIVED vs AUTHORED: can a baseline `<cap>-usage` walk be *derived* from
  the verb set + roles (transform→effect→act ordering), per the derivability
  heuristic — so a drop-in capability gets a usage-walk for free? Or must each be
  authored? Likely a **derived default** (a phase per role-cluster, terminating in a
  "confirm outcome" gate) that a capability MAY override with an authored skill.
- Confirm the walker renders a usage-walk into the emitted SKILL.md (a "How to walk
  this" L2 section) so the descriptive + procedural skills are one artefact.

## Design (provisional — refine after research)

1. **Derived usage-walk.** `WalkerSkills.from_verbs(cap)` builds a default
   `<cap>-usage` phase-graph: order verbs by role (transform → effect → act → gate),
   one phase each (`produces: [<verb>_result]`), ending in a hard `confirm` gate.
   `as_capability` attaches it when the class declares no `ontology.skills` —
   mirroring the Spec 080 docstring-derivation pattern (free by default, override
   by declaration).
2. **Emit.** `emit_skill` renders a "## Walk this capability" section listing the
   phases + the `develop.skill_walk` invocation that drives them.
3. **Discoverable.** The usage-walk registers on `ontology.skills`; `search` +
   `develop.checklist(<cap>-usage)` surface it.

## Done When

- [ ] Research report (above) recorded as a reflection.
- [ ] A derived `<cap>-usage` walkable skill exists for every verb-bearing capability
  (authored override respected); each walks via `develop.skill_walk` to a hard gate
  with recorded provenance.
- [ ] `emit_skill` renders the walk into the per-cap SKILL.md.
- [ ] Tests: a derived walk for a sample cap walks end-to-end (status contract +
  provenance); an authored `ontology.skills` overrides the derived default;
  emit includes the walk section. `pytest` green; `check-drift` clean.

## Spec-panel critique (multi-expert, pre-implementation)

- **Token economist:** a per-verb phase for a 22-verb cap (`jules`) is a huge walk —
  derive by role-CLUSTER, not per-verb, and cap phase count (≤ ~6) so the walk
  stays token-tiny. *Accepted: cluster by role, cap at 6 phases, overflow → a
  "drive remaining verbs" phase.*
- **Doctrine (rule 5, cluster coherence):** walkable skills are a Lifecycle concern
  owned via `ontology.skills` — keep the walker in `develop`/`skill.py`; do NOT add
  a new walking verb per capability. *Accepted: one shared walker; capabilities only
  DECLARE/derive schemas.*
- **Authoring ergonomics:** a derived default must lint clean and be genuinely
  useful, else it's noise. *Open: validate the derived walk via a `develop`
  verb (extend `validate_skill`) before emit.*
- **Skeptic:** is a derived "phase per role" actually teaching, or just listing
  verbs in order? *Risk acknowledged — the derived walk is a SCAFFOLD; high-value
  capabilities (jules, research, develop) should AUTHOR a real discipline. The
  derived default guarantees coverage; authored skills guarantee quality.*

**Verdict:** APPROVE with the cluster-not-per-verb + ≤6-phase cap + validate-before-
emit refinements folded into Design.
