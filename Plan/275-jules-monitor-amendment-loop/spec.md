---
spec_id: "275"
slug: jules-monitor-amendment-loop
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "022"
depends_on: ["022", "150", "274", "271"]
vision_goals: [6, 8]
affects:
  - agency/capabilities/jules/_main.py
  - tests/test_jules_amendment_loop.py
---

# Spec 275 — Jules monitor → amendment loop

## Why

Spec 022 makes Jules the first consumer of the monitor channel
(dispatched/recovery_started/silent_fail_detected events). These
events are exactly the kind of recurring pattern the dogfood
classifier (Spec 150) should mine: a Jules verb that silent-fails N
times across intents IS an amendment proposal ("flag the verify
window", "swap the recovery default"). This closes the loop on remote-
agent operations.

## Done When

- [ ] **Jules MonitorEvents feed Spec 150** as a `proposal` source —
      recurring silent-fail patterns yield amendment proposals.
- [ ] **Bridges across drivers** (Spec 271 Jules ↔ MA bridge) —
      patterns apply regardless of remote driver.
- [ ] **Structured monitor (Spec 274) is the query backend.**
- [ ] **Loop quality measured** via Spec 258.
- [ ] Test: 3× silent-fail on a fixture verb yields a proposal
      naming the verb (mocked).
- [ ] TODO row + drift clean.

## Interconnects

- Spec 022 (parent); Spec 150 (dogfood classifier); Spec 274 (queryable
  monitor); Spec 271 (Jules/MA bridge).
- **Dogfood-loop chain** + **harness-in-harness** (Goal 8).
