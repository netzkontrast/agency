Feature: render substrate — docstring slicing and output envelope (Spec 023 / 146 / 154)
  The render substrate cleaves verb docstrings into brief / standard / deep slices
  across surface × depth × format axes. The ResponseEnvelope separates
  per-build prefix from per-call body to enable Claude API prompt caching.

  Scenario: parse_slices extracts brief inputs returns and chain_next from compliant docstring
    When I parse a compliant verb docstring
    Then the brief is the first-paragraph one-liner without newlines
    And inputs contains the declared parameter names
    And returns contains the declared return shape
    And chain_next contains the declared next call

  Scenario: parse_slices returns empty markers for legacy docstring
    When I parse a legacy verb docstring without markers
    Then the brief is the first paragraph
    And inputs returns and chain_next are all empty

  Scenario: render_verb at brief depth shows name role brief only
    When I render a compliant docstring at brief depth
    Then the output contains the verb name and role
    And the output contains the one-line brief
    And the output does not contain Inputs or Returns

  Scenario: render_verb at standard depth adds inputs and returns but not chain_next
    When I render a compliant docstring at standard depth
    Then the output contains Inputs
    And the output contains Returns
    And the output does not contain chain_next

  Scenario: render_verb at deep depth adds chain_next and body
    When I render a compliant docstring at deep depth
    Then the output contains chain_next
    And the output contains the body detail

  Scenario: brief output is significantly smaller than deep output
    When I render a compliant docstring at brief depth
    And I render the same docstring at deep depth
    Then the brief output is less than half the size of the deep output

  Scenario: json format returns a structured dict
    When I render a compliant docstring in json format at standard depth
    Then the result is a dict with name role brief inputs and returns

  Scenario: snippet format returns a code block with named argument keys
    When I render a compliant docstring in snippet format at standard depth
    Then the result contains a code block with call_tool
    And the argument keys are the parsed input names not raw prose

  Scenario: snippet for legacy docstring emits a TODO sentinel not an empty dict
    When I render a legacy docstring in snippet format at standard depth
    Then the snippet contains _TODO and get_schema
    And the call_tool argument is a dict not a set

  Scenario: registered tool descriptions are the brief slice not the full docstring
    Given a fresh agency engine in code-mode
    When a client lists all capability tools
    Then each tool description is the brief slice of its docstring
    And the cumulative tight descriptions are less than half the legacy full-docstring total

  Scenario: ResponseEnvelope merges prefix and body into a flat dict
    When I create an envelope with separate prefix and body
    Then to_dict returns all keys from both halves
    And overlapping keys raise a ValueError

  Scenario: canonical_json places prefix keys before body keys
    When I create an envelope with prefix keys and body keys
    Then canonical_json output has all prefix keys before body keys
    And the serialization is deterministic regardless of insertion order
    And canonical_json uses compact separators

  Scenario: prefix hash changes when prefix changes but not when body changes
    When I create two envelopes with the same prefix but different bodies
    Then the prefix hashes are equal
    When I create two envelopes with different prefixes
    Then the prefix hashes differ

  Scenario: capture_body_overflow returns envelope unchanged when body fits budget
    When I capture body overflow with a budget larger than the body
    Then the returned envelope body is unchanged
    And the overflow handle is None

  Scenario: capture_body_overflow replaces body with overflow shape when over budget
    When I capture body overflow with a budget smaller than the body
    Then the returned envelope body contains _overflow_preview and _overflow_handle
    And the overflow handle reports truncated True
    And the prefix is byte-identical to the original prefix
