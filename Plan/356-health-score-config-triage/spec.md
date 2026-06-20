---
spec_id: "356"
slug: health-score-config-triage
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 4]
depends_on: ["353", "354", "334", "336", "290"]
domain: analyze
wave: brooks-port
parent_spec: "353"
---

# Spec 356 — Health Score + config + history + triage

> Part of the Spec 353 brooks-lint port. This slice ports brooks-lint's
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
(Spec 353: "use everything") — but agency already has better homes for two of
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
concern owned by 357, parameterized here.

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
(355). Then:

- **Trend is a query**, not a file read: `manage.timeline` / `analyze.graph` over
  `QualityRun` nodes for the same mode gives "85 → 82 (−3)" for free, bi-temporal
  and durable across sessions (the sidecar file couldn't survive an ephemeral
  container; the graph snapshot does — Spec 195/289 portability).
- The report's Trend line (357) is derived from the prior same-mode `QualityRun`.
- **No `.brooks-lint-history.json`** — it disappears (port-forward, like
  `report-parse` in 357).

### 4. Triage + suppression — provenance, with expiry

brooks' interactive triage (accept/dismiss/defer/skip) and `suppress:` entries
become graph state:

- `analyze.triage(finding_id, action, reason="", expires="")` (`role="effect"`) —
  `dismiss` records a `Suppression{risk, pattern, reason}` node SUPPRESSES the
  finding pattern; `defer` adds `expires` (default +90d); `accept` records an
  acknowledgement; `skip` no-ops.
- **Scan-time matching**: on the next run, a finding matching a live `Suppression`
  (risk + file glob) is downgraded to `info` and shown under a collapsed
  "Suppressed" section — not counted in the score. An **expired** suppression is
  ignored (finding resurfaces at original severity) and the Summary notes "N
  suppressed findings expired and are active again" (brooks `common.md` behaviour,
  now a graph query: `Suppression` where `expires < now`).
- Interactive triage (the one-finding-at-a-time prompt) is the **Post-Report
  Triage** phase of the mode skill (355), guarded to interactive sessions only
  (skip in CI/headless — brooks' guard). The state it writes is the same
  `Suppression` nodes, so CI and interactive share one model.

> **Tension resolved — suppression is keep-both, not delete (Spec 292).** A
> suppressed finding is still *recorded* (the run produced it); the `Suppression`
> only changes its *tier* on read. History never lies about what was found — the
> finding node persists, the suppression is a separate, expiring overlay. This is
> the bi-temporal keep-both discipline applied to triage.

### What this slice does NOT do

- No report rendering / SARIF (357) — it computes the score + the suppressed set;
  357 renders them.
- No new findings — it scores/filters the findings 354/355 produce.
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
  Given I dismiss an R3 finding in src/util.py with a reason
  When the same review runs again
  Then the finding is downgraded to info under a collapsed Suppressed section
  And a Suppression node records the risk, pattern, and reason
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
  `Acknowledgement` node — the provenance is cheap and useful.)

## Followup — Implementation Status (2026-06-20)

**DRAFTED 2026-06-20** — the scoring/config/triage slice of the Spec 353 program.
No code yet. Reuses Spec 334 (unified config), Spec 290 (`manage.timeline` for
trend), Spec 336/292 (keep-both, no sidecar files). Depends on 354 (the `tier`
mapping + finding shape). Next (after 354): `_score.py` + `score-presets.json` +
the `quality:` config block + `QualityRun`/`Suppression` nodes + `analyze.triage`,
RED→GREEN.
