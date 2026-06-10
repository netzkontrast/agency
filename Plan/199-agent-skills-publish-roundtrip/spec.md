---
spec_id: "199"
slug: agent-skills-publish-roundtrip
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "080"
depends_on: ["080", "083", "149", "163"]
vision_goals: [4, 5]
affects:
  - agency/capabilities/plugin/_main.py
  - tests/test_agent_skills_roundtrip.py
---

# Spec 199 — Agent-Skill publish round-trip validation

## Why

Spec 080 makes every capability a drop-in Agent Skill (SkillDoc derived
from the docstring). Spec 083 publishes them to the Anthropic Skills
API. But nothing validates the ROUND TRIP — that a published skill,
when loaded back into a fresh Claude surface, actually triggers on its
`Use when:` description and produces the documented behaviour. Per the
`claude-api` Skills doc, a skill's description is what gates loading;
a derived description that doesn't trigger is dead surface.

## Done When

- [ ] **`plugin.validate_published_skill(name)`** — publishes (dry-run)
      then asserts the Skills-API round-trip: the skill's metadata is
      well-formed, the `Use when:` triggers on a fixture task (Spec 147
      Driver simulates the trigger decision).
- [ ] **The derived SkillDoc (Spec 080) is the single source** — no
      hand-authored description diverges (Spec 149 drift).
- [ ] **A trigger-quality check** — the description must distinguish its
      skill from its siblings (no two skills with near-identical
      triggers; an audit).
- [ ] Test: a well-triggered skill validates; a vague-description
      fixture fails the trigger-quality check.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 083 (Skills-API publish) is the publish surface.
- Spec 163 (progressive disclosure) derives the SkillDoc.
- **Drift-derivation chain** (149).

## Open questions

1. Live Skills-API call in CI? **Recommend**: dry-run + simulated
   trigger in CI; a tagged live round-trip validates publication.
