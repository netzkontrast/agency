---
spec_id: "139"
slug: reveal-discipline
status: draft
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["101", "128", "131", "138"]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_reveal_discipline.py
domain: novel / reader-steering / continuity
parent_spec: "101"
mvp-source:
  - "examples/kohaerenz-protokoll/05_welt-sensorik-drafting.md (§6 Reveal-Disziplin — drei Bewusstseins-Schichten, Reveal-Timeline)"
  - "examples/kohaerenz-protokoll/02_begriffe-und-konzepte.md (§13 Lesersteuerung, Iser'sche Leerstellen, drei Layer der Reader-Funktion)"
---

# Spec 139 — Reveal-discipline & reader-steering

## Why

"Lesersteuerung als oberstes Prinzip": in every encoding and drafting
decision the Kohärenz Protokoll asks — *what must the reader know when, what
may they NOT know when, through what do they learn it?* The novel runs a
**multiplicity-veil** that holds until ~ch13 (the reader feels Kael's
plurality only through glitches, never named), a per-information reveal-
timeline across **three audience tiers** (Reader / POV-character / the AEGIS
antagonist), and Iser-style deliberate "Leerstellen" (gaps the reader fills).

Spec 131 (character-knowledge) tracks what a *character* knows by narrative
position. But there is no surface for what the **reader** may know vs the
**POV** vs the **antagonist** — three distinct knowledge horizons that the KP
manipulates independently (e.g. the reader knows AEGIS from ch0; Kael never
knows he is a system until ch13; AEGIS is structurally blind to Juna forever).
Without it, a drafting agent can't tell whether a scene leaks a reveal early.

## Done When

- [ ] **`AUDIENCE_TIER` enum** = `{reader, pov, antagonist}` — the three
      knowledge horizons.
- [ ] **`RevealRule` node** `{novel, fact, tier, may_know_from_chapter,
      must_not_before, channel}` — for a given fact + audience tier, the
      earliest chapter that tier may know it (`may_know_from_chapter`),
      optionally a hard "must not appear before" floor (`must_not_before`),
      and `channel` (how it is learned — glitch / log / sensory / dialogue).
- [ ] **`GOVERNS_REVEAL` edge**: RevealRule → (Scene | CodexEntry | Alter | …)
      — the fact-bearing node the rule constrains.
- [ ] **Verbs**:
      - `set_reveal_rule(novel_id, fact, tier, may_know_from_chapter,
        must_not_before="", channel="")` — mints/updates a rule.
      - `check_reveal_timing(scene_id, fact)` — given a scene (with a chapter
        number) and a fact, returns `{ok, violations: [{tier, rule,
        verdict}]}`: a violation fires when the scene's chapter precedes a
        tier's `must_not_before` (premature reveal) for content present in
        the scene. Returns `ok=True` with `no_rule=True` when no rule governs.
      - `reveal_timeline_report(novel_id, tier="")` — the full per-tier
        timeline: every RevealRule sorted by `may_know_from_chapter`; the
        author's "who knows what when" map. The KP's §6.2 Reveal-Timeline.
      - `check_veil(novel_id, veil_term_set, hold_until_chapter)` — the
        multiplicity-veil scan: any chapter before `hold_until_chapter` whose
        body contains a veil term (`DID`, `Alter`, `Fragment`, `ANP`, `EP`,
        `TSDP`) is a veil breach. Returns the breaching chapters + terms.
        (Pairs with Spec 138 `check_alter_recognition` — that checks naming
        *form*; this checks reveal *timing*.)
      - `record_leerstelle(scene_id, kind, note)` — registers a deliberate
        Iser gap (`fragmented-perspective` / `contradictory-footnote` /
        `temporal-scramble` / `pronoun-shift`) so a reviewer sees the gap is
        intentional, not a defect. `leerstellen_report(novel_id)` lists them.
      - `reader_function_audit(scene_id)` — tags which of Iser's three
        reader-layers a scene serves (narratological / phenomenological /
        operative) — the KP's "reader-as-substrate" check that a scene gives
        the reader something to *assemble*, not just consume.
