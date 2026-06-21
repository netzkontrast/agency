---
spec_id: "143"
slug: kohaerenz-prompt-fragments
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["129", "136", "138", "139", "140", "141"]
affects:
  - agency/capabilities/prompt/_main.py
  - agency/capabilities/novel/data/dramatica/ontology.json
  - agency/capabilities/novel/data/kp-fragments.yaml  # NEW
  - tests/test_kohaerenz_prompt_fragments.py
domain: novel / prompt / kohaerenz
parent_spec: "101"
mvp-source:
  - "examples/kohaerenz-protokoll/02_begriffe-und-konzepte.md (§10 narrative modes, §11 Vortex, §12 Genesis-Ouroboros)"
  - "examples/kohaerenz-protokoll/03_anteile-profile-sprach-dna.md (full Sprach-DNA per alter)"
  - "examples/kohaerenz-protokoll/05_welt-sensorik-drafting.md (§10 R-rules as prose rules)"
  - "examples/kohaerenz-protokoll/06_philosophie-im-detail.md (§15 six synthesis movements)"
---

# Spec 143 — Kohärenz-Protokoll deep prompt fragments

## Why

Spec 129 vendored 304 Dramatica fragments (`prompt.fragment`,
`prompt.fragments_for`) — the *theory-side* prompt vocabulary. The
Kohärenz Protokoll wave (Specs 136–141) introduced concepts Dramatica
doesn't have words for: dual-storyform routing, Klein-c inversion,
mode-blocks, audience-tier reveals, R-rules, motif discipline, plural
voice. Each is a node-class in the graph (Spec 136–141) — but each is
ALSO a recurring drafting prompt the LLM needs spelled out.

Without those fragments, the verbs on 136–141 wire data into the graph
but the *prompt* that an LLM driver runs against the verb's output is
hand-rolled every time. Spec 129's compose-pattern wins exactly when
there's a vocabulary; this spec extends it to the KP vocabulary, while
keeping all of it project-overlay-able (so non-KP novels don't see KP
fragments by default).

## Done When

