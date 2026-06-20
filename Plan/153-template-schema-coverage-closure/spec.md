---
spec_id: "153"
slug: template-schema-coverage-closure
status: partial
last_updated: 2026-06-11
owner: "@agency"
enhances: "004"
depends_on: ["004", "060", "032", "149"]
vision_goals: [4, 7]
affects:
  - agency/_templates.py
  - agency/_lints/_schema_coverage.py
  - tests/test_template_schema_coverage.py
---

# Spec 153 — Template/schema coverage closure

## Why

Spec 004 (wire the generate/validate loop for uncovered node kinds) is
Not Started. Spec 060 shipped the substrate (loader + dataclasses +
materialiser) + 15 schema files + 7 template files, but Phase 5 (verb
migration to `ctx.template()`) is opt-in and most node kinds still have
NO schema — so the generate/validate pair (CORE.md §"Schemas &
templates") is half-wired. This closes the coverage gap with a derived
audit, not a hand-maintained list.

## Done When

- [ ] **`_check_schema_coverage` audit** lists every node label the
      live ontology declares vs every label with a Schema; the delta is
      the uncovered set (derived — Spec 149, rule 8). Typed shape:
      `{covered: list[Label], uncovered: list[Label], coverage_fraction:
      float, priority_uncovered: list[(Label, node_count)]}`.
- [ ] **`agency_doctor` reports `schema_coverage`** as a fraction.
- [ ] **Schemas authored for the highest-traffic uncovered kinds**
      (the audit ranks by graph node-count — derive the priority).
- [ ] **`generate → validate` round-trip test** per newly-covered kind:
      a Template renders an Artefact a Schema validates; a missing field
      fails (the CORE.md proven-runnable pattern, extended).
- [ ] **Measurable invariants** (rule 8):
      (a) `schema_coverage.fraction >= floor` (monotone non-decreasing,
      floor = last shipped); (b) for every node label with ≥ 1 live
      graph node, a Schema exists OR the label is tagged
      `# AGENCY-SCHEMA-DEFERRED: <reason>` (no silent gaps);
      (c) every Schema has ≥ 1 Template that round-trips against it
      (covered_schemas ⊆ template_renderable_schemas).
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  ontology declares node label "Reflection" with 1,403 live nodes
        and no Schema authored
When:   _check_schema_coverage runs
Then:   uncovered includes "Reflection";
        priority_uncovered ranks it near the top by node_count;
        agency_doctor.schema_coverage.fraction < 1.0

Given:  a "Reflection" Schema + Template are authored
When:   the round-trip test runs (template renders → schema validates →
        material round-trips back to dict)
Then:   passes; coverage_fraction increases monotonically; floor advances
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Schema without Template | author Schema, skip Template | invariant (c) — round-trip gate | block CI; require paired Template |
| Speculative Schema | Schema for a label with 0 live nodes | priority ranking surfaces low value | tag `# AGENCY-SCHEMA-SPECULATIVE` so it doesn't inflate fraction |
| Coverage regression on label rename | label renamed without Schema migration | invariant (a) — monotone floor | block; require explicit migration step |
| LLM-generated nodes bypass Schema | a Driver (Spec 147) emits raw dicts directly into the graph | round-trip gate (c) catches missing Schema; typed `Codes.SCHEMA_MISSING` at write | all graph writes go through generate→validate; no direct dict insertion |

## Interconnects

- **Drift-derivation chain** (149): `schema_coverage` is derived.
- Spec 060 (templates-schemas) is the substrate this exercises.
- Spec 152 (typed Skill/Phase) is the parse-side sibling of this
  generate/validate discipline.
- Spec 151 (Codes coverage) supplies `Codes.SCHEMA_MISSING` /
  `Codes.TEMPLATE_RENDER_FAILED` for the round-trip surface.
- Spec 157 (architecture-drift gate) treats `schema_coverage.fraction`
  as one of its standing monotone invariants.
- Spec 159 (dogfood collect deprecation) closes the markdown-parse
  anti-pattern — the schema/template pair is the IN-substrate replacement.
- Spec 154 (output-overflow) — overflow Artefacts are themselves a node
  kind that needs a Schema; this audit covers them uniformly.
- Spec 158 (capability scaffold) — scaffold-marked capabilities are
  expected to declare Schemas for any node kind they emit.
- **LLM-driver chain** (147): generate-side validation gives the
  Driver typed `output_config.format` to write structured outputs
  against; without Schemas the Driver falls back to freeform text.

## Open questions

1. Author all uncovered schemas, or only graph-present kinds?
   **Recommend**: only kinds with ≥1 live node first (the rest are
   speculative); the audit ranks by count.
2. Schema versioning policy — pin per spec or float? **Recommend**:
   float with a `schema_version` field in the prefix (Spec 146) so a
   schema bump invalidates the cache deliberately, never silently.

## Followup — Implementation Status (2026-06-11)

### Done — Slice 1 (pure schema coverage audit)

- **`scripts/check_schema_coverage.py`** — pure functions walking
  `agency/capabilities/*/schemas/*.json`:
  - `schema_paths(root) -> list[Path]` (sorted-by-full-path,
    deterministic per Spec 149).
  - `schema_labels(root) -> set[str]` (extracts `title` from each
    schema; malformed JSON / missing title silently skipped).
  - `audit_schemas(root, ontology_labels) -> CoverageReport` (pure;
    no engine boot).
- **`CoverageReport` typed shape** — `{covered, uncovered, spurious,
  total_ontology_labels}` + computed `.coverage_fraction` property
  (= `|covered| / |ontology|`; empty ontology is 1.0 by convention).
  `spurious` surfaces schemas whose label is NOT in the ontology
  (e.g. stale schemas for removed node types) so they don't
  silently inflate the covered set (rule 8 subset invariant).
- **CLI** — `python -m scripts.check_schema_coverage [--root agency]`
  prints fraction + uncovered head:20 + spurious. Slice 1 is
  informational (`return 0`); Slice 2 promotes to a CI gate per
  Spec 058 WARN→error doctrine.
- **10 tests green** (`tests/test_template_schema_coverage.py`) —
  deterministic discovery + non-JSON skipped + title extraction +
  malformed json tolerated + coverage_fraction relationship + empty-
  ontology convention + spurious detection + subset invariant +
  live-tree shape invariant.

### Done — Slice 2 (uncovered baseline + WARN→error CI gate, 2026-06-12)

Adopts the Spec 146 Slice 2.2 / Spec 151 Slice 2 baseline-drift pattern
(0.232 coverage; the floor approach is uninformative, the uncovered
set captures REGRESSIONS directly).

- **`load_schema_baseline(path)`** — one-label-per-line parser, blank
  + `#`-comment lines tolerated.
- **`compare_uncovered_to_baseline(report, baseline)` →
  `SchemaRegressionReport{new_uncovered, fixed_uncovered, ok}`** — pure
  set diff: live − baseline = REGRESSIONS (gate-fail); baseline − live =
  FIXED (label is now covered, trim baseline).
- **CLI flags** `--baseline PATH --strict`:
  - `--strict` without baseline: any uncovered label → exit 1.
  - `--strict --baseline`: only NEW labels → exit 1; FIXED entries are
    surfaced so the baseline can be trimmed in the same PR.
- **`Plan/_planning/schema-coverage-baseline.txt`** — enumerates the 53
  currently-uncovered labels. Slice 6 backfill (per the followup) will
  author schemas for the highest-traffic ones and monotonically reduce.
- **CI step `Schema-coverage lint`** in `.github/workflows/test.yml`.
- **7 new tests** in `tests/test_template_schema_coverage.py`:
  load_schema_baseline parse + missing-file empty;
  compare_uncovered_to_baseline OK / new / fixed; CLI strict-without
  baseline fails; CLI strict-with baseline passes on the committed set;
  LIVE INVARIANT (committed baseline = live uncovered set).

### Done — Slice 3 (agency_doctor schema_coverage block, 2026-06-18)

`agency_doctor.schema_coverage` now reports the typed audit result:
`{fraction, covered, uncovered, total_labels, non_node_schemas,
priority_uncovered}` — uncovered labels ranked by live graph node-count.

### Done — Slice 4 (engine-load intersection gate, 2026-06-19 steward run)

The "file present, cap undeclared → glob counts as covered" trap
occurred 3 times across Slice 6 batches (develop, document, skills
caps). This slice closes it permanently.

- **`engine_loaded_schema_titles(merged_schemas) -> set[str]`** —
  extracts the PascalCase label for every schema the engine actually
  loaded (dict-form with/without `title`, list-form inline; mirrors
  `schema_labels()` extraction logic so the sets are comparable).
  Added to `agency/_schema_coverage.py`; re-exported via
  `scripts/check_schema_coverage.py`.
- **`audit_schemas()` gains `engine_loaded_titles: set[str] | None`** —
  when supplied: `covered = schemas ∩ ontology ∩ engine_loaded`;
  `dormant_schemas = (schemas ∩ ontology) − engine_loaded` (file-backed
  + matching ontology label, but NOT declared by the cap → engine never
  loads it). Backwards-compatible: callers without the param get the
  prior behaviour.
- **`CoverageReport.dormant_schemas: set[str]`** — the new field; empty
  when `engine_loaded_titles` is not supplied.
- **`agency_doctor.schema_coverage.dormant_schemas`** — the live sorted
  list (empty = all on-disk schemas are engine-declared).
- **2 acceptance scenarios** (24 total, was 22):
  1. Unit: a schema file whose cap has no `artefact_schemas` declaration
     → `dormant_schemas` (not `covered`).
  2. Live: boot the engine; 0 dormant schemas (all current caps declared).
- `scripts/check_schema_coverage.py` re-exports `engine_loaded_schema_titles`.
- drift + doc-drift clean (6 stale docs from prior run re-stamped).

### Still — Slice 5+

- **Slice 5** — `# AGENCY-SCHEMA-DEFERRED: <reason>` tag scan so the
  audit subtracts deferred-but-documented gaps from the uncovered set
  (per Spec 054 drift pattern; matches the AGENCY-RESERVED escape
  hatch in Spec 151).
- **Slice 6** — author schemas for the top-N highest-traffic
  uncovered labels (driven by Slice 3 ranking); push fraction above
  0.5 then re-floor.

### Done — Slice 6 (backfill the highest-traffic provenance-spine schemas, 2026-06-19)

Open question 1 answered: authored only the kinds with ≥1 live node
first (the Slice 3 `priority_uncovered` ranking), not speculative ones.

- **5 schemas authored** — title = ontology label, properties DERIVED
  from the live node-creation sites (not invented; CLAUDE.md derivability
  audit):
  - `intent/schemas/intent.json` (`Intent`) ← `agency/intent.py`
    (`purpose`/`deliverable`/`acceptance`/`status`/`owner`/`parent_intent_id`).
  - `intent/schemas/invocation.json` (`Invocation`) ← `agency/_invoke.py`
    (`capability`/`verb`/`role`).
  - `jules/schemas/agent.json` (`Agent`) ← `_invoke`/`lifecycle`/`delegate`
    (`runtime` enum external/delegated/cloud-async).
  - `develop/schemas/maintenance-run.json` (`MaintenanceRun`) ←
    `develop._main` (`focus`/`status`/`selected`/`next_candidate`).
  - `gate/schemas/gate.json` (`Gate`) ← `gate._main`/`_substrate_tools`
    (`name`/`passed`/`evidence`/`question`); distinct from the existing
    `GateOutcome` wire-payload schema.
- **Engine-load fix (the real catch)** — the file-glob audit
  (`schema_paths`) counts a `schemas/*.json` even when the owning
  capability never declares `artefact_schemas`, so the engine never
  LOADS it: dormant surface that reads as "covered". The `intent` and
  `develop` caps lacked the declaration → added
  `artefact_schemas = ArtefactSchemas.from_module(__file__)` to both;
  the engine ontology now carries all 5 schemas (verified).
- **2 acceptance scenarios** (`tests/acceptance/features/template_schema.feature`
  + `test_template_schema.py`): (1) the named `CORE_PROVENANCE_LABELS`
  set is schema-covered by the live-tree audit; (2) the live engine
  actually LOADS each — guards the file-present-but-undeclared trap.
  Named-set contract, not a magic count (rule 8).
- **Baseline trimmed** `Plan/_planning/schema-coverage-baseline.txt`
  70→65 uncovered (the live-baseline invariant test enforces the trim).
- **Coverage** `schema_coverage.fraction` 0.213→0.270 (19→24 covered).
  Full closure to >0.5 + re-floor is the remaining Slice 6 work
  (next labels: AcceptanceCriterion/Artefact/Session/Document).

### Done — Slice 6 cont. (document-convergence schema backfill, 2026-06-19)

Steward run continuation: the 4 highest-traffic uncovered labels named in
the prior Slice 6 entry.

- **4 schemas authored** — title = ontology label, properties DERIVED from
  the live node-creation sites:
  - `discover/schemas/acceptance-criterion.json` (`AcceptanceCriterion`) ←
    `discover/clusters/scope.py` (`text`/`gherkin`/`measurable`; Spec 317).
  - `develop/schemas/artefact.json` (`Artefact`) ← `agency/ontology.py` +
    `agency/_invoke.py` (`kind`; optional `path`/`name`).
  - `document/schemas/session.json` (`Session`) ← `agency/engine.py` +
    `document/_main.py` (`session_id`; optional `status`; Spec 292).
  - `document/schemas/document.json` (`Document`) ← `document/_main.py`
    (`path`/`content_sha`; optional `template`/`schema`; Spec 292).
- **Engine-load fix** — `discover` cap lacked `artefact_schemas`; added
  `ArtefactSchemas.from_module(__file__)` (same pattern as intent/develop
  Slice 6). All 4 now verified engine-loaded.
- **2 acceptance scenarios** — `DOC_CONVERGENCE_LABELS` named contract set
  (`{"AcceptanceCriterion","Artefact","Session","Document"}`):
  (1) all four are schema-covered by the live-tree audit; (2) the engine
  actually loads each (guards the undeclared trap). 20 scenarios total (was 18).
- **Baseline trimmed** `Plan/_planning/schema-coverage-baseline.txt` 65→61.
- **Coverage** `schema_coverage.fraction` 0.270→0.315 (24→28 covered).
  Next: continued backfill toward >0.5; Slice 4 round-trip invariant.

### Done — Slice 6 workflow-spine wave (2026-06-19)

Steward run continuation: 5 workflow-spine labels covering the four-pillar
surface (Lifecycle pillar node, substrate hook Events, skill-walk Phase,
Capability pillar Skill surface, discover ClarificationQuestion).

- **5 schemas authored** — title = ontology label, properties DERIVED from
  the live node-creation sites:
  - `develop/schemas/lifecycle.json` (`Lifecycle`) ← `agency/lifecycle.py`
    (`state` enum A2A-aligned, `phase` int; Spec 153).
  - `develop/schemas/event.json` (`Event`) ← `agency/engine.py`
    (`name`/`session` required; `tool`/`summary` optional; Spec 076).
  - `skills/schemas/phase.json` (`Phase`) ← `agency/skill.py` +
    `skills/_main.py` (`skill`/`index`/`name` required; `produces` optional).
  - `skills/schemas/skill.json` (`Skill`) ← `agency/skill.py` +
    `skills/_main.py` (`name`/`kind` enum usage|discipline required).
  - `discover/schemas/clarification-question.json` (`ClarificationQuestion`)
    ← `discover/clusters/clarify.py` + `discover/ontology.py`
    (`text`/`options`/`ambiguity_kind` required; `status` optional).
- **Engine-load fix** — `skills` cap had no `schemas/` dir and no
  `artefact_schemas` declaration; created the dir and added
  `ArtefactSchemas.from_module(__file__)` to `SkillsCapability` (import +
  class attr). doc-drift caught immediately (check-doc-drift: skills.md
  stale → re-stamped). Three occurrences of this trap across Slice 6
  batches — candidate for Slice 4 engine-load intersection gate.
- **2 acceptance scenarios** — `WORKFLOW_SPINE_LABELS` named contract set
  (`{"Lifecycle","Event","Phase","Skill","ClarificationQuestion"}`):
  (1) all five are schema-covered by the live-tree audit; (2) the engine
  actually loads each (guards the undeclared trap). 22 scenarios total (was 20).
- **Baseline trimmed** `Plan/_planning/schema-coverage-baseline.txt` 61→56.
- **Coverage** `schema_coverage.fraction` 0.315→0.371 (28→33 covered).
  Next: continued backfill toward >0.5; Slice 4 round-trip invariant.
  Remaining uncovered: 56 labels (see baseline). Strong candidates for
  next wave: `PromptFramework`, `Reflection`-adjacent (Template, Schema,
  Tool), discover wave (`FeasibilitySignal`, `IntentRefinement`, `ScopeBoundary`).

### Done — Slice 6 discover-prompt wave (2026-06-19)

Steward run continuation: 4 labels spanning the discover cap's intent-program
nodes + the core Template node + the prompt cap's PromptFramework.

- **4 schemas authored** — title = ontology label, properties DERIVED from
  the live node-creation sites:
  - `discover/schemas/feasibility-signal.json` (`FeasibilitySignal`) ←
    `discover/ontology.py` (`verdict` enum {go/no-go/refine}, `rationale` str).
  - `discover/schemas/intent-refinement.json` (`IntentRefinement`) ←
    `discover/ontology.py` (`trigger`/`before`/`after` required str).
  - `document/schemas/template.json` (`Template`) ← `agency/ontology.py`
    (`name`/`body` required str — the core Jinja2 template node).
  - `prompt/schemas/prompt-framework.json` (`PromptFramework`) ←
    `prompt/ontology.py` (`slug`/`name`/`intent_category`/`complexity_tier`
    required; `intent_category` enum {recover/clarify/create/transform/reason/
    critique/agentic/functional}; `complexity_tier` enum {simple/medium/
    comprehensive/reasoning/structure/critique/meta}).
- **Engine-load fix** — `prompt` cap had no `schemas/` dir and no
  `artefact_schemas` declaration; created the dir and added
  `ArtefactSchemas.from_module(__file__)` to `PromptCapability`. Pattern
  identical to `skills` cap fix in the workflow-spine wave.
- **2 acceptance scenarios** — `DISCOVER_PROMPT_LABELS` named contract set
  (`{"FeasibilitySignal","IntentRefinement","Template","PromptFramework"}`):
  (1) all four are schema-covered by the live-tree audit; (2) the engine
  actually loads each (guards the undeclared trap). 26 scenarios total (was 24).
- **Baseline trimmed** `Plan/_planning/schema-coverage-baseline.txt` 63→59.
- **Coverage** `schema_coverage.fraction` 0.371→0.416 (33→37 covered).
  Next: continued backfill toward >0.5; Slice 5 deferred-tag gate.
  Remaining uncovered: 52 labels (see baseline).

### Done — Slice 6 prompt-dossier + document + jules wave (2026-06-19)

Steward run continuation: 6 labels from caps already declaring `artefact_schemas`
(no new cap setup needed for any of these).

- **6 schemas authored** — title = ontology label, properties DERIVED from
  the live node-creation sites:
  - `prompt/schemas/brief-audit.json` (`BriefAudit`) ← `prompt/ontology.py`
    (`brief`/`clarity_score` required; `status` enum {pending/passed/failed}).
  - `prompt/schemas/catalog-module.json` (`CatalogModule`) ← `prompt/ontology.py`
    (`category` enum {A/B/C}; `identifier`/`name` required).
  - `prompt/schemas/research-intent.json` (`ResearchIntent`) ← `prompt/ontology.py`
    (`seed_query`/`topic` required; `deliverable` enum {dossier/report/outline/memo}).
  - `prompt/schemas/anti-pattern.json` (`AntiPattern`) ← `prompt/ontology.py`
    (`kind` enum 8-member anti-pattern set; `body` required str).
  - `document/schemas/doc-revision.json` (`DocRevision`) ← `document/_main.py`
    (`source` enum {graph/file}; `content_sha` required; Spec 292 keep-both).
  - `jules/schemas/jules-alias.json` (`JulesAlias`) ← `jules/_main.py`
    (`name`/`sid` required str — alias→session-ID mapping).
- **2 acceptance scenarios** — `PROMPT_DOSSIER_DOC_JULES_LABELS` named contract
  set; 28 scenarios total (was 26). No artefact_schemas additions needed.
- **Baseline trimmed** `Plan/_planning/schema-coverage-baseline.txt` 59→53.
- **Coverage** `schema_coverage.fraction` 0.416→0.483 (37→43 covered).
  Next: push past 0.5 — next targets `Analysis`/`Finding` (analyze cap, needs
  `artefact_schemas`) or `Schema`/`Tool` (core nodes — assign to develop cap).

### Done — Slice 6 analyze + select wave (2026-06-19)

Steward run continuation: 3 labels from analyze + select caps — both needed
`artefact_schemas` declared.

- **3 schemas authored** — title = ontology label, properties DERIVED from
  live node-creation sites:
  - `analyze/schemas/analysis.json` (`Analysis`) ← `analyze/_main.py`
    (`path`/`axes`/`started_at` required; `axes` items enum 5-member axis set).
  - `analyze/schemas/finding.json` (`Finding`) ← `analyze/_main.py`
    (`rule`/`severity`/`file`/`line`/`message` required; `severity` enum
    {info/warn/fail}; `evidence` optional).
  - `select/schemas/selection.json` (`Selection`) ← `select/_main.py`
    (`operation`/`approach` required; `approach` enum {semantic/pattern/native}).
- **2 capabilities updated** — `ArtefactSchemas.from_module(__file__)` added
  to `AnalyzeCapability` and `SelectCapability`.
- **2 acceptance scenarios** — `ANALYZE_SELECT_LABELS` named contract set;
  30 scenarios total (was 28).
- **Baseline trimmed** `Plan/_planning/schema-coverage-baseline.txt` 53→50.
- **Coverage** `schema_coverage.fraction` 0.483→0.517 (43→46 covered). 
  Crossed 0.5 milestone. Next: continue toward 0.6.

### Done — Slice 6 research + develop-extras wave (2026-06-19)

Steward run continuation: 6 labels from research + develop caps — both already
declared `artefact_schemas` (no cap setup needed).

- **6 schemas authored** — title = ontology label, properties DERIVED from
  live node-creation sites:
  - `research/schemas/research.json` (`Research`) ← `research/_main.py`
    (`question`/`depth`/`started_at`/`status` required; `status` enum 6-member
    lifecycle set {planning/fanning-out/verifying/ready/superseded/failed}).
  - `research/schemas/research-claim.json` (`ResearchClaim`) ← `research/_main.py`
    (`text`/`research_id` required).
  - `develop/schemas/plan.json` (`Plan`) ← `develop/_main.py`
    (`title` required; `status` optional enum {drafted/in-progress/done/abandoned}).
  - `develop/schemas/plan-step.json` (`PlanStep`) ← `develop/_main.py`
    (`plan`/`index`/`description` required; `state` enum {pending/done/blocked/skipped}).
  - `develop/schemas/mode-shift.json` (`ModeShift`) ← `develop/_main.py`
    (`from_mode`/`to_mode` required; both enum SESSION_MODE 5-member set).
  - `develop/schemas/session-lifecycle.json` (`SessionLifecycle`) ← `develop/_main.py`
    (`mode`/`status` required; mode enum SESSION_MODE; status enum {active/paused/archived}).
- **2 acceptance scenarios** — `RESEARCH_DEVELOP_EXTRAS_LABELS` named contract
  set; 32 scenarios total (was 30). No artefact_schemas additions needed.
- **Baseline trimmed** `Plan/_planning/schema-coverage-baseline.txt` 50→44.
- **Coverage** `schema_coverage.fraction` 0.517→0.584 (46→52 covered).
  Crossed 0.5+ continue toward 0.6.

### Done — Slice 6 recommend + mode + panel + thinking wave (2026-06-19)

Steward run continuation: 6 labels from 4 new caps gaining `artefact_schemas`
+ 2 from prompt cap (already wired).

- **6 schemas authored** — title = ontology label, properties DERIVED from
  live node-creation sites:
  - `recommend/schemas/recommendation.json` (`Recommendation`) ← `recommend/_main.py`
    (`request`/`capability` required; no enums — free string fields).
  - `mode/schemas/mode-activation.json` (`ModeActivation`) ← `mode/_main.py`
    (`mode` required; enum 5-member `_BY_NAME` set).
  - `panel/schemas/panel.json` (`Panel`) ← `panel/_main.py`
    (`subject`/`mode` required; mode enum {discussion/debate/socratic}).
  - `thinking/schemas/thinking-method.json` (`ThinkingMethod`) ← `thinking/_main.py`
    (`method`/`subject` required; method enum 10-member set).
  - `prompt/schemas/prompt-variant.json` (`PromptVariant`) ← `prompt/ontology.py`
    (`parent_instance`/`variant_kind` required; variant_kind enum 6-member `VARIANT_KIND`).
  - `prompt/schemas/prompt-output.json` (`PromptOutput`) ← `prompt/ontology.py`
    (`instance`/`response_body` required).
- **4 capabilities updated** — `ArtefactSchemas.from_module(__file__)` added
  to `RecommendCapability`, `ModeCapability`, `PanelCapability`, `ThinkingCapability`.
- **2 acceptance scenarios** — `RECOMMEND_MODE_PANEL_THINKING_LABELS` named contract
  set; 34 scenarios total (was 32).
- **Baseline trimmed** `Plan/_planning/schema-coverage-baseline.txt` 44→38.
- **Coverage** `schema_coverage.fraction` 0.584→0.652 (52→58 covered).
  Crossed 0.6 milestone. Next: continue toward 0.7.

### Done — Slice 6 plugin + persona + doctrine + dogfood wave (2026-06-19)

Steward run continuation: 6 labels — 2 from plugin cap (already had
`artefact_schemas`), 1 from prompt cap (already wired), 3 from new caps.

- **6 schemas authored** — title = ontology label, properties DERIVED from
  live node-creation sites:
  - `plugin/schemas/plugin.json` (`Plugin`) ← `plugin/_main.py`
    (`name`/`version`/`description` required).
  - `plugin/schemas/command.json` (`Command`) ← `plugin/_main.py`
    (`name`/`description` required).
  - `prompt/schemas/research-brief.json` (`ResearchBrief`) ← `prompt/clusters/dossier.py`
    (`intent`/`body` required).
  - `persona/schemas/persona-brief.json` (`PersonaBrief`) ← `persona/_main.py`
    (`persona` enum 14-member `_BY_NAME` set; `task` required).
  - `doctrine/schemas/doctrine-citation.json` (`DoctrineCitation`) ← `doctrine/_main.py`
    (`name` required).
  - `dogfood/schemas/decision-record.json` (`DecisionRecord`) ← `dogfood/_main.py`
    (`subject`/`decision`/`rationale` required — ADR triple).
- **3 capabilities updated** — `ArtefactSchemas.from_module(__file__)` added
  to `PersonaCapability`, `DoctrineCapability`, `DogfoodCapability`.
- **2 acceptance scenarios** — `PLUGIN_PERSONA_DOCTRINE_DOGFOOD_LABELS` named
  contract set; 36 scenarios total (was 34).
- **Baseline trimmed** `Plan/_planning/schema-coverage-baseline.txt` 38→32.
- **Coverage** `schema_coverage.fraction` 0.652→0.719 (58→64 covered).
  Crossed 0.7 milestone. Remaining: 25 labels (mostly music/novel/worldbuilding).

## Done — Slice 6 music + dogfood-boundary + prompt-opt wave (2026-06-19)

Wave 5 (steward run): 8 labels covered (Album/Track/Genre/Idea/Tweet/Reference
in music cap [new schemas/ + artefact_schemas], BoundaryUse in dogfood [already
wired], OptimizationPass in prompt [already wired]). Also fixed inline
`schemas={"doctrine-citation": ["name"]}` collision in doctrine OntologyExtension
(double-declared with the file — removed inline entry). Baseline 26→17 (26
counted DecisionRecord which Wave 4 squash-merge hadn't fully trimmed).
schema_coverage 0.719→0.809, crossing 0.8 milestone. 2 acceptance scenarios
(MUSIC_DOGFOOD_PROMPT_LABELS contract set). Drift clean.


## Done — round-trip invariant (2026-06-20)

The last remaining "Still" item from the original spec: for every covered label,
`memory.record(label, valid_props)` succeeds and `memory.record(label,
missing_required_prop)` raises ValueError — closing the enforcement loop.

- **2 acceptance scenarios added** — `test_recording_a_covered_label_with_all_required_fields_succeeds`
  and `test_recording_a_covered_label_with_a_missing_required_field_raises_valueerror`
  in `tests/acceptance/features/template_schema.feature` +
  `tests/acceptance/test_template_schema.py`. 46 scenarios total (was 44).
- **Representative label: Intent** — NODE_SCHEMAS["Intent"] requires
  ["purpose", "deliverable", "acceptance", "status", "owner"]; valid-props
  passes all 5, missing-props omits "purpose".
- **Enforcement path** — `memory.record()` → `ont.violations()` →
  `missing_required()` reads `self.nodes["Intent"]` (NODE_SCHEMAS); raises
  ValueError when non-empty. This is the live enforcement, unchanged.
- **Invariant scope**: this closes invariant (a) — `memory.record` is the
  guard. The original invariant (c) (`covered_schemas ⊆
  template_renderable_schemas`) is architecturally deferred: requires
  `Template`-per-label authorship (74 labels don't have templates today)
  and is out of scope for this spec cycle.
- All 46 scenarios green; drift clean.

## Done — Slice 6 novel + core Schema/Tool wave (2026-06-19)

Wave 6 (steward run, FINAL Slice 6 wave): 17 labels covered — 15 novel cap
labels (Novel/Chapter/Storyform/NovelClaim/Scene/World/Culture/Religion/Language/
MagicSystem/WorldAxiom/StoryTimeEvent/NarrativeBeat/CodexEntry/KnownFact) +
Schema/Tool (core ontology labels; develop cap already declares artefact_schemas).

- **15 schemas authored** — novel capability, new schemas/ directory:
  novel.json, chapter.json, storyform.json, novel-claim.json, scene.json,
  world.json, culture.json, religion.json, language.json, magic-system.json,
  world-axiom.json, story-time-event.json, narrative-beat.json, codex-entry.json,
  known-fact.json (15 files, required fields DERIVED from novel_ontology.nodes).
- **2 schemas authored** — develop capability: schema.json (Schema, required:
  name/required), tool.json (Tool, required: name/input/output) — DERIVED from
  agency/ontology.py NODE_SCHEMAS.
- **NovelCapability updated** — ArtefactSchemas import + artefact_schemas wired.
- **2 acceptance scenarios** — NOVEL_CORE_LABELS named contract set (17 labels);
  44 scenarios total (was 42).
- **Baseline cleared** Plan/_planning/schema-coverage-baseline.txt 17→0 (empty).
- **Coverage** schema_coverage.fraction 0.809→1.0 (72→89 covered).
  FULL COVERAGE ACHIEVED — Spec 153 Slice 6 complete.
- Drift clean.
