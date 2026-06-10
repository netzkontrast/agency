---
spec_id: "159"
slug: dogfood-collect-deprecation-llm-classify
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "017"
depends_on: ["017", "150", "045", "147"]
vision_goals: [7, 6]
affects:
  - agency/capabilities/dogfood/_main.py
  - tests/test_dogfood_collect_removal.py
---

# Spec 159 — Retire dogfood.collect; LLM-classify on ingest

## Why

Spec 017 shipped `dogfood.note` / `dogfood.render` (graph-native) and
DEPRECATED `dogfood.collect` (the markdown-parse-into-nodes anti-pattern
that violates Goal 7) — but kept it "for backward compat + Spec 014
pipeline". Spec 150 now provides the Spec-014 pipeline natively, so the
last reason to keep `collect` is gone. This spec removes it and, in the
same move, upgrades `dogfood.note` to optionally LLM-classify the note's
scope on write (Spec 147) so Reflections land pre-tagged for Spec 150's
classifier.

## Done When

- [ ] **`dogfood.collect` removed** — no caller remains (Spec 150 closed
      the pipeline use; Spec 159 confirms zero references via a derived
      grep).
- [ ] **`dogfood.note` gains optional `auto_scope=True`** — when set
      and `[anthropic]` present, the Spec 147 Driver classifies the note
      into a scope enum (observation/proposal/refinement) with
      `output_config.format`; degrades to the caller-supplied scope.
- [ ] **No markdown is parsed into nodes anywhere** — the Goal-7
      violation is fully closed (assert via an architecture check, Spec
      157).
- [ ] Test: `collect` is gone (import-level); `note(auto_scope=True)`
      tags scope via a mocked Driver.
- [ ] TODO row + drift clean.

## Interconnects

- **Dogfood-loop chain** (150): pre-tagged Reflections sharpen the
  classifier.
- **LLM-driver chain** (147): the auto-scope engine.
- Spec 017 is the parent; Spec 157 (architecture gate) enforces the
  no-markdown-parse invariant.

## Open questions

1. Hard-remove `collect` or tombstone with a `DEPRECATED` raise?
   **Recommend**: tombstone one cycle (raise with a pointer to `note`),
   then hard-remove — matches the alias-and-deprecate doctrine.
