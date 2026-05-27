---
spec_id: novel-001
slug: novel-cluster
status: draft
owner: "@claude"
depends_on: []
affects:
  - "agency/capabilities/narrative.py"
source-repos:
  - "https://github.com/netzkontrast/the-agency-system @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22"
estimated_jules_sessions: 2
domain: "novel"
wave: 2
---

# Novel Capability Cluster

## Why
The Agency system natively integrates long-form narrative primitives (Dramatica theory components, character arcs, structure nodes) into its data models. Currently, these are missing from the PR1 baseline execution capabilities. We must bridge the gap described in the `the-agency-system` phase 7 plans (`phase-7-domain-handler-completion`) by creating dedicated capabilities (`novel.*`) for outlining, drafting, and reviewing structural arcs.

## Done When
- [ ] Create `agency/capabilities/narrative.py` exposing a `novel` capability.
- [ ] Implement `novel.outline` to define a structural anchor document.
- [ ] Implement `novel.draft` to expand those nodes.
- [ ] Implement `novel.review_arc` which asserts presence of `canonical_appreciation` data against the outline.

## Source clones
```bash
git clone --depth=1 https://github.com/netzkontrast/the-agency-system.git ~/work/vendor/the-agency-system
# SHA: 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22
```

## Files
- Create: `agency/capabilities/narrative.py`

## Evidence
- `the-agency-system/phase-7-domain-handler-completion/acceptance.feature`

## Self-Review
Directly translates the Phase 7 domain requirements into Agency execution models.
