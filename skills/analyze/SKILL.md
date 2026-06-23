---
name: analyze
description: "Use when assessing a codebase or diff for quality, security, performance, or architecture problems before review or shipping — surfaces decidable findings as graph artefacts."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# analyze capability

Analyze runs decidable transforms over source and reports findings on the quality, security, performance, and architecture axes as graph nodes the orchestrator can reason about, rather than prose opinions. Scope WHAT to analyze with codegraph first — `codegraph impact <symbol>` (blast radius of a change), `codegraph callers <symbol>` (every call site), `codegraph explore "<area>"` (understand an unfamiliar area) — before running the transforms, so the analysis follows the real dependency edges.

## When to use

- Unsure whether a change is safe to ship
- Suspected security or performance regressions in a diff
- A codebase area that feels risky or unfamiliar before review
- Scoping a risky change → `codegraph impact <symbol>` (blast radius) + `codegraph callers <symbol>` (call sites) before the analyzers

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `architecture` | transform | Dependency-graph + structural checks: import cycles, file LOC thresholds. | [details](references/architecture.md) |
| `cleanup` | act | Focused mode: analyse for dead-code findings only, draft a patch plan. | [details](references/cleanup.md) |
| `gate` | act | Record the quality gate verdict as an auditable Gate node (Spec 382 §2). | [details](references/gate.md) |
| `graph` | transform | Query the provenance graph — a census of node types + a typed listing (read the graph). | [details](references/graph.md) |
| `improve` | act | Read prior Analysis findings, draft an improvement plan as a Reflection. | [details](references/improve.md) |
| `migrate_quality_config` | effect | One-time importer: ``.brooks-lint.yaml`` → ``.agency/config.yaml quality:`` block + ``Suppression`` nodes (Spec 385 §1). | [details](references/migrate_quality_config.md) |
| `migrate_quality_history` | effect | One-time importer: ``.brooks-lint-history.json`` → back-dated ``QualityRun`` nodes (Spec 385 §2). | [details](references/migrate_quality_history.md) |
| `paths` | transform | Spec 048 intent-path analysis: long chains + verb sequences. | [details](references/paths.md) |
| `performance` | transform | AST-based hot-path lint: nested O(n²), += in loop, unbounded while True. | [details](references/performance.md) |
| `quality` | transform | Decidable lint findings: unused imports, long lines, long functions, long files. | [details](references/quality.md) |
| `record_run` | act | Record a QualityRun history node + return the trend (Spec 381 §3). | [details](references/record_run.md) |
| `report` | effect | Render the Iron-Law quality report from the ported templates + persist it as a round-trippable Document (Spec 384 close-out / 382 §4). | [details](references/report.md) |
| `review` | act | Headless code-quality review for CI — never pauses; risky remedies auto-declined. | [details](references/review.md) |
| `run` | act | Run the requested analysis axes and record an Analysis + per-Finding nodes. | [details](references/run.md) |
| `sarif` | transform | Render Findings as SARIF 2.1.0 for code-scanning — READ-ONLY (Spec 382 §1). | [details](references/sarif.md) |
| `score` | transform | Compute the Health Score (Spec 381) from findings × preset/config — READ-ONLY. | [details](references/score.md) |
| `security` | transform | Decidable security patterns: eval/exec, hardcoded credentials, pickle.load, shell=True. | [details](references/security.md) |

## Example

```bash
await call_tool('capability_analyze_architecture', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Shipping a risky diff with no analysis → run capability_analyze_security first
- Hand-waving 'looks fine' on unfamiliar code → get findings via capability_analyze_quality
- Guessing a change's blast radius → `codegraph impact <symbol>` gives it directly from the call graph

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`code-analysis`** (discipline): scope → axes → run → review → apply
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'code-analysis', 'inputs': {}, 'intent_id': '…'})`
  1. **scope** — Fix the path + language under analysis.
     Name the file/dir to analyse and its language. A scoped target keeps the run fast and the findings relevant.
  2. **axes** — Choose the quality axes to run.
     Pick the axes that matter for this target — quality, security, performance, architecture. Don't run every axis by reflex; match them to the risk.
  3. **run** — Run the decidable analyzers over the scope.
     Execute the chosen axes; collect the decidable findings + totals as a recorded Analysis (rule-based, reproducible — not opinion).
  4. **review** — Triage the findings into a summary.
     Group the findings by severity; separate the decidable (must-fix) from the advisory. Lead the summary with what blocks shipping.
  5. **apply** — Apply the safe fixes; gate the risky ones.
     Apply the low-risk remediations; leave risky ones flagged for human review. Confirm this gate only after re-running the analyzers to show the fixes held.
