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

## Schema

```text
# New enums
ALTER_CATEGORY  = {"anp", "ep", "special", "mirror"}
TRAUMA_LAYER    = {"layer-1", "layer-2", "cross-layer"}
PHOBIA_VECTOR   = {"anp-ep", "anp-anp", "ep-ep", "mirror"}
PHOBIA_INTENSITY = {"max", "phobic-avoidance", "friction", "ambivalent"}

# New nodes
CharacterSystem {
  novel: str        # FK
  name:  str        # "Kael"
  model: str        # "TSDP" | "OSDD" | "authored"
}

Alter {
  system_id: str    # FK → CharacterSystem
  name:      str    # "Lex", "Nyx", "Echo", "Sonder", "Spiegel-Silas", …
  category:  str    # ∈ ALTER_CATEGORY
  layer:     str    # ∈ TRAUMA_LAYER
  function:  str    # "Fight" | "Freeze" | "Caregiver" | "Rationalist" | …  (freeform)
  taboo_rules: str  # comma-separated anti-cliché rules (read by Spec 134 check_pov_voice)
}

# New edges
ALTER_OF   : Alter --→ CharacterSystem            (cardinality N:1)
PHOBIA_OF  : Alter --→ Alter                       (cardinality N:N; typed)
             props: vector ∈ PHOBIA_VECTOR
                    intensity ∈ PHOBIA_INTENSITY
                    rationale: str (freeform why)
VOICED_BY  : Alter --→ VoiceProfile (Spec 134)    (cardinality 1:1)
MIRRORS    : Alter --→ <external-entity-node>     (cardinality 1:N; mirror-alters only)
```

## Verb signatures

```python
def create_character_system(novel_id: str, name: str, model: str = "TSDP") -> dict:
    """Returns: {system_id, novel_id, name, model}"""

def add_alter(
    system_id: str,
    name: str,
    category: str,
    layer: str,
    function: str = "",
    taboo_rules: str = "",
) -> dict:
    """Enum-validates category + layer.
    Returns: {alter_id, system_id, name, category, layer, function}
    Raises: ValueError on unknown enum value or duplicate name in system.
    """

def record_alter_conflict(
    alter_a: str,
    alter_b: str,
    vector: str,
    intensity: str,
    rationale: str = "",
) -> dict:
    """Mints PHOBIA_OF edge (a→b). To record symmetric phobia, call twice.
    Returns: {edge_id, a, b, vector, intensity}
    Raises on unknown vector/intensity; rejects a==b.
    """

def conflict_matrix_report(system_id: str) -> dict:
    """The §6 matrix.
    Returns: {
      alters: [{id, name, category, layer}…],
      cells: [{from, to, vector, intensity, rationale}…],
      max_pairs: [(a, b)…],   # max-intensity pairs — never co-front a scene
      by_vector: {"anp-ep": int, "anp-anp": int, "ep-ep": int, "mirror": int},
    }
    """

def assign_voice_to_alter(alter_id: str, voice_profile_id: str) -> dict:
    """Mints VOICED_BY. One voice per alter (rebind replaces).
    Returns: {alter_id, voice_profile_id, replaced_voice: <prev-or-empty>}
    """

def check_alter_recognition(
    scene_id: str,
    veil_chapter: int = 13,
    veil_terms: str = "DID,Alter,Fragment,ANP,EP,TSDP",
) -> dict:
    """Scans scene.body for:
      A) forbidden header/labeling patterns regardless of chapter
         (regexes: r'\\[\\w+\\]:?\\s', r'^\\w+ spricht:', '<alter-name>:')
      B) veil terms (csv arg) when scene.chapter < veil_chapter
    Returns: {
      passed: bool,
      violations: [{kind: "header"|"veil", pattern, span: (start, end), reason}…],
      checked_chapter: int,
      veil_active: bool,
    }
    """

def switching_log(system_id: str, novel_id: str) -> dict:
    """Per scene, the inferred fronting alter (matched from VoiceProfile signature
    against scene body) + micro-cue count (R-4: max 3 per bridge).
    Returns: {
      scenes: [{scene_id, chapter, inferred_alter, confidence,
                micro_cue_count, exceeds_cue_cap: bool}…],
      summary: {total_scenes, scenes_with_inference, ambiguous},
    }
    """

def validate_no_fusion(system_id: str) -> dict:
    """Resolution-discipline assertion: no alter may carry a `fused`/`eliminated`
    flag. The KP canon end-state is plural "Wir".
    Returns: {
      passed: bool,
      fused_alters: [{alter_id, name, flag}…],
      total_alters: int,
    }
    """

def record_mirror(alter_id: str, external_node_id: str, rationale: str = "") -> dict:
    """Mints MIRRORS edge. Asserts alter.category == "mirror".
    Returns: {alter_id, external_node_id, rationale}
    """
```

