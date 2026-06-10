---
spec_id: "175"
slug: install-surface-derived
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "061"
depends_on: ["061", "149", "148", "170"]
vision_goals: [5, 4]
affects:
  - agency/install.py
  - tests/test_install_surface_derived.py
---

# Spec 175 — install-surface fully derived

## Why

Spec 061 (install-surface-refresh) made `marketplace.json`'s
description read the live registry (cap count + first-7 surface). The
enhancement layer extends this: the ENTIRE install surface
(`marketplace.json`, the README capability table, the slash-command
family from Spec 148, the `userConfig` extras list) should DERIVE from
the live registry + the installed extras, so adding a capability or an
extra updates the install surface with zero hand-edits (the drop-in
bar, CLAUDE.md).

## Done When

- [ ] **README capability table derived** (Spec 149) — a new capability
      auto-adds its row.
- [ ] **`userConfig` extras list derived** from `pyproject.toml`
      `[project.optional-dependencies]` — a new extra (`[anthropic]`)
      auto-appears.
- [ ] **Slash-command family (Spec 148) regenerated** on install.
- [ ] **`check-doc-drift` (Spec 149) gates the README table** against
      the live registry.
- [ ] Test: add a fixture capability → README row + marketplace
      description + slash command all update on `agency install`.
- [ ] TODO row + drift clean.

## Interconnects

- **Drift-derivation chain** (149) · **UX-onboarding chain** (148).
- Spec 170 (doctor) reports the derived surface.

## Open questions

1. Derive at install-time or commit-time? **Recommend**: both —
   commit-time gate (drift) keeps the repo honest, install-time
   regen keeps a fresh clone correct.
