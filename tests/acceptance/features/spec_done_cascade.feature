Feature: finish_spec — the done-cascade trigger (Spec 388)
  Moving a spec to /done is ONE owner trigger, not a manual six-step dance: it
  syncs the physical Plan/<state>/ folder, the `state:` frontmatter, and the
  SpecLifecycle node, approves the spec's ADR decisions (owner authority), and
  rebuilds architecture.md. The folder is authoritative; the node + ADR steps are
  best-effort so a not-yet-ingested spec still finishes cleanly.

  Background:
    Given a confirmed intent

  Scenario: finishing a draft spec moves it to /done across folder + frontmatter
    Given a draft spec "999-demo" in a temp Plan tree
    When I finish_spec "999" in that tree
    Then the finish result reports moved from "draft"
    And the spec now lives under "done" in the tree
    And the moved spec frontmatter state is "done"
    And the source draft folder is gone

  Scenario: finishing an unknown spec returns a typed error
    Given a draft spec "999-demo" in a temp Plan tree
    When I finish_spec "404" in that tree
    Then the finish result is a typed error
