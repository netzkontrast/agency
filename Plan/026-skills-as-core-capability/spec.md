---
spec_id: "026"
slug: skills-as-core-capability
status: draft
version: 2                              # rev 2 — folds spec-panel verdict REVISE
owner: "@agency"
depends_on: ["016", "023"]
parallel_to: ["025"]
panel_revision: "ab452c028937d1095"     # spec-panel run id; verdict: REVISE
affects:
  - agency/capabilities/skills.py       # NEW core capability — registry + render + lint (NOT dispatch — see §F5)
  - agency/capabilities/intent.py       # NEW verb intent.suggests_skill — the projection from Intent → next-Skill
  - agency/ontology.py                  # Skill+Phase+Gate nodes; Matcher schema pinned
  - agency/skill.py                     # SkillRun: cue rendering; no new dispatch
  - agency/render.py                    # skill-template surface (T1/T2/T3) — reuses Spec 025 Phase-1 work
  - agency/capability.py                # at registration, promote Capability.ontology.skills → Skill graph nodes; cycle-check deciders
  - tests/test_skills_capability.py     # registry, render, backward-compat
  - tests/test_intent_suggests_skill.py # the three dispatch modes — REAL examples from the existing 17
  - tests/test_jules_workflow_dispatch.py  # convergence benchmark (§F7)
estimated_jules_sessions: 0
domain: meta / dispatch
wave: 3
---

# Spec 026 v2 — Skills as a core capability + intent-conditioned dispatch on `intent`

> **What changed in v2.** Spec-panel returned REVISE with six findings.
> Folded all six (cite tag in each section). Headlines: (1) `attach`
> dropped — return-shape convention. (2) `applies_when` typed as a
> base `Matcher` with cross-cutting concerns. (3) Reference examples
> are now three of the existing 17 skills, not invented. (4) `dispatch`
> moves from `skills` to **`intent.suggests_skill`** — Intent owns
> the projection (CORE.md §Four-concepts fidelity preserved). (5)
> Cycle-check on deciders. (6) Convergence gate = the **Jules workflow
> benchmark**, not a synthetic 50-intent fixture.

## Why

The current model has skills as data — `Capability.ontology.skills`
dicts merged into one ontology. The runtime (`SkillRun`) walks them
linearly by orchestrator-chosen schedule. Nothing in the system
projects from intent → next-skill. Concretely, the Jules workflow
today (the highest-traffic real example, **survey: 6 skills**)
hardcodes that projection in orchestrator code: dispatch returns a
session, the human reads its state, picks the next skill manually
(`AWAITING_PLAN_APPROVAL` → `jules.approve_plan`; `COMPLETED+plan_unapproved` →
`jules-recovery-when-stuck`; PR review comments → `jules-pr-review-cycle`;
batch → `jules-fanout`).

The user's frame: **"Skills accompany every code-mode capability
aspect as prose for the ideal next step of that MCP function in
dependency of the current intent."** This spec realizes that frame
**without** promoting Skills to a fifth concept: it keeps Skills as
Lifecycle templates (CORE.md §51-52) and puts the *projection* —
Intent → next-best-Skill — on the **Intent** capability where it
belongs. Skills remain Lifecycle templates; dispatching them is
Intent's job.

## The four-concept ownership split (panel F5 — pull back)

| Concern | Owner | Verb(s) |
|---|---|---|
| Skill schema, ontology fragment, templates, lint | **skills capability** (new core file) | `skills.find`, `skills.render`, `skills.lint` |
| Projection: intent → next-skill | **intent capability** (existing) | `intent.suggests_skill` |
| Linear walk of a chosen skill | **skill.py runtime** (existing `SkillRun`) | `current()` / `submit()` |
| Verb-result decoration (next-cue, next-skill) | **return-shape convention** (no verb) | shape: `{result: ..., next_skill?: {name, cue}}` |

This holds the four-concept line cleanly: Intent owns intent-keyed
projections; Skills owns the Lifecycle-template registry; the runtime
walker is unchanged.

## Done When

### Skills capability (registry + render + lint)

