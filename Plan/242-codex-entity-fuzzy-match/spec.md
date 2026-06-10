---
spec_id: "242"
slug: codex-entity-fuzzy-match
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "132"
depends_on: ["132", "216", "147", "146"]
vision_goals: [4]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_codex_fuzzy.py
---

# Spec 242 — codex entity matching: word-boundary + fuzzy

## Why

Spec 132 ships `match_codex_entries` with plain substring; its Open Q1
named the false-positive risk ("raven" matching "ravenous"). Slice 2
listed word-boundary regex matching. Spec 216 generalized the
name-exposure check into a shared substrate (whole-word + fuzzy). This
applies the same upgrade to codex matching — and reuses Spec 216's
substrate so the two stay in sync.

## Done When

- [ ] **Word-boundary matching** (`\b...\b`) — closes Slice 2 of 132.
- [ ] **Optional fuzzy match** (Spec 216 substrate) for typos +
      partial mentions; tagged `judged`, advisory.
- [ ] **Decidable whole-word stays the canonical match** (the gate).
- [ ] Test: "raven" no longer matches "ravenous"; fuzzy flags typo
      "Sebatsian" → "Sebastian" (mocked Driver).
- [ ] TODO row + drift clean.

## Interconnects

- Spec 216 (shared name-exposure substrate) — co-consumer.
- **LLM-driver chain** (147) for the fuzzy pass.
