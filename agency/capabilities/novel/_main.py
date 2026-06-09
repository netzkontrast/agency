# agency-scaffold: v1
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


# ─────────────────────────── enums ───────────────────────────
NOVEL_STATUS = {"concept", "outlining", "drafting", "revising",
                "beta", "querying", "published"}
CHAPTER_STATUS = {"outlined", "drafted", "revised", "final"}
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
    },
    enums={
        ("Novel",   "status"): NOVEL_STATUS,
        ("Chapter", "status"): CHAPTER_STATUS,
        ("Idea",    "status"): IDEA_STATUS,
        ("NovelClaim", "verified"): CLAIM_VERIFIED,
        ("NovelClaim", "domain"):   RESEARCH_DOMAINS,
    },
    edges={
        "CHAPTER_OF",       # Chapter → Novel (mirror of music's RECORDED_FOR)
        "PROMOTED_TO",      # Idea → Novel (mirror of music's PROMOTED_TO)
    },
    skills={"novel-concept": NOVEL_CONCEPT_SKILL},
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
    def create_novel(self, title: str, author: str) -> ToolResult:
        """Record a Novel node SERVING the intent (effect).

        Inputs: title, author.
        Returns: ``{novel_id, title, status}``.
        chain_next: ``novel.create_chapter`` once outline is ready.
        """
        nid = self.ctx.record("Novel", {
            "title": title, "author": author, "status": "concept",
        })
        self.ctx.link(nid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "novel_id": nid, "title": title, "status": "concept",
        })

    @verb(role="effect")
    def create_chapter(self, novel_id: str, number: int,
                        title: str, body: str = "") -> ToolResult:
        """Record a Chapter graph node + CHAPTER_OF the parent Novel (effect).

        Inputs: novel_id, number (1-indexed), title, body (optional draft body).
        Returns: ``{chapter_id, novel_id, number, title, status}``.
        chain_next: ``novel.chapter_report`` to aggregate state.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        cid = self.ctx.record("Chapter", {
            "novel": novel_id, "number": number, "title": title,
            "status": "outlined", "body": body,
        })
        self.ctx.link(cid, novel_id, "CHAPTER_OF")
        self.ctx.link(cid, self.ctx.intent_id, "SERVES")
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
        chapters = [c for c in self.ctx.find("Chapter")
                    if c.get("novel") == novel_id]
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
            [c for c in self.ctx.find("Chapter")
             if c.get("novel") == novel_id],
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

    # NOTE: `check_quad_completeness` (row 3) DEFERRED to Slice 2.
    # The decidable distinction between row 3 (quad completeness) and
    # row 6 (crucial-element placement) requires ontology lookup to know
    # which Elements sit on the same Dramatica quad. Without it, the
    # broken_work_quad_completeness and broken_work_crucial_element_placement
    # fixtures both trip the same `ce_id != mc.problem_id` shape signal
    # — Round 1 sc-analyze (commit 21aff0e) flagged this honestly as a
    # false-positive risk. Per Rec 2's "each broken fixture fails EXACTLY
    # its named check" contract: ship only verbs that hold the contract.
    # Slice 2 reconciles fixture-ids ↔ vendored ontology then implements
    # all 13 checks with the full element-graph traversal.

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
        chapters = [c for c in self.ctx.find("Chapter")
                    if c.get("novel") == novel_id]
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
            [c for c in self.ctx.find("Chapter")
             if c.get("novel") == novel_id],
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
        chapters = [c for c in self.ctx.find("Chapter")
                    if c.get("novel") == novel_id]
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
