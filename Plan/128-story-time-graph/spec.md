---
spec_id: "128"
slug: story-time-graph
status: draft
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["101", "125"]
affects:
  - agency/capabilities/novel/_main.py
  - agency/capabilities/prompt/_main.py
  - tests/test_novel_story_time.py
domain: novel / continuity / time
parent_spec: "101"
mvp-source:
  - "User brainstorm 2026-06-10 (Novelcrafter-parity dynamic prompts)"
  - "Plan/127-dynamic-prompt-assembly/spec.md _continuity carve-out"
---

# Spec 128 — Story-time / narrative-time graph

## Why

Spec 127's `assemble_scene_brief` `_continuity` composer is a placeholder
because the substrate has no way to answer "what HAS happened by the time
this scene takes place?" Story-time is distinct from narrative-time: a
chapter-7 flashback shows chapter-2 events; a chapter-3 foreshadowing
hints at chapter-12 reveals. The agent writing a scene needs both views.

Without this graph, every dynamic prompt leans on the orchestrator (or
the author) to track the timeline mentally — fine for short stories,
broken for long-form.

## Done When

- [ ] **`StoryTimeEvent` node** — `{label, when_story, when_narrative,
      tags}`. `when_story` is a sortable string ("3:14" = act 3, beat 14;
      "1991-04-23" works too); `when_narrative` references the
      revealing scene/chapter. Both can be partial — the schema doesn't
      force a calendar.
- [ ] **`NarrativeBeat` node** — represents a "moment in narrative order"
      independent of any specific scene; lets stories with parallel POVs
      have the same narrative beat across multiple scenes.
- [ ] **3 new edges**:
      - `HAPPENS_AT` — StoryTimeEvent → StoryTimeEvent (chronological
        successor) OR Scene → StoryTimeEvent (this scene depicts this
        event)
      - `REVEALED_IN` — StoryTimeEvent → Scene (when narrative-time is
        when the event is disclosed)
      - `PRECEDES` — NarrativeBeat → NarrativeBeat (narrative-order
        DAG; lets a beat have one predecessor, supports parallel POV)
- [ ] **6 worldbuilding-style verbs**:
      - `record_story_event(novel_id, label, when_story, scene_id=None)`
        — mints StoryTimeEvent; optionally HAPPENS_AT a scene.
      - `reveal_in_scene(event_id, scene_id)` — adds the REVEALED_IN edge
        for foreshadow-then-pay scenarios.
      - `list_story_events_up_to(scene_id)` — returns events whose
        `when_story` is ≤ this scene's anchor (the continuity slice).
      - `list_reveals_in(scene_id)` — events the scene discloses (the
        author's checklist for "is the reveal landing here?").
      - `mark_narrative_beat(scene_id, beat_label, predecessor_id=None)`
        — mints a NarrativeBeat + PRECEDES edge.
      - `narrative_order(novel_id)` — topo-sort over PRECEDES; returns
        the canonical reading order.
- [ ] **`prompt.assemble_scene_brief` upgrade** — `_continuity` composer
      starts using `list_story_events_up_to(scene_id)` once shipped;
      placeholder text is replaced with the actual event list (bounded
      to `section_budget` per the existing truncation contract).
- [ ] Lint clean; drift clean; TODO row.

## Design notes

- `when_story` is a STRING with documented sortability — no Date type,
  no calendar coupling. Sci-fi works use "Y2391.04"; fantasy uses
  "Third Age, year 3019"; mundane fiction uses ISO dates. The author
  picks.
- **No automatic causality inference** — `HAPPENS_AT` is authored, not
  derived. We're a graph for the author's bookkeeping, not a temporal
  reasoner.
- Stretch: `find_continuity_break(scene_id)` — flags events the scene
  references (`reveals_in` claims) that have no `HAPPENS_AT` predecessor
  in the up-to-scope. The "you mentioned this never happened" check.

## Open questions

1. Story-time as plain string (max flexibility) vs ISO date subset
   (sortable but coercion needed)? **Recommend**: string. Sortability
   is the author's responsibility; we sort lexicographically.
2. Should `Scene` get a `story_time` property directly, or always go
   through a HAPPENS_AT edge? **Recommend**: edge — scenes can depict
   MULTIPLE story-events (flashbacks within a scene); a property
   forces a single-event-per-scene shape.

## Followup

(Populated when the PR ships.)