- [ ] **`kp-fragments.yaml` vendored** at
      `agency/capabilities/novel/data/kp-fragments.yaml` — a sibling
      overlay registered via Spec 129's overlay mechanism. Ships ~60
      hand-authored fragments across 6 families (≤300 cl100k tokens each):

      1. **Plurality family** (~15 fragments) — one per ALTER_CATEGORY
         + one per documented Sprach-DNA archetype (Fight / Freeze /
         Caregiver / Rationalist / Witness / Mirror …). Each fragment
         tells an LLM how a scene fronting that alter SHOULD read:
         syntax, register, taboo, somatik tags. Slug pattern:
         `kp.alter.<archetype>`.

      2. **Klein-c & dual-storyform family** (~8 fragments) — slot
         pairs as prompts ("In an A-storyform scene the MC operates
         from Mind; in the parallel B scene the MC operates from
         Universe — they mirror, never resolve in this beat") +
         routing-mode fragments (`kp.route.hard`, `kp.route.soft`,
         `kp.transition.operative`, `kp.transition.ontological`,
         `kp.transition.synthesis`).

      3. **Mode-block family** (~10 fragments) — one per NARRATIVE_MODE
         value (`linear-introspective` / `cyclic-recursive` /
         `linear-ascending` / `vortex-still` / `choral` / `framing`)
         + one per genre accent (`philosophical-horror`, `literary-sf`,
         `technothriller`, `choral-drama`, `metaphysical-climax`,
         `spiritual-apotheosis`). Slug pattern: `kp.mode.<value>`,
         `kp.genre.<value>`.

      4. **Reveal-tier family** (~9 fragments) — one per AUDIENCE_TIER
         (reader / pov / antagonist), one per REVEAL_CHANNEL
         (glitch / log / sensory / dialogue / metaphor / narration),
         and three veil-fragments (`kp.veil.maintain`,
         `kp.veil.leak-via-glitch`, `kp.veil.payoff`).

      5. **R-rule family** (~10 fragments) — one per canonical R-rule
         (R-4 micro-cue-cap, R-5 hot-polarity, R-6 one-concept-cap,
         R-7 genesis-echo-cap, R-8 AEGIS-register, R-9 no-style-mimicry)
         + four predicate-kind fragments (mutual-exclusion,
         per-scene-budget, forbidden-verbatim, register-forbidden) that
         tell an LLM how to author a NEW R-rule.

      6. **Synthesis-movements family** (~6 fragments) — one per of the
         six synthesis movements from §15 of the philosophy doc
         (philosophical → narratological → editorial → ontological →
         epistemological → reader-experiential). These are
         *thinking-prompts*, not drafting prompts — feed them to a
         critique pass when an author asks "is this scene doing what
         it should be doing at this beat?".

- [ ] **`prompt.fragments_for_scope(scope)`** extension — `scope` accepts
      KP-specific keys: `{mode_block, audience_tier, alter_id,
      routing_mode, r_rule_id, …}`. The verb maps each to its fragment
      slug(s) and composes, respecting the existing ≤2000-token cap
      with `truncated: True` signalling. Returns existing
      `[{slug, kind, text, tokens}]` shape — no new return contract.

- [ ] **`prompt.compose_drafting_brief(scene_id)`** — new convenience
      verb. Reads the scene's chapter / mode-block / fronting alter /
      active reveal-rules / required R-rules, calls
      `fragments_for_scope` per slice, deduplicates, returns a single
      composed brief STRING (newline-joined) + the `sources` list of
      fragment slugs that contributed. The LLM-side counterpart of
      Spec 127's `assemble_scene_brief` (which is graph-side).

- [ ] **Fragment lint extension** — Spec 129's lint already enforces
      ≤300-token cap; extends to require fragments in `kp-fragments.yaml`
      to carry a `slug` matching `^kp\\.[a-z]+(\\.[a-z0-9-]+)+$` and a
      `family` field ∈ the six above.

- [ ] **Overlay isolation** — the YAML loads only when the novel cap
      detects a `CharacterSystem` node (Spec 138) OR a `StoryformSet`
      node (Spec 136) OR explicit author opt-in
      (`Engine(..., kp_fragments=True)`). Non-KP novels see only Spec
      129's 304 Dramatica fragments — no contamination.

- [ ] **One golden composition test per family** — six end-to-end
      compositions assert the right fragments compose for a fixture
      KP scene, total tokens ≤ 2000, no missing fragment errors.

- [ ] TODO row + drift clean.

## Design notes

- **Why a YAML overlay, not back into `ontology.json`?** KP fragments
  belong to a *project*, not the universal Dramatica vocabulary. Spec
  129 already supports overlay; this is the first non-bootstrap
  overlay. Future novels (each their own canon) get their own YAML.
- **Why include the synthesis movements as prompts?** §15 of the
  philosophy doc names six axes any scene can be critiqued on. They're
  thinking-prompts — not "how to write" but "how to evaluate what was
  written". They feed into the editorial-gate pipeline (Spec 122) +
  the future critique loop, not the drafting loop directly.
- **The 6 families map 1:1 to the spec wave.** Plurality↔138,
  klein-c↔136, mode-block↔141, reveal↔139, R-rule↔140, synthesis is
  cross-cutting + sits with 139's reader-function-audit. Discoverable
  by family lookup; composable in any combination.
- **Token budget is firm.** 60 fragments × ≤300 tokens = ≤18k
  fragment corpus; any single compose call still ≤2000 by Spec 129's
  cap. The composer prefers higher-specificity fragments (alter slug
  beats archetype beats category) and drops generic ones first when
  truncating.

## Verb signatures

```python
def fragments_for_scope(scope: dict) -> dict:
    """Existing Spec 129 verb; extended to accept KP scope keys.
    KP scope keys (all optional):
      mode_block:     str   # one of NARRATIVE_MODE
      audience_tier:  str   # one of AUDIENCE_TIER
      routing_mode:   str   # "hard" | "soft"
      alter_id:       str   # → look up Alter node + voice profile
      r_rule_ids:     [str] # list of registered R-rule ids
      genre_accent:   str
      reveal_channels:[str]
      family:         str   # explicit family filter
    Returns: {fragments: [{slug, kind, text, tokens, family, source}],
              total_tokens, truncated}
    """

def compose_drafting_brief(scene_id: str, max_tokens: int = 2000) -> dict:
    """Reads the scene's KP context (mode-block, fronting alter, active
    reveal-rules, required R-rules, codex matches) and composes one
    newline-joined brief.
    Returns: {
      scene_id: str,
      brief: str,                   # newline-joined fragment chain
      sources: [{slug, family, tokens}…],
      truncated: bool,
      total_tokens: int,
    }
    """
```

## Test scaffold

```text
tests/test_kohaerenz_prompt_fragments.py  (target ≥ 18 tests)
  test_kp_fragments_yaml_loads_when_storyform_set_present
  test_kp_fragments_skipped_for_non_kp_novel
  test_fragment_slug_pattern_lint
  test_fragment_family_field_required
  test_plurality_family_one_per_category
  test_klein_c_family_routes_and_transitions
  test_mode_block_family_one_per_mode
  test_genre_accent_family_one_per_accent
  test_reveal_tier_family_one_per_tier
  test_r_rule_family_one_per_canonical_rule
  test_synthesis_movements_family_six_entries
  test_fragments_for_scope_alter_id_resolves_voice
  test_fragments_for_scope_truncates_at_2000
  test_fragments_for_scope_prefers_specific_over_generic
  test_compose_drafting_brief_reads_mode_block
  test_compose_drafting_brief_reads_fronting_alter
  test_compose_drafting_brief_reads_active_reveal_rules
  test_compose_drafting_brief_reads_required_r_rules
  test_compose_drafting_brief_truncated_flag_on_budget_exceeded
  test_compose_drafting_brief_artefact_recorded
```

## Open questions

1. **Naming overlap.** Should the YAML live under `data/` (vendored,
   shipped) or under `.agency/` (project-local, gitignored)?
   **Recommend**: vendored under `data/kp-fragments.yaml` AND a
   project-local `.agency/kp-fragments-overlay.yaml` that overrides —
   same pattern as Spec 129 (vendored + overlay). The vendored set is
   the canonical KP corpus; the overlay lets a project iterate.
2. **Multilingual fragments?** KP is German; fragments are also
   German. Spec 129's bootstrap is English. **Recommend**: fragments
   carry an optional `lang` field (default "en"); the composer prefers
   the novel's `Novel.language` match. KP fragments ship `lang: de`.
3. **Synthesis movements: prompts or check-verbs?** They could become
   six new `thinking.*` verbs (Spec 110). **Recommend**: ship as
   fragments first (cheap); promote to verbs when a critique-loop
   actually uses them programmatically. The fragment-form keeps the
   author in control of WHEN to apply them.

## Followup

(Populated when the PR ships.)
