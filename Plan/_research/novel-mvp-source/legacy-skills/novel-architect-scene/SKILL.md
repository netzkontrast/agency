---
name: novel-architect-scene
description: >-
  Scene-Level Sub-Skill von novel-architect. Übernimmt Per-Scene/Per-Moment-
  Detail für Phase 5 (Scene Matrix Detailauflösung) und Phase 6 (Drafting
  Pre-Checks). Stellt das Q1–Q5 Scene-Level-Bridge-Audit bereit (Dramatica-
  Storyform → Szenenarbeit). Trigger: "Scene-Detail", "Moment Audit",
  "Scene-Level-Bridge", Q1-Q5, /novel-draft Pre-Check. Delegiert Storyform-
  Reasoning an dramatica-theory + dramatica-vocabulary.
metadata:
  category: creative-writing
  parent: novel-architect
  version: "1.1.1"
  status: active
  date_added: "2026-05-11"
  date_updated: "2026-05-12"
  state_management: "ncp"
  ncp_schema_version: "1.3.0"
  triggers: >-
    novel-architect-scene, scene-level bridge, scene audit, moment audit,
    Q1-Q5 audit, scene matrix detail, /novel-draft pre-check
  delegates_to: >-
    novel-architect (parent orchestrator), dramatica-theory, dramatica-vocabulary,
    ncp-author
---

# novel-architect-scene v1.1.1

Sub-Skill von [`novel-architect`](../novel-architect/). Übernimmt das
*Scene-Level-Detail* zwischen abstrakter Storyform-Struktur (Phase 2/5
Akt-Ebene) und konkreter Prosa-Generierung (Phase 6 Drafting). Trägt seit
v1.1.1 das volle Q1–Q5-Scene-Level-Bridge-Audit (vom v1.1.0-Stub
graduiert, nachdem Task 075 die Methoden-Bibliothek in v1.1.0 befüllt hat
— die "stub"-Bezeichnung war eine Selbst-Beschränkung der v1.1.0-
Metadaten und wurde in v1.1.1 zurückgezogen, da das Audit tatsächlich
bereits aktiv ist).

## Scope

| Phase | Verantwortung |
|-------|---------------|
| Phase 5 — Scene Matrix (Detail) | Per-Scene-Slot-Befüllung; `moment.id` Generation; storypoint-zu-moment Mapping |
| Phase 6 — Drafting (Pre-Check) | Q1–Q5 Audit pro Moment, bevor Prosa-Generierung startet |

## Verfügbare Methoden

| File | Methode | Status |
|------|---------|--------|
| [`methods/scene-level-bridge.md`](./methods/scene-level-bridge.md) | Q1–Q5 Per-Moment Audit (dominant throughline, signpost timing, conflict flavor, character arc, thematic beat) | **active** (149 LOC; Task 075 closed in v1.1.0; "stub" qualifier dropped in v1.1.1) |

Die Methoden-Bibliothek ist seit v1.1.0 durch [Task 075](../../tasks/075-novel-architect-scene-level-bridge/task.md) populiert. v1.1.1 retired the "stub in v1.1.0" qualifier from the orchestrator's `delegates_to` metadata; the sub-skill is now first-class.

## Delegation Contract

Dieser Sub-Skill schreibt:

- NCP `narratives[].storytelling.moments[]` (Phase 5; über `ncp-author`)
- Workspace-File `scene-matrix.md` Moment-Sektionen (über `render_scene_matrix.py` im Orchestrator)
- Workspace-File `drafts/ch-XX-precheck.md` (Phase 6 Pre-Check Output)

Q1–Q5 Audit-Resolution MUSS gegen `dramatica-theory` reasoniert werden — siehe `skills/dramatica-theory/references/12-scene-level-bridge.md`.

## Constraints

- **First-class seit v1.1.1:** die v1.1.0 "stub"-Selbst-Beschränkung ist zurückgezogen. Phase-5/6 Per-Moment-Arbeit läuft über diesen Sub-Skill via [`methods/scene-level-bridge.md`](./methods/scene-level-bridge.md).
- **Skill ist projekt-agnostisch:** kein Genre/Plot-Default.
- **NCP-Schutz:** `moments[]` werden nur via `ncp-author` geschrieben, nie direkt.

## Integration mit novel-architect

| Skill-Call | Aktion |
|---|---|
| `/novel-scenes` (Phase 5 Detail) | Orchestrator routet Per-Moment-Arbeit zu diesem Sub-Skill |
| `/novel-draft` (Phase 6 Pre-Check) | Orchestrator triggert das Q1-Q5 Audit hier |

## Closing Note

Dieser Sub-Skill ist die **Brücke zwischen Storyform und Prosa**. Er entscheidet
nicht *was* in einer Szene passiert (das tut die Storyform / der Author), sondern
*ob* die geplante Szene mit der Storyform konsistent ist und welche Slots noch
fehlen.
