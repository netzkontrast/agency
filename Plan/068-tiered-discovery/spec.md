---
spec_id: "068"
slug: tiered-discovery
status: draft
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
