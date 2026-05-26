"""music — a domain capability: album conceptualization.

Demonstrates a DOMAIN capability that OWNS its ontology fragment — none of this
lives in the core. It contributes the `album-concept` conceptualizer (a 7-phase
gated planning skill ending in a hard confirm gate), an `Album` node type, the
closed `album type` enum, and an album-concept artefact schema. This is how a
domain (music, novels, …) becomes a capability bundle, proving the extension
contract end to end.
"""
from __future__ import annotations

from ..capability import Capability
from ..ontology import OntologyExtension

ALBUM_TYPES = {"documentary", "narrative", "thematic", "character-study",
               "collection", "ost"}

# the conceptualizer: a 7-phase gated planning skill (foundation → concept → sonic
# → structure → art → practical → confirmation), ending in a HARD confirm gate.
# The engine's skill walker walks it one phase at a time (progressive disclosure).
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


def conceptualize(artist: str, title: str, type: str,
                  theme: str = "", tracklist: str = "") -> dict:
    "Render an album-concept document (act). `type` must be a known album type."
    if type not in ALBUM_TYPES:
        raise ValueError(f"type={type!r} not in {sorted(ALBUM_TYPES)}")
    body = (f"# {title}\n\n**Artist:** {artist}  \n**Type:** {type}\n\n"
            f"## Theme\n{theme}\n\n## Tracklist\n{tracklist}\n")
    return {"result": body, "artefact": {
        "kind": "album-concept", "artist": artist, "title": title,
        "type": type, "body": body}}


music_ontology = OntologyExtension(
    nodes={"Album": ["artist", "title", "type"], "Track": ["title"]},
    enums={("Album", "type"): ALBUM_TYPES},
    skills={"album-concept": ALBUM_CONCEPT_SKILL},
    schemas={"album-concept": ["artist", "title", "type"]},
)

music_capability = Capability(
    name="music",
    home="capability",
    verbs={"conceptualize": {"role": "act", "fn": conceptualize}},
    ontology=music_ontology,
)
