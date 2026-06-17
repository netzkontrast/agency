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

  # ── Prompt-framework library (Spec 304) ──────────────────────────────────

  Scenario: framework lookup returns a template and metadata for a known slug
    When I look up framework "co-star"
    Then the framework name is "CO-STAR"
    And the framework template is non-empty
    And the framework intent_category is "create"
    And the framework has a positive token count

  Scenario: framework lookup returns NO_FRAMEWORK for an unknown slug
    When I look up framework "does-not-exist"
    Then the framework error is "NO_FRAMEWORK"

  Scenario: the library covers every user intent category
    When I list every framework intent category present
    Then every user intent category has at least one framework

  Scenario: frameworks_for returns only frameworks for the requested intent
    When I list frameworks for intent "reason"
    Then every returned framework belongs to intent "reason"
    And the frameworks_for total_tokens is positive

  Scenario: frameworks_for truncates on a tight token budget
    When I list frameworks for intent "create" with a tight budget
    Then the frameworks_for truncated_at field is set

  Scenario: register_framework round-trips through the overlay
    When I register a custom framework "my-fw" with a template
    And I look up framework "my-fw"
    Then the framework name is "My Framework"
    And the framework template is non-empty

  Scenario: register_framework rejects a payload with no template
    When I register a custom framework "bad-fw" with no template
    Then the framework error is "INVALID_ARGUMENT"

  # ── Framework routing + render + evaluate (Spec 305) ─────────────────────

  Scenario: route_framework returns one framework with a scaffold and rationale
    When I route the draft "Write a blog post about machine learning for a non-technical audience"
    Then the routed intent is "create"
    And the routed framework is present
    And the route scaffold is non-empty
    And the route rationale is non-empty

  Scenario: route_framework honors an explicit intent hint
    When I route the draft "do the thing" with intent hint "reason"
    Then the routed intent is "reason"

  Scenario: route_framework is token-efficient versus the candidate list
    When I route the draft "Calculate the payback period for CAC 1200 and MRR 150"
    Then the route returns at most two frameworks total
    And that is fewer than the frameworks_for candidate list for intent "reason"

  Scenario: route_framework records a Recommendation serving the intent
    When I route the draft "Rewrite this email to sound more professional"
    Then a Recommendation node serves the intent

  Scenario: render fills a framework template into a PromptInstance
    When I render framework "ape" with action, purpose and expectation fields
    Then the rendered body mentions the field values
    And a FILLS_FRAMEWORK edge links the instance to a PromptFramework node

  Scenario: render refuses an over-budget body
    When I render framework "co-star" with a huge field and a tight budget
    Then the render result is null with error "INVALID_ARGUMENT"

  Scenario: render returns NO_FRAMEWORK for an unknown slug
    When I render framework "nope" with empty fields
    Then the render error is "NO_FRAMEWORK"

  Scenario: evaluate scores a user prompt across five dimensions
    When I evaluate a well-formed user prompt
    Then the evaluation has five dimension scores
    And the evaluation has a status and an overall score

  Scenario: evaluate returns UNKNOWN_TARGET for an unregistered target
    When I evaluate with target "bogus-target"
    Then the evaluation error is "UNKNOWN_TARGET"

  Scenario: evaluate scores a vague prompt below a clear one
    When I evaluate a vague user prompt
    And I evaluate a clear user prompt
    Then the vague overall is below the clear overall

  # ── Functional-doc evaluation (Spec 306) ─────────────────────────────────

  Scenario: evaluate flags role_padding on a functional doc with a Role
    When I evaluate a role-framed functional doc with target "skilldoc"
    Then the evaluation flags include "role_padding"

  Scenario: evaluate does not flag role_padding on a clean functional doc
    When I evaluate a clean functional doc with target "skilldoc"
    Then the evaluation flags exclude "role_padding"

  Scenario: the tool-desc profile flags a missing wire shape
    When I evaluate a bare verb name with target "tool-desc"
    Then the evaluation flags include "missing_returns"
    And the evaluation flags include "missing_inputs"

  Scenario: functional frameworks are held out of user routing
    When I list frameworks for every user intent category
    Then no functional framework slug appears in any candidate list

  # ── Improvement pass (analyze→panel→implement) ────────────────────────────

  Scenario: register_framework rejects an out-of-enum intent_category (fail-fast)
    When I register a custom framework "bad-cat" with intent_category "nonsense"
    Then the framework error is "INVALID_ARGUMENT"

  Scenario: register_framework overlay overrides a vendored framework slug
    When I register an override of vendored framework "co-star" named "Overridden CO-STAR"
    And I look up framework "co-star"
    Then the framework name is "Overridden CO-STAR"

  Scenario: render marks unfilled functional slots with TODO
    When I render framework "skilldoc" with only a use_when field
    Then the rendered body fills the use_when slot
    And the rendered body marks the red_flags slot as TODO

  Scenario: route_framework returns populated alternates when more are requested
    When I route the draft "Write a blog post about machine learning" asking for 2 alternates
    Then the route alternates are populated
    And each alternate has a slug and a name
