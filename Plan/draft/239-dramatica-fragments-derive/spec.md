---
spec_id: "239"
slug: dramatica-fragments-derive
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "129"
depends_on: ["129", "147", "149", "143"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/novel/data/dramatica/ontology.json
  - tests/test_dramatica_fragments_derive.py
---

# Spec 239 — Dramatica fragments: derive + lint coverage

## Why

Spec 129 ships 34 hand-authored fragments out of 304 ontology entries
(11%). Its Slice 2 names "authoring the remaining ~270 entries +
lint enforcement of 'fragment OR placeholder'". With Spec 147 the
remaining fragments can be DRAFTED via the Driver against the
ontology entry's metadata + the existing 34 as exemplars — author
reviews, never auto-canonizes. Spec 143's KP fragments are a worked
overlay precedent.

## Done When

- [ ] **`prompt.draft_fragments(scope) -> DraftFragmentsResult`** where
      `DraftFragmentsResult = {drafted: list[FragmentId], skipped:
      list[(entry_id, reason)], canon_status: Literal["proposal"],
      driver_calls: int, total_tokens: int}` — invariant: every drafted
      fragment lands with `canon_status="proposal"`; the result NEVER
      contains `"canon"`.
- [ ] **Lint: "fragment OR placeholder"** — invariant: for every
      ontology entry `e`, `has_fragment(e) XOR has_placeholder(e)` is
      True; CI gates fail when the XOR breaks. Coverage relation:
      `len(entries_with_fragment) + len(entries_with_placeholder) ==
      total_entries` — never a pinned percentage.
- [ ] **Coverage derived** (Spec 149) — `agency_doctor.fragment_coverage`
      returns `{total, with_fragment, with_placeholder, proposal_count,
      canon_count}` all computed from the live ontology, no constants.
      Invariant: `proposal_count + canon_count == with_fragment`.
- [ ] **Author confirms each proposal** — invariant: a drafted fragment
      stays `proposal` until an explicit `confirm_fragment(id)` call;
      no time-based auto-canonization, no batch-accept.
- [ ] **Byte-stable prompt prefix** (Spec 146) — invariant: the prompt
      bytes for `draft_fragments(scope)` depend only on the ontology
      shape, not on the in-flight proposal set; two runs over the same
      ontology hit identical cache keys.
- [ ] **Failure modes** — Driver unreachable (Spec 147) →
      `Codes.DRIVER_UNAVAILABLE`, drafted list stays empty, lint still
      runs on existing entries; Driver returns invalid fragment schema
      → entry SKIPPED with `Codes.FRAGMENT_INVALID`, never partial-write
      to ontology JSON; ontology file write race → optimistic-lock
      retry, then `Codes.ONTOLOGY_LOCKED` on second failure.
- [ ] Test: drafted fragment lands as proposal; lint trips on a missing
      slot.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  ontology has 34 entries with fragments, 270 without; mocked
        Driver returns valid fragment schemas for all 270
When:   prompt.draft_fragments(scope="all") runs
Then:   result.drafted has 270 items AND
        result.canon_status == "proposal" AND
        agency_doctor.fragment_coverage.proposal_count == 270 AND
        agency_doctor.fragment_coverage.canon_count == 34 AND
        proposal_count + canon_count == with_fragment (invariant)

Given:  one ontology entry has BOTH a fragment AND a placeholder
When:   the lint runs
Then:   Codes.FRAGMENT_XOR_VIOLATED is raised naming the entry id AND
        CI fails — the XOR invariant is the gate
```

## Interconnects

- **LLM-driver chain** (147); Spec 143 is the worked overlay sibling.
- Spec 137 (canon-status) — drafts are `proposal`, not silent canon.
- Spec 146 (output-prefix) — ontology prefix is the byte-stable base.
- Spec 237 (scene-brief cache) — primary consumer of canonized fragments
  as the frozen prefix section.
- Spec 230 (storyform completion) — uses fragments as the rubric source.

## Open questions

1. **Batch size per Driver call.** **Recommend:** ≤20 entries per call
   — fits in the Spec 146 prefix budget with headroom.
2. **Confirmation UX.** Walk-driven or bulk-table? **Recommend:**
   walk-driven via a skill phase; bulk-confirm risks unreviewed canon.
3. **Re-draft on confirm-reject.** Retry with feedback, or skip?
   **Recommend:** one retry with rejection rationale as context; then
   skip with `Codes.FRAGMENT_REJECTED_PERSISTENT`.
