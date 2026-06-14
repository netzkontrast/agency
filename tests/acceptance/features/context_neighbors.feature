Feature: CapabilityContext.neighbors() one-hop edge traversal (Spec 125)
  ctx.neighbors(node_id, edge, direction) exposes one-hop graph traversal inside
  capability verbs, closing the dormant-edge advisory: caps declared edges like
  CHAPTER_OF but verbs fell back to find()+filter. Observable: the returned
  property dicts and their count; direction semantics; limit; empty / unknown cases.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent
    And a novel with two chapters

  Scenario: neighbors returns property dicts in the same shape as find()
    When I traverse CHAPTER_OF edges inward from the novel
    Then 2 property dicts are returned
    And each dict has an id key

  Scenario: default direction is "in" — nodes pointing AT the target
    When I traverse CHAPTER_OF edges from the novel using the default direction
    Then 2 property dicts are returned

  Scenario: direction out finds nodes the source points at
    When I traverse CHAPTER_OF edges outward from a chapter
    Then 1 property dict is returned
    And the returned node id matches the novel

  Scenario: empty result when no matching edges exist
    When I traverse a NONEXISTENT_EDGE from the novel
    Then an empty list is returned

  Scenario: unknown node id returns empty list
    When I traverse CHAPTER_OF from a node id that does not exist
    Then an empty list is returned

  Scenario: invalid direction raises an error
    When I traverse CHAPTER_OF with direction sideways
    Then a ValueError is raised

  Scenario: limit kwarg caps the number of returned rows
    When I traverse CHAPTER_OF with limit 1
    Then at most 1 property dict is returned

  Scenario: neighbors is consistent with find-plus-filter
    When I traverse CHAPTER_OF edges inward from the novel
    And I list chapters using find-plus-filter
    Then both results contain the same chapter ids
