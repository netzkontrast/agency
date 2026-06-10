---
spec_id: "265"
slug: plugin-publish-marketplace-shape
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "061"
depends_on: ["061", "175", "148", "177"]
vision_goals: [5]
affects:
  - .claude-plugin/marketplace.json
  - tests/test_marketplace_shape.py
---

# Spec 265 — plugin marketplace.json: full derived shape

## Why

Spec 061 made `marketplace.json` description read the live registry.
Spec 175 derives the install surface. The PLUGIN MARKETPLACE entry
itself (per `developing-claude-code-plugins` skill) should derive: name
+ description + version + source + dependencies. The agency plugin
should publish to a marketplace shape `/plugin install agency` resolves
cleanly, with the deep slash family (Spec 148) advertised.

## Done When

- [ ] **`.claude-plugin/marketplace.json` fully derived** from
      `pyproject.toml` + the live registry + the charter.
- [ ] **Slash family from Spec 148 advertised** in the marketplace
      entry metadata.
- [ ] **Version pinning** via the substrate hardening rules (Spec 092
      generalization, Spec 205).
- [ ] **`check-plugin-reference` (Spec 177) gates the shape.**
- [ ] Test: marketplace.json round-trips through `/plugin install`
      (mocked); shape audit passes.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 175 (install surface) · Spec 148 (slash family) · Spec 177
  (reference audit).
- **UX-onboarding chain** completion at the install surface.
