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

from agency._enums import project_enum
from agency._frontmatter import frontmatter_hash
from agency._render import RenderRule, RenderSpec
from agency.capability import CapabilityBase, RenderTemplates, verb
from agency.ontology import OntologyExtension
from ._slug import slugify
from agency.toolresult import ToolResult


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
         "verbs": []},
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


class NovelCapability(CapabilityBase):
    name = "novel"
    home = "capability"
    ontology = novel_ontology
    render_templates = RenderTemplates.from_module(__file__)

    # ───────── Spec 121: lazy production-driver auto-wiring ─────────
    # AGENCY-DRIFT: novel driver set — mirror production_drivers() keys
    # and the diagnose-wanted list when adding novel drivers (text/format/etc).
    _NOVEL_DRIVER_NAMES = ("novel_state", "novel_format")

    def _production_enabled(self) -> bool:
        """Auto-wiring only fires under the production MCP runtime
        (`agency/__main__.py` flips ``engine._novel_production = True``).
        Unit tests build a bare Engine without the flag and keep the typed
        ``DEPENDENCY_MISSING`` contract — bounded blast radius."""
        return getattr(self.ctx.engine, "_novel_production", False) is True

    def _autowire_novel_drivers(self) -> None:
        """Build ``production_drivers(NovelConfig.bootstrap())`` ONCE and
        register the bundle on first miss. ``NovelConfig.bootstrap()``
        writes the default `.agency/novel-config.yaml` + creates the
        content root when a fresh repo has none.
        """
        reg = self.ctx.drivers
        if reg is None or not self._production_enabled():
            return
        if all(reg.has(n) for n in self._NOVEL_DRIVER_NAMES):
            return
        from .config import NovelConfig
        from .drivers_production import production_drivers
        bundle = production_drivers(NovelConfig.bootstrap())
        for n, drv in bundle.items():
            if not reg.has(n):
                reg.register(n, drv)

    def _require_drv(self, name: str):  # type: ignore[override]
        """Auto-wire production drivers on first miss before falling
        back to the base typed-failure resolver (Spec 121 mirrors Spec 117)."""
        if name in self._NOVEL_DRIVER_NAMES:
            reg = self.ctx.drivers
            if reg is not None and not reg.has(name):
                self._autowire_novel_drivers()
        return super()._require_drv(name)

    def _maybe_state_driver(self):
        """Return the wired novel_state driver or None when production
        isn't on. Used by verbs that have a graph-only default with an
        opportunistic disk side-effect (CLAUDE.md rule 2)."""
        return self._maybe_driver("novel_state")

    def _maybe_format_driver(self):
        """Spec 124 — opportunistic FormatDriver. When production is on
        (FakeFormatDriver lands by default; PandocFormatDriver in Slice 2),
        export verbs hand the manuscript markdown to the driver. Otherwise
        export verbs return DEPENDENCY_MISSING typed failure."""
        return self._maybe_driver("novel_format")

    def _maybe_driver(self, name: str):
        reg = self.ctx.drivers
        if reg is None or not self._production_enabled():
            return None
        if not reg.has(name):
            self._autowire_novel_drivers()
        if reg.has(name):
            return reg.get(name)
        return None

    def _require_novel(self, novel_id: str) -> tuple[dict | None, ToolResult | None]:
        """NOT_FOUND guard shared by every verb taking a novel_id.

        Returns ``(node, fail)``: when the novel exists, ``node`` is the
        graph payload and ``fail`` is ``None``; when missing, ``node`` is
        ``None`` and ``fail`` is a typed ToolResult.failure the caller
        forwards.

        One source of truth for the NOT_FOUND message — keeps the error
        string drift-free across create_chapter, chapter_report, and
        render_manuscript (which previously held a hand-rolled copy).
        """
        node = self.ctx.recall(novel_id)
        if node is None:
            return None, ToolResult.failure(
                "NOT_FOUND", f"novel_id={novel_id!r} not found")
        return node, None

    @verb(role="act")
    def conceptualize(self, title: str, author: str,
                       premise: str = "",
                       central_question: str = "") -> ToolResult:
        """Render a novel-concept document (act); the first verb of the MVN flow.

        Inputs: title, author, premise, central_question.
        Returns: ``{result, artefact}`` novel-concept artefact.
        chain_next: ``novel.create_novel`` to mint the Novel node.
        """
        body = (f"# {title}\n\n**Author:** {author}\n\n"
                f"## Premise\n{premise}\n\n"
                f"## Central question\n{central_question}\n")
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "novel-concept",
                         "title": title, "premise": premise,
                         "central_question": central_question,
                         "body": body},
        })

    @verb(role="effect")
    def create_novel(self, title: str, author: str,
                      genre: str = "novel") -> ToolResult:
        """Record a Novel node SERVING the intent; materialise disk on production.

        Inputs: title, author, genre (default "novel"; routes the disk
                layout `works/{author}/works/{genre}/{slug}/`).
        Returns: ``{novel_id, title, status, work_path?}`` — ``work_path``
                appears when the production driver is wired (Spec 121).
        chain_next: ``novel.create_chapter`` once outline is ready.
        """
        nid = self.ctx.record("Novel", {
            "title": title, "author": author,
            "genre": genre, "status": "concept",
        })
        self.ctx.link(nid, self.ctx.intent_id, "SERVES")
        out: dict = {"novel_id": nid, "title": title, "status": "concept"}
        drv = self._maybe_state_driver()
        if drv is not None:
            disk = drv.create_work(author, genre, title)
            out["work_path"] = disk["path"]
            out["work_slug"] = disk["slug"]
        return ToolResult.success(data=out)

    @verb(role="effect")
    def create_chapter(self, novel_id: str, number: int,
                        title: str, body: str = "") -> ToolResult:
        """Record a Chapter graph node + CHAPTER_OF the parent Novel (effect).

        Inputs: novel_id, number (1-indexed), title, body (optional draft body).
        Returns: ``{chapter_id, novel_id, number, title, status}``.
        chain_next: ``novel.chapter_report`` to aggregate state.
        """
        novel_node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        cid = self.ctx.record("Chapter", {
            "novel": novel_id, "number": number, "title": title,
            "status": "outlined", "body": body,
        })
        self.ctx.link(cid, novel_id, "CHAPTER_OF")
        self.ctx.link(cid, self.ctx.intent_id, "SERVES")
        drv = self._maybe_state_driver()
        if drv is not None:
            drv.create_chapter(
                novel_node.get("author", ""),
                novel_node.get("genre", "novel"),
                novel_node.get("title", ""),
                number, title, body=body)
        return ToolResult.success(data={
            "chapter_id": cid, "novel_id": novel_id,
            "number": number, "title": title, "status": "outlined",
        })

    @verb(role="transform")
    def chapter_report(self, novel_id: str) -> ToolResult:
        """Read-only aggregate over the novel's chapters (transform).

        Inputs: novel_id.
        Returns: ``{novel_id, chapter_count, word_count_total, by_status}``.
        chain_next: revise chapters then ``novel.render_manuscript``.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        # Find chapters of this novel
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        word_count = sum(len((c.get("body") or "").split())
                         for c in chapters)
        by_status: dict[str, int] = {}
        for c in chapters:
            s = c.get("status", "outlined")
            by_status[s] = by_status.get(s, 0) + 1
        return ToolResult.success(data={
            "novel_id": novel_id,
            "chapter_count": len(chapters),
            "word_count_total": word_count,
            "by_status": by_status,
        })

    @verb(role="act")
    def render_manuscript(self, novel_id: str) -> ToolResult:
        """Concatenate chapters into a manuscript artefact (act).

        Inputs: novel_id.
        Returns: ``{result, artefact}`` manuscript artefact with the assembled body.
        chain_next: terminal — deliver to the publishing path.
        """
        novel_node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = sorted(
            self.ctx.neighbors(novel_id, "CHAPTER_OF"),
            key=lambda c: c.get("number", 0))
        title = novel_node.get("title", "Untitled")
        author = novel_node.get("author", "")
        parts = [f"# {title}\n", f"by {author}\n\n"]
        for c in chapters:
            parts.append(
                f"\n## Chapter {c.get('number', 0)}: {c.get('title', '')}\n\n"
                f"{c.get('body', '')}\n")
        body = "".join(parts)
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "manuscript",
                         "novel": novel_id,
                         "chapter_count": len(chapters),
                         "body": body},
        })

    @verb(role="effect")
    def render_all(self, novel_id: str) -> ToolResult:
        """Re-materialise a novel's full markdown tree from graph ground truth (effect).

        Spec 283 Slice 1 (Workstream F) — the on-demand full-rebuild path. Walks
        the novel `RenderSpec` (Novel → work.md, each Chapter →
        chapters/NN-slug.md), writes each file via the wired `render` driver
        (graph-only when none is wired — bare engines are unaffected), and mints
        ONE `Artefact{kind, path, entity_id, frontmatter_hash}` + `PRODUCES`
        edge per rendered entity. Closes the graph/disk provenance split (the
        evidence's 2-Artefacts-for-41-files drift): now #Artefacts == #files.
        Idempotent. Replaces the out-of-band `scripts/materialize_manuscript.py`.

        Inputs: novel_id.
        Returns: ``{novel_id, count, rendered: [{path, entity_id, artefact_id}],
                   wrote_disk}``.
        chain_next: ``novel.audit_novel_provenance`` to see the new Artefacts;
                    or any editorial gate.
        """
        novel_node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        reg = self.ctx.drivers
        driver = reg.get("render") if (reg is not None and reg.has("render")) else None
        rendered: list[dict] = []
        # Novel (work.md), then each chapter in number order.
        self._render_entity(NOVEL_RENDER_SPEC.rule_for("Novel"), novel_node, driver, rendered)
        chapters = sorted(self.ctx.neighbors(novel_id, "CHAPTER_OF"),
                          key=lambda c: c.get("number", 0))
        crule = NOVEL_RENDER_SPEC.rule_for("Chapter")
        for c in chapters:
            self._render_entity(crule, c, driver, rendered)
        return ToolResult.success(data={
            "novel_id": novel_id, "count": len(rendered),
            "rendered": rendered, "wrote_disk": driver is not None,
        })

    def _render_entity(self, rule, node: dict, driver, rendered: list) -> None:
        """Render one node via its RenderRule: write (if a driver is wired) +
        mint the Artefact + PRODUCES edge. Shared by render_all (and, Slice 2,
        the auto-render hook)."""
        if rule is None or not node:
            return
        path = rule.output_path(node)
        fm = rule.frontmatter(node)
        body = rule.body(node)
        if driver is not None:
            driver.write(path, fm, body)
        aid = self.ctx.record("Artefact", {
            "kind": rule.kind, "path": path,
            "entity_id": node.get("id", ""),
            "frontmatter_hash": frontmatter_hash(fm),
        })
        self.ctx.link(self.ctx.intent_id, aid, "PRODUCES")
        rendered.append({"path": path, "entity_id": node.get("id", ""),
                         "artefact_id": aid})

    # ───────────────── Spec 102 — lifecycle delta ─────────────────
    # Idea capture/promotion + novel discovery/status flip. Graph-only
    # for Slice 1; StateDriver (disk-layer) lands in a Spec-115-equivalent
    # follow-up matching music's production-binding split.

    @verb(role="effect")
    def capture_idea(self, text: str) -> ToolResult:
        """Record an Idea node SERVING the intent (effect).

        Pre-novel capture surface: free-text premise jotted before the
        gated conceptualizer runs. Default status ``new``.

        Inputs: text.
        Returns: ``{idea_id, text, status}``.
        chain_next: ``novel.promote_idea`` once the premise hardens.
        """
        iid = self.ctx.record("Idea", {"text": text, "status": "new"})
        self.ctx.link(iid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "idea_id": iid, "text": text, "status": "new",
        })

    @verb(role="transform")
    def list_ideas(self, status: str = "") -> ToolResult:
        """List captured ideas; optional status filter (transform).

        Inputs: status (one of ``IDEA_STATUS`` or ``""`` for all).
        Returns: ``{ideas: [...], count}``.
        chain_next: ``novel.promote_idea`` for any "new" idea ready to ship.
        """
        if status and status not in IDEA_STATUS:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"status={status!r} not in {sorted(IDEA_STATUS)}")
        ideas = [i for i in self.ctx.find("Idea")
                 if not status or i.get("status") == status]
        return ToolResult.success(data={"ideas": ideas, "count": len(ideas)})

    @verb(role="effect")
    def promote_idea(self, idea_id: str, title: str,
                      author: str) -> ToolResult:
        """Idea → Novel transition; records PROMOTED_TO edge (effect).

        Flips the Idea's status to ``promoted``, mints a Novel node, and
        wires a PROMOTED_TO edge. Mirrors music's promote_idea / Idea-to-
        Album lineage.

        Inputs: idea_id, title, author.
        Returns: ``{idea_id, novel_id, title, status}``.
        chain_next: ``novel.create_chapter`` to start outlining.
        """
        node = self.ctx.recall(idea_id)
        if node is None:
            return ToolResult.failure(
                "NOT_FOUND", f"idea_id={idea_id!r} not found")
        nid = self.ctx.record("Novel", {
            "title": title, "author": author, "status": "concept",
        })
        self.ctx.link(nid, self.ctx.intent_id, "SERVES")
        self.ctx.link(idea_id, nid, "PROMOTED_TO")
        self.ctx.update(idea_id, {"status": "promoted"})
        return ToolResult.success(data={
            "idea_id": idea_id, "novel_id": nid,
            "title": title, "status": "concept",
        })

    @verb(role="transform")
    def find_novel(self, query: str = "") -> ToolResult:
        """Substring-match novel titles (transform, driver-free).

        Inputs: query (case-insensitive substring; ``""`` returns all).
        Returns: ``{novels: [{novel_id, title, author, status}], count}``.
        chain_next: ``novel.set_novel_status`` or ``novel.render_manuscript``.
        """
        q = query.lower()
        hits = []
        for n in self.ctx.find("Novel"):
            title = (n.get("title") or "").lower()
            if not q or q in title:
                hits.append({
                    "novel_id": n.get("id"),
                    "title": n.get("title"),
                    "author": n.get("author"),
                    "status": n.get("status"),
                })
        return ToolResult.success(data={"novels": hits, "count": len(hits)})

    @verb(role="effect")
    def set_novel_status(self, novel_id: str, status: str) -> ToolResult:
        """Flip a Novel's lifecycle status; enum-checked (effect).

        Inputs: novel_id, status (one of ``NOVEL_STATUS``).
        Returns: ``{novel_id, status}``.
        chain_next: continue per the new lifecycle phase.
        """
        if status not in NOVEL_STATUS:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"status={status!r} not in {sorted(NOVEL_STATUS)}")
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        self.ctx.update(novel_id, {"status": status})
        return ToolResult.success(data={
            "novel_id": novel_id, "status": status,
        })

    # ───────────────── Spec 102 Slice 2 — chapter + scene + session ─────────────────
    # Graph-only; StateDriver disk-layer still deferred per Slice 1 carve-out.

    def _require_chapter(self, chapter_id: str) -> tuple[dict | None, ToolResult | None]:
        """NOT_FOUND guard for verbs taking a chapter_id — mirrors `_require_novel`."""
        node = self.ctx.recall(chapter_id)
        if node is None:
            return None, ToolResult.failure(
                "NOT_FOUND", f"chapter_id={chapter_id!r} not found")
        return node, None

    @verb(role="transform")
    def list_chapters(self, novel_id: str) -> ToolResult:
        """List a novel's chapters ordered by number (transform).

        Inputs: novel_id.
        Returns: ``{chapters: [{chapter_id, number, title, status}], count}``.
        chain_next: ``novel.set_chapter_status`` or ``novel.create_scene``.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = sorted(
            self.ctx.neighbors(novel_id, "CHAPTER_OF"),
            key=lambda c: c.get("number", 0))
        items = [{
            "chapter_id": c.get("id"),
            "number": c.get("number"),
            "title": c.get("title"),
            "status": c.get("status"),
        } for c in chapters]
        return ToolResult.success(data={"chapters": items, "count": len(items)})

    @verb(role="effect", param_enums={"pov": SCENE_POV})
    def create_scene(self, chapter_id: str, slug: str,
                      pov: str) -> ToolResult:
        """Record a Scene node + SCENE_OF the parent Chapter (effect).

        Spec 284 — ``pov`` is a *projected enum*: it accepts rich free text
        (e.g. ``"auktorialer Erzähler"``) and projects it onto a canonical
        ``SCENE_POV`` member, preserving the original in ``pov_detail`` (the
        non-lossy contract). Input carrying no POV signal still fails
        PERMANENT, listing the members.

        Inputs: chapter_id, slug (scene-local short name), pov (a ``SCENE_POV``
                member or rich text projected onto one).
        Returns: ``{scene_id, chapter_id, slug, pov, pov_detail?}``.
        chain_next: ``novel.create_scene`` for next beat or back to
                    ``novel.set_chapter_status`` once the chapter's
                    scene set is complete.
        """
        canonical, detail = project_enum(pov, SCENE_POV, aliases=_POV_ALIASES)
        if canonical is None:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"pov={pov!r} carries no POV signal — not projectable onto "
                f"{sorted(SCENE_POV)}")
        _, fail = self._require_chapter(chapter_id)
        if fail is not None:
            return fail
        props = {"chapter": chapter_id, "slug": slug, "pov": canonical}
        if detail:
            props["pov_detail"] = detail
        sid = self.ctx.record("Scene", props)
        self.ctx.link(sid, chapter_id, "SCENE_OF")
        self.ctx.link(sid, self.ctx.intent_id, "SERVES")
        out = {"scene_id": sid, "chapter_id": chapter_id,
               "slug": slug, "pov": canonical}
        if detail:
            out["pov_detail"] = detail
        return ToolResult.success(data=out)

    @verb(role="act")
    def generate_scene_body(self, scene_id: str = "", scene_brief: str = "",
                              alter_id: str = "", system: str = "",
                              host_completion: dict | None = None,
                              prefer_delegate: bool = False,
                              max_tokens: int = 8000) -> ToolResult:
        """Spec 220 Slice 1 — wet scene-body generation via Spec 147 + Spec 279.

        Drives the Spec 130 scene-writer phase 3 (generate) with a real
        TextDriver backed by the AnthropicDriver. Three paths
        (resume wins):

        1. ``host_completion`` supplied — Claude Code already ran the
           inference after a prior delegation; parse the result.
        2. AnthropicDriver capable → ``driver.complete(messages,
           system)`` direct (Spec 147 Slice 1).
        3. Driver backend ``"none"`` AND ``prefer_delegate=True`` →
           return a ``kind="llm_delegate"`` envelope so the host runs
           inference and re-calls (Spec 279).

        The generated body is ALWAYS captured via Spec 154
        ``capture_overflow`` and returned through ``body_handle``
        (Artefact id) — never inline. A wrapping LLM driver fetches
        only the slice it needs (Spec 146 prefix discipline).

        Slice 1 ships the driver-bound generate path + the typed
        ``WetSceneResult`` shape. Slice 2+ adds the gate-driven
        regenerate loop (the shipped prose checks gate the output).

        Inputs:
          - scene_id (str — Scene node id; the body is recorded as
            an Artefact PRODUCES_FROM this Scene)
          - scene_brief (str — assembled scene brief from Spec 127;
            the scene-writer phase 1 output. Named to match the
            phase's produces key so the skill walker's input mapping
            forwards it verbatim.)
          - alter_id (str — when set, the scene is voice-locked via
            Spec 144; ``voice_locked=True`` in the result)
          - system (str — system prompt override)
          - host_completion (dict | None — Spec 279 resume envelope)
          - prefer_delegate (bool — when True + backend "none",
            emit the llm_delegate envelope instead of failing)
          - max_tokens (int — request budget for the LLM call)
        Returns: ``WetSceneResult`` dict with ``{intent_id, scene_id,
                 body_handle, wc, driver, voice_locked, refusal?,
                 kind?, request?, regen_count, passes_all, checks}``.
        chain_next: ``novel.integrate_scene_body(scene_id, body)``
                    after fetching via ``memory.recall_overflow_slice``.
        Failure modes: ``Codes.VOICE_BRIEF_MISSING`` (alter_id set but
                       brief empty); ``Codes.SCENE_OVERFLOW_LOST``
                       (capture failed); ``Codes.DRIVER_REFUSAL``
                       (Spec 147 propagates).
        """
        from agency._host_llm import (
            complete_or_delegate, HostLLMRequest, HostDelegateError,
            make_continuation_token,
        )
        from agency._overflow import capture_overflow
        from agency._tokens import count_tokens

        voice_locked = bool(alter_id)
        # Voice-lock fidelity invariant: when alter_id set, the brief
        # must come from Spec 144 (signaled by non-empty `brief`).
        if voice_locked and not scene_brief.strip():
            return ToolResult.failure(
                "VOICE_BRIEF_MISSING",
                f"alter_id={alter_id!r} requires a Spec 144 voice-locked "
                f"scene_brief; got empty scene_brief")

        # Codex review (P2): validate scene_id BEFORE spending LLM work.
        # A mistyped scene_id would otherwise burn a real Anthropic /
        # host generation and produce prose whose `body_handle` can't
        # be integrated downstream because the Scene doesn't exist.
        # Empty scene_id is allowed for stateless probe calls (tests).
        # Codex review on PR #137 round 2: use `recall_typed("Scene", …)`
        # (Spec 056 — <label>_id params must be label-checked). Passing
        # a Chapter or Intent id previously slipped past the bare
        # `recall` guard and would mis-attribute the body.
        if scene_id:
            scene_node = self.ctx.memory.recall_typed(scene_id, "Scene")
            if scene_node is None:
                return ToolResult.failure(
                    "NOT_FOUND",
                    f"scene_id={scene_id!r} not found as a Scene node — "
                    f"cannot route the generated body to a non-existent "
                    f"or wrong-label node; create the Scene with "
                    f"novel.create_scene first")

        # Resolve the anthropic driver (None when not wired).
        driver = None
        try:
            reg = getattr(self.ctx, "drivers", None)
            if reg is not None and reg.has("anthropic"):
                driver = reg.get("anthropic")
        except Exception:
            driver = None

        # No driver AND no resume → degrade to graceful failure so
        # tests/CI without a key path don't crash. The caller can
        # retry with prefer_delegate=True to opt into the envelope.
        if driver is None and host_completion is None:
            return ToolResult.failure(
                "DEPENDENCY_MISSING",
                "no anthropic driver wired and no host_completion "
                "supplied; pass prefer_delegate=True for host-LLM "
                "delegation (Spec 279) or wire an AnthropicDriver "
                "(Spec 147)")

        # When the driver isn't capable AND we're not opting into
        # delegation AND there's no resume, refuse cleanly.
        if (driver is not None and host_completion is None
                and not prefer_delegate
                and driver.backend() == "none"):
            return ToolResult.failure(
                "DEPENDENCY_MISSING",
                "anthropic driver backend is 'none' (no key, no client) "
                "and prefer_delegate=False; set ANTHROPIC_API_KEY or "
                "pass prefer_delegate=True for host-LLM delegation")

        # Build the LLM request. The brief carries the per-scene
        # instructions; system carries the role/voice directive.
        messages = [{"role": "user", "content": scene_brief or ""}]
        system_prompt = system or _DEFAULT_SCENE_SYSTEM
        if voice_locked:
            system_prompt = (
                f"{system_prompt}\n\nVoice-lock active for alter "
                f"`{alter_id}`; honour the §TABOO + §EXAMPLES "
                f"sections of the brief verbatim.")

        # Stable continuation token for the resume invariant
        # (Spec 279 single-Invocation moat).
        token = make_continuation_token(
            self.ctx.intent_id or "",
            "novel.generate_scene_body",
            {"scene_id": scene_id, "alter_id": alter_id})

        # Driver may be None when we have a host_completion to resume.
        if driver is None:
            class _NoDriver:
                def backend(self) -> str:
                    return "none"
            driver = _NoDriver()

        try:
            result = complete_or_delegate(
                driver,
                messages=messages,
                system=system_prompt,
                host_completion=host_completion,
                continuation_token=token,
                max_tokens=max_tokens,
                host=self.ctx.host,        # Spec 285 — real MCP sampling when available
            )
        except HostDelegateError as exc:
            return ToolResult.failure(
                "HOST_DELEGATE_MALFORMED" if exc.code ==
                HostDelegateError.MALFORMED else "HOST_DELEGATE_FAIL",
                str(exc))
        except Exception as exc:                                      # noqa: BLE001
            return ToolResult.failure(
                "DRIVER_REFUSAL",
                f"AnthropicDriver raised on scene-body generation: {exc}")

        # Branch 3: delegate envelope — return it so the wrapping host
        # (Claude Code) recognises the kind="llm_delegate" signal.
        if isinstance(result, HostLLMRequest):
            return ToolResult.success(data={
                "intent_id":      self.ctx.intent_id,
                "scene_id":       scene_id,
                "body_handle":    "",
                "wc":             0,
                "checks":         [],
                "passes_all":     False,
                "regen_count":    0,
                "driver":         "delegate",
                "voice_locked":   voice_locked,
                "refusal":        None,
                "kind":           result.kind,
                "request":        result.to_dict(),
            })

        # Branches 1+2: a Completion. Capture the body via Spec 154 so
        # it returns via handle, never inline (Spec 146 + Spec 154).
        body_text = result.text or ""
        try:
            ovf = capture_overflow(
                body_text, max_tokens=512, counter=count_tokens)
        except Exception as exc:                                      # noqa: BLE001
            return ToolResult.failure(
                "SCENE_OVERFLOW_LOST",
                f"capture_overflow failed: {exc}")

        # Record the body as an Artefact so a follow-up
        # `memory.recall_overflow_slice(handle)` serves the full body.
        artefact_id = self.ctx.record("Artefact", {
            "kind":             "scene-body",
            "scene_id":         scene_id,
            "voice_locked":     voice_locked,
            "alter_id":         alter_id,
            "total_tokens":     ovf.total_tokens,
            "full_body":        ovf.full_body,
            "stop_reason":      result.stop_reason,
            "driver":           ("host" if result.stop_reason ==
                                  "host_provided" else "spec147"),
        })
        if scene_id:
            self.ctx.link(artefact_id, scene_id, "PRODUCES_FROM")
        self.ctx.link(artefact_id, self.ctx.intent_id, "SERVES")

        # Word count (cheap, kept on the prefix per Spec 146).
        wc = len(body_text.split()) if body_text else 0

        return ToolResult.success(data={
            "intent_id":      self.ctx.intent_id,
            "scene_id":       scene_id,
            "body_handle":    artefact_id,
            "wc":             wc,
            "checks":         [],
            # Codex review (P2): empty `checks` means no gate was applied
            # — `passes_all=True` would be misleading. Slice 1 hasn't
            # wired the regenerate loop; report `unchecked` so callers
            # don't integrate the body assuming the gate ran.
            "passes_all":     False,
            "unchecked":      True,
            "regen_count":    0,
            "driver":         ("host" if result.stop_reason ==
                                "host_provided" else "spec147"),
            "voice_locked":   voice_locked,
            "refusal":        None,
        })

    @verb(role="transform")
    def fetch_scene_body(self, body_handle: str = "",
                          max_chars: int = 0) -> ToolResult:
        """Spec 220 Slice 1.5 — public retrieval for a scene-body Artefact.

        ``novel.generate_scene_body`` returns the body via ``body_handle``
        (an Artefact id) instead of inlining the prose (Spec 146 prefix
        discipline + Spec 154 budget). This verb resolves the handle back
        to the body so the MCP/CLI surface has a documented fetch path —
        Codex review on PR #137 surfaced that ``memory.recall_overflow_slice``
        isn't registered as a verb, leaving the body stranded behind a
        graph-internal field.

        Inputs: body_handle (Artefact id), max_chars (0 = full body;
                positive = head-slice cap).
        Returns: ``{body, total_chars, total_tokens, voice_locked,
                 alter_id, scene_id, driver, stop_reason, truncated}``.
        chain_next: ``novel.integrate_scene_body(scene_id, body)``.
        Failure modes: ``NOT_FOUND`` (body_handle missing),
                       ``BAD_REQUEST`` (handle resolves to a non-scene-
                       body Artefact).
        """
        if not body_handle:
            return ToolResult.failure(
                "INVALID_ARGUMENT", "body_handle is required")
        art = self.ctx.recall(body_handle)
        if art is None:
            return ToolResult.failure(
                "NOT_FOUND", f"body_handle={body_handle!r} not found")
        if art.get("kind") != "scene-body":
            return ToolResult.failure(
                "BAD_REQUEST",
                f"body_handle={body_handle!r} is "
                f"kind={art.get('kind')!r}, not 'scene-body'")
        full = str(art.get("full_body") or "")
        truncated = False
        if max_chars and max_chars > 0 and len(full) > max_chars:
            body = full[:max_chars]
            truncated = True
        else:
            body = full
        return ToolResult.success(data={
            "body":          body,
            "total_chars":   len(full),
            "total_tokens":  int(art.get("total_tokens") or 0),
            "voice_locked":  bool(art.get("voice_locked")),
            "alter_id":      str(art.get("alter_id") or ""),
            "scene_id":      str(art.get("scene_id") or ""),
            "driver":        str(art.get("driver") or ""),
            "stop_reason":   str(art.get("stop_reason") or ""),
            "truncated":     truncated,
        })

    @verb(role="effect")
    def integrate_scene_body(self, scene_id: str, body: str) -> ToolResult:
        """Spec 130 phase 5 — write the generated body back to the Scene (effect).

        The scene-writer skill's hard-gate integrate phase: promotes a
        draft body (from skill phase 3's generate output) onto the Scene
        node and records a ``scene-integration`` Artefact for provenance.

        Inputs: scene_id, body (the prose body to commit).
        Returns: ``{scene_id, artefact_id, bytes}``.
        chain_next: terminal — the manuscript advances to the next scene.
        """
        if self.ctx.recall(scene_id) is None:
            return ToolResult.failure(
                "NOT_FOUND", f"scene_id={scene_id!r} not found")
        self.ctx.memory.update(scene_id, {"body": body})
        aid = self.ctx.record("Artefact", {
            "kind": "scene-integration",
            "scene_id": scene_id,
            "bytes": len(body),
        })
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        self.ctx.link(self.ctx.intent_id, aid, "PRODUCES")
        return ToolResult.success(data={
            "scene_id": scene_id,
            "artefact_id": aid,
            "bytes": len(body),
        })

    @verb(role="effect")
    def set_chapter_status(self, chapter_id: str,
                            status: str) -> ToolResult:
        """Flip a Chapter's lifecycle status; enum-checked (effect).

        Inputs: chapter_id, status (one of ``CHAPTER_STATUS``).
        Returns: ``{chapter_id, status}``.
        chain_next: ``novel.novel_progress`` to see the aggregate shift.
        """
        if status not in CHAPTER_STATUS:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"status={status!r} not in {sorted(CHAPTER_STATUS)}")
        _, fail = self._require_chapter(chapter_id)
        if fail is not None:
            return fail
        self.ctx.update(chapter_id, {"status": status})
        return ToolResult.success(data={
            "chapter_id": chapter_id, "status": status,
        })

    @verb(role="effect")
    def rename_novel(self, novel_id: str, new_title: str) -> ToolResult:
        """Update a Novel's title (effect, graph-only).

        Inputs: novel_id, new_title.
        Returns: ``{novel_id, title}``.
        chain_next: continue authoring; the rename is auditable via the
                    graph's bi-temporal stamp.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        self.ctx.update(novel_id, {"title": new_title})
        return ToolResult.success(data={
            "novel_id": novel_id, "title": new_title,
        })

    @verb(role="transform")
    def novel_progress(self, novel_id: str) -> ToolResult:
        """Aggregate progress (word-count + per-status counts) for a novel (transform).

        Inputs: novel_id.
        Returns: ``{novel_id, chapter_count, word_count_total, by_status}``.
        chain_next: ``novel.render_manuscript`` once status counts say ready.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        word_count = sum(len((c.get("body") or "").split())
                         for c in chapters)
        by_status: dict[str, int] = {}
        for c in chapters:
            s = c.get("status", "outlined")
            by_status[s] = by_status.get(s, 0) + 1
        return ToolResult.success(data={
            "novel_id": novel_id,
            "chapter_count": len(chapters),
            "word_count_total": word_count,
            "by_status": by_status,
        })

    @verb(role="transform")
    def resume_session(self) -> ToolResult:
        """Return the most-recently-created Novel's id + title (transform).

        Inputs: none.
        Returns: ``{novel_id, title}`` — empty strings when no Novel exists.
        chain_next: typically ``novel.novel_progress(novel_id)`` to land in
                    the right state on session resume.
        """
        novels = list(self.ctx.find("Novel"))
        if not novels:
            return ToolResult.success(data={"novel_id": "", "title": ""})
        # Newest first by valid-from (graphqlite's bi-temporal stamp).
        last = max(novels, key=lambda r: r.get("vfrom", 0))
        return ToolResult.success(data={
            "novel_id": last.get("id", ""),
            "title": last.get("title", ""),
        })

    # ───────────────── Spec 103 — Dramatica storyform checks ─────────────────
    # Per the sc:sc-recommend top-3 inputs to Spec 103 brainstorming:
    # (1) graph-only first — no drivers.py / clusters/ split (verbs live in
    #     _main.py reading the already-landed data/dramatica/ontology.json
    #     directly via a module-level memoized loader);
    # (2) NCP body passed as a dict arg — the storyform-build skill (Slice 2)
    #     will mint Storyform nodes whose body field carries the NCP;
    # (3) schema-skill alignment — phase 1 (premise) produces `logline` +
    #     `central_question`, which Spec 102's `novel-concept` already does.
    #
    # Slice 1 ships 2 representative checks (row 5 throughline-partition
    # covering H1+H2+H8, row 3 quad-completeness covering H3-style invariants).
    # Slice 2 ships the remaining 9 decidable + 2 hybrid verbs + the
    # `novel_coherence_check` composite gate verb + the storyform-build
    # walkable skill (6 phases per Spec 103 design).

    @verb(role="effect")
    def create_storyform(self, novel_id: str, body: dict | None = None) -> ToolResult:
        """Mint the Storyform node for a novel + STORYFORM_OF edge (effect).

        Spec 103 Slice 2 (Workstream D) — closes the documented ENGINE GAP:
        the storyform gates + checks read a ``Storyform`` node, but no verb
        minted one (it had to be inserted surgically). This verb records it
        properly, carrying the NCP payload as a JSON ``body`` and wiring the
        STORYFORM_OF edge to the parent Novel. Idempotent per novel: a second
        call updates the existing Storyform's body rather than minting a
        duplicate.

        Inputs: novel_id (parent Novel), body (the NCP v1.3.0 storyform dict —
                stored JSON-serialised; optional, defaults to empty).
        Returns: ``{storyform_id, novel_id, has_body}``.
        chain_next: ``novel.pre_draft_gate`` (now satisfiable) or the
                    ``storyform-build`` skill which fills the body.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        body_json = json.dumps(body, sort_keys=True) if body else ""
        # Idempotent: one Storyform per novel — update the existing body.
        existing = next((s for s in self.ctx.find("Storyform")
                         if s.get("novel") == novel_id), None)
        if existing is not None:
            sid = existing["id"]
            if body_json:
                self.ctx.memory.update(sid, {"body": body_json})
            return ToolResult.success(data={
                "storyform_id": sid, "novel_id": novel_id,
                "has_body": bool(body_json or existing.get("body")),
            })
        sid = self.ctx.record("Storyform", {"novel": novel_id, "body": body_json})
        self.ctx.link(sid, novel_id, "STORYFORM_OF")
        self.ctx.link(sid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "storyform_id": sid, "novel_id": novel_id, "has_body": bool(body_json),
        })

    @verb(role="transform")
    def get_storyform(self, novel_id: str) -> ToolResult:
        """Return a novel's Storyform node + parsed NCP body (transform).

        Inputs: novel_id (parent Novel).
        Returns: ``{storyform_id, novel_id, body}`` (``body`` is the parsed
                 NCP dict, or ``{}`` when unset); ``found=False`` when the
                 novel has no Storyform yet.
        chain_next: feed ``body`` into ``novel.novel_coherence_check`` or any
                    decidable ``check_*`` verb.
        """
        sf = next((s for s in self.ctx.find("Storyform")
                   if s.get("novel") == novel_id), None)
        if sf is None:
            return ToolResult.success(data={"found": False, "novel_id": novel_id})
        raw = sf.get("body") or ""
        try:
            body = json.loads(raw) if raw else {}
        except (ValueError, TypeError):
            body = {}
        return ToolResult.success(data={
            "found": True, "storyform_id": sf["id"],
            "novel_id": novel_id, "body": body,
        })

    @verb(role="transform")
    def check_throughline_partition(self, ncp: dict) -> ToolResult:
        """Decidable check (row 5): 4 throughlines / 4 distinct Classes (transform).

        Inputs: ncp (the NCP v1.3.0 storyform payload — top-level dict
                with ``storyform.throughlines.{mc,os,ic,rs}.class_id``).
        Returns: ``{passed, violations}`` — violations is a list of
                 short codes (≤120 chars each per the report-shape
                 budget in Spec 103 §"Done When").
        chain_next: ``novel.check_quad_completeness`` then the composite
                    ``novel_coherence_check`` (Slice 2).
        """
        violations: list[str] = []
        story = ncp.get("storyform") or {}
        throughlines = story.get("throughlines") or {}
        # H1: exactly the four named throughlines (mc, os, ic, rs)
        expected = {"mc", "os", "ic", "rs"}
        actual = set(throughlines)
        if actual != expected:
            missing = expected - actual
            extra = actual - expected
            if missing:
                violations.append(f"H1: missing throughlines {sorted(missing)}")
            if extra:
                violations.append(f"H1: unexpected throughlines {sorted(extra)}")
        # H2: each Class used exactly once across the 4 throughlines.
        # Post Round-1 sc-analyze F3: the missing-class_id branch must
        # not be suppressed when other H2 violations fire. Report
        # missing-class_id IFF the throughline count is correct (H1 passed)
        # but some throughline omits `class_id` — that's a separate H2
        # facet from class-reuse.
        classes = [t.get("class_id") for t in throughlines.values()
                   if t.get("class_id")]
        from collections import Counter
        counts = Counter(classes)
        dupes = [c for c, n in counts.items() if n > 1]
        if dupes:
            violations.append(f"H2: class reuse {sorted(dupes)}")
        if len(throughlines) == 4 and len(classes) < 4:
            violations.append("H2: missing class_id on some throughlines")
        return ToolResult.success(data={
            "passed": not violations,
            "violations": violations,
        })

    # NOTE: `check_quad_completeness` (row 3) DEFERRED to Slice 3.
    # The decidable distinction between row 3 (quad completeness) and
    # row 6 (crucial-element placement) requires ontology lookup to know
    # which Elements sit on the same Dramatica quad. Both fixtures trip
    # the same `ce_id != mc.problem_id` shape signal — Slice 1 retraction
    # log carries the detail. Slice 3 reconciles fixture-ids ↔ vendored
    # ontology then implements all 13 checks with full element traversal.

    # ───────────── Spec 103 Slice 2 — 3 more decidable checks ─────────────
    # All 3 ship the EXACT-FAIL contract per Rec 2: each fires on its
    # named broken fixture and PASSES on the other 10. No ontology lookup
    # needed; shape-decidable from the NCP body alone.

    @verb(role="transform")
    def check_slot_fill(self, ncp: dict) -> ToolResult:
        """Decidable check (row 4): no null required slots (transform).

        Each throughline must carry non-null `class_id`, `concern_id`,
        `approach`, `mental_sex`, `resolve` slots (or omit the slot
        entirely — explicit null is a fill error, not absence).

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: ``novel.check_throughline_partition`` for H1+H2.
        """
        violations: list[str] = []
        story = ncp.get("storyform") or {}
        throughlines = story.get("throughlines") or {}
        for tname, tbody in throughlines.items():
            for slot in ("class_id", "concern_id", "approach",
                         "mental_sex", "resolve"):
                if slot in tbody and tbody.get(slot) is None:
                    violations.append(
                        f"row4: {tname}.{slot} is null (use omission, not null)")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    @verb(role="transform")
    def check_storybeat_moment_refs(self, ncp: dict) -> ToolResult:
        """Decidable check (row 11): every moment.storybeat_ref resolves (transform).

        Each `moments[*].storybeat_ref` must point to an existing
        `storybeats[*].id`. A dangling ref is a NCP-referential break.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: ``novel.check_slot_fill`` for row 4 audit.
        """
        violations: list[str] = []
        storybeats = ncp.get("storybeats") or []
        moments = ncp.get("moments") or []
        beat_ids = {sb.get("id") for sb in storybeats if sb.get("id")}
        for i, m in enumerate(moments):
            ref = m.get("storybeat_ref")
            if ref and ref not in beat_ids:
                violations.append(
                    f"row11: moments[{i}].storybeat_ref={ref!r} dangling")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    # ─────────────────── Spec 120 — 8 remaining decidable checks ───────────────────
    # All take `ncp: dict` (consistent with Slice 1+2 surface). The exact-fail
    # contract (Rec 2) is enforced via check-chaining: row 5 gates rows 3 and
    # 10; row 10 gates row 2. This makes the "false positive" overlap from
    # Slice 2 (ktad_coverage vs signpost_permutation) tractable structurally.

    @verb(role="transform")
    def check_dynamic_pair_reciprocity(self, ncp: dict) -> ToolResult:
        """Decidable check (row 1): mc.dynamic and os.dynamic must differ.

        In Dramatica, the mc/os throughline pair shares a binary dynamic axis
        (`thought` ↔ `knowledge`) — the same value on both sides collapses
        the pair. Same for ic/rs.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: ``novel.check_throughline_partition`` (row 5).
        """
        violations: list[str] = []
        tls = (ncp.get("storyform") or {}).get("throughlines") or {}
        for a, b in (("mc", "os"), ("ic", "rs")):
            da = (tls.get(a) or {}).get("dynamic")
            db = (tls.get(b) or {}).get("dynamic")
            if da and db and da == db:
                violations.append(
                    f"row1: {a}.dynamic == {b}.dynamic ({da!r}); "
                    f"pair must be antipodes")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    @verb(role="transform")
    def check_ktad_coverage(self, ncp: dict) -> ToolResult:
        """Decidable check (row 2): concern_id == signposts[0] (K-position).

        The first signpost is the concern's KTAD-K anchor for that
        throughline. A mismatch means the concern wandered from its K slot.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: gated behind row 10 in the composite — only runs when
                    signposts are in a canonical permutation.
        """
        violations: list[str] = []
        tls = (ncp.get("storyform") or {}).get("throughlines") or {}
        for tname, tbody in tls.items():
            concern = tbody.get("concern_id")
            signposts = tbody.get("signposts") or []
            if concern and signposts and signposts[0] != concern:
                violations.append(
                    f"row2: {tname}.concern_id={concern!r} != "
                    f"signposts[0]={signposts[0]!r}")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    @verb(role="transform")
    def check_quad_completeness(self, ncp: dict) -> ToolResult:
        """Decidable check (row 3): mc problem and solution are paired.

        Resolves each via ``_resolve_term`` (kind-agnostic; tolerates
        ``el.*`` vs ``var.*``), then asserts the resolved problem's
        ``dynamic_pair_id`` slug matches the resolved solution's slug.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: gated behind row 5 in the composite (per Slice-2 lesson).
        """
        violations: list[str] = []
        mc = ((ncp.get("storyform") or {}).get("throughlines") or {}
              ).get("mc") or {}
        problem = mc.get("problem_id")
        solution = mc.get("solution_id")
        if problem and solution:
            p_entry, _ = _resolve_term(problem)
            s_entry, _ = _resolve_term(solution)
            if p_entry and s_entry:
                p_pair = (p_entry.get("dynamic_pair_id") or "").split(".", 1)
                s_slug = (s_entry.get("id") or "").split(".", 1)
                p_pair_slug = p_pair[1] if len(p_pair) == 2 else ""
                s_slug_only = s_slug[1] if len(s_slug) == 2 else ""
                if p_pair_slug and s_slug_only and p_pair_slug != s_slug_only:
                    violations.append(
                        f"row3: mc.problem={problem!r}'s dynamic_pair_id is "
                        f"{p_entry.get('dynamic_pair_id')!r}, not solution={solution!r}")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    @verb(role="transform")
    def check_crucial_element_placement(self, ncp: dict) -> ToolResult:
        """Decidable check (row 6): storyform.crucial_element_id == mc.problem_id.

        The crucial element is the storyform-level pivot point — by
        Dramatica convention it sits on mc.problem. Mismatch means the
        storyform's center of gravity moved without the throughline
        following it.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: ``novel.check_resolve_outcome_judgment`` (row 7).
        """
        violations: list[str] = []
        story = ncp.get("storyform") or {}
        crucial = story.get("crucial_element_id")
        mc_problem = ((story.get("throughlines") or {}).get("mc") or {}
                      ).get("problem_id")
        if crucial and mc_problem:
            c_slug = crucial.split(".", 1)[-1]
            p_slug = mc_problem.split(".", 1)[-1]
            if c_slug != p_slug:
                violations.append(
                    f"row6: crucial_element_id={crucial!r} != "
                    f"mc.problem_id={mc_problem!r}")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    @verb(role="transform")
    def check_resolve_outcome_judgment(self, ncp: dict) -> ToolResult:
        """Decidable check (row 7): resolve/outcome/judgment triple is legal.

        4 canonical Dramatica endings encode the legal triples:
            Triumph         = (change,    success, good)
            Tragedy         = (steadfast, failure, bad)
            Personal Triumph= (steadfast, failure, good)
            Personal Tragedy= (change,    success, bad)
        Other 4 combos are inconsistent (e.g. change+failure+good has the
        protagonist abandon their drive for a happy result — not a
        canonical Dramatica ending). Cap at the documented table.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: ``novel.check_approach_concern`` (row 8).
        """
        violations: list[str] = []
        story = ncp.get("storyform") or {}
        mc = (story.get("throughlines") or {}).get("mc") or {}
        os_tl = (story.get("throughlines") or {}).get("os") or {}
        resolve = mc.get("resolve")
        outcome = os_tl.get("outcome")
        judgment = os_tl.get("judgment")
        if resolve and outcome and judgment:
            valid = {
                ("change", "success", "good"),
                ("steadfast", "failure", "bad"),
                ("steadfast", "failure", "good"),
                ("change", "success", "bad"),
            }
            if (resolve, outcome, judgment) not in valid:
                violations.append(
                    f"row7: triple (resolve={resolve!r}, outcome={outcome!r}, "
                    f"judgment={judgment!r}) is not a canonical Dramatica ending")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    @verb(role="transform")
    def check_approach_concern(self, ncp: dict) -> ToolResult:
        """Mostly-decidable check (row 8): approach ↔ class compatibility (WARN-severity).

        Per Dramatica theory: Do-er approach pairs with Universe/Physics
        classes; Be-er pairs with Mind/Psychology. Mismatch is a soft
        signal — emits ``warnings``, not ``violations``, so the composite
        passes-with-note instead of blocking.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed: True, violations: [], warnings: [str]}``.
        chain_next: ``novel.check_mental_sex_problem_solving`` (row 9).
        """
        warnings: list[str] = []
        mc = ((ncp.get("storyform") or {}).get("throughlines") or {}
              ).get("mc") or {}
        approach = mc.get("approach")
        klass = mc.get("class_id")
        if approach and klass:
            doer_classes = {"class.universe", "class.physics"}
            beer_classes = {"class.mind", "class.psychology"}
            if approach == "do-er" and klass not in doer_classes:
                warnings.append(
                    f"row8: approach=do-er but class={klass!r} "
                    f"(expected universe/physics)")
            elif approach == "be-er" and klass not in beer_classes:
                warnings.append(
                    f"row8: approach=be-er but class={klass!r} "
                    f"(expected mind/psychology)")
        return ToolResult.success(data={
            "passed": True,           # WARN-severity: never blocks
            "violations": [],
            "warnings": warnings,
        })

    @verb(role="transform")
    def check_mental_sex_problem_solving(self, ncp: dict) -> ToolResult:
        """Decidable check (row 9): mental_sex ↔ class compatibility.

        Parallel rule to row 8 but on the mental_sex axis. Universe /
        Physics classes pair with ``linear`` problem-solving (sequential,
        cause→effect); Mind / Psychology pair with ``holistic`` (gestalt,
        whole-system). Mismatch is a structural violation.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: ``novel.check_signpost_permutation`` (row 10).
        """
        violations: list[str] = []
        mc = ((ncp.get("storyform") or {}).get("throughlines") or {}
              ).get("mc") or {}
        ms = mc.get("mental_sex")
        klass = mc.get("class_id")
        if ms and klass:
            linear_classes = {"class.universe", "class.physics"}
            holistic_classes = {"class.mind", "class.psychology"}
            if ms == "linear" and klass not in linear_classes:
                violations.append(
                    f"row9: mental_sex=linear but class={klass!r}")
            elif ms == "holistic" and klass not in holistic_classes:
                violations.append(
                    f"row9: mental_sex=holistic but class={klass!r}")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    @verb(role="transform")
    def check_signpost_permutation(self, ncp: dict) -> ToolResult:
        """Decidable check (row 10): signposts in canonical order per class.

        Each class has a canonical ordering of its 4 types (the Dramatica
        signpost sequence). A reordering signals an authoring drift.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: gated behind row 5 in the composite.
        """
        violations: list[str] = []
        canonical = _CANONICAL_SIGNPOST_ORDER
        tls = (ncp.get("storyform") or {}).get("throughlines") or {}
        for tname, tbody in tls.items():
            klass = tbody.get("class_id")
            signposts = tbody.get("signposts") or []
            expected = canonical.get(klass)
            if expected and signposts and list(signposts) != list(expected):
                violations.append(
                    f"row10: {tname}.signposts={signposts!r} not canonical "
                    f"order for {klass!r}")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    @verb(role="effect")
    def novel_coherence_check(self, ncp: dict) -> ToolResult:
        """Composite gate (Spec 120): runs all 11 storyform checks with chaining.

        Chain order (Rec 2 exact-fail contract):
            row 5 (throughline_partition) →
              if pass → rows 3 (quad_completeness) + 10 (signpost_permutation)
              if row 10 pass → row 2 (ktad_coverage)
            rows 1, 4, 6, 7, 8 (WARN), 9, 11 always run.

        Records a ``gate.check(name="storyform-coherent")`` Gate node and
        a ``dogfood.record_decision`` for traceability.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations: [{check, message}], warnings: [{check, message}]}``.
        chain_next: terminal — orchestrator gates on ``passed``.
        """
        violations: list[dict] = []
        warnings: list[dict] = []

        def _record(check_name: str, result: dict) -> bool:
            for msg in result.get("violations", []):
                violations.append({"check": check_name, "message": msg})
            for msg in result.get("warnings", []):
                warnings.append({"check": check_name, "message": msg})
            return result.get("passed", True)

        # Always-run checks.
        for verb_name, check_name in (
            ("check_dynamic_pair_reciprocity", "dynamic_pair_reciprocity"),
            ("check_slot_fill", "slot_fill"),
            ("check_crucial_element_placement", "crucial_element_placement"),
            ("check_resolve_outcome_judgment", "resolve_outcome_judgment"),
            ("check_approach_concern", "approach_concern"),
            ("check_mental_sex_problem_solving", "mental_sex_problem_solving"),
            ("check_storybeat_moment_refs", "storybeat_moment_refs"),
        ):
            r = self.ctx.call("novel", verb_name, ncp=ncp)
            _record(check_name, r)

        # Chain: row 5 gates 3 and 10; 10 gates 2.
        r5 = self.ctx.call("novel", "check_throughline_partition", ncp=ncp)
        if _record("throughline_partition", r5):
            r3 = self.ctx.call("novel", "check_quad_completeness", ncp=ncp)
            _record("quad_completeness", r3)
            r10 = self.ctx.call(
                "novel", "check_signpost_permutation", ncp=ncp)
            if _record("signpost_permutation", r10):
                r2 = self.ctx.call("novel", "check_ktad_coverage", ncp=ncp)
                _record("ktad_coverage", r2)

        passed = not violations
        # Record the verdict as an Artefact (provenance moat) — composite
        # doesn't bind to a Lifecycle (caller may not have one yet); the
        # walkable storyform-build skill's final phase carries the gate.
        aid = self.ctx.record("Artefact", {
            "kind": "storyform-coherence-report",
            "passed": passed,
            "violations_count": len(violations),
            "warnings_count": len(warnings),
        })
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "passed": passed,
            "violations": violations,
            "warnings": warnings,
            "report_id": aid,
        })

    @verb(role="transform")
    def validate_appreciations(self, ncp: dict) -> ToolResult:
        """Row 12 hybrid: NCP appreciations ∈ canonical 463 (transform).

        Walks every ``appreciation`` field across the NCP body
        recursively; each string must belong to the
        ``canonical_appreciation`` enum from the vendored NCP v1.3.0
        schema (463 values).

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations: [{path, value}], canonical_size}``.
        chain_next: ``novel.validate_narrative_functions`` for row 13.
        """
        canonical = _canonical_appreciations()
        violations: list[dict] = []
        for path, value in _walk_field(ncp, "appreciation"):
            if value not in canonical:
                violations.append({"path": path, "value": value})
        return ToolResult.success(data={
            "passed": not violations,
            "violations": violations,
            "canonical_size": len(canonical),
        })

    @verb(role="transform")
    def validate_narrative_functions(self, ncp: dict) -> ToolResult:
        """Row 13 hybrid: NCP narrative_functions ∈ canonical 144 (transform).

        Walks every ``narrative_function`` field; each string must
        belong to the ``canonical_narrative_function`` enum (144 values).

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations: [{path, value}], canonical_size}``.
        chain_next: ``novel.check_throughline_partition`` for structural row 5.
        """
        canonical = _canonical_narrative_functions()
        violations: list[dict] = []
        for path, value in _walk_field(ncp, "narrative_function"):
            if value not in canonical:
                violations.append({"path": path, "value": value})
        return ToolResult.success(data={
            "passed": not violations,
            "violations": violations,
            "canonical_size": len(canonical),
        })

    # NOTE: `check_signpost_permutation` (row 10) DEFERRED to Slice 3.
    # The canonical signpost orderings ARE encodable in-code, but the
    # check over-fires on `broken_work_throughline_partition` (which
    # mutates mc.class_id universe→physics, leaving the original
    # universe signposts intact — now mismatched under physics).
    # Per Rec 2's exact-fail contract: ship only verbs that hold the
    # contract. Slice 3 chains the two checks (gate on partition-clean,
    # only then audit signpost-canonical) so the over-fire is structural.

    # ───────────────── Spec 104 — prose-analysis (driver-free) ─────────────────
    # Slice 1 ships 3 deterministic, driver-free prose-analysis verbs.

    @verb(role="transform")
    def count_words(self, body: str) -> ToolResult:
        """Word + char counter (transform, driver-free).

        Inputs: body. Returns: ``{word_count, char_count}``.
        chain_next: ``novel.analyze_readability`` for prosody metrics.
        """
        return ToolResult.success(data={
            "word_count": len(_word_tokens(body)),
            "char_count": len(body.strip()),
        })

    @verb(role="transform")
    def analyze_readability(self, body: str) -> ToolResult:
        """Flesch Reading Ease for prose (transform, driver-free).

        Score 0-100; conversational lands ~60-70. Formula:
        206.835 − 1.015 × (words/sentences) − 84.6 × (syllables/words).
        Inputs: body (non-empty). Returns: ``{flesch, words, sentences,
        syllables}``.
        chain_next: ``novel.check_filter_words`` for show-don't-tell pass.
        """
        if not body.strip():
            return ToolResult.failure(
                "INVALID_ARGUMENT", "body is empty")
        words = _word_tokens(body)
        word_n = len(words)
        sent_n = _count_sentences(body)
        syll_n = sum(_syllables_word(w) for w in words)
        flesch = (206.835
                  - 1.015 * (word_n / max(sent_n, 1))
                  - 84.6 * (syll_n / max(word_n, 1)))
        return ToolResult.success(data={
            "flesch": round(flesch, 2),
            "words": word_n,
            "sentences": sent_n,
            "syllables": syll_n,
        })

    @verb(role="transform")
    def check_filter_words(self, body: str,
                            threshold: float = FILTER_WORD_DENSITY_THRESHOLD
                            ) -> ToolResult:
        """Filter-word density check (transform, show-don't-tell).

        Scans for canonical filter words (really / just / very / etc.).
        Density = filter-count / total-words; passes when ≤ threshold.

        Inputs: body, threshold (default 0.05).
        Returns: ``{passed, filter_count, total_words, density, offenders}``.
        chain_next: ``novel.set_chapter_status`` once density is in range.
        """
        words_lower = [w.lower() for w in _word_tokens(body)]
        total = len(words_lower)
        offenders = [w for w in words_lower if w in FILTER_WORDS]
        density = (len(offenders) / total) if total else 0.0
        return ToolResult.success(data={
            "passed": density <= threshold,
            "filter_count": len(offenders),
            "total_words": total,
            "density": round(density, 4),
            "offenders": sorted(set(offenders)),
        })

    # ─────────────── Spec 104 Slice 2 — 4 more prose checks ───────────────

    @verb(role="transform")
    def scan_proper_nouns(self, body: str) -> ToolResult:
        """Extract proper nouns (Title-Case words, sentence-starter words filtered) (transform).

        Catches character + place names for continuity / world-bible
        cross-reference. Filters out common sentence-starter words
        ("The", "She", "Then", etc.) which would be Title-Case at
        position 1 of every sentence — a false-positive source.

        Inputs: body.
        Returns: ``{proper_nouns: [sorted unique], count}``.
        chain_next: ``novel.check_continuity`` (Slice 3+) for the cross-check.
        """
        nouns: set[str] = set()
        for w in body.split():
            w_clean = w.strip(".,;:!?\"'()")
            if (w_clean and w_clean[0].isupper()
                    and w_clean[1:].islower()
                    and w_clean.lower() not in _SENTENCE_STARTERS):
                nouns.add(w_clean)
        return ToolResult.success(data={
            "proper_nouns": sorted(nouns),
            "count": len(nouns),
        })

    @verb(role="transform")
    def check_dialogue_attribution(self, body: str) -> ToolResult:
        """Dialogue-tag check — plain ('said') vs flowery (transform).

        Counts plain attributions (`said`/`asked`/etc.) vs flowery ones
        (`exclaimed`/`muttered`/etc.). Strunk & White: invisible is
        better. Passes when `flowery_count == 0`.

        Inputs: body.
        Returns: ``{passed, plain_count, flowery_count, flowery_hits}``.
        chain_next: revise flowery hits then re-check.
        """
        words = [w.lower() for w in _word_tokens(body)]
        plain = [w for w in words if w in PLAIN_ATTRIBUTIONS]
        flowery = [w for w in words if w in FLOWERY_ATTRIBUTIONS]
        return ToolResult.success(data={
            "passed": len(flowery) == 0,
            "plain_count": len(plain),
            "flowery_count": len(flowery),
            "flowery_hits": sorted(set(flowery)),
        })

    @verb(role="transform")
    def check_show_dont_tell(self, body: str) -> ToolResult:
        """Telling-verb scan — interior-monologue tells (transform).

        Distinct from ``check_filter_words`` (which scans adverbs).
        Flags ``felt``/``realized``/``noticed``/etc. — verbs that
        NARRATE emotion instead of dramatizing it.

        Inputs: body.
        Returns: ``{passed, tell_count, tells}``.
        chain_next: rewrite tells into action / sensory detail.
        """
        words = [w.lower() for w in _word_tokens(body)]
        hits = [w for w in words if w in TELLING_VERBS]
        return ToolResult.success(data={
            "passed": len(hits) == 0,
            "tell_count": len(hits),
            "tells": sorted(set(hits)),
        })

    @verb(role="transform")
    def check_content_warnings(self, body: str) -> ToolResult:
        """Content-warning category scanner (transform, driver-free).

        Scans body for canonical content-warning keyword stems
        (violence / sex / substance / death / self-harm). Returns
        matched categories so publishers + reviewers can flag in
        front-matter.

        Inputs: body.
        Returns: ``{warnings: [categories], hits: {category: [keywords]}}``.
        chain_next: add to manuscript front-matter or trigger
                    sensitivity-reader workflow (Slice 3).
        """
        words_lower = {w.lower() for w in _word_tokens(body)}
        warnings: list[str] = []
        hits: dict[str, list[str]] = {}
        for category, lexicon in CONTENT_WARNINGS.items():
            matched = sorted(words_lower & lexicon)
            if matched:
                warnings.append(category)
                hits[category] = matched
        return ToolResult.success(data={
            "warnings": sorted(warnings),
            "hits": hits,
        })

    # ──────────────────── Spec 122 — editorial pipeline ────────────────────
    # 5 chapter-spanning prose checks + 3 composite editorial-stage gates.
    # The checks (voice/POV/continuity/sensitivity/chapter_report_full)
    # run ACROSS chapter bodies; the gates compose them into
    # developmental → line → copy progression.

    @verb(role="transform")
    def check_voice_consistency(self, bodies: list[str],
                                  z_threshold: float = 2.0) -> ToolResult:
        """Per-chapter voice-signature outlier check (transform).

        Computes a 3-feature signature per body (avg sentence length /
        filter-word density / flowery-attribution density), then flags
        any chapter whose feature z-score exceeds ``z_threshold`` (default
        2.0 — the documented tunable per spec Open Q1).

        Inputs: bodies (list[str] — one per chapter, in order),
                z_threshold (float — std deviations).
        Returns: ``{passed, signatures, outliers: [{index, feature, z}]}``.
        chain_next: ``novel.line_gate`` for per-chapter line-level scrutiny.
        """
        sigs: list[dict] = []
        for b in bodies:
            tokens = _word_tokens(b)
            total = len(tokens) or 1
            sentences = [s for s in b.split(".") if s.strip()]
            avg_sl = (sum(len(_word_tokens(s)) for s in sentences)
                      / max(1, len(sentences)))
            filter_density = sum(1 for w in tokens
                                  if w.lower() in FILTER_WORDS) / total
            flowery_density = sum(1 for w in tokens
                                   if w.lower() in FLOWERY_ATTRIBUTIONS) / total
            sigs.append({
                "avg_sentence_length": round(avg_sl, 2),
                "filter_density": round(filter_density, 4),
                "flowery_density": round(flowery_density, 4),
            })
        outliers: list[dict] = []
        if len(sigs) >= 3:
            for feat in ("avg_sentence_length", "filter_density",
                         "flowery_density"):
                vals = [s[feat] for s in sigs]
                mean = sum(vals) / len(vals)
                var = sum((v - mean) ** 2 for v in vals) / len(vals)
                std = var ** 0.5
                if std == 0:
                    continue
                for i, v in enumerate(vals):
                    z = abs(v - mean) / std
                    if z > z_threshold:
                        outliers.append({"index": i, "feature": feat,
                                          "z": round(z, 2)})
        return ToolResult.success(data={
            "passed": not outliers,
            "signatures": sigs,
            "outliers": outliers,
        })

    @verb(role="transform")
    def check_pov_consistency(self, novel_id: str) -> ToolResult:
        """Per-chapter POV uniformity check across scenes (transform).

        Walks each chapter's Scene nodes via SCENE_OF and groups POV
        values. A chapter with > 1 distinct POV (excluding scenes that
        declare ``pov=""``) is a flagged break.

        Inputs: novel_id.
        Returns: ``{passed, per_chapter: [{chapter_id, povs, mixed}]}``.
        chain_next: ``novel.line_gate``.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        per_chapter: list[dict] = []
        any_mixed = False
        for c in sorted(chapters, key=lambda c: c.get("number", 0)):
            cid = c.get("id", "")
            scenes = self.ctx.neighbors(cid, "SCENE_OF")
            povs = sorted({s.get("pov") for s in scenes if s.get("pov")})
            mixed = len(povs) > 1
            if mixed:
                any_mixed = True
            per_chapter.append({
                "chapter_id": cid, "number": c.get("number", 0),
                "povs": povs, "mixed": mixed,
            })
        return ToolResult.success(data={
            "passed": not any_mixed,
            "per_chapter": per_chapter,
        })

    @verb(role="transform")
    def check_continuity(self, novel_id: str) -> ToolResult:
        """Cross-chapter proper-noun continuity check (transform).

        Scans each chapter body for proper nouns; flags two patterns:
        (1) names appearing in exactly ONE chapter (likely typos or
        deleted characters), (2) close-distance spelling pairs (e.g.
        Lara/Laura — Levenshtein ≤ 2 + both ≥ 4 chars).

        Inputs: novel_id.
        Returns: ``{passed, single_chapter: [{name, chapter}], close_pairs}``.
        chain_next: ``novel.copy_gate``.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = sorted(
            self.ctx.neighbors(novel_id, "CHAPTER_OF"),
            key=lambda c: c.get("number", 0))
        registry: dict[str, set[int]] = {}
        for c in chapters:
            body = c.get("body", "") or ""
            scan_result = self.check_scan_proper_nouns_helper(body)
            for name in scan_result:
                registry.setdefault(name, set()).add(c.get("number", 0))
        all_names = sorted(registry.keys())
        single_chapter = [
            {"name": n, "chapter": next(iter(registry[n]))}
            for n in all_names if len(registry[n]) == 1
        ]
        close_pairs: list[dict] = []
        for i, a in enumerate(all_names):
            for b in all_names[i + 1:]:
                if len(a) >= 4 and len(b) >= 4 and _levenshtein(a, b) <= 2:
                    close_pairs.append({"a": a, "b": b})
        return ToolResult.success(data={
            "passed": not single_chapter and not close_pairs,
            "single_chapter": single_chapter,
            "close_pairs": close_pairs,
        })

    def check_scan_proper_nouns_helper(self, body: str) -> list[str]:
        """Same scan as `scan_proper_nouns` verb — extracted for in-process reuse."""
        tokens = body.split()
        return sorted({t.strip(".,!?;:") for t in tokens
                       if t and t[0].isupper() and t.strip(".,!?;:").isalpha()
                       and t.strip(".,!?;:") not in _SENTENCE_STARTERS})

    @verb(role="transform")
    def check_sensitivity(self, body: str) -> ToolResult:
        """Sensitivity-topic advisory scan (transform, WARN-severity).

        Extends content-warnings with a documented sensitivity lexicon
        covering mental-health, identity, and trauma-adjacent terms.
        Always passes — sensitivity is informational, not blocking
        (the spec's "exact-severity discipline" — advisory checks never
        gate). Emits ``warnings`` array for the editorial report.

        Inputs: body.
        Returns: ``{passed: True, warnings: [{category, term}]}``.
        chain_next: ``novel.developmental_gate`` (advisory only).
        """
        words = {w.lower() for w in _word_tokens(body)}
        warnings: list[dict] = []
        for category, terms in _SENSITIVITY_LEXICON.items():
            for term in terms:
                if term in words:
                    warnings.append({"category": category, "term": term})
        return ToolResult.success(data={
            "passed": True, "warnings": warnings,
        })

    @verb(role="act")
    def chapter_report_full(self, chapter_id: str) -> ToolResult:
        """Full editorial dashboard for one chapter (act).

        Runs every prose check over the chapter's body and aggregates the
        verdicts; records a ``chapter-report`` Artefact + SERVES intent.

        Inputs: chapter_id.
        Returns: ``{chapter_id, checks: {...}, artefact_id}``.
        chain_next: ``novel.line_gate`` to roll up to a manuscript verdict.
        """
        chapter = self.ctx.recall(chapter_id)
        if chapter is None:
            return ToolResult.failure(
                "NOT_FOUND", f"chapter_id={chapter_id!r} not found")
        body = chapter.get("body", "") or ""
        checks = {
            "readability": self.ctx.call("novel", "analyze_readability",
                                          body=body),
            "filter_words": self.ctx.call("novel", "check_filter_words",
                                           body=body),
            "show_dont_tell": self.ctx.call("novel", "check_show_dont_tell",
                                             body=body),
            "dialogue_attribution": self.ctx.call(
                "novel", "check_dialogue_attribution", body=body),
            "content_warnings": self.ctx.call(
                "novel", "check_content_warnings", body=body),
            "sensitivity": self.ctx.call("novel", "check_sensitivity",
                                          body=body),
        }
        aid = self.ctx.record("Artefact", {
            "kind": "chapter-report",
            "chapter_id": chapter_id,
        })
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "chapter_id": chapter_id,
            "checks": checks,
            "artefact_id": aid,
        })

    @verb(role="effect")
    def developmental_gate(self, novel_id: str) -> ToolResult:
        """Composite gate: structure-level editorial readiness (effect).

        Combines storyform coherence + chapter contiguity + at-least-one
        outlined chapter. Mirrors music's lyric-gate composition pattern.

        Inputs: novel_id.
        Returns: ``{passed, checks}`` or typed GATE_FAILED.
        chain_next: ``novel.line_gate`` once developmental edits are done.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        coh = self.ctx.call("novel", "manuscript_coherence_check",
                             novel_id=novel_id)
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        checks = {
            "chapter_contiguity": bool(coh.get("passed")),
            "has_chapters": bool(chapters),
            "storyform_present": bool([
                s for s in self.ctx.find("Storyform")
                if s.get("novel") == novel_id
            ]),
        }
        if not all(checks.values()):
            return ToolResult.failure(
                "GATE_FAILED",
                f"developmental: missing "
                f"{[k for k, v in checks.items() if not v]}")
        return ToolResult.success(data={"passed": True, "checks": checks})

    @verb(role="effect")
    def line_gate(self, novel_id: str) -> ToolResult:
        """Composite gate: prose-level editorial readiness (effect).

        Every chapter must pass filter-word density + show-don't-tell +
        dialogue attribution thresholds. POV consistency across scenes
        is required too. The exact-severity discipline: advisory
        (sensitivity) does NOT block; structural failures do.

        Inputs: novel_id.
        Returns: ``{passed, checks, per_chapter}`` or typed GATE_FAILED.
        chain_next: ``novel.copy_gate`` once line edits are done.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = sorted(
            self.ctx.neighbors(novel_id, "CHAPTER_OF"),
            key=lambda c: c.get("number", 0))
        per_chapter: list[dict] = []
        all_pass = True
        for c in chapters:
            body = c.get("body", "") or ""
            fw = self.ctx.call("novel", "check_filter_words", body=body)
            sdt = self.ctx.call("novel", "check_show_dont_tell", body=body)
            da = self.ctx.call("novel", "check_dialogue_attribution",
                                body=body)
            ok = (fw.get("passed") and sdt.get("passed")
                  and da.get("passed"))
            if not ok:
                all_pass = False
            per_chapter.append({
                "chapter_id": c.get("id", ""),
                "number": c.get("number", 0),
                "filter_words": fw.get("passed"),
                "show_dont_tell": sdt.get("passed"),
                "dialogue_attribution": da.get("passed"),
                "passed": ok,
            })
        pov = self.ctx.call("novel", "check_pov_consistency",
                             novel_id=novel_id)
        all_pass = all_pass and pov.get("passed", False)
        checks = {
            "all_chapters_line_clean": all([c["passed"] for c in per_chapter]),
            "pov_consistent": pov.get("passed", False),
        }
        if not all_pass:
            return ToolResult.failure(
                "GATE_FAILED",
                f"line: {[k for k, v in checks.items() if not v]}")
        return ToolResult.success(data={
            "passed": True, "checks": checks, "per_chapter": per_chapter,
        })

    @verb(role="effect")
    def copy_gate(self, novel_id: str) -> ToolResult:
        """Composite gate: surface-level editorial readiness (effect).

        Continuity (proper-noun registry) + content warnings DECLARED
        on the novel + readability in genre band (advisory). Continuity
        + content-warning declaration are blocking; readability emits
        warning only.

        Inputs: novel_id.
        Returns: ``{passed, checks, warnings}`` or typed GATE_FAILED.
        chain_next: ``novel.publish_ready_gate``.
        """
        novel, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        cont = self.ctx.call("novel", "check_continuity", novel_id=novel_id)
        cw_declared = bool(novel.get("content_warnings"))
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        readability_warnings: list[str] = []
        for c in chapters:
            body = c.get("body", "") or ""
            if not body:
                continue
            r = self.ctx.call("novel", "analyze_readability", body=body)
            flesch = r.get("flesch_reading_ease", 60.0)
            if flesch < 50 or flesch > 90:
                readability_warnings.append(
                    f"chapter {c.get('number', '?')}: flesch={flesch}")
        checks = {
            "continuity_clean": cont.get("passed", False),
            "content_warnings_declared": cw_declared,
        }
        if not all(checks.values()):
            return ToolResult.failure(
                "GATE_FAILED",
                f"copy: {[k for k, v in checks.items() if not v]}")
        return ToolResult.success(data={
            "passed": True, "checks": checks,
            "readability_warnings": readability_warnings,
        })

    # ───────────────── Spec 105 — research cluster (graph-only) ─────────────────
    # Slice 1 ships 3 graph-only research verbs (mirrors music's 099
    # pattern via the NovelClaim node). The delegating verbs
    # (research_scope, dispatch_research, verify_sources, document_hunt)
    # + composite `verify_gate` + `research-workflow` walkable skill land
    # in Slice 2 once the wiring against agency.research is exercised on
    # a research-bearing novel intent.

    @verb(role="effect")
    def capture_claim(self, text: str, source_uri: str,
                       domain: str) -> ToolResult:
        """Record a NovelClaim node SERVING the intent (effect).

        Inputs: text, source_uri, domain (one of ``RESEARCH_DOMAINS``).
        Returns: ``{claim_id, text, domain, verified}``.
        chain_next: ``novel.verify_sources`` (Slice 2) to cross-check.
        """
        if domain not in RESEARCH_DOMAINS:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"domain={domain!r} not in {sorted(RESEARCH_DOMAINS)}")
        cid = self.ctx.record("NovelClaim", {
            "text": text, "source_uri": source_uri,
            "domain": domain, "verified": "pending",
        })
        self.ctx.link(cid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "claim_id": cid, "text": text,
            "domain": domain, "verified": "pending",
        })

    @verb(role="transform")
    def list_claims(self, verified: str = "") -> ToolResult:
        """List captured claims; optional verified-status filter (transform).

        Inputs: verified (one of ``CLAIM_VERIFIED`` or ``""`` for all).
        Returns: ``{claims, count}``.
        chain_next: ``novel.verify_sources`` for pending claims.
        """
        if verified and verified not in CLAIM_VERIFIED:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"verified={verified!r} not in {sorted(CLAIM_VERIFIED)}")
        claims = [c for c in self.ctx.find("NovelClaim")
                  if not verified or c.get("verified") == verified]
        return ToolResult.success(data={
            "claims": claims, "count": len(claims),
        })

    # ───────────────── Spec 106 — catalogue (graph-only) ─────────────────
    # Slice 1 ships 1 graph-only coherence verb. DBDriver-backed verbs
    # (beta reader registry, edit notes, version log) + composite
    # beta_feedback_gate land in Slice 2 once the DBDriver protocol is
    # declared (parallel to music's 097 pattern).

    @verb(role="transform")
    def manuscript_coherence_check(self, novel_id: str) -> ToolResult:
        """Chapter-sequence contiguity check (transform, driver-free).

        Inputs: novel_id.
        Returns: ``{passed, chapter_count, gaps}`` — gaps lists missing
        chapter numbers between 1 and the max present number.
        chain_next: ``novel.render_manuscript`` when contiguous.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        numbers = sorted({int(c.get("number", 0)) for c in chapters})
        gaps: list[int] = []
        if numbers:
            for n in range(1, max(numbers) + 1):
                if n not in numbers:
                    gaps.append(n)
        return ToolResult.success(data={
            "passed": not gaps,
            "chapter_count": len(chapters),
            "gaps": gaps,
        })

    # ───────────────── Spec 107 — manuscript renderers (driver-free) ─────────────────
    # 3 driver-free artefact renderers for publication packages. The
    # FormatDriver-backed verbs (epub/PDF/docx export via pandoc shell-outs
    # behind a deterministic fake) + composite publication_gate + walkable
    # skills land in Slice 2.
    #
    # Post Round-1 sc-analyze F1 — the 10 vendored markdown templates
    # under `templates/` are NOT consumed by these Slice-1 renderers
    # (each hand-rolls its body via f-strings); they materialise as
    # Template graph nodes per Spec 032 and Slice 2's FormatDriver-backed
    # renderers will read them via `ctx.template(name).template`. Acknowledged
    # debt, not drift — same shape as music's "per-cluster file split
    # deferred" carve-out.

    @verb(role="act")
    def render_blurb(self, novel_id: str, hook: str,
                      stakes: str) -> ToolResult:
        """Render a back-cover blurb (act, driver-free).

        Inputs: novel_id, hook (one-sentence premise), stakes.
        Returns: ``{result, artefact}`` blurb artefact.
        chain_next: ``novel.render_query_letter`` for the agent submission.
        """
        node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        title = node.get("title", "Untitled")
        author = node.get("author", "")
        body = (f"**{title}** by {author}\n\n"
                f"{hook}\n\n"
                f"But {stakes}\n")
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "blurb", "novel": novel_id,
                         "title": title, "author": author,
                         "body": body},
        })

    @verb(role="act")
    def render_query_letter(self, novel_id: str, agent_name: str,
                              comp_titles: str = "") -> ToolResult:
        """Render an agent query letter (act, driver-free).

        Inputs: novel_id, agent_name, comp_titles (comparable titles).
        Returns: ``{result, artefact}`` query-letter artefact.
        chain_next: ``novel.render_synopsis`` to bundle the submission.
        """
        node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        title = node.get("title", "Untitled")
        author = node.get("author", "")
        body = (f"Dear {agent_name},\n\n"
                f"I'm seeking representation for my novel "
                f"**{title}**.\n\n"
                f"For fans of {comp_titles}.\n\n"
                f"Sincerely,\n{author}\n")
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "query-letter", "novel": novel_id,
                         "agent": agent_name, "body": body},
        })

    @verb(role="act")
    def render_synopsis(self, novel_id: str) -> ToolResult:
        """Render a synopsis from chapter outline (act, driver-free).

        Inputs: novel_id.
        Returns: ``{result, artefact}`` synopsis artefact with chapters
        in order.
        chain_next: ``novel.render_query_letter`` for the submission.
        """
        node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = sorted(
            self.ctx.neighbors(novel_id, "CHAPTER_OF"),
            key=lambda c: c.get("number", 0))
        title = node.get("title", "Untitled")
        parts = [f"# Synopsis: {title}\n\n"]
        for c in chapters:
            parts.append(
                f"**Chapter {c.get('number', 0)}: {c.get('title', '')}**\n"
                f"{c.get('body', '')[:200]}\n\n")
        body = "".join(parts)
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "synopsis", "novel": novel_id,
                         "chapter_count": len(chapters), "body": body},
        })

    # ───────────────── Spec 108 — gates (composite) ─────────────────
    # Slice 1 ships 1 composite gate verb wiring the cross-cluster
    # predicates that have actually landed in 101 + 102 + 103 + 105.
    # Slice 2 adds beta-ready / query-ready / publish-ready gates +
    # their walkable skills + the full 6-verb gate surface.

    @verb(role="effect")
    def pre_draft_gate(self, novel_id: str) -> ToolResult:
        """Composite gate: storyform + research + chapters present (effect).

        Inputs: novel_id.
        Returns: ``{passed, checks}`` or typed GATE_FAILED.
        chain_next: ``novel.set_novel_status('drafting')`` once passed.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        claims = list(self.ctx.find("NovelClaim"))
        storyforms = [s for s in self.ctx.find("Storyform")
                      if s.get("novel") == novel_id]
        checks = {
            "chapter_outline": bool(chapters),
            "research_present": bool(claims),
            "storyform_present": bool(storyforms),
        }
        if not all(checks.values()):
            failed = [k for k, v in checks.items() if not v]
            return ToolResult.failure(
                "GATE_FAILED",
                f"pre-draft: missing {failed}")
        return ToolResult.success(data={
            "passed": True, "checks": checks,
        })

    @verb(role="effect")
    def beta_ready_gate(self, novel_id: str) -> ToolResult:
        """Composite gate: all chapters drafted+ (effect).

        Passes IFF every Chapter for the Novel has status ∈
        {drafted, revised, final}. Outlined chapters block.

        Inputs: novel_id.
        Returns: ``{passed, checks}`` or typed GATE_FAILED.
        chain_next: ``novel.set_novel_status('beta')`` then ship to readers.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        drafted_plus = {"drafted", "revised", "final"}
        outlined = [c for c in chapters
                    if c.get("status") not in drafted_plus]
        checks = {
            "has_chapters": bool(chapters),
            "all_chapters_drafted": not outlined,
        }
        if not all(checks.values()):
            failed = [k for k, v in checks.items() if not v]
            return ToolResult.failure(
                "GATE_FAILED",
                f"beta-ready: missing {failed}")
        return ToolResult.success(data={
            "passed": True, "checks": checks,
        })

    @verb(role="effect")
    def query_ready_gate(self, novel_id: str) -> ToolResult:
        """Composite gate: status ≥ beta + content-clean (effect).

        Composes: Novel.status reaches {beta, querying, published}
        AND aggregate chapter body passes check_content_warnings
        (empty warnings list).

        Inputs: novel_id.
        Returns: ``{passed, checks}`` or typed GATE_FAILED.
        chain_next: ``novel.render_query_letter`` then agent submission.
        """
        node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        body = " ".join(c.get("body", "") for c in chapters)
        # Re-use the canonical CONTENT_WARNINGS scanner inline (sibling
        # verb composition stays in-process; no MCP roundtrip).
        words_lower = {w.lower() for w in _word_tokens(body)}
        warnings_hit: list[str] = []
        for category, lexicon in CONTENT_WARNINGS.items():
            if words_lower & lexicon:
                warnings_hit.append(category)
        status_ok = node.get("status") in {"beta", "querying", "published"}
        checks = {
            "status_beta_or_later": status_ok,
            "content_clean": not warnings_hit,
        }
        if not all(checks.values()):
            failed = [k for k, v in checks.items() if not v]
            return ToolResult.failure(
                "GATE_FAILED",
                f"query-ready: missing {failed}; warnings={warnings_hit}")
        return ToolResult.success(data={
            "passed": True, "checks": checks,
            "content_warnings": warnings_hit,
        })

    @verb(role="effect")
    def publish_ready_gate(self, novel_id: str) -> ToolResult:
        """Composite gate: contiguous chapters + status ≥ querying (effect).

        Composes: manuscript_coherence_check (no chapter-number gaps)
        AND Novel.status ∈ {querying, published}. The publication-prep
        terminal gate before set_novel_status('published').

        Inputs: novel_id.
        Returns: ``{passed, checks}`` or typed GATE_FAILED.
        chain_next: ``novel.set_novel_status('published')``.
        """
        node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        numbers = sorted(c.get("number") for c in chapters
                         if isinstance(c.get("number"), int))
        gaps: list[int] = []
        if numbers:
            for n in range(1, max(numbers) + 1):
                if n not in numbers:
                    gaps.append(n)
        status_ok = node.get("status") in {"querying", "published"}
        checks = {
            "no_chapter_gaps": not gaps,
            "status_at_querying_or_later": status_ok,
        }
        if not all(checks.values()):
            failed = [k for k, v in checks.items() if not v]
            return ToolResult.failure(
                "GATE_FAILED",
                f"publish-ready: missing {failed}; gaps={gaps}")
        return ToolResult.success(data={
            "passed": True, "checks": checks,
        })

    # ───────────────── Spec 124 — FormatDriver export verbs ─────────────────
    # 3 export verbs (epub / pdf / docx) hand the rendered manuscript to
    # the wired FormatDriver and record a published-manuscript Artefact.

    def _export_format(self, novel_id: str, fmt: str) -> dict:
        novel_node, fail = self._require_novel(novel_id)
        if fail is not None:
            return {"_fail": fail}
        drv = self._maybe_format_driver()
        if drv is None:
            return {"_fail": ToolResult.failure(
                "DEPENDENCY_MISSING",
                "novel_format driver not wired (set engine._novel_production = True "
                "or add the novel_format driver to Engine(drivers=...))")}
        if fmt not in drv.available_formats():
            return {"_fail": ToolResult.failure(
                "INVALID_ARGUMENT",
                f"format={fmt!r} not in driver.available_formats() "
                f"= {drv.available_formats()}")}
        manuscript_result = self.ctx.call("novel", "render_manuscript",
                                            novel_id=novel_id)
        manuscript_md = (manuscript_result or {}).get("result", "")
        meta = {
            "title": novel_node.get("title", ""),
            "author": novel_node.get("author", ""),
            "genre": novel_node.get("genre", "novel"),
            "slug": novel_node.get("title", "").lower().replace(" ", "-"),
        }
        method = getattr(drv, f"to_{fmt}")
        path = method(manuscript_md, meta)
        aid = self.ctx.record("Artefact", {
            "kind": "published-manuscript",
            "format": fmt, "path": path,
            "novel_id": novel_id,
        })
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        self.ctx.link(self.ctx.intent_id, aid, "PRODUCES")
        return {"format": fmt, "path": path, "artefact_id": aid}

    @verb(role="effect")
    def export_epub(self, novel_id: str) -> ToolResult:
        """Render manuscript + write epub via FormatDriver (effect).

        Inputs: novel_id.
        Returns: ``{format, path, artefact_id}``; typed DEPENDENCY_MISSING
                 when no FormatDriver is wired (production flag off).
        chain_next: ``novel.publication_gate``.
        """
        out = self._export_format(novel_id, "epub")
        if "_fail" in out:
            return out["_fail"]
        return ToolResult.success(data=out)

    @verb(role="effect")
    def export_pdf(self, novel_id: str) -> ToolResult:
        """Render manuscript + write PDF via FormatDriver (effect).

        Inputs: novel_id.
        Returns: ``{format, path, artefact_id}``; typed DEPENDENCY_MISSING
                 when no FormatDriver is wired.
        chain_next: ``novel.publication_gate``.
        """
        out = self._export_format(novel_id, "pdf")
        if "_fail" in out:
            return out["_fail"]
        return ToolResult.success(data=out)

    @verb(role="effect")
    def export_docx(self, novel_id: str) -> ToolResult:
        """Render manuscript + write docx via FormatDriver (effect).

        Inputs: novel_id.
        Returns: ``{format, path, artefact_id}``; typed DEPENDENCY_MISSING
                 when no FormatDriver is wired.
        chain_next: ``novel.publication_gate``.
        """
        out = self._export_format(novel_id, "docx")
        if "_fail" in out:
            return out["_fail"]
        return ToolResult.success(data=out)

    @verb(role="effect")
    def publication_gate(self, novel_id: str) -> ToolResult:
        """Terminal composite: publish_ready + ≥1 export + front-matter declared (effect).

        Composes:
        - ``publish_ready_gate`` (chapters contiguous + status ≥ querying)
        - at least one ``published-manuscript`` Artefact already exists
          (caller has run ``export_epub`` / ``export_pdf`` / ``export_docx``)
        - novel front-matter declares ``content_warnings`` (empty string OK,
          but the field MUST be set so reviewers see a deliberate state).

        Inputs: novel_id.
        Returns: ``{passed, checks, exports: [{format, path}]}`` or typed
                 GATE_FAILED.
        chain_next: terminal — call ``novel.set_novel_status('published')``.
        """
        novel_node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        pub_ready = self.ctx.call("novel", "publish_ready_gate",
                                    novel_id=novel_id)
        ready_passed = bool((pub_ready or {}).get("passed"))
        exports = [
            {"format": a.get("format"), "path": a.get("path")}
            for a in self.ctx.find("Artefact")
            if a.get("kind") == "published-manuscript"
            and a.get("novel_id") == novel_id
        ]
        # `content_warnings` field must be SET (even if empty) — declares
        # the author has thought about it.
        cw_set = "content_warnings" in novel_node
        checks = {
            "publish_ready": ready_passed,
            "has_exports": bool(exports),
            "content_warnings_declared": cw_set,
        }
        if not all(checks.values()):
            return ToolResult.failure(
                "GATE_FAILED",
                f"publication: missing "
                f"{[k for k, v in checks.items() if not v]}")
        return ToolResult.success(data={
            "passed": True, "checks": checks, "exports": exports,
        })

    @verb(role="transform")
    def pending_verifications(self) -> ToolResult:
        """Aggregate pending claims by domain (transform).

        Inputs: none.
        Returns: ``{count, by_domain}`` — only claims with ``verified=="pending"``.
        chain_next: ``novel.dispatch_research`` (Slice 2) to fan out specialists.
        """
        pending = [c for c in self.ctx.find("NovelClaim")
                   if c.get("verified") == "pending"]
        by_domain: dict[str, int] = {}
        for c in pending:
            d = c.get("domain", "unknown")
            by_domain[d] = by_domain.get(d, 0) + 1
        return ToolResult.success(data={
            "count": len(pending), "by_domain": by_domain,
        })

    # ─────────── Tight integration — Research + Prompt + Thinking xcap ───────────
    # Per the goal's tight-integration contract (Spec 114 verb-first routing).
    # Each verb routes through ctx.call so a sibling cap's Invocation links
    # back to the SAME serving intent — the provenance moat distinguishes
    # verb-first routing from raw cross-call.

    @verb(role="effect")
    def dispatch_novel_research(self, question: str,
                                  domain: str) -> ToolResult:
        """Mint a research lead + record NovelClaim (delegates to research cap).

        Routes through ``research.lead`` to mint the Research node, then
        binds the resulting research_id into a NovelClaim that SERVES
        the novel's intent. domain must be one of ``RESEARCH_DOMAINS``.

        Inputs: question, domain (one of RESEARCH_DOMAINS).
        Returns: ``{research_id, claim_id, question, domain}``.
        chain_next: ``research.specialist`` per domain or ``novel.verify_sources``.
        """
        if domain not in RESEARCH_DOMAINS:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"domain={domain!r} not in {sorted(RESEARCH_DOMAINS)}")
        # Cross-cap call — research.lead mints the Research node + serves
        # the current intent. The Invocation+SERVES edge is auto-recorded
        # by Registry.invoke.
        lead = self.ctx.call("research", "lead",
                              question=question, depth="standard")
        research_id = (lead or {}).get("research_id", "")
        # Bind into NovelClaim so the novel cap's provenance traversal
        # surfaces the delegation.
        cid = self.ctx.record("NovelClaim", {
            "text": question, "source_uri": research_id,
            "domain": domain,
        })
        self.ctx.link(cid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "research_id": research_id, "claim_id": cid,
            "question": question, "domain": domain,
        })

    @verb(role="act")
    def render_chapter_brief(self, chapter_id: str,
                               research_intent_id: str = "") -> ToolResult:
        """Produce a research-dossier brief tied to a chapter (act, xcap to prompt).

        Gathers chapter context (parent novel title, chapter title + body
        preview) and renders a research-dossier artefact. When
        ``research_intent_id`` is supplied, chains ``prompt.brief_render``
        to weave the dossier into the body; otherwise renders a minimal
        body from chapter context alone.

        Inputs: chapter_id, research_intent_id (optional).
        Returns: ``{result, artefact}`` research-dossier.
        chain_next: ``novel.dispatch_novel_research`` if more sources needed.
        """
        _, fail = self._require_chapter(chapter_id)
        if fail is not None:
            return fail
        chapter = self.ctx.recall(chapter_id) or {}
        novel_id = chapter.get("novel", "")
        novel = self.ctx.recall(novel_id) or {}
        title = novel.get("title", "Untitled")
        cnum = chapter.get("number", 0)
        ctitle = chapter.get("title", "")
        body_preview = (chapter.get("body") or "")[:300]
        # Cross-cap call when an upstream research intent is available;
        # otherwise render context-only.
        prompt_body = ""
        if research_intent_id:
            try:
                pr = self.ctx.call("prompt", "brief_render",
                                    research_intent_id=research_intent_id)
                if isinstance(pr, dict):
                    prompt_body = pr.get("body", "")
            except Exception:
                # Best-effort — degrade to context-only brief.
                prompt_body = ""
        body = (
            f"# Research Dossier — {title}, Chapter {cnum}: {ctitle}\n\n"
            f"## Chapter context (preview)\n{body_preview}\n\n"
            f"## Research findings\n{prompt_body or '_(none yet — call dispatch_novel_research)_'}\n"
        )
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "research-dossier",
                          "chapter": chapter_id, "novel": novel_id,
                          "body": body},
        })

    @verb(role="act")
    def storyform_critical_pass(self, novel_id: str) -> ToolResult:
        """Critical-thinking pass over the storyform (act, xcap to thinking).

        Walks ``thinking.apply_full_review`` against the novel's storyform
        body (or premise / title as fallback) and surfaces the 8-method
        scaffold as a thinking-analysis artefact. The xcap call records
        a SERVES edge from the thinking cap's Invocation back to this
        intent — provenance traversal sees the critique.

        Inputs: novel_id.
        Returns: ``{result, artefact}`` thinking-analysis.
        chain_next: revise storyform per the surfaced concerns.
        """
        node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        # Build the subject from the most-specific available signal.
        storyforms = [s for s in self.ctx.find("Storyform")
                      if s.get("novel") == novel_id]
        subject = (storyforms[0].get("body") if storyforms
                    and storyforms[0].get("body")
                    else f"Novel: {node.get('title','')} by {node.get('author','')}")
        # Cross-cap call — thinking.apply_full_review serves the same intent.
        tr = self.ctx.call("thinking", "apply_full_review",
                            subject=subject, depth="standard")
        body = (tr or {}).get("result") or (tr or {}).get("body") or str(tr or "")
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "thinking-analysis",
                          "novel": novel_id, "body": body},
        })

    @verb(role="effect")
    def record_storyform_decision(self, novel_id: str, decision: str,
                                    rationale: str = "") -> ToolResult:
        """Record a contested storyform decision (effect, xcap to dogfood).

        Routes through ``dogfood.record_decision`` so the decision lands
        in the cluster-wide decision audit. ``subject`` is bound to the
        novel id so analyses can filter by story.

        Inputs: novel_id, decision, rationale (optional).
        Returns: ``{novel_id, decision_id, decision}``.
        chain_next: continue authoring; later ``analyze.graph`` reads
                    the audit trail.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        result = self.ctx.call("dogfood", "record_decision",
                                subject=novel_id,
                                decision=decision,
                                rationale=rationale)
        decision_id = (result or {}).get("decision_id", "")
        return ToolResult.success(data={
            "novel_id": novel_id,
            "decision_id": decision_id,
            "decision": decision,
        })

    # ──────────────────── Spec 123 — World sub-graph (Slice 1) ────────────────────
    # World shapes the bible the author references; Culture / Religion /
    # Language / MagicSystem populate it; WorldAxiom carries the
    # load-bearing rules. Slice 2 lands character psychology +
    # foreshadowing + skill rewiring.

    @verb(role="effect")
    def create_world(self, slug: str, name: str) -> ToolResult:
        """Mint a World node + SERVES intent (effect).

        Inputs: slug (URL-safe handle), name (human label).
        Returns: ``{world_id, slug, name}``.
        chain_next: ``novel.create_culture`` / ``create_religion`` /
                    ``create_language`` / ``create_magic_system`` /
                    ``create_world_axiom`` to populate it.
        """
        wid = self.ctx.record("World", {"slug": slug, "name": name})
        self.ctx.link(wid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "world_id": wid, "slug": slug, "name": name,
        })

    @verb(role="effect")
    def create_culture(self, world_id: str, slug: str,
                        name: str) -> ToolResult:
        """Mint a Culture under a World + PART_OF_WORLD edge (effect).

        Inputs: world_id, slug, name.
        Returns: ``{culture_id, world_id, slug, name}``.
        chain_next: continue populating the world.
        """
        return self._create_world_child(
            world_id, "Culture", slug, name, return_key="culture_id")

    @verb(role="effect")
    def create_religion(self, world_id: str, slug: str,
                         name: str) -> ToolResult:
        """Mint a Religion under a World + PART_OF_WORLD edge (effect).

        Inputs: world_id, slug, name.
        Returns: ``{religion_id, world_id, slug, name}``.
        chain_next: continue populating the world.
        """
        return self._create_world_child(
            world_id, "Religion", slug, name, return_key="religion_id")

    @verb(role="effect")
    def create_language(self, world_id: str, slug: str,
                         name: str) -> ToolResult:
        """Mint a Language under a World + PART_OF_WORLD edge (effect).

        Inputs: world_id, slug, name.
        Returns: ``{language_id, world_id, slug, name}``.
        chain_next: continue populating the world.
        """
        return self._create_world_child(
            world_id, "Language", slug, name, return_key="language_id")

    @verb(role="effect")
    def create_magic_system(self, world_id: str, slug: str,
                             name: str) -> ToolResult:
        """Mint a MagicSystem under a World + PART_OF_WORLD edge (effect).

        Inputs: world_id, slug, name.
        Returns: ``{magic_system_id, world_id, slug, name}``.
        chain_next: ``novel.create_world_axiom`` to encode its rules.
        """
        return self._create_world_child(
            world_id, "MagicSystem", slug, name,
            return_key="magic_system_id")

    def _create_world_child(self, world_id: str, label: str, slug: str,
                              name: str, *, return_key: str) -> ToolResult:
        world = self.ctx.recall(world_id)
        if world is None:
            return ToolResult.failure(
                "NOT_FOUND", f"world_id={world_id!r} not found")
        nid = self.ctx.record(label, {"slug": slug, "name": name})
        self.ctx.link(nid, world_id, "PART_OF_WORLD")
        self.ctx.link(nid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            return_key: nid, "world_id": world_id,
            "slug": slug, "name": name,
        })

    @verb(role="effect")
    def create_world_axiom(self, world_id: str, text: str,
                            severity: str = "hard") -> ToolResult:
        """Encode a WorldAxiom (rule) under a World (effect).

        Inputs: world_id, text (the rule body — concise),
                severity (one of ``WORLD_AXIOM_SEVERITY``: hard | soft).
        Returns: ``{axiom_id, world_id, severity, text}``.
        chain_next: ``novel.find_axiom_contradictions`` after several land.
        """
        if severity not in WORLD_AXIOM_SEVERITY:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"severity={severity!r} not in {sorted(WORLD_AXIOM_SEVERITY)}")
        world = self.ctx.recall(world_id)
        if world is None:
            return ToolResult.failure(
                "NOT_FOUND", f"world_id={world_id!r} not found")
        aid = self.ctx.record("WorldAxiom", {
            "text": text, "severity": severity,
        })
        self.ctx.link(aid, world_id, "PART_OF_WORLD")
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "axiom_id": aid, "world_id": world_id,
            "severity": severity, "text": text,
        })

    @verb(role="transform")
    def list_world(self, world_id: str) -> ToolResult:
        """Render a tree of a World's contents (transform).

        Walks PART_OF_WORLD edges (Spec 125 `ctx.neighbors`) and groups
        the children by label.

        Inputs: world_id.
        Returns: ``{world, cultures, religions, languages, magic_systems,
                  axioms}``.
        chain_next: ``novel.find_axiom_contradictions`` for the rule audit.
        """
        world = self.ctx.recall(world_id)
        if world is None:
            return ToolResult.failure(
                "NOT_FOUND", f"world_id={world_id!r} not found")
        children = self.ctx.neighbors(world_id, "PART_OF_WORLD")
        groups = {
            "cultures": [], "religions": [], "languages": [],
            "magic_systems": [], "axioms": [],
        }
        label_to_key = {
            "Culture": "cultures", "Religion": "religions",
            "Language": "languages", "MagicSystem": "magic_systems",
            "WorldAxiom": "axioms",
        }
        for c in children:
            # The child's "labels" aren't on the props dict; look up the
            # node to discover its label set.
            node = self.ctx.memory.g.get_node(c.get("id", ""))
            if node is None:
                continue
            for label in (node.get("labels") or []):
                if label in label_to_key:
                    groups[label_to_key[label]].append(c)
                    break
        return ToolResult.success(data={
            "world": {"id": world_id, "slug": world.get("slug"),
                       "name": world.get("name")},
            **groups,
        })

    @verb(role="effect")
    def find_axiom_contradictions(self, world_id: str) -> ToolResult:
        """Decidable axiom-contradiction scan + emit CONTRADICTS edges (effect).

        Per Open Q2 (resolved as v1 decidable): flags axiom pairs whose
        bodies share ≥ 2 motif words AND one carries a negation marker
        the other lacks (``not``, ``never``, ``no``). The judgement pass
        (full red_team) is a future xcap to ``thinking.red_team``.

        Inputs: world_id.
        Returns: ``{passed, contradictions: [{a_id, b_id, a_text, b_text}]}``.
        chain_next: walk pairs; refine wording; rerun.
        """
        if self.ctx.recall(world_id) is None:
            return ToolResult.failure(
                "NOT_FOUND", f"world_id={world_id!r} not found")
        axioms = [a for a in self.ctx.neighbors(world_id, "PART_OF_WORLD")
                   if "text" in a and "severity" in a]
        contradictions: list[dict] = []
        negations = {"not", "never", "no", "cannot", "without"}
        for i, a in enumerate(axioms):
            a_words = {w.lower() for w in _word_tokens(a.get("text", ""))}
            a_neg = bool(a_words & negations)
            for b in axioms[i + 1:]:
                b_words = {w.lower() for w in _word_tokens(b.get("text", ""))}
                b_neg = bool(b_words & negations)
                shared = a_words & b_words - negations
                # Two axioms share motif words AND exactly one carries
                # a negation marker → likely contradiction.
                if len(shared) >= 2 and (a_neg ^ b_neg):
                    contradictions.append({
                        "a_id": a.get("id"), "b_id": b.get("id"),
                        "a_text": a.get("text"),
                        "b_text": b.get("text"),
                    })
                    # Record CONTRADICTS edge so the relationship is
                    # queryable from the graph (not just the verb return).
                    self.ctx.link(a.get("id"), b.get("id"), "CONTRADICTS")
        return ToolResult.success(data={
            "passed": not contradictions,
            "contradictions": contradictions,
        })

    @verb(role="effect")
    def link_character_to_world(self, character_id: str, target_id: str,
                                 edge_kind: str = "BELONGS_TO") -> ToolResult:
        """Add a typed edge from Character → World child (effect).

        ``edge_kind`` is constrained to the documented set:
        ``BELONGS_TO`` (catch-all), ``INHABITS`` (lives in / Culture),
        ``WORSHIPS`` (Religion), ``SPEAKS`` (Language), ``WIELDS``
        (MagicSystem). The orchestrator picks one matching the target's
        label.

        Inputs: character_id, target_id, edge_kind.
        Returns: ``{character_id, target_id, edge_kind}``.
        chain_next: continue weaving the character into the world.
        """
        if edge_kind not in _CHARACTER_WORLD_EDGES:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"edge_kind={edge_kind!r} not in "
                f"{sorted(_CHARACTER_WORLD_EDGES)}")
        # Character node doesn't exist in the ontology yet (Slice 2);
        # accept any node id pending the character-psychology layer.
        if self.ctx.recall(character_id) is None:
            return ToolResult.failure(
                "NOT_FOUND", f"character_id={character_id!r} not found")
        if self.ctx.recall(target_id) is None:
            return ToolResult.failure(
                "NOT_FOUND", f"target_id={target_id!r} not found")
        self.ctx.link(character_id, target_id, edge_kind)
        return ToolResult.success(data={
            "character_id": character_id, "target_id": target_id,
            "edge_kind": edge_kind,
        })

    # ───────────────── Spec 128 — story-time / narrative-time ─────────────────
    # StoryTimeEvent + NarrativeBeat + 6 verbs. Closes Spec 127's
    # `_compose_continuity` placeholder; that composer now reads the event
    # list from the graph (see prompt._main.py).

    @verb(role="effect")
    def record_story_event(self, novel_id: str, label: str,
                            when_story: str,
                            scene_id: str = "") -> ToolResult:
        """Mint a StoryTimeEvent + optional HAPPENS_AT edge from a scene (effect).

        ``when_story`` is a plain string by design (Open Q1) — the author
        owns sortability. Lexicographic sort is the slice contract for
        ``list_story_events_up_to``.

        Inputs: novel_id, label (short event name), when_story (sortable
                string), scene_id (optional — when supplied, mints
                Scene-HAPPENS_AT->Event edge).
        Returns: ``{event_id, label, when_story, scene_id?}``.
        chain_next: ``novel.reveal_in_scene`` for foreshadow/payoff.
        """
        if self.ctx.recall(novel_id) is None:
            return ToolResult.failure(
                "NOT_FOUND", f"novel_id={novel_id!r} not found")
        eid = self.ctx.record("StoryTimeEvent", {
            "novel": novel_id, "label": label, "when_story": when_story,
        })
        self.ctx.link(eid, self.ctx.intent_id, "SERVES")
        out: dict = {"event_id": eid, "label": label,
                     "when_story": when_story}
        if scene_id:
            if self.ctx.recall(scene_id) is None:
                return ToolResult.failure(
                    "NOT_FOUND", f"scene_id={scene_id!r} not found")
            self.ctx.link(scene_id, eid, "HAPPENS_AT")
            out["scene_id"] = scene_id
        return ToolResult.success(data=out)

    @verb(role="effect")
    def reveal_in_scene(self, event_id: str, scene_id: str) -> ToolResult:
        """Add the REVEALED_IN edge (event disclosed by this scene) (effect).

        Inputs: event_id (existing StoryTimeEvent), scene_id (existing Scene).
        Returns: ``{event_id, scene_id}``.
        chain_next: ``novel.list_reveals_in(scene_id)`` to verify.
        """
        if self.ctx.recall(event_id) is None:
            return ToolResult.failure(
                "NOT_FOUND", f"event_id={event_id!r} not found")
        if self.ctx.recall(scene_id) is None:
            return ToolResult.failure(
                "NOT_FOUND", f"scene_id={scene_id!r} not found")
        self.ctx.link(event_id, scene_id, "REVEALED_IN")
        return ToolResult.success(data={
            "event_id": event_id, "scene_id": scene_id,
        })

    @verb(role="transform")
    def list_story_events_up_to(self, scene_id: str) -> ToolResult:
        """Story-time slice: events with ``when_story`` ≤ this scene's anchor (transform).

        The scene's anchor is the ``when_story`` of any StoryTimeEvent the
        scene HAPPENS_AT. If the scene has multiple, takes the latest. No
        anchor → empty list (the scene has no story-time reference frame
        yet).

        Inputs: scene_id.
        Returns: ``{anchor_when, events: [{event_id, label, when_story}]}``.
        chain_next: ``prompt.assemble_scene_brief`` consumes this for the
                    continuity section.
        """
        scene = self.ctx.recall(scene_id)
        if scene is None:
            return ToolResult.failure(
                "NOT_FOUND", f"scene_id={scene_id!r} not found")
        anchors = self.ctx.neighbors(scene_id, "HAPPENS_AT", direction="out")
        if not anchors:
            return ToolResult.success(data={
                "anchor_when": None, "events": [],
            })
        anchor_when = max(a.get("when_story", "") for a in anchors)
        novel_id = (self.ctx.recall(scene.get("chapter", "")) or {}
                    ).get("novel", "")
        events = [
            {"event_id": ev.get("id"), "label": ev.get("label"),
             "when_story": ev.get("when_story")}
            for ev in self.ctx.find("StoryTimeEvent")
            if ev.get("novel") == novel_id
            and (ev.get("when_story") or "") <= anchor_when
        ]
        events.sort(key=lambda e: e["when_story"] or "")
        return ToolResult.success(data={
            "anchor_when": anchor_when, "events": events,
        })

    @verb(role="transform")
    def list_reveals_in(self, scene_id: str) -> ToolResult:
        """List events this scene discloses (transform).

        Walks REVEALED_IN edges incoming on the scene (so an Event points
        to a Scene as its reveal point).

        Inputs: scene_id.
        Returns: ``{reveals: [{event_id, label, when_story}]}``.
        chain_next: author's checklist for "is the reveal landing here?".
        """
        if self.ctx.recall(scene_id) is None:
            return ToolResult.failure(
                "NOT_FOUND", f"scene_id={scene_id!r} not found")
        reveals = self.ctx.neighbors(scene_id, "REVEALED_IN", direction="in")
        return ToolResult.success(data={
            "reveals": [
                {"event_id": r.get("id"), "label": r.get("label"),
                 "when_story": r.get("when_story")}
                for r in reveals
            ],
        })

    @verb(role="effect")
    def mark_narrative_beat(self, scene_id: str, beat_label: str,
                             predecessor_id: str = "") -> ToolResult:
        """Mint a NarrativeBeat + optional PRECEDES edge from a predecessor (effect).

        Inputs: scene_id, beat_label (e.g. "opening-image" or
                "inciting-incident"), predecessor_id (optional — links the
                new beat into the narrative-order DAG).
        Returns: ``{beat_id, scene_id, label}``.
        chain_next: ``novel.narrative_order(novel_id)`` to read topo-sort.
        """
        scene = self.ctx.recall(scene_id)
        if scene is None:
            return ToolResult.failure(
                "NOT_FOUND", f"scene_id={scene_id!r} not found")
        # Spec 282 Workstream C — validate ALL preconditions BEFORE any write,
        # so a bad predecessor never leaves an orphan NarrativeBeat node (the
        # create-node-then-fail-edge partial write). The node + its PRECEDES
        # edge land together or not at all.
        if predecessor_id and self.ctx.recall(predecessor_id) is None:
            return ToolResult.failure(
                "NOT_FOUND",
                f"predecessor_id={predecessor_id!r} not found")
        novel_id = (self.ctx.recall(scene.get("chapter", "")) or {}
                    ).get("novel", "")
        bid = self.ctx.record("NarrativeBeat", {
            "novel": novel_id, "label": beat_label, "scene": scene_id,
        })
        self.ctx.link(bid, self.ctx.intent_id, "SERVES")
        if predecessor_id:
            self.ctx.link(predecessor_id, bid, "PRECEDES")
        return ToolResult.success(data={
            "beat_id": bid, "scene_id": scene_id, "label": beat_label,
        })

    @verb(role="transform")
    def narrative_order(self, novel_id: str) -> ToolResult:
        """Topo-sort over PRECEDES; canonical narrative reading order (transform).

        Inputs: novel_id.
        Returns: ``{beats: [{beat_id, label, scene_id}]}`` ordered so every
                 predecessor appears before its successor.
        chain_next: author's checklist for the manuscript's narrative spine.
        """
        if self.ctx.recall(novel_id) is None:
            return ToolResult.failure(
                "NOT_FOUND", f"novel_id={novel_id!r} not found")
        beats = [b for b in self.ctx.find("NarrativeBeat")
                  if b.get("novel") == novel_id]
        # Build predecessor map by querying PRECEDES.
        precedes_rows = self.ctx.memory.g.query(
            "MATCH (a:NarrativeBeat)-[:PRECEDES]->(b:NarrativeBeat) "
            "RETURN a, b")
        edges = []
        for r in precedes_rows:
            a_id = r["a"]["properties"].get("id")
            b_id = r["b"]["properties"].get("id")
            if a_id and b_id:
                edges.append((a_id, b_id))
        # Kahn's algorithm over the beats of THIS novel.
        beat_ids = {b.get("id") for b in beats}
        in_degree = {bid: 0 for bid in beat_ids}
        successors: dict = {bid: [] for bid in beat_ids}
        for a, b in edges:
            if a in beat_ids and b in beat_ids:
                in_degree[b] += 1
                successors[a].append(b)
        queue = [bid for bid, d in in_degree.items() if d == 0]
        order: list[str] = []
        while queue:
            n = queue.pop(0)
            order.append(n)
            for s in successors[n]:
                in_degree[s] -= 1
                if in_degree[s] == 0:
                    queue.append(s)
        beat_by_id = {b.get("id"): b for b in beats}
        return ToolResult.success(data={
            "beats": [
                {"beat_id": bid,
                 "label": beat_by_id[bid].get("label"),
                 "scene_id": beat_by_id[bid].get("scene")}
                for bid in order if bid in beat_by_id
            ],
        })

    # ───────────────── Spec 132 — codex entries (Novelcrafter parity) ─────────────────
    # CodexEntry + CODEX_OF + 5 verbs. Closes Spec 127's `_world_rules`
    # placeholder; that composer now scans the scene's text against
    # registered triggers and injects matched bodies.

    @verb(role="effect")
    def create_codex_entry(self, novel_id: str, slug: str, name: str,
                            kind: str, body: str,
                            triggers: str = "") -> ToolResult:
        """Mint a CodexEntry + CODEX_OF edge to the Novel (effect).

        Inputs: novel_id, slug, name, kind (one of CODEX_ENTRY_KIND),
                body (agent-facing description), triggers (comma-separated
                trigger phrases; defaults to ``name, slug`` if empty).
        Returns: ``{entry_id, slug, name, kind}``.
        chain_next: ``novel.match_codex_entries`` to verify auto-injection.
        """
        if kind not in CODEX_ENTRY_KIND:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"kind={kind!r} not in {sorted(CODEX_ENTRY_KIND)}")
        if self.ctx.recall(novel_id) is None:
            return ToolResult.failure(
                "NOT_FOUND", f"novel_id={novel_id!r} not found")
        if not triggers:
            triggers = f"{name}, {slug}"
        cid = self.ctx.record("CodexEntry", {
            "novel": novel_id, "slug": slug, "name": name,
            "kind": kind, "body": body, "triggers": triggers,
        })
        self.ctx.link(cid, novel_id, "CODEX_OF")
        self.ctx.link(cid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "entry_id": cid, "slug": slug, "name": name, "kind": kind,
        })

    @verb(role="transform")
    def list_codex_entries(self, novel_id: str,
                            kind: str = "") -> ToolResult:
        """List CodexEntries for a novel, optionally filtered by kind (transform).

        Inputs: novel_id, kind (optional — one of CODEX_ENTRY_KIND).
        Returns: ``{entries: [{entry_id, slug, name, kind, body}], count}``.
        chain_next: ``novel.match_codex_entries`` to scan a body.
        """
        if kind and kind not in CODEX_ENTRY_KIND:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"kind={kind!r} not in {sorted(CODEX_ENTRY_KIND)}")
        entries = [
            {"entry_id": e.get("id"), "slug": e.get("slug"),
             "name": e.get("name"), "kind": e.get("kind"),
             "body": e.get("body")}
            for e in self.ctx.find("CodexEntry")
            if e.get("novel") == novel_id
            and (not kind or e.get("kind") == kind)
            and e.get("archived") != "yes"
        ]
        return ToolResult.success(data={
            "entries": entries, "count": len(entries),
        })

    @verb(role="transform")
    def match_codex_entries(self, novel_id: str,
                              text: str) -> ToolResult:
        """Scan ``text`` for any registered codex trigger; return matches (transform).

        Case-insensitive whole-substring match (the simpler half of the
        Novelcrafter behaviour; word-boundary matching is a Slice 2
        refinement). Archived entries are skipped.

        Inputs: novel_id, text (the body to scan — chapter outline, scene
                draft, etc.).
        Returns: ``{matches: [{entry_id, slug, name, kind, body,
                  trigger_hit}]}``.
        chain_next: feed matches to ``prompt.assemble_scene_brief``'s
                    world_rules section.
        """
        text_l = text.lower()
        matches: list[dict] = []
        for e in self.ctx.find("CodexEntry"):
            if e.get("novel") != novel_id:
                continue
            if e.get("archived") == "yes":
                continue
            triggers = [t.strip() for t in (e.get("triggers") or "").split(",")
                        if t.strip()]
            for trigger in triggers:
                if trigger.lower() in text_l:
                    matches.append({
                        "entry_id": e.get("id"),
                        "slug": e.get("slug"),
                        "name": e.get("name"),
                        "kind": e.get("kind"),
                        "body": e.get("body"),
                        "trigger_hit": trigger,
                    })
                    break   # one match per entry — don't duplicate
        return ToolResult.success(data={"matches": matches})

    @verb(role="effect")
    def update_codex_entry(self, entry_id: str,
                            body: str = "", triggers: str = "",
                            name: str = "") -> ToolResult:
        """Edit a CodexEntry's body / triggers / name (effect).

        Inputs: entry_id; any of body / triggers / name (empty = unchanged).
        Returns: ``{entry_id, fields_updated: [str]}``.
        chain_next: ``novel.list_codex_entries`` to verify.
        """
        node = self.ctx.recall(entry_id)
        if node is None:
            return ToolResult.failure(
                "NOT_FOUND", f"entry_id={entry_id!r} not found")
        updates: dict = {}
        if body:
            updates["body"] = body
        if triggers:
            updates["triggers"] = triggers
        if name:
            updates["name"] = name
        if updates:
            self.ctx.memory.update(entry_id, updates)
        return ToolResult.success(data={
            "entry_id": entry_id,
            "fields_updated": sorted(updates.keys()),
        })

    @verb(role="effect")
    def archive_codex_entry(self, entry_id: str,
                              reason: str = "") -> ToolResult:
        """Flag a CodexEntry as archived (effect, soft-delete).

        Archived entries are skipped by ``match_codex_entries`` and
        ``list_codex_entries``. They remain in the graph for provenance.

        Inputs: entry_id, reason (optional — recorded in `archived_reason`).
        Returns: ``{entry_id, archived: True}``.
        chain_next: ``novel.list_codex_entries`` to verify the prune.
        """
        node = self.ctx.recall(entry_id)
        if node is None:
            return ToolResult.failure(
                "NOT_FOUND", f"entry_id={entry_id!r} not found")
        self.ctx.memory.update(entry_id, {
            "archived": "yes",
            "archived_reason": reason or "",
        })
        return ToolResult.success(data={
            "entry_id": entry_id, "archived": True,
        })

    # ───────────────── Spec 131 — character-knowledge ledger ─────────────────
    # KnownFact node + KNOWS / LEARNED_IN edges + 3 verbs. Closes Spec 127's
    # `_pov_card` knowledge gap when a scene declares `pov_character_id`.

    @verb(role="effect")
    def record_character_learns(self, character_id: str, fact: str,
                                  scene_id: str) -> ToolResult:
        """Mint a KnownFact + KNOWS + LEARNED_IN edges (effect).

        Inputs: character_id (any node id — Character ontology lands in
                Spec 123 Slice 2; for now any id works), fact (freeform),
                scene_id (existing Scene).
        Returns: ``{fact_id, character_id, scene_id}``.
        chain_next: ``novel.what_does_X_know_as_of`` to verify.
        """
        if self.ctx.recall(character_id) is None:
            return ToolResult.failure(
                "NOT_FOUND",
                f"character_id={character_id!r} not found")
        if self.ctx.recall(scene_id) is None:
            return ToolResult.failure(
                "NOT_FOUND", f"scene_id={scene_id!r} not found")
        fid = self.ctx.record("KnownFact", {
            "character": character_id, "fact": fact,
        })
        self.ctx.link(character_id, fid, "KNOWS")
        self.ctx.link(fid, scene_id, "LEARNED_IN")
        self.ctx.link(fid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "fact_id": fid, "character_id": character_id,
            "scene_id": scene_id,
        })

    @verb(role="transform")
    def what_does_X_know_as_of(self, character_id: str,
                                  scene_id: str) -> ToolResult:
        """List facts the character has learned ≤ the scene's narrative position (transform).

        Narrative-position is approximated by the chapter number of the
        LEARNED_IN scene vs the target scene. When chapter numbers tie,
        scene-creation order within the chapter is the tie-breaker.

        Inputs: character_id, scene_id.
        Returns: ``{facts: [{fact_id, fact, learned_in_scene}]}``.
        chain_next: feed into ``prompt.assemble_scene_brief``'s pov_card.
        """
        target = self.ctx.recall(scene_id)
        if target is None:
            return ToolResult.failure(
                "NOT_FOUND", f"scene_id={scene_id!r} not found")
        target_chapter = (self.ctx.recall(target.get("chapter", "")) or {}
                          ).get("number", 0)
        # Walk KNOWS to get the character's facts.
        facts: list[dict] = []
        for f in self.ctx.neighbors(character_id, "KNOWS", direction="out"):
            # LEARNED_IN scene of this fact.
            learned = self.ctx.neighbors(f.get("id", ""), "LEARNED_IN",
                                           direction="out")
            if not learned:
                continue
            ls = learned[0]
            l_chapter = (self.ctx.recall(ls.get("chapter", "")) or {}
                         ).get("number", 0)
            if l_chapter <= target_chapter:
                facts.append({
                    "fact_id": f.get("id"),
                    "fact": f.get("fact"),
                    "learned_in_scene": ls.get("id"),
                })
        return ToolResult.success(data={"facts": facts})

    @verb(role="transform")
    def flag_anachronistic_reference(self, scene_id: str,
                                       character_id: str,
                                       fact_text: str) -> ToolResult:
        """Check if the character knows the fact yet (transform).

        Walks the character's KNOWS to find a matching fact; if found,
        compares LEARNED_IN scene's chapter number to the target scene's.
        When LEARNED_IN's chapter > target's chapter → anachronism (the
        character references something they haven't learned yet).

        Inputs: scene_id (the scene that references the fact),
                character_id, fact_text (the fact body to match).
        Returns: ``{anachronism, expected_learned_in?, no_record?}``.
        chain_next: revise the scene OR add a `record_character_learns`
                    earlier in the manuscript.
        """
        target = self.ctx.recall(scene_id)
        if target is None:
            return ToolResult.failure(
                "NOT_FOUND", f"scene_id={scene_id!r} not found")
        target_chapter_node = self.ctx.recall(target.get("chapter", ""))
        target_chapter = (target_chapter_node or {}).get("number", 0)
        target_title = (target_chapter_node or {}).get("title", "")
        # Find a KnownFact for this character whose body matches.
        for f in self.ctx.neighbors(character_id, "KNOWS", direction="out"):
            if (f.get("fact") or "").strip() != fact_text.strip():
                continue
            learned = self.ctx.neighbors(f.get("id", ""), "LEARNED_IN",
                                           direction="out")
            if not learned:
                continue
            ls = learned[0]
            l_chapter_node = self.ctx.recall(ls.get("chapter", ""))
            l_chapter = (l_chapter_node or {}).get("number", 0)
            l_title = (l_chapter_node or {}).get("title", "")
            anachronism = l_chapter > target_chapter
            return ToolResult.success(data={
                "anachronism": anachronism,
                "expected_learned_in": (f"Ch {l_chapter}: {l_title}"
                                          if l_title else
                                          f"scene {ls.get('id', '?')}"),
            })
        # No record of this character ever learning the fact.
        return ToolResult.success(data={
            "anachronism": False, "no_record": True,
        })

    @verb(role="transform")
    def audit_novel_provenance(self, novel_id: str) -> ToolResult:
        """Aggregate the provenance graph census for the serving intent (transform, xcap to analyze).

        Routes through ``analyze.graph`` to surface a node-type census
        + verb summary. The audit catches which cluster caps have
        SERVED the novel's intent across the session.

        Inputs: novel_id (validated for NOT_FOUND only).
        Returns: ``{novel_id, census, capabilities}``.
        chain_next: revise the storyform per surfaced gaps.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        # analyze.graph returns a census + typed listing for the current intent.
        result = self.ctx.call("analyze", "graph",
                                node_type="Invocation", limit=200)
        census = (result or {}).get("census") or {}
        nodes = (result or {}).get("nodes") or []
        caps = sorted({n.get("capability", "") for n in nodes
                       if n.get("capability")})
        return ToolResult.success(data={
            "novel_id": novel_id,
            "census": census,
            "capabilities": caps,
        })
