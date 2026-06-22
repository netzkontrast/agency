---
spec_id: "159"
slug: dogfood-collect-deprecation-llm-classify
status: draft
state: inprogress
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
      Returns typed `NoteResult{node_id: NodeId, scope: Scope,
      scope_source: Literal["caller", "classifier", "default"],
      confidence: float | None}`.
- [ ] **No markdown is parsed into nodes anywhere** — the Goal-7
      violation is fully closed (assert via an architecture check, Spec
      157).
- [ ] **Measurable invariants** (rule 8):
      (a) `grep -rn "dogfood.collect\|from agency.*collect" agency/
      tests/` returns zero hits on `main` — derived check, monotone;
      (b) `set(Scope) == {"observation", "proposal", "refinement"}` —
      classifier output ⊆ closed enum (any other value fails parse);
      (c) classifier path falls back deterministically — when
      `[anthropic]` missing, `scope_source == "default"` AND `confidence
      is None` (no silent misbranding);
      (d) the no-markdown-parse architecture rule (Spec 157) is
      asserted across `agency/` — invariant zero parser sites.
- [ ] Test: `collect` is gone (import-level); `note(auto_scope=True)`
      tags scope via a mocked Driver; fallback path returns
      `scope_source="default"` when Driver unavailable.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  dogfood.note(text="research.fetch returned 12k tokens — should we
        cap at 4k by default?", auto_scope=True) with `[anthropic]` installed
When:   the Spec 147 Driver classifies via output_config.format
Then:   NoteResult{node_id="ref_abc", scope="proposal",
        scope_source="classifier", confidence=0.87};
        Reflection(scope="proposal") SERVES the active intent;
        Spec 150 ingests it as an amendment candidate

Given:  same call with `[anthropic]` extra NOT installed
When:   dogfood.note(text=..., auto_scope=True)
Then:   NoteResult{scope="observation", scope_source="default",
        confidence=None} — never silently mis-classified
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Driver hallucinates a non-enum scope | classifier returns "idea" not in Scope | invariant (b) — parse rejects | typed Codes.NOTE_SCOPE_INVALID; fall back to default scope + Reflection noting the rejection |
| Silent classifier downgrade | API quota / network hiccup | typed `scope_source` field | caller sees `scope_source != "classifier"`; can retry deliberately |
| Cost blow-up on every note | every note hits the API | `auto_scope=True` is opt-in, never default | per-session budget; surface tokens-spent in Reflection metadata |
| Caller passes both scope= and auto_scope=True | ambiguity | reject at parse with Codes.NOTE_SCOPE_CONFLICT | caller chooses one; classifier path requires absence of `scope=` |

## Interconnects

- **Dogfood-loop chain** (150): pre-tagged Reflections sharpen the
  classifier.
- **LLM-driver chain** (147): the auto-scope engine.
- Spec 017 is the parent; Spec 157 (architecture gate) enforces the
  no-markdown-parse invariant.
- Spec 151 (Codes coverage) supplies `Codes.NOTE_SCOPE_INVALID` and
  `Codes.NOTE_SCOPE_CONFLICT`.
- Spec 153 (schema coverage) — Reflection schema gains a `scope` enum
  whose closed set this spec defines.
- Spec 155 (red-team) — red-team Reflections land pre-classified through
  this same path; consistent classifier across Reflection sources.

## Open questions

1. Hard-remove `collect` or tombstone with a `DEPRECATED` raise?
   **Recommend**: tombstone one cycle (raise with a pointer to `note`),
   then hard-remove — matches the alias-and-deprecate doctrine.
2. Classifier model — Haiku or Sonnet for cost? **Recommend**: Haiku
   4.5 (classification is bounded-output; per `claude-api` skill the
   cheapest model is correct unless rubric agreement < 0.85).

## Followup — Implementation Status (Slice 1, 2026-06-12)

**Verdict:** Slice 1 SHIPPED on `claude/autonomous-completion`.

Driven through the engine surface end-to-end (intent:11e7f576;
skill:90c00b85 tdd walk; 4 Reflections recorded via dogfood.note;
branch.commit_smart composed the commit's conventional-commit
type+scope).

### Done — Slice 1 (typed CollectCallersReport + audit)

- **`scripts/check_collect_callers.py`**:
  - `CallerSite{file, line, text}` frozen dataclass.
  - `CollectCallersReport{callers}` + `caller_count` property.
  - `audit_collect_callers(root)` walks `<root>/**/*.py`, regex-matches
    `dogfood.collect(` call syntax (NOT import lines or comment/docstring
    mentions), skips `__pycache__` + `tests/` (fixtures legitimately
    reference the deprecated verb). Output sorted by file:line.
  - CLI `--strict` exits 1 when any caller remains (Slice 2 promotes
    to the deprecation gate).

- **7 tests** in `tests/test_collect_callers.py`:
  - typed CallerSite shape
  - empty-tree returns 0
  - explicit caller surfaced
  - comments/docstrings NOT counted
  - import lines NOT counted
  - __pycache__ + tests/ skipped
  - live-tree audit (shape invariant; no pinned count per rule 8)

### Still — Slice 2+

- **Slice 2** — wire CI gate: `caller_count` monotonically decreasing
  across PRs. Baseline tracked in
  `Plan/_planning/collect-callers-baseline.txt`.
- **Slice 3** — `dogfood.note(auto_scope=True)` so the migration path
  is a single-arg swap.
- **Slice 4** — final caller removal + deprecation warning on
  `dogfood.collect` itself.
- **Slice 5** — LLM-classifier pass turning the remaining caller
  intents into structured `dogfood.note(scope=...)` calls
  (Spec 147 wet driver).

