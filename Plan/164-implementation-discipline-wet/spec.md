---
spec_id: "164"
slug: implementation-discipline-wet
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "041"
depends_on: ["041", "081", "156", "147"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/develop/_main.py
  - tests/test_implementation_discipline_wet.py
---

# Spec 164 — Implementation-discipline skills, wet phases

## Why

Spec 041 (implementation-discipline-skills) is Partial — 3 disciplines
ported (dispatching-parallel-agents, subagent-driven-development,
executing-plans) under the derive model, but the skills are scaffolds
the agent fills in chat. With Spec 147 + 156's wet path, the
disciplines can RUN their checks — e.g. `executing-plans` can verify a
plan step's acceptance via the Driver, `subagent-driven-development`
can score a returned subagent transcript.

## Done When (measurable invariants — rule 8)

- [ ] **Typed return shape: `VerifyResult{phase_id, accepted: bool,
      rationale: str ≤ 200 chars, evidence_refs: list[node_id],
      matcher: Literal["wet", "scaffold"]}`** — `output_config.format`
      enforces it; rejects anything else.
- [ ] **Invariant: when `[anthropic]` absent, `matcher == "scaffold"`** for
      every discipline — degrades silently (Spec 050 pattern).
- [ ] **Invariant: every failed wet verify EMITS a Reflection** linked to
      the discipline's intent (SERVES + OBSERVED_DURING per Spec 058) —
      relationship, not pinned count.
- [ ] **Relationship: `walk_halts(failed_gate) == True`** — when a gate
      phase returns `accepted=False`, the walk MUST halt before the next
      phase; asserted from the live walk graph, not snapshot.
- [ ] **Relationship: `skills/ folder count == 0`** after retire — the
      derived set fully supplants literal authoring (Spec 081 derive
      model, derivability audit).
- [ ] **Failure modes (wet path):** Driver timeout → fall back to
      scaffold + emit `Codes.VERIFY_TIMEOUT` Reflection; structured
      output malformed → reject + scaffold fallback; Driver returns
      `evidence_refs` pointing at non-existent node-ids → reject (never
      trust opaque IDs back from the model). Never let a Driver error
      auto-advance a gate.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  walk `develop.execute` mid-plan, phase 3 of 7 is gated,
        `[anthropic]` present, prior phase produced evidence node N42
When:   develop.execute.verify(phase_id=3, evidence_refs=[N42]) runs
Then:   driver.complete returns VerifyResult{accepted=true, matcher="wet",
        rationale references N42's content} AND walk advances to phase 4
        AND envelope.prefix bytes are byte-identical to phase 2's
        (Spec 146 cache held)

Given:  same walk, Driver returns accepted=false on phase 3
When:   verify completes
Then:   walk halts before phase 4 AND a Reflection is written linking
        SERVES intent + OBSERVED_DURING phase 3 (Spec 058) AND the
        Reflection is classifier-ready for Spec 150 amendment proposal

Given:  same walk, `[anthropic]` absent
When:   verify runs
Then:   matcher=="scaffold" AND walk proceeds with scaffold-check (no
        halt) AND no spurious Reflection is emitted
```

## Failure modes (Nygard)

| Failure | Discipline response |
|---|---|
| Driver `TIMEOUT` on a gate verify | fall back to scaffold + emit Reflection; never auto-pass |
| Driver `REFUSAL` (Spec 147) | scaffold fallback; never retry same request |
| Malformed `VerifyResult` | reject + scaffold fallback; emit `Codes.VERIFY_MALFORMED` |
| `evidence_refs` includes unknown node-id | reject; emit `Codes.VERIFY_UNKNOWN_REF` |
| `[anthropic]` extra missing | silent degrade to scaffold (matcher="scaffold") |
| Discipline's skills/ folder still present after retire | drift lint fails (Spec 149) |

## Interconnects

- **LLM-driver chain** (147) — the verify path is the second non-thinking
  Driver consumer after Spec 150.
- **Dogfood-loop chain** (150/173) — every failed verify produces a
  Reflection the classifier reads; Spec 173's promotion guarantees the
  edges exist.
- **Output-budget chain** (146) — verify's structured output budgets
  through the same envelope; rationale capped at 200 chars to keep
  prefix bytes stable across walks.
- Spec 156 (wet pressure) is the sibling wet-path spec.
- Spec 081 (derive model) is the retire target; Spec 149 audits drift.
- Spec 151 (Codes coverage) supplies `VERIFY_TIMEOUT`, `VERIFY_MALFORMED`,
  `VERIFY_UNKNOWN_REF`.
- Spec 161 (discovery rank) — disciplines surface through the same
  re-rank path; consistent structured-output contract.

## Open questions

1. Verify every step or only gate steps? **Recommend**: gate steps only
   (cost); intermediate steps stay scaffold-checked. A `gate_phase: bool`
   flag on the phase declaration; default false.
2. Reflection scope for a failed wet verify — `observation` or
   `proposal`? **Recommend**: `observation` (Spec 159 auto_scope); Spec
   150's classifier promotes to `proposal` if the pattern repeats ≥ N.
3. Cache verify result per (phase_hash, evidence_hash)? **Recommend**:
   session-scoped only; invalidates on capability-set-hash change
   (Spec 146 prefix). A re-walk of the same plan shouldn't re-pay the
   Driver call within a session.