- [ ] **`reveal_gate(novel_id)`** composite — passes IFF no scene breaches a
      `must_not_before` floor for any tier AND the veil holds through its
      configured chapter. Drops into the editorial pipeline (Spec 122) as a
      pre-publication discipline.
- [ ] TODO row + drift clean.

## Design notes

- **Three tiers, independently tracked.** The reader/POV/antagonist horizons
  are orthogonal — the KP exploits all three. `check_reveal_timing` checks a
  scene against every tier's rule independently.
- **Complements 131, doesn't duplicate it.** 131 answers "what does character
  X know as of scene Y" (in-world continuity). 139 answers "what may the
  *reader* know as of chapter N" (authorial reveal-steering). Different
  horizons; the KP needs both.
- **Veil = timing; recognition (138) = form.** A chapter can name no alters
  (138 passes) yet still leak the *concept* of plurality early (139 veil
  fails), or vice versa. Two checks, two failure modes.
- **Leerstellen are first-class.** Registering an intentional gap stops a
  later prose-lint from "fixing" a deliberate indeterminacy — the KP's
  contradictory footnotes and temporal scrambling are features.

## Schema

```text
# New enums
AUDIENCE_TIER  = {"reader", "pov", "antagonist"}
REVEAL_CHANNEL = {"glitch", "log", "sensory", "dialogue", "metaphor", "narration", ""}
LEERSTELLE_KIND = {
  "fragmented-perspective", "contradictory-footnote",
  "temporal-scramble", "pronoun-shift",
}
READER_LAYER = {"narratological", "phenomenological", "operative"}

# New nodes
RevealRule {
  novel:                    str
  fact:                     str   # freeform OR a node-id
  fact_node_id:             str   # populated when fact IS a node-ref ("" otherwise)
  tier:                     str   # ∈ AUDIENCE_TIER
  may_know_from_chapter:    int
  must_not_before:          int   # 0 = no hard floor (uses may_know_from_chapter)
  channel:                  str   # ∈ REVEAL_CHANNEL
  rationale:                str
}

Leerstelle {
  novel:    str
  scene_id: str
  kind:     str   # ∈ LEERSTELLE_KIND
  note:     str
}

# New edges
GOVERNS_REVEAL : RevealRule --→ <fact-bearing-node>   (cardinality N:N optional)
HAS_GAP        : Leerstelle --→ Scene                  (cardinality N:1)
```

## Verb signatures

