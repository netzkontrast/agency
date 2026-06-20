---
spec_id: "367"
slug: pillar-skills
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [3]
depends_on: ["363", "365"]
parent_spec: "362"
domain: skills
---

# Spec 367 — The 3 pillar skills (intent · lifecycle · memory)

> Child 5 of Spec 362. The three non-capability concepts of CORE.md's four become
> first-class, self-contained skills — so an agent can learn each pillar, not just
> each capability.

## Why
Agency emits a skill per capability but NONE for the concepts themselves. Intent,
Lifecycle and Memory are the spine every capability rides; an agent needs a skill
that teaches each.

## Design (sketch)
- Three `type: pillar` skills authored as committed `skill.yaml` (via 366 or by
  hand), rendered by the per-type pillar template (365):
  - **intent** — bootstrap → clarify/confirm → the clarity gate; how every session
    serves an intent; the critical-thinking methods.
  - **lifecycle** — open · move · close + read/find/check/watch; the A2A transition
    table; agent-as-parameterization.
  - **memory** — record/recall/link; the bi-temporal graph; provenance edges.
- A generation path for pillar skills (they aren't a `capabilities/<cap>/` folder —
  they're concept skills); `install.generate` emits them alongside the per-cap skills.
- Each is self-contained (A1) with one-deep references into the relevant substrate.

## Slices (TDD)
1. The pillar-skill source location + generation wiring.
2. Author the three pillar `skill.yaml` (intent, lifecycle, memory) + render them.

## Acceptance
- `skills/intent`, `skills/lifecycle`, `skills/memory` render as self-contained
  pillar skills (type=pillar), each teaching its concept with a real example.
- They appear in `agency_welcome` / the skill listing.
