---
spec_id: "171"
slug: node-id-guard-coverage
status: draft
state: inprogress
last_updated: 2026-06-10
owner: "@agency"
enhances: "056"
depends_on: ["056", "058", "149", "151"]
vision_goals: [4, 2]
affects:
  - agency/_lints/_node_id_guards.py
  - tests/test_node_id_guard_coverage.py
---

# Spec 171 — node-id guard coverage promotion

## Why

Spec 056 ships `Memory.recall_typed` + a WARN-only `_check_node_id_guards`
lint and migrated the research/intent/document guards. But it stays
WARN-only — a new verb that takes a `node_id` and skips the label check
ships silently. Like Spec 058's reflection-link lint, this should
become a coverage discipline: every node-id parameter is guarded, and
the lint promotes to error once the live registry is clean.

## Done When (measurable invariants — rule 8)

- [ ] **Typed lint finding: `GuardFinding{verb_id, param_name,
      expected_label: str, severity: Literal["error", "warn"], file,
      line}`** — uniform finding shape across the WARN→error
      transition.
- [ ] **Invariant: `unguarded_node_id_params == ∅`** across the live
      registry — derived sweep over every verb declaring a `*_id`
      param against `recall_typed` call sites.
- [ ] **Invariant: each `*_id` param has exactly ONE declared label**
      — Spec 056's typed recall requires it; a param routing to two
      labels is a wire-shape bug (Spec 019).
- [ ] **Invariant: lint severity is `error` iff sweep is clean** —
      relationship, not pinned timing; the promotion is gated on the
      live registry having zero violations (Spec 056/058 pattern).
- [ ] **Relationship: a deliberately unguarded fixture verb fails
      the (post-promotion) lint** — proves the gate, not pinned.
- [ ] **Invariant: `agency_doctor.node_id_guard_coverage.ready ==
      True` iff sweep clean** — Spec 170 consumer; derived.
- [ ] **Failure mode (lint itself):** the AST walk can't resolve a
      verb's signature (dynamic decorator chain) → emit
      `Codes.GUARD_LINT_UNRESOLVED` + the verb is flagged for manual
      review, NOT silently passed.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  live registry sweep reports zero unguarded `*_id` params;
        lint currently WARN-only
When:   PR ships the WARN→error promotion + adds a fixture verb
        `analyze.foo(target_id: NodeId)` that calls `Memory.recall`
        directly (not `recall_typed`)
Then:   lint emits GuardFinding{verb_id="analyze.foo",
        param_name="target_id", expected_label="Document",
        severity="error"}; CI fails the PR

Given:  same PR fixes analyze.foo to call recall_typed(target_id,
        label="Document")
When:   lint reruns
Then:   findings == [] AND sweep stays clean AND
        agency_doctor.node_id_guard_coverage.ready == True
```

## Failure modes

| Failure | Lint response |
|---|---|
| Verb signature unresolvable (decorator chain) | `GUARD_LINT_UNRESOLVED` + manual-review flag |
| `*_id` param routes to two labels | wire-shape violation; Spec 019 sibling lint catches |
| Sweep finds a hidden site after promotion | CI fails; revert promotion, fix, re-promote (no quarantine list) |
| Live registry adds a new label type | `expected_label` set expands; lint remains stable (open-set) |

## Interconnects

- Spec 058 (reflection-link) is the promotion-pattern sibling.
- Spec 173 (reflection-link promote error) is the simultaneous
  promotion in the dogfood-loop chain.
- Spec 151 (Codes coverage) is the parallel coverage discipline +
  supplies `GUARD_LINT_UNRESOLVED`.
- Spec 170 (doctor) reports `node_id_guard_coverage` (derived).
- Spec 169 (CI coverage gate) — the promoted lint becomes part of
  the per-capability gate's fail conditions.
- **Drift-derivation chain** (149): sweep result + doctor field
  derived per-run, never pinned.

## Open questions

1. Promote now or after one WARN cycle? **Recommend**: after the sweep
   confirms zero gaps — never flip a lint to error with known
   violations (Spec 056/058 non-negotiable rule).
2. Handle dynamic verb registration (e.g. plugin extras)? **Recommend**:
   the lint runs against the loaded registry, not source files only;
   `extra_capabilities=[…]` participates.
3. Cross-process node-ids (Managed Agents session bridge, Spec 147)?
   **Recommend**: the label set is the union across processes; a
   foreign label is `expected_label="<foreign>"` and lint passes
   (boundary-respect).

## Followup — Implementation Status (Slice 1, 2026-06-12)

**Verdict:** Slice 1 SHIPPED on `claude/autonomous-completion` as part of
the typed-shape wave-1 batch (intent:ba14917e tdd walk).

### Done — Slice 1

Typed frozen dataclass + `__post_init__` invariants — see
`agency/_link_finding.py` (Spec 173) and `agency/_typed_shapes_wave1.py`
(Specs 171/175/176). 19 tests in `tests/test_link_finding.py` +
`tests/test_typed_shapes_wave1.py`. The data shape is the Slice 1
contract; Slice 2 wires it into the live verb / gate / hook layer.

### Still — Slice 2+

See the spec's main "Done When" + "Still" sections. The Slice 2
wiring path (graph query, CI gate, sessionstart hook, install
generator) is the next step.

