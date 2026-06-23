<!-- doc-source: agency/_skill_parse.py agency/capabilities/plugin/clusters/lint.py agency/skill_emit.py Plan/done/370-skill-system-v2/spec.md -->
<!-- doc-hash: 954aeb315aac828d -->
# Agency skill contract v2 — the layered, per-type, self-contained skill

> Doctrine reference for the Spec 370 skill-system-v2 program (Specs 371–378).
> Every skill — a generated `skills/<capability>/SKILL.md`, a committed
> `skill.yaml` (the concept pillars, Spec 375), or a capability-authored skill
> (A6) — is a contract between the plugin and the calling agent. v1 (Spec 031)
> framed it as five obligations of a capability SkillDoc; v2 generalises to the
> **layered, typed schema (371)** that the strict lint (377) enforces.
>
> **Code is the final decision.** This doc is DERIVED from what shipped — the
> typed schema in [`agency/_skill_parse.py`](../../agency/_skill_parse.py) and the
> two lint surfaces in
> [`agency/capabilities/plugin/clusters/lint.py`](../../agency/capabilities/plugin/clusters/lint.py).
> Where a rule carries an `R…`/`A…` label it is the program's assembled
> best-practice of that name; the authority is the code cited beside it.

## The two skill surfaces

| Surface | Source | Validator |
|---|---|---|
| **Capability SkillDoc** | derived from a capability's module docstring (`Use when:` / `Triggers:` / `Red flags:`) | `lint_skill_doc` (9 rules, §"Capability SkillDoc rules") |
| **Committed `skill.yaml`** | a typed `Skill` dict on disk — the concept pillars (375), capability-authored skills (A6) | `parse_skill` (schema) + `lint_skill_schema` (strict, Spec 377) |

Both render through the per-type templates ([`agency/render/skill/`](../../agency/render/skill/)); a discipline's phases render the SAME content the walker delivers (one source — A2).

## 1. Classification — `type` (R15) and the per-type required core

Every typed skill declares a `type` ∈ `{pillar, capability, technique, pattern,
reference, discipline}` (`_SKILL_TYPES`). `type` is the best-practices
CLASSIFICATION (R15) — orthogonal to `kind` (the walk-shape). Each type carries a
small **required core** (`_TYPE_REQUIRED`), everything else optional (frugal —
A4 layered content):

| type | required core beyond `description` |
|---|---|
| `technique` | `phases` |
| `pattern` | `overview` |
| `reference` | `references` |
| `discipline` | `common_mistakes` |
| `pillar` | `overview` |
| `capability` | — (the description-only floor) |

`parse_skill` enforces the per-type core: a typed skill missing it FAILS
(`schema` violation). `owner` (A6) records WHO authored the skill — `auto`
(the generator) or `capability` (a cap shipping its own).

## 2. WHEN to call — trigger-first description (R1)

The `description` MUST start with `"Use when…"` and name the triggering symptoms,
NOT summarise the workflow. Enforced by `description-trigger-first` (+
`description-no-workflow-summary` / `overview-no-workflow-summary` on the SkillDoc
path; `description-trigger-first` on the schema path). A capability SkillDoc names
2–5 concrete triggers (`triggers-count`, `triggers-named-symptoms`).

## 3. Self-containment (A1) and walk↔file parity (A2)

A skill is self-contained: a read-only agent can follow it top-to-bottom WITHOUT
the skill-walker. Every phase carries non-empty `instructions` (the inline steps)
— enforced by `phase-self-contained` (Spec 377). The phase's `goal` /
`instructions` / `example` / `done_when` / `freedom` are ONE source: the walker
delivers them AND the rendered SKILL.md inlines them (A2 —
`skill_emit._render_phase_detail`), so the two surfaces never drift.

## 4. The content layers — example (R9), mistakes (R13), references (R4/R5)

- **R9** — exactly ONE concrete `examples` entry (`[{input, output}]`); the
  capability SkillDoc's `canonical_example` MUST reference a real verb
  (`example-uses-real-verb`).
