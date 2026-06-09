---
spec_id: "111"
slug: capability-migration-to-prompt-thinking-dossier
status: draft
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["109", "110", "112"]
affects:
  - agency/capabilities/intent/        # delegate critical-thinking to thinking
  - agency/capabilities/analyze/       # use thinking.tradeoffs + prompt.engineer
  - agency/capabilities/develop/       # use thinking.apply_design_review + prompt.brief_render
  - agency/capabilities/document/      # use prompt.engineer for render explanations
  - agency/capabilities/research/      # consumed by dossier; minor wiring
  - agency/capabilities/delegate/      # use thinking.tradeoffs for dispatch decisions
  - agency/capabilities/jules/         # use prompt for review-comment composition
  - agency/capabilities/gate/          # use thinking for predicate clarity
  - agency/capabilities/reflect/       # use prompt for reflection synthesis
  - agency/capabilities/subagent/      # use prompt for sub-agent prompt composition
  - agency/capabilities/skill_generator/  # use prompt for skill text generation
  - agency/capabilities/skills/        # use prompt for skill rendering
  - agency/capabilities/dogfood/       # use thinking for observation analysis
  - agency/capabilities/plugin/        # use prompt for skill body authoring
  - examples/music.py                  # (when music ships its own capability folder)
  - agency/capabilities/novel/         # 105 iter-10 → dossier; 104 iter-11 → prompt
  - tests/test_capability_migration_*.py
domain: substrate / migration
wave: 8
research_first: false
---

# Spec 111 — Capability Migration to `prompt` + `thinking` + `dossier`

## Why

User directive (2026-06-07): *"Also think about how to Improve and
migrate all current capabilities to use those new capabilities."*

Specs 109 (`prompt`), 110 (`thinking`), 112 (`dossier`) ship three new
substrate-adjacent capabilities. This spec is the **systematic migration
plan** for every existing agency capability to adopt them, so the new
substrate becomes the canonical surface, not a parallel layer.

The migration is **additive + backward-compatible**: existing verb
signatures preserved; bodies refactored to delegate to the new caps;
no API break for callers.

## Discoverable migration surface

For each of agency's 17 existing capabilities, this spec declares:
1. **Adoption surface** — which verbs delegate to prompt/thinking/dossier
2. **Migration shape** — wrapper / refactor / delete-and-replace
3. **Backward compat note** — any caller-visible change
4. **PR sequencing** — independent / sequenced / batched

## The 17 existing capabilities

```
analyze · branch · delegate · develop · document · dogfood · gate ·
intent · jules · plugin · reflect · research · shell · skill_generator ·
skills · subagent · workspace
```

Plus 2 in-flight domain caps:
- music (Spec 093 wave) — shipped; iter-extensions inform pattern
- novel (Spec 101 wave) — drafted; primary consumer of new caps

## Per-capability migration matrix

### 1. `intent` (Spec 091)

**Adoption surface**: 8 critical-thinking methods become thin wrappers
delegating to `thinking.*`.

| 091 verb | becomes |
|---|---|
| `intent.decompose` | `wraps thinking.decompose(intent_id=...)` |
| `intent.assumptions` | `wraps thinking.assumptions` |
| `intent.premortem` | `wraps thinking.premortem` |
| `intent.first_principles` | `wraps thinking.first_principles` |
| `intent.inversion` | `wraps thinking.inversion` |
| `intent.steelman` | `wraps thinking.steelman` |
| `intent.second_order` | `wraps thinking.second_order` |
| `intent.tradeoffs` | `wraps thinking.tradeoffs` |

**Shape**: thin wrappers (1-line bodies). The `intent.suggests`
projection logic (Spec 091 Followup) and the `critical-thinking`
walkable skill move ENTIRELY to `thinking` capability — `intent` keeps
only the intent-bootstrap surface.

**Backward compat**: ✅ caller-visible API unchanged.

**PR sequencing**: ships AFTER 110 (thinking) lands.

### 2. `analyze` (Spec 042)

