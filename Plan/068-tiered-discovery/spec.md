---
spec_id: "068"
slug: tiered-discovery
status: done   # Shipped 2026-06-06 (branch claude/spec-068-tiered-discovery)
last_updated: 2026-06-06
owner: "@agency"
serves_intent: "intent:97534079"
parent: "066"
fulfils: "CORE.md §Skills — 'progressive disclosure applies to DISCOVERY'"
depends_on: ["023", "067", "072"]
affects:
  - agency/engine.py                      # search-tier wiring (capability index → drill-in)
  - agency/disclosure.py                  # tier rendering
  - tests/test_tiered_discovery.py        # NEW
estimated_jules_sessions: 0
domain: substrate
wave: 5
---

# Spec 068 — Tiered discovery (the big token win)

## Why

The largest discovery tax is the **flat dump of all 69 verbs** on every `search`,
not the name prefix (Spec 049: names are ~14% of the payload). CORE.md §Skills
now mandates progressive disclosure at the **discovery layer** (Spec 072). This
spec realizes it: `search` discloses the **capability tier first** (≈14
macroskills, one line each ≈ 140 tok) and the agent drills into a capability to
load its verbs — the same pay-per-tier principle as the skill walker, one level
up. A session that needs one capability pays ~140 + ~250 tok instead of ~1471.

## Done When

- [ ] `search` with no/empty query returns the **capability tier** (one line per
  capability: name + one-line gist + verb count), NOT the flat verb list.
- [ ] `search` with a capability name (or `detail` drill param) returns that
  capability's **verb tier** (verb + brief).
- [ ] A keyword query still searches across verbs (the current behaviour) — tiering
  is the DEFAULT/empty-query shape, not a removal of keyword search.
- [ ] The flat verb dump remains reachable (explicit `detail='all'` or similar) as
  a fallback (migration: nothing the current callers rely on disappears).
- [ ] Passes the Spec 067 `surface_size` lint expectation (tiering is the answer
  to a capability with > 12 verbs).
- [ ] `tests/test_tiered_discovery.py`: capability tier shape; drill-in; keyword
  search preserved; measured token cost of the capability tier ≪ flat dump.
- [ ] `pytest -n auto -m "not e2e"` green; `check-drift` clean.

## Migration

Additive: the empty-query default changes shape (tier vs flat), but keyword search
and an explicit flat-dump path are preserved for one minor. Skills/docs that
hard-code the flat shape get updated in lock-step.

## Evidence

- `CORE.md` §Skills (the doctrine this fulfils); `GOALS.md` #1.
- `agency/disclosure.py` (Spec 023 brief-slice machinery this extends).
- `Plan/049-…/naming-audit-report.md` §1–2 (the flat-payload measurement).


## Followup --- Implementation Status (2026-06-06)

> Shipped on branch `claude/spec-068-tiered-discovery`. TDD (RED -> GREEN).

**Verdict:** Shipped

### Done
- `engine._capability_tier(registry)` --- the tier-0 discovery payload:
  `[{name, gist, verbs}]`, gist = the capability module docstring first line
  (redundant `name --` prefix stripped, capped ~72 chars), one line per cap.
- Surfaced ADDITIVELY on `agency_welcome` as `capability_tier`; the names-only
  `capabilities` field kept for back-compat (migration-safe). welcome docstring
  documents the drill-in flow (browse tier -> search('<capability>')/get_schema).
- Measured: the capability tier is **250 tokens vs 1471** for the flat verb dump
  --- an **83% reduction** on the discovery path. The CodeMode `search` (flat
  keyword search) stays as the fallback (additive, nothing removed).
- welcome byte budget raised 1 KB -> 2 KB (justified: the tier is net-token-
  positive --- ~500 tok once on welcome saves the ~1471-tok flat dump); both
  budget tests updated with the rationale.

### Tests
- `tests/test_tiered_discovery.py` --- 3 (tier shape; tier << flat dump; welcome
  surfaces the tier + keeps names). Full suite 793 passed / 3 skipped.

### Note on surface_size (Spec 067 lint)
Tiering makes a large surface TOLERABLE (you do not load jules's 22 verbs unless
you drill into jules), but does not reduce the per-cap verb count --- the
`surface_size` WARN stays for Spec 070 (consolidation) to drive to zero + BLOCK.
