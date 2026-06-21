---
spec_id: "207"
slug: music-lifecycle-output-budget
status: draft
state: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "094"
depends_on: ["094", "146", "154", "160", "206", "210", "214"]
vision_goals: [1]
affects:
  - agency/capabilities/music/_main.py
  - agency/capabilities/music/clusters/lifecycle.py
  - tests/test_music_lifecycle_budget.py
---

# Spec 207 — music lifecycle output-budget + cluster-file split

## Why

Spec 094 (music-lifecycle) ships the CRUD pipeline but stays Partial —
"per-cluster verb migration to `clusters/*.py` modules" deferred, and
its list verbs (`list_albums`, `list_tracks`, `album_progress`) can
return large payloads with no budget. The catalogue-listing verbs are
exactly the high-token output the charter's gap #1 targets. This
applies the output-budget discipline and lands the deferred file-split.

## Done When

- [ ] **`list_*` / `*_progress` verbs honor the output budget** —
      payload routes through Spec 146 (`ResponseEnvelope{prefix, body}`)
      with the per-call `intent_id`/timestamps in `body`, and overflow
      captures into a graph node via Spec 154 with a `next_cursor`.
      Typed return: `ListResult = {items: list[ItemRef], next_cursor: str | None,
      truncated: bool, recall_handle: NodeId | None, total_count: int}`.
- [ ] **`--fields` projection (Spec 160)** is honored on every list verb —
      callers select the projection; the unselected columns never enter
      the prefix or body.
- [ ] **The deferred `clusters/lifecycle.py` split lands** (094's
      standing migration) — verbs move out of `_main.py` into the
      cluster module; the public registry surface is unchanged.
- [ ] **094 row flips toward Shipped** once the split + budget land.
- [ ] **TODO row + drift clean.**

## Measurable invariants (relationships, not pinned counts)

- **Capture-and-recall round-trip** — for any list of size `N`, the
  total tokens emitted across the initial response + `recall_handle`
  read satisfy `emitted_tokens_initial <= MAX_BODY_TOKENS` (Spec 154
  budget, derived from config) AND a full recall reconstructs the
  same `N` items in the same order.
- **Prefix stability** — `envelope.prefix` bytes are identical between
  two `list_albums()` calls separated by 60s while the capability set is
  unchanged (Spec 146 invariant applied to a music verb).
- **Field projection monotonicity** — `len(item.keys())` returned with
  `--fields=a,b` ≤ `len(item.keys())` returned without (no expansion);
  every requested field must be present (no silent drop).
- **Cluster surface equivalence** — `set(registry.verbs("music.lifecycle"))`
  before and after the file split is identical (the migration is a
  rename, not a deletion).

## Worked example (Given/When/Then)

```text
Given:  100 albums in the graph, MAX_BODY_TOKENS=2000, --fields=id,title
When:   music.list_albums(fields=["id","title"])
Then:   returns ListResult with truncated=True
        AND recall_handle points at a graph node SERVING the caller intent
        AND analyze.graph_query(recall_handle) yields all 100 albums in order
        AND second call's envelope.prefix is byte-identical to the first
```

## Failure modes (Nygard)

| Failure | Verb response |
|---|---|
| Body exceeds `MAX_BODY_TOKENS` mid-serialization | typed truncation: emit `next_cursor` + write `recall_handle`; never silently drop |
| Prefix budget exceeded (capability set grew past Spec 146 limit) | `Codes.PREFIX_BUDGET_EXCEEDED` — never partial-cache |
| `--fields` names a column that doesn't exist | typed `BAD_REQUEST{detail:"unknown_field"}`; never silently ignore |
| Graph offline at recall-handle write | typed failure; the verb does NOT return partial data without a recall handle |
| Migration leaves a verb registered twice (split race) | install-time lint fails (Spec 054 drift check) |

## Interconnects

- **output-budget chain** (146/154/160) — anchors the music slice of it.
- Spec 206 (produce-album walk) consumes `list_albums`/`list_tracks` as
  the lifecycle phase's enumerative steps; budgets must agree.
- Spec 210 (catalogue graph-query) is the sibling list-verb consumer —
  shares the `ListResult` typed shape.
- Spec 214 (derived music config) reports `MAX_BODY_TOKENS` as a derived
  doctor field so users can audit the budget.
- Unblocks the batched cluster-file split (TODO row 129 note).

## Open questions

1. Split all clusters here or just lifecycle? **Recommend**: lifecycle
   first (it carries the migration); siblings split in their own
   enhancement (208-213).
2. Where does the lifecycle module's `clusters/__init__.py` sit relative
   to existing music sub-packages? **Recommend**: `agency/capabilities/music/
   clusters/lifecycle.py`; registry auto-discovers like top-level caps —
   no new wiring (the drop-in-capability bar).
3. Cursor encoding? **Recommend**: opaque base64-wrapped graph
   `(node_id, offset)` tuple — never expose row offsets directly, so
   future re-orderings don't break in-flight cursors.
