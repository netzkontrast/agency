---
spec_id: "216"
slug: music-name-exposure-driver
status: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "119"
depends_on: ["119", "147", "138", "208", "211", "150", "214"]
vision_goals: [4]
affects:
  - agency/_substrate/_name_exposure.py
  - agency/capabilities/music/_main.py
  - tests/test_music_name_exposure_driver.py
---

# Spec 216 — music name-exposure: fuzzy + cross-domain reuse

## Why

Spec 119 (music-name-exposure) ships whole-word + case-insensitive
blocklist scanning ("Lex" never fires inside "lexicon") across lyrics +
promo. It is purely decidable — a name spelled slightly differently
(homophone, misspelling, split-across-lines) slips through. The novel
plural-character system (Spec 138) has the SAME need
(`check_alter_recognition` — names never labeled). This generalizes the
name-exposure check into a shared substrate both domains use, with an
optional Spec 147 fuzzy pass for near-misses.

## Done When

- [ ] **The name-exposure check is extracted to a shared substrate**
      both music (119) and novel (138) consume — one implementation, two
      callers (the drop-in bar, CLAUDE.md). Typed return:
      `NameExposureFinding = {decidable_hits: list[Hit],
      fuzzy_hits: list[FuzzyHit], driver_used: bool,
      blocklist_hash: str}` where `Hit = {term, line, column,
      match_kind: Literal["whole_word","case_insensitive"]}` and
      `FuzzyHit = Hit + {original_term, distance: float,
      hypothesis: Literal["homophone","split","misspelling"],
      confidence: float}`.
- [ ] **Optional fuzzy pass** — the Spec 147 Driver flags near-miss
      exposures (homophones, split names) the decidable scan misses;
      tagged `judged`, advisory; `driver_used=False` when caller passes
      `fuzzy=False` or `[anthropic]` is absent.
- [ ] **The decidable whole-word scan stays the hard gate** (Spec 119);
      `fuzzy_hits` are never promoted into `decidable_hits`.
- [ ] **Shared blocklist hash** — both music and novel consult the
      same hashed blocklist; `blocklist_hash` is returned so callers
      can prove they scanned against the current list.
- [ ] **Reflections record fuzzy hits** (Spec 150) — every fuzzy hit
      emits a scoped Reflection so the dogfood loop can promote a
      recurring fuzzy hit into the decidable blocklist over time.
- [ ] **Test**: a homophone leak is fuzzy-flagged (mocked); the
      decidable gate unchanged; novel + music both call the shared check
      and observe the same `blocklist_hash`.
- [ ] **TODO row + drift clean.**

## Measurable invariants (relationships, not pinned counts)

- **Decidable-gate invariance** — for any input + blocklist pair, the
  set of `decidable_hits` is byte-identical whether `fuzzy=True` or
  `fuzzy=False` (the fuzzy pass is purely additive).
- **Cross-domain parity** — music and novel callers on identical input
  + blocklist return IDENTICAL `NameExposureFinding` (set equality on
  hits + same `blocklist_hash`).
- **Fuzzy advisory invariant** — `assert all(h.confidence < 1.0 for h
  in fuzzy_hits)` — fuzzy never claims certainty (that would justify
  blocking, violating the advisory invariant).
- **Blocklist-hash freshness** — `blocklist_hash` matches the hash of
  the live blocklist at scan time; a test asserts this by mutating the
  blocklist between calls and observing the hash change.

## Worked example (Given/When/Then)

```text
Given:  blocklist=["Alex Karp"]; lyric line "alecks carp drove the deal";
        AnthropicDriver mocked to return one fuzzy hit at distance 0.18
        with hypothesis="homophone", confidence=0.82
When:   check_name_exposure(text, fuzzy=True)
Then:   returns NameExposureFinding{decidable_hits=[],
        fuzzy_hits=[FuzzyHit{term="alecks carp", original_term="Alex Karp",
        hypothesis="homophone", confidence=0.82}],
        driver_used=True, blocklist_hash=<sha>}
        AND a Reflection SERVES the calling intent scoped to
        ("name_exposure_fuzzy", "alecks carp")
        AND a parallel call from novel/138 on identical input + blocklist
        returns the same NameExposureFinding
```

## Failure modes (Nygard)

| Failure | Check response |
|---|---|
| Driver `REFUSAL` on fuzzy pass | `fuzzy_hits=[]`, `driver_used=False`, Reflection records the refusal; decidable result unchanged |
| Driver `RATE_LIMITED` | same as refusal; advisory-only never blocks the calling pipeline |
| Blocklist file unreadable | typed `Codes.BLOCKLIST_UNREADABLE` BEFORE scan; never silently return zero hits (which would unblock leaks) |
| Caller passes `fuzzy=True` without `[anthropic]` | `fuzzy_hits=[]`, `driver_used=False`, doctor hint surfaced; decidable unchanged |
| Music + novel observe DIFFERENT `blocklist_hash` for one input | install-time lint fails — the substrate has drifted between domains (rule 8 enforcement) |
| Fuzzy hit overlaps a decidable hit | decidable wins; the fuzzy hit is dropped (no double-counting); invariant test asserts disjointness |

## Interconnects

- Spec 138 (alter recognition) is the cross-domain co-consumer.
- **LLM-driver chain** (147) for the fuzzy pass.
- Spec 208 (lyrics generation) runs the gate on generated text.
- Spec 211 (promo generation) runs the gate on generated copy.
- Spec 150 (dogfood) — fuzzy hits feed blocklist amendment proposals.
- Spec 214 (derived config) — the doctor reports the blocklist hash.

## Open questions

1. Where does the shared check live? **Recommend**: a substrate helper
   at `agency/_substrate/_name_exposure.py` since two domains need it;
   promote to a tiny `text` capability if a third consumer appears (the
   drop-in bar — coupling is the bug).
2. Should fuzzy hits ever block? **Recommend**: never by default; an
   author may chain `fuzzy_hit.confidence > 0.9 → block` explicitly,
   but the substrate never auto-promotes.
3. Dogfood-loop promotion path? **Recommend**: a Reflection that
   repeats N times scoped to the same `(original_term, hypothesis)`
   becomes a Spec 150 amendment proposal that adds the variant to the
   decidable blocklist — closes the loop without manual edits.