**Adoption surface**:
- The 4-axis prioritization (quality/security/performance/architecture)
  calls `thinking.tradeoffs` to choose which axis to run first when
  intent doesn't specify
- The `analyze.improve` verb (output of recommendations) calls
  `prompt.engineer` with builder=`improvement-recommendation`,
  context_refs=findings, voice_refs=(none)

**Shape**: refactor improve verb; add tradeoffs delegation to axis
selection.

**Backward compat**: ✅ caller-visible API unchanged; output shape
preserved.

**PR sequencing**: ships AFTER 109 + 110.

### 3. `develop` (Spec 060/018)

**Adoption surface**:
- `develop.checklist` (returns walkable-skill steps) — no change
- `develop.skill_walk` — no change
- The brainstorm discipline calls `thinking.apply_full_review` at the
  explore phase
- `develop.estimate` calls `thinking.tradeoffs` for confidence
  calibration

**Shape**: brainstorm + estimate verbs delegate.

**Backward compat**: ✅ caller-visible API unchanged.

**PR sequencing**: ships AFTER 109 + 110.

### 4. `document` (Spec 043)

**Adoption surface**:
- `document.explain` calls `prompt.engineer` with builder=`explanation`,
  context_refs=(target code/spec), constraints=depth
- `document.render` (4 scopes) — no change

**Shape**: refactor explain verb body.

**Backward compat**: ✅ caller-visible API unchanged.

**PR sequencing**: ships AFTER 109.

### 5. `research` (Spec 044)

**Adoption surface**: minor — research is the DOWNSTREAM cap that
dossier delegates TO. The 044 verbs (`lead` / `specialist` / `verify`)
are unchanged. Brief calls them.

**Shape**: no direct refactor; research stays as-is. Brief consumes
research output.

**Backward compat**: ✅ no change.

**PR sequencing**: independent.

### 6. `delegate` (Spec 040)

**Adoption surface**:
- `delegate.dispatch_decision` calls `thinking.tradeoffs` to score
  inline-vs-subagent-vs-jules
- `delegate.fan_out` calls `prompt.engineer` with
  builder=`dispatch-prompt` for each fan-out target

**Shape**: refactor dispatch_decision (already takes the 11 signals;
adds thinking.tradeoffs for clearer rationalization).

**Backward compat**: ✅ output shape preserved; reasoning trail richer.

**PR sequencing**: ships AFTER 109 + 110.

### 7. `jules` (Spec 030)

**Adoption surface**:
- `jules.dispatch` calls `prompt.engineer` with builder=`jules-prompt`,
  context_refs=(spec body), constraints=(JULES_PROTOCOL.md tail)
- `jules.review_comment` calls `prompt.engineer` with
  builder=`review-comment`
- `jules.lint_prompt` calls `prompt.audit` for reader-test simulation

**Shape**: dispatch + review_comment + lint_prompt all delegate.

**Backward compat**: ✅ caller-visible API unchanged.

**PR sequencing**: ships AFTER 109.

### 8. `gate` (Spec 057)

**Adoption surface**: minor — `gate.check` is core; no delegation
needed.
- Predicate-clarity audit (verifying gate names + evidence strings
  are clear) calls `prompt.audit` — but this is a v2 enhancement.

**Shape**: no v1 refactor.

**Backward compat**: ✅ no change.

**PR sequencing**: independent / deferred.

### 9. `reflect` (Spec 045)

**Adoption surface**:
- `reflect.note` — no change (just records observation)
- `reflect.recall` + `reflect.recall_semantic` — no change
- A new `reflect.synthesize(scope, depth)` verb (iter-1 of 111) calls
  `prompt.engineer` with builder=`reflection-synthesis`,
  context_refs=(recalled reflections), constraints=(depth)
  → produces a single synthesized Reflection from N raw Reflections

**Shape**: ADD `synthesize` verb (NET-NEW). Existing verbs unchanged.

**Backward compat**: ✅ purely additive.

**PR sequencing**: ships AFTER 109.

### 10. `subagent` (Spec 011)

