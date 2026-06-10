---
spec_id: "253"
slug: kp-fragments-derive-overlay
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "143"
depends_on: ["143", "239", "147", "149"]
vision_goals: [4]
affects:
  - agency/capabilities/novel/data/kp-fragments.yaml
  - tests/test_kp_fragments_derive.py
---

# Spec 253 — KP fragments: derived overlay + coverage lint

## Why

Spec 143 vendors ~60 KP-derived fragments across 6 families. Like Spec
239 generalizes for Dramatica fragments, the KP overlay should derive
the per-novel overlay from project-specific node properties (alter
names, mode-block labels, reveal-channels). Author authors ONCE per
slug; rest derive.

## Done When

- [ ] **`prompt.derive_overlay_fragments(novel_id)`** generates the
      novel-specific overlay from graph properties — alter taboo from
      Alter.taboo_rules, mode-block from ModeBlock.label etc.
- [ ] **Coverage lint** — every KP-substrate node has a fragment OR
      placeholder.
- [ ] **Lint runs in `check-doc-drift`** (Spec 149).
- [ ] Test: derive overlay reproduces vendored KP corpus on a fixture.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 239 (Dramatica derive) is the parent pattern.
- **Drift-derivation chain** (149).
