---
spec_id: "180"
slug: research-managed-agent-fanout
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "044"
depends_on: ["044", "147", "168", "040"]
vision_goals: [8, 1]
affects:
  - agency/capabilities/research/_main.py
  - tests/test_research_managed_agent.py
---

# Spec 180 — research Managed-Agent fan-out (harness-in-harness)

## Why

Spec 044 ships lead + specialist + verify with 3 specialist roles, all
running in-process. Goal 8 (harness-in-harness) and the `claude-api`
Managed-Agents surface let a research fan-out dispatch each specialist
to a SEPARATE Managed-Agent session whose tools execute on Anthropic
sandboxes and whose events stream back — the same dispatch-decision
heuristic (Spec 040) that governs subagent/Jules dispatch now governs
the Managed-Agent path.

## Done When

- [ ] **`research.lead(..., driver="managed-agent")`** dispatches each
      specialist as a Managed-Agent session (Spec 147 `dispatch_session`),
      per the create-once-Agent doctrine; events stream back as
      `MonitorEvent`s (Spec 021) and a typed shape is returned:
      ```python
      FanOutResult = {
        "driver":           Literal["in_process", "managed_agent"],
        "specialists":      list[SpecialistRun],   # one per role
        "citations":        list[Citation],        # merged set
        "dispatch_reason":  str,                   # which Spec 040 signals fired
        "monitor_events":   list[MonitorEvent],    # streamed back
        "usage_total":      Usage,                 # aggregated across sessions
      }
      SpecialistRun = {
        "role":           str,
        "session_id":     str | None,              # None for in-process
        "citation_count": int,
        "status":         Literal["ok","partial","skipped","failed"],
        "duration_ms":    int,
      }
      ```
- [ ] **Invariant — heuristic determines driver.** The dispatch-decision
      heuristic (Spec 040) gates it; an assertion verifies
      `driver=="managed_agent"` iff the 11-signal rule scored ≥ 1
      positive AND no disqualifier fired. The `dispatch_reason` string
      enumerates the fired signals.
- [ ] **Invariant — Citation parity.** Citations emitted via the
      managed-agent path are SCHEMA-IDENTICAL to in-process Citations
      (same node label, same edge set, same required properties); a
      property-based test asserts the two streams round-trip through
      `analyze.graph` with byte-identical typed shapes.
- [ ] **Invariant — provenance preserved.** Every specialist run
      produces a `SubagentSession` node with SERVES edge to the parent
      Intent and PRODUCES edges to its Citation nodes (Spec 048
      PARENT_INTENT chain intact across the harness boundary).
- [ ] **In-process path unchanged** (Spec 044 default — assert
      byte-identical Citation set on a frozen fixture with both
      drivers given the same seed).
- [ ] **Fetched bodies honor the output budget** (Spec 146/154) — the
      aggregated `usage_total.output_tokens ≤ output_budget_tokens`;
      overflow triggers Spec 154 recall.
- [ ] **Degrades cleanly** without `[anthropic]` (driver forced to
      `in_process`, no error; `dispatch_reason="no_managed_agent_extra"`).
- [ ] Test: a fan-out dispatches N sessions (mocked), collects N
      Citation sets; the heuristic chooses in-process below threshold.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a research question with 4 specialist roles, estimated return
        tokens ≈ 12000, 6 unfamiliar files per role
When:   research.lead(question=..., driver="managed-agent")
Then:   returns FanOutResult{
            driver: "managed_agent",
            specialists: [4 SpecialistRun entries, each status="ok"],
            citations: [merged set, 18 entries],
            dispatch_reason: "S1(return_tokens>=5000), S2(unfamiliar>=4)",
            usage_total: Usage{input_tokens: 9200, output_tokens: 11800}
        }
        AND every Citation has identical schema to in-process driver
        AND every SpecialistRun produces a SubagentSession node SERVES the parent Intent
        AND a parallel call with driver="in_process" on the same fixture
            yields a Citation set with the same node ids
```

## Failure modes (Nygard)

| Failure | Fan-out response |
|---|---|
| `DriverError.RATE_LIMITED` on one specialist | retry with backoff (Spec 147); mark `SpecialistRun.status="partial"`; other specialists unaffected |
| `DriverError.SESSION_LOST` mid-stream | resume via `session_id` per claude-api skill; if unrecoverable, status `failed`, citations from that role dropped |
| Heuristic mis-routes (over-dispatches small task) | post-run reflection records the cost; Spec 150 amendment proposal raises the threshold |
| Citation schema drift across drivers | typed `Codes.CITATION_SHAPE_DRIFT`; in-process result wins; managed-agent stream quarantined |
| Output budget exceeded | per Spec 154, recall the longest bodies and reference by node id; if still over, return `Codes.OUTPUT_OVER_BUDGET` |
| Missing `[anthropic]` extra | driver forced to `in_process`; no error; `dispatch_reason` records the downgrade |

## Interconnects

- **LLM-driver chain** (147) — the Managed-Agents bridge and `Usage` envelope.
- **Output-budget chain** (146/154) — fetched bodies + recall.
- Spec 040 (dispatch-decision) governs the driver choice — the
  11-signal rule is the single oracle.
- Spec 168 (web depth) is the per-specialist tool surface.
- Spec 048 (PARENT_INTENT) — every dispatched session SERVES the
  parent Intent; the chain crosses the harness boundary.
- Spec 179 (document-render LLM narrative) is the downstream
  consumer that renders the Citations this spec produces.
- Spec 178 (analyze judge axis) shares the driver-error vocabulary
  and the `Usage` envelope contract.
- Spec 183 (intent-chain opportunity detector) consumes the
  fan-out Invocation chains as candidate sequences.

## Open questions

1. **One Agent per role or one shared?** **Recommend**: one persisted Agent
   per specialist role (create-once, version-pinned, claude-api skill);
   sessions are per fan-out — keeps system prompts cache-stable (Spec 146).
2. **Citation deduplication strategy?** **Recommend**: dedupe by
   `(url, claim_span_hash)` post-merge; preserve all SpecialistRun
   provenance edges to the surviving Citation node (no dropped lineage).
3. **Heuristic re-evaluation cadence?** **Recommend**: evaluate ONCE at
   `research.lead` entry; do not re-route mid-flight (cost + provenance
   complexity outweighs adaptivity). Slice-2 may add a per-specialist
   re-check if measured mis-routing exceeds 10%.
