---
spec_id: "138"
slug: plural-character-system
status: draft
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["101", "123", "134"]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_plural_character.py
domain: novel / character / dissociation
parent_spec: "101"
mvp-source:
  - "examples/kohaerenz-protokoll/03_anteile-profile-sprach-dna.md (full doc — 13 alters, ANP/EP, conflict matrix, switching)"
  - "examples/kohaerenz-protokoll/01_storyform-und-outline.md (§4 Figuren-Kurzanker, TSDP-Architektur)"
---

# Spec 138 — Plural-character system (dissociative-system model)

## Why

The Kohärenz Protokoll's protagonist is **not one person** — it is a *system*
(Kael) of 13 alters under a clinical TSDP (tertiary structural dissociation)
architecture: ANP (apparently-normal) / EP (emotional) / Sonder / Spiegel
categories, a phobia-driven inter-alter **conflict matrix**, two trauma
**layers** (Schicht 1 / Schicht 2), and a switching mechanic where alters are
**never labeled in the prose** — recognized only by syntax + somatik + lexicon.
The resolution is *functional multiplicity, never fusion*.

Spec 123 Slice 2 (drafted) adds `PsychProfile` (big-five/enneagram/ifs/jung) +
`Trait` — but that models ONE psyche. Spec 134 (drafted) adds a `VoiceProfile`
— but a single voice per character. Neither expresses a plural system: the
roster, the categories, the conflict matrix, the layer-assignment, the
"recognized not named" discipline, the no-fusion resolution constraint. This
is the character architecture the KP is built on, and it generalizes to any
DID/plural-narrator novel.

## Done When

- [ ] **`CharacterSystem` node** `{novel, name, model}` — the host system
      (Kael). `model` documents the clinical frame (TSDP / OSDD / authored).
- [ ] **`Alter` node** `{system_id, name, category, layer, function}` +
      `ALTER_OF` edge → CharacterSystem. `category` ∈ `ALTER_CATEGORY`
      (`anp` / `ep` / `special` / `mirror`); `layer` ∈ `TRAUMA_LAYER`
      (`layer-1` / `layer-2` / `cross-layer`); `function` is freeform
      (Fight / Freeze / Caregiver / Rationalist / …).
- [ ] **`PHOBIA_OF` typed edge** Alter → Alter with a `vector` prop
      (`anp-ep` / `anp-anp` / `ep-ep` / `mirror`) and an `intensity`
      (`max` / `phobic-avoidance` / `friction` / `ambivalent`). This is the
      conflict matrix — the "Klebstoff" that holds the dissociative
      architecture together.
- [ ] **Verbs**:
      - `create_character_system(novel_id, name, model)` — mints the system.
      - `add_alter(system_id, name, category, layer, function)` — adds an
        alter; enum-validates category + layer.
      - `record_alter_conflict(alter_a, alter_b, vector, intensity)` —
        the conflict-matrix edge.
      - `conflict_matrix_report(system_id)` — renders the full
        ANP↔EP / ANP↔ANP / EP↔EP / mirror matrix (the §6 table); flags
        `max`-intensity pairs that must never co-front a scene without a
        voice-collision warning.
      - `assign_voice_to_alter(alter_id, voice_profile_id)` — binds a Spec
        134 `VoiceProfile` to an alter (one voice per alter); the system's
        voices become a discoverable set.
      - `check_alter_recognition(scene_id)` — the "never labeled" discipline:
        scans the scene body for forbidden alter-naming/header patterns
        ("Lex spricht", "[Nyx]", "DID", "Alter") and for the Akt-I veil terms
        forbidden before a configurable reveal chapter. Returns
        `{passed, violations: [{pattern, reason}]}`.
      - `switching_log(system_id, novel_id)` — per scene, which alter is
        inferred to front (from the bound voice signature) + flags scenes
        with > N micro-cues (the "max 3 micro-cues per bridge" R-4 rule).
      - `validate_no_fusion(system_id)` — the resolution constraint: asserts
        no alter is marked `eliminated`/`fused`; the canonical end-state is a
        plural "Wir", not a merged single self. A node flagged fused fails.
- [ ] **Anti-cliché hard-rules** (per-alter, author-authored): an alter can
      carry a `taboo_rules` field (e.g. "never curses, never cries";
      "not cute"; "not moody"; "not depressive"). `check_pov_voice`
      (Spec 134) reads these as hard violations when matched — extends 134
      with the plural-specific anti-cliché layer.
- [ ] TODO row + drift clean.

## Design notes

- **Extends, doesn't replace, 123 + 134.** A `PsychProfile` (123) can attach
  to an Alter via the existing patterns; a `VoiceProfile` (134) binds per
  alter via `assign_voice_to_alter`. 138 is the *plural container*: roster,
  categories, layers, conflict matrix, recognition discipline.
- **Layer-assignment is reveal-relevant.** Schicht-1 alters surface in Akt I
  as background pressure; Schicht-2 reveals in Akt II. The `layer` field feeds
  Spec 139's reveal-timeline (when may which alter become readable).
- **The conflict matrix is the moat.** Any author can list characters; only
  the typed phobia-matrix + the `max`-pair co-front warning encodes the
  *clinical* truth that two specific alters destabilize each other on the page.
- **No-fusion is a hard invariant**, not a style note — the KP forbids final
  fusion absolutely; `validate_no_fusion` makes that machine-checkable.

## Open questions

1. Should the Spiegel (mirror) alters get a typed edge to the *external*
   force they mirror (Silas↔Juna, Oblivion↔AEGIS)? **Recommend**: yes —
   a `MIRRORS` edge from Alter → (external entity node), so the
   "ouroboros: what happens outside happens inside" architecture is queryable.
2. Veil-reveal chapter as a system property or a Spec-139 reveal-rule?
   **Recommend**: Spec 139 owns reveal-timelines; 138's
   `check_alter_recognition` reads the threshold from there when 139 ships,
   else from a verb arg.

## Followup

(Populated when the PR ships.)
