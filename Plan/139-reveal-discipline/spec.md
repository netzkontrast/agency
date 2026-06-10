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

## Open questions

1. Should `fact` be a freeform string or a ref to a graph node (CodexEntry /
   Alter / StoryTimeEvent)? **Recommend**: accept both — a string for abstract
   reveals ("AEGIS is K₀ not K₁"), a node-id when the fact IS a node.
2. Veil-term set per-novel or shared default? **Recommend**: per-novel arg
   with a documented default (`{DID, Alter, Fragment, ANP, EP, TSDP}`); other
   novels have other veils.

## Followup

(Populated when the PR ships.)
