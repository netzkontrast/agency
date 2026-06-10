---
spec_id: "202"
slug: skills-api-publish-managed
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "083"
depends_on: ["083", "147", "180", "199"]
vision_goals: [8, 4]
affects:
  - agency/capabilities/plugin/_main.py
  - tests/test_skills_api_managed.py
---

# Spec 202 — publish skills as Managed-Agent skills

## Why

Spec 083 publishes a cap's Agent Skill to the Anthropic Skills API. The
`claude-api` Managed-Agents surface lets a persisted Agent reference
those skills (max 20 per agent) so a Managed-Agent session loads them on
demand. This closes the harness-in-harness loop (Goal 8): an agency
capability becomes a skill a Managed Agent (Spec 180's research fan-out,
or any user agent) can use — the agency engine projecting itself onto
the Anthropic agent platform.

## Done When

- [ ] **`plugin.attach_skill_to_agent(skill_id, agent_id)`** — adds a
      published skill (Spec 083) to a persisted Managed Agent (Spec 147
      create-once doctrine), respecting the 20-skill cap.
- [ ] **The research fan-out (Spec 180) loads its specialist skills**
      this way — a specialist Agent carries the agency `research` skill.
- [ ] **Round-trip validated** (Spec 199) before attach.
- [ ] **Provenance** — the attach records an Artefact + edge.
- [ ] Test: attach respects the cap; a non-validated skill is refused.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) — Managed-Agents bridge.
- Spec 180 (research fan-out) is the first consumer.
- Spec 199 (publish round-trip) gates the attach.

## Open questions

1. Anthropic or custom skill type? **Recommend**: custom (`skill_id`
   from the Skills API, claude-api skill); the agency skills are
   project-specific, not Anthropic's prebuilt set.
