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

from agency.capability import CapabilityBase, RenderTemplates, verb
from agency.ontology import OntologyExtension
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
    },
    enums={
        ("Novel",   "status"): NOVEL_STATUS,
        ("Chapter", "status"): CHAPTER_STATUS,
        ("Idea",    "status"): IDEA_STATUS,
        ("NovelClaim", "verified"): CLAIM_VERIFIED,
        ("NovelClaim", "domain"):   RESEARCH_DOMAINS,
        ("Scene",   "pov"): SCENE_POV,
    },
    edges={
        "CHAPTER_OF",       # Chapter → Novel (mirror of music's RECORDED_FOR)
        "PROMOTED_TO",      # Idea → Novel (mirror of music's PROMOTED_TO)
        "SCENE_OF",         # Spec 102 Slice 2 — Scene → Chapter
    },
    skills={"novel-concept": NOVEL_CONCEPT_SKILL,
            "character-architect": CHARACTER_ARCHITECT_SKILL,
            "world-bible-architect": WORLD_BIBLE_ARCHITECT_SKILL,
            "scene-bridge-auditor": SCENE_BRIDGE_AUDITOR_SKILL,
            "storyform-build": STORYFORM_BUILD_SKILL},
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
    _NOVEL_DRIVER_NAMES = ("novel_state",)

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
        reg = self.ctx.drivers
        if reg is None or not self._production_enabled():
            return None
        if not reg.has("novel_state"):
            self._autowire_novel_drivers()
        if reg.has("novel_state"):
            return reg.get("novel_state")
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

    @verb(role="effect")
    def create_scene(self, chapter_id: str, slug: str,
                      pov: str) -> ToolResult:
        """Record a Scene node + SCENE_OF the parent Chapter (effect).

        Inputs: chapter_id, slug (scene-local short name), pov (one of
                ``SCENE_POV``).
        Returns: ``{scene_id, chapter_id, slug, pov}``.
        chain_next: ``novel.create_scene`` for next beat or back to
                    ``novel.set_chapter_status`` once the chapter's
                    scene set is complete.
        """
        if pov not in SCENE_POV:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"pov={pov!r} not in {sorted(SCENE_POV)}")
        _, fail = self._require_chapter(chapter_id)
        if fail is not None:
            return fail
        sid = self.ctx.record("Scene", {
            "chapter": chapter_id, "slug": slug, "pov": pov,
        })
        self.ctx.link(sid, chapter_id, "SCENE_OF")
        self.ctx.link(sid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "scene_id": sid, "chapter_id": chapter_id,
            "slug": slug, "pov": pov,
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
