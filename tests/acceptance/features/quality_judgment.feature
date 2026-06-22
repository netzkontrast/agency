Feature: the LLM judgment pass (Spec 380 §judgment, via Spec 352/279 seam)

  The judgment pass is what produces the REASONING-heavy decay findings
  (R2/R3/R6/T1–T6) the decidable scanners cannot — completing the Spec 380
  "scope → decidable → judgment" core and unblocking the Spec 383 wet corpus.
  It routes through `complete_or_delegate` (OpenRouter free-first → driver → MCP
  host-sampling → host-delegate), so it needs NO API key: inside Claude Code the
  host runs inference and resumes via `host_completion`. Behaviour is verified
  deterministically by injecting a frozen `host_completion` (the resume rail) —
  the real-model path is the same code with a live backend.

  Background:
    Given an engine and confirmed intent

  Scenario: the judgment pass turns an LLM reply into Iron-Law Findings
    Given a frozen LLM reply citing a real risk, a hallucinated code, and an incomplete one
    When the judgment pass runs over a code unit with that reply
    Then only the real, Iron-Law-complete finding survives
    And it carries a risk_code, a Source, a Consequence, and a Remedy

  Scenario: no LLM available degrades to a delegate envelope (decidable still stands)
    When the judgment pass runs with no driver, host, or completion
    Then it produces no judgment findings
    And it returns an "llm_delegate" envelope for the host to fulfil

  Scenario: analyze.review merges judgment findings with the decidable pass
    Given a fixture file that trips a decidable rule
    When analyze.review runs over it with a judgment reply for the same file
    Then the merged findings include the judgment risk_code
    And the decidable finding is still present
