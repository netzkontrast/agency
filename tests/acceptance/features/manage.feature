Feature: manage capability — generic CRUD over every graph node type (Spec 293)
  The manage capability gives capability-agnostic Create/Read/Update/Amend/Retract
  over any ontology label, completing the write+read management surface of Memory.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: create then read a node of any label
    When I manage.create a "Document" with path "/x.md" and content_sha "deadbeef"
    Then the create result carries an id
    And manage.read on that id reports it live with the path

  Scenario: update mutates a node in place
    Given a managed "Document" node exists
    When I manage.update that node's content_sha to "feedface"
    Then manage.read shows the updated content_sha

  Scenario: list returns live nodes of a label and excludes retracted ones
    Given a managed "Document" node exists
    When I manage.retract that node
    Then manage.read reports it not live
    And manage.list of "Document" does not include that node

  Scenario: amend creates an append-only successor
    Given a managed "Document" node exists
    When I manage.amend that node's content_sha to "0ddba11"
    Then the amend result carries a new id distinct from the old

  Scenario: create rejects an ontology violation by naming it
    When I manage.create a "Document" with no required props
    Then the create result carries an error

  Scenario: state rolls up live counts across the pillars
    Given a managed "Document" node exists
    When I ask manage.state
    Then the state rollup reports at least one intent and the document count

  Scenario: open_intents lists live intents with their SERVES subtree size
    Given a managed "Document" node exists
    When I ask manage.open_intents
    Then open_intents includes the confirmed intent with a positive serves_count

  Scenario: timeline orders an intent's events and invocations
    Given a managed "Document" node exists
    When I ask manage.timeline for the confirmed intent
    Then the timeline lists the create invocation

  Scenario: whats_next surfaces the intent's acceptance as the next action
    When I ask manage.whats_next for the confirmed intent
    Then whats_next echoes the intent acceptance and lists at least one next action

  Scenario: research_state groups leads with their citations
    Given a research lead with one citation exists
    When I ask manage.research_state
    Then research_state totals report at least one lead and one citation
    And research_state lists the lead as pending

  Scenario: render projects the read-API as a markdown dashboard
    Given a managed "Document" node exists
    When I ask manage.render for the confirmed intent
    Then the dashboard markdown has a heading and an open-intents section
    And the dashboard echoes the intent acceptance and a next action

  Scenario: project returns a query-ranked, token-budgeted slice of a label
    Given five managed "Document" nodes exist
    When I project "Document" matching "needle" under a tiny token budget
    Then the projection is truncated under the budget
    And the matching document ranks first in the projection
