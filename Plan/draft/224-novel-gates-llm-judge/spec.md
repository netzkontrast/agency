---
spec_id: "224"
slug: novel-gates-llm-judge
status: draft
state: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "108"
depends_on: ["108", "178", "122", "150", "147", "217", "220", "222"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_gates_judge.py
---

# Spec 224 — novel gates: optional judgement findings

## Why

Spec 108 (novel-gates) ships the decidable publication gates. The
editorial pipeline (Spec 122) is also decidable (filter-words,
show-don't-tell, continuity). But developmental questions (does the
midpoint land? is the antagonist's arc satisfying?) need judgement.
Mirroring the analyze judge axis (Spec 178) + the music gates (Spec
213), the novel gates can carry an OPTIONAL judged finding, tagged,
augmenting the decidable verdict — never replacing it.

## Done When

- [ ] **Each novel gate gains an optional `judge=True`** — the Spec 147
      Driver scores against a rubric, returns a tagged `judged` finding;
      the decidable verdict unchanged.
- [ ] **Typed return shape**:
      ```python
      GateResult = {
        "gate":           str,             # gate name from Spec 108 registry
        "decidable_pass": bool,            # the hard verdict (unchanged)
        "judged":         dict | None,     # populated iff judge=True
          # judged: {
          #   "score":    int,             # 0..10 rubric score
          #   "tags":     list[str],       # e.g. ["weak-midpoint","arc-flat"]
          #   "evidence": list[dict],      # span citations into the work
          #   "rubric_id": str,            # Spec 178 rubric reference
          #   "model":    str,             # Spec 147 model used
          # }
        "blocks":         bool,            # equals decidable_pass; judged never blocks alone
        "reflection_id":  str | None,      # Spec 150 reflection when chained
        "refusal":        dict | None,
      }
      ```
- [ ] **Judged findings never block** unless explicitly chained — the
      decidable gates stay the hard pass; assert `blocks == (not
      decidable_pass)` in every test row regardless of judged outcome.
- [ ] **Judged findings become Reflections** (Spec 150 dogfood loop) —
      e.g. a recurring "weak midpoint" judgement across chapters becomes
      an amendment proposal via the Spec 150 classifier.
- [ ] **Per-gate rubric vendoring** — each gate names its rubric file
      at `agency/capabilities/novel/_rubrics/<gate>.yaml`; author-
      overridable via Lock (Spec 137 pattern).
- [ ] **Invariant — gate registry coverage.** The set of gates
      exposing `judge=True` MUST equal the live Spec 108 gate registry
      (derived, not pinned). CI asserts via the dormant-surface audit
      pattern (CLAUDE.md heuristic).
- [ ] **Invariant — judged separation.** Assert in CI that NO test
      shows `decidable_pass=True AND blocks=True` (judged can never
      flip a pass into a block); a `blocks=True` row MUST have
      `decidable_pass=False`.
- [ ] **Invariant — rubric stability.** A judged call with the same
      input + rubric_id MUST return a score within RUBRIC_VARIANCE
      points across runs (Spec 147 prefix-cache + deterministic
      decoding settings); the bound is a tunable, not pinned.
- [ ] **Invariant — reflection causality.** Every Reflection produced
      by a judged finding carries the `gate` + `work_id` + `score` on
      its payload — Spec 150's classifier needs that triple to promote
      recurring patterns to amendments.
- [ ] **Degrades** without `[anthropic]` (Spec 108 decidable-only);
      `judge=True` without the extra raises
      `Codes.JUDGE_DRIVER_UNAVAILABLE` early (not silently ignored).
- [ ] **Failure modes**:
      - `Codes.DRIVER_REFUSAL` from Spec 147 — judged is None,
        decidable verdict still authoritative; refusal Artefact written;
      - `Codes.JUDGE_RUBRIC_MISSING` when `judge=True` for a gate with
        no vendored rubric;
      - `Codes.JUDGE_DRIVER_UNAVAILABLE` when `judge=True` without the
        `[anthropic]` extra installed.
- [ ] Test: a gate returns a tagged judged finding (mocked); decidable
      verdict unchanged; judged-only failure does not block; recurring
      tag across 5 chapters produces a Spec 150 Reflection; missing
      rubric raises typed code.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a 41-chapter novel passing every decidable gate, and the
        Spec 147 driver mocked to score the midpoint-load gate at 4/10
        with tags ["weak-midpoint","stakes-flat"] across chapters 18-22
When:   gates_check(work_id=X, judge=True) is called
Then:   each GateResult has decidable_pass=True
        AND the midpoint-load gate has judged.score == 4
        AND judged.tags == ["weak-midpoint","stakes-flat"]
        AND blocks == False (judged never blocks alone)
        AND 5 Reflection nodes appear (one per chapter) with
            scope="judge-midpoint" and payload carrying gate+work+score

Given:  the same novel, but judge=True passed without [anthropic]
        installed
When:   gates_check runs
Then:   returns Codes.JUDGE_DRIVER_UNAVAILABLE immediately
        AND does NOT run the decidable gates (early reject — caller
            asked for an unavailable mode; runs again without judge=True
            to get decidable-only verdict)

Given:  20 novels across the catalogue, judged midpoint-load scores
        averaging 4.2/10 with recurring "weak-midpoint" tags
When:   the Spec 150 classifier processes the Reflections
Then:   it surfaces an amendment proposal targeting Spec 108's
        midpoint-load rubric (the dogfood loop closes)
```

## Failure modes

LLM-touching: Spec 147 refusal leaves the decidable verdict intact —
judged is opportunistic, never authoritative. Rubric vendoring is a
caller contract; a missing rubric is a developer error, not a runtime
degradation surface. The `judge=True` flag without `[anthropic]` is
caught EARLY (before running decidable gates) so the caller sees the
typed code immediately rather than a silent skip. Rubric stability
depends on Spec 147 prefix-cache + decoding-temperature controls;
small score drift within `RUBRIC_VARIANCE` is acceptable, larger drift
indicates rubric or model bug.

## Interconnects

- Spec 178 (analyze judge) + Spec 213 (music gates judge) are the
  pattern · **dogfood** (150).
- Spec 122 (editorial) is the decidable sibling.
- Spec 147 (Driver) underlies the judged calls.
- Spec 217 (build walkable) — calls this verb at the gates phase
  with `judge=True` when the walk runs in author mode.
- Spec 220 (prose driver wet) — judged findings on freshly-generated
  scenes feed back into the regenerate loop (advisory, not gating).
- Spec 222 (catalogue graph-query) — cross-work judged-tag queries
  ("every chapter tagged 'weak-midpoint' across my catalogue") use
  the same Reflection nodes.

## Open questions

1. Per-gate rubric? **Recommend**: yes — developmental ≠ line ≠ copy
   judgement; vendored, author-overridable via Lock (Spec 137).
2. Score scale 0..10 or 0..5? **Recommend**: 0..10 — finer granularity
   helps Spec 150 detect drift trends; downstream UIs can binarize.
3. Should judged ever block when explicitly chained? **Recommend**:
   only via an explicit Lock entry `judge_blocks=True` per gate —
   default is advisory; the author opts in per project.
4. Cross-work rubric reuse? **Recommend**: yes — the same rubric_id
   serves every novel in an author's catalogue by default; author
   can fork per-work via Lock.
