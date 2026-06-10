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

## Schema

```text
# New nodes
StoryformSet {
  novel:  str         # novel_id (FK)
  label:  str         # "kohaerenz-protokoll-dual-A-B"
  count:  int         # 2 for KP, N-ary
}

StoryformTransition {
  storyform_set_id: str   # FK
  from_role:        str   # "primary" | "secondary" | …
  to_role:          str
  at_chapter:       int   # chapter where the transition centres
  kind:             str   # ∈ STORYFORM_TRANSITION_KIND
}

# Extends existing Storyform node (additive — open-set property)
Storyform.role: str       # "primary" | "secondary" | "tertiary"…
                          # Defaults absent for single-storyform novels.

# New enums
STORYFORM_TRANSITION_KIND = {"operative", "ontological", "synthesis"}
SCENE_ROUTE_MODE          = {"hard", "soft"}

# New edges
MEMBER_OF   : Storyform           --→ StoryformSet     (cardinality N:1)
ROUTED_TO   : Scene               --→ Storyform        (cardinality N:1 per mode;
                                                        a scene can have one
                                                        ROUTED_TO[mode=hard] OR
                                                        two ROUTED_TO[mode=soft])
TRANSITIONS : StoryformTransition --→ StoryformSet     (cardinality N:1)
```

## Verb signatures

```python
def create_storyform_set(novel_id: str, label: str, count: int = 2) -> dict:
    """Returns: {set_id, label, count}"""

def add_storyform_to_set(storyform_id: str, set_id: str, role: str) -> dict:
    """Mints MEMBER_OF; stamps Storyform.role.
    Returns: {storyform_id, set_id, role, set_membership_count}
    Raises: ValueError when role collides with an existing member's role.
    """

def check_klein_c_inversion(storyform_set_id: str) -> dict:
    """Verify involutive symmetry across the two slot dimensions.
    Returns: {
      passed: bool,
      class_pair: {a_mc, b_mc, a_os, b_os, inverted: bool},
      dynamics: {
        resolve:  {a, b, inverted: bool},
        growth:   {a, b, inverted: bool},
        approach: {a, b, inverted: bool},
        style:    {a, b, inverted: bool},
        driver:   {a, b, inverted: bool},
        limit:    {a, b, inverted: bool},
        outcome:  {a, b, inverted: bool},
        judgment: {a, b, inverted: bool},
      },
      non_inverted: [{slot, a_value, b_value}…]   # the failure list
    }
    Math: V₄ = Z₂(class) × Z₂(dynamics); each Z₂ check is independent.
    Pass condition: both Z₂ flips hold (all 8 dynamics inverse AND class-pair swap).
    """

def record_storyform_transition(
    storyform_set_id: str,
    from_role: str,
    to_role: str,
    at_chapter: int,
    kind: str,
) -> dict:
    """Returns: {transition_id, …}; Raises on unknown kind."""

def check_driver_transition_legality(transition_id: str) -> dict:
    """Returns: {
      passed: bool,
      from_driver: str,          # e.g. "Action"
      to_driver:   str,          # e.g. "Decision"
      same_storyform: bool,      # true → illegal (Dramatica forbids driver-flip)
      verdict: str,              # "legal-transition" | "illegal-within-storyform"
    }
    """

def route_scene_storyform(
    scene_id: str,
    primary_role: str,
    mode: str = "hard",
    secondary_role: str = "",
) -> dict:
    """Mints ROUTED_TO edge(s) with mode.
    `mode=hard`  → single edge to the primary_role's Storyform.
    `mode=soft`  → two edges (primary + secondary), both readings simultaneously true.
    Returns: {scene_id, mode, routed_storyforms: [storyform_id…]}
    Raises: ValueError when mode=soft and secondary_role is empty/same as primary.
    """

def bridge_frequency_report(novel_id: str) -> dict:
    """Per mode-block (Spec 141 IN_MODE_BLOCK), the share of soft-routed scenes.
    Returns: {
      blocks: [{label, from_chapter, to_chapter,
                soft_share, target, deviation, verdict}…],
      curve_intact: bool,   # True iff soft_share monotone non-decreasing through Vortex
    }
    Targets per KP §1: Akt I ~0.10, Akt II ~0.25, Akt III-A ~0.40, Vortex 1.00.
    Deviation > 0.15 from a configured target flags the block.
    """

def dual_storyform_coherence_check(storyform_set_id: str) -> dict:
    """Composite: runs novel_coherence_check on each member + Klein-c +
    transition legality for every recorded transition.
    Returns: {
      passed: bool,
      members:    [{role, storyform_id, coherence: <novel_coherence_check-output>}],
      inversion:  <check_klein_c_inversion-output>,
      transitions:[{transition_id, legality: <check_driver_transition_legality-output>}],
      bridge:     <bridge_frequency_report-output>,
      artefact_id: str,    # the dual-storyform-report Artefact this records
    }
    """
```

