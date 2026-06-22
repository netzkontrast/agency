---
spec_id: "213"
slug: music-gates-llm-judge
status: draft
state: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "100"
depends_on: ["100", "178", "147", "150", "146", "206", "208", "211"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/music/_main.py
  - agency/capabilities/music/clusters/gates.py
  - tests/test_music_gates_judge.py
---

# Spec 213 — music gates: optional judgement findings

## Why

Spec 100 (music-gates) ships 8 decidable gate verbs (audio-release,
catalogue, promo, sub-gates) + the E2E provenance test. The gates are
DECIDABLE — but some quality questions (does this master sound muddy?
does this promo land?) need judgement. Mirroring the analyze judge axis
(Spec 178), the music gates can carry an OPTIONAL judged finding,
clearly tagged, that augments the decidable verdict without replacing it.

## Done When

- [ ] **Each music gate gains an optional `judge=True`** — the Spec 147
      Driver scores the artefact against a vendored rubric, returns a
      tagged `judged` finding; the decidable verdict is unchanged.
      Typed return: `GateVerdict = {gate_name, decidable: bool,
      decidable_reasons: list[str], judged: JudgedFinding | None,
      driver_usage: TokenUsage | None}` where
      `JudgedFinding = {score: float, rationale: str, rubric_id: str,
      confidence: Literal["low","medium","high"]}`.
- [ ] **Judged findings never block** (advisory) unless the author
      explicitly chains them — the decidable gates stay the hard pass.
- [ ] **Judged findings become Reflections** (Spec 150 dogfood loop) —
      scoped to the gate name + artefact so per-rubric drift can be
      learned over time.
- [ ] **Rubric prefix is cache-stable** (Spec 146) — the rubric text
      sits in the system-prompt prefix; only the artefact varies in body.
- [ ] **Degrades** without `[anthropic]` (decidable-only, Spec 100);
      `judged=None` is the expected value, not an error.
- [ ] **Test**: a gate returns a tagged judged finding (mocked);
      decidable verdict unchanged with/without judge; rubric prefix
      bytes match across two calls on different artefacts.
- [ ] **TODO row + drift clean.**

## Measurable invariants (relationships, not pinned counts)

- **Decidable invariance under judge** — for any artefact, calling the
  gate with `judge=False` and `judge=True` yields the SAME
  `decidable` value and `decidable_reasons` (the judge cannot change
  the hard verdict — only annotate).
- **No silent block** — `assert verdict.judged is None or
  verdict.decidable is not None` (judged is never the only signal).
- **Rubric coverage** — every gate that supports `judge=True` has a
  vendored rubric at `agency/capabilities/music/rubrics/<gate>.md`; a
  drift test asserts the rubric set matches the judge-capable gate set.
- **Reflection-per-judgement** — `count(Reflections scoped to
  (gate_name, artefact_id)) == count(judge=True calls)` over a test run.

## Worked example (Given/When/Then)

```text
Given:  a mastered_audio artefact; the audio-release gate's decidable
        path returns passed=True, reasons=["LUFS in range"]; the
        AnthropicDriver mocked to score 0.62 with rationale "high-mid
        congestion in chorus"
When:   audio_release_gate(track_id, judge=True)
Then:   returns GateVerdict{decidable=True,
        decidable_reasons=["LUFS in range"],
        judged=JudgedFinding{score=0.62, rationale="...",
        rubric_id="audio-release", confidence="medium"}}
        AND analyze.graph(reflection_id).scope ⊇ {"gate":"audio-release",
        "artefact":track_id}
        AND a sibling call with judge=False returns the same decidable
        verdict and judged=None
```

## Failure modes (Nygard)

| Failure | Verb response |
|---|---|
| Driver `REFUSAL` on judged scoring | `judged=None`, decidable unchanged, Reflection records the refusal; no error to caller (judging is advisory) |
| Driver `RATE_LIMITED` | `judged=None` with a Reflection noting rate-limit; caller retries by re-calling with `judge=True` |
| Rubric file missing for a gate | install-time lint fails (drift); never silent fall-through to "no rubric, just pass" |
| Judged score parse error (Driver returns malformed JSON) | `judged=None`, Reflection records the parse failure with the raw bytes for forensic replay |
| `[anthropic]` extra missing | `judged=None`; never raise (judging is opt-in) |
| Gate composes judged result into the decidable verdict (anti-pattern leak) | unit test fails: invariant "decidable invariance under judge" guards this exactly |

## Interconnects

- Spec 178 (analyze judge axis) is the pattern; **dogfood** (150).
- **LLM-driver chain** (147) · **output-budget** (146).
- Spec 206 (produce-album walk) records `judge=True` verdicts on every
  hard gate so the walk's `WalkResult` carries the augmented finding.
- Spec 208 (lyrics) + Spec 211 (promo) consume the judged findings on
  their respective gates to drive the iterate-to-gate loop with
  richer hints.

## Open questions

1. Per-gate rubric or shared? **Recommend**: per-gate (audio quality ≠
   promo quality); vendored rubrics, author-overridable.
2. Should judged findings ever block? **Recommend**: never by default;
   an author may opt-in via `verdict.judged.score < threshold and
   author_block=True` — explicit, never implicit.
3. Where do rubric versions land? **Recommend**: in a Spec 137 Lock
   keyed on `(gate_name, rubric_version)` — so historical Reflections
   can replay against the rubric they were scored under.