- [ ] **`agency/capabilities/skills.py` lands** as a single-file core
  capability (~150 LOC + tests). Class-based `SkillsCapability`
  (`CapabilityBase`) per the survey §4 pattern. Owns:
  - **Ontology**: `Skill`, `Phase`, `Gate`, `Matcher` node types;
    `APPLIES_WHEN`, `CHAINS_TO`, `MATCHED_BY` edges;
    `Skill.kind ∈ {discipline, authoring, workflow}` enum.
  - **Pinned `Matcher` schema in `OntologyExtension.schemas`** (panel
    F3b — without this, `record`/`link` cannot validate skills and the
    ontology-rejects-drift guarantee silently weakens).
  - **Templates**: `phase-cue-t1`, `phase-contract-t2`, `phase-reference-t3`.
  - **Verbs**:
    - `skills.find(intent_id=None, *, kind=None, capability=None) -> {candidates: [skill_meta], total}`
      — pure registry browse. **`transform`** role.
    - `skills.render(skill_name, *, depth='brief', phase_index=None, intent_id=None) -> str`
      — render a skill or one of its phases at T1/T2/T3. Reuses Spec
      025 Phase-1 `render_phase`. **`transform`** role.
    - `skills.lint(skill_name) -> {ok, violations}` — phase-shape +
      matcher-schema validation. **`transform`** role.
  - **NO `dispatch` verb here.** Panel F5 + user decision: that's
    Intent's job.

### Intent-conditioned dispatch (on `intent`)

- [ ] **`intent.suggests_skill(intent_id, *, called_capability=None, called_verb=None, called_state=None) -> {skill, mode, confidence, cue, ...} | None`**
  — the central projection. **`effect`** role (panel F1b: may call
  decider verbs / `ctx.sample`; observable cost; provenance writes).
  Walks `applies_when` matchers across the registry; returns the
  winner or `None`.

- [ ] **The `Matcher` schema** (panel F3a — base + kind, not three
  parallel discriminants):

  ```python
  Matcher = {
      "kind": "pattern" | "verb_code" | "llm_select",  # required
      "budget_ms": int = 2000,                          # cross-cutting
      "min_confidence": float = 0.5,                    # cross-cutting
      "cache_ttl_s": int = 60,                          # cross-cutting
      # kind-specific payload (one of):
      "pattern": {"purpose_kw": [str], "intent_re": str?, "acceptance_kw": [str]?},
      "verb_code": {"capability": str, "verb": str},   # decider must return {matches: bool, confidence: float}
      "llm_select": {"prompt": str, "candidates": [skill_name]},
  }
  ```

  All three modes inherit `budget_ms` / `min_confidence` / `cache_ttl_s`
  — caching, timeout, confidence-floor all centralized (panel F2 + F3).

- [ ] **Failure semantics** (panel F2 — distributed systems lens):
  - Per-mode default `budget_ms`: pattern=100ms (effectively instant),
    verb_code=2000ms, llm_select=15000ms. Override per matcher.
  - **Timeout or exception → demote to next mode** in the candidate
    set; do NOT raise into the caller. Log a `Reflection{scope:technical,
    text: "matcher X failed: ..."}` for audit.
  - **LLM-select gibberish** → JSON parse error → demote. Never
    pass unparsed text to the orchestrator.
  - **Decider→skill cycles forbidden** (panel F2c + F1b). At
    registration (`Registry._wire_skill_tags` already runs cross-capability),
    DFS the verb_code matchers; if a decider's invoked verb is itself
    bound to a skill whose matcher uses that decider, raise at engine
    build (clear error, before any run).
  - **Cache**: per `(intent_id, matcher_key)`, TTL `cache_ttl_s`,
    invalidates on `intent.supersede`.

### Three REAL reference examples (panel F4 — no invented skills)

All three exist today. The spec wires them with `applies_when` matchers;
implementation is additive.

| Mode | Existing skill | Matcher |
|---|---|---|
| **Pattern** | `plugin.skill-creation` (5 phases — survey) | `{kind:"pattern", pattern:{purpose_kw:["skill","SKILL.md","author"]}}` — intent.purpose mentions skill authoring |
| **Verb-code** | `delegate.dispatch-decision` (already a decider, 4 phases) | `{kind:"verb_code", verb_code:{capability:"delegate", verb:"dispatch_decision"}}` — re-use existing recommendation logic AS the matcher (panel F4 explicitly cited this) |
| **LLM-select** | `jules.jules-fanout` vs `jules.jules-dispatch` (sibling Jules entry skills) | `{kind:"llm_select", llm_select:{prompt:"Pick the Jules entry-skill best matched to: {intent.purpose}", candidates:["jules-dispatch","jules-fanout"]}}` |

Each example becomes one integration test in
`tests/test_intent_suggests_skill.py` — real engine, real ontology,
real dispatch.

### Return-shape convention for verb-result chaining (panel F1a — no `attach` verb)

Verbs that opt in to chain-suggestion include in their return:

