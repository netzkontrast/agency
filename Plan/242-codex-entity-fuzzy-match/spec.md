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

- [ ] **`match_codex_entries(text, codex_id) -> MatchResult`** where
      `MatchResult = {decidable: list[Match], judged: list[Match],
      total: int}` and `Match = {entry_id, surface_form, span: (int,
      int), kind: Literal["whole_word","fuzzy"], confidence: float |
      None}`. Invariant: `total == len(decidable) + len(judged)` AND
      `all(m.confidence is None for m in decidable)`.
- [ ] **Word-boundary matching** (`\b...\b`) — invariant: for every
      decidable match, the matched span aligns to word boundaries in
      the source text; `text[span[0]-1]` is non-alphanumeric or start-
      of-string AND `text[span[1]]` is non-alphanumeric or end-of-
      string. Closes Slice 2 of 132.
- [ ] **No false positives on the canonical test set** — invariant:
      "raven" never appears in `decidable` when the source contains
      only "ravenous" (the substring trap that motivated this spec).
      Asserted as relation: `"ravenous" in text AND
      not any(m.entry_id == raven_id for m in result.decidable)`.
- [ ] **Optional fuzzy match** (Spec 216 substrate) for typos +
      partial mentions; tagged `judged`, advisory. Invariant: judged
      matches NEVER raise gate severity above WARN (Spec 232 advisory
      pattern); only decidable matches participate in continuity gates.
- [ ] **Decidable whole-word stays the canonical match** (the gate) —
      invariant: a name's `Continuity` gate consumes only `decidable`
      matches; `judged` matches surface as suggestions for the author.
- [ ] **Failure modes** — codex_id unknown → `Codes.CODEX_NOT_FOUND`,
      empty result; Driver unavailable for fuzzy pass →
      `Codes.DRIVER_UNAVAILABLE`, `judged=[]`, decidable matches
      returned unchanged (graceful degrade); regex compile fail on a
      malformed codex entry → `Codes.CODEX_ENTRY_INVALID` naming the
      offending entry, other entries still match.
- [ ] Test: "raven" no longer matches "ravenous"; fuzzy flags typo
      "Sebatsian" → "Sebastian" (mocked Driver).
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  codex with entries {raven: Character, Sebastian: Character};
        text = "The ravenous Sebatsian glared at the raven."
When:   match_codex_entries(text, codex_id, fuzzy=True) runs
        (mocked Driver maps "Sebatsian" → Sebastian with conf=0.85)
Then:   len(result.decidable) == 1 (raven at the actual occurrence) AND
        len(result.judged) == 1 (Sebatsian → Sebastian fuzzy) AND
        the decidable raven match has span pointing at "raven", NOT
        at the "raven" prefix of "ravenous" AND
        the judged match has kind=="fuzzy", confidence==0.85, and
        severity in the consuming gate is WARN (never ERROR)

Given:  same text, fuzzy=False (default)
When:   match_codex_entries runs
Then:   result.judged == [] AND
        result.decidable still excludes the "ravenous" prefix
```

## Failure modes

LLM/remote/cache surfaces: Driver returns malformed match span
(out-of-bounds offsets) → entry rejected with `Codes.MATCH_INVALID`;
fuzzy confidence drift over time as the model updates — mitigated by
recording the model id in the Match record so historical judged matches
remain interpretable.

## Interconnects

- Spec 216 (shared name-exposure substrate) — co-consumer.
- **LLM-driver chain** (147) for the fuzzy pass.
- Spec 232 (editorial judge) — same decidable/judged partition pattern;
  judged is advisory, decidable is the gate.
- Spec 241 (character-knowledge extract) — character_id resolution
  reuses this matcher to attach extracted facts to codex entries.
- Spec 233 (worldbuilding Slice 2) — Conflict parties resolve to
  codex entries via this matcher.

## Open questions

1. **Fuzzy threshold.** Levenshtein ≤2 or substring-similarity ≥0.8?
   **Recommend:** Levenshtein ≤2 for short names (<8 chars), similarity
   ≥0.8 otherwise — the shared substrate (Spec 216) decides.
2. **Multi-word entries.** "John Smith" matched as whole phrase or
   per-token? **Recommend:** whole phrase first, fall back to per-token
   if zero phrase matches AND fuzzy=True.
3. **Performance.** Naive scan on every gate run? **Recommend:** memoize
   per `(text_sha256, codex_version)` in the engine cache — cheap and
   keyed on derivable inputs, never on time.
