---
spec_id: "239"
slug: dramatica-fragments-derive
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "129"
depends_on: ["129", "147", "149", "143"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/novel/data/dramatica/ontology.json
  - tests/test_dramatica_fragments_derive.py
---

# Spec 239 — Dramatica fragments: derive + lint coverage

## Why

Spec 129 ships 34 hand-authored fragments out of 304 ontology entries
(11%). Its Slice 2 names "authoring the remaining ~270 entries +
lint enforcement of 'fragment OR placeholder'". With Spec 147 the
remaining fragments can be DRAFTED via the Driver against the
ontology entry's metadata + the existing 34 as exemplars — author
reviews, never auto-canonizes. Spec 143's KP fragments are a worked
overlay precedent.

## Done When

- [ ] **`prompt.draft_fragments(scope)`** runs the Spec 147 Driver
      across ontology entries lacking fragments; output is `proposal`
      status (Spec 137 canon-status), never auto-canon.
- [ ] **Lint: "fragment OR placeholder"** — every ontology entry has
      one or the other; CI gates.
- [ ] **Coverage derived** (Spec 149) — `agency_doctor.fragment_coverage`.
- [ ] Test: drafted fragment lands as proposal; lint trips on a missing
      slot.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147); Spec 143 is the worked overlay sibling.
- Spec 137 (canon-status) — drafts are `proposal`, not silent canon.
