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
            "release-qa": RELEASE_QA_SKILL},
    schemas={"album-concept": ["artist", "title", "type"],
             "promo-copy": ["album", "body"],
             "mastering-report": ["album", "body"],
             "lyric-report": ["album", "body"],
             "sheet-music": ["album", "body"]},
)
