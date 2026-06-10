---
spec_id: "136"
slug: dual-storyform-architecture
status: draft
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["103", "120", "128"]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_dual_storyform.py
domain: novel / storyform / post-dramatica
parent_spec: "101"
mvp-source:
  - "examples/kohaerenz-protokoll/01_storyform-und-outline.md (§2 Dual-Storyform A‖B, full spec)"
  - "examples/kohaerenz-protokoll/02_begriffe-und-konzepte.md (§9 Dual-Storyform als post-Dramatica-Innovation)"
---

# Spec 136 — Dual-Storyform architecture (post-Dramatica)

## Why

The whole Dramatica engine (Spec 103/120) assumes **one** storyform per
novel — `Storyform` is a single node, `novel_coherence_check` validates a
single NCP body. The Kohärenz Protokoll is built on **two simultaneous,
complete storyforms** in one work (A = *Heuristics of Integration*, Kael-MC;
B = *Phoenix Collapse*, AEGIS-MC), related by an involutive Klein-c inversion
symmetry, with a structured **Vortex** where storyform B is overtaken by A,
and then a post-orthodox synthesis (c) that leaves the Klein-c scheme.

Dramatica cannot express this — it knows one Grand Argument Story plus
subordinated subplots. The KP authors call it a "post-Dramatica innovation"
and *the defining structural decision of the project*. Without it, the engine
can validate either A or B but never their **inversion symmetry**, never the
storyform-transition, never per-scene routing between two live storyforms.

## Done When

- [ ] **`StoryformSet` node** `{novel, label, count}` — groups N storyforms
      under one novel; `count` is the number of simultaneous forms (2 for KP,
      but the design is N-ary, not hard-coded to 2).
- [ ] **`Storyform` gains a `role` field** (`primary` | `secondary` | …) +
      `MEMBER_OF` edge to the StoryformSet. Existing single-storyform novels
      get an implicit 1-member set (backward compatible — `novel_coherence_check`
      still works on a lone Storyform).
- [ ] **`check_klein_c_inversion(storyform_set_id)`** — verifies the
      involutive symmetry between two storyforms across the documented slot
      pairs: class-swap (A-MC=Mind ↔ B-MC=Universe; A-OS=Psychology ↔
      B-OS=Physics) **plus** dynamics-inversion (Resolve / Growth / Approach /
      Style / Driver / Limit / Outcome / Judgment all inverse). Returns
      `{passed, inverted_slots, non_inverted: [{slot, a_value, b_value}]}`.
      The Klein-Vierergruppe (V₄ = Z₂×Z₂) structure means the check is two
      independent Z₂ flips — class-pair and dynamics — each verifiable.
- [ ] **`StoryformTransition` node** `{storyform_set_id, from_role, to_role,
      at_chapter, kind}` — records a Vortex: where one storyform overtakes
      another. `kind` ∈ `{operative, ontological, synthesis}` (KP: Vortex 1
      operative B→A at ch35-36; Vortex 2 ontological synthesis at ch38-39).
- [ ] **`check_driver_transition_legality(transition_id)`** — encodes the
      KP "no driver-flip within a storyform (illegal); only storyform
      *transition* B(Action)→A(Decision)" rule. A transition that flips a
      slot *within* one storyform fails; a transition that hands off between
      storyforms passes. The pivot must be a Decision that retroactively
      transforms prior Actions.
- [ ] **`route_scene_storyform(scene_id, mode, primary_role)`** —
      per-chapter dual-POV routing (KP Hybrid Option 3): `mode` ∈
      `{hard, soft}`. Hard = scene belongs to exactly one storyform;
      Soft = bridge scene where both storyforms' readings are simultaneously
      true. Records a `ROUTED_TO` edge (Scene → Storyform) with the mode.
- [ ] **`bridge_frequency_report(novel_id)`** — per mode-block, the share of
      soft-layered (bridge) scenes; flags blocks that violate the documented
      monotone-increasing curve (~10% Akt I → ~25% Akt II → ~40% Akt III-A →
      100% Vortex). This is the architectural answer to "how do the two
      storyforms interleave."
- [ ] **`dual_storyform_coherence_check(storyform_set_id)`** composite —
      runs `novel_coherence_check` on EACH member storyform + the Klein-c
      inversion check + transition legality; records a
      `dual-storyform-report` Artefact.
- [ ] TODO row + drift clean.

## Design notes

- **N-ary, not binary.** The KP needs 2 but the node design is a set with
  count; a future triple-storyform work is expressible without re-architecting.
- **Backward compatible.** A novel with one Storyform and no StoryformSet
  behaves exactly as today. The set is opt-in; `dual_storyform_coherence_check`
  is a new verb, `novel_coherence_check` is untouched.
- **The inversion check is the moat.** Any author can write two storyforms;
  only the Klein-c check proves they are *the two halves of one severed whole*
  — which is the KP's ontological claim ("the dual-storyform is the form of
  the separation in narrative form").
- Stays graph-only; NCP bodies live on the Storyform nodes' `body` field as
  today.

## Open questions

1. Should `route_scene_storyform` reject a hard-routed scene that contradicts
   the chapter's mode-block default (Spec 141)? **Recommend**: warn, don't
   block — the author may have a deliberate exception.
2. Klein-c verification when the two NCPs use different slot vocabularies?
   **Recommend**: require both to validate against the same NCP schema first
   (Spec 120's checks) before comparing — fail fast on schema mismatch.

## Followup

(Populated when the PR ships.)
