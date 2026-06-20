---
spec_id: "357"
slug: sarif-ci-quality-gate
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 6]
depends_on: ["353", "354", "356", "292"]
domain: analyze
wave: brooks-port
parent_spec: "353"
---

# Spec 357 — SARIF emit + CI step + the quality gate + report rendering

> Part of the Spec 353 brooks-lint port. This slice ports brooks-lint's
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
nodes (Spec 354), so SARIF renders straight from the graph — there is nothing to
parse. (The brooks parser-fidelity benchmark therefore becomes a SARIF-validity
property test, Spec 358 — not a parser test.)

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

- **`rules`** ← the live risk-code registry (Spec 354 `decay-risks.json` + any
  `Cx`): one `reportingDescriptor` per risk, `id=R1…`, `name`, `shortDescription`
  = diagnostic question, `helpUri` → the source-coverage doc (358), `properties`
  carry the book sources. The rule set is **derived from the live registry**, not
  a literal list — so it never drifts (rule 8; tested in 358).
- **`results`** ← each `Finding`: `ruleId=risk_code`, `level` from the derived
  `tier` (`critical→error, warning→warning, suggestion→note`), `message.text` =
  the Iron Law (Symptom + Consequence + Remedy joined), `locations` from
  file/line, `partialFingerprints` from the rule+file+symptom (stable across runs
  so code-scanning dedups). Decidable-only findings (empty `risk_code`, Spec 354)
  map to their `rule` id under a `analyze.*` tool component.

### 2. The quality gate — score/severity threshold via `gate`

`develop.review` / `analyze.review` (355) end by recording a gate:

```
gate.check(lifecycle_id, name="quality:<mode>",
           passed = score >= min_score AND critical_count <= max_critical,
           evidence = "score 72 (min 70); 0 critical (max 0)")
```

Thresholds are config (`quality.gate.min_score`, `quality.gate.max_critical` —
Spec 356), documented tunable budgets (rule 8). A failed gate flips the lifecycle
`input-required` (the existing `gate` behaviour, codegraph: gate/_main.py:52-57) →
in CI that is a non-zero exit (§3); interactively it pauses for a confirm
override. The gate outcome is **auditable provenance** (a `Gate` node), which
brooks' `ci-gate.mjs` exit code was not.

### 3. CI step — review the diff, emit SARIF, gate the PR

A job in `.github/workflows/test.yml` (or a sibling `quality.yml`), mirroring
brooks' GitHub Action + agency's existing CI shape:

```yaml
quality:
  steps:
    - run: agency develop review --mode review --scope diff   # CLI mirror (Spec 079)
    - run: agency analyze sarif > quality.sarif
    - uses: github/codeql-action/upload-sarif@v3
      with: { sarif_file: quality.sarif }
    - run: agency gate assert --name "quality:review"   # non-zero if BLOCKED_ON
```

- Runs on PRs (incremental, `--scope diff`) — fast, per CLAUDE.md rule 7's
  "focused slice locally / CI is the net" discipline.
- SARIF upload makes findings inline-annotate the PR (the code-scanning surface).
- The gate step fails the check if the quality gate is `BLOCKED_ON`.
- The agency self-hosted-install drift check (existing) is unaffected.

> **Tension resolved — incremental in CI, full on demand.** PR CI reviews only
> the diff (`--scope diff`) so it is cheap and unblocking; a scheduled/whole-repo
> `audit`/`health` run (`--scope repo`) is a separate, slower job (or a manual
> dispatch), exactly as brooks separates PR Review from Architecture Audit.

### 4. Report rendering — the Iron Law template via `document.render`

The human-readable report is rendered graph→file (Spec 292 `document.render`),
porting brooks' `common.md` Report Template. **The template FILE itself
(`analyze/templates/quality-report.md` + `iron-law-finding.md`) is authored in
Spec 359** (the prose port); this slice owns the *render path* that projects it
from the graph. The template carries these as `<!-- AGENT: -->` blocks:

- Header: `Mode · Scope · Health Score [· Trend]` (trend from 356's `QualityRun`).
- `Config:` line when a config was applied (preset, N disabled, M ignored).
- **Findings** sorted by tier (critical→warning→suggestion), each as the Iron Law
  block (`Symptom / Source / Consequence / Remedy`); empty tiers omitted.
- **Module Dependency Graph** (mermaid) — audit mode only (R5).
- **Summary** — 2–3 sentences; under `legacy-friendly`, lead with the three
  highest-leverage fixes (Spec 356 §1).
- A collapsed **Suppressed** section (Spec 356 §4) when suppressions matched.
- **Language rule** (brooks `common.md`): render finding prose in the user's
  language; keep Iron Law labels, book titles, and structural headers in English.

The report is an `Artefact` (PRODUCES edge) and can round-trip back via
`document.sync` (Spec 292) — so an edited report is not lost.

### What this slice does NOT do

- No `report-parse` port (dropped — findings born structured).
- No score math (356) / no finding production (354/355) — it renders + gates them.
- No new severity vocabulary — SARIF `level` derives from `tier` (354 §1).
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
```

## Open questions

- **OQ1** — one `quality.yml` workflow or a job inside `test.yml`? (Default: a job
  in `test.yml` for PRs + a separate scheduled `quality-audit.yml` for whole-repo.)
- **OQ2** — `agency gate assert` CLI verb: add it, or have `develop.review` exit
  non-zero directly in `--ci` mode? (Default: a thin `gate.assert` reader verb —
  reusable beyond quality.)

## Followup — Implementation Status (2026-06-20)

**DRAFTED 2026-06-20** — the CI/output slice of the Spec 353 program. No code yet.
Reuses `gate` (codegraph: gate/_main.py:24/52), `document.render` (Spec 292), the
CLI mirror (Spec 079), and `test.yml`. Depends on 354 (findings) + 356 (score).
Port-forward: `report-parse.mjs` dropped (findings born structured). Next (after
354/356): `_sarif.py` + `analyze.sarif` + the gate wiring + the CI job + the
report template, RED→GREEN.
