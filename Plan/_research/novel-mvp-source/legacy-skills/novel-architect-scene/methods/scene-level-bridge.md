# Method: Scene-Level-Bridge (Q1–Q5)

> **Sub-Skill:** `novel-architect-scene`
> **Load when:** Phase 5 (Scene Matrix Detail) oder Phase 6 (Drafting Pre-Check)
> **Quelle:** [`skills/dramatica-theory/references/12-scene-level-bridge.md`](../../dramatica-theory/references/12-scene-level-bridge.md)
> **Implementiert:** Task 075 (PR-Path)

## §0 Wofür Q1–Q5?

Die Scene-Level-Bridge ist der Audit-Mechanismus, der das *abstrakte Storyform*
(Class/Concern/Issue/Problem) auf eine *konkrete Szene* (POV, Beat, Konflikt-
Geschmack, thematische Aussage) abbildet. Ohne diesen Audit driftet Phase-6-
Prosa in zwei typische Fehler:

1. **Storyform-naive Prosa:** Szene erzählt einen Beat, der nicht auf einen
   Throughline-Signpost zurückverweisbar ist. Folge: Theme verschwimmt.
2. **Theorie-überladene Prosa:** Szene illustriert *die Theorie*, statt eine
   konkrete Handlung zu zeigen. Folge: didaktischer Ton, kein Story-First.

Q1–Q5 sind die fünf Fragen, die pro Moment beantwortet sein MÜSSEN, bevor
Drafting startet. Sie kommen alle fünf aus dem
[`dramatica-theory/references/12-scene-level-bridge.md`](../../../dramatica-theory/references/12-scene-level-bridge.md)
und sind hier in Workflow-Form übersetzt.

## §1 Die fünf Fragen

| ID | Frage | Storyform-Anker |
|----|-------|------------------|
| **Q1** | Welche der vier Throughlines (OS, MC, IC, SS) dominiert in diesem Moment? | `narratives[].subtext.perspectives[].throughline_id` |
| **Q2** | Welcher Signpost / Storybeat ist gerade aktiv? Liegt der Moment im richtigen Akt-Slot? | `narratives[].subtext.storybeats[].signpost_id` |
| **Q3** | Welcher Konflikt-Geschmack treibt die Reibung — Class-Type, Class-Variation, oder Element? | `narratives[].subtext.storypoints[].element_id` |
| **Q4** | Welcher Charakter-Arc-Beat hier? Ist es ein MC-Resolve-Test, IC-Steadfast-Test, oder Relationship-Shift? | `players[].perspectives[].arc_beat_id` |
| **Q5** | Welche thematische Aussage entsteht — und steht sie im Dienst des Themes oder dagegen? | `narratives[].subtext.theme_anchors[]` |

## §2 Audit-Pipeline

```python
def audit_moment(moment: dict, ncp: dict, arch: dict) -> AuditReport:
    """Return per-moment audit covering Q1-Q5."""
    return AuditReport(
        q1=audit_q1_dominant_throughline(moment, arch),
        q2=audit_q2_signpost_timing(moment, ncp),
        q3=audit_q3_conflict_flavor(moment, ncp),
        q4=audit_q4_character_arc(moment, ncp),
        q5=audit_q5_thematic_alignment(moment, ncp),
    )
```

Jeder Sub-Audit returnt eine von drei Verdicten:

- **PASS** — Slot ist gefüllt + konsistent mit Storyform
- **PARTIAL** — Slot ist gefüllt aber inconsistency mit anderem Slot oder NCP
- **MISSING** — Slot ist nicht gefüllt

## §3 Drafting Pre-Check Workflow

Phase 6 (`/novel-draft`) ruft pro Moment **vor** Prosa-Generierung
`audit_moment`. Verdict-Gates:

