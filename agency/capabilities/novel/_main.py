# agency-scaffold: v1
# agency-accept-warn: surface_size clustered domain capability (Spec 093/101): 8 sub-clusters by design, ~45 verbs across lifecycle/storyform/prose/research/catalogue/manuscript/gates/xcap. Tier discovery via Spec 068 not warranted while cluster slices are still landing.
"""novel — minimum-viable-novel Slice 1 (Spec 101 master First-Principles Minimum).

Five-verb path from premise to manuscript: conceptualize → create_novel → create_chapter → chapter_report → render_manuscript, plus the novel-concept gated planning skill.

Use when: authoring a novel — turning a premise into a structured manuscript through gated concept → chapters → report → render.
Triggers:
- A novel premise needs structured planning before drafting
- A chapter needs a per-chapter report (word count, beat progress)
- A finished draft needs rendering to manuscript format
Red flags:
- Hand-rolling chapter files outside the capability → call `novel.create_chapter`
- Skipping the conceptualizer's hard gate → walk `novel-concept`
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from agency._render import RenderRule, RenderSpec
from agency.capability import ArtefactSchemas, CapabilityBase, RenderTemplates
from agency.ontology import OntologyExtension
from ._slug import slugify


# Spec 104 — show-don't-tell filter words (canonical writing-craft list).
# A documented tunable per CLAUDE.md §8: not a snapshot of "what we
# measured once" — the set IS the writing convention.
FILTER_WORDS: frozenset[str] = frozenset({
    "really", "just", "very", "somehow", "actually", "perhaps",
    "maybe", "literally", "basically", "totally", "definitely",
    "probably", "suddenly", "instantly", "completely", "absolutely",
    "quite", "rather", "almost", "nearly", "seemingly",
})

# Spec 104 — filter-word density threshold for the show-don't-tell gate.
# Documented tunable; 5% = "polished" prose per editorial heuristics.
FILTER_WORD_DENSITY_THRESHOLD: float = 0.05

# Spec 104 Slice 2 — dialogue attribution lexicons.
# `PLAIN_ATTRIBUTIONS` are the invisible tags an editor prefers (Strunk &
# White, Stephen King "On Writing"). `FLOWERY_ATTRIBUTIONS` are the
# attention-stealing alternatives; high count = author intruding.
PLAIN_ATTRIBUTIONS: frozenset[str] = frozenset({
    "said", "asked", "replied", "answered",
})
FLOWERY_ATTRIBUTIONS: frozenset[str] = frozenset({
    "exclaimed", "muttered", "ejaculated", "expostulated",
    "interjected", "vociferated", "thundered", "whimpered",
    "growled", "hissed", "gasped", "sputtered",
})

# Spec 104 Slice 2 — common sentence-starter stopwords filtered out by
# `scan_proper_nouns`. Title-Case at sentence position 1 is ambiguous;
# this allow-list says "these never refer to people/places". Documented
# tunable per CLAUDE.md §8: editorial canon, not a snapshot. Cased
# lowercase here; the verb compares case-folded.
_SENTENCE_STARTERS: frozenset[str] = frozenset({
    "the", "a", "an",
    "he", "she", "it", "they", "we", "you", "i",
    "his", "her", "their", "its",
    "this", "that", "these", "those",
    "then", "when", "where", "why", "how", "what", "who",
    "if", "as", "and", "but", "or", "so", "yet",
    "after", "before", "during", "while", "since", "until",
    "now", "still", "even", "just", "only",
})


# Spec 104 Slice 2 — show-don't-tell telling verbs (interior monologue).
# Distinct from FILTER_WORDS (adverbs); these flag verbs that NARRATE
# emotion instead of dramatizing it.
TELLING_VERBS: frozenset[str] = frozenset({
    "felt", "feel", "feels",
    "realized", "realize", "realizes",
    "noticed", "notice", "notices",
    "wondered", "wonder", "wonders",
    "thought", "thinks",
    "knew", "knows",
})

# Spec 104 Slice 2 — canonical content-warning category lexicons.
# A documented tunable per CLAUDE.md §8 (editorial taxonomy, not a
# snapshot); each category maps to a set of keyword stems. Matched
# category names go in the returned `warnings` list.
CONTENT_WARNINGS: dict[str, frozenset[str]] = {
    "violence":  frozenset({"knife", "blood", "gun", "shot",
                             "stab", "punch", "kill", "killed",
                             "murder", "wound", "bleeding"}),
    "sex":       frozenset({"sex", "naked", "intimate", "kiss",
                             "lover", "bed", "undress"}),
    "substance": frozenset({"whiskey", "vodka", "beer", "wine",
                             "cocaine", "heroin", "cigarette",
                             "marijuana", "drunk", "overdose"}),
    "death":     frozenset({"died", "dying", "corpse", "funeral",
                             "grave", "death", "dead"}),
    "self-harm": frozenset({"suicide", "cutting", "razor", "overdose"}),
}

# Spec 122 — sensitivity-topic advisory lexicon (extends content-warnings
# with mental-health / identity / trauma-adjacent terms). Always emits as
# `warnings`, never blocks gates (the spec's "exact-severity discipline").
_SENSITIVITY_LEXICON: dict[str, frozenset[str]] = {
    "mental-health": frozenset({"depression", "anxiety", "panic", "trauma",
                                  "ptsd", "breakdown", "psychosis"}),
    "identity":      frozenset({"queer", "trans", "nonbinary", "race",
                                  "ethnicity", "religion"}),
    "trauma":        frozenset({"assault", "abuse", "violence", "rape",
                                  "harassment"}),
}


def _levenshtein(a: str, b: str) -> int:
    """Cheap Levenshtein distance for the continuity-check close-pair scan.

    O(len(a)*len(b)) in space — fine for the proper-noun registry where
    both strings are ≤ ~30 chars. Stdlib-only.
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[-1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


_WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
_VOWEL_GROUP_RE = re.compile(r"[aeiouyAEIOUY]+")


def _word_tokens(body: str) -> list[str]:
    return _WORD_RE.findall(body)


def _count_sentences(body: str) -> int:
    return max(1, len(re.findall(r"[.!?]+", body)))


def _syllables_word(w: str) -> int:
    """Deterministic syllable heuristic — delegates to `agency._prosody.syllables`.

    Post Round-1 sc-analyze F2: music + novel previously hand-rolled two
    syllable counters with the same heuristic but different impl —
    classic derivability-audit drift. Promoted to `agency._prosody` so
    both caps import the same source.
    """
    from agency._prosody import syllables
    return syllables(w)


@lru_cache(maxsize=1)
def _load_ncp_schema() -> dict:
    """Spec 103 hybrid rows 12+13 — vendored NCP v1.3.0 JSON schema loader.

    Reads `data/ncp/ncp-schema-v1.3.0.json` once (lru-cached); the
    canonical_appreciation (463 values) and canonical_narrative_function
    (144 values) sets live under `$defs.*.enum`.
    """
    p = Path(__file__).parent / "data" / "ncp" / "ncp-schema-v1.3.0.json"
    return json.loads(p.read_text())


@lru_cache(maxsize=1)
def _canonical_appreciations() -> frozenset[str]:
    """The 463 canonical NCP appreciations from the vendored schema."""
    defs = _load_ncp_schema().get("$defs", {})
    return frozenset(
        defs.get("canonical_appreciation", {}).get("enum", []))


@lru_cache(maxsize=1)
def _canonical_narrative_functions() -> frozenset[str]:
    """The 144 canonical NCP narrative_function values from the schema."""
    defs = _load_ncp_schema().get("$defs", {})
    return frozenset(
        defs.get("canonical_narrative_function", {}).get("enum", []))


def _walk_field(obj, field_name: str, path: str = ""):
    """Yield (path, value) for every `field_name` occurrence in nested dict/list."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            child_path = f"{path}.{k}" if path else k
            if k == field_name and isinstance(v, str):
                yield child_path, v
            else:
                yield from _walk_field(v, field_name, child_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from _walk_field(item, field_name, f"{path}[{i}]")


@lru_cache(maxsize=1)
def _load_dramatica_ontology() -> dict:
    """Spec 103 — module-level memoized loader for the Dramatica ontology.

    Reads the vendored `data/dramatica/ontology.json` (304 entries) once;
    LRU-cached so the 50KB JSON parse happens at most once per process.
    Storyform check verbs (Spec 103 Slice 1+) call this directly — no
    TextDriver, no lazy-import indirection (per the sc:sc-recommend Rec 1
    'graph-only-first; defer the TextDriver split').
    """
    p = Path(__file__).parent / "data" / "dramatica" / "ontology.json"
    return json.loads(p.read_text())


@lru_cache(maxsize=1)
def _ontology_by_slug() -> dict:
    """Spec 120 — slug-indexed lookup for `_resolve_term`.

    The vendored ontology mixes kinds (element, variation, type, etc.) and
    NCP fixtures sometimes use the wrong kind-prefix (`el.self-interest`
    when the entry actually lives as `var.self-interest`). The map below
    groups every entry by its kind-stripped slug so `_resolve_term` can
    find the canonical entry regardless of the caller's prefix guess.
    """
    by_slug: dict[str, list[dict]] = {}
    for entry in _load_dramatica_ontology()["entries"]:
        eid = entry.get("id", "")
        if "." in eid:
            slug = eid.split(".", 1)[1]
        else:
            slug = eid
        by_slug.setdefault(slug, []).append(entry)
    return by_slug


def _resolve_term(term_id: str) -> tuple[dict | None, bool]:
    """Spec 120 — kind-agnostic ontology lookup.

    Returns ``(entry, exact_kind_match)``:
    - ``entry`` is the matched ontology row (or None if no slug match);
    - ``exact_kind_match`` is True iff the caller's prefix (e.g. ``el.``)
      matched the entry's actual kind. NCP fixtures use ``el.self-interest``
      while the ontology stores ``var.self-interest`` — the slug matches,
      so we return the variation entry with ``exact_kind_match=False``.

    Per implementation-spec-libs.md and the Slice-2 retraction lesson: the
    fixtures themselves blur kind boundaries, so strict-kind would re-break
    the oracle suite. Verbs that NEED kind certainty consult the bool.
    """
    if not term_id or "." not in term_id:
        return None, False
    prefix, slug = term_id.split(".", 1)
    entries = _ontology_by_slug().get(slug, [])
    if not entries:
        return None, False
    kind_prefix_map = {
        "el": "element", "var": "variation", "t": "type",
        "type": "type", "dp": "dynamic-pair", "quad": "quad",
        "class": "class", "arc": "archetype", "pd": "plot-dynamic",
        "cd": "character-dynamic", "th": "throughline", "con": "concept",
    }
    expected_kind = kind_prefix_map.get(prefix)
    for entry in entries:
        if entry.get("kind") == expected_kind:
            return entry, True
    return entries[0], False


# ─────────────────────────── enums ───────────────────────────
NOVEL_STATUS = {"concept", "outlining", "drafting", "revising",
                "beta", "querying", "published"}
CHAPTER_STATUS = {"outlined", "drafted", "revised", "final"}
# Spec 102 Slice 2 — Scene POV (canonical narrative-craft set).
SCENE_POV = {"first", "second", "third-limited", "third-omniscient"}
# Spec 284 — POV projection alias map (the domain half of the projected-enum
# substrate; the primitive lives in agency/_enums.py). Keys are matched as
# lowercased substrings of the normalized input, longest first — so a specific
# signal (``omniscient``) beats a generic one (``third``). Rich descriptions
# project onto a canonical member; the original is preserved in ``pov_detail``.
# English + German signals (this engine drafts German novels — see kohaerenz).
_POV_ALIASES = {
    "first": "first", "1st": "first", "ich-": "first",
    "ich erzähler": "first", "erste person": "first", "first-person": "first",
    "second": "second", "2nd": "second", "du-": "second",
    "zweite person": "second", "second-person": "second",
    "omniscient": "third-omniscient", "auktorial": "third-omniscient",
    "allwissend": "third-omniscient", "omni": "third-omniscient",
    "third-limited": "third-limited", "limited": "third-limited",
    "personal": "third-limited", "limitiert": "third-limited",
    "vermittler": "third-limited", "third": "third-limited",
    "dritte person": "third-limited", "er-perspektive": "third-limited",
}
# Spec 102 — Idea lifecycle (mirrors music's IDEA_STATUS).
IDEA_STATUS = {"new", "promoted", "dropped"}
# Spec 105 — research-claim verification + domain enums (mirrors 099's
# AlbumClaim shape; reused as NovelClaim with the same status alphabet).
CLAIM_VERIFIED = {"pending", "confirmed", "refuted", "needs-source"}
RESEARCH_DOMAINS = {
    "historical", "scientific", "cultural", "geographical",
    "linguistic", "philosophical", "religious", "political",
    "technological", "biographical",
}
# Spec 123 — WorldAxiom severity. Hard axioms are inviolable world rules
# (gravity reverses; the dead don't come back); soft axioms are tendencies
# (most nobles distrust foreigners). Determines whether
# find_axiom_contradictions flags a pair as a structural break or a note.
WORLD_AXIOM_SEVERITY: frozenset[str] = frozenset({"hard", "soft"})
# Spec 132 — CodexEntry kinds (Novelcrafter-aligned).
CODEX_ENTRY_KIND: frozenset[str] = frozenset({
    "location", "minor-character", "artefact", "concept", "faction",
})
# Spec 123 — `link_character_to_world` edge-kind whitelist. BELONGS_TO is
# the catch-all; the others are specific relationship verbs. Passing an
# unknown kind returns INVALID_ARGUMENT.
_CHARACTER_WORLD_EDGES: frozenset[str] = frozenset({
    "BELONGS_TO", "INHABITS", "WORSHIPS", "SPEAKS", "WIELDS",
})


# Spec 283 Slice 1 (Workstream F) — the novel render ruleset (graph → markdown
# view). The REFERENCE RenderSpec: Novel → work.md, Chapter →
# chapters/NN-slug.md. Each rule's frontmatter carries the node id + parent
# edge so a re-render is byte-identical and round-trips. `render_all` walks
# these to re-materialise the tree + mint one Artefact per file.
def _novel_fm(node: dict) -> dict:
    return {"id": node.get("id", ""), "kind": "novel",
            "title": node.get("title", ""), "author": node.get("author", ""),
            "status": node.get("status", "")}


def _novel_body(node: dict) -> str:
    return f"# {node.get('title', 'Untitled')}\n\nby {node.get('author', '')}\n"


def _chapter_path(node: dict) -> str:
    return (f"chapters/{int(node.get('number', 0)):02d}-"
            f"{slugify(node.get('title', '') or 'untitled')}.md")


def _chapter_fm(node: dict) -> dict:
    return {"id": node.get("id", ""), "kind": "chapter",
            "novel": node.get("novel", ""), "number": int(node.get("number", 0)),
            "title": node.get("title", ""), "status": node.get("status", "")}


def _chapter_body(node: dict) -> str:
    return node.get("body", "") or ""


NOVEL_RENDER_SPEC = RenderSpec(rules=[
    RenderRule(label="Novel", kind="novel",
               output_path=lambda n: "work.md",
               frontmatter=_novel_fm, body=_novel_body),
    RenderRule(label="Chapter", kind="chapter",
               output_path=_chapter_path,
               frontmatter=_chapter_fm, body=_chapter_body),
])


# ─────────────────────────── walkable skill ───────────────────────────
# Spec 102 §"novel-concept walkable skill (10 phases)" — extends the
# 5-phase Slice 1 skeleton with genre/audience/setting/characters-core/
# dramatica-seed/outline-shape/series-hypothesis blocks. The dramatica-seed
# phase populates the 4 dynamics that Spec 103's storyform cluster consumes.
NOVEL_CONCEPT_SKILL = {
    "name": "novel-concept", "kind": "conceptualizer",
    "phases": [
        {"index": 1, "name": "premise",
         "produces": ["logline", "central_question"]},
        {"index": 2, "name": "genre",
         "produces": ["genre", "subgenre", "tone"]},
        {"index": 3, "name": "audience",
         "produces": ["target_reader", "comp_titles"]},
        {"index": 4, "name": "pov",
         "produces": ["pov_choice", "narrator_voice"]},
        {"index": 5, "name": "setting",
         "produces": ["world", "time_period", "geography"]},
        {"index": 6, "name": "characters-core",
         "produces": ["protagonist_seed", "antagonist_seed",
                      "supporting_seeds"]},
        {"index": 7, "name": "dramatica-seed",
         "produces": ["resolve_intent", "growth_intent",
                      "approach_intent", "mental_sex_intent"]},
        {"index": 8, "name": "outline-shape",
         "produces": ["act_structure", "midpoint_intent",
                      "ending_intent"]},
        {"index": 9, "name": "series-hypothesis",
         "produces": ["standalone_or_series", "series_arc"]},
        {"index": 10, "name": "confirmation",
         "produces": ["user_confirmed"], "gate": "hard"},
    ],
}


# Spec 102/104 — character-architect walkable skill (4 phases).
# Per kohaerenz §04-character-and-world: psychology (TSDP/IFS/Big-Five/
# Enneagram) → archetype (Jung + moral alignment) → voice → confirm.
CHARACTER_ARCHITECT_SKILL = {
    "name": "character-architect", "kind": "conceptualizer",
    "phases": [
        {"index": 1, "name": "psychology",
         "produces": ["big_five", "enneagram", "ifs_parts"]},
        {"index": 2, "name": "archetype",
         "produces": ["jung_archetype", "moral_alignment"]},
        {"index": 3, "name": "voice",
         "produces": ["voice_signature", "register"]},
        {"index": 4, "name": "confirmation",
         "produces": ["user_confirmed"], "gate": "hard"},
    ],
}


# Spec 102/104 — world-bible-architect walkable skill (5 phases).
# Per kohaerenz §04: geography → cultures → religions+languages →
# magic-systems → canon-lock (axioms become hard invariants).
WORLD_BIBLE_ARCHITECT_SKILL = {
    "name": "world-bible-architect", "kind": "conceptualizer",
    "phases": [
        {"index": 1, "name": "geography",
         "produces": ["continents", "biomes", "time_period"]},
        {"index": 2, "name": "cultures",
         "produces": ["cultures", "core_values"]},
        {"index": 3, "name": "religions-languages",
         "produces": ["religions", "languages"]},
        {"index": 4, "name": "magic-systems",
         "produces": ["magic_systems", "hard_or_soft"]},
        {"index": 5, "name": "canon-lock",
         "produces": ["user_confirmed", "axioms_canon_locked"],
         "gate": "hard"},
    ],
}


# Spec 103/108 — scene-bridge-auditor walkable skill (5 phases / Q1-Q5).
# Per kohaerenz §05-structure-scene-coherence + decidability brief
# ("tools assert structure; skills assert meaning"): scene-bridge
# Q1-Q5 ships as a walkable skill — purpose/POV/stakes/conflict/payoff.
# Spec 120 — canonical signpost order per class. Each class's 4 types
# enumerate the natural Dramatica K→T→A→D sequence for that throughline.
# Deviations are row-10 violations (chained behind row 5).
_CANONICAL_SIGNPOST_ORDER = {
    "class.universe":   ["t.past", "t.progress", "t.future", "t.present"],
    "class.physics":    ["t.learning", "t.doing", "t.obtaining", "t.understanding"],
    "class.mind":       ["t.memory", "t.preconscious", "t.subconscious", "t.conscious"],
    "class.psychology": ["t.conceptualizing", "t.being", "t.becoming", "t.conceiving"],
}


# Spec 120 — storyform-build walkable skill (6 phases). Phases bind to
# real verbs so walking the skill EXECUTES (not documents) the build.
STORYFORM_BUILD_SKILL = {
    "name": "storyform-build", "kind": "builder",
    "phases": [
        {"index": 1, "name": "throughline-partition",
         "produces": ["throughlines_assigned"],
         "verbs": ["novel.check_throughline_partition"]},
        {"index": 2, "name": "concern-and-signposts",
         "produces": ["signposts_assigned", "concerns_set"],
         "verbs": ["novel.check_signpost_permutation",
                   "novel.check_ktad_coverage"]},
        {"index": 3, "name": "elements-and-pair",
         "produces": ["problem_solution_set", "crucial_element_set"],
         "verbs": ["novel.check_quad_completeness",
                   "novel.check_crucial_element_placement",
                   "novel.check_dynamic_pair_reciprocity"]},
        {"index": 4, "name": "dynamics-and-style",
         "produces": ["resolve_outcome_judgment_set",
                      "approach_set", "mental_sex_set"],
         "verbs": ["novel.check_resolve_outcome_judgment",
                   "novel.check_approach_concern",
                   "novel.check_mental_sex_problem_solving"]},
        {"index": 5, "name": "ncp-shape",
         "produces": ["slots_filled", "moments_anchored"],
         "verbs": ["novel.check_slot_fill",
                   "novel.check_storybeat_moment_refs",
                   "novel.validate_appreciations",
                   "novel.validate_narrative_functions"]},
        {"index": 6, "name": "composite-gate",
         "produces": ["storyform_coherent"],
         "verbs": ["novel.novel_coherence_check"],
         "gate": "hard"},
    ],
}


SCENE_BRIDGE_AUDITOR_SKILL = {
    "name": "scene-bridge-auditor", "kind": "auditor",
    "phases": [
        {"index": 1, "name": "Q1-purpose",
         "produces": ["scene_purpose"]},
        {"index": 2, "name": "Q2-POV",
         "produces": ["pov_choice", "narrator_voice"]},
        {"index": 3, "name": "Q3-stakes",
         "produces": ["stakes_internal", "stakes_external"]},
        {"index": 4, "name": "Q4-conflict",
         "produces": ["conflict_axis", "tension_arc"]},
        {"index": 5, "name": "Q5-payoff-and-signoff",
         "produces": ["user_confirmed", "scene_signoff"],
         "gate": "hard"},
    ],
}


# Spec 122 — developmental-editor walkable skill. 5 phases; phase 3 binds
# to developmental_gate so the walk's pass condition IS the gate verdict.
DEVELOPMENTAL_EDITOR_SKILL = {
    "name": "developmental-editor", "kind": "editor",
    "phases": [
        {"index": 1, "name": "structure-pass",
         "produces": ["manuscript_coherent", "chapters_contiguous"],
         "verbs": ["novel.manuscript_coherence_check"]},
        {"index": 2, "name": "storyform-pass",
         "produces": ["storyform_coherent"],
         "verbs": ["novel.novel_coherence_check"]},
        {"index": 3, "name": "developmental-gate",
         "produces": ["developmental_ready"],
         "verbs": ["novel.developmental_gate"]},
        {"index": 4, "name": "voice-pass",
         "produces": ["voice_consistent"],
         "verbs": ["novel.check_voice_consistency"]},
        {"index": 5, "name": "sign-off",
         "produces": ["developmental_signoff"],
         "gate": "hard"},
    ],
}


# Spec 124 — publish-prep walkable skill. 4 phases driving the
# publication path: render → export → publication_gate → sign-off.
PUBLISH_PREP_SKILL = {
    "name": "publish-prep", "kind": "publisher",
    "phases": [
        {"index": 1, "name": "manuscript-pass",
         "produces": ["manuscript_rendered"],
         "verbs": ["novel.render_manuscript"]},
        {"index": 2, "name": "export-pass",
         "produces": ["exports_written"],
         "verbs": ["novel.export_epub", "novel.export_pdf",
                   "novel.export_docx"]},
        {"index": 3, "name": "publication-gate",
         "produces": ["publication_ready"],
         "verbs": ["novel.publication_gate"]},
        {"index": 4, "name": "sign-off",
         "produces": ["publication_signoff"],
         "gate": "hard"},
    ],
}


# Spec 122 — line-editor walkable skill. 4 phases; phase 3 binds to
# line_gate so the walk's pass condition is every chapter line-clean.
LINE_EDITOR_SKILL = {
    "name": "line-editor", "kind": "editor",
    "phases": [
        {"index": 1, "name": "prose-pass",
         "produces": ["filter_words_clean", "show_dont_tell_clean",
                       "dialogue_attribution_clean"],
         "verbs": ["novel.check_filter_words",
                   "novel.check_show_dont_tell",
                   "novel.check_dialogue_attribution"]},
        {"index": 2, "name": "pov-pass",
         "produces": ["pov_consistent"],
         "verbs": ["novel.check_pov_consistency"]},
        {"index": 3, "name": "line-gate",
         "produces": ["line_ready"],
         "verbs": ["novel.line_gate"]},
        {"index": 4, "name": "sign-off",
         "produces": ["line_signoff"],
         "gate": "hard"},
    ],
}


# Spec 220 — default system prompt for the wet scene-body driver.
# Kept SHORT so it stays on the cache prefix (Spec 146 discipline);
# scene-specific guidance lives in the brief (Spec 127 / Spec 144).
_DEFAULT_SCENE_SYSTEM = (
    "You are a novelist. Write the next scene as instructed by the brief. "
    "Show, don't tell. Avoid filter words. Attribute dialogue cleanly. "
    "Output ONLY the scene prose — no headings, no commentary."
)


# Spec 130 — scene-writer walkable skill. The integration of the
# dynamic-prompt depth wave: assemble (127) → validate-constraints →
# generate (Spec 220 Slice 1: novel.generate_scene_body via Spec 147 +
# Spec 279) → check (chains 4 prose/storyform checks) → integrate (HARD
# GATE — writes scene body back via novel.integrate_scene_body).
# Phases bind to real verbs so walking the skill EXECUTES the loop.
SCENE_WRITER_SKILL = {
    "name": "scene-writer", "kind": "writer",
    "phases": [
        {"index": 1, "name": "assemble",
         "produces": ["scene_brief"],
         "verbs": ["prompt.assemble_scene_brief"]},
        {"index": 2, "name": "validate-constraints",
         "produces": ["constraints_validated"],
         # No bound verb yet — the brief's token_count + truncated
         # flags carry the validation; phase output is the gate.
         "verbs": [],
         # Spec 285 Part B — the scene's POV must not be ASSUMED. The walker
         # elicits a choice from the canonical SCENE_POV set (sourced from the
         # in-capability `novel.pov_options` verb) when the caller hasn't
         # supplied `pov_choice`; with no elicit-capable host it pauses rather
         # than guessing. Demonstrates the enforced no-assumption gate.
         "requires_input": ["pov_choice"],
         "resolve_via": {"capability": "novel", "verb": "pov_options"}},
        {"index": 3, "name": "generate",
         # Codex review on PR #137 round 2: phase 1's output key is
         # `scene_brief`; the verb accepts it under the same name so
         # the skill walker's `args = {k: outputs[k] for k in inputs}`
         # mapping forwards the assembled brief without renaming.
         "inputs":   ["scene_id", "scene_brief", "alter_id"],
         # The verb returns the typed `WetSceneResult` envelope (dict),
         # NOT a body string — the body itself lives in the Artefact
         # behind `body_handle`. Naming the produce slot
         # `wet_scene_result` is honest about the shape so downstream
         # phases know to fetch the body via
         # `novel.fetch_scene_body(body_handle)` rather than treating
         # it as ready-to-integrate prose (Slice 2 wires the prose
         # checks against the fetched body).
         "produces": ["wet_scene_result"],
         # Spec 220 Slice 1: bound to the wet generator (Spec 147
         # AnthropicDriver + Spec 279 host-LLM delegation). The
         # `invoke` block EXECUTES the verb (Codex review on PR #137
         # round 1: `verbs` alone is advisory metadata).
         "invoke":   {"capability": "novel",
                       "verb":       "generate_scene_body"},
         "verbs":    ["novel.generate_scene_body"]},
        {"index": 4, "name": "check",
         "produces": ["check_verdict"],
         "verbs": ["novel.check_filter_words",
                   "novel.check_dialogue_attribution",
                   "novel.check_show_dont_tell",
                   "novel.novel_coherence_check"]},
        {"index": 5, "name": "integrate",
         "produces": ["scene_integrated"],
         "verbs": ["novel.integrate_scene_body"],
         "gate": "hard"},
    ],
}


# ─────────────────────────── ontology ───────────────────────────
novel_ontology = OntologyExtension(
    nodes={
        # Lifecycle (Slice 1 minimum — extended in 102/103/...)
        "Novel":   ["title", "author", "status"],
        "Chapter": ["novel", "number", "title", "status"],
        # Spec 102 — pre-novel idea capture (mirrors music's Idea node:
        # schema is text-only, `status` carried as an optional field
        # constrained by the IDEA_STATUS enum below — same shape music uses).
        "Idea":    ["text"],
        # Spec 103 — Dramatica storyform payload (NCP v1.3.0 shape).
        # Schema is `["novel"]` — the NCP body lives as an optional `body`
        # field (open dict). Check verbs read the body directly.
        "Storyform": ["novel"],
        # Spec 105 — research-claim layer (mirrors music's AlbumClaim).
        # Domain + verification status are optional fields constrained by
        # the enums below; same shape as the music cap's NovelClaim sibling.
        "NovelClaim": ["text", "source_uri", "domain"],
        # Spec 102 Slice 2 — Scene under Chapter (drafting-grain).
        "Scene": ["chapter", "slug", "pov"],
        # Spec 123 — World sub-graph (Slice 1). Worlds span multiple
        # novels (recommend novel-scoped Conflict/Theme per Open Q1 —
        # those land in Slice 2). World shapes the bible the author
        # references; Culture / Religion / Language / MagicSystem
        # populate it; WorldAxiom carries the load-bearing rules.
        "World":        ["slug", "name"],
        "Culture":      ["slug", "name"],
        "Religion":     ["slug", "name"],
        "Language":     ["slug", "name"],
        "MagicSystem":  ["slug", "name"],
        "WorldAxiom":   ["text", "severity"],
        # Spec 128 — story-time / narrative-time graph.
        "StoryTimeEvent": ["novel", "label", "when_story"],
        "NarrativeBeat":  ["novel", "label", "scene"],
        # Spec 132 — codex entries (Novelcrafter-parity).
        "CodexEntry":   ["novel", "slug", "name", "kind"],
        # Spec 131 — character-knowledge ledger.
        "KnownFact":    ["character", "fact"],
    },
    enums={
        ("Novel",   "status"): NOVEL_STATUS,
        ("Chapter", "status"): CHAPTER_STATUS,
        ("Idea",    "status"): IDEA_STATUS,
        ("NovelClaim", "verified"): CLAIM_VERIFIED,
        ("NovelClaim", "domain"):   RESEARCH_DOMAINS,
        ("Scene",   "pov"): SCENE_POV,
        # Spec 123 — WorldAxiom severity: hard rules block the world
        # (gravity reverses; magic costs blood); soft rules describe
        # tendencies (most nobles distrust foreigners).
        ("WorldAxiom", "severity"): WORLD_AXIOM_SEVERITY,
        # Spec 132 — CodexEntry kind (5 Novelcrafter categories).
        ("CodexEntry", "kind"): CODEX_ENTRY_KIND,
    },
    edges={
        "CHAPTER_OF",       # Chapter → Novel (mirror of music's RECORDED_FOR)
        "PROMOTED_TO",      # Idea → Novel (mirror of music's PROMOTED_TO)
        "SCENE_OF",         # Spec 102 Slice 2 — Scene → Chapter
        "STORYFORM_OF",     # Spec 103 Slice 2 (Workstream D) — Storyform → Novel
        # Spec 123 — World sub-graph edges.
        "PART_OF_WORLD",    # Culture/Religion/Language/MagicSystem/Axiom → World
        "CONTRADICTS",      # WorldAxiom → WorldAxiom (find_axiom_contradictions)
        # Spec 123 — character ↔ world relationships. Edge kind is the
        # narrative relationship (catch-all is BELONGS_TO).
        "BELONGS_TO", "INHABITS", "WORSHIPS", "SPEAKS", "WIELDS",
        # Spec 128 — story-time / narrative-time edges.
        "HAPPENS_AT",   # Scene → StoryTimeEvent (this scene depicts the event)
        "REVEALED_IN",  # StoryTimeEvent → Scene (the disclosure point)
        "PRECEDES",     # NarrativeBeat → NarrativeBeat (narrative-order DAG)
        # Spec 132 — CodexEntry → Novel.
        "CODEX_OF",
        # Spec 131 — character-knowledge ledger edges.
        "KNOWS",        # Character → KnownFact
        "LEARNED_IN",   # KnownFact → Scene
    },
    skills={"novel-concept": NOVEL_CONCEPT_SKILL,
            "character-architect": CHARACTER_ARCHITECT_SKILL,
            "world-bible-architect": WORLD_BIBLE_ARCHITECT_SKILL,
            "scene-bridge-auditor": SCENE_BRIDGE_AUDITOR_SKILL,
            "storyform-build": STORYFORM_BUILD_SKILL,
            "publish-prep": PUBLISH_PREP_SKILL,
            "developmental-editor": DEVELOPMENTAL_EDITOR_SKILL,
            "line-editor": LINE_EDITOR_SKILL,
            "scene-writer": SCENE_WRITER_SKILL},
    schemas={
        # Spec 102: logline replaces `premise` in the canonical phase name;
        # both verb args + skill produce the same field set.
        "novel-concept": ["title", "logline", "central_question"],
        "chapter-report": ["novel_id", "chapter_count", "word_count_total"],
        "manuscript":     ["novel", "body", "chapter_count"],
    },
)



# ─────────────────────────── capability ───────────────────────────
# Spec 286 P3 — the verb surface is split across cluster mixins (one file
# per cluster under ``clusters/``); NovelCapability composes them into ONE
# registered ``novel`` capability. Mixins FIRST, CapabilityBase LAST so the
# base resolvers (ctx, _require_drv) sit at the end of the MRO and NovelBase's
# override wins. ``CapabilityBase.as_capability`` walks the full MRO, so every
# mixin's @verb methods are discovered — same verb-name set + count as before.
from .clusters import (  # noqa: E402  (after module-level names the mixins import)
    NovelBase,
    LifecycleMixin,
    StoryformMixin,
    ProseMixin,
    ResearchMixin,
    ManuscriptMixin,
    WorldMixin,
    StoryTimeMixin,
    CodexMixin,
    CharacterKnowledgeMixin,
)


class NovelCapability(
    LifecycleMixin,
    StoryformMixin,
    ProseMixin,
    ResearchMixin,
    ManuscriptMixin,
    WorldMixin,
    StoryTimeMixin,
    CodexMixin,
    CharacterKnowledgeMixin,
    NovelBase,
    CapabilityBase,
):
    name = "novel"
    home = "capability"
    ontology = novel_ontology
    artefact_schemas = ArtefactSchemas.from_module(__file__)
    render_templates = RenderTemplates.from_module(__file__)
