Feature: Skill authoring — grounding context (Spec 374 Slice 1)
  The skill-creator grounds an authored skill in a capability's REAL surface:
  its live verbs, signatures, docstrings, and ontology. The grounding builder is
  pure + deterministic (no host LLM) — it is both the structured input a
  skill-creator prompt fills (Slice 2) and the graceful fallback an author reads
  by hand when no host is bound (acceptance: "no host ⇒ graceful return").

  Background:
    Given a confirmed intent

  Scenario: grounding a capability lists its live verbs mirroring the source
    When I ground skill authoring for the "analyze" capability
    Then the grounding lists exactly the live verbs of that capability
    And each grounded verb mirrors its live role and docstring
    And each grounded verb signature omits the injected parameters
    And the grounding summarises the capability's ontology

  Scenario: the grounding is deterministic — same capability, same bytes
    When I ground skill authoring for the "analyze" capability
    And I ground skill authoring for the "analyze" capability again
    Then the two groundings are identical

  Scenario: grounding an unknown capability returns a typed error
    When I ground skill authoring for the "no-such-cap" capability
    Then the grounding result is an error naming the unknown capability

  # ── Spec 374 Slice 2 — per-type prompt + host.sample → schema-parsed draft ────

  Scenario: authoring with a sampling host returns a schema-valid draft
    When I author a "discipline" skill for "analyze" with a stub sampling host
    Then the author result status is "drafted"
    And the draft is a schema-valid skill of type "discipline"

  Scenario: the skill-creator prompt grounds in the capability's real verbs
    When I author a "discipline" skill for "analyze" with no host bound
    Then the prompt lists exactly the capability's live verbs
    And the prompt instructs strict JSON output

  Scenario: no sampling host degrades gracefully to grounding plus prompt
    When I author a "capability" skill for "analyze" with no host bound
    Then the author result status is "no-host"
    And the result carries the grounding and the per-type prompt
    And the per-type prompt names the type's required fields

  # ── Spec 374 Slice 3 — draft validation + source_stamp + install guard ───────

  Scenario: a draft referencing a hallucinated verb is rejected
    When I author a "capability" skill for "analyze" with a stub host that includes a nonexistent verb
    Then the author result status is "invalid"
    And the result names the hallucinated verb

  Scenario: the drafted skill carries a source_stamp
    When I author a "discipline" skill for "analyze" with a stub sampling host
    Then the result carries a source_stamp

  Scenario: the source_stamp is stable — same source yields the same stamp
    When I author a "discipline" skill for "analyze" with a stub sampling host
    And I author the same skill again with a stub sampling host
    Then both source_stamps are identical

  Scenario: install.generate never invokes the host sampler — deterministic install (A7)
    When install.generate runs with a sampling-capable host bound
    Then the host was never sampled during install
