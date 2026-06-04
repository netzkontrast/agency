---
name: deep-research
description: Use when answering an open question that needs cited evidence from MULTIPLE sources (codebase + prior reflections + docs + optional web) — drives a research-question through lead → fan-out → verify → publish, recording every Citation as a graph node so the report survives the session.
allowed-tools:
  - mcp__plugin_agency_agency__execute
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
---

# Deep research (4-phase, hard publish gate)

## When to use

- "What does the codebase actually do about X?" — needs codebase
  citations AND prior-reflections context.
- "How have we approached Y before?" — needs cross-session reflection
  retrieval + corroboration from docs.
- "Is claim Z supported by the project?" — needs an ADVERSARIAL
  verifier pass before you trust the answer.

DON'T use when:
- The question is a single-file lookup (just `Read` it).
- You want LLM prose synthesis (this is composition + verification;
  document.render projects records, no prose generation).
- The question lives entirely outside the repo AND the web specialist
  isn't wired up (v1 ships no default web backend).

## The chain (4 phases — walk `research.ontology.skills["deep-research"]`)

```
1. plan      →  research_id, specialists      (research.lead)
2. fan-out   →  citations_recorded            (research.specialist × N)
3. verify    →  verification_status           (research.verify)
4. publish   →  published                     (HARD GATE)
```

The hard gate at phase 4 protects against publishing a research report
whose verifier returned `fail`. Override available with `force=True`
and an OVERRIDDEN_BY audit edge.

## The four specialist roles

| Role | What it does | Confidence rule |
|---|---|---|
| `codebase` | grep + AST walk over `agency/` | 1.0 (deterministic) |
| `prior-reflections` | `reflect.recall_semantic` over Reflection nodes | ranker score (0..1) |
| `doc-corpus` | walk `docs/` for keyword + semantic match | substring → 1.0, semantic → score |
| `web` | injected WebSearchClient (v1: none default) | 0.9 (URL + page text) |

See [`references/specialist-roles.md`](references/specialist-roles.md)
for the per-role detail.

## The verifier checks (v1)

| Check | What it does |
|---|---|
| `evidence-supports-claim` | substring OR semantic ≥ 0.5 |
| `contradiction-cluster` | same-topic citations with opposite polarity → warn |

`web-reachability` is reserved for v2 (HEAD URL + 2xx).

See [`references/verification-rules.md`](references/verification-rules.md)
for the threshold rationale.

## How to call

```python
# 1) Plan.
p = await call_tool('capability_research_lead', {
    'intent_id': iid,
    'question': 'how does dispatch_decision pick a driver?',
    'depth': 'standard'})
# p → {research_id, specialists, plan}

# 2) Fan out (one call per planned specialist).
for role in p['specialists']:
    r = await call_tool('capability_research_specialist', {
        'intent_id': iid,
        'research_id': p['research_id'],
        'role': role,
        'query': 'dispatch_decision driver selection'})

# 3) Verify.
v = await call_tool('capability_research_verify', {
    'intent_id': iid, 'research_id': p['research_id']})
# v → {ok, checks: {evidence-supports-claim, contradiction-cluster}}

# 4) Publish (walker-managed; HARD GATE).
```

## Dispatch decision integration

`research.lead` consults `delegate.dispatch_decision` (Spec 040) when
the depth's specialist set has ≥ 3 roles (S4:parallel fires).
`standard` depth is borderline; `deep` always dispatches.

## References

- [`references/specialist-roles.md`](references/specialist-roles.md) —
  per-role details + confidence-rule table.
- [`references/verification-rules.md`](references/verification-rules.md)
  — threshold rationale + the v2 web-reachability roadmap.
