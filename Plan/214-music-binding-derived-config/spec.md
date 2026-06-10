---
spec_id: "214"
slug: music-binding-derived-config
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "115"
depends_on: ["115", "117", "149", "170"]
vision_goals: [4, 5]
affects:
  - agency/capabilities/music/_config.py
  - tests/test_music_binding_derived.py
---

# Spec 214 — music binding: derived config + doctor

## Why

Spec 115 (music production-binding) wires the production drivers; Spec
117 (music-runtime-binding) closed the runtime gap with lazy
auto-wiring + `MusicConfig.bootstrap()`. The config surface
(content_root, drivers, name-exposure blocklist) is hand-maintained.
The derived-doc discipline (Spec 149) + deep doctor (Spec 170) should
extend to music: the config schema is derived, and `agency_doctor`
reports music-driver readiness so a user knows what's wired.

## Done When

- [ ] **`agency_doctor` reports music readiness** — `music_drivers_wired`,
      `content_root`, `name_exposure_blocklist` size (derived, Spec 149).
- [ ] **The music-config schema is validated** against the live driver
      bundle — a missing driver yields a typed hint (Spec 170 pattern).
- [ ] **`MusicConfig.bootstrap()` is idempotent + reported** (extends
      Spec 117's bootstrap with doctor visibility).
- [ ] Test: doctor reports the music surface; a missing driver yields
      its hint.
- [ ] TODO row + drift clean.

## Interconnects

- **Drift-derivation chain** (149) · Spec 170 (doctor deepening).
- Spec 117 (runtime binding) is the wiring this reports.

## Open questions

1. One doctor section for music or per-cluster? **Recommend**: one
   music section — matches the single-doctor surface.
