---
capability: develop
pillar: lifecycle
vision_goals: [2, 3, 4, 6, 9]
status: living
last_generated: 2026-06-19
sources: [16, 18, 24, 41, 80]
---

# develop — Develop owns the development disciplines as walkable skills, a capability scaffolder that lints clean, and an atomic skill walker that records every phase as provenance (lifecycle pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
Develop owns development disciplines as walkable skills, scaffolds new capabilities with linting, walks skills recording each phase as provenance, and reloads edited capability code mid-session so the development loop stays tight and decisions are auditable.

## Verbs (generated · 14)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `develop.checklist` | transform | **discipline** | Project a discipline (skill walk) into a step-by-step checklist. |
| `develop.draft_plan` | act | **title** · steps | Author a bite-sized plan as graph provenance (Spec 287; rule 2). |
| `develop.estimate` | transform | loc · files · tests | Decidable effort estimate from change-size inputs (Spec 046 F-D — sc-estimate, |
| `develop.mode_select` | effect | **session_lifecycle_id** · **new_mode** · reason | Switch session mode + record a ModeShift node (effect). |
| `develop.plan_status` | transform | **plan_id** | Roll up a Plan's steps + completion (Spec 287) — the render-on-demand |
| `develop.record_authoring_outcome` | act | **name** · kind | Record a Reflection at the end of an authoring-capabilities walk. |
| `develop.record_step_outcome` | act | **step_id** · **outcome** · evidence | Mark a PlanStep's execution outcome (Spec 287). |
| `develop.reference` | transform | **topic** | Fetch a discipline's heavy how-to on demand (T3 disclosure). |
| `develop.scaffold_capability` | act | **name** · kind · base_dir | Emit a CAPABILITY-AUTHORING.md-compliant capability skeleton. |
| `develop.session_check` | transform | session_lifecycle_id | Read the current SessionLifecycle state (transform). |
| `develop.session_init` | act | purpose · deliverable · acceptance · mode_hint | Mint a SessionLifecycle SERVING the intent; detect mode; suggest first verb. |
| `develop.session_resume` | transform | for_intent_id | Spec 114 Slice 2 — cross-session handoff. |
| `develop.skill_walk` | act | **name** · **inputs** · resume_from | Walk a registered skill to the first hard gate in ONE call (the atomic walker). |
| `develop.validate_skill` | transform | name | Validate a capability's Agent-Skill (its SkillDoc) — lint + dry-run emit. |

## Ontology (generated)

**Nodes:** `SessionLifecycle`(mode, status) · `ModeShift`(from_mode, to_mode) · `Plan`(title) · `PlanStep`(plan, index, description)
**Edges:** `HAS_STEP`
**Enums:** `('SessionLifecycle', 'mode')` ∈ {brainstorming, coding, review, spec-authoring, synthesize} · `('SessionLifecycle', 'status')` ∈ {active, archived, paused} · `('ModeShift', 'from_mode')` ∈ {brainstorming, coding, review, spec-authoring, synthesize} · `('ModeShift', 'to_mode')` ∈ {brainstorming, coding, review, spec-authoring, synthesize} · `('PlanStep', 'state')` ∈ {blocked, done, pending, skipped}

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/develop -->