```python
{
    "result": ...,                          # the verb's normal return
    "next_skill": {                          # optional, populated when caller passed intent_id
        "name": "jules-recovery-when-stuck",
        "cue": "Probe the session once for a missing patch — then classify recovery path.",
        "confidence": 0.78,
        "matched_by": "verb_code:jules.classify_recovery_state",
    },
}
```

`engine._wire` reads `next_skill` from the verb's return and **does
not unwrap** it (preserves through to the orchestrator). Pure
convention — no engine code beyond preserving the field. Orchestrator
opts in by calling `intent.suggests_skill` after the verb (or the
verb itself can call it inline and embed the result).

### Backward compatibility (panel F6 — strict-additive AUDIT)

- [ ] **All 17 existing skills work unchanged.** `applies_when`
  absent → never dispatched, still walkable by name via `SkillRun`.
  Asserted by `tests/test_skills_capability.py::test_all_existing_skills_walkable_unchanged`.

- [ ] **Promotion to graph nodes is observable; tests assert it.**
  At engine build, every `Capability.ontology.skills` entry produces a
  `Skill` node. Existing tests asserting graph counts at boot will
  see new nodes — those tests get updated in this same PR. Cite list:
  none today assert exact graph counts (verified via
  `grep "memory.find\|graph_count" tests/`).

- [ ] **Name collision behavior preserved AND tightened** (panel F6b):
  `ontology.py:114-117` already raises on duplicate skill name during
  merge. After promotion, the same uniqueness is enforced at the
  graph layer as a `Skill.name` index constraint. Test:
  `test_duplicate_skill_collision_raises_at_registration`.

### Convergence gate — the Jules workflow benchmark (panel F7 + user redirect)

The user's redirect: instead of a synthetic 50-intent fixture, **use
Jules as the real benchmark**. Concretely:

- [ ] **`tests/test_jules_workflow_dispatch.py`** measures the Jules
  4-step canonical flow under three orchestration models:
  1. **Status quo** — orchestrator hardcodes the chain (the current
     `AGENCY_PROTOCOL.md §5` flow).
  2. **Spec 025 only** (skill-first discovery surface) — orchestrator
     calls `search(tags=["skill:jules-*"])` between steps.
  3. **Spec 026** (`intent.suggests_skill`) — orchestrator calls
     `intent.suggests_skill(intent_id, called_verb=...)` between steps.

  Measure for each: (a) lines of orchestrator code, (b) tiktoken
  cost from search/get_schema/return-envelopes, (c) number of
  manual-routing decisions remaining.

- [ ] **Convergence decision rule** (panel F7 — falsifiable):
  - **If Spec 026 reduces (a) AND (c) by ≥50% vs status quo on the
    Jules flow → Spec 026 ships, Spec 025 becomes discovery layer
    only (no skill.walk verb).**
  - **If both 025 and 026 produce identical Jules orchestration AND
    025 wins on (b) → merge to Spec 027 with discovery-first only.**
  - **If neither significantly improves Jules → reconsider both;
    write a third proposal.**

  The user can run this benchmark and read the table; the answer
  is binary. Gates Spec 025 Phase-2+ AND Spec 026 implementation —
  neither ships further phases until the benchmark fires.

## Files (final list)

- **Create:**
  - `agency/capabilities/skills.py` (~150 LOC)
  - `tests/test_skills_capability.py` (registry, render, backward-compat)
  - `tests/test_intent_suggests_skill.py` (three real-example integration tests)
  - `tests/test_jules_workflow_dispatch.py` (convergence benchmark)
- **Modify:**
  - `agency/capabilities/intent.py` — add `suggests_skill` verb
  - `agency/capability.py` — at registration, promote skill dicts to
    graph nodes + DFS-check decider cycles
  - `agency/ontology.py` — Skill/Phase/Gate/Matcher node schemas +
    Matcher JSON Schema pinned in `OntologyExtension.schemas`
  - `agency/render.py` — skill-render templates (T1/T2/T3) on top of
    existing `render_phase`

## Open Questions (post-revision)

1. **Recursion depth on chained suggestions.** Verb-A returns
   `next_skill: B`; orchestrator walks B; B's last phase calls verb-C
   which returns `next_skill: D`; … is there a hop cap? Recommend:
   yes, same as `ctx.MAX_DEPTH=16` (capability.py). Track per-intent.

2. **`intent.suggests_skill` confidence floor when ZERO matchers
   apply** — return `None` and let orchestrator decide, or return the
   highest sub-threshold candidate with a warning flag? Recommend:
   return `None`; orchestrator decides whether to fall back.

