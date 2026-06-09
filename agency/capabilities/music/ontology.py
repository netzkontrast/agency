# agency-scaffold: v1
"""music ontology — the consolidated ``OntologyExtension`` (nodes, enums,
edges, skills, schemas, templates) for the music capability.

Spec 094 (lifecycle child of 093) consolidates the ontology into its own
module so subsequent cluster children (095 lyrics, 096 audio, 097
catalogue, 098 promo, 099 research, 100 gates) extend it additively without
churning the cluster code module. Verbs live in ``clusters/*.py`` and
import these constants.

The OntologyExtension is **purely additive** vs the 007 baseline: existing
required fields stay required; new fields land as optional (i.e. not in
the required-list, which is the strict set ``Memory.record`` enforces).
"""
from __future__ import annotations

from agency.ontology import OntologyExtension

ALBUM_TYPES = {"documentary", "narrative", "thematic", "character-study",
               "collection", "ost"}
ALBUM_STATUS = {"draft", "in-production", "mastered", "released"}
TRACK_STATUS = {"draft", "recorded", "mixed", "mastered"}


# the conceptualizer: a 7-phase gated planning skill (foundation → … → confirmation),
# ending in a HARD confirm gate. The engine's skill walker walks it one phase at a time.
ALBUM_CONCEPT_SKILL = {
    "name": "album-concept",
    "kind": "conceptualizer",
    "phases": [
        {"index": 1, "name": "foundation",
         "produces": ["artist", "genre", "type", "scale", "theme", "true_story"]},
        {"index": 2, "name": "concept",
         "produces": ["key_subjects", "emotional_core", "why"]},
        {"index": 3, "name": "sonic",
         "produces": ["references", "production_style", "vocal_approach",
                      "instrumentation", "mood", "target_duration"]},
        {"index": 4, "name": "structure",
         "produces": ["tracklist", "sequencing", "energy_map"]},
        {"index": 5, "name": "art",
         "produces": ["visual_concept", "palette", "symbols"]},
        {"index": 6, "name": "practical",
         "produces": ["album_title", "track_titles", "research_needs",
                      "explicit", "distributor_genres"]},
        {"index": 7, "name": "confirmation",
         "produces": ["user_confirmed"], "gate": "hard"},
    ],
}

# Two gated, walkable workflow skills (CORE.md:57-62) — computed predicates advance
# the early phases; the terminal "ship it?" is a HARD human gate.
PRE_GENERATION_SKILL = {
    "name": "pre-generation", "kind": "gate",
    "phases": [
        {"index": 1, "name": "concept-ready", "produces": ["concept_complete"]},
        {"index": 2, "name": "rights-clear", "produces": ["rights_ok"]},
        {"index": 3, "name": "approve", "produces": ["approved"], "gate": "hard"},
    ],
}
RELEASE_QA_SKILL = {
    "name": "release-qa", "kind": "gate",
    "phases": [
        {"index": 1, "name": "mastered", "produces": ["all_tracks_mastered"]},
        {"index": 2, "name": "metadata", "produces": ["metadata_complete"]},
        {"index": 3, "name": "ship", "produces": ["released"], "gate": "hard"},
    ],
}

# Spec 095 — lyric-writing workflow skill. 6 phases ending in a hard elicit.
# Computed gates at prosody / pronunciation / cross-track / explicit delegate to
# tiny *_gate verbs (the lifecycle cluster pattern from 007: pregen_check,
# release_check) — each verb composes the underlying transforms + calls
# gate.check to record PASSED/BLOCKED_ON on the lifecycle.
#
# Note on `gate_verb`: this is **advisory metadata for the dispatching agent**,
# not a walker auto-invoke directive. The agency skill walker
# (`agency/skill.py`) advances on `run.submit(fills)` only; it does NOT call
# the named gate_verb itself. The agent walking the skill is expected to
# invoke the gate verb between phase submits (CORE.md:57-62 — progressive
# disclosure means the walker emits one phase at a time; verb dispatch is
# the orchestrating agent's job). Reading `phase["gate_verb"]` tells the
# agent "this is the right gate to call before submitting this phase's
# fills". A future walker enhancement could automate this; v1 is metadata.
LYRIC_WRITING_SKILL = {
    "name": "lyric-writing", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "draft", "produces": ["lyrics_draft"]},
        {"index": 2, "name": "prosody",
         "produces": ["syllable_target_met", "rhyme_scheme_valid"],
         "gate": "computed", "gate_verb": "music.prosody_gate"},
        {"index": 3, "name": "pronunciation",
         "produces": ["pronunciation_clean"],
         "gate": "computed", "gate_verb": "music.pronunciation_gate"},
        {"index": 4, "name": "cross-track",
         "produces": ["no_album_wide_repeats"],
         "gate": "computed", "gate_verb": "music.repetition_gate"},
        {"index": 5, "name": "explicit",
         "produces": ["explicit_rating_assigned"],
         "gate": "computed", "gate_verb": "music.explicit_gate"},
        {"index": 6, "name": "finalize",
         "produces": ["lyrics_locked"], "gate": "hard"},
    ],
}


IDEA_STATUS = {"new", "promoted", "dropped"}


music_ontology = OntologyExtension(
    nodes={
        # 007 baseline (verbatim required-fields preserved)
        "Album": ["artist", "title", "type", "status", "genre", "slug", "target_lufs"],
        "Track": ["title", "status", "slug"],
        "Tweet": ["text"],
        "Idea": ["text"],                        # optional: status, captured_at
        "SheetMusic": ["title"],
        # 094 Slice 2 — reference data nodes (back the vendored genres + reference docs)
        "Genre": ["slug", "name"],               # optional: mastering_target_lufs, suno_tips
        "Reference": ["kind", "slug"],           # optional: body
    },
    enums={("Album", "type"): ALBUM_TYPES,
           ("Album", "status"): ALBUM_STATUS,
           ("Track", "status"): TRACK_STATUS,
           ("Idea", "status"): IDEA_STATUS},     # 094 Slice 2 NEW
    edges={                                       # 094 Slice 2 NEW closed-set edges
        "PROMOTED_TO",                            # Idea → Album (promote_idea)
        "RECORDED_FOR",                           # Track → Album (create_track)
    },
    skills={"album-concept": ALBUM_CONCEPT_SKILL,
            "pre-generation": PRE_GENERATION_SKILL,
            "release-qa": RELEASE_QA_SKILL,
            "lyric-writing": LYRIC_WRITING_SKILL},   # 095 NEW
    schemas={"album-concept": ["artist", "title", "type"],
             "promo-copy": ["album", "body"],
             "mastering-report": ["album", "body"],
             "lyric-report": ["album", "body"],
             "sheet-music": ["album", "body"],
             # 095 NEW — lyric cluster artefact reports
             "pronunciation-report": ["album", "track", "findings"],
             "prosody-report":       ["album", "track", "scheme"],
             "cross-track-report":   ["album", "repeated_lines"],
             "explicit-scan":        ["album", "track", "rating"],
             "voice-check":          ["album", "track", "findings"]},
)
