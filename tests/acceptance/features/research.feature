Feature: research capability — lead, specialist, verify, ingest_gdoc (Spec 044, Spec 052, Spec 126, Spec 168)
  The research capability drives structured evidence gathering. lead mints a
  Research node and fan-out plan; specialist roles record Citation nodes; verify
  runs adversarial checks (evidence-supports-claim, contradiction-cluster,
  web-reachability); ingest_gdoc returns a dispatch contract. Behaviour is
  observable through returned values and graph state.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  # ── research.lead — scope + plan ───────────────────────────────────────────

  Scenario: lead records a Research node in the graph
    When I call research.lead with question "how does dispatch work?" at depth "brief"
    Then the result carries a research_id
    And a Research node with that id exists in the graph
    And the Research node has question "how does dispatch work?" and depth "brief"
    And the Research node status is "planning"

  Scenario: lead links the Research node to the intent
    When I call research.lead with question "x" at depth "brief"
    Then the Research node has a SERVES edge to the intent

  Scenario: lead at depth brief returns only the codebase specialist
    When I call research.lead with question "how does dispatch work?" at depth "brief"
    Then the specialist list contains only "codebase"

  Scenario: lead at depth standard returns two or more specialists
    When I call research.lead with question "what is the dispatch heuristic" at depth "standard"
    Then the specialist list has at least 2 entries
    And "codebase" is among the specialists

  Scenario: lead at depth deep returns three or more specialists
    When I call research.lead with question "how do agency capabilities compose" at depth "deep"
    Then the specialist list has at least 3 entries

  Scenario: lead returns a non-empty plan
    When I call research.lead with question "x" at depth "brief"
    Then the plan text is non-empty

  # ── research.specialist — codebase ─────────────────────────────────────────

  Scenario: codebase specialist records Citation nodes with confidence 1.0
    Given I have seeded a research lead at depth "brief" for "dispatch"
    When I run the codebase specialist with query "dispatch_decision" on the agency source
    Then the citations count is at least 1
    And the specialist result carries a summary
    And all Citation nodes for the research have confidence 1.0
    And all those Citation nodes have source_kind "codebase"

  # ── research.specialist — prior-reflections ────────────────────────────────

  Scenario: prior-reflections specialist records reflection-sourced citations
    Given a reflection about dispatch signals is recorded
    And I have seeded a research lead at depth "brief" for "x"
    When I run the prior-reflections specialist with query "dispatch signals"
    Then the citations count is at least 1
    And at least one Citation node has source_kind "reflection"

  # ── research.specialist — doc-corpus ───────────────────────────────────────

  Scenario: doc-corpus specialist finds matching content in a local docs directory
    Given a local docs directory with a file mentioning dispatch_decision
    And I have seeded a research lead at depth "brief" for "x"
    When I run the doc-corpus specialist with query "dispatch_decision" against that docs dir
    Then the citations count is at least 1

  # ── research.specialist — error handling ───────────────────────────────────

  Scenario: unknown specialist role returns an error
    Given I have seeded a research lead at depth "brief" for "x"
    When I run a specialist with an unknown role
    Then the result carries an error key

  # ── research.verify — evidence-supports-claim ──────────────────────────────

  Scenario: verify passes when evidence text contains the claim
    Given I have seeded a research lead for verification
    And a citation where evidence contains the claim text
    When I call research.verify on that research
    Then the verify result is ok
    And the evidence-supports-claim check status is "pass"

  Scenario: verify fails when evidence is unrelated to the claim
    Given I have seeded a research lead for verification
    And a citation where evidence is unrelated to the claim
    When I call research.verify on that research
    Then the verify result is not ok
    And the evidence-supports-claim check status is "fail"
    And the evidence-supports-claim check lists offending items

  # ── research.verify — contradiction-cluster ────────────────────────────────

  Scenario: verify flags contradicting claims
    Given I have seeded a research lead for verification
    And two citations with contradicting claims
    When I call research.verify on that research
    Then the contradiction-cluster check status is "warn" or "fail"
    And the contradiction-cluster check lists items

  # ── research.verify — provenance ───────────────────────────────────────────

  Scenario: verify records a Verification node in the graph
    Given I have seeded a research lead for verification
    And a matching citation
    When I call research.verify on that research
    Then a Verification node exists for the research in the graph
    And the Verification node has a valid status

  Scenario: verify creates a VERIFIES edge from Verification to Research
    Given I have seeded a research lead for verification
    And a matching citation
    When I call research.verify on that research
    Then a Verification node has a VERIFIES edge to the Research node

  Scenario: verify fails when no citations exist
    Given I have seeded a research lead for verification
    When I call research.verify on that research
    Then the verify result is not ok
    And the evidence-supports-claim check shows n_checked of 0

  # ── research.verify — three-check payload ─────────────────────────────────

  Scenario: verify payload contains exactly three named checks
    Given I have seeded a research lead for verification
    When I call research.verify on that research
    Then the checks dict has exactly the keys evidence-supports-claim, contradiction-cluster, and web-reachability

  # ── research.verify — web-reachability ────────────────────────────────────

  Scenario: web-reachability passes vacuously when no web citations exist
    Given I have seeded a research lead for verification
    And a codebase citation exists
    When I call research.verify on that research
    Then the web-reachability check status is "pass"

  # ── research.ingest_gdoc — source resolution ───────────────────────────────

  Scenario: ingest_gdoc resolves a Google Docs URL to a file_id
    When I call research.ingest_gdoc with a Google Docs URL containing the file id
    Then the result file_id matches the embedded id

  Scenario: ingest_gdoc resolves a Google Drive URL to a file_id
    When I call research.ingest_gdoc with a Google Drive URL containing the file id
    Then the result file_id matches the embedded id

  Scenario: ingest_gdoc resolves a bare file id
    When I call research.ingest_gdoc with a bare file id
    Then the result file_id matches the bare id

  Scenario: ingest_gdoc rejects an invalid source
    When I call research.ingest_gdoc with an invalid source
    Then the result error is "INVALID_SOURCE"

  # ── research.ingest_gdoc — default dest ────────────────────────────────────

  Scenario: ingest_gdoc default dest path is under .agency/sources
    When I call research.ingest_gdoc with a bare file id
    Then the dest path starts with ".agency/sources/gdoc-"

  Scenario: ingest_gdoc explicit dest is preserved
    When I call research.ingest_gdoc with a bare file id and explicit dest ".agency/sources/brief.md"
    Then the dest path is ".agency/sources/brief.md"

  # ── research.ingest_gdoc — dispatch contract ───────────────────────────────

  Scenario: ingest_gdoc dispatch contract action is dispatch_subagent
    When I call research.ingest_gdoc with a bare file id
    Then the result action is "dispatch_subagent"

  Scenario: ingest_gdoc dispatch contract includes required Drive tools and excludes Read/Grep
    When I call research.ingest_gdoc with a bare file id
    Then the tools list includes the four required Drive tools
    And the tools list does not include "Read" or "Grep"

  Scenario: ingest_gdoc dispatch contract prompt mentions the file id and forbids body echo
    When I call research.ingest_gdoc with a bare file id
    Then the prompt contains the file id
    And the prompt forbids echoing the document body
    And the prompt requires a JSON return with path, sha256, and title

  Scenario: ingest_gdoc dispatch contract recommends haiku model
    When I call research.ingest_gdoc with a bare file id
    Then the model recommendation is "haiku"

  # ── research.record_ingested_source — provenance ──────────────────────────

  Scenario: record_ingested_source returns an artefact_id
    When I call research.record_ingested_source with valid metadata
    Then the result carries an artefact_id

  Scenario: record_ingested_source creates an Artefact node with correct properties
    When I call research.record_ingested_source with valid metadata
    Then an Artefact node exists with kind "ingested-source"
    And the Artefact node has the supplied path, bytes, lines, sha256, and title

  Scenario: record_ingested_source serves the intent
    When I call research.record_ingested_source with valid metadata
    Then the Artefact node has a SERVES edge to the intent

  Scenario: record_ingested_source is idempotent on sha256
    When I call research.record_ingested_source twice with the same sha256
    Then both calls return the same artefact_id

  Scenario: record_ingested_source creates distinct artefacts for distinct sha256 values
    When I call research.record_ingested_source twice with different sha256 values
    Then the two artefact_ids are different

  # ── citation type system (Spec 168) ────────────────────────────────────────

  Scenario: citation hash is deterministic for the same url and snippet
    When I compute the citation hash for the same url and snippet twice
    Then both hashes are identical

  Scenario: citation hash differs for different snippets
    When I compute the citation hash for two different snippets at the same url
    Then the hashes differ

  Scenario: backend selection returns duckduckgo without api key
    When I ask for the research backend with no environment variables set
    Then the selected backend is "duckduckgo"

  Scenario: backend selection honours AGENCY_RESEARCH_ANTHROPIC=0 even with a key
    When I ask for the research backend with key set but AGENCY_RESEARCH_ANTHROPIC=0
    Then the selected backend is "duckduckgo"

  # ── web search backend ─────────────────────────────────────────────────────

  Scenario: engine default web search backend is duckduckgo
    When I create a fresh engine with no web_search override
    Then the engine web_search name is "duckduckgo"

  Scenario: engine web_search kwarg overrides the default
    When I create a fresh engine with a stub web search client named "stub"
    Then the engine web_search name is "stub"