**Adoption surface**:
- `subagent.dispatch` calls `prompt.engineer` with
  builder=`subagent-prompt`, context_refs=(parent intent),
  constraints=(quality + spec gates)

**Shape**: refactor dispatch body.

**Backward compat**: ✅ caller-visible API unchanged.

**PR sequencing**: ships AFTER 109.

### 11. `skill_generator` (Spec 080)

**Adoption surface**:
- `skill_generator.generate` calls `prompt.engineer` with
  builder=`skill-doc`, context_refs=(capability ontology),
  constraints=(SkillDoc shape)

**Shape**: refactor generate body.

**Backward compat**: ✅ caller-visible API unchanged.

**PR sequencing**: ships AFTER 109.

### 12. `skills` (Spec 026)

**Adoption surface**:
- `skills.suggests` (already moved here from intent per 091 followup)
  — no change; this is the Matcher projection
- A `skills.render` ENHANCEMENT (calls `prompt.engineer` with
  builder=`skill-text`, context_refs=(skill phase-graph)) — v2

**Shape**: no v1 refactor.

**Backward compat**: ✅ no change.

**PR sequencing**: independent / deferred.

### 13. `dogfood` (Spec 017)

**Adoption surface**:
- `dogfood.observe` — no change
- A new `dogfood.analyze_observations(scope, depth)` verb calls
  `thinking.apply_full_review` on the observation set; produces a
  CriticalAnalysisArtefact

**Shape**: ADD `analyze_observations` verb (NET-NEW).

**Backward compat**: ✅ purely additive.

**PR sequencing**: ships AFTER 110.

### 14. `plugin` (Spec 016 — current shipped version)

**Adoption surface**:
- `plugin.publish_skill` (Spec 083) — no change
- `plugin.lint_capability` — no change
- A new `plugin.author_skill_body(name, capability_ref)` calls
  `prompt.engineer` with builder=`skill-body` — v2 enhancement

**Shape**: no v1 refactor.

**Backward compat**: ✅ no change.

**PR sequencing**: deferred to v2.

### 15. `shell` (Spec 073)

**Adoption surface**: minor.
- A new `shell.author_template(name, description)` calls
  `prompt.engineer` with builder=`shell-template-doc` — v2

**Shape**: no v1 refactor.

**Backward compat**: ✅ no change.

**PR sequencing**: deferred to v2.

### 16. `branch` (Spec 064)

**Adoption surface**: minor.
- `branch.commit_smart` calls `prompt.engineer` with
  builder=`commit-message`, context_refs=(git diff +
  intent.deliverable)

**Shape**: refactor commit_smart body.

**Backward compat**: ✅ caller-visible API unchanged (commit message
just gets better).

**PR sequencing**: ships AFTER 109.

### 17. `workspace` (Spec 011a)

**Adoption surface**: none (workspace is filesystem isolation; no
prompt/thinking surface).

**Shape**: no change.

**Backward compat**: ✅ no change.

**PR sequencing**: independent / no work.

### 18. `music` (Spec 093 wave — already shipped)

**Adoption surface**: music's iter-5 LLM-driven verbs (promo_copy etc.)
delegate to `prompt.engineer` instead of calling `llm` driver directly.
Music ports the iter-11 novel pattern.

**Shape**: refactor music's LLM-using verbs (promo_copy, scribe etc.)
to delegate to prompt.

**Backward compat**: ✅ caller-visible API unchanged.

**PR sequencing**: ships AFTER 109 + the music spec set ships.

### 19. `novel` (Spec 101 wave — drafted)

**Adoption surface**: BIGGEST refactor of any capability.

| 101-wave verb | becomes |
|---|---|
| 104 `chapter_draft_assisted` | delegates to `prompt.engineer` (iter-11 wrapped) |
| 104 iter-11 10 prompt builders | move to `prompt.build` (registered as domain-specific builders via `prompt.register_builder`) |
| 104 iter-11 engineering verbs | delegate to `prompt.*` |
| 105 iter-10 research-entity stack | delegates to `dossier.*` (per Spec 112 §"Migration from 105") |
| 105 iter-12 research-prompt-optimizer verbs | delegate to `dossier.*` + `prompt.*` |
| 101 CRITICAL-ANALYSIS.md | uses `thinking.apply_design_review` |

