Feature: Semantic recall over reflections (reflect.recall_semantic)
  reflect.recall_semantic returns a documented, score-ranked payload over the
  recorded Reflection nodes — the cross-session memory read surface (Spec 045).
  Behaviour only (the tfidf embedder is the default backend).

  Background:
    Given a confirmed intent
    And a few technical and project reflections are recorded

  Scenario: recall_semantic returns the documented payload
    When I semantically recall "fix MCP startup" with k 3
    Then the payload names its embedder
    And every result carries id, score, scope and text with a score in [0,1]

  Scenario: results are ranked by score descending
    When I semantically recall "fix MCP startup" with k 3
    Then the result scores are in descending order

  Scenario: k limits the number of results
    When I semantically recall "fix MCP startup" with k 1
    Then at most 1 result is returned

  Scenario: an empty query returns no results
    When I semantically recall with an empty query
    Then no results are returned
