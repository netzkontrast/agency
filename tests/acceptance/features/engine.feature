Feature: engine substrate — monitor channel, wire unwrap, lifespan, typed shapes (Spec 012 / 019 / 021 / 059 / 146 / 171 / 175 / 176)
  The engine owns the monitor channel, implements the output-unwrap contract,
  and wires the Jules lifespan. Typed shapes enforce enum and domain invariants
  at construction time. ToolResult supports success/failure constructors with
  Registry.invoke stamping the trace_id.

  Scenario: MonitorEvent serializes to a single JSON line and round-trips
    When I create a MonitorEvent and serialize it
    Then the JSON line contains no newlines
    And deserializing it returns an equal event

  Scenario: emitter appends JSONL lines in order
    When I emit two monitor events to a log file
    Then the log file contains exactly two lines
    And the first line has the first event's message
    And the second line has the second event's kind

  Scenario: emitter rotates log at the configured byte threshold
    When I emit many events to a log with a small rotation threshold
    Then the .1 backup file is created
    And the live log file stays near the threshold size

  Scenario: emitter truncates long messages to the 4096-byte POSIX atomic limit
    When I emit a MonitorEvent with a 10000-character message
    Then the log line is at most 4096 bytes
    And the line is still valid JSON

  Scenario: resolve_monitor_log_path prefers explicit path then env then db sibling
    When I resolve the monitor log path with an explicit path set
    Then the result is the explicit path
    When I resolve with only AGENCY_MONITOR_LOG set
    Then the result is from the env var

  Scenario: engine owns a MonitorEmitter instance
    Given a fresh agency engine in code-mode
    Then the engine has a monitor attribute that is a MonitorEmitter

  Scenario: dict-wrapped internal result unwraps at the wire then re-wraps for MCP
    Given a fresh engine with confirmed intent for wire tests
    When I call reflect.recall via the wire
    Then the wire result has a result key containing a list

  Scenario: scalar-wrapped internal result stays wrapped at the wire
    Given a fresh engine with confirmed intent for wire tests
    When I call reflect.note via the wire
    Then the wire result has a result key containing a string starting with reflection:

  Scenario: rich-dict internal result passes through at the wire unchanged
    Given a fresh engine with confirmed intent for wire tests
    When I call dogfood.note via the wire
    Then the wire result has reflection_id and plan_slug keys
    And the wire result does not have a result key

  Scenario: build_mcp wires a non-default lifespan onto the FastMCP server
    Given a fresh agency engine in code-mode
    When I build the MCP server
    Then the lifespan is not the FastMCP default no-op lifespan

  Scenario: engine lifespan attaches the Jules watcher on enter
    Given a fresh agency engine in code-mode
    When I enter the engine lifespan
    Then _jules_watcher is attached to the engine
    And the watcher task is running

  Scenario: engine lifespan cancels the watcher task on exit
    Given a fresh agency engine in code-mode
    When I enter and then exit the engine lifespan
    Then the watcher task is done after exit

  Scenario: ToolResult.success returns ok True with data
    When I construct a ToolResult.success with data and warnings
    Then ok is True and data matches and warnings are set and error is None

  Scenario: ToolResult.failure returns ok False with a TypedError
    When I construct a ToolResult.failure with UNSUPPORTED code
    Then ok is False and error.code is unsupported and trace_id is empty

  Scenario: Registry.invoke stamps the error trace_id when verb omits it
    Given a fresh engine with a failure capability and confirmed intent
    When the verb is invoked via the registry
    Then the Invocation node has outcome failed
    And the Invocation carries the error code

  Scenario: GuardFinding rejects empty verb_id
    When I create a GuardFinding with empty verb_id
    Then a ValueError is raised

  Scenario: GuardFinding rejects invalid severity
    When I create a GuardFinding with severity bogus
    Then a ValueError is raised

  Scenario: CapabilityRow rejects a negative verb count
    When I create a CapabilityRow with verb_count -1
    Then a ValueError is raised

  Scenario: IntentCapture rejects an invalid source
    When I create an IntentCapture with source bogus
    Then a ValueError is raised

  Scenario: IntentCapture rejects negative turns
    When I create an IntentCapture with turns -1
    Then a ValueError is raised

  Scenario: branch.commit_smart infers type and scope from changed paths
    Given a fresh engine with micro-extension intent
    When I invoke branch.commit_smart with summary Add the parser and path agency/capabilities/analyze/_main.py
    Then the commit message is feat(analyze): add the parser
    And type is feat and scope is analyze

  Scenario: develop.estimate is monotonic in size and deterministic
    Given a fresh engine with micro-extension intent
    When I estimate a small change at loc 20 files 1 tests 1
    And I estimate a large change at loc 800 files 12 tests 10
    Then the small change has bucket S and the large change has bucket XL
    And the large change has more points than the small change
    And the same inputs yield the same estimate