**Shape**: spec changes in 104, 105, 101 land BEFORE implementation
PRs begin; implementation directly uses delegated pattern.

**Backward compat**: ✅ caller-visible API unchanged.

**PR sequencing**: ships AS PART OF the novel implementation wave
(not before novel ships).

## Migration summary table

| Capability | Adoption depth | Net new verbs | PR sequencing |
|---|---|---|---|
| intent | 8 thin wrappers | 0 | After 110 |
| analyze | 2 verb refactors | 0 | After 109+110 |
| develop | 2 verb refactors | 0 | After 109+110 |
| document | 1 verb refactor | 0 | After 109 |
| research | none (downstream) | 0 | Independent |
| delegate | 2 verb refactors | 0 | After 109+110 |
| jules | 3 verb refactors | 0 | After 109 |
| gate | none (v1) | 0 | Deferred v2 |
| reflect | net-new synthesize | +1 | After 109 |
| subagent | 1 verb refactor | 0 | After 109 |
| skill_generator | 1 verb refactor | 0 | After 109 |
| skills | none (v1) | 0 | Deferred v2 |
| dogfood | net-new analyze_observations | +1 | After 110 |
| plugin | none (v1) | 0 | Deferred v2 |
| shell | none (v1) | 0 | Deferred v2 |
| branch | 1 verb refactor | 0 | After 109 |
| workspace | none | 0 | No work |
| music | LLM verbs delegated | 0 | After 109 + music ships |
| novel | biggest refactor | 0 (deletes its own iter-10/11) | With novel impl |

**Totals**:
- 6 capabilities ship "ready-to-adopt" after 109+110+112 (intent /
  analyze / develop / document / jules / branch / subagent / 
  skill_generator)
- 2 capabilities gain net-new verbs (reflect / dogfood)
- 4 capabilities deferred to v2 (gate / skills / plugin / shell)
- 1 capability independent (research / workspace)
- 2 domain caps refactor as part of their wave (music / novel)

## Done When

- [ ] Per-capability adoption table above implemented; tests assert
      delegation (`mock prompt.engineer; call analyze.improve; assert
      prompt.engineer was called with builder='improvement-recommendation'`)
- [ ] Backward-compat tests pass: every existing caller still works
      with no API change
- [ ] Migration ledger in `agency/MIGRATION-LEDGER.md` records each
      capability's adoption status (so audit can verify "every cap
      either adopts or is explicitly deferred")
- [ ] `TODO.md` updated with 111 row referencing each child PR

## How the migration is sequenced

```
Wave 1: 109 + 110 + 112 land (the three new caps)
            ↓
Wave 2: per-capability migration PRs (parallel-safe):
   - PR-111A: intent thin-wrappers
   - PR-111B: analyze + develop + document + branch (after 109)
   - PR-111C: delegate + jules + subagent + skill_generator (after 109)
   - PR-111D: reflect.synthesize + dogfood.analyze_observations (net-new)
   - PR-111E: music LLM-verb delegation
            ↓
Wave 3: novel implementation wave consumes the migrated caps
        from the start (no separate migration; pre-baked).
```

## Open questions

1. **Migration ledger format**: a single MIGRATION-LEDGER.md OR
   per-capability followups? Single file is simpler; per-cap is
   discoverable per cap. Recommend single file with H2-per-cap
   sections.
2. **API freezing**: should we freeze existing API now (no breaking
   changes during migration) and version-bump on the migrated set?
   v1 stays additive (no break); v2 may consolidate signatures.
3. **Test discipline**: should migration tests live in
   `tests/test_migration_<cap>.py` or in the capability's existing
   test file? Per-cap test files keep concerns separated.
4. **Order vs parallelism**: 6 capabilities ready-to-adopt after
   109+110+112 — can ship in any order (parallel PRs). 4 deferred
   to v2. Music ships when ready.

## Followup

(Populated when the PR ships.)
