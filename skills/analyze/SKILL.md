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

Analyze runs decidable transforms over source and reports findings on the quality, security, performance, and architecture axes as graph nodes the orchestrator can reason about, rather than prose opinions.

## When to use

- Unsure whether a change is safe to ship
- Suspected security or performance regressions in a diff
- A codebase area that feels risky or unfamiliar before review

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `architecture` | transform | Dependency-graph + structural checks: import cycles, file LOC thresholds. | [details](references/architecture.md) |
| `cleanup` | act | Focused mode: analyse for dead-code findings only, draft a patch plan. | [details](references/cleanup.md) |
| `graph` | transform | Query the provenance graph — a census of node types + a typed listing (read the graph). | [details](references/graph.md) |
| `improve` | act | Read prior Analysis findings, draft an improvement plan as a Reflection. | [details](references/improve.md) |
| `paths` | transform | Spec 048 intent-path analysis: long chains + verb sequences. | [details](references/paths.md) |
| `performance` | transform | AST-based hot-path lint: nested O(n²), += in loop, unbounded while True. | [details](references/performance.md) |
| `quality` | transform | Decidable lint findings: unused imports, long lines, long functions, long files. | [details](references/quality.md) |
| `run` | act | Run the requested analysis axes and record an Analysis + per-Finding nodes. | [details](references/run.md) |
| `security` | transform | Decidable security patterns: eval/exec, hardcoded credentials, pickle.load, shell=True. | [details](references/security.md) |

## Example

```bash
await call_tool('capability_analyze_architecture', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Shipping a risky diff with no analysis → run capability_analyze_security first
- Hand-waving 'looks fine' on unfamiliar code → get findings via capability_analyze_quality

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`code-analysis`** (discipline): scope → axes → run → review → apply
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'code-analysis', 'inputs': {}, 'intent_id': '…'})`
