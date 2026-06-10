---
spec_id: "144"
slug: voice-locked-drafting-prompt
status: draft
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["127", "129", "134", "138", "143"]
affects:
  - agency/capabilities/prompt/_main.py
  - agency/capabilities/novel/_main.py
  - tests/test_voice_locked_drafting.py
domain: novel / prompt / voice
parent_spec: "101"
mvp-source:
  - "examples/kohaerenz-protokoll/03_anteile-profile-sprach-dna.md (full Sprach-DNA spec — 13 alters × 9 fields each)"
  - "Plan/134-pov-voice-profiles/spec.md (VoiceProfile data model)"
  - "Plan/138-plural-character-system/spec.md (Alter + VOICED_BY)"
---

# Spec 144 — Voice-locked drafting prompt

## Why

Spec 134 ships `VoiceProfile` (vocabulary / sentence-shape / taboo /
signature phrases). Spec 138 ships `Alter` + `VOICED_BY` binding. Spec
127 + 143 ship the prompt-composition stack. But the KP-canonical
**Sprach-DNA per alter** — syntax fingerprint + lexicon + somatik tags +
taboo list + example sentences — has no single-call composer that emits
a *voice-locked prompt*: a brief that's so tightly bound to an alter's
voice that a one-shot LLM call drafts in that voice without leaking
into another alter's register.

