---
spec_id: "252"
slug: novel-skill-walks-managed
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "142"
depends_on: ["142", "180", "147", "150", "021", "040", "146", "245", "247"]
vision_goals: [8, 4]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_skill_walks_managed.py
---

# Spec 252 — novel-craft skill walks: Managed-Agent dispatch

## Why

Spec 142 ships six walkable skills (dual-storyform-author /
canon-lock-author / alter-roster-builder / reveal-rule-author /
r-rule-author / chapter-briefing-author). Each is a 4–6 phase walk
suitable for autonomous run via Managed-Agent (claude-api skill).
This adds the dispatch option: a walk runs locally OR as a
Managed-Agent session, events stream back. The harness-in-harness
ladder applied to novel-craft.

## Done When

- [ ] **`skill_walk(name, driver="managed-agent")`** dispatches the
      walk to a session (Spec 147 `dispatch_session`); events stream as
      MonitorEvents (Spec 021).
- [ ] **Dispatch heuristic** (Spec 040) gates the choice; local default.
- [ ] **Walk artefacts (proposals) record identically** across drivers.
- [ ] Test: a walk runs both ways with parity (mocked session).
- [ ] TODO row + drift clean.

## Interconnects

- Spec 180 (research fan-out) is the pattern.
- **LLM-driver chain** (147) — Managed-Agents bridge.
