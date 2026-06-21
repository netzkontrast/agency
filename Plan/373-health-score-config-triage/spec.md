---
spec_id: "373"
slug: health-score-config-triage
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 4]
depends_on: ["371", "354", "334", "336", "290", "091"]
domain: analyze
wave: brooks-port
parent_spec: "371"
---

# Spec 373 — Health Score + config + history + triage

> Part of the Spec 371 brooks-lint port. This slice ports brooks-lint's
> **scoring + tunability + lifecycle** layer: the Health Score, the
> `.brooks-lint.yaml` settings, the run history/trend, and the
> accept/dismiss/defer triage — each landing as a **computed value or a graph
> node**, never a frozen snapshot or a sidecar JSON file.

## Why

brooks-lint turns findings into a **decision surface**: a Health Score (base 100,
deductions per finding), a `.brooks-lint.yaml` to tune the bar per team, a
`.brooks-lint-history.json` trend, and an interactive triage (accept/dismiss/
defer/skip) with expiring suppressions. These are what make it usable on a real,
imperfect codebase instead of a wall of red. The port must carry all of them
(Spec 371: "use everything") — but agency already has better homes for two of
them: the **unified config** (Spec 334) and the **provenance graph** (Goal 2),
which replace the two sidecar files with first-class, queryable state.

## Design

### 1. Health Score — computed, preset-weighted (rule 8)

`agency/capabilities/analyze/_score.py` — a pure function over the recorded
`Finding`s:

```
score = max(0, 100 - Σ deduction(finding.tier, preset))
```

The per-tier deductions are a **documented tunable budget** (CLAUDE.md #8 — named
config with a rationale, not a current-state snapshot), vendored from brooks
`common.md`:

| Preset | 🔴 critical | 🟡 warning | 🟢 suggestion |
|---|---|---|---|
| `strict` | −20 | −8 | −2 |
| `balanced` (default) | −15 | −5 | −1 |
| `legacy-friendly` | −8 | −3 | −1 |

`tier` is the **derived** mapping from `FindingSeverity` (Spec 354 §1) — the score
reads `fail/warn/info` → `critical/warning/suggestion`, so there is one severity
source. The weights live in `analyze/data/score-presets.json` (definable
registry), so a team can add a preset without a code edit. The score is
**computed from the live findings every run**, never stored as a magic number;
tests assert the *relationship* (`strict ≤ balanced ≤ legacy-friendly` for the
same findings), not a pinned value.