The KP source ships this discipline as a *manual* pre-scene checklist
(§12 of the alter doc: 7 mandatory checks). This spec automates it as
a single composer that an LLM driver calls once per scene to get a
voice-locked drafting prompt — the "recognized not named" discipline
(Spec 138's `check_alter_recognition`) made productive instead of just
defensive.

## Why this isn't already Spec 134

134's `VoiceProfile` is the *data*. 138's `Alter` is the *roster*. 127
assembles a *scene brief* (graph-side). 143 ships *fragment* prompts.
None of them: (a) bake a voice profile INTO a drafting prompt at
single-call resolution, (b) embed the alter's taboo list as an
"absolute negative-constraint" block, (c) inject 1–3 example sentences
from the alter's Sprach-DNA as one-shot exemplars, (d) honor the
co-fronting matrix (Spec 138 `max_pairs`) by refusing to compose a
brief that lets two phobic alters share a frontstage.

## Done When

- [ ] **`prompt.compose_voice_locked_brief(scene_id, alter_id)`** — the
      single composer. Returns a brief with this structure:
      ```
      §VOICE-LOCK: <alter.name>  (category=<…>  layer=<…>  function=<…>)
      §SYNTAX:       <voice_profile.sentence_shape>
      §LEXICON-PREFERRED:   <voice_profile.vocabulary_preferred>
      §LEXICON-FORBIDDEN:   <voice_profile.vocabulary_forbidden>
      §SOMATIK:      <alter.somatik_tags>          # from VoiceProfile or Alter
      §TABOO (HARD): <alter.taboo_rules>           # never-violate negatives
      §SIGNATURE:    <voice_profile.signature_phrases>
      §EXAMPLES:
        1) <example sentence 1>
        2) <example sentence 2>
        3) <example sentence 3>
      §SCENE BRIEF: <the Spec 127 scene-brief content>
      §INSTRUCTION: Draft the scene in <alter.name>'s voice. Honor every
        §TABOO absolutely. Match the §SYNTAX rhythm. Use §LEXICON-PREFERRED;
        avoid §LEXICON-FORBIDDEN. End-state required: <derived from
        chapter's mode-block + reveal-rules>.
      ```
- [ ] **`prompt.compose_voice_locked_brief` co-front guard** — when the
      scene's cast includes ≥ 2 alters from the same CharacterSystem
      AND the pair is a max-intensity PHOBIA_OF pair (Spec 138 conflict
      matrix), the verb refuses to compose unless `allow_max_pair=True`
      is explicit. Returns `{refused: True, reason: "max-pair-cofront",
      pair: (a, b), advice: "split into two scenes or pass allow_max_pair=True"}`.
- [ ] **`prompt.exemplar_pool(alter_id, n=3)`** — companion verb.
      Returns N example sentences from the alter's stored Sprach-DNA
      examples (rotates deterministically by intent-id hash so the LLM
      sees varied exemplars across drafts, not the same three every
      call).
- [ ] **`prompt.voice_drift_audit(scene_id)`** — after the LLM returns
      a draft, scans the body against the alter's voice profile and
      reports drift:
      ```
      Returns: {
        passed: bool,
        forbidden_lexicon_hits: [str…],
        taboo_violations: [{rule, span, snippet}…],
        signature_phrase_presence: bool,
        register_match_score: float,    # 0..1 heuristic
        verdict: "in-voice" | "drifted" | "leaked-other-alter",
      }
      ```
      The verdict `"leaked-other-alter"` fires when the body matches a
      DIFFERENT bound alter's signature better than the assigned one
      (Spec 138's `switching_log` heuristic, applied as a defensive
      check).
- [ ] **`scene-writer` (Spec 130) phase 1 extension** — when a scene's
      chapter has a fronting alter, the assemble phase chains
      `compose_voice_locked_brief` instead of bare `assemble_scene_brief`.
      Backward compatible: scenes WITHOUT a fronting alter use the
      existing path.
- [ ] **Lint** — voice-locked briefs ≤ 3000 cl100k tokens total (raised
      from 2000 because the voice-lock block is bulky). Truncation
      drops `§EXAMPLES` first, then `§SIGNATURE`, never `§TABOO`.
- [ ] TODO row + drift clean.

## Design notes

- **The taboo block is non-truncatable.** Truncating an alter's taboo
  list to fit a token budget defeats the entire purpose; the budget
  is generous instead. A scene where the alter's taboo list ALONE
  exceeds the cap is a malformed VoiceProfile (lint catches it).
- **Exemplars over instructions.** The §EXAMPLES block is the
  single most LLM-actionable piece — three voice-locked example
  sentences move register far more reliably than ten lines of
  prose-instruction. Spec 134's `example_sentences` field is the
  pool; this spec consumes it.
- **The co-front guard is the discipline-as-code.** The KP source
  forbids max-pair co-fronting because the voices destabilize each
  other on the page (the Klebstoff phobia-matrix is real
  psychophysiology, not décor). Refusing the compose is the cleanest
  enforcement — the LLM can't accidentally write the disallowed
  scene if the brief is never assembled.
- **Voice-drift audit closes the loop.** Drafting in-voice is one
  thing; verifying the draft IS in-voice is another. The audit
  reuses Spec 138's `switching_log` inference engine but in defensive
  mode — fail-loudly when the body matches the wrong alter.

## Schema (no new nodes; uses existing 134/138)

```text
# Reads:
Alter.taboo_rules, Alter.category, Alter.layer, Alter.function
VoiceProfile.vocabulary_preferred, .vocabulary_forbidden,
             .sentence_shape, .signature_phrases, .example_sentences
VOICED_BY edge (Alter → VoiceProfile)
PHOBIA_OF edge (Alter ↔ Alter, with vector/intensity)

# Writes:
Artefact (the composed brief; PRODUCES from the compose Invocation)
Reflection (voice_drift_audit findings)
```

## Verb signatures

```python
def compose_voice_locked_brief(
    scene_id: str,
    alter_id: str,
    *,
    allow_max_pair: bool = False,
    max_tokens: int = 3000,
) -> dict:
    """Returns: {
      brief: str,                   # the assembled prompt
      sections: {"voice-lock", "syntax", "lexicon-preferred",
                 "lexicon-forbidden", "somatik", "taboo",
                 "signature", "examples", "scene-brief",
                 "instruction": str},
      sources: [{node_id, kind, role}…],
      tokens: int,
      truncated: bool,
      refused: bool,
      refusal: {reason: str, advice: str} | None,
    }
    """

def exemplar_pool(alter_id: str, n: int = 3, intent_id: str = "") -> dict:
    """Returns: {alter_id, examples: [str…], pool_size: int, rotated_by: str}"""

def voice_drift_audit(scene_id: str) -> dict:
    """Returns: {
      passed: bool,
      assigned_alter: str,
      forbidden_lexicon_hits: [str…],
      taboo_violations: [{rule, span: (start,end), snippet}…],
      signature_phrase_presence: bool,
      register_match_score: float,
      verdict: str,
      leaked_to_alter: str,         # populated when verdict=="leaked-other-alter"
    }
    """
```

## Test scaffold

```text
tests/test_voice_locked_drafting.py  (target ≥ 20 tests)
  test_compose_voice_locked_brief_emits_all_sections
  test_compose_voice_locked_brief_taboo_block_never_truncated
  test_compose_voice_locked_brief_truncates_examples_first
  test_compose_voice_locked_brief_truncates_signature_second
  test_compose_voice_locked_brief_records_artefact
  test_compose_voice_locked_brief_refuses_max_pair_cofront
  test_compose_voice_locked_brief_allows_max_pair_with_override
  test_compose_voice_locked_brief_no_alter_bound_fails_clean
  test_exemplar_pool_returns_n_examples
  test_exemplar_pool_rotates_deterministically_by_intent_id
  test_voice_drift_audit_passes_in_voice_draft
  test_voice_drift_audit_flags_forbidden_lexicon
  test_voice_drift_audit_flags_taboo_violation
  test_voice_drift_audit_reports_register_match_score
  test_voice_drift_audit_detects_leaked_to_other_alter
  test_voice_drift_audit_passes_when_no_signature_required
  test_scene_writer_phase1_chains_voice_lock_when_alter_present
  test_scene_writer_phase1_falls_back_to_plain_brief_without_alter
  test_lint_rejects_voice_profile_with_oversized_taboo_block
  test_lint_passes_canonical_kp_alter_profile
```

## Open questions

1. Should the §EXAMPLES rotation be deterministic-by-intent or random?
   **Recommend**: deterministic by intent — reproducibility wins; an
   author chaining a long drafting run wants stable inputs for
   bisection when something drifts.
2. Voice-drift audit's `register_match_score` — heuristic or
   driver-mediated? **Recommend**: heuristic v1 (n-gram + lexicon
   overlap); a future LLM-judge Driver can replace it without changing
   the verb signature.
3. Should `compose_voice_locked_brief` accept multiple alters when the
   scene legitimately switches mid-scene? **Recommend**: no for v1 —
   force the author into one alter per scene OR explicit switching;
   the multi-alter case is a Slice-2 compositional verb that calls
   this one N times and stitches.

## Followup

(Populated when the PR ships.)
