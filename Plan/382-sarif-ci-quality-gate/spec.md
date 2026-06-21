---
spec_id: "382"
slug: sarif-ci-quality-gate
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 6]
depends_on: ["379", "360", "381", "292"]
domain: analyze
wave: brooks-port
parent_spec: "379"
---

# Spec 382 — SARIF emit + CI step + the quality gate + report rendering

> Part of the Spec 379 brooks-lint port. This slice ports brooks-lint's
> **machine-facing output** — SARIF for code-scanning, a CI step that reviews the
> diff and gates the PR, and the Iron Law report rendering — onto agency's `gate`
> + `document.render` + the existing `test.yml` workflow.

## Why

brooks-lint's value in CI is three things: it emits **SARIF** (`sarif.mjs`) so
findings show up in GitHub code-scanning; it **gates** a PR on severity
(`ci-gate.mjs`); and it renders the **Iron Law report** (the markdown a human
reads). Agency already has the substrate for all three — the `gate` capability
(records a `Gate` node, PASSED/BLOCKED_ON edges; codegraph: gate/_main.py:24),
`document.render` (graph→file, Spec 292), and `.github/workflows/test.yml` — so
this is wiring, not new machinery.

One brooks plumbing module is **intentionally dropped**: `report-parse.mjs`. It
exists only because brooks' findings live in prose that must be parsed back into
structure for SARIF. Agency findings are **born structured** as `Finding` graph
nodes (Spec 360), so SARIF renders straight from the graph — there is nothing to
parse. (The brooks parser-fidelity benchmark therefore becomes a SARIF-validity
property test, Spec 383 — not a parser test.)

## Design

### 1. SARIF emit — straight from structured findings

`agency/capabilities/analyze/_sarif.py` + a verb:

```python
@verb(role="transform")
def sarif(self, findings: list = None, run_id: str = "") -> dict:
    """Render recorded Findings as SARIF 2.1.0 for code-scanning upload.

    Inputs: findings (list — or '' to pull the QualityRun's findings by run_id).
    Returns: {sarif: {...}, rule_count, result_count} (the SARIF doc; full text
             also written to an Artefact per Spec 292/336).
    chain_next: upload to GitHub code-scanning in CI (§3).
    """
```

The SARIF mapping is mechanical (no parsing):

- **`rules`** ← the live risk-code registry (Spec 360 `decay-risks.json` + any
  `Cx`): one `reportingDescriptor` per risk, `id=R1…`, `name`, `shortDescription`
  = diagnostic question, `helpUri` → the source-coverage doc (383), `properties`
  carry the book sources. The rule set is **derived from the live registry**, not
  a literal list — so it never drifts (rule 8; tested in 383).
- **`results`** ← each `Finding`: `ruleId=risk_code`, `level` from the derived
  `tier` (`critical→error, warning→warning, suggestion→note`), `message.text` =
  the Iron Law (Symptom + Consequence + Remedy joined), `locations` from
  file/line, `partialFingerprints` from the rule+file+symptom (stable across runs
  so code-scanning dedups). Decidable-only findings (empty `risk_code`, Spec 360)
  map to their `rule` id under a `analyze.*` tool component.

### 2. The quality gate — score/severity threshold via `gate`

`develop.review` / `analyze.review` (380) end by recording a gate:

```
gate.check(lifecycle_id, name="quality:<mode>",
           passed = score >= min_score AND critical_count <= max_critical,
           evidence = "score 72 (min 70); 0 critical (max 0)")
```

Thresholds are config (`quality.gate.min_score`, `quality.gate.max_critical` —
Spec 381), documented tunable budgets (rule 8). A failed gate flips the lifecycle
`input-required` (the existing `gate` behaviour, codegraph: gate/_main.py:52-57) →
in CI a new **`gate.assert(name)`** reader verb (OQ2) reads the latest `Gate` and
exits non-zero on `BLOCKED_ON`; interactively it pauses for a confirm override. A
wedged PR (false-positive critical, `max_critical=0`, no interactive confirm) has
a documented bypass — a `quality-override` label or a config threshold bump —
recorded as `Gate{overridden_by}` (§3, Nygard). The gate outcome is **auditable
provenance** (a `Gate` node), which brooks' `ci-gate.mjs` exit code was not.

### 3. CI step — review the diff, emit SARIF, gate the PR

A job in `.github/workflows/test.yml` (or a sibling `quality.yml`), mirroring
brooks' GitHub Action + agency's existing CI shape. **The CI entry is
`analyze.review` — the headless twin (380 §3a)** — never `develop.review`, because
the CI actor must not pause (Cockburn):

```yaml
quality:
  permissions: { security-events: write, contents: read }   # SARIF upload needs this
  steps:
    - uses: actions/cache@v4                 # persist the graph for trend (Hightower)
      with: { path: .agency, key: agency-quality-${{ github.base_ref }} }
    - run: agency analyze review --mode review --scope diff --ci   # headless; never blocks
    - run: agency analyze sarif --review $REVIEW_ID --max-results 5000 > quality.sarif
    - uses: github/codeql-action/upload-sarif@v3
      with: { sarif_file: quality.sarif }
    - run: agency gate assert --name "quality:review"   # non-zero iff BLOCKED_ON
```

