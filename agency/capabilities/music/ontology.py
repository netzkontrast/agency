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

# Spec 100 — gates cluster walkable skills (the lifecycle binders).
PRE_GENERATION_FULL_SKILL = {
    "name": "pre-generation-full", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "concept-ready",
         "produces": ["concept_present"],
         "gate": "computed", "gate_verb": "music.concept_gate"},
        {"index": 2, "name": "research-verified",
         "produces": ["sources_signed_off"],
         "gate": "computed", "gate_verb": "music.verify_gate"},
        {"index": 3, "name": "lyrics-clean",
         "produces": ["lyrics_ok"],
         "gate": "computed", "gate_verb": "music.lyrics_pregen_gate"},
        {"index": 4, "name": "ready-to-generate",
         "produces": ["ready"], "gate": "hard"},
    ],
}
RELEASE_QA_FULL_SKILL = {
    "name": "release-qa-full", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "audio-mastered",
         "produces": ["audio_ok"],
         "gate": "computed", "gate_verb": "music.audio_release_gate"},
        {"index": 2, "name": "catalogue-synced",
         "produces": ["catalogue_ok"],
         "gate": "computed", "gate_verb": "music.catalogue_gate"},
        {"index": 3, "name": "promo-drafted",
         "produces": ["promo_ok"],
         "gate": "computed", "gate_verb": "music.promo_gate"},
        {"index": 4, "name": "ship",
         "produces": ["shipped"], "gate": "hard"},
    ],
}
VALIDATE_STRUCTURE_SKILL = {
    "name": "validate-structure", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "album-files",
         "produces": ["album_files_present"]},
        {"index": 2, "name": "track-files",
         "produces": ["track_files_present"]},
        {"index": 3, "name": "mirror-paths",
         "produces": ["mirror_paths_consistent"]},
    ],
}

# Spec 099 — research cluster.
RESEARCH_DOMAINS = {
    "legal", "financial", "security", "government", "journalism",
    "biographical", "historical", "primary_source", "technical",
    "document_hunter",
}
RESEARCH_CLAIM_VERIFIED = {"pending", "human-confirmed", "rejected"}
VERIFICATION_VERDICT = {"confirmed", "rejected", "needs-more-evidence"}

RESEARCH_WORKFLOW_SKILL = {
    "name": "research-workflow", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "scope",
         "produces": ["research_question", "domains_selected"]},
        {"index": 2, "name": "dispatch-specialists",
         "produces": ["specialists_dispatched"]},
        {"index": 3, "name": "collect",
         "produces": ["claims_captured"]},
        {"index": 4, "name": "verify",
         "produces": ["pending_resolved"],
         "gate": "computed", "gate_verb": "music.verify_gate"},
        {"index": 5, "name": "human-sign-off",
         "produces": ["sources_signed_off"], "gate": "hard"},
    ],
}

# Spec 098 — promo cluster walkable skills.
PROMO_PASS_SKILL = {
    "name": "promo-pass", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "draft",
         "produces": ["promo_body", "promo_platform"]},
        {"index": 2, "name": "review",
         "produces": ["review_score", "review_passed"],
         "gate": "computed", "gate_verb": "music.promo_review_gate"},
        {"index": 3, "name": "asset-attach",
         "produces": ["assets_attached"]},
        {"index": 4, "name": "schedule",
         "produces": ["scheduled_at_set"]},
        {"index": 5, "name": "publish",
         "produces": ["published"], "gate": "hard"},
    ],
}
RELEASE_PUBLISH_SKILL = {
    "name": "release-publish", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "gather-assets",
         "produces": ["release_assets_collected"]},
        {"index": 2, "name": "upload",
         "produces": ["assets_uploaded"]},
        {"index": 3, "name": "catalogue-update",
         "produces": ["catalogue_synced"]},
        {"index": 4, "name": "announce",
         "produces": ["announcement_posted"], "gate": "hard"},
    ],
}

# Spec 097 — tweet status enum (open-set: bitwize uses {draft, scheduled, posted, archived}).
TWEET_STATUS = {"draft", "scheduled", "posted", "archived"}

# Spec 097 — catalogue cluster walkable skills.
TWEET_CURATION_SKILL = {
    "name": "tweet-curation", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "draft",
         "produces": ["tweet_body", "tweet_platform"]},
        {"index": 2, "name": "schedule",
         "produces": ["scheduled_at_set"],
         "gate": "computed", "gate_verb": "music.tweet_schedule_gate"},
        {"index": 3, "name": "publish",
         "produces": ["posted"]},
        {"index": 4, "name": "archive",
         "produces": ["archived"]},
    ],
}
STREAMING_VERIFY_SKILL = {
    "name": "streaming-verify", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "collect",
         "produces": ["urls_to_check"]},
        {"index": 2, "name": "head-check",
         "produces": ["live_urls", "dead_urls"]},
        {"index": 3, "name": "record",
         "produces": ["verification_recorded"]},
    ],
}

