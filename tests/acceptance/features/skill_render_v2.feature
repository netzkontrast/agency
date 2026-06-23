Feature: Per-type skill rendering (Spec 373)
  One renderer (`render_typed_skill`) renders any v2 Skill self-contained (A1) via
  its `render/skill/<type>.md` template — pillar / capability / discipline each get
  their type's required sections from the Skill schema (371). The description is
  the AUTHORED field (no first-sentence truncation), the render is deterministic
  (A7 — same skill ⇒ byte-identical), and the apologetic `_(Tier B…)_` stub no
  longer ships to disk (a marker-less verb is a lint finding, Spec 377).

  Scenario: a capability-type skill renders its data sections
    When I render a capability-type v2 skill
    Then the rendered skill heads with "capability" and inlines its overview and example

  Scenario: a discipline-type skill renders its rationalization table
    When I render a discipline-type v2 skill
    Then the rendered skill heads with "discipline" and inlines its common-mistakes table

  Scenario: a pillar-type skill renders via the pillar template
    When I render a pillar-type v2 skill
    Then the rendered skill heads with "pillar"

  Scenario: the renderer uses the authored description, not a truncated sentence
    When I render a v2 skill with a multi-sentence description
    Then the full authored description survives in the frontmatter

  Scenario: the per-type render is deterministic (A7)
    When I render a capability-type v2 skill
    Then rendering the same skill again yields byte-identical output

  Scenario: no apologetic Tier-B stub ships in any committed skill
    Then no committed SKILL.md contains the Tier-B apologetic stub
