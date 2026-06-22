---
spec_id: "218"
slug: novel-lifecycle-output-budget
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "102"
depends_on: ["102", "146", "154", "160"]
vision_goals: [1]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_lifecycle_budget.py
---

# Spec 218 — novel lifecycle output-budget

## Why

Spec 102 (novel-lifecycle) ships the CRUD pipeline (works, chapters,
scenes). Its list/aggregate verbs (`list_chapters`, manuscript
assembly) return large payloads — a 41-chapter novel's full body is
exactly the high-token output the charter's gap #1 targets. This
applies the output-budget discipline so a wrapping LLM driver never
eats the whole manuscript when it asked for a chapter list.

## Done When

- [ ] **List/aggregate verbs honor the output budget** (Spec 146 prefix
      split + Spec 154 overflow capture + Spec 160 `--fields`).
- [ ] **Typed return shape** for the budgeted list verbs:
      ```python
      BudgetedListResult = {
        "prefix": {                   # cache-stable per work (Spec 146)
          "work_id": str,
          "schema_version": str,
          "capability_set_hash": str,
        },
        "body": {
          "items":        list[dict],   # `--fields`-projected
          "total":        int,
          "shown":        int,
          "overflow_handle": str | None, # Spec 154 recall key
          "next_cursor":  str | None,
        },
      }
      ```
- [ ] **A full-manuscript fetch captures-and-recalls** (Spec 154) — the
      body is an Artefact with a recall handle, not a context dump.
- [ ] **Invariant — prefix byte-stability without metadata change.**
      Two `list_chapters(work_id=X)` calls 60s apart with no work
      mutation MUST return `prefix` byte-identical. CI asserts
      `len(prefix_run1) == len(prefix_run2)` AND `prefix_run1 ==
      prefix_run2`.
- [ ] **Invariant — overflow threshold is RELATIONAL, not pinned.**
      Assert `overflow_handle is not None` whenever
      `len(rendered_body_bytes) > MAX_BODY_BYTES` (configured budget,
      Spec 154). Do NOT pin a chapter count; the threshold is a
      relationship between bytes and the configured cap (CLAUDE.md
      rule 8).
- [ ] **Invariant — recall fidelity.** `recall_overflow(handle).items`
      yields the SAME items, in the same order, as the un-budgeted
      list would (a derived equality check, not a pinned hash).
- [ ] **Invariant — `--fields` projects strictly.** Every dict in
      `body.items` has keys ⊆ requested `fields`; the unprojected
      payload bytes ≥ projected bytes (no padding).
- [ ] **Failure modes**:
      - `Codes.OVERFLOW_HANDLE_MISSING` when caller passes a stale
        handle (Spec 154 GC swept it);
      - `Codes.FIELDS_UNKNOWN` when `--fields` names a key the row
        schema doesn't expose;
      - `Codes.PREFIX_BUDGET_EXCEEDED` propagated from Spec 146 when
        work metadata grows past the prefix cap.
- [ ] Test: a 41-chapter list captures-and-recalls; `--fields` projects;
      stale handle raises typed code; prefix byte-stable across runs.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a novel with 41 chapters and ~180k tokens of body
When:   list_chapters(work_id=X) is called with default budget
Then:   prefix carries the work_id + capability_set_hash
        AND body.items length == 41 (chapter rows, projected)
        AND body.overflow_handle is None (chapter metadata fits)
        AND a second call 60s later returns byte-identical prefix

Given:  assemble_manuscript(work_id=X) called on the same novel
When:   the rendered body exceeds MAX_BODY_BYTES
Then:   body.items is the first N chapters that fit
        AND body.overflow_handle is a recall key
        AND an Artefact(kind="overflow") PRODUCES-from the assemble
            verb invocation
        AND recall_overflow(handle, grep="Chapter 12") returns
            Chapter 12 in full

Given:  list_chapters(..., fields=["title","wc"]) called
When:   the verb returns
Then:   every body.items entry has keys exactly {"title","wc"}
        AND projecting an unknown field returns Codes.FIELDS_UNKNOWN
```

## Failure modes

The Spec 154 overflow store is external state — handle GC, recall
fetch, and `--fields` schema lookup all share its failure surface.
Propagate typed codes; never silently truncate (would partial-cache
under Spec 146). When the wrapping driver re-runs after a refusal,
prefix-cache must hit — assert via `usage.cache_read_input_tokens > 0`
on the second call (per `claude-api` skill).

## Interconnects

- **output-budget chain** (146/154/160).
- Spec 217 (build walkable) consumes the budgeted lists at every
  list-producing phase.
- Spec 222 (catalogue graph-query) shares the same prefix/body
  envelope across the work catalogue.
- Spec 223 (manuscript managed export) consumes the overflow handle
  as the export input — body never crosses back through the LLM.
- Spec 237 (scene-brief cache discipline) honors the same prefix split.
- Spec 257 (managed-cache proof) re-verifies the cache-hit across
  Managed-Agents session boundaries.
- Spec 269 (followup-status derived per spec) reads the same envelope
  for status rollup.

## Open questions

1. Chapter-granular or scene-granular recall? **Recommend**: both —
   `recall_overflow(handle, grep="Chapter 12")` slices either; the
   handle index keys by both `chapter_id` and `scene_id`.
2. Cursor-based pagination on top of overflow capture, or just one or
   the other? **Recommend**: cursor for the prefix/body return,
   overflow for the body when rendered bytes still exceed the cap —
   they compose (cursor is "next N rows", overflow is "the rendered
   bytes of THIS page didn't fit").
3. Per-author MAX_BODY_BYTES override? **Recommend**: defer — global
   cap with author-level override is a Slice-2 if a real author hits
   the cap; v1 keeps one knob.
