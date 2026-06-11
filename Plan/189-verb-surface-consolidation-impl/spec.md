---
spec_id: "189"
slug: verb-surface-consolidation-impl
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "070"
depends_on: ["070", "067", "182", "149"]
vision_goals: [1, 4]
affects:
  - agency/capabilities/
  - tests/test_verb_consolidation.py
---

# Spec 189 — verb-surface consolidation implementation

## Why

Spec 070 (verb-surface-consolidation) is WARN-accepted / "optional
future" in the token-economy cluster — the lint flags redundant verbs
but no consolidation shipped. As the enhancement waves add verbs
(AnthropicDriver consumers, judge axes, opportunity detectors), the
surface grows; periodic consolidation keeps discovery cheap (Goal 1).
This spec runs the consolidation the 070 lint recommends, derived from
the live duplicate-verb report.

## Done When

- [ ] **The 070 lint's redundant-verb report drives a consolidation
      pass** — near-duplicate verbs alias-and-deprecate to one
      canonical (never a hard break). The report is a typed
      `ConsolidationCandidate{canonical:str, duplicates:list[str],
      call_frequency:int, semantic_overlap:float, evidence_intents:
      list[str]}` per candidate cluster.
- [ ] **The consolidation is derived** (Spec 149) — the report ranks
      candidates by `score = call_frequency * semantic_overlap` read
      from the live graph (Invocation count) and the live verb
      docstrings. No hand-pinned candidate list.
- [ ] **Aliases preserve the wire contract** (Goal 5): the deprecated
      name resolves to the canonical handler (identity, not equality);
      `tools/list` still carries both for one deprecation window;
      removal happens only after one full cycle of zero calls to the
      deprecated name.
- [ ] **Cluster-coherence (Spec 182) re-checked** post-consolidation —
      the canonical verb must land in the same cluster as the
      duplicates it absorbed; otherwise reject the consolidation.
- [ ] **Discovery token count drops** measurably (rule 8 relationship):
      `tokens(discovery_after) < tokens(discovery_before)` AND the
      drop is at least the sum of the absorbed-verb tokens.
- [ ] **Failure-mode coverage** for premature aliasing, cluster
      drift, and silent semantic divergence (see below).
- [ ] Test: a duplicate-verb fixture consolidates; the alias still
      resolves to the same handler object; cluster map stays coherent;
      discovery payload shrinks measurably.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  the 070 lint reports {canonical: "analyze.graph", duplicates:
        ["analyze.census", "analyze.inventory"], call_frequency: 47,
        semantic_overlap: 0.91, evidence_intents: ["intent:..."]}
        AND a human reviewer accepts the candidate
When:   the consolidation pass runs
Then:   call_tool("analyze_census", {...}) resolves to the same handler
        object as call_tool("analyze_graph", {...}) (identity check);
        tools/list contains both for the deprecation window; the cluster
        map (Spec 182) places all three in the analyze cluster; and
        discovery payload tokens drop by at least the tokens of the two
        absorbed verb names

Given:  a candidate where the canonical and duplicate live in DIFFERENT
        clusters per Spec 182
When:   the consolidation pass evaluates the candidate
Then:   the candidate is rejected with reason "cluster_divergence", no
        alias is created, the lint continues to WARN
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Semantic divergence | "duplicates" have subtly different params | param-signature comparison in the report | reject candidate unless signatures are subset-compatible |
| Cluster drift | absorbed verb belonged to a different cluster | post-consolidation Spec 182 re-check | reject; the lint stays WARN |
| Premature deprecation | deprecated name removed while still called | call-frequency probe over deprecation window | removal blocked until window of zero calls observed |
| Surface re-growth | a later spec adds a new verb that re-creates the duplicate | the 070 lint re-fires | re-run consolidation; the cycle is permanent |
| Auto-alias error | machine consolidates without human review | gate: human-confirm required | the report PROPOSES; the alias_and_deprecate writes only on confirm |

## Interconnects

- Spec 067 (lint pipeline) supplies the redundancy report.
- Spec 182 (cluster audit) validates the result.
- **Drift-derivation chain** (149).
- Spec 184 (codemode bare alias) is the sibling discovery-cost win;
  this trims the verb set, that trims the prefix.
- Spec 188 (tiered-discovery drill) gets a smaller per-capability
  verb list to expand.
- Spec 187 (output lints) gates the new aliases against prefix drift.
- Spec 190 (skill surface reconciliation) is the parallel discipline
  on the skill side.

## Open questions

1. Auto-alias or human-confirm each? **Recommend**: human-confirm v1
   (consolidation is judgement); the report proposes, a person accepts.
   Revisit after one full cycle of green consolidations.
2. Deprecation window length? **Recommend**: one full Spec cycle
   (release-to-release) of zero calls to the deprecated name before
   removal — call-frequency-driven, not time-driven.
3. What about cross-capability duplicates (e.g. `analyze.search` vs
   `research.search`)? **Recommend**: out of scope — those are
   namespace decisions, not redundancies; defer to Spec 182.
