---
spec_id: "220"
slug: novel-prose-driver-wet
status: partial
last_updated: 2026-06-12
owner: "@agency"
enhances: "104"
depends_on: ["104", "147", "130", "144", "146", "154", "217", "219", "279"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_prose_wet.py
---

# Spec 220 — novel prose TextDriver (wet generation)

## Why

Spec 104 (novel-prose) ships the prose engine + checks. Spec 130
(scene-writer) ships the 5-phase walk but its generate phase is "no
driver binding yet — Slice 2 territory gated on Spec 005", using a
FakeTextDriver stub. Spec 147 lifts the gate: a real TextDriver backed
by the AnthropicDriver generates the scene body from the assembled
brief (Spec 127) or the voice-locked brief (Spec 144), and the shipped
checks validate it.

## Done When

- [ ] **A production TextDriver** behind the Spec 002 boundary, backed
      by Spec 147 — scene-writer phase 3 (generate) uses it; the
      FakeTextDriver stays the CI default.
- [ ] **Typed return shape**:
      ```python
      WetSceneResult = {
        "intent_id":      str,
        "scene_id":       str,
        "body_handle":    str,        # Spec 154 recall handle for the body
        "wc":             int,        # word count (cheap, kept on the prefix)
        "checks":         list[dict], # [{name, pass, evidence}] from Spec 104
        "passes_all":     bool,
        "regen_count":    int,        # bounded gate-driven regenerations
        "driver":         Literal["spec147","fake"],
        "voice_locked":   bool,       # True iff Spec 144 brief used
        "refusal":        dict | None,
      }
      ```
- [ ] **Generation consumes the voice-locked brief** (Spec 144) when an
      alter is bound, else the plain brief (Spec 127).
- [ ] **The shipped prose checks gate the output** (filter-words,
      show-don't-tell, voice-drift); failures trigger a bounded
      regenerate.
- [ ] **Generation honors the output budget** (Spec 146/154 — a long
      scene captures); the scene body NEVER returns inline — always via
      `body_handle`, so a wrapping LLM driver fetches only what it needs.
- [ ] **Invariant — every shipped scene passes every shipped check.**
      Assert `passes_all is True` for returned scenes; if the bounded
      regenerate loop exhausts, surface a typed refusal rather than
      ship gate-failing prose (relationship, not pinned count).
- [ ] **Invariant — regen bound is RELATIONAL.** Assert
      `regen_count <= MAX_PROSE_REGEN` (configured tunable); on
      overshoot, return `Codes.PROSE_GATE_NONCONVERGENT` with the
      failing check set.
- [ ] **Invariant — check coverage equals registry.** `checks` length
      equals the live Spec 104 check registry length — never a pinned
      number (CLAUDE.md rule 8).
- [ ] **Invariant — voice-lock fidelity.** When `voice_locked` is True,
      assert the scene-body Artefact carries a `voice-drift` check
      whose evidence references the Spec 144 alter id.
- [ ] **Failure modes**:
      - `Codes.DRIVER_REFUSAL` from Spec 147 — refusal Artefact written;
      - `Codes.PROSE_GATE_NONCONVERGENT` after `MAX_PROSE_REGEN` rounds;
      - `Codes.SCENE_OVERFLOW_LOST` when the Spec 154 capture fails
        (sandbox / disk full) — scene-writer halts at this scene only;
      - `Codes.VOICE_BRIEF_MISSING` when `alter_id` set but Spec 144
        produced no brief.
- [ ] Test: scene-writer generates a gate-passing body (mocked Driver);
      voice-locked vs. plain branches both validated; gate-non-convergence
      raises typed code; Fake fallback unchanged.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a scene brief with alter_id="kira-pov" (Spec 144 voice locked)
        and the Spec 147 driver mocked to return a 1200-word body that
        passes filter-words + show-don't-tell on round 1 but fails
        voice-drift (echoes a forbidden register)
When:   scene-writer phase 3 runs
Then:   round 1 regenerates with voice-drift evidence as feedback
        AND round 2 passes all three checks
        AND result.regen_count == 1
        AND result.passes_all is True
        AND result.voice_locked is True
        AND result.body_handle resolves a 1200-word Artefact via
            recall_overflow

Given:  MAX_PROSE_REGEN=4 and the loop fails 4 successive rounds on
        show-don't-tell
When:   scene-writer exhausts the budget
Then:   returns Codes.PROSE_GATE_NONCONVERGENT
        AND the last failing body is preserved as
            Artefact(kind="prose-rejected") for author inspection
        AND no scene-body Artefact PRODUCES the Scene node

Given:  alter_id set but Spec 144 returned no voice-locked brief
When:   scene-writer phase 3 starts
Then:   returns Codes.VOICE_BRIEF_MISSING
        AND does NOT fall back to the plain brief silently
```

## Failure modes

LLM-touching: Spec 147 propagates refusal/overflow codes. The bounded
regenerate loop catches gate-non-convergence rather than shipping
sub-quality prose. The Spec 154 overflow store is external — capture
failures (disk full, sandbox eviction) surface `SCENE_OVERFLOW_LOST`
and halt this scene without rolling back prior scenes. Voice-lock is
a hard input contract: an `alter_id` without a Spec 144 brief is a
caller bug, not a degradation surface.

## Interconnects

- **LLM-driver chain** (147) — lands Spec 130's deferred generate phase.
- Spec 144 (voice-locked) + Spec 127 (brief) are the prompt inputs.
- Spec 146 (output-prefix) + Spec 154 (overflow capture) — scene body
  always returns via handle, never inline.
- Spec 217 (build walkable) calls this verb at the scene phase.
- Spec 219 (storyform LLM-assist) — the storyform NCP scopes the
  per-scene brief.
- Spec 222 (catalogue graph-query) — cross-work prose queries traverse
  the same Scene SERVES Novel moat.
- Spec 224 (gates LLM-judge) — developmental judgement on the same
  scene body augments the decidable checks.
- Spec 252 (novel skill-walks managed) — wraps this verb on the
  Managed-Agents path.

## Open questions

1. Stream the scene body? **Recommend**: yes (Spec 146 streaming) —
   scenes exceed the non-streaming token guard; stream into the
   Spec 154 capture, expose `body_handle` only.
2. Regenerate the whole scene or patch failing spans? **Recommend**:
   whole-scene for v1 (predictable, fits the decidable checks);
   span-patching is a Slice-2 once Spec 104 exposes
   span-grained check evidence.
3. Voice-drift threshold per alter or global? **Recommend**:
   per-alter — Spec 144 brief carries the threshold; global default
   when unset.
4. Surface failing-prose Artefacts to the author UI? **Recommend**:
   yes — `kind="prose-rejected"` Artefacts SERVES intent so the
   catalogue (Spec 222) can list them for hand-edit.


## Followup — Implementation Status (Slice 1, 2026-06-12)

### Done — Slice 1 (driver-bound generate phase + Spec 279 delegation)

- **`novel.generate_scene_body(scene_id, brief, alter_id, system,
  host_completion, prefer_delegate, max_tokens)`** verb ships:
  - Drives Spec 147 AnthropicDriver via Spec 279
    `complete_or_delegate` — three paths (resume wins):
    1. `host_completion` supplied → parse text → `driver="host"`.
    2. driver capable → `complete()` → `driver="spec147"`.
    3. driver backend "none" AND `prefer_delegate=True` → emit
       `kind="llm_delegate"` envelope (`driver="delegate"`).
  - Body ALWAYS captured via Spec 154 `capture_overflow` (512-token
    head budget); response carries `body_handle` (Artefact id), NEVER
    the body inline (Spec 146 prefix discipline; Spec 154 budget).
  - Voice-lock fidelity: `alter_id` requires non-empty `brief` from
    Spec 144 — empty brief → `VOICE_BRIEF_MISSING` typed code.
  - System prompt includes voice-lock directive when alter is bound.
  - Continuation token derived deterministically via Spec 279
    `make_continuation_token(intent_id, verb, {scene_id, alter_id})`.

- **Scene-writer phase 3 wired** — `SCENE_WRITER_SKILL` phase 3
  `verbs: []` → `verbs: ["novel.generate_scene_body"]`. The deferred
  Slice-1 stub is lifted; walking the scene-writer skill now
  EXECUTES the generate phase end-to-end.

- **Typed failure codes** — `VOICE_BRIEF_MISSING`,
  `DEPENDENCY_MISSING`, `SCENE_OVERFLOW_LOST`, `DRIVER_REFUSAL`,
  `HOST_DELEGATE_MALFORMED`. The default Engine-created driver has
  backend "none"; without `prefer_delegate=True` the verb refuses
  cleanly rather than crashing the loop.

- **Provenance moat** — every generated body records an
  `Artefact(kind="scene-body", scene_id, voice_locked, alter_id,
  total_tokens, full_body, stop_reason, driver)` with PRODUCES_FROM
  the Scene + SERVES the active intent.

- **13 tests green** (`tests/test_novel_prose_wet.py`):
  registration + scene-writer-phase-3 binding; capable-driver
  Completion → handle; brief forwarded; voice-lock marks artefact
  + requires brief; delegate envelope when `prefer_delegate=True`;
  silent typed fail when no driver/delegate; resume from
  host_completion + wins over driver + malformed code; Artefact
  provenance shape + body never inline (3KB body still carried via
  handle).

- **Install drift clean** — `python -m agency.install` regenerates
  `bin/agency-novel-generate_scene_body` +
  `skills/novel/references/generate_scene_body.md`; test_agency
  install-self-hosted invariant green.

### Still — Slice 2+

- **Slice 2 — gate-driven regenerate loop**: wire `check_filter_words`
  / `check_dialogue_attribution` / `check_show_dont_tell` /
  `novel_coherence_check` against the captured body; on failure,
  call the driver again with the prior-round evidence as feedback;
  bounded by `MAX_PROSE_REGEN` (default 4); on exhaustion return
  `Codes.PROSE_GATE_NONCONVERGENT` with the failing-check set +
  preserve the last failing body as `Artefact(kind="prose-rejected")`.
- **Slice 3 — voice-drift evidence references alter_id**: when
  `voice_locked=True`, the voice-drift check evidence must cite the
  Spec 144 alter id (the spec invariant).
- **Slice 4 — streaming**: long scenes overflow the non-streaming
  16K guard; stream via Spec 147 Slice 2.x `stream()` into the Spec
  154 capture so `body_handle` always serves.
- **Slice 5 — refusal Artefacts visible**: surface `prose-rejected` /
  `refusal` Artefacts via Spec 222 catalogue so the author can
  hand-edit.
- **Spec 252 integration**: managed-agents path wraps this verb on
  the long-form session boundary.

