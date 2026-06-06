---
spec_id: "067"
slug: lint-token-economy-rules
status: draft
last_updated: 2026-06-06
owner: "@agency"
serves_intent: "intent:97534079"
parent: "066"
depends_on: ["016", "019", "023", "049", "054"]
affects:
  - agency/capabilities/plugin/_main.py     # NEW _check_* rules + lint_capability wiring
  - scripts/check-drift                      # surface the new WARN counts in CI
  - tests/test_lint_token_economy.py         # NEW
  - docs/vision/CAPABILITY-AUTHORING.md      # codify the budgets
estimated_jules_sessions: 0
domain: meta
wave: 5
---

# Spec 067 — Lint rules that test the token-economy goals

## Why

This is the **first** child of the token-economy cluster (Spec 066) and the
**executable test for the goals of the whole program**: before any surface
changes (068–071), the readability/token goals are encoded as decidable
`plugin.lint_capability` rules, WARN-first, wired into `scripts/check-drift`. Each
subsequent spec must keep these rules clean (or migrate the surface that trips
them). The lint pipeline is the existing, canon-faithful place for this (Spec
016/019/054/056/058 all extend the same `_check_*` family) — no new mechanism.

## Done When

- [ ] **`_check_name_token_budget(cap)`** (WARN) — flags any verb whose
  `cl100k` token count exceeds a budget (default 6 — `capability_<cap>_<verb>`
  wire form; the bare verb budget is 3). Reports the verb + its token cost + the
  proposed-shorter hint. Encodes GOALS #1; operationalizes the 049 audit.
- [ ] **`_check_bare_name_unique(registry)`** (WARN) — a registry-level rule (not
  per-cap) that flags cross-capability bare-verb collisions (the 049 §4 set:
  `note`, `render`, `verify`) AND any bare verb that shadows a code-mode contract
  tool (`search`/`get_schema`/`execute` — e.g. `reflect.search`). Gates the
  bare-name dispatch surface 069 introduces.
- [ ] **`_check_surface_size(cap, max_verbs=12)`** (WARN) — flags a capability
  carrying more than `max_verbs` verbs without sub-grouping (jules = 22 today).
  Gates the tiered-discovery work (068) + consolidation (070).
- [ ] **`_check_skill_name_parity(registry)`** (WARN) — flags an `ontology.skills`
  key with no matching `skills/<key>/SKILL.md` folder, or a divergent pair
  (the §6b finding: `tdd` ↔ `test-driven-development`). Gates 071.
- [ ] **`brief_budget` parity assertion** — the Spec 023 `_check_render_slice`
  rule already enforces ≤120-char briefs; this spec adds a test asserting that
  rule is present + active (no new rule, parity guard).
- [ ] **Wiring:** the four new rules join the WARN-only `soft_findings` bucket in
  `lint_capability` (same pattern as 056/058 — never block, even in block mode,
  during the migration window). Registry-level rules (`bare_name_unique`,
  `skill_name_parity`) run once over the whole registry, surfaced via a new
  `lint_surface(registry)` entry the engine + `check-drift` call.
- [ ] **`scripts/check-drift`** prints the new WARN counts (token-economy section)
  so CI surfaces the surface's current budget state without failing (WARN).
- [ ] **`tests/test_lint_token_economy.py`** — per rule: a synthetic cap/verb
  that trips it, one that passes, plus a live-registry snapshot of the CURRENT
  WARN set (so the baseline is recorded + drift-guarded, like Spec 049).
- [ ] **CAPABILITY-AUTHORING.md** — a "Token-economy budgets" section naming the
  name/surface/skill budgets + the WARN→BLOCK timeline.
- [ ] `pytest -n auto -m "not e2e"` stays green; `check-drift` exit 0 (WARN ≠ fail).

## Design

### Why WARN-first (and the BLOCK timeline)

The live surface trips these rules TODAY (69 verbs incl. the prefix; jules = 22;
the skill divergence). Blocking immediately would break every capability. WARN-
first records the baseline; each child spec (068–071) drives the relevant WARN
count to zero, then THAT spec flips its rule to BLOCK. Mirrors 056/058.

### Registry-level vs per-capability rules

`name_token_budget` + `surface_size` are per-capability (fit the existing
`_check_*(cap)` signature). `bare_name_unique` + `skill_name_parity` are
inherently cross-capability — they need the whole registry. Add a sibling
`lint_surface(registry) -> {warnings}` entry point (the engine has the registry;
`check-drift` builds a throwaway `Engine(":memory:")`). Keep `lint_capability`
unchanged in shape; the surface rules are a parallel, additive call.

### Budgets (pinned, documented, overridable)

- name: bare verb ≤ 3 cl100k tok; wire `capability_<cap>_<verb>` ≤ 6.
- surface: ≤ 12 verbs per capability before sub-grouping is expected.
- These are the 049-measured medians rounded up; documented in
  CAPABILITY-AUTHORING.md so they are a convention, not a magic number.

## Files

- **Modify:** `agency/capabilities/plugin/_main.py` (4 rules + `lint_surface`),
  `scripts/check-drift` (WARN section), `docs/vision/CAPABILITY-AUTHORING.md`.
- **Create:** `tests/test_lint_token_economy.py`.

## Open Questions

1. **`check-drift` WARN vs FAIL.** v1: WARN-only (exit 0) so the baseline lands
   without breaking CI. Each child flips its own rule to BLOCK when its surface
   is clean. (Resolved: WARN-first.)
2. **Budget tuning.** The 3/6/12 budgets are 049-derived estimates; the live
   snapshot test records the current WARN set so tuning is evidence-driven.

## Evidence

- `agency/capabilities/plugin/_main.py` — `lint_capability` + the `_check_*`
  family + the WARN-only `soft_findings` bucket (Spec 056/058).
- `Plan/049-naming-and-token-economy/naming-audit-report.md` — the budgets +
  collision set + skill-surface divergence this spec encodes as rules.
- `scripts/check-drift` — the CI guard the new WARN section plugs into (Spec 054).
- `GOALS.md` #1 (token efficiency) + `CORE.md` §Naming (the wire form the
  name budget measures against).
