Feature: Plugin authoring — SkillDoc lint and Skill registry (plugin + skills capability)
  The plugin capability lints SkillDocs and capabilities. The skills capability
  finds, renders, ranks, and lints skills from the live registry.
  The emit pipeline produces SKILL.md + reference files + bash wrappers.

  Background:
    Given a confirmed intent

  # ── skills capability — find / render / rank ─────────────────────────────────

  Scenario: skills.find lists all skills with owning capability
    When I invoke "skills" "find" with no arguments
    Then the result has at least one candidate
    And the candidate for "tdd" names "develop" as its capability

  Scenario: skills.find filters by kind
    When I invoke "skills" "find" with kind "usage"
    Then every candidate has kind "usage"

  Scenario: skills.find filters by capability
    When I invoke "skills" "find" with capability "develop"
    Then every candidate belongs to capability "develop"

  Scenario: skills.render returns brief markdown for a skill
    When I invoke "skills" "render" for "shell-usage"
    Then the markdown contains the skill name and a "phases:" section

  Scenario: skills.render returns full markdown with produces when depth is full
    When I invoke "skills" "render" for "shell-usage" with depth "full"
    Then the markdown contains a "produces:" section

  Scenario: skills.render for an unknown skill returns an error
    When I invoke "skills" "render" for "nonexistent-skill"
    Then the result contains an error field

  Scenario: skills.lint passes for a well-formed derived skill
    When I invoke "skills" "lint" for "shell-usage"
    Then lint reports ok with no violations

  Scenario: skills.lint flags an unknown skill
    When I invoke "skills" "lint" for "nope"
    Then lint reports not ok with at least one violation

  Scenario: skills.rank with empty query lists all skills with zero scores
    When I invoke "skills" "rank" with an empty query
    Then the result has at least one candidate with score 0.0
    And the scorer is "keyword"

  Scenario: skills.rank places an exact-name match first
    When I invoke "skills" "rank" with query "tdd"
    Then "tdd" is the first candidate
    And the first candidate has a positive score

  Scenario: skills.rank is deterministic
    When I invoke "skills" "rank" with query "agency walker" twice
    Then both results have the same candidate order and scores

  Scenario: the skills-triage discipline overrides the derived usage skill
    When I invoke "skills" "find" for capability "skills"
    Then "skills-triage" is present in the candidates
    And "skills-usage" is absent from the candidates

  Scenario: skills-triage is walkable via skill_walk
    When I walk the "skills-triage" skill with no inputs
    Then the status is one of "completed", "input-required", "blocked", or "failed"

  # ── validate_skill (develop capability) ──────────────────────────────────────

  Scenario: validate_skill reports all capabilities clean
    When I invoke "develop" "validate_skill" with no arguments
    Then the result is ok
    And the "shell" capability is present and clean

  Scenario: validate_skill for a single capability reports only that capability
    When I invoke "develop" "validate_skill" for capability "reflect"
    Then the result is ok
    And only "reflect" appears in the results

  Scenario: validate_skill for an unknown capability fails with typed violation
    When I invoke "develop" "validate_skill" for capability "no-such-cap"
    Then the result is not ok
    And the violation rule is "unknown-capability"

  # ── lint_capability / lint_surface (plugin capability) ───────────────────────

  Scenario: plugin.lint_explain returns a recipe for a known rule
    When I invoke "plugin" "lint_explain" for rule "surface_size"
    Then the result has steps and a reference
    And the kind is "surface_size"

  Scenario: plugin.lint_explain for an unknown rule returns an error
    When I invoke "plugin" "lint_explain" for rule "no-such-rule"
    Then the result contains an error field

  Scenario: lint_surface splits open warnings from accepted ones
    Given a fresh agency engine in code-mode
    Then lint_surface has no open bare_name_collision warnings
    And lint_surface accepted findings carry an accept_reason

  # ── publish_skill (plugin capability) ────────────────────────────────────────

  Scenario: publish_skill dry-run returns manifest without uploading
    When I invoke "plugin" "publish_skill" for "shell" in dry_run mode
    Then uploaded is False
    And the manifest includes "SKILL.md"
    And no upload was made to the skills client

  Scenario: publish_skill upload records provenance
    When I invoke "plugin" "publish_skill" for "shell" with upload enabled
    Then uploaded is True
    And a published-skill Artefact is recorded

  Scenario: publish_skill for an unknown capability returns an error
    When I invoke "plugin" "publish_skill" for "no-such-cap" as unknown
    Then the publish result contains an error field

  # ── install / emit pipeline ───────────────────────────────────────────────────

  Scenario: every capability with verbs has a declared skill_doc
    Given a fresh agency engine in code-mode
    Then no verb-bearing capability is missing a skill_doc

  Scenario: the generated help skill teaches the MCP form
    Given a fresh agency engine in code-mode
    Then the generated help SKILL.md references "mcp__plugin_agency_agency__execute"
    And the generated help SKILL.md references the bash fallback

  Scenario: the generated SKILL.md for a capability includes required frontmatter
    Given a fresh agency engine in code-mode
    Then the generated shell SKILL.md contains "name: shell"
    And the generated shell SKILL.md contains "description:"

  Scenario: the generated .mcp.json uses the bare agency-mcp command
    Given a fresh agency engine in code-mode
    Then the generated .mcp.json command is "agency-mcp"
    And "AGENCY_DB" is in the env block
