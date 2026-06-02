---
name: code-analysis
description: Use when about to assess a codebase (or part of one) for quality / security / performance / architecture issues, before requesting review or shipping — to run decidable transforms over the source and surface findings as graph artefacts the orchestrator can reason about.
allowed-tools:
  - mcp__plugin_agency_agency__execute
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
---

# Code analysis (4-axis decidable, with hard apply gate)

## When to use

- A PR is ready for review: run the analysis FIRST, share the
  graph-recorded findings instead of asking a reviewer to lint manually.
- Onboarding a new codebase: `analyze.architecture` surfaces cycles and
  file-LOC outliers in seconds.
- Before refactoring: `analyze.run` + `analyze.improve` give a
  prioritised plan from rule-id-grouped findings.
- "Tidy up the obviously dead": `analyze.cleanup` does the focused
  unused-import pass.

DON'T use this when:
- You want LLM judgement ("name is unclear") — that's not decidable;
  dispatch to a subagent via the skill's `review` phase instead.
- The codebase is non-Python (v1 only ships `lang="py"`).

## The chain (5 phases — walk `analyze.ontology.skills["code-analysis"]`)

```
1. scope         →  path, lang
2. axes          →  axes (default: all four)
3. run           →  analysis_id, totals
4. review        →  findings_summary
5. apply (hard)  →  applied  (gates improve / cleanup writes)
```

The hard gate at phase 5 is the agency-native answer to SC's "STOP
AFTER analysis" prompt-text discipline — apply NEVER runs without an
explicit gate-pass.

## The four axes

| Axis | What it checks | Rule prefix |
|---|---|---|
| `quality` | unused imports, long lines / functions / files | `Q*` |
| `security` | eval/exec, hardcoded credentials, pickle.load, shell=True | `S*` |
| `performance` | nested O(n²), `+=` in loop, unbounded `while True` | `P*` |
| `architecture` | import cycles, file LOC thresholds | `A*` |

NO LLM "may be vulnerable" judgements — see
[`references/improve-vs-cleanup.md`](references/improve-vs-cleanup.md)
for the doctrine.

## The Finding contract

Every axis emits the canonical Finding shape:

```python
{
    "rule": "S001",                          # stable across runs
    "severity": "info"|"warn"|"fail",        # pinned per rule-id
    "file": "agency/capabilities/x.py",
    "line": 42,                              # 1-indexed
    "message": "<= 120 chars",               # Spec 023 brief-budget
    "evidence": "<= 200 chars"               # source line (redacted for S002)
}
```

See [`references/finding-shape.md`](references/finding-shape.md) for
severity-assignment rules per axis.

## How to call

```python
# 1) Run all four axes; record findings in the graph.
r = await call_tool('capability_analyze_run', {
    'intent_id': iid, 'path': 'agency/', 'axes': None})  # default = all four
# r → {analysis_id, totals: {quality, security, performance, architecture}}

# 2) Draft an improvement plan.
p = await call_tool('capability_analyze_improve', {
    'intent_id': iid,
    'analysis_id': r['analysis_id'],
    'axes': ['quality', 'security']})    # only these axes
# p → {improvement_plan_id, item_count, summary}

# 3) Focused cleanup (dead-code only).
c = await call_tool('capability_analyze_cleanup', {
    'intent_id': iid, 'path': 'agency/', 'dry_run': True})
```

## Dispatch decision integration

For large repos (> 10 packages), the `axes` phase consults
`delegate.dispatch_decision` (Spec 040): S1 (return tokens) + S2 (file
count) typically fire → `analyze.architecture` dispatches to a local
subagent. Cache-warm sessions on the same tree see S10 fire and
inline-win instead.

See [`skills/dispatch-decision/SKILL.md`](../dispatch-decision/SKILL.md)
for the heuristic.

## References

- [`references/finding-shape.md`](references/finding-shape.md) — the
  finding contract + severity-assignment-per-axis table.
- [`references/improve-vs-cleanup.md`](references/improve-vs-cleanup.md)
  — when to use `analyze.improve` vs. `analyze.cleanup`.
