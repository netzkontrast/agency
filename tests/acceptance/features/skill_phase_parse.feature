Feature: Skill and Phase parse boundary — typed validation (parse_skill / parse_phase)
  parse_phase and parse_skill validate Skill/Phase dicts at the boundary,
  returning a typed ParseResult with ok/code/message. Every live ontology
  skill parses clean. SkillRun validates its schema at construction.

  # ── Phase variant discriminator ──────────────────────────────────────────────

  Scenario: a plain phase without gate or invoke has variant "step"
    When I parse a phase with name "design" and produces ["plan"]
    Then the parse succeeds with variant "step"

  Scenario: a phase with gate "hard" has variant "hard_gate"
    When I parse a phase with gate "hard"
    Then the parse succeeds with variant "hard_gate"

  Scenario: a phase with gate "soft" has variant "soft_gate"
    When I parse a phase with gate "soft"
    Then the parse succeeds with variant "soft_gate"

  Scenario: a computed gate phase requires a gate_verb
    When I parse a phase with gate "computed" and gate_verb "music.verify_gate"
    Then the parse succeeds with variant "computed_gate"

  Scenario: a computed gate phase without gate_verb fails with typed code
    When I parse a phase with gate "computed" but no gate_verb
    Then the parse fails with code "phase_missing_field" mentioning "gate_verb"

  Scenario: a phase with an invoke block has variant "verb_bound"
    When I parse a phase with invoke capability "plugin" verb "lint_skill"
    Then the parse succeeds with variant "verb_bound"

  Scenario: a phase missing the required "name" field fails with typed code
    When I parse a phase dict that has no "name" key
    Then the parse fails with code "phase_missing_field" mentioning "name"

  Scenario: a phase with an unknown gate value fails with typed code
    When I parse a phase with gate "bogus"
    Then the parse fails with code "phase_unknown_kind"

  Scenario: a phase with produces as a non-list fails with typed code
    When I parse a phase with produces set to an empty string
    Then the parse fails with code "phase_missing_field" mentioning "produces"

  Scenario: a phase with a non-string produces element fails with typed code
    When I parse a phase with produces [1, 2]
    Then the parse fails with code "phase_missing_field"

  Scenario: a verb-bound phase with a gate field fails with typed code
    When I parse a phase with both invoke and gate "hard"
    Then the parse fails with code "phase_unknown_kind"

  Scenario: a verb-bound phase requires exactly one produces entry
    When I parse a verb-bound phase with two produces entries
    Then the parse fails with code "phase_missing_field"

  # ── parse_skill ───────────────────────────────────────────────────────────────

  Scenario: parse_skill returns a Skill with typed phases
    When I parse a skill with name "develop" and three phases including a hard gate
    Then the parse succeeds with 3 phases
    And the phase variants are ["step", "step", "hard_gate"]

  Scenario: parse_skill propagates a phase failure
    When I parse a skill whose second phase is missing a "name"
    Then the parse fails with code "skill_parse_invalid" mentioning "phases[1]"

  Scenario: parse_skill missing name fails with typed code
    When I parse a skill dict that has no "name" key
    Then the parse fails with code "skill_parse_invalid"

  Scenario: parse_skill with non-list phases fails with typed code
    When I parse a skill with phases set to an empty string
    Then the parse fails with code "skill_parse_invalid" mentioning "phases"

  Scenario: parse_skill missing kind fails with typed code
    When I parse a skill with only name and phases but no kind
    Then the parse fails with code "skill_parse_invalid" mentioning "kind"

  Scenario: parse_skill preserves the kind field through round-trip
    When I parse a skill with kind "usage"
    Then the round-trip to_dict preserves the kind

  Scenario: parse_skill round-trips a complex skill dict without loss
    When I parse a multi-phase skill with index, verbs, computed gate, and hard gate phases
    Then the round-trip to_dict equals the input dict

  Scenario: non-contiguous phase indices fail with typed code
    When I parse a skill whose phases have indices [1, 3] skipping 2
    Then the parse fails with code "skill_parse_invalid" mentioning "contiguous"

  # ── live invariant ────────────────────────────────────────────────────────────

  Scenario: every live ontology skill parses clean
    Given a fresh agency engine in code-mode
    Then every skill in the live ontology passes parse_skill with no failures

  # ── SkillRun validates at construction ────────────────────────────────────────

  Scenario: SkillRun rejects a malformed schema at construction
    When I construct a SkillRun with a phase missing its name field
    Then a ValueError is raised with a typed code in the message

  Scenario: SkillRun accepts a valid schema
    When I construct a SkillRun with a valid one-phase schema
    Then the current phase name is returned without error
