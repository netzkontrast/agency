---
spec_id: "218"
slug: novel-lifecycle-output-budget
status: draft
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
- [ ] **A full-manuscript fetch captures-and-recalls** (Spec 154) — the
      body is an Artefact with a recall handle, not a context dump.
- [ ] **The prefix (work metadata) is cache-stable** across calls.
- [ ] Test: a 41-chapter list captures-and-recalls; `--fields` projects.
- [ ] TODO row + drift clean.

## Interconnects

- **output-budget chain** (146/154/160).
- Spec 217 (build walkable) consumes the budgeted lists.

## Open questions

1. Chapter-granular or scene-granular recall? **Recommend**: both —
   `recall_overflow(handle, grep="Chapter 12")` slices either.
