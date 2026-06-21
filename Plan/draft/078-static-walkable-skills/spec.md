---
spec_id: "078"
slug: static-walkable-skills
status: draft
state: draft
last_updated: 2026-06-06
owner: "@agency"
depends_on: ["031", "060"]   # SKILL.md emit + the template/render machinery
research_first: true
affects:
  - agency/skill.py                     # a static/reference skill kind in the walker
  - agency/capabilities/                # candidate: welcome-as-skill
estimated_jules_sessions: 0
domain: substrate
wave: 5
---

# Spec 078 — Static / semi-templated walkable skills

## Why

User directive (2026-06-06): *"we might need to reshape capabilities if the gates
are not passed — like the current welcome … this could also be a static skill.
Maybe we need to be able to add semi-templated skills that contain static
knowledge and are still skill-walkable."* Two ideas:
1. **Some "capabilities" are static content delivery, not gated workflows** —
   `agency_welcome` is onboarding content, no gate. It could be a SKILL (the
   Lifecycle-template surface) rather than a substrate tool.
2. **A skill kind that carries STATIC KNOWLEDGE** (reference blocks rendered from
   templates — Spec 060) AND is still walkable phase-by-phase (progressive
   disclosure). Today a skill is a phase-graph; a "reference" skill would
   interleave static knowledge sections with optional gated phases.

> **Needs clarification (flagged):** "reshape capabilities if the gates are not
> passed" and "via pandoc" are ambiguous — the research phase pins the intended
> mechanism with the user before designing.

## Research first

- The current skill model (`agency/skill.py` `SkillRun`; Spec 031 `emit_skill`;
  Spec 060 templates) — how a phase renders, where a gate lives, how static text
  is carried today.
- What "semi-templated + static knowledge + still walkable" means concretely:
  a skill `kind: "reference"` whose phases are knowledge blocks (no gate) + the
  option of gated action phases? Render via the Spec 060 template machinery (NOT
  a new pandoc dependency unless the user confirms that path).
- Whether `welcome` should become such a skill (cost/benefit: discoverability,
  token budget, the using-agency first-call contract).
- Record findings as a graph reflection.

## Done When

- [ ] **Research + design report** resolving the ambiguities with the user.
- [ ] **A `reference`/`static` skill kind** in the walker: static knowledge
  sections (rendered from templates, disclosed progressively) interleaved with
  optional gated phases. No gate ⇒ pure knowledge delivery; gates ⇒ walkable.
- [ ] **Pilot:** express one static surface (e.g. an onboarding/reference doc) as
  a static skill that the walker renders.
- [ ] Tests + `check-drift` clean.

## Migration

Additive: a new skill kind alongside the existing discipline/authoring kinds.
`welcome` (if reshaped) keeps the substrate tool as a back-compat alias for one
minor.

## Open Questions

1. **"Reshape capabilities if gates not passed"** — does this mean a failed gate
   should re-render the capability as guidance (a recovery affordance), or that
   gateless capabilities should be skills? Research pins it.
2. **"via pandoc"** — is markdown→format conversion actually wanted, or just
   template rendering (Spec 060)? Confirm before adding a dependency.

## Evidence

- `agency/skill.py` + Spec 031 (`emit_skill`) + Spec 060 (templates/render).
- `agency_welcome` (the candidate static surface).
- CORE.md §Skills (skills are atomic, gated, progressively-disclosed step-graphs —
  this extends the model to gateless/reference skills).
- User directive (2026-06-06).

## Followup — Implementation Status (2026-06-12)

**Verdict:** Drafted (backlog / WARN-accepted / cluster-master). Tracked
in TODO.md's Verdicts row; no Slice 1 commitment beyond the spec body.
For the autonomous-completion goal stop condition (2), this spec is
classified as drafted-by-doctrine, not pending-implementation.

