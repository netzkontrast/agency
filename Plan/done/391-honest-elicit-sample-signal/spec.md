<!-- agency-node: spec-391 -->
---
spec_id: "391"
slug: honest-elicit-sample-signal
status: done
state: done
last_updated: 2026-06-23
owner: "@agency"
vision_goals: [1, 4]
depends_on: ["285", "390"]
affects:
  - agency/_substrate_tools.py    # agency_doctor host block: honest "advertised, not guaranteed" note
  - agency/install.py             # using-agency: the input-required/resume mid-chain contract
domain: host-bridge / onboarding / honesty
wave: agency-self-teaching
---

# Spec 391 — Honest elicit/sample signal (the C3 defect, correctly scoped)

> Agency Self-Teaching Loop, Pass 2. OBSERVE caveat **C3** reported elicit/sample
> as "advertised live but unreachable from the walker." Investigation (codegraph +
> live repro) found the OPPOSITE of a walker bug.

## Finding — the mechanism is already correct (Spec 285)

`HostBridge.sample`/`elicit` are already SYNC and already bridge the async client
call (`agency/_host_bridge.py::_run` → `anyio.from_thread.run`, asyncio fallback).
`develop._sample_phase` / `_assumption_gate` already call them and advance the walk
when a capable host is bound — **proven** by `tests/test_skill_walk_part_b.py`
(`test_sample_phase_advances_with_host`: the draft is host-sampled; the no-host case
pauses `input-required`). So there is **no walker bug**; the sync↔async bridge exists.

Live, `skill_walk("brainstorm")` returns `input-required, blocked_on: sample:questions`
because THIS client declines server-initiated `ctx.sample()` — `can_sample()` is
optimistic (it only checks the flag + that the Context exposes `sample`), the call
raises `HostUnavailable`, and the walker falls back gracefully. Correct behaviour.

## The real defect — a misleading signal

`agency_doctor`'s `host` block reported `sampling: true` with no hint that it is
*advertised*, not *guaranteed*. A fresh agent trusts it, calls a sample phase, and
is surprised by the pause. The fix is HONESTY, not a new mechanism.

## Approach

1. `agency_doctor` host block gains a `note`: capability is advertised and verified
   only at call time; a decline falls back to an `input-required` pause you resume.
2. `using-agency` documents the **input-required/resume** cycle as the *universal*
   mid-chain interaction (client-support-independent): supply the value and
   `skill_walk(resume_from=…)`.

## Acceptance

```gherkin
Scenario: agency_doctor is honest that host sampling is advertised, not guaranteed
  Given an engine whose host block is reported
  Then the block carries a note that capability is advertised/verified-at-call-time
  And the note names the input-required fallback

Scenario: a capable host still round-trips inline (mechanism unchanged)
  Given a sampling-capable host Context is bound
  When a sample phase is walked
  Then it advances with the host-sampled value (no input-required pause)
```

## Decisions (WH(Y))

- **D1 — Fix the signal, not the mechanism.** The bridge is correct (Spec 285,
  tested); the defect is an over-confident report. WHY: a misleading "sampling:true"
  costs a fresh agent a surprised failure; honesty is the cheap, correct fix.
- **D2 — `input-required`/resume is the canonical mid-chain interaction.** It works
  on every client; server-initiated sample/elicit is the inline OPTIMISATION when
  the client supports it. Document the universal path so no agent depends on the
  optional one.