```
audit = audit_moment(moment, ncp, arch)

if any q.verdict == MISSING:
    block_draft()
    askuser_fill_missing_slots()

if any q.verdict == PARTIAL:
    surface_inconsistency()
    askuser_resolve_or_proceed_with_note

if all q.verdict == PASS:
    proceed_to_draft()
```

Output: `<workspace>/drafts/ch<NN>-precheck.md` (via `render/io_helpers.write_audit_report`).

## §4 Phase-5 Detail-Pass Integration

Phase 5 (Scene Matrix) hat 3 Gates pro
[`phases/phase5-scene-matrix.md`](../../../novel-architect/phases/phase5-scene-matrix.md):

| Gate | Granularität | Q-Audit-Coverage |
|------|--------------|-------------------|
| 5.A | Akt-Block (4 Akte mit Themen + Sub-Concerns) | Q2 (Signpost-Allokation pro Akt) |
| 5.B | Kapitel-Plan (40 Kapitel mit POV, Storybeat, Storypoint) | Q1, Q2, Q3 |
| 5.C | Per-Moment-Detail | Q1–Q5 vollständig (Pre-Drafting-Ready) |

Dual-storyform-Projekte: Q1–Q5 müssen pro Narrative parallel beantwortet
werden, sonst entsteht Drift wie in AP-9.

## §5 NCP-Integration

Q1–Q5 mappen auf konkrete NCP-Slots:

```yaml
# Beispiel: moment "moment_ch12_a_s03" mit Q-Audit-Resolution
moment:
  id: moment_ch12_a_s03
  # Q1: dominant throughline
  dominant_throughline: mc
  # Q2: signpost + timing
  signpost_ref: signpost_act2_mc
  # Q3: conflict flavor (resolved via nav.py by-id)
  storypoint_element_id: element.test
  # Q4: character arc
  character_arc_beat: arc_mc_resolve_test_3
  # Q5: thematic anchor
  theme_anchor_ref: theme_anchor_2
```

Mapping wird via `ncp-author` geschrieben (AGENTS.md Rule NO.2 — kein direct
hand-edit). Pro `references/ncp-integration-contract.md` §5, Phase 5 schreibt
`narratives[].subtext.storypoints[]`, `storybeats[]`, und
`narratives[].storytelling.moments[]`.

## §6 Acceptance Scenarios (Normativ)

```gherkin
Feature: Drafting waits for Q1-Q5 audit pass

  # anchor: T075.SLB.1
  Scenario: Drafting blocks on missing Q-slot
    Given a moment exists in NCP with all Q1-Q4 slots filled but Q5 (theme_anchor_ref) empty
    When /novel-draft fires for that chapter
    Then audit_moment MUST return q5.verdict == MISSING
    And the pre-check report MUST surface the missing slot
    And drafting MUST NOT proceed until Q5 is filled OR the user explicitly accepts the gap with a notes.md entry

  # anchor: T075.SLB.2
  Scenario: Partial inconsistency surfaces for review
    Given Q1.dominant_throughline = "mc" AND Q2.signpost_ref points at an OS signpost
    When audit_moment runs
    Then audit MUST return q1.verdict == PARTIAL with cross-link to q2 inconsistency
    And the user MUST resolve (either change Q1 to OS or change Q2 to an MC signpost)

  # anchor: T075.SLB.3
  Scenario: Dual-storyform requires per-narrative audit
    Given dramatica_storyform_count == "dual"
    And only narratives[0].moment fields are Q-audited
    When /novel-draft fires
    Then the pre-check MUST emit AP-9 + MUST require narratives[1] moment audit
    And drafting MUST NOT proceed with single-narrative coverage
```

## §7 Open Questions (Sequel)

- Q1-Q5 als `tools/check-scene-audit.py` CLI-Linter implementieren? — Sequel-Task.
- Per-Throughline-Audit-Templates für unzuverlässige Erzähler (mosaic POVs)?
- Auto-Generation der Q1-Q4-Vorschläge aus storypoint + storybeat? — wenn ja, askuser nur für Q5.
