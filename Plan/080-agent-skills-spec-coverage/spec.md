---
spec_id: "080"
slug: agent-skills-spec-coverage
status: shipped
last_updated: 2026-06-06
owner: "@agency"
depends_on: ["031", "032", "024"]   # the emit pipeline + capability authoring
research_first: true
affects:
  - agency/capabilities/*               # skill_doc on all 15 capabilities
  - agency/capabilities/develop/        # skill-validation verb (owned by develop)
  - agency/engine.py                    # skill_doc REQUIRED at bootstrap
  - agency/capabilities/develop (scaffold) # new caps born with a skill_doc stub
domain: capability
wave: 5
---

# Spec 080 — Complete Agent Skills spec coverage (activate + own + require)

## Why

User directive (2026-06-06): *"I want Agency capabilities to completely capture
all parts of the Anthropic Skill spec"* + *"what about references in skills?"* +
*"the validate-skilldocs need to be part of the develop capability."*

**The machinery already exists** (Spec 031/032): `emit_skill` renders a spec-
faithful `SKILL.md` (name + description frontmatter + body), `emit_references`
emits `references/<verb>.md` (progressive disclosure — Level 3), and
`emit_bash_wrappers` emits `scripts/` wrappers. But it is **dormant**: `generate()`
skips every capability without a `skill_doc`, and **0 of 15 capabilities declare
one**. So agency ships ZERO per-capability skills today.

This spec ACTIVATES full coverage by migrating all 15 capabilities to declare a
`skill_doc`, makes the validation a first-class `develop` verb (dogfood, not a
script), and makes `skill_doc` REQUIRED so every capability — current and future —
is a complete Agent Skill.

## Research findings — the Anthropic Agent Skills spec (2026-06-06)

Source: `platform.claude.com/docs/en/agents-and-tools/agent-skills/overview`.

- **SKILL.md** (required) with YAML frontmatter. Required fields: **`name`**
  (≤64 chars; lowercase letters/numbers/hyphens; no XML tags; NOT "anthropic"/
  "claude") and **`description`** (non-empty; ≤1024 chars; no XML tags; states
  WHAT + WHEN). All other frontmatter (`allowed-tools`, `license`, `metadata`)
  is platform/Claude-Code extension, not core-required.
- **Three loading levels (progressive disclosure):** L1 metadata (name +
  description, always loaded, ~100 tok); L2 SKILL.md body (on trigger, <5k tok);
  L3 bundled resources — additional markdown (references), `scripts/` (executable,
  output-only), assets — loaded as needed via bash.
- **Agency mapping:** L1 = the SkillDoc description; L2 = the rendered SKILL.md
  (overview + triggers + verb table + example + red-flags); L3 = `references/
  <verb>.md` (Tier-A verbs) + `scripts/` bash wrappers. Coverage is COMPLETE once
  a capability declares a `skill_doc`.

## Done When

- [x] **Research report** — the spec's parts + agency's mapping (above).
- [ ] **`develop.validate_skill(name="")`** (transform) — validates a
  capability's `SkillDoc` via `lint_skill_doc` + a dry-run `emit_skill` (catches
  reference/frontmatter problems); `name=""` validates ALL caps that declare one.
  This is the `/tmp` validation made a first-class, dogfoodable verb (user
  directive). Returns per-cap `{ok, violations, emits}`.
- [ ] **`skill_doc` on all 15 capabilities** — authored + lint-clean (validated
  by the verb above): analyze, branch, delegate, develop, document, dogfood, gate,
  jules, plugin, reflect, research, shell, skill_generator, subagent, workspace.
- [ ] **`skill_doc` REQUIRED at bootstrap** — flip the opt-in
  `AGENCY_SKILL_DOC_REQUIRED` gate to always-on; every verb-bearing capability
  MUST declare one (fail-loud at engine start).
- [ ] **Scaffolder emits a `skill_doc` stub** — `develop.scaffold_capability`
  skeletons include a minimal valid `skill_doc` so new caps are born compliant.
- [ ] **Install regen** — `generate()` now emits `skills/<cap>/SKILL.md` +
  `references/<verb>.md` + `scripts/` for all 15 (the dormant pipeline lights up);
  committed so the self-host test passes. The name constraint (no "claude"/
  "anthropic") holds for all 15 capability names.
- [ ] Tests: the verb validates clean + flags a broken doc; bootstrap rejects a
  verb-bearing cap without skill_doc; install emits the per-cap skill triad.
- [ ] `pytest` green; `check-drift` clean.

## Followup — Implementation Status (2026-06-06)

**Verdict:** Shipped — and the sourcing was refactored mid-spec per user
direction from inline literals to **docstring-derivation** (the better design).

### Done

- **Docstring-derived SkillDocs (the OOP win).** A capability's MODULE docstring
  is the single source: `disclosure.parse_module_skill` reads `Use when:` /
  `Triggers:` / `Red flags:` sections; overview = the prose paragraph; the
  example is synthesized from the primary (sorted-first) verb. `SkillDoc.
  from_module` builds it; `CapabilityBase.as_capability` DERIVES `skill_doc` when
  the class sets none. **No separate file, no redundant literal** — a drop-in
  capability folder needs only a well-formed docstring. All 15 core caps + the
  `music` example migrated to docstring-only.
- **`develop.validate_skill(name="")`** — validates a cap's derived SkillDoc via
  `lint_skill_doc` + dry-run `emit_skill`; `""` validates all. The dogfooded gate.
- **`skill_doc` REQUIRED at bootstrap** (always-on; `_require_skill_doc=False`
  bypass for lint probes / fixtures). Scaffolder emits the docstring sections so
  new caps are born compliant.
- **Full Agent Skills spec coverage emitted** — per-cap `SKILL.md` (L1 name +
  description frontmatter, L2 body) + `references/<verb>.md` (L3 progressive
  disclosure) for all 15. Emitted skill `name` is spec-legal (hyphens, not
  underscores — `skill_generator` → `skill-generator`).
- **Tests** — `tests/test_skill_docs.py` (incl. derivation unit tests),
  updated `test_skill_doc_validation` (always-required semantics), `test_install_
  per_cap` (inverted to assert per-cap emission). Full suite: 858 passed, 3
  skipped; `check-drift` clean; install regen committed.

### Deferred

- More representative `canonical_example` than sorted-first (add an `Example:`
  docstring line where it matters) — OQ-2.
- `license`/`metadata` frontmatter — OQ-1, not core-required.

## Open Questions

1. **Frontmatter completeness.** v1 emits `name` + `description` + `allowed-tools`
   (the Claude Code surface). `license`/`metadata` are deferred (not core-required);
   add if a consumer needs them.
2. **References granularity.** Agency maps references to PER-VERB detail files
   (Tier A). The `develop.REFERENCES` topic docs (testing-skills, …) could also
   emit as references — deferred; the per-verb mapping satisfies the spec's L3.

## Evidence

- `agency/skill_emit.py` (emit_skill / emit_references / emit_bash_wrappers — the
  dormant full-spec pipeline) + `agency/render/capability-skill.md` (frontmatter).
- `agency/capabilities/plugin/_main.py` `lint_skill_doc` (the contract the verb runs).
- `agency/install.py` `generate()` (skips caps without skill_doc — the dormancy).
- `agency/engine.py` (the opt-in `AGENCY_SKILL_DOC_REQUIRED` bootstrap shim).
- Anthropic Agent Skills spec (researched above).
- User directive (2026-06-06).