## Test scaffold

```text
tests/test_novel_plural_character.py  (target ≥ 22 tests)
  test_character_system_node_registered
  test_alter_category_enum_validated
  test_trauma_layer_enum_validated
  test_phobia_vector_enum_validated
  test_phobia_intensity_enum_validated
  test_create_character_system_happy_path
  test_add_alter_mints_ALTER_OF
  test_add_alter_rejects_duplicate_name_in_system
  test_add_alter_rejects_unknown_category
  test_record_alter_conflict_mints_PHOBIA_OF
  test_record_alter_conflict_rejects_self_loop
  test_conflict_matrix_report_shape
  test_conflict_matrix_max_pairs_surfaced
  test_assign_voice_to_alter_one_per_alter
  test_assign_voice_to_alter_rebind_replaces
  test_check_alter_recognition_passes_clean_scene
  test_check_alter_recognition_flags_header_pattern
  test_check_alter_recognition_flags_veil_term_before_chapter
  test_check_alter_recognition_allows_veil_term_after_chapter
  test_switching_log_infers_voice_signature
  test_switching_log_flags_excess_micro_cues
  test_validate_no_fusion_passes_canonical_plural
  test_validate_no_fusion_fails_on_fused_flag
  test_record_mirror_requires_mirror_category
  test_taboo_rules_field_round_trips
```

## Fixture (KP 13-alter roster)

```text
ANP (4):     Kael / Lex / Eos / Iren
EP  (4):     Nyx / Echo / Bren / Sol
Special(3):  Sonder, Memory-of-(name), Witness
Mirror(2):   Spiegel-Silas, Spiegel-Oblivion
Layer-1:     Lex, Nyx, Echo, Bren, Spiegel-Silas
Layer-2:     Eos, Iren, Sol, Sonder, Spiegel-Oblivion
Cross:       Kael, Memory-of-(name), Witness
Max-pairs:   (Lex, Nyx), (Eos, Sol), (Kael, Sonder)
```

## Open questions

1. Should the Spiegel (mirror) alters get a typed edge to the *external*
   force they mirror (Silas↔Juna, Oblivion↔AEGIS)? **Recommend**: yes —
   a `MIRRORS` edge from Alter → (external entity node), so the
   "ouroboros: what happens outside happens inside" architecture is queryable.
2. Veil-reveal chapter as a system property or a Spec-139 reveal-rule?
   **Recommend**: Spec 139 owns reveal-timelines; 138's
   `check_alter_recognition` reads the threshold from there when 139 ships,
   else from a verb arg.
3. PHOBIA_OF symmetry — auto-mirror on insert, or require two calls?
   **Recommend**: require two calls — phobic relations are NOT always
   symmetric in the KP (Lex→Nyx is `max`/`anp-ep`; Nyx→Lex may be
   `phobic-avoidance`/`anp-ep`); forcing symmetry would lie.

## Followup

(Populated when the PR ships.)
