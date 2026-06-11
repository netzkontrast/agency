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

- [ ] **`plugin.validate_published_skill(name) -> RoundTripReport`** —
      `RoundTripReport = {name, metadata_valid: bool, trigger_fired: bool,
      distinctness_score: float, sibling_collisions: list[str],
      driver_used: bool}`. Publishes (dry-run) then asserts the
      Skills-API round-trip: the skill's metadata is well-formed; the
      `Use when:` triggers on a fixture task (Spec 147 Driver simulates
      the trigger decision); degrades to a metadata-only check without
      `[anthropic]`.
- [ ] **Invariant — single source of truth** (relationship): the
      published SkillDoc bytes equal `derive_skill_doc(module)` (Spec
      080); any hand-authored override flagged by Spec 149 drift.
- [ ] **Invariant — trigger distinctness** (relationship): for every
      pair `(s_i, s_j)` of published skills,
      `cosine_distance(trigger_i, trigger_j) >= MIN_DISTINCT` (configured
      threshold, default 0.25) — overlap means the API can't disambiguate
      which to load.
- [ ] **Invariant — trigger fires on positive fixture** (relationship):
      across the published set, `trigger_fired_count / fixture_count
      >= TRIGGER_FIRE_FLOOR` (default 0.9) — a description that fires
      <90% of the time on its own positive examples is dead surface.
- [ ] **Failure mode coverage** — Driver REFUSAL / RATE_LIMITED /
      TIMEOUT each yield a typed `RoundTripReport.driver_used=false`
      with `error_code`, never crash the publish step.
- [ ] Test: a well-triggered fixture skill validates; a vague-description
      fixture fails the distinctness check; a Driver TIMEOUT yields the
      degraded report.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  capability `research` ships with a derived SkillDoc whose
        `Use when:` reads "answering an open question with cited
        evidence from multiple sources" AND [anthropic] is installed
When:   plugin.validate_published_skill("research") runs against a
        fixture task "find three sources on prompt caching"
Then:   RoundTripReport{metadata_valid:true, trigger_fired:true,
        distinctness_score: 0.41, sibling_collisions: []}
        AND a PRODUCES edge from the publish Invocation to the
        RoundTripReport Artefact is written

Given:  two skills' Use-when descriptions are near-identical
        (cosine_distance < MIN_DISTINCT)
When:   the validator runs over the live set
Then:   RoundTripReport.sibling_collisions lists both names
        AND CI fails with TRIGGER_AMBIGUOUS

Given:  the Skills API call raises Driver REFUSAL
When:   plugin.validate_published_skill runs
Then:   returns RoundTripReport{trigger_fired:false, driver_used:false,
        error_code:"REFUSAL"} — never crashes the publish pipeline
```

## Failure modes (Nygard)

| Failure | Validator response |
|---|---|
| Driver `REFUSAL` (Spec 147) | degraded RoundTripReport with `error_code:"REFUSAL"`; skip trigger check |
| Driver `RATE_LIMITED` | retry per Spec 147 budget; never exceed per-validate cap |
| Driver `TIMEOUT` | degraded report; mark `trigger_fired=null` (unknown, not false) |
| Skills-API rejects metadata | typed `BAD_REQUEST{detail:"metadata"}` with the offending field |
| Distinctness threshold violated | report lists colliding siblings; CI fails (no auto-rename) |
| Hand-edited description diverges from derived | Spec 149 drift fails the commit |
| No positive fixture for a skill | typed `BAD_REQUEST{detail:"no_fixture"}` — never publish unverified |

## Interconnects

- Spec 083 (Skills-API publish) is the publish surface.
- Spec 163 (progressive disclosure) derives the SkillDoc.
- **Drift-derivation chain** (149) gates the single-source rule.
- **LLM-driver chain** (147) — Driver simulates the trigger decision.
- Spec 202 (Managed-Agent attach) consumes only round-trip-validated
  skills; an unvalidated skill cannot attach.
- Spec 146 (output-prefix) — the validator's report honors the prefix
  split so re-runs are cache-hit on unchanged skill sets.
- Spec 196 (BDD author_bdd) is itself a validated published skill — the
  validator runs over it like any other.

## Open questions

1. Live Skills-API call in CI? **Recommend**: dry-run + simulated
   trigger in CI (cheap, deterministic); a tagged `live-skills` job
   validates real publication on tag-cut.
2. Where do the positive trigger fixtures live? **Recommend**: derived
   from each capability's docstring `Triggers:` block — same single-
   source rule as the SkillDoc itself (no hand-authored test fixtures
   per CLAUDE.md rule 8).
3. Distinctness metric? **Recommend**: cosine on small-embedding of the
   `Use when:` line; threshold a tunable config constant with documented
   rationale (not a frozen number).