## Test scaffold

```text
tests/test_novel_dual_storyform.py  (target ≥ 18 tests)
  test_storyform_set_node_registered
  test_storyform_role_field_extends_storyform
  test_create_storyform_set_count_default_2
  test_add_storyform_to_set_mints_MEMBER_OF_and_role
  test_add_storyform_to_set_rejects_role_collision
  test_check_klein_c_passes_canonical_kohaerenz_fixture
  test_check_klein_c_fails_when_dynamics_not_inverse
  test_check_klein_c_fails_when_class_pair_same
  test_check_klein_c_lists_non_inverted_slots
  test_storyform_transition_kind_enum_validated
  test_record_storyform_transition_happy_path
  test_check_driver_transition_legality_legal_handoff
  test_check_driver_transition_legality_illegal_within_storyform
  test_route_scene_storyform_hard_single_edge
  test_route_scene_storyform_soft_two_edges
  test_route_scene_storyform_soft_rejects_missing_secondary
  test_bridge_frequency_report_curve_intact
  test_bridge_frequency_report_flags_deviation
  test_dual_storyform_coherence_check_composes_all
  test_dual_storyform_coherence_records_artefact
  test_backward_compat_single_storyform_unchanged
```

## Fixture (canonical KP slot table — for klein-c test)

```text
A storyform (Kael):                  B storyform (AEGIS):
  MC class    = Mind                   MC class    = Universe
  OS class    = Psychology             OS class    = Physics
  Resolve     = Steadfast              Resolve     = Change
  Growth      = Stop                   Growth      = Start
  Approach    = Be-er                  Approach    = Do-er
  Style       = Holistic               Style       = Linear
  Driver      = Decision               Driver      = Action
  Limit       = Optionlock             Limit       = Timelock
  Outcome     = Success                Outcome     = Failure
  Judgment    = Good                   Judgment    = Bad

Klein-c check passes IFF every row's A ≠ B AND the pair is the documented inverse.
```

## Open questions

1. Should `route_scene_storyform` reject a hard-routed scene that contradicts
   the chapter's mode-block default (Spec 141)? **Recommend**: warn, don't
   block — the author may have a deliberate exception.
2. Klein-c verification when the two NCPs use different slot vocabularies?
   **Recommend**: require both to validate against the same NCP schema first
   (Spec 120's checks) before comparing — fail fast on schema mismatch.
3. The synthesis-kind transition (c, leaving Klein-c) — should it be a separate
   verb or a `kind` value on `StoryformTransition`? **Recommend**: keep it a
   `kind` value (`synthesis`) — a transition out of the symmetry group is still
   a storyform-transition; only the post-condition (the symmetry no longer holds
   thereafter) differs, and `dual_storyform_coherence_check` re-runs
   inversion-check only over chapters BEFORE the synthesis transition.

## Followup

(Populated when the PR ships.)
