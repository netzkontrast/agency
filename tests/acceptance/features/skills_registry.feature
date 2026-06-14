Feature: Skills registry — index, discovery, and skill-tagging (skills.index, skill tags)
  Skills can be promoted to graph nodes via skills.index. Verbs that are bound
  by a skill phase carry a skill:* tag discoverable via search. MatcherResult
  is the typed shape for skill-match results.

  Background:
    Given a confirmed intent

  # ── skills.index ─────────────────────────────────────────────────────────────

  Scenario: skills.index promotes skills and phases to graph nodes
    When I invoke "skills" "index"
    Then the result reports at least one skill and one phase
    And the graph census shows Skill and Phase nodes matching those counts

  Scenario: indexed skill nodes carry name and kind
    When I invoke "skills" "index"
    Then the "skills-triage" Skill node has kind "discipline"
    And it has an associated Phase node linking back to the skill

  Scenario: skills.index is idempotent
    When I invoke "skills" "index" twice
    Then both calls return the same counts
    And the graph has no duplicate Skill nodes

  # ── skill-tag wiring ─────────────────────────────────────────────────────────

  Scenario: a verb bound by a skill phase carries a skill tag
    Given a fresh agency engine in code-mode
    Then the "delegate" "fan_out" verb carries the tag "skill:review"

  Scenario: a verb can carry multiple skill tags
    Given a fresh agency engine in code-mode
    Then the "delegate" "fan_out" verb's tags collection is a set type

  Scenario: a verb not bound by any skill phase has an empty tag set
    Given a fresh agency engine in code-mode
    Then the "reflect" "note" verb has no skill tags

  Scenario: manually added skill tags are stripped at engine build
    Given a fresh agency engine in code-mode
    Then an extra_capability verb with a hand-written skill tag has that tag removed

  # ── MatcherResult typed shape ─────────────────────────────────────────────────

  Scenario: MatcherResult accepts a valid construction
    When I build a MatcherResult with skill "tdd", confidence 0.9, matcher "pattern"
    Then skill_id is "tdd" and confidence is within [0, 1]

  Scenario: MatcherResult rejects out-of-range confidence
    When I build a MatcherResult with confidence 1.5
    Then a ValueError is raised

  Scenario: MatcherResult rejects rationale longer than 200 characters
    When I build a MatcherResult with a 201-character rationale
    Then a ValueError is raised

  Scenario: MatcherResult rejects an unknown matcher kind
    When I build a MatcherResult with matcher "bogus"
    Then a ValueError is raised

  Scenario: MatcherResult.from_legacy adapts the intent.suggests output shape
    When I build a MatcherResult from the legacy shape with skill "tdd" and mode "pattern"
    Then skill_id is "tdd" and matcher is "pattern"

  Scenario: from_legacy maps llm_select to llm matcher
    When I build a MatcherResult from legacy with mode "llm_select"
    Then the matcher is "llm"

  Scenario: from_legacy clamps confidence over 1.0
    When I build a MatcherResult from legacy with confidence 2.5
    Then the confidence is clamped to 1.0