- **R13** — `common_mistakes` (`[{symptom, counter}]`) is the rationalization
  table a discipline requires; the SkillDoc's `red_flags` are its analogue
  (`red-flags-required` when a cap ships ≥3 verbs, `red-flags-format` for the
  `<symptom> → <counter>` shape).
- **R4 / R5** — heavy per-verb detail lives ONE level deep in `references`
  (`[{path, title?}]`), linked with relative markdown links (never `@`-imports);
  the body stays ≤500 lines (R3), with a ToC when it exceeds ~100 (R5).

## 5. Degrees of freedom (R8)

When a phase names how much the agent may deviate, it uses `freedom` ∈
`{high, medium, low}` (`_FREEDOM`) — a rigid-vs-flexible signal the walker and
the reader both honour.

## 6. No hallucinated verbs (F3) — verb-resolves

A phase's `invoke` binding MUST name a LIVE `(capability, verb)` — enforced by
`verb-resolves` (Spec 377), scoped to the executable `invoke` binding. The
authoring-time skill-creator (374) additionally rejects a draft whose
`phases[*].verbs` reference a verb absent from the live registry. (The advisory
`verbs` list is NOT strictly resolved — it legitimately names skills/methods, not
only verbs.)

## 7. No stubs on disk — no-stub

The Tier-B render placeholder (`(Tier B…)`) must NEVER reach a committed skill —
enforced by `no-stub` (Spec 377). The renderer drops it (373 Slice 3 direction);
the lint blocks it if it ever slips in.

## 8. Deterministic install + staleness (A7)

Install NEVER samples an LLM. The skill-creator's LLM output is **authoring-time
and committed** (374); `install.generate` only RENDERS committed skills, so
`install regen` is byte-stable and CI/Jules/offline safe (A7). A committed skill
carries a `source_stamp = hash(grounding + prompt-version)`; a future staleness
gate flags a skill whose source drifted from its stamp.

## Capability SkillDoc rules (`lint_skill_doc`, block mode)

Enforced at install for every capability SkillDoc (a failure aborts the install —
no bad SKILL.md reaches disk):

- `description-trigger-first` · `description-no-workflow-summary` ·
  `overview-no-workflow-summary`
- `triggers-named-symptoms` · `triggers-count` (2–5)
- `example-uses-real-verb`
- `red-flags-required` · `red-flags-format`
- `verb-briefs-resolve`

## Committed-skill rules (`lint_skill_schema`, Spec 377)

Enforced for every committed `skill.yaml` (the strict contract, beyond the
SkillDoc shape):

- `schema` — `parse_skill` (structure + per-type completeness)
- `description-trigger-first` (R1)
- `phase-self-contained` (A1)
- `no-stub`
- `verb-resolves` (F3, on the `invoke` binding)

## The graduated gate (Spec 377 Slice 2)

Rollout is graduated so the legacy surface doesn't all break at once:

- **Block set — committed `skill.yaml` (the pillars, 375).** `install.generate`
  raises and `check-drift` flags (section 2b) if any committed skill fails strict
  lint. `lint_pillars` is the gate.
- **Block — the 39 disciplines (Spec 378 complete).** They derive from capability
  ontologies (via `emit_skill`), not committed `skill.yaml`. **Spec 378 finished the
  migration**: every discipline is now self-contained, so `lint_disciplines` runs
  `strict=True` (repo-wide block) — every discipline must pass, not merely warn.

## Provenance

v2 authored under Spec 377 Slice 3 (2026-06-22), superseding the v1 five-obligation
contract (Spec 031 §16). Cross-references:

- Spec 371 — the committed layered schema (`Skill`/`Phase`, types, per-type core).
- Spec 372 — phase = single source (the walk content IS the rendered content).
- Spec 373 — per-type templates + the deterministic renderer; walk↔file parity.
- Spec 374 — the authoring-time skill-creator (sampling committed, A7; F3 grounding).
- Spec 375 — the concept pillars (the first `type: pillar` committed skills).
- Spec 377 — this contract's strict lint + the graduated gate.
- Spec 378 — migrates the legacy capability skills onto the contract; widens the gate.
- superpowers:writing-skills — the upstream discipline this contract ports.
