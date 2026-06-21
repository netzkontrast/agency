---
spec_id: "162"
slug: skills-cap-llm-matcher
status: draft
state: inprogress
last_updated: 2026-06-10
owner: "@agency"
enhances: "026"
depends_on: ["026", "147", "152", "161"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/skills.py
  - tests/test_skills_matcher_result.py   # Slice 1 SHIPPED 2026-06-12 (replaces planned test_skills_llm_matcher.py)
---

# Spec 162 — `skills` cap `llm_select` Matcher

## Why

Spec 026 (skills-as-core-capability) is Partial — its Followup names
the exact blocker: "Remaining: `llm_select` Matcher (needs LLM Driver)
+ Jules convergence benchmark". Spec 147 lifts the blocker. The
`llm_select` Matcher lets the `skills` cap pick the right skill for a
free-text task via the Driver, complementing the pattern + verb_code
Matchers already shipped.

## Done When (measurable invariants — rule 8)

- [ ] **Typed return shape: `MatcherResult{skill_id, confidence: float
      in [0,1], rationale: str ≤ 200 chars, matcher: Literal["llm",
      "pattern", "verb_code"]}`** — `output_config.format` enforces it
      via a Pydantic schema; rejects anything else.
- [ ] **Invariant: when `[anthropic]` absent, `matcher != "llm"`** —
      degrades silently to `pattern` + `verb_code` (Spec 050 pattern).
- [ ] **Invariant: `llm_select` confidence is calibrated against
      ground truth** — on the fixture, `mean(confidence | correct) >
      mean(confidence | incorrect)` (relationship, not a pinned
      number).
- [ ] **Relationship: `accuracy(llm_select) ≥ accuracy(lexical_baseline)`**
      on the 10-pair fixture (≥, not absolute) — derived from the
      fixture each run.
- [ ] **Failure modes (LLM path):** Driver returns a `skill_id` not
      in the candidate set → reject + fall through to `pattern`;
      Driver returns confidence > 1 or < 0 → reject; Driver streams
      stop a partial structured output → retry once, then fall
      through; rate-limit → fall through with a `RATE_LIMITED`
      Reflection. Never let an LLM error halt the walk.
- [ ] **Session-scoped match cache** keyed on `(task_hash,
      skill_set_hash)` — repeated walks of the same skill don't
      re-call the Driver.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  task "I need to verify my last change actually works in the
        running app" and candidate skill set including `verify`,
        `develop.test`, `dogfood.observe`, `branch.commit_smart`
When:   skills.llm_select(task, candidates) runs with `[anthropic]`
        present
Then:   result.matcher == "llm" AND
        result.skill_id == "verify" AND
        result.confidence > 0.7 AND
        result.rationale references "run the app + observe"

Given:  same task, `[anthropic]` absent
When:   skills.match(task, candidates) runs
Then:   result.matcher in {"pattern", "verb_code"} AND
        result is reproducible across runs (deterministic fallback)
```

## Interconnects

- **LLM-driver chain** (147).
- Spec 152 (typed Skill/Phase) supplies the candidate type.
- Spec 161 (discovery rank) shares the re-rank structured-output
  contract — both call the Driver with a candidate set + return a
  ranked result.
- Spec 170 (doctor) reports `llm_select_available` (derived from
  `[anthropic]` + benchmark parity).
- Spec 151 (Codes coverage) supplies `MATCHER_REJECTED_INVALID_ID`
  + `MATCHER_RATE_LIMITED`.
- Spec 146 (output-prefix) — the cache key includes the
  capability-set-hash, so a new skill invalidates the per-task cache.

## Open questions

1. **Cache the match per (task-hash, skill-set-hash)?** **Recommend**:
   yes, session-scoped (cache invalidates on capability-set change
   per Spec 146 prefix hash). Repeated walks of the same skill
   shouldn't re-call.
2. **Fixture size — 10 pairs enough?** **Recommend**: start at 10
   (cheap to maintain, covers the common Lifecycle templates);
   grow only when a confusion-pair lands in production.
3. **Live-Driver benchmark cadence?** **Recommend**: gated behind a
   `[llm-live]` pytest mark + nightly job — keeps the merge gate
   mock-driven (deterministic) while still catching API drift.

## Followup — Implementation Status (Slice 1, 2026-06-12)

**Verdict:** Slice 1 SHIPPED on `claude/autonomous-completion`.

The typed shape this spec carries was shipped as part of the wave-1+2
batch (intents trackable in graph). See TODO.md row + the corresponding
test module under `tests/`.

