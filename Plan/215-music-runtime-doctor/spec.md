---
spec_id: "215"
slug: music-runtime-doctor
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "117"
depends_on: ["117", "214", "209", "170"]
vision_goals: [3, 5]
affects:
  - agency/capabilities/music/_main.py
  - tests/test_music_runtime_doctor.py
---

# Spec 215 — music runtime self-diagnose closure

## Why

Spec 117 (music-runtime-binding) is Partial — Slices 1+2 shipped (F1-F5
closed), but the lazy auto-wiring's failure modes (missing audio deps,
absent content_root, driver build error) surface as raw exceptions
rather than the typed `diagnose` the spec scoped. With the Managed-Agent
audio driver (Spec 209) as a fallback and the deep doctor (Spec 214),
the runtime can self-diagnose and route around a missing local
capability.

## Done When

- [ ] **`music.diagnose()` returns a typed readiness report** — which
      drivers built, which deps are missing, whether the Managed-Agent
      audio fallback (Spec 209) is available.
- [ ] **A missing local audio dep auto-suggests the Managed-Agent
      path** (Spec 209) instead of crashing.
- [ ] **Closes 117's `diagnose` scope** — the Partial flips toward
      Shipped.
- [ ] Test: `diagnose` reports a missing dep + the fallback offer.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 209 (Managed-Agent audio) is the fallback `diagnose` points to.
- Spec 214 (derived config) + Spec 170 (doctor) are the report surface.

## Open questions

1. Auto-route to Managed-Agent or just suggest? **Recommend**: suggest
   (the user's egress policy governs); auto-route behind an opt-in flag.