Under `legacy-friendly`, the report Summary leads with the **three
highest-leverage fixes** (brooks' first-run-not-a-wall-of-red rule) — a render
concern owned by 374, parameterized here. **"Leverage" is a defined, computed
quantity** (Wiegers fix — not a vague adjective): `leverage(finding) =
deduction_weight(tier, preset) × occurrence_count(risk_code)` — the score points
recovered by fixing it × how often that risk recurs. The Summary ranks findings by
`leverage` desc and names the top three. A pure function over the findings + the
preset, testable, no magic.

### 2. Config — map `.brooks-lint.yaml` onto the unified config (Spec 334)

The canonical home is `.agency/config.yaml` under a `quality:` block; the legacy
`.brooks-lint.yaml` is still read for drop-in compat (owner OQ1 default: honor
both, agency canonical, agency wins on conflict). Settings (ported verbatim from
brooks `common.md`):

| Setting | Effect |
|---|---|
| `disable: [R1, T5, ...]` | skip those risks entirely (omitted from report + score) |
| `severity: {R1: suggestion}` | override a risk's tier for this project |
| `ignore: ["**/*.generated.*", ...]` | glob-exclude files (findings solely from them dropped) |
| `focus: [R2, R5]` | evaluate ONLY these (mutually exclusive with `disable`) |
| `strictness: strict\|balanced\|legacy-friendly` | the score preset (§1) |
| `custom_risks: {C1: {...}}` | merge `Cx` definitions into the decay-risk registry (Spec 354 §4) |
| `suppress: [{risk, pattern, expires}]` | scan-time downgrade (§4) |

**Config validation** (ported from brooks `common.md` §Config Validation, surfaced
in the report, never fatal): invalid risk code → skip + note; invalid severity →
skip + note; `disable` AND `focus` both non-empty → ignore both + note; invalid
`strictness` → fall back `balanced` + note; unparseable YAML → defaults. Reuses
the existing `config.validate` path (Spec 334) — the `quality:` block gets a
schema; ad-hoc list/dict blocks skip structured validation (the Spec 352 Slice-2a
precedent).

### 3. History + trend — a graph node, not a sidecar file

brooks appends to `.brooks-lint-history.json`. Agency records each run as a
**graph node** instead (Goal 2): a `QualityRun{mode, scope, score, critical,
warning, suggestion, recorded_at}` SERVING the intent, edged to the `SkillRun`
(372). Then:

- **Trend is a query**, not a file read: `manage.timeline` / `analyze.graph` over
  `QualityRun` nodes for the same mode gives "85 → 82 (−3)" for free, bi-temporal
  and durable across sessions (the sidecar file couldn't survive an ephemeral
  container; the graph snapshot does — Spec 195/289 portability).
- **Trend in ephemeral CI (Hightower fix).** A fresh CI container has an empty
  graph, so trend would always read "first run" — the regression the panel caught.
  374 §3 **caches `.agency/` keyed by the base branch** so prior `QualityRun` nodes
  survive across CI runs; on a cache miss the report says "first run" (an honest
  fallback, not a broken feature). The graph-node design is what makes this
  cache-portable; the old JSON sidecar would have needed the same cache anyway.
- **Incomplete runs are recorded but excluded from trend (Nygard fix).** A walk
  that crashed mid-judgment records `QualityRun{status: incomplete}` with whatever
  partial findings exist; the trend query reads only `status: complete` runs, so a
  partial run never distorts the delta nor reports a (misleadingly high) score as
  the latest point.
- The report's Trend line (374) is derived from the prior same-mode **complete**
  `QualityRun`.
- **No `.brooks-lint-history.json`** — it disappears (port-forward, like
  `report-parse` in 374). Its one-time import is owned by the migration slice
  (Spec 377).

### 4. Triage + suppression — the verb lives in `intent` (owner directive)

brooks' interactive triage (accept/dismiss/defer/skip) and `suppress:` entries
become graph state. The **triage verb is an `intent` concern, not `analyze`**
(owner directive 2026-06-20): a `Finding` SERVES an intent, and triage is a
*judgment about that finding relative to the goal* — accept it, dismiss it as
not-worth-it, defer it. That is the same family as `intent.assumptions` /
`intent.tradeoffs` / `intent.steelman` (codegraph: `intent/_main.py:40` — the
judgment surface). Mechanical `analyze` detects; the intent decides its stance.
So:

- **`intent.triage(finding_id, action, reason="", expires="")`** (`role="act"`,
  lands on `IntentCapability`) — `dismiss` records a `Suppression{risk, pattern,
  reason}` node that SUPPRESSES the finding pattern AND SERVES the intent; `defer`
  adds `expires` (default +90d); `accept` records an `Acknowledgement` (OQ2);
  `skip` no-ops. The `Suppression` + `Acknowledgement` nodes live in the
  **`intent` ontology** (the capability that writes them owns the declaration);
  the `SUPPRESSES` edge points at the `analyze` `Finding` node — a cross-capability
  edge on the one shared graph (the substrate is single; edges cross freely).
- **Scan-time matching stays an `analyze`/score concern** (this spec): on the next
  run, the score path reads live `Suppression`s cross-capability
  (`ctx.find("Suppression")`) and a finding matching one (risk + file glob) is
  downgraded to `info`, shown under a collapsed "Suppressed" section, NOT counted
  in the score. An **expired** suppression is ignored (finding resurfaces at
  original severity) and the Summary notes "N suppressed findings expired and are
  active again" — a graph query: `Suppression` where `expires < now`. So the
  *write* surface is `intent`, the *scoring* read is `analyze` — one node model,
  two readers.
- Interactive triage (the one-finding-at-a-time prompt) is the **Post-Report
  Triage** phase of the mode skill (372), guarded to interactive sessions only
  (skip in CI/headless — brooks' guard). It calls `intent.triage` per finding, so
  CI and interactive share one write path.

> **Tension resolved — suppression is keep-both, not delete (Spec 292).** A
> suppressed finding is still *recorded* (the run produced it); the `Suppression`
> only changes its *tier* on read. History never lies about what was found — the
> finding node persists, the suppression is a separate, expiring overlay. This is
> the bi-temporal keep-both discipline applied to triage.

### What this slice does NOT do

- No report rendering / SARIF (374) — it computes the score + the suppressed set;
  374 renders them.
- No new findings — it scores/filters the findings 354/372 produce.
- **No triage VERB here** — `intent.triage` lands on `IntentCapability` (§4); this
  spec owns only the scan-time suppression *scoring* read. The `Suppression` /
  `Acknowledgement` node declarations move to the `intent` ontology.
- No deletion of suppressed findings (keep-both).
- No frozen score constants (rule 8) — only the named preset weights, which are
  documented tunable budgets.

## Acceptance (Gherkin)

```gherkin
Scenario: the score is computed per preset, not pinned
  Given findings: 1 critical, 2 warning, 3 suggestion
  When I score under balanced
  Then the score is 100 - (15 + 2*5 + 3*1) = 72
  And the same findings score lower under strict and higher under legacy-friendly

Scenario: disable removes a risk from report and score
  Given config quality.disable includes R1
  When a review runs over code with an R1 finding
  Then no R1 finding appears in the report
  And the score deduction for it is not applied

Scenario: focus and disable together is a config error
  Given config sets both quality.focus and quality.disable non-empty
  Then both are ignored and the report notes the config error

Scenario: trend comes from the graph, not a file
  Given two prior QualityRun nodes for mode "review"
  When a third review runs
  Then the report Trend line shows the delta from the most recent prior run
  And no .brooks-lint-history.json is written

Scenario: a dismissed finding is suppressed next run, with provenance
  Given I dismiss an R3 finding in src/util.py via intent.triage with a reason
  When the same review runs again
  Then the finding is downgraded to info under a collapsed Suppressed section
  And a Suppression node (in the intent ontology) records the risk, pattern, and reason
  And the Suppression SERVES the intent and SUPPRESSES the analyze Finding (cross-capability edge)
  And the finding node still exists (keep-both — history is not rewritten)

Scenario: a deferred suppression expires and resurfaces
  Given a Suppression with expires in the past
  When a review runs
  Then the finding resurfaces at its original severity
  And the Summary notes that N suppressions expired
```

## Open questions

- **OQ1** — keep reading `.brooks-lint.yaml`, or require migration to
  `.agency/config.yaml quality:`? (Default: read both for one release, deprecate.)
- **OQ2** — should `accept` (acknowledge) also create a `Suppression`-like node so
  "acknowledged, won't fix" is queryable, or stay a no-op? (Default: record an
  `Acknowledgement` node in the `intent` ontology — the provenance is cheap and
  useful.)
- **OQ3** — does `intent.triage` need the `Finding`'s `risk_code` + `file` to build
  the `Suppression` pattern, or does it take them as args? (Default: read them from
  the `Finding` node by `finding_id` — one source, no caller duplication.)

## Followup — Implementation Status (2026-06-20)

**DRAFTED 2026-06-20** — the scoring/config/triage slice of the Spec 371 program.
No code yet. Reuses Spec 334 (unified config), Spec 290 (`manage.timeline` for
trend), Spec 336/292 (keep-both, no sidecar files). Depends on 354 (the `tier`
mapping + finding shape). **Amended 2026-06-20 (owner directive):** the triage
verb moves to `intent.triage` (judgment about a finding = an intent concern); the
`Suppression`/`Acknowledgement` nodes move to the `intent` ontology, with the
`SUPPRESSES` edge crossing to the `analyze` `Finding`. This spec keeps the
score/config/history machinery + the scan-time suppression *scoring* read.

**Amended 2026-06-20 (spec-panel critique):** "highest-leverage" is now a defined
computed quantity `deduction_weight(tier) × occurrence_count` (Wiegers); the
`QualityRun` node gains a `status` field (complete|incomplete) so a crashed walk is
recorded but excluded from trend (Nygard); the ephemeral-CI trend gap is closed by
374's base-branch `.agency` cache, with "first run" as the honest miss-fallback
(Hightower); `.brooks-lint-history.json` one-time import moves to the new migration
slice (Spec 377). Next (after 354): `_score.py` + `score-presets.json` + the
`quality:` config block + `QualityRun{status}` node + the score-side suppression
read, RED→GREEN; `intent.triage` + the `Suppression`/`Acknowledgement` ontology
land on `IntentCapability`.

**Slice 1 SHIPPED 2026-06-21 (TDD) — the Health Score engine (§1).**
`analyze/_score.py` (pure: `score = max(0, 100 - Σ deduction(tier, preset))`
floored at 0; `leverage = deduction_weight(tier) × occurrence_count(risk_code)`;
`top_leverage` ranks one representative per recurring risk) + the per-tier
deduction budgets in `analyze/data/score-presets.json` (definable registry,
`_source`-stamped — strict/balanced/legacy-friendly, a documented tunable budget
NOT a snapshot, rule 8); `analyze.score(findings, preset)` (role=`transform`,
READ-ONLY — folds nothing into the graph yet, the QualityRun node is Slice 2).
`tier` reads `Finding.tier` (Spec 354 §1 — one severity source); unknown preset
falls back to balanced (§2 default). **4 Gherkin scenarios**
(`tests/acceptance/features/health_score.feature`) assert the score as a
RELATIONSHIP (strict ≤ balanced ≤ legacy-friendly), the zero floor, the
preset fallback, and leverage ranking — never a pinned snapshot. Install regen +
analyze test slice green (60 passed). **Still (Slice 2+):** the `quality:` config
block (disable/severity/ignore/focus/strictness/custom_risks) onto Spec 334 +
validation; the `QualityRun{status}` history node + trend query; the scan-time
suppression *scoring* read; and `intent.triage` + the `Suppression`/
`Acknowledgement` ontology on `IntentCapability`.
