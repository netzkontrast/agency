<!-- agency-node: spec-365 -->
---
spec_id: "365"
slug: loop-council
status: draft
last_updated: 2026-06-21
owner: "@agency"
vision_goals: [3, 4]
depends_on: ["002", "040", "271", "294", "297", "362", "364"]
parent_spec: "362"
affects:
  - agency/_loop.py                        # recommend_council helper (cross-family + verdict-source check)
  - agency/_lifecycle_data/loop/rubrics/   # council-rubric.md (verbatim from looper)
  - agency/capabilities/persona/           # reuse — a council member IS a persona
  - agency/capabilities/panel/             # reuse — convene IS a panel
domain: loop / delegation / lifecycle-spine
wave: looper-port
---

# Spec 365 — The cross-model council (reuse persona + panel + delegate)

> Child of Spec 362. **Spine-framed + frugal (2026-06-21):** looper's cross-model
> review council maps 1:1 onto primitives that already exist — a council member
> **IS a `persona` (297)** bound to a model **driver (002)**; convening **IS a
> `panel` (294)**; dispatch to another model **IS `delegate`/`jules` (040/271)**.
> 365 adds only the council rubric (data) + a cross-family recommendation helper.
> **No new capability.**

## Why

Looper wires a **reviewer or judge from a different model family than the host** —
the "codex → claude / claude → codex" bridge — because a second, different model
catches what the author misses. Two roles:

- **reviewer** → notes; the host revises against them. No verdict.
- **judge** → a structured verdict that **gates progression**.

**The reviewer-only rule:** `verdict_policy: revise_until_clean` **requires a
`verdict_source`** (a judge member or `human`); a reviewer-only gate may use
`fixed_passes` but not `revise_until_clean` — nothing can declare "clean."

## Design

### A council member = a `persona` bound to a model driver

`persona.create` (297) mints a role-scoped reviewer; binding it to a named model
**driver** (`ctx.get_driver`, 002 — resolved/registered by 369) supplies the
"which model, which family" part. `role` (reviewer|judge), `scope`
(plan|delivery), `family`, and `local` are persona/driver props — no new node type.

### Convene = `panel`; verdict via `delegate`/`jules`; degrade parity

`panel.convene` (294) runs the members over an artefact; a **judge** member's
output is a structured verdict `{verdict, blocking_issues, confidence, notes}`.
A cross-vendor send goes through `delegate`/`jules` (040/271) + the
`egress_consent` gate (369). **Judge JSON degrades to revise + warn** on
unparseable output (looper `parse_judge_output`, ported) — never a crash.

### `_loop.recommend_council` — the one helper (cross-family + the rule)

```python
def recommend_council(ctx, loop_id) -> dict:
    """For each revise_until_clean gate, report whether a verdict source exists
    (judge member or human) — the reviewer-only rule (enforced at _loop.open, 366).
    Recommend a member from a DIFFERENT family than the host (cross-model is the
    coaching default, NOT a hard rule). Returns {verdict_sources_ok, missing:[gate],
    recommended:[{persona, family}]}. Surfaces council-rubric.md."""
```

`council-rubric.md` ships verbatim to `agency/_lifecycle_data/loop/rubrics/`.

## Acceptance (Gherkin)

```gherkin
Scenario: a council member is a persona bound to a model driver
  When I add a judge member on the codex family while the host is claude
  Then a persona role=judge family=codex is recorded, bound to a driver
  And recommend_council notes it is cross-family (the coaching default)

Scenario: a judge verdict is structured and gates progression
  When a judge convenes over a plan artefact and returns revise with blocking issues
  Then the verdict parses structurally and the gate does not pass

Scenario: an unparseable judge verdict degrades to revise + warn
  When a judge returns non-JSON text
  Then it is treated as revise, tagged unparseable (no crash)

Scenario: the reviewer-only rule is reported for a revise_until_clean gate
  Given a revise_until_clean gate with only reviewer members
  When I recommend_council
  Then verdict_sources_ok is false and the gate is listed as missing a verdict source
```

## Done When

- [ ] A council member is a `persona` (297) bound to a model driver (002); role/scope/family/local as props; no new node type.
- [ ] Convene reuses `panel.convene` (294); cross-vendor sends route through `delegate`/`jules` + the 369 egress gate.
- [ ] Judge output is structured; unparseable degrades to revise + warn (ported `parse_judge_output`).
- [ ] `_loop.recommend_council` reports verdict-source presence + a cross-family recommendation.
- [ ] `council-rubric.md` ships verbatim under `agency/_lifecycle_data/loop/rubrics/`.
- [ ] `tests/acceptance/test_loop_council.py` covers the scenarios.
- [ ] `TODO.md` row updated.

## Followup — Implementation Status (2026-06-21)

**Verdict:** Re-drafted spine-framed (2026-06-21). The council as **reuse**:
member = `persona`+driver, convene = `panel`, dispatch = `delegate`/`jules`.
**Frugal: net-new is council-rubric (data) + one `recommend_council` helper — no
new capability.** The reviewer-only rule is reported here, enforced at
`_loop.open` (366); the verdict feeds 366's `advance`.