```python
def set_reveal_rule(
    novel_id: str,
    fact: str,
    tier: str,
    may_know_from_chapter: int,
    must_not_before: int = 0,
    channel: str = "",
    rationale: str = "",
    fact_node_id: str = "",
) -> dict:
    """Mints/updates a RevealRule (upsert keyed by (novel_id, fact, tier)).
    Returns: {rule_id, novel_id, fact, tier, may_know_from_chapter,
              must_not_before, channel, was_update: bool}
    Raises on unknown tier/channel.
    """

def check_reveal_timing(scene_id: str, fact: str = "") -> dict:
    """For a scene (+ chapter), check every rule governing the fact(s)
    detected in the scene body. When `fact` is empty, scans the scene
    for ALL rules' facts (substring match, case-insensitive) and checks
    each hit.
    Returns: {
      ok: bool,
      chapter: int,
      violations: [{tier, rule_id, fact, must_not_before, verdict}…],
      no_rule: bool,    # true when no rule governs anything in the scene
    }
    Verdict: "premature-reveal" when scene.chapter < rule.must_not_before
             (or < may_know_from_chapter when must_not_before == 0).
    """

def reveal_timeline_report(novel_id: str, tier: str = "") -> dict:
    """The §6.2 timeline. Sorted by may_know_from_chapter ASC.
    Returns: {
      by_tier: {tier: [{rule_id, fact, may_know_from_chapter,
                        must_not_before, channel}…]},
      total: int,
    }
    """

def check_veil(
    novel_id: str,
    veil_terms: str = "DID,Alter,Fragment,ANP,EP,TSDP",
    hold_until_chapter: int = 13,
) -> dict:
    """Scans every chapter < hold_until_chapter for any veil term.
    Returns: {
      passed: bool,
      breaches: [{chapter, scene_id, term, snippet}…],
      veil_terms_checked: [str…],
      hold_until: int,
    }
    """

def record_leerstelle(scene_id: str, kind: str, note: str) -> dict:
    """Returns: {leerstelle_id, scene_id, kind, note}; raises on unknown kind."""

def leerstellen_report(novel_id: str) -> dict:
    """Returns: {gaps: [{leerstelle_id, scene_id, chapter, kind, note}…],
                 by_kind: {kind: count}}"""

def reader_function_audit(scene_id: str) -> dict:
    """Tags which of Iser's three reader-layers the scene serves.
    Returns: {
      scene_id: str,
      layers_served: [str…],         # subset of READER_LAYER
      gives_reader_assembly_work: bool,
      missing_layers: [str…],
    }
    Heuristic (decidable): narratological iff at least one Leerstelle of
    kind ∈ {temporal-scramble, fragmented-perspective}; phenomenological
    iff scene has sensoric markers (Spec 140 motif/anchor refs);
    operative iff scene chains into another scene's Leerstelle resolution.
    """

def reveal_gate(novel_id: str) -> dict:
    """Composite. Passes iff:
      - check_reveal_timing(scene) has no `premature-reveal` for ANY scene
      - check_veil(novel_id) passes
    Returns: {
      passed: bool,
      premature_reveals: [{scene_id, …}…],
      veil_breaches: [{chapter, term, …}…],
    }
    """
```

## Test scaffold

```text
tests/test_novel_reveal_discipline.py  (target ≥ 20 tests)
  test_audience_tier_enum_registered
  test_reveal_channel_enum_registered
  test_leerstelle_kind_enum_registered
  test_set_reveal_rule_upsert_by_key
  test_set_reveal_rule_rejects_unknown_tier
  test_check_reveal_timing_passes_after_must_not_before
  test_check_reveal_timing_flags_premature
  test_check_reveal_timing_no_rule_returns_ok
  test_check_reveal_timing_multi_tier_independent
  test_reveal_timeline_report_sorted_by_chapter
  test_reveal_timeline_report_filtered_by_tier
  test_check_veil_passes_after_hold_chapter
  test_check_veil_flags_breach_before_chapter
  test_check_veil_custom_terms
  test_record_leerstelle_happy_path
  test_record_leerstelle_rejects_unknown_kind
  test_leerstellen_report_grouped_by_kind
  test_reader_function_audit_tags_narratological
  test_reader_function_audit_tags_phenomenological
  test_reader_function_audit_tags_operative
  test_reveal_gate_passes_clean_manuscript
  test_reveal_gate_fails_on_premature_reveal
  test_reveal_gate_fails_on_veil_breach
```

## Open questions

1. Should `fact` be a freeform string or a ref to a graph node (CodexEntry /
   Alter / StoryTimeEvent)? **Recommend**: accept both — a string for abstract
   reveals ("AEGIS is K₀ not K₁"), a node-id when the fact IS a node.
2. Veil-term set per-novel or shared default? **Recommend**: per-novel arg
   with a documented default (`{DID, Alter, Fragment, ANP, EP, TSDP}`); other
   novels have other veils.
3. Should `check_reveal_timing` scan ALL rules' facts when `fact=""` or
   require an explicit fact arg? **Recommend**: scan-all on empty; this is
   the editorial-pipeline use-case (Spec 122 chains it on every scene),
   which can't enumerate every rule by hand.
4. `reader_function_audit` heuristic — decidable proxy vs LLM judgement?
   **Recommend**: decidable proxy (specified above); the KP wants
   machine-checkable, and "narratological/phenomenological/operative" map
   cleanly onto graph features. LLM-grade Iser-analysis is out of scope.

## Followup

(Populated when the PR ships.)
