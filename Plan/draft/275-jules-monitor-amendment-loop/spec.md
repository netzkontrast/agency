---
spec_id: "275"
slug: jules-monitor-amendment-loop
status: draft
state: draft
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

- [ ] **Jules MonitorEvents feed Spec 150** as a `proposal` source — a
      mining pass queries Spec 274 for recurring `silent_fail_detected`
      / `recovery_started` patterns and emits AmendmentProposal nodes.
- [ ] **Bridges across drivers** (Spec 271 Jules ↔ MA bridge) — the
      mining pass groups by `(verb, kind)` ignoring `driver`; patterns
      apply regardless of remote driver. A pattern observed only on
      one driver carries `scope=driver_specific` metadata.
- [ ] **Structured monitor (Spec 274) is the query backend** — never
      raw SLOG; the loop runs on typed `MonitorEvent` nodes.
- [ ] **Loop quality measured** via Spec 258 — proposal acceptance rate
      + time-to-amendment tracked as graph metrics.
- [ ] **Threshold is a tunable budget, not a frozen count** — default
      `N=3` repeats within `window=7d`, both overridable via
      `dogfood.config`. (CLAUDE.md rule 8: a named tunable budget with
      rationale is fine; a hardcoded `if count == 3:` is not.)
- [ ] **Invariants** (CLAUDE.md rule 8):
      - For every AmendmentProposal `p` of source=jules_monitor,
        `count(MonitorEvent where verb=p.verb AND kind=p.kind AND
        ts > now - p.window) >= p.threshold` — the proposal cites the
        evidence count, not a magic number.
      - Proposals dedupe on `(verb, kind, week_bucket)` — the same
        recurring pattern produces ONE proposal per bucket, not N.
      - `set(driver) ⊆ {jules, managed_agent, *future}` — open-set
        per Spec 271; the loop never hard-codes the driver list.
- [ ] **Failure modes table** — see below.
- [ ] Test: 3× silent-fail on a fixture verb within window yields a
      proposal naming the verb + the evidence count (mocked); proposals
      dedupe across the same week; a mixed Jules+MA pattern produces
      one driver-agnostic proposal; 2 events do NOT trigger.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  over 7 days, jules.dispatch emits silent_fail_detected for
        intent_a (driver=jules), intent_b (driver=jules), intent_c
        (driver=managed_agent) — 3 events, mixed drivers
When:   the mining pass runs (daily)
Then:   one AmendmentProposal emits: {verb: jules.dispatch, kind:
        silent_fail_detected, evidence_count: 3, drivers: [jules,
        managed_agent], window: 7d, suggestion: "raise verify_window_s
        OR swap default recovery"}; scope=cross_driver, not
        driver_specific

Given:  the same pattern persists into next week — 2 more events for
        jules.dispatch
When:   mining pass runs again
Then:   no NEW proposal (dedupe on week_bucket); the existing proposal
        node's evidence_count updates to 5; if the proposal was
        accepted as an amendment in the prior week, the loop closes
        and Spec 258 records time-to-amendment

Given:  a contributor disagrees with the classifier and rejects the
        proposal
When:   dogfood.reject(proposal_id) runs
Then:   proposal marked rejected with rationale; mining pass skips this
        (verb, kind) for `cool_off_window=30d`; recurring rejections
        are themselves a meta-pattern Spec 150 mines
```

## Failure modes

| # | Failure | Detection | Response |
|---|---|---|---|
| F1 | Mining pass runs against incomplete graph (ingest lag) | Query Spec 274 ingest_lag metric | Defer mining pass; emit `mining_deferred_lag` MonitorEvent; never propose on partial data |
| F2 | LLM classifier (Spec 150) misclassifies a transient as a pattern | Acceptance rate tracking (Spec 258) drops | Spec 277 dogfood loop tunes the classifier prompt; proposal carries `confidence` |
| F3 | Driver-specific pattern surfaces as cross-driver | Driver-set check on the proposal | Mining pass tags `scope=driver_specific` when ≥80% of evidence is one driver |
| F4 | Same proposal re-emits every run (dedupe broken) | `(verb, kind, week_bucket)` uniqueness | Block emit at write time + emit `proposal_dedupe_violation` |
| F5 | Threshold tuned too low → proposal storm | Acceptance rate < threshold | Auto-raise `N` for that verb; doctor surfaces the over-eager rule |
| F6 | Verb is renamed (Spec 080-style migration) and history splits | Pattern matcher loses continuity | Mining pass reads `Verb.aliases` from the graph; matches union of names |

## Interconnects

- Spec 022 (parent) — Jules as first monitor consumer.
- Spec 150 (dogfood classifier) is the proposal sink.
- Spec 274 (queryable monitor) is the query backend.
- Spec 271 (Jules/MA bridge) provides the driver-agnostic event stream.
- Spec 277 (dispatch LLM refine) is a sibling consumer — recurring
  LLM-overrides on dispatch also feed Spec 150.
- Spec 276 (doctor managed-aware) surfaces mining-pass lag as a
  readiness signal.
- Spec 258 (loop quality) measures acceptance rate + time-to-amendment.
- **Dogfood-loop chain** + **harness-in-harness** (Goal 8) closure for
  remote-agent operations.

## Open questions

1. **Mining pass cadence.** Continuous vs daily?
   **Recommend**: daily — pattern detection over a 7d window doesn't
   need sub-minute freshness; daily keeps the LLM cost bounded.
2. **Proposal auto-apply.** Should high-confidence proposals
   auto-merge as amendments? **Recommend**: NO — a human (or the
   spec-author agent) reviews every proposal. The loop's value is
   surfacing the candidate; auto-apply turns it into a runaway.
3. **Cross-spec patterns.** If silent_fail recurs across multiple
   verbs, propose a substrate-wide amendment? **Recommend**: yes —
   tag the proposal `scope=substrate` when ≥3 verbs share the kind;
   the proposal becomes a spec draft (Spec 150 → new spec generator).