- **Runs on PRs** (incremental, `--scope diff`) — fast, per CLAUDE.md rule 7.
- **LLM credential + graceful degradation (Hightower fix).** The judgment pass
  needs an LLM key (openrouter/anthropic). When the secret is present, CI runs the
  full hybrid; **when absent, `analyze.review` degrades to decidable-only** (free,
  keyless, every fork/PR still gets the mechanical findings) and the report notes
  `judgment: skipped (no LLM key)`. The decidable gate still runs. No silent
  full-pass-that-was-actually-empty.
- **Trend in ephemeral CI (Hightower fix).** The graph DB is otherwise fresh each
  run, so the 381 `QualityRun` trend would always read "first run". The job
  **caches `.agency/` keyed by the base branch** so prior `QualityRun` nodes
  survive across CI runs; on a cache miss the report says "first run" (honest
  fallback, not a broken feature).
- **SARIF size cap (Nygard fix).** GitHub caps code-scanning SARIF (~10MB / 25k
  results). `analyze.sarif --max-results N` paginates/caps and emits a truncation
  **locator** (CLAUDE.md #9 — count + "N of M shown", never a silent drop); the
  full finding set stays in the graph.
- **Stuck-PR override (Nygard fix).** A false-positive critical with
  `max_critical=0` would wedge the PR with no interactive confirm available. The
  gate honours a documented bypass: a `quality-override` PR label OR a config
  `quality.gate.max_critical` bump, recorded as `Gate{overridden_by}` provenance.
- The gate step fails the check iff the quality gate is `BLOCKED_ON`.
- The agency self-hosted-install drift check (existing) is unaffected.

> **Tension resolved — incremental in CI, full on demand.** PR CI reviews only
> the diff (`--scope diff`) so it is cheap and unblocking; a scheduled/whole-repo
> `audit`/`health` run (`--scope repo`) is a separate, slower job (or a manual
> dispatch), exactly as brooks separates PR Review from Architecture Audit.

> **Failure mode — a partial walk never reports green (Nygard fix).** If the
> judgment pass crashes/times out mid-walk, the run records
> `QualityRun{status: incomplete}` and the gate step **does not emit a pass
> verdict** (exit non-zero with "review incomplete"), so a crashed review can never
> masquerade as a clean one.

### 4. Report rendering — the Iron Law template via `document.render`

The human-readable report is rendered graph→file (Spec 292 `document.render`),
porting brooks' `common.md` Report Template. **The template FILE itself
(`analyze/templates/quality-report.md` + `iron-law-finding.md`) is authored in
Spec 384** (the prose port); this slice owns the *render path* that projects it
from the graph. The template carries these as `<!-- AGENT: -->` blocks:

- Header: `Mode · Scope · Health Score [· Trend]` (trend from 381's `QualityRun`).
- `Config:` line when a config was applied (preset, N disabled, M ignored).
- **Findings** sorted by tier (critical→warning→suggestion), each as the Iron Law
  block (`Symptom / Source / Consequence / Remedy`); empty tiers omitted.
- **Module Dependency Graph** (mermaid) — audit mode only (R5).
- **Summary** — 2–3 sentences; under `legacy-friendly`, lead with the three
  highest-leverage fixes (Spec 381 §1).
- A collapsed **Suppressed** section (Spec 381 §4) when suppressions matched.
- **Language rule** (brooks `common.md`): render finding prose in the user's
  language; keep Iron Law labels, book titles, and structural headers in English.

The report is an `Artefact` (PRODUCES edge) and can round-trip back via
`document.sync` (Spec 292) — so an edited report is not lost.

### What this slice does NOT do

- No `report-parse` port (dropped — findings born structured).
- No score math (381) / no finding production (360/380) — it renders + gates them.
- No new severity vocabulary — SARIF `level` derives from `tier` (360 §1).
- No mandatory CI block on suggestions — the gate is score + critical-count only,
  configurable.

## Acceptance (Gherkin)

```gherkin
Scenario: SARIF renders from structured findings without parsing
  Given recorded Findings including an R5 import-cycle finding
  When I call analyze.sarif
  Then the SARIF is valid 2.1.0
  And it has one rule per live risk code (count derived from the registry)
  And the R5 result's level is "error" and message carries Symptom+Consequence+Remedy

Scenario: the quality gate blocks below threshold, with provenance
  Given a review scoring 60 with min_score 70
  When the review's gate runs
  Then a Gate node records passed=false with the score evidence
  And the lifecycle is input-required (CI: non-zero exit)

Scenario: the CI step uploads SARIF and gates the PR
  Given a PR diff with a critical finding and max_critical 0
  When the quality CI job runs
  Then quality.sarif is uploaded to code-scanning
  And the gate step exits non-zero

Scenario: the report renders the Iron Law template
  When the report is rendered for an audit run
  Then findings are sorted critical→warning→suggestion
  And each finding shows Symptom/Source/Consequence/Remedy
  And a mermaid Module Dependency Graph is present (audit mode only)

Scenario: the SARIF rule set cannot drift
  Then the SARIF rule ids equal the live risk-code registry set
  And adding a custom Cx risk adds exactly one SARIF rule, with no code edit

Scenario: CI degrades to decidable-only without an LLM key
  Given the quality CI job runs with no LLM secret configured
  When analyze.review --ci runs
  Then decidable findings are still produced and the decidable gate runs
  And the report notes "judgment: skipped (no LLM key)"
  And the job does not report a full clean pass it did not perform

Scenario: trend survives ephemeral CI via the graph cache
  Given the .agency graph cache restored a prior QualityRun for this base branch
  When a new CI review runs
  Then the report Trend line shows the delta from the cached prior run
  And a cache miss falls back to "first run" (not a crash)

Scenario: SARIF is capped with a truncation locator, never silently dropped
  Given a whole-repo audit producing 40000 findings
  When analyze.sarif --max-results 5000 renders
  Then at most 5000 results are emitted
  And the SARIF reports "5000 of 40000 shown" and the full set stays in the graph

Scenario: a false-positive critical can be overridden in CI
  Given a blocked gate and a quality-override PR label
  When the gate step runs
  Then the gate passes and records Gate{overridden_by: "label:quality-override"}

Scenario: a partial walk never reports green
  Given the judgment pass crashes after 3 of 8 risks
  Then QualityRun.status is "incomplete"
  And the gate step exits non-zero with "review incomplete"
```

## Open questions (resolved 2026-06-20 — spec-panel)

- **OQ1 — RESOLVED:** a job in `test.yml` for PRs (`--scope diff`) + a separate
  scheduled `quality-audit.yml` for whole-repo (`--scope repo`). The diff job is
  keyless-capable (decidable-only) so forks aren't blocked on a secret.
- **OQ2 — RESOLVED:** add the thin `gate.assert(name)` reader verb (reusable
  beyond quality) — it reads the latest `Gate` for the name and exits non-zero on
  `BLOCKED_ON`. Cleaner than a `--ci` exit baked into `analyze.review`.

## Followup — Implementation Status (2026-06-20)

**DRAFTED 2026-06-20** — the CI/output slice of the Spec 379 program. No code yet.
Reuses `gate` (codegraph: gate/_main.py:24/52), `document.render` (Spec 292), the
CLI mirror (Spec 079), and `test.yml`. Depends on 360 (findings) + 381 (score).
Port-forward: `report-parse.mjs` dropped (findings born structured).

**Amended 2026-06-20 (spec-panel critique — the operational axis was the weakest at
5.5/10; this is the hardening pass).** CI entry is the headless `analyze.review`
twin (380 §3a), never the interactive `develop.review` (Cockburn). Added:
keyless decidable-only degradation when no LLM secret (Hightower); `.agency` graph
cache keyed by base branch so the 381 trend survives ephemeral CI (Hightower);
`security-events: write` permissions; `analyze.sarif --max-results` cap with a
truncation locator (Nygard); a `quality-override` label / threshold-bump bypass
for a wedged PR, recorded as `Gate{overridden_by}` (Nygard); a partial-walk
`QualityRun{status: incomplete}` that never reports green (Nygard). OQ1/OQ2
resolved (job-in-`test.yml` + scheduled `quality-audit.yml`; thin `gate.assert`
reader verb). Next (after 360/381): `_sarif.py` + `analyze.sarif` (+ `--max-results`)
+ `gate.assert` + the CI job + the report template, RED→GREEN.

**Slice 1 SHIPPED 2026-06-21 (TDD) — the SARIF emit (§1).** `analyze/_sarif.py`
(pure `to_sarif(findings, risks, max_results)` → SARIF 2.1.0: `rules` DERIVED
one-per-risk from the live `decay-risks.json` registry [never pinned — rule 8],
`level` from the tier [critical→error/warning→warning/suggestion→note], `message`
= the Iron Law [Symptom + Consequence + Remedy], `partialFingerprints` stable for
code-scanning dedup) + `analyze.sarif(findings, max_results)` (role=`transform`;
`max_results` caps with a `properties.truncated` "N of M shown" locator — never a
silent drop, #9; full set stays in the graph). No parsing — findings born
structured (Spec 360); brooks' `report-parse.mjs` stays dropped. **3 Gherkin
scenarios** (`tests/acceptance/features/quality_sarif.feature`): valid-2.1.0 +
level + Iron-Law message, rule-set-derived-from-registry, truncation locator. 91
green across the analyze slice; install regen + check-drift + doc-drift clean.
**Still (Slice 2+):** the quality gate (score/critical threshold via `gate` +
`gate.assert` reader verb, §2), the CI job (§3), and the report render path (§4,
template authored in 384).
