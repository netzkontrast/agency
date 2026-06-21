---
spec_id: "179"
slug: document-render-llm-narrative
status: draft
state: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "043"
depends_on: ["043", "147", "146", "154"]
vision_goals: [7, 1]
affects:
  - agency/capabilities/document/_main.py
  - tests/test_document_narrative.py
---

# Spec 179 — document.render narrative scope (composition + optional LLM)

## Why

Spec 043 ships `render` (4 graph→md scopes) + `explain` (composition,
not generation) + `index_repo` (94% token reduction). `explain` is
deliberately composition-only. But a `research-report` scope (named as
a Spec 044 v2 followup) and an audit-narrative scope want an optional
LLM pass that WEAVES the composed facts into prose — strictly on top of
the graph-derived skeleton (Goal 7: the graph is the store, prose is the
rendered view), never inventing facts.

## Done When

- [ ] **`document.render(scope="research-report", narrate=False)`**
      composes the graph skeleton (Citations, claims, evidence) and
      returns a typed shape:
      ```python
      RenderResult = {
        "skeleton":     str,            # composition-only markdown
        "narrated":     str | None,     # narrate=True path
        "coverage":     {
          "claim_count":         int,
          "covered_claim_count": int,   # claims traced to a node id
          "coverage_ratio":      float, # covered / total
          "uncovered":           list[str],  # claim spans flagged
        },
        "cache_prefix_tokens": int,     # Spec 146 stable prefix
        "driver_usage":  Usage | None,  # Spec 147 envelope when narrated
      }
      ```
- [ ] **Invariant — coverage floor.** When `narrate=True`,
      `coverage.coverage_ratio ≥ 0.95` on the fixture; below threshold
      the result returns `Result.failure(Codes.NARRATIVE_UNCOVERED)`
      with the uncovered spans listed.
- [ ] **Invariant — cache-stable prefix.** Across two consecutive
      `render` calls on the same graph, `usage.cache_read_input_tokens
      / usage.cache_creation_input_tokens > 0.5` on the second call
      (Spec 146).
- [ ] **Invariant — recall on large bodies.** When skeleton tokens >
      `output_budget_tokens`, the result references nodes by id and the
      narrated body materializes via Spec 154 recall — measured by
      `len(skeleton_tokens) + len(narrated_tokens) ≤ budget` post-recall.
- [ ] **Invariant — composition determinism.** `narrate=False` output
      is byte-identical across runs on a frozen fixture graph.
- [ ] **Degrades to composition-only** without `[anthropic]` (Spec 043
      behavior preserved; `narrated=None`, no error).
- [ ] Test: report renders from a fixture graph; every narrated claim
      maps to a node; composition-only fallback deterministic.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a research intent with 7 Citations + 12 Claim nodes in the graph
When:   document.render(scope="research-report",
                        intent_id="…",
                        narrate=True)
Then:   returns RenderResult{
            skeleton:  "# Findings\n\n## Claim 1 [n1]…",
            narrated:  "The evidence shows… [n1, n3] …",
            coverage:  {claim_count: 12, covered_claim_count: 12,
                        coverage_ratio: 1.0, uncovered: []}
        }
        AND every narrated claim cites at least one Claim node id
        AND coverage_ratio ≥ 0.95
        AND a second call within the cache TTL records
            usage.cache_read_input_tokens > 0
```

## Failure modes (Nygard)

| Failure | Render response |
|---|---|
| `DriverError.REFUSAL` | return skeleton only; `narrated=None`; emit Reflection(`scope="narrate-refusal"`) |
| `DriverError.RATE_LIMITED` | retry with backoff (Spec 147); on budget exhaustion fall back to skeleton |
| Coverage floor breach | typed `Codes.NARRATIVE_UNCOVERED`; uncovered spans listed — caller decides (re-render with stricter prompt, or accept skeleton) |
| Hallucinated noun-phrase | uncovered-claim list flags it; never auto-strip (preserve evidence for the dogfood loop) |
| Skeleton > output budget | recall via Spec 154; if still over, return `Codes.OUTPUT_OVER_BUDGET` |

## Interconnects

- **LLM-driver chain** (147) · **output-budget chain** (146/154).
- Spec 044 (research) is the first consumer (research-report scope).
- Spec 178 (analyze judge axis) shares the LLM-content tagging
  pattern; align vocabulary (`narrated` vs `judged`).
- Spec 180 (research managed-agent fan-out) produces the Citations
  this scope renders; the contract on Citation node shape is shared.
- Spec 183 (intent-chain opportunity detector) renders its proposals
  through this scope.
- Spec 149 (derived-doc discipline) is the broader doc-derivation
  invariant; narrate scopes must obey the same source markers.

## Open questions

1. **How to enforce "no invention"?** **Recommend**: post-render
   coverage check — every noun-phrase claim must trace to a composed
   node id; uncovered claims flag (not auto-strip). The 0.95 floor is
   the gate; 1.0 is aspirational.
2. **Per-scope prompt vendoring.** **Recommend**: vendored prompt
   templates at `agency/capabilities/document/_prompts/<scope>.md`
   reviewed alongside the scope's Done-When fixture.
3. **Re-narrate on graph change?** **Recommend**: keyed cache on
   `(intent_id, graph_snapshot_hash)`; a re-render hits cache when the
   skeleton is unchanged, regenerates otherwise.
