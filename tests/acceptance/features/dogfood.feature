Feature: dogfood capability — graph-native ledgers, export/import, amendment pipeline
  The dogfood capability records observations as Reflection nodes (Spec 017),
  exports and replays the graph (Spec 020), and classifies + applies spec
  amendments from accumulated observations (Spec 150).
  All assertions are on observable verb outputs and graph state only.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  # ── dogfood.note ──────────────────────────────────────────────────────────

  Scenario: note records a Reflection with plan_slug
    When I call dogfood.note with observation "dispatch hardcodes driver" and plan_slug "040-test"
    Then the response contains a reflection_id
    And the Reflection node in the graph has the plan_slug "040-test"
    And the Reflection node has scope "observation"

  Scenario: note links the Reflection to the intent via SERVES
    When I call dogfood.note with observation "some observation" and plan_slug "017-test"
    Then a SERVES edge connects the Reflection to the intent

  # ── dogfood.render ────────────────────────────────────────────────────────

  Scenario: render returns markdown containing the recorded observations
    Given two observations noted under plan_slug "048-test"
    When I render plan_slug "048-test"
    Then the content contains "# DOGFOOD-NOTES"
    And the content contains both observation texts

  Scenario: render returns clean markdown for an unknown plan_slug
    When I render plan_slug "999-nonexistent"
    Then the content includes the plan_slug
    And the content indicates no observations yet

  Scenario: render scopes output to the requested plan_slug
    Given one observation under plan_slug "plan-A" and one under "plan-B"
    When I render plan_slug "plan-A"
    Then the content contains the plan-A observation
    And the content does not contain the plan-B observation

  Scenario: render is pure — it does not write new Reflection nodes
    Given one observation under plan_slug "pure-test"
    When I render plan_slug "pure-test"
    Then the Reflection count in the graph is unchanged

  Scenario: render caps output at the token budget
    Given 30 large observations under plan_slug "big-plan"
    When I render plan_slug "big-plan" with max_tokens 500
    Then the returned token count is within budget
    And the response reports omitted observations

  # ── dogfood.collect ───────────────────────────────────────────────────────

  Scenario: collect parses observations from DOGFOOD-NOTES.md files
    Given a plan tree with a DOGFOOD-NOTES.md containing 3 entries
    When I collect from that plan tree
    Then the collect result count is 3
    And the plans list contains the plan subdirectory name
    And the texts list matches the observation texts

  Scenario: collect returns empty when the plan directory does not exist
    When I collect from a non-existent directory
    Then the collect result count is 0
    And the warnings mention the missing directory

  Scenario: collect skips plan subdirectories without DOGFOOD-NOTES.md
    Given a plan tree where one subdirectory has DOGFOOD-NOTES.md and one does not
    When I collect from the mixed plan tree
    Then only the subdirectory with the file appears in the plans list

  # ── dogfood.export ────────────────────────────────────────────────────────

  Scenario: export writes a well-formed JSON file
    When I export the graph to a file
    Then the file exists and parses as JSON
    And the JSON has keys "version", "nodes", and "edges"

  Scenario: export response carries path, node count, edge count and byte count
    When I export the graph to a file
    Then the response has "path", "nodes", "edges", and "bytes" fields

  Scenario: export captures Reflection nodes with their properties
    Given a noted observation "round-trip text" under plan_slug "rt"
    When I export the graph to a file
    Then the exported JSON contains a Reflection node with text "round-trip text"

  Scenario: export captures Intent nodes with owner and parent_intent_id
    Given a child intent under the confirmed intent
    When I export the graph to a file
    Then the exported JSON includes the child intent with its owner and parent_intent_id

  Scenario: export captures graph edges
    Given a noted observation under plan_slug "edge-test"
    When I export the graph to a file
    Then the exported edges include at least one of SERVES or OBSERVED_DURING

  Scenario: export is pure — it does not write Reflection or Intent nodes
    Given a noted observation under plan_slug "purity"
    When I export the graph to a file
    Then the Reflection count and Intent count are unchanged after export

  Scenario: two exports in quick succession produce distinct file paths
    When I export the graph twice with no explicit path
    Then the two export paths differ

  # ── dogfood.import ────────────────────────────────────────────────────────

  Scenario: import returns counts and version
    When I export then import into a fresh engine
    Then the import response has "imported_nodes", "imported_edges", and "version" fields
    And at least one node is imported

  Scenario: import rejects an unknown version
    When I import a JSON file with version 999
    Then a ValueError mentioning "version" is raised

  Scenario: import raises FileNotFoundError for a missing file
    When I import a non-existent file path
    Then a FileNotFoundError is raised

  Scenario: import preserves node ids from the source graph
    Given a noted observation "round-trip text" under plan_slug "rt"
    When I export then import into a fresh engine
    Then every source node id is present in the fresh graph

  Scenario: import preserves Reflection properties
    Given a noted observation "preserve me" under plan_slug "020-prop"
    When I export then import into a fresh engine
    Then the fresh graph contains a Reflection with text "preserve me" and the plan_slug "020-prop"

  Scenario: import recreates edges between nodes
    When I export then import into a fresh engine
    Then the fresh graph contains SERVES or OBSERVED_DURING edges

  Scenario: round-trip export → import → re-export preserves all node ids
    Given two noted observations for round-trip
    When I export, import into a fresh engine, then re-export
    Then every original node id appears in the re-exported JSON

  Scenario: import advances the logical clock beyond imported timestamps
    When I export then import into a fresh engine
    Then the fresh engine's next tick exceeds the maximum vfrom seen in the import

  # ── dogfood.parse_amendment (Spec 150 Slice 1) ───────────────────────────

  Scenario: parse_amendment returns an empty proposal list when no reflections exist
    When I call parse_amendment with default args
    Then the proposals list is empty

  Scenario: parse_amendment keyword path classifies a proposal-shaped observation
    Given a proposal-shaped observation and a neutral observation recorded
    When I call parse_amendment with default args
    Then at least one proposal is returned
    And each proposal has the required ProposalPayload fields
    And each proposal's source_reflections is non-empty
    And each proposal's confidence is in [0, 1]

  Scenario: neutral observations yield no proposals
    Given two neutral observations recorded
    When I call parse_amendment with default args
    Then the proposals list is empty

  Scenario: scope parameter filters proposals by plan_slug
    Given a proposal observation for plan "146" and one for plan "147"
    When I call parse_amendment scoped to "146"
    Then the proposals only reference spec_id "146"
    And spec_id "147" is absent

  Scenario: limit caps the number of returned proposals
    Given 5 proposal-shaped observations each referencing a different spec
    When I call parse_amendment with limit 2
    Then at most 2 proposals are returned

  Scenario: LLM classifier is used when an Anthropic driver is wired
    Given two seeded reflections and a capable Anthropic driver stub
    When I call parse_amendment with default args
    Then the response classifier is "llm"
    And the driver was called exactly once

  Scenario: keyword fallback when driver backend is "none"
    Given two seeded reflections and a no-backend driver stub
    When I call parse_amendment with default args
    Then the response classifier is "keyword"

  Scenario: prefer_delegate emits an llm_delegate envelope
    Given two seeded reflections and a no-backend driver stub
    When I call parse_amendment preferring delegation
    Then the response classifier is "llm-delegate"
    And the response kind is "llm_delegate"
    And the request envelope carries messages and output_schema
    And the proposals list is empty

  Scenario: host_completion resume path classifies proposals as "host"
    Given two seeded reflections and a pre-built host_completion payload
    When I call parse_amendment with the host_completion payload
    Then the response classifier is "host"
    And at least one proposal is returned

  Scenario: hallucinated reflection ids are dropped
    Given two seeded reflections and a driver stub returning a ghost reflection id
    When I call parse_amendment with default args
    Then the proposals list is empty

  Scenario: use_llm false forces the keyword path even with a capable driver
    Given two seeded reflections and a capable Anthropic driver stub
    When I call parse_amendment with use_llm false
    Then the response classifier is "keyword"
    And the driver was not called

  Scenario: driver exception degrades gracefully to keyword classifier
    Given two seeded reflections and a driver stub that raises on complete
    When I call parse_amendment with default args
    Then the response classifier is "keyword"

  Scenario: host_completion with invalid op is dropped
    Given two seeded reflections and a host_completion with op "delete-everything"
    When I call parse_amendment with the host_completion payload
    Then the proposals list is empty

  Scenario: host_completion with invalid section is dropped
    Given two seeded reflections and a host_completion with section "Random Made Up Section"
    When I call parse_amendment with the host_completion payload
    Then the proposals list is empty

  Scenario: host_completion with confidence outside [0, 1] is dropped
    Given two seeded reflections and a host_completion with confidence 5.0
    When I call parse_amendment with the host_completion payload
    Then the proposals list is empty

  Scenario: host_completion with short rationale is dropped
    Given two seeded reflections and a host_completion with a rationale shorter than 40 chars
    When I call parse_amendment with the host_completion payload
    Then the proposals list is empty

  Scenario: driver-returned spec_id mismatching the reflection's plan_slug is dropped
    Given two seeded reflections and a driver stub returning spec_id "999" for a "146" reflection
    When I call parse_amendment with default args
    Then the proposals list is empty

  Scenario: driver-omitted spec_id is derived from the reflection's plan_slug
    Given two seeded reflections and a driver stub returning an empty spec_id for a "146" reflection
    When I call parse_amendment with default args
    Then the proposal's spec_id is "146"

  # ── dogfood.apply_amendment (Spec 150 Slice 1) ───────────────────────────

  Scenario: apply_amendment dry-run returns a unified diff
    When I call apply_amendment in dry-run mode with a valid payload
    Then the response contains a "diff" field with "---" and "+++" markers

  Scenario: apply_amendment dry-run records a provenance Artefact
    Given two cited Reflection nodes
    When I call apply_amendment citing those reflections in dry-run mode
    Then an Artefact of kind "amendment-proposal" is recorded
    And PRODUCES_FROM edges connect the Artefact to each cited Reflection

  Scenario: apply_amendment dry-run does not write the spec file
    When I call apply_amendment in dry-run mode with a valid payload
    Then no "written_path" is returned

  Scenario: apply_amendment with a non-existent spec_id raises AMENDMENT_BAD_SPEC
    When I call apply_amendment with spec_id "9999" in dry-run mode
    Then an exception containing "AMENDMENT_BAD_SPEC" is raised

  Scenario: apply_amendment with no source reflections raises AMENDMENT_NO_SOURCE
    When I call apply_amendment with empty source_reflections in dry-run mode
    Then an exception containing "AMENDMENT_NO_SOURCE" is raised

  Scenario: apply_amendment with a short rationale raises AMENDMENT_VAGUE
    When I call apply_amendment with short rationale in dry-run mode
    Then an exception containing "AMENDMENT_VAGUE" is raised

  Scenario: apply_amendment live-write without a matching confirm_token raises
    When I call apply_amendment with dry_run false and a wrong confirm_token
    Then an exception mentioning "confirm_token" or "amendment_unconfirmed" is raised

  Scenario: apply_amendment live-write folds the amendment into the spec file
    Given a temp spec file with a Done-When section
    When I apply a live amendment with the matching confirm_token
    Then the spec file gains the new Done-When bullet
    And the response carries a written_path

  # ── reflect.batch_note ────────────────────────────────────────────────────

  Scenario: batch_note records one Reflection per text
    When I call reflect.batch_note with two texts
    Then the batch response count is 2
    And 2 Reflection nodes exist in the graph

  Scenario: batch_note skips empty and None texts
    When I call reflect.batch_note with one real text one empty string and one None
    Then the batch response count is 1

  Scenario: batch_note with an invalid scope raises a ValueError
    When I call reflect.batch_note with an invalid scope
    Then a ValueError mentioning "scope" is raised

  # ── jules-self-improvement skill ──────────────────────────────────────────

  Scenario: skill walk chains collect into batch_note and records both observations
    Given a plan tree with two DOGFOOD-NOTES.md observations
    When I walk the jules-self-improvement skill through both phases
    Then both observation texts appear as Reflection nodes in the graph

  # ── dogfood spec lifecycle verbs ─────────────────────────────────────────

  Scenario: spec_status returns on-disk spec details
    When I call spec_status for spec "003"
    Then the status result shows spec_id "003" on disk
    And the status field is "drafted"

  Scenario: spec_status returns shipped for archived spec
    When I call spec_status for spec "146"
    Then the status result shows spec_id "146" as shipped
    And on_disk is false

  Scenario: spec_status returns unknown for nonexistent spec
    When I call spec_status for spec "9999"
    Then the status result shows status "unknown"

  Scenario: specs lists all on-disk plan directories
    When I call specs with no filter
    Then the specs list has more than 100 entries
    And every entry has spec_id slug and status fields

  Scenario: spec_refs finds code references to a known spec
    When I call spec_refs for spec "150"
    Then the refs list is non-empty
    And every ref has file line and text fields
