---
spec_id: "377"
slug: skill-lint-enforcement
status: partial
state: draft
last_updated: 2026-06-22
owner: "@agency"
vision_goals: [1, 3]
depends_on: ["032", "054", "371", "373"]
parent_spec: "370"
domain: skills
---

# Spec 377 — Strict per-type lint + schema enforcement (graduated)

> Child 7 of Spec 370. Make the contract enforceable: per-type schema + the new
> quality rules gate generation, graduated warn→block so the existing 33 don't all
> break at once.

## Why
`lint_skill_doc` checks the description/triggers/example shape but passes thin
bodies, stub sections, and missing phase instructions. The schema (`skill-md.json`)
enforces nothing. So low-quality skills ship.

## Design (sketch)
- Extend `lint_skill_doc` with **per-type completeness** (each `type`'s required
  sections present), **self-containment** (every phase has non-empty `instructions`,
  A1), **no-stub** (no `_(Tier B…)_` text), **verb-resolves** (every referenced verb
  exists), and the R1/R3/R4 checks (description-when-not-what, ≤500 lines, refs
  one-deep).
- Validate the `Skill`/`Phase` schema (371) at `install.generate` AND in
  `check-drift` (Spec 054).
- **Graduated rollout** (Spec 032 `AGENCY_BOOTSTRAP_LINT={strict,warn,off}` precedent):
  warn repo-wide; **block** for new/changed skills + the pillars (375) + frugal as
  first exemplars; flip to repo-wide block when 378 finishes the 33.
- Rewrite `docs/vision/SKILL-CONTRACT.md` → v2 (the R1–A7 contract).

## Slices (TDD)
1. The per-type + self-containment + no-stub + verb-resolves lint rules.
2. Schema validation wired into `install.generate` + `check-drift`; the graduated
   warn/block gate.
3. `SKILL-CONTRACT.md` v2.

## Acceptance
- A thin/stub/non-self-contained skill FAILS lint (was passing).
- New/changed skills + pillars + frugal are blocked on failure; legacy caps warn.
- `check-drift` validates every committed `skill.yaml` against the schema.

## Followup — Implementation Status (2026-06-22)

**Slice 1 — SHIPPED: the strict per-type + self-containment + no-stub +
verb-resolves lint rules.** Slices 2 (wire into install.generate + check-drift,
graduated warn/block) and 3 (SKILL-CONTRACT.md v2) remain.

Done (file:line evidence):
- `agency/capabilities/plugin/clusters/lint.py` — `lint_skill_schema(skill,
  verbs_index=None)` validates a 371 Skill dict beyond the SkillDoc shape:
  ``schema`` (via `parse_skill` — structure AND per-type completeness, the R15
  required core; a schema failure short-circuits), ``description-trigger-first``
  (R1 — 'Use when…'), ``phase-self-contained`` (A1 — every phase carries non-empty
  `instructions`), ``no-stub`` (no `(Tier B…)` placeholder), ``verb-resolves`` (a
  phase's `invoke` binding names a LIVE verb — scoped to `invoke`, the executable
  contract; the loose advisory `verbs` list is NOT strictly resolved because it
  legitimately names skills/methods like `develop.brainstorm`, not just verbs —
  avoids false positives). Surfaced as `plugin.lint_skill_schema(skill)` (role=
  transform), which builds `verbs_index` from the live registry.
- Tests: `tests/acceptance/features/skill_lint.feature` + `test_skill_lint.py` — 5
  scenarios: 4 crafted fail cases (one per rule: thin-technique → schema;
  tier-b-stub → no-stub; no-instructions → phase-self-contained; bad-verb →
  verb-resolves) + the live PASS exemplar (every committed pillar passes strict
  lint, derived from `load_pillars()`, rule 8). 5/5 green; 31 across
  skill_lint/plugin_authoring; install regen (the new verb's wrapper + reference +
  help entry) clean.

**Slice 2 — SHIPPED: the committed-skill gate at install.generate + check-drift.**

Done (file:line evidence):
- `agency/_pillars.py` — `lint_pillars(verbs_index=None, directory=None)` strict-
  lints every committed pillar via `lint_skill_schema`, returning `[{name,
  violations}]` for any failure (empty ⇒ clean). The committed `skill.yaml` (the
  pillars) are the **block-set exemplars**.
- `agency/install.py::generate` — builds `verbs_index` from the live registry and
  RAISES `ValueError` if any pillar fails strict lint, BEFORE rendering — a broken
  pillar never reaches disk (mirrors `emit_skill`'s PRE-emit lint raise for
  capability SkillDocs).
- `scripts/check-drift` — new "committed skill schema lint (Spec 377)" section
  (2b) runs `lint_pillars()` → DRIFT on failure; skips gracefully when agency deps
  are unavailable in the shell (CI runs it with the venv active).
- Tests: 3 new `skill_lint` scenarios — the committed source passes the gate
  (live exemplar); a lint-failing pillar in a temp source is flagged
  (`directory=`); `install.generate` is REFUSED (raises) when a committed pillar
  fails (monkeypatched `load_pillars`). 8/8 skill_lint + 42 across
  lint/pillar/install/command green; check-drift's new section reports "committed
  skills: clean"; install regen diff-free (the gate is a guard, not new output).

**Graduated rollout note.** The block set is the committed `skill.yaml` (the
pillars) — they BLOCK. The 39 legacy disciplines are NOT committed `skill.yaml`
(they derive from capability ontologies via `emit_skill`), so the committed-skill
gate does not touch them — they are implicitly "warn" (untouched) until Spec 378
fills their phase `instructions` and migrates them to the strict contract, at
which point the gate widens. `frugal` becomes a block exemplar when it lands as a
committed skill.

**Slice 3 — SHIPPED: `docs/vision/SKILL-CONTRACT.md` v2.** Rewritten from the v1
five-obligation SkillDoc contract to the layered, per-type, self-contained v2:
the two skill surfaces (capability SkillDoc vs committed `skill.yaml`), the type
classification (R15) + per-type required core, self-containment (A1) + walk↔file
parity (A2), the content layers (R9/R13/R4/R5/R8), F3 verb-resolves, no-stub,
deterministic install (A7), and BOTH lint rule-sets (`lint_skill_doc` 9 rules +
`lint_skill_schema` 5 rules) + the graduated gate. DERIVED from shipped code
(every rule cites its code home — no fabricated rule numbers); carries a
`doc-source` marker + stamped `doc-hash` (check-doc-drift in sync).

**All three slices SHIPPED.** The strict contract is enforceable and enforced at
the committed-skill (pillar) block set; the legacy-discipline widening is Spec
378's job.