# Spec 096 — mastering + mix-polish workflow skills.
MASTERING_SKILL = {
    "name": "mastering", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "measure",
         "produces": ["loudness_measured", "signature_captured"],
         "gate": "computed", "gate_verb": "music.measure_gate"},
        {"index": 2, "name": "polish",
         "produces": ["stems_polished"]},
        {"index": 3, "name": "master",
         "produces": ["master_rendered"]},
        {"index": 4, "name": "qc",
         "produces": ["qc_passed"],
         "gate": "computed", "gate_verb": "music.qc_gate"},
        {"index": 5, "name": "coherence",
         "produces": ["album_coherent"], "gate": "hard"},
    ],
}
MIX_POLISH_SKILL = {
    "name": "mix-polish", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "transcribe-stems",
         "produces": ["stems_isolated"]},
        {"index": 2, "name": "polish-per-stem",
         "produces": ["stems_polished"]},
        {"index": 3, "name": "remix",
         "produces": ["remixed_track"]},
        {"index": 4, "name": "loudness-check",
         "produces": ["loudness_in_target"], "gate": "hard"},
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
        # 099 NEW — music-specific research nodes (the `research` capability
        # owns its own ResearchClaim/VerificationRecord with a slightly
        # different shape; ours are music-album-scoped).
        "AlbumClaim": ["text", "source_uri", "domain", "verified"],
        "AlbumVerification": ["claim", "verdict"],
    },
    enums={("Album", "type"): ALBUM_TYPES,
           ("Album", "status"): ALBUM_STATUS,
           ("Track", "status"): TRACK_STATUS,
           ("Idea", "status"): IDEA_STATUS,      # 094 Slice 2 NEW
           ("Tweet", "status"): TWEET_STATUS,    # 097 NEW
           ("AlbumClaim", "verified"): RESEARCH_CLAIM_VERIFIED,  # 099 NEW
           ("AlbumClaim", "domain"): RESEARCH_DOMAINS,           # 099 NEW
           ("AlbumVerification", "verdict"): VERIFICATION_VERDICT}, # 099 NEW
    edges={                                       # 094 Slice 2 NEW closed-set edges
        "PROMOTED_TO",                            # Idea → Album (promote_idea)
        "RECORDED_FOR",                           # Track → Album (create_track)
    },
    skills={"album-concept": ALBUM_CONCEPT_SKILL,
            "pre-generation": PRE_GENERATION_SKILL,
            "release-qa": RELEASE_QA_SKILL,
            "lyric-writing": LYRIC_WRITING_SKILL,    # 095 NEW
            "mastering": MASTERING_SKILL,            # 096 NEW
            "mix-polish": MIX_POLISH_SKILL,          # 096 NEW
            "tweet-curation": TWEET_CURATION_SKILL,  # 097 NEW
            "streaming-verify": STREAMING_VERIFY_SKILL,  # 097 NEW
            "promo-pass": PROMO_PASS_SKILL,          # 098 NEW
            "release-publish": RELEASE_PUBLISH_SKILL,  # 098 NEW
            "research-workflow": RESEARCH_WORKFLOW_SKILL,  # 099 NEW
            "pre-generation-full": PRE_GENERATION_FULL_SKILL,  # 100 NEW
            "release-qa-full": RELEASE_QA_FULL_SKILL,    # 100 NEW
            "validate-structure": VALIDATE_STRUCTURE_SKILL},  # 100 NEW
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
             "voice-check":          ["album", "track", "findings"],
             # 096 NEW — audio cluster artefact reports
             "mix-analysis":         ["album", "track", "findings"],
             "qc-report":            ["album", "track", "rows"],
             "coherence-report":     ["album", "avg_distance"],
             "promo-video":          ["album", "track", "output_path"],
             "album-sampler":        ["album", "output_path"],
             # 097 NEW — catalogue cluster artefact reports
             "tweet-record":         ["album", "body", "platform"],
             "streaming-verify":     ["album", "live", "dead"],
             "catalogue-snapshot":   ["album", "total", "by_status"],
             # 098 NEW — promo cluster artefact reports
             "published-asset":      ["album", "key", "bytes"],
             "promo-album-package":  ["album", "assets"],
             "social-post":          ["album", "platform", "body"],
             # 099 NEW — research cluster artefact reports
             "album-claim":          ["text", "domain"],
             "album-verification":   ["claim", "verdict"]},
)
