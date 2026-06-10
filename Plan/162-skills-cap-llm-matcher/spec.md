---
spec_id: "162"
slug: skills-cap-llm-matcher
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "026"
depends_on: ["026", "147", "152", "161"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/skills.py
  - tests/test_skills_llm_matcher.py
---

# Spec 162 — `skills` cap `llm_select` Matcher

## Why

Spec 026 (skills-as-core-capability) is Partial — its Followup names
the exact blocker: "Remaining: `llm_select` Matcher (needs LLM Driver)
+ Jules convergence benchmark". Spec 147 lifts the blocker. The
`llm_select` Matcher lets the `skills` cap pick the right skill for a
free-text task via the Driver, complementing the pattern + verb_code
Matchers already shipped.

## Done When

- [ ] **`llm_select` Matcher** added to the `skills` cap — given a task
      string + the candidate skill set (Spec 152 typed `Skill`s), the
      Spec 147 Driver returns the best match with a confidence and a
      one-line rationale (`output_config.format`).
- [ ] **Degrades to `pattern`+`verb_code` Matchers** when no
      `[anthropic]` extra (never hard-fails).
- [ ] **Jules convergence micro-benchmark** — the deferred 026 task:
      a fixture of 10 task→skill pairs; assert `llm_select` ≥ lexical
      baseline (mocked Driver in CI; live behind a tag).
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147).
- Spec 152 (typed Skill/Phase) supplies the candidate type.
- Spec 161 (discovery rank) shares the re-rank pattern.

## Open questions

1. Cache the match per (task-hash, skill-set-hash)? **Recommend**: yes,
   session-scoped — repeated walks of the same skill shouldn't re-call.
