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
      `MonitorEvent`s (Spec 021) and Citations record identically.
- [ ] **The dispatch-decision heuristic (Spec 040) gates it** — only
      when the 11-signal rule favors out-of-process (return tokens ≥
      5000, ≥ 4 unfamiliar files, etc.).
- [ ] **In-process path unchanged** (Spec 044 default).
- [ ] **Fetched bodies honor the output budget** (Spec 146/154).
- [ ] Test: a fan-out dispatches N sessions (mocked), collects N
      Citation sets; the heuristic chooses in-process below threshold.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) — the Managed-Agents bridge.
- Spec 040 (dispatch-decision) governs the driver choice.
- Spec 168 (web depth) is the per-specialist tool surface.

## Open questions

1. One Agent per role or one shared? **Recommend**: one persisted Agent
   per specialist role (create-once, version-pinned, claude-api skill);
   sessions are per fan-out.
