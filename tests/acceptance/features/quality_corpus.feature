Feature: paired decidable corpus + coverage matrix (Spec 383 Slice 2)

  Every DECIDABLE decay risk (one whose `decidable` array maps an analyze rule-id)
  is grounded by a PAIRED fixture: a positive that trips it (the symptom IS flagged
  with the right risk code + a complete Iron Law) and a negative "What Not to Flag"
  guard (the symptom-shaped-but-legitimate case is NOT flagged). Fixtures are real
  compilable code generated from the LIVE thresholds (rule 8 — no frozen snapshot),
  asserted via the structured Finding (Adzic — not prose Givens). The judgment-only
  risks are the `-m wet` corpus (Slice 2b). Coverage is a DERIVED invariant: every
  decidable risk has both halves, and all six modes run a decidable scan.

  Background:
    Given an engine and confirmed intent

  Scenario Outline: <risk> flags its positive fixture and spares its negative
    When the "<risk>" decidable corpus is reviewed
    Then the positive fixture raises an "<risk>" Finding with Source, Consequence, and Remedy
    And the negative fixture raises no "<risk>" Finding

    Examples:
      | risk |
      | R1   |
      | R4   |
      | R5   |

  Scenario: every decidable risk in the registry has paired corpus coverage
    Then every decidable risk is covered by a positive and a negative fixture

  Scenario: all six quality modes run a decidable scan
    Then each of the six modes flags the long-function symptom
