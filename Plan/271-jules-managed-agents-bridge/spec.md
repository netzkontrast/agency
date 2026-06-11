---
spec_id: "271"
slug: jules-managed-agents-bridge
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "012"
depends_on: ["012", "147", "180", "021"]
vision_goals: [3, 8]
affects:
  - agency/capabilities/jules/_main.py
  - tests/test_jules_managed_bridge.py
---

# Spec 271 — Jules ↔ Managed-Agents bridge

## Why

Spec 012 ships the full Jules v1alpha lifecycle (dispatch + watcher +
recovery). Per the `claude-api` skill, Managed-Agents is Anthropic's
in-house remote-agent surface — same shape as Jules (persisted agent,
session-based, event streams, COMPLETED ≠ done). The agent-uniform
Lifecycle promise (Goal 3) means both should plug into the same
substrate; the harness-in-harness ladder (Goal 8) means an agency walk
can dispatch to EITHER Jules or a Managed Agent.

## Done When

- [ ] **`jules.dispatch` and `agent.dispatch_session` share a base
      protocol** — same Lifecycle transitions, same SERVES edge, same
      verify-before-COMPLETED discipline.
- [ ] **A `delegate.dispatch_remote(driver=...)` chooser** routes to
      jules / managed-agent / future driver via the Spec 040 heuristic.
- [ ] **Events normalize as MonitorEvents** (Spec 021) regardless of
      driver — one stream, one watcher.
- [ ] **The watcher (Spec 012) handles both** sources transparently.
- [ ] Test: a dispatch routes to MA when 11-signal favors it; Jules
      otherwise; both record matching provenance shapes.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 147 (AnthropicDriver) provides MA session API.
- Spec 180 (research fan-out) is the first verb-level consumer.
- Spec 040 (dispatch-decision) governs the choice.
- **Agent-uniform Lifecycle** (Goal 3) closure.
