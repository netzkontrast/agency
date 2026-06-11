---
spec_id: "188"
slug: tiered-discovery-llm-drill
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "068"
depends_on: ["068", "161", "146", "147"]
vision_goals: [1, 5]
affects:
  - agency/_discovery.py
  - tests/test_tiered_discovery_drill.py
---

# Spec 188 — tiered-discovery LLM-assisted drill

## Why

Spec 068 ships tiered discovery (−83% discovery tokens) — capability
tier first, drill into a capability for its verbs. The DRILL decision
(which capability to drill into) is currently the agent's job from the
one-line summaries. When the Spec 147 Driver is present, `search` can
suggest the most likely capability to drill into for a free-text query —
saving the round trip — while still never loading the full verb list
(Goal 1) and on a cache-stable prefix (Spec 146).

## Done When

- [ ] **`search(query, suggest_drill=True)`** returns a typed
      `TieredDiscoveryResult{tier:list[CapabilityBrief], suggested:
      DrillSuggestion|None, expanded_capability:str|None,
      expanded_verbs:list[VerbBrief], driver_used:bool}`. When the
      Driver runs, `suggested` is non-null; the verbs of ONLY the
      suggested capability appear in `expanded_verbs`.
- [ ] **The pre-expansion respects the budget** — exactly one
      capability's verbs, not all (Goal 1 preserved). Invariant:
      `len(expanded_verbs) == verbs_in(expanded_capability)` AND
      `tokens(result) <= tokens(tiered_baseline) + tokens(one_capability_drill)`.
- [ ] **Degrades to plain tiered discovery** without `[anthropic]` —
      `suggested = None`, `expanded_verbs = []`, the result shape stays
      identical so consumers don't branch.
- [ ] **The −83% baseline is not regressed** — measured (Spec 149)
      against the live registry, not re-pinned. Assertion: `tokens(
      suggest_drill_off) <= tokens(pre_068_baseline) * 0.20`.
- [ ] **Cache-stable** — the suggested-drill output goes in `body`,
      not `prefix` (Spec 146); the query-dependent suggestion must not
      interpolate into a cacheable prefix.
- [ ] **Mis-drill recovery** — when the suggestion is wrong, a second
      `search(query, drill_into=<other>)` call costs at most one extra
      capability drill (the agent is not punished for the suggestion).
- [ ] Test: a query drills into the right capability (mocked Driver);
      token count stays under the tiered baseline; a wrong-suggestion
      fixture recovers cleanly.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  the live registry with N capabilities and the [anthropic] extra installed
        AND a query "find files with regex"
When:   call mcp__agency__search(query="find files with regex", suggest_drill=True)
Then:   result.tier lists all N capabilities (one-line briefs);
        result.suggested.capability == "analyze" (the most likely);
        result.expanded_verbs lists analyze's verbs only;
        tokens(result) < tokens(full_verb_listing); AND
        result.driver_used == True

Given:  the same call but [anthropic] not installed
When:   the engine runs the search
Then:   result.suggested is None, result.expanded_verbs is [],
        result.tier still lists all capabilities, the consumer shape
        is identical — no branching required

Given:  the Driver suggested the wrong capability
When:   the agent calls search(query, drill_into="research") to override
Then:   exactly one additional capability drill cost is paid; no
        full-surface load happens
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Driver pre-expansion exceeds budget | suggested capability has >> N verbs | invariant test: `len(expanded_verbs) == verbs_in(cap)` | hard-cap; if a single cap exceeds budget, that's a Spec 189 consolidation flag |
| Query-bleed into prefix | suggestion text interpolated into cacheable prefix | Spec 146 prefix-stability probe | suggestion lives in body only |
| Driver hallucinates capability name | suggested name not in registry | resolver compares to live cap list | discard suggestion; fall back to plain tiered |
| Wrong suggestion silently misleads | agent trusts suggestion, drills into the wrong cap | second call to override is cheap (single drill) | document recovery path; do not auto-retry |
| API latency tax | Driver call adds round-trip time | timing probe on the Driver call | skip Driver when `latency_budget_ms` insufficient |

## Interconnects

- **LLM-driver chain** (147) · **output-budget chain** (146).
- Spec 161 (discovery rank) is the sibling LLM-assist.
- Spec 184 (codemode bare alias) further trims the prefix on top of
  this tier; the two compose.
- Spec 187 (output lints) gates that `suggested` lives in body, not
  prefix.
- Spec 149 (derived docs) measures the −83% baseline against the
  live registry.
- Spec 193 (capstone) exercises the suggested-drill path in its
  end-to-end cache-hit proof.

## Open questions

1. Pre-expand one capability or top-2? **Recommend**: one (the budget
   discipline); the agent drills further if wrong. Top-2 doubles the
   pre-expansion cost for marginal accuracy gain.
2. Cache the Driver's suggestion per (query, capability_set_hash)?
   **Recommend**: yes — same query against the same registry should
   not pay the Driver call twice. Cache key is the prefix hash.
3. What if the query is ambiguous (e.g. "search")? **Recommend**:
   `suggested = None, reason = "ambiguous"` — never guess; force the
   agent to refine.
