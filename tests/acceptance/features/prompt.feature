Feature: Prompt capability — research briefs, engineering, scene assembly
  prompt assembles dossier-style research briefs, engineers prompts within
  token budgets, audits prose quality, assembles scene briefs with Dramatica
  fragment injection, and gates both at lifecycle phase boundaries (Spec 109/127/129).

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  # ── intent_capture ───────────────────────────────────────────────────────

  Scenario: intent_capture records a ResearchIntent with SERVES edge
    When I capture a research intent with topic "phreakers" and deliverable "dossier"
    Then a ResearchIntent node is created
    And it SERVES the confirmed intent

  Scenario: intent_capture rejects an unknown deliverable
    When I capture a research intent with deliverable "nonsense"
    Then the captured intent is null with error "INVALID_ARGUMENT"

  # ── catalog_list ─────────────────────────────────────────────────────────

  Scenario: catalog_list returns the seed module catalogue
    When I list the prompt module catalogue
    Then the catalogue has 6 modules across categories A, B, C

  Scenario: catalog_list filters by category
    When I list the prompt module catalogue filtered by category "A"
    Then every returned module belongs to category "A"

  Scenario: catalog_list rejects an unknown category
    When I list the prompt module catalogue filtered by category "Z"
    Then the catalogue list is null with error "INVALID_ARGUMENT"

  # ── brief_render ─────────────────────────────────────────────────────────

  Scenario: brief_render produces a research-dossier artefact with RENDERS_FROM edge
    When I render a brief from a captured intent with modules "M01,M03,M06"
    Then the brief artefact kind is "research-dossier"
    And the brief body mentions the topic and the module ids
    And a RENDERS_FROM edge links the brief to the research intent

  Scenario: brief_render returns NOT_FOUND for a missing intent
    When I render a brief for an unknown research intent id
    Then the brief render is null with error "NOT_FOUND"

  # ── brief_audit + brief_finalize ─────────────────────────────────────────

  Scenario: brief_audit records an audit node with AUDITS edge
    When I audit a rendered brief
    Then the audit result has a clarity_score and a status
    And an AUDITS edge links the audit to the brief

  Scenario: brief_finalize flips the brief to finalized
    When I finalize a rendered brief
    Then the finalize result reports finalized true

  # ── engineer + audit ─────────────────────────────────────────────────────

  Scenario: engineer renders a prompt-instance artefact within token budget
    When I engineer a "dialogue-prompt" with normal context
    Then the artefact kind is "prompt-instance"
    And the artefact reports a positive token count

  Scenario: engineer rejects a context that exceeds the token budget
    When I engineer a "dialogue-prompt" with a very tight max_tokens budget
    Then the engineer result is null with error "INVALID_ARGUMENT"

  Scenario: audit scores a prompt for clarity
    When I audit a prompt body with clear structure
    Then the audit reports a clarity_score and a status

  Scenario: audit penalises vague language
    When I audit a vague prompt body
    And I audit a clear prompt body
    Then the vague prompt scores lower than the clear one

  # ── gates ─────────────────────────────────────────────────────────────────

  Scenario: token_budget_gate passes a short prompt
    When I check the token budget gate with a short prompt and limit 100
    Then the token budget gate reports passed true

  Scenario: token_budget_gate blocks an over-budget prompt and pauses the lifecycle
    When I check the token budget gate with a long prompt and limit 10
    Then the token budget gate reports blocked
    And the lifecycle state is "input-required"

  Scenario: audit_gate blocks a low-clarity prompt
    When I check the audit gate with a vague prompt and min_score 70
    Then the audit gate reports blocked

  # ── assemble_scene_brief ─────────────────────────────────────────────────

  Scenario: assemble_scene_brief returns the standard brief shape
    Given a scene is created in the graph
    When I assemble a scene brief
    Then the brief has keys prompt, sections, token_count, sources, brief_id
    And the token count is positive

  Scenario: assemble_scene_brief returns NOT_FOUND for unknown scene
    When I assemble a brief for scene "scene:does-not-exist"
    Then the result error is "NOT_FOUND"

  Scenario: all seven sections are present in the brief
    Given a scene is created in the graph
    When I assemble a scene brief with generous budget
    Then all seven expected sections are present

  Scenario: POV card reflects the scene POV
    Given a scene is created in the graph
    When I assemble a scene brief
    Then the pov_card section contains "third-limited"

  Scenario: storyform section falls back gracefully when no storyform exists
    Given a scene is created in the graph
    When I assemble a scene brief
    Then the storyform section is non-empty

  Scenario: brief artefact is recorded with SERVES edge
    Given a scene is created in the graph
    When I assemble a scene brief
    Then the brief artefact is recorded with kind "scene-brief"
    And the brief artefact SERVES the confirmed intent

  # ── Dramatica fragment verbs ──────────────────────────────────────────────

  Scenario: fragment lookup returns text and metadata for a canonical slug
    When I look up fragment "throughline.main"
    Then the fragment text is non-empty
    And the fragment canonical_id is "throughline.main"
    And the fragment kind is "throughline"
    And the fragment has a positive token count

  Scenario: fragment lookup resolves an element alias
    When I look up fragment "el.morality"
    Then the fragment canonical_id is "var.morality"

  Scenario: fragment returns NO_FRAGMENT for an authoredless entry
    When I look up fragment "el.ability"
    Then the fragment error is "NO_FRAGMENT"

  Scenario: fragment returns UNKNOWN_SLUG for a nonexistent slug
    When I look up fragment "bogus.nonexistent"
    Then the fragment error is "UNKNOWN_SLUG"

  Scenario: fragments_for composes a scope into a fragment list
    When I call fragments_for with a standard scope
    Then the result contains fragments for throughline.main and class.universe
    And the total_tokens is positive
    And truncated_at is null

  Scenario: fragments_for truncates on a tight budget
    When I call fragments_for with a tight max_tokens budget
    Then the truncated_at field is set
    And the total tokens fit within the budget

  Scenario: fragments_for skips unknown slugs and unauthored entries
    When I call fragments_for with an unknown class_id
    Then the unknown slug appears in skipped_no_fragment
