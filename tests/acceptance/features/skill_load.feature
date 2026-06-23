Feature: Loading a capability's v2 Skill (Spec 371 Slices 2-3)
  A capability's skill data DERIVES from its module docstring (rule 2 — no
  duplicated authored file): `load_skill` returns that derived, schema-valid v2
  Skill (the back-compat shim, owner=auto). A capability that SHIPS a `skill.yaml`
  gets it parsed as the A6 authored override (owner=capability). `skill_source`
  is the read API — where a capability's skill data came from.

  Background:
    Given a confirmed intent

  Scenario: deriving a Skill from a capability SkillDoc yields a valid v2 capability skill
    When I derive a v2 skill from a capability docstring
    Then the derived skill parses clean with type "capability" and owner "auto"

  Scenario: every registered capability resolves to a valid v2 Skill (back-compat)
    Given a fresh agency engine in code-mode
    Then every capability with a skill_doc loads a schema-valid v2 Skill

  Scenario: a capability shipping a skill.yaml loads it as the authored override (A6)
    When I load a capability that ships a skill.yaml override
    Then the loaded skill is owner "capability" and round-trips its authored phases

  Scenario: the source read API reports derived vs authored provenance
    When I check skill source for a capability with and without a skill.yaml
    Then the bare capability reports source "derived" owner "auto"
    And the skill.yaml capability reports source "authored" owner "capability"

  Scenario: the skills.source verb reports a live capability's provenance
    Given a fresh agency engine in code-mode
    When I read skill source for the "develop" capability via the verb
    Then the verb reports a derived skill owned by "auto"
