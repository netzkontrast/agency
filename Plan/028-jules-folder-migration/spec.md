---
spec_id: "028"
slug: jules-folder-migration
status: stub                     # placeholder for Spec 016 Phase 6 deferral
owner: "@agency"
depends_on: ["016"]              # the folder-form contract Spec 016 v2 proved at 8a5a45d
affects:
  - agency/capabilities/jules.py            → agency/capabilities/jules/jules.py
  - agency/capabilities/_jules_api.py       → agency/capabilities/jules/api.py
  - agency/capabilities/_jules_watch.py     → agency/capabilities/jules/watch.py
  - agency/capabilities/_jules_patch.py     → agency/capabilities/jules/patch.py
  - agency/capabilities/_jules_preambles.py → agency/capabilities/jules/preambles.py
  - agency/capabilities/_jules_skills.py    → agency/capabilities/jules/skills.py
  - agency/capabilities/jules/__init__.py   (NEW — re-exports JulesCapability)
  - 13 test files                           (import path rewires)
estimated_jules_sessions: 0
domain: meta / refactor
wave: 4                          # post-Spec-016-v2 cleanup
---

# Spec 028 — jules → folder form (stub; Spec 016 Phase 6 deferral)

## Why this is a separate spec, not Phase 6 of Spec 016

Spec 016 v2 (`status: complete`, see `Plan/016-…/spec.md`) deferred the
jules migration because:

1. **Mechanical scope is heavy.** 6 source files move + 13 test files
   need import rewires + the `_wire_skill_tags` cross-capability binding
   needs verification under the new module paths. ~500 LOC diff.

2. **Doctrine-vs-mechanical separation.** Spec 016's purpose was the
   *doctrine* (CAPABILITY-AUTHORING.md) + the *foundation* (folder-form
   discover, shared fixtures). The mechanical refactor of an existing
   capability proves nothing about the doctrine that
   `tests/test_subpackage_discovery.py` doesn't already prove.

3. **Risk of co-mingling.** Bundling a heavy refactor with the doctrine
   commit makes bisection painful if something breaks.

## What this spec will cover (when activated)

- The 6-file → folder-form move with import rewires.
- `agency/capabilities/jules/__init__.py` re-exports `JulesCapability`
  (the Hint #1 canonical pattern).
- The 13 test files updated.
- Confirmation that `_wire_skill_tags` still cross-binds jules skills
  to delegate.fan_out etc. under the new paths.
- Full suite stays green throughout.

## Activation gate

This spec activates when:
- Someone needs a 7th `_jules_*.py` sibling helper (Hint #2 promote
  trigger), OR
- A capability authoring pass discovers the existing jules layout is
  blocking some new work, OR
- A maintainer decides the doctrine-vs-implementation gap is enough
  to schedule it.

Until then: stub. The deferral has a home with the rationale visible.

## Evidence

- `Plan/016-capability-authoring-doctrine/spec.md` v2 frontmatter
  `defers_to: ["028"]`.
- `tests/test_subpackage_discovery.py` (`8a5a45d`) — empirical proof
  the folder form works; this spec is purely mechanical when activated.
- `agency/capabilities/jules.py` + 5 `_jules_*.py` helpers — the
  current single-file-with-siblings layout that meets Hint #2's
  promotion threshold (≥3 siblings).
