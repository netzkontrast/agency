---
spec_id: "231"
slug: production-binding-derived
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "121"
depends_on: ["121", "149", "170", "214"]
vision_goals: [4, 5]
affects:
  - agency/capabilities/novel/_config.py
  - tests/test_novel_binding_derived.py
---

# Spec 231 — novel production-binding: derived config + doctor

## Why

Spec 121 wires NovelConfig + FileNovelStateDriver. Like the music
parallel (Spec 214), the novel binding's surface should derive: the
config schema, the driver bundle, the render templates — all visible to
`agency_doctor` so a user knows what's wired before they invoke.

## Done When

- [ ] **`agency_doctor` reports novel readiness** — `novel_drivers_wired`,
      `content_root`, template count (derived, Spec 149).
- [ ] **`NovelConfig.bootstrap()` idempotent + reported** (extends 121).
- [ ] **A missing driver yields a typed hint** (Spec 170 pattern).
- [ ] Test: doctor reports the surface; missing driver yields hint.
- [ ] TODO row + drift clean.

## Interconnects

- **Drift-derivation chain** (149) · Spec 214 (music sibling).
- Spec 170 (doctor) is the report surface.
