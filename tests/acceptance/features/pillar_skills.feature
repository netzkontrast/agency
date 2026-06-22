Feature: Pillar skills — the concept skills (Spec 375)
  Agency's four concepts include three non-capability pillars: Intent, Lifecycle,
  Memory. They are authored as committed `skill.yaml` of `type: pillar` and
  rendered by `install.generate` — no LLM, deterministic (A7). lifecycle & memory
  render standalone at skills/<name>; the intent pillar augments the existing
  intent CAPABILITY skill with its concept section (rather than clobbering it).

  Scenario: the committed pillar source loads as schema-valid type=pillar skills
    When I load the committed pillar skills
    Then at least one pillar is loaded
    And every loaded pillar is a schema-valid skill of type "pillar"
    And the loaded pillars include "intent", "lifecycle" and "memory"

  Scenario: a non-colliding pillar renders standalone, self-contained
    When the install files are generated
    Then a "skills/lifecycle/SKILL.md" pillar skill is emitted
    And the rendered "lifecycle" pillar declares its name and description in frontmatter
    And the rendered "lifecycle" pillar inlines its overview

  Scenario: the intent pillar augments the intent capability skill without clobbering it
    When the install files are generated
    Then the "skills/intent/SKILL.md" skill keeps its capability verb table
    And the "skills/intent/SKILL.md" skill gains the intent pillar concept section

  Scenario: rendering pillars is deterministic — same source, identical bytes (A7)
    When the install files are generated
    And the install files are generated again
    Then the two "skills/lifecycle/SKILL.md" renders are byte-identical
    And the two "skills/intent/SKILL.md" renders are byte-identical

  # ── Spec 375 Slice 2 — listing integration ───────────────────────────────────

  Scenario: the onboarding payload lists the concept pillars
    When the agency welcome payload is fetched
    Then the welcome payload names every concept pillar

  Scenario: the skill listing includes the concept pillars
    When I list all skills
    Then the listing includes every concept pillar with kind "pillar"

  Scenario: the skill listing can filter to just the pillars
    When I list skills of kind "pillar"
    Then the listing is exactly the concept pillars