3. **Cache invalidation on intent mutation.** Intent can be
   `supersede`d (CORE.md §22). Cache keys should include
   `intent.version` to auto-invalidate. Tracked in implementation.

4. **Does this subsume `chain_next:` docstring markers?** Today
   prose only; if `intent.suggests_skill` provides the dynamic answer
   per-call, the static marker becomes documentation. Recommend:
   keep static `chain_next:` as the always-on default (zero-cost
   fallback when no `intent_id` is in scope); dispatcher overrides
   when available.

## Loop position

- ✅ **Design** (v1) — `f272b80`
- ✅ **spec-panel** — verdict REVISE, 7 lens findings
- ✅ **Design (rev 2)** — this revision (all 6 panel changes folded)
- ⏭ **Workflow** — IMPLEMENTATION-PLAN.md (next step)
- ⏭ **Implement** — TDD per phase; phase-0 ships the Matcher schema
  + `tests/test_jules_workflow_dispatch.py` baseline (status-quo
  measurement) so the convergence gate has a number BEFORE any new
  surface ships
- ⏭ **Review** + **Improve** — close the loop with benchmark data

Goal contributed to `intent:c374ac3d`: **the orchestrator stops
hand-routing Jules between dispatch/watch/recover/review — the
`intent.suggests_skill` projection routes based on intent.purpose +
the verb's last result.** Measurable via the Jules workflow
benchmark; ships only if it reduces orchestrator hardcoding by ≥50%.

## Followup — Implementation Status (2026-05-31)

> Consolidation pass on branch `claude/plan-spec-review-74gHM`. Frontmatter `status:` may be stale; this section reflects verified code state.

**Verdict:** Not started

### Done
- Nothing — no implementation commits found for Spec 026. `agency/capabilities/skills.py` does not exist; `agency/capabilities/intent.py` does not exist; `agency/ontology.py` has no `Matcher` schema; `agency/capability.py` has no DFS cycle-check for decider verbs.

### Still to implement
- **P0 ✗** — `agency/capabilities/skills.py` (registry + render + lint capability, ~150 LOC): `skills.find`, `skills.render`, `skills.lint` verbs; `Skill`/`Phase`/`Gate`/`Matcher` node types; `Matcher` JSON Schema pinned in `OntologyExtension.schemas`. This is the unblock gate for Spec 024 PR-C.
- **P0 ✗** — `tests/test_jules_workflow_dispatch.py` baseline measurement (status-quo numbers) — the convergence gate has no baseline yet; further phases of both Spec 025 and 026 are blocked without it.
- **P1 ✗** — `intent.suggests_skill(intent_id, ...)` verb on `agency/capabilities/intent.py` (new file).
- **P1 ✗** — Three-mode `Matcher` dispatch (pattern / verb_code / llm_select) with failure semantics, budget_ms, cache, DFS cycle-check.
- **P1 ✗** — Three real reference examples wired with `applies_when` matchers (`plugin.skill-creation`, `delegate.dispatch-decision`, Jules fanout/dispatch).
- **P1 ✗** — Return-shape `next_skill` convention on engine (`engine._wire` preserving the field through to orchestrator).
- **All tests** — `tests/test_skills_capability.py`, `tests/test_intent_suggests_skill.py`, `tests/test_jules_workflow_dispatch.py` do not exist.
- Backward-compat audit: promotion of all 17 existing skills to graph `Skill` nodes not done.

### Refinement needed (given later specs)
- Spec 024 PR-C (three Matcher-mode scaffolds in `examples/`) is explicitly blocked on 026-P0. If 026 design changes, Spec 024 Open Q #5 must be resolved (archive or rewrite PR-C).
- Spec 025 P2+ is gated on the convergence benchmark this spec must run first. The loop is blocked: 025 and 026 cannot advance independently.
- `agency/capabilities/skills.py` will itself be a new capability — it should be authored under the Spec 024 discipline (dogfood test).

### Evidence
- code: `agency/capabilities/skills.py` — absent; `agency/capabilities/intent.py` — absent; `agency/ontology.py` — no Matcher schema
- tests: `tests/test_skills_capability.py` — absent; `tests/test_intent_suggests_skill.py` — absent; `tests/test_jules_workflow_dispatch.py` — absent
- commits/notes: Spec design commits only (`f272b80` v1 draft); no implementation commits found. IMPLEMENTATION-PLAN.md exists but no TDD cycle started.
