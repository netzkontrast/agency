---
spec_id: "104"
slug: novel-prose-cluster
status: draft
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["102", "103", "101"]
affects:
  - agency/capabilities/novel/clusters/prose.py
  - agency/capabilities/novel/drivers.py        # TextDriver extensions
  - agency/capabilities/novel/ontology.py       # prose artefact schemas
  - tests/test_novel_prose.py
domain: novel / prose / editorial
wave: 8
parent_spec: "101"
mvp-source:
  - "Plan/_research/novel-mvp-source/references/parity-table.md (editorial-stage skills)"
  - "Plan/_research/novel-mvp-source/prior-specs/021-prompt-builder.md (prose-generation prompts)"
  - "Plan/_research/novel-mvp-source/legacy-skills/dramatica-theory/references/07-storyencoding.md (encoding to scene-level prose)"
---

# Spec 104 — Novel Prose Cluster

## Why

The TextDriver showcase for novels: ~12 verbs + 3 editorial-stage gate
verbs. Per the imported **Novel-Craft Parity Table**, the editorial pipeline
follows the canonical 4-stage workflow (developmental → line → copy →
proof) + Susan-Dennard "layered polish" + a generated-prose path through
the `llm` driver (Spec 092 G3).

Music's lyrics cluster (095) gave us the pattern: decidable text analysis
verbs (readability, voice consistency, POV check, dialogue tagging, etc.)
+ computed gates inside a writing workflow. 104 ports that pattern to
novels with editorial-stage clarity.

## Done When

- [ ] **12 user-facing verbs ship** (prose analysis + editorial passes;
      see manifest).
- [ ] **3 composite gate verbs ship** — `developmental_gate`, `line_gate`,
      `copy_gate` — each computes its editorial-stage predicates.
- [ ] **TextDriver extended** with prose-analysis methods (voice
      signature, POV consistency, dialogue ratio, filter-word scan).
- [ ] **Walkable skills ship** (per parity table mapping):
      `chapter-drafting`, `scene-revision`, `developmental-editor`,
      `line-editor`, `voice-consistency-checker`, `narrator-voice-
      specialist` (proper-noun curator), `polish-pass`,
      `prose-generation-prompt-engineer`.
- [ ] **`tests/test_novel_prose.py` Green** (~14 tests).
- [ ] **`TODO.md` updated** with 104 row.

## Verb manifest

| # | Verb | Role | Driver | Music analog |
|---|---|---|---|---|
| 1 | `chapter_report` | act | TextDriver | `lyric_report` |
| 2 | `count_words` | transform | (driver-free) | `count_syllables` |
| 3 | `analyze_readability` | transform | TextDriver | `analyze_readability` |
| 4 | `check_voice_consistency` | transform | TextDriver | `voice_checker` |
| 5 | `check_pov_consistency` | transform | TextDriver | (new) |
| 6 | `check_dialogue_attribution` | transform | TextDriver | (new) |
| 7 | `check_filter_words` | transform | TextDriver | (new — show-don't-tell discipline) |
| 8 | `check_show_dont_tell` | transform | TextDriver | (new — adjective-heavy passage scan) |
| 9 | `check_continuity` | transform | TextDriver | (new — character-name + timeline scan) |
| 10 | `scan_proper_nouns` | transform | TextDriver | `scan_artist_names` |
| 11 | `check_content_warnings` | transform | TextDriver | `check_explicit_content` (split A) |
| 12 | `check_sensitivity` | transform | TextDriver | `check_explicit_content` (split B) |

**Internal composite gate verbs**:

| # | Verb | Composes | Walks |
|---|---|---|---|
| G1 | `developmental_gate` | character-arc-coverage + throughline-coverage + plot-pacing + gate.check | `chapter-drafting` phase 5 |
| G2 | `line_gate` | filter-word density + show/tell ratio + voice consistency + dialogue attribution + gate.check | `scene-revision` phase 3 |
| G3 | `copy_gate` | spell-check + grammar pass + style-sheet adherence + gate.check | manuscript-pass (107) gate |

**Total: 12 user + 3 gate = 15 registered verbs.**

## Design

### TextDriver method delta

```python
class TextDriver(Boundary):
    # reused from music (095)
    def readability(self, text: str) -> dict: ...

    # new methods (104) — pure-stdlib + pattern tables
    def voice_signature(self, text: str) -> dict:
        """Per-passage signature: avg sentence length, word-freq histogram,
        comma-density, dialogue-ratio — for cross-chapter drift detection."""
    def pov_violations(self, text: str, pov: str) -> list[dict]: ...
    def dialogue_attribution(self, text: str) -> dict: ...
        # ratio of {said, asked, replied, …} vs verb-heavy tags
    def filter_words(self, text: str) -> list[dict]: ...
        # known filter words: saw, heard, felt, noticed, watched, …
    def show_dont_tell(self, text: str) -> dict: ...
        # adjective-density vs concrete-noun ratio
    def continuity_facts(self, text: str) -> dict: ...
        # extracts character names + timestamps + locations for cross-chapter linting
    def content_warning_scan(self, text: str) -> dict: ...
    def sensitivity_scan(self, text: str, lens: str = "default") -> dict: ...
```

All methods stdlib-only; pattern tables (filter words, sensitivity lens
phrases) ship as YAML under `data/reference/prose/` (loaded once,
memoized).

### Walkable skill: `chapter-drafting` (5 phases)

```python
CHAPTER_DRAFTING_SKILL = {
    "name": "chapter-drafting",
    "kind": "workflow",
    "phases": [
        {"index": 1, "name": "beat-sheet",
         "produces": ["beats_committed"]},
        {"index": 2, "name": "scene-draft",
         "produces": ["draft_body"]},
        {"index": 3, "name": "continuity-check",
         "produces": ["continuity_facts_extracted"],
         "gate": "computed", "gate_verb": "novel.check_continuity"},
        {"index": 4, "name": "readability-check",
         "produces": ["readability_within_target"],
         "gate": "computed", "gate_verb": "novel.developmental_gate"},
        {"index": 5, "name": "confirmation",
         "produces": ["draft_locked"], "gate": "hard"},
    ],
}
```

**Primary actor**: agent (drafts); human-curator signs off at phase 5.

### Walkable skill: `scene-revision` (4 phases)

```python
SCENE_REVISION_SKILL = {
    "name": "scene-revision",
    "kind": "workflow",
    "phases": [
        {"index": 1, "name": "issue-survey",
         "produces": ["issues_listed"]},
        {"index": 2, "name": "revise",
         "produces": ["revised_body"]},
        {"index": 3, "name": "line-check",
         "produces": ["filter_word_density", "show_tell_ratio"],
         "gate": "computed", "gate_verb": "novel.line_gate"},
        {"index": 4, "name": "confirmation",
         "produces": ["scene_locked"], "gate": "hard"},
    ],
}
```

### Prose generation (Path B opt-in)

```python
@verb(role="act")
def chapter_draft_assisted(self, novel: str, chapter: int,
                           outline_beats: str = "") -> ToolResult:
    """Draft a chapter via the `llm` driver if usable. Path A (default):
    returns a structured scaffold the agent fills inline. Path B: LLM-
    drafted prose marked with `generated_by` metadata."""
    state = self.ctx.get_driver("music_state")
    novel_data = state.find_novel(novel)[0]
    # Path A scaffold (always):
    scaffold = (f"# Chapter {chapter}\n\n"
                f"Beats:\n{outline_beats or '(none provided)'}\n\n"
                f"<!-- agent: draft scene-by-scene here -->\n")
    body, generated_by = scaffold, "agent"
    try:
        llm = self.ctx.get_driver("llm")
        decision = llm.decide(
            prompt=(f"Draft chapter {chapter} of {novel_data['title']}. "
                    f"Beats:\n{outline_beats}\n\n"
                    f"Voice: {novel_data.get('voice_notes', '')}.\n"
                    f"Genre: {novel_data['genre']}."),
            options=["free-form"])
        body, generated_by = decision.get("choice", body), "llm"
    except (DriverMissing, RuntimeError, KeyError, ValueError,
            TimeoutError, OSError):
        pass
    return ToolResult.success(data={"body": body, "artefact": {
        "kind": "draft", "novel": novel, "chapter": chapter,
        "body": body, "generated_by": generated_by}})
```

Path A is the default-install behaviour per Spec 101 deployment plan.

## Test plan

```python
# tests/test_novel_prose.py — ~14 tests
def test_prose_cluster_discovers_all_15_verbs(): ...
def test_chapter_report_records_artefact_with_produces_edge(): ...
def test_count_words_is_deterministic_and_driver_free(): ...
def test_check_voice_consistency_flags_drift_against_prior_chapter(): ...
def test_check_pov_consistency_flags_third_person_violations(): ...
def test_check_dialogue_attribution_flags_verb_heavy_tags(): ...
def test_check_filter_words_flags_known_filters(): ...
def test_check_show_dont_tell_flags_adjective_heavy_passages(): ...
def test_check_continuity_extracts_character_names_and_timeline(): ...
def test_check_content_warnings_classifies_known_phrase(): ...
def test_check_sensitivity_flags_lens_phrases(): ...
def test_developmental_gate_blocks_when_arc_coverage_low(): ...
def test_line_gate_blocks_when_filter_word_density_high(): ...
def test_chapter_draft_assisted_falls_back_to_scaffold_without_llm(): ...
def test_chapter_drafting_skill_walks_through_developmental_gate(): ...
def test_scene_revision_skill_pauses_on_hard_confirm_gate(): ...
```

## Complex-novel extensions (iteration 2)

### Per-POV voice signatures (ADR-6)

`check_voice_consistency` is parameterized by POV character. The
`voice_signature` is computed per `(novel, pov_character)` so a
5-POV-character novel has 5 independent signatures. Drift is detected
within a POV across chapters, NOT across POVs (different POV characters
SHOULD sound different).

```python
@verb(role="transform")
def check_voice_consistency(self, novel: str, chapter: int,
                            pov_character: str = "") -> ToolResult:
    """Per-POV voice drift detection. If pov_character is omitted, infers
    from Scene.pov_character. Compares against the running signature for
    the SAME pov across prior chapters."""
```

### Voice-signature versioning (character arc evolution — ADR-6)

A character's voice changes over their arc (a darker tone after losing a
loved one; more clipped speech after combat trauma). `voice_signature` is
versioned per `ArcPhase`:

```python
# Character node carries: voice_signature_by_phase: {phase_id: signature}
# 104's check_voice_consistency uses the CURRENT phase's signature, not
# the chapter-1 signature, when evaluating later chapters.
```

The arc-evolution model is opt-in: novels without `Arc` nodes use the
single-signature path.

### Multilingual canon preservation (ADR-1 — load-bearing)

The capability **MUST NOT translate canon prose into any other language**.

- No `translate_prose` verb exists on this cluster.
- The `chapter_draft_assisted` verb's Path B (LLM-drafted prose) returns
  prose IN THE CHAPTER'S `canon_language`; if the LLM responds in a
  different language, the verb returns `ToolResult.failure(
  CANON_LANGUAGE_VIOLATION, ...)` and discards the draft.
- A `extract_language` verb (transform) detects prose language for any
  block; chapter's `canon_language` field is the source of truth.

Test asserts: a German `canon_language: "de"` chapter that is
LLM-drafted in English causes a typed failure.

### POV-balance gate (for 108)

The cluster ships `pov_balance_check` (transform — reads Scene.
pov_character distribution across the novel). 108's `pov_balance_gate`
calls it. Per-novel threshold: default "no POV > 40% unless
`narrative_type=first-person-protagonist`".

## Writer's workflow extensions (iteration 3)

Real writers don't draft sequentially — they jump around, leave TODOs,
stub chapters, revise out-of-order. The design supports this through
**inline-TODO extraction**, **stub-chapter** flagging, and **skip-write**:

### Inline-TODO extraction

Drafts may contain `<!-- TODO: <text> -->` HTML-style comments OR
`[[TODO: <text>]]` brackets. A new transform verb extracts them:

```python
@verb(role="transform")
def extract_inline_todos(self, novel: str = "",
                        chapter: int = 0) -> ToolResult:
    """Scan draft prose for inline TODOs; return structured findings
    that 106's add_edit_note can record as EditNotes per chapter."""
```

The `chapter-drafting` skill phase 1 (beat-sheet) accepts beats with
embedded TODOs; the draft body preserves them as scaffolding. Phase 5
(confirmation) reports unresolved TODO count; the hard gate WARNS
(but does not block) if TODOs remain — the writer signs off
intentionally.

### Stub-chapter flagging

A chapter can be marked `status: stub` (102 enum extended). A stub has
only the beat-sheet + placeholder body. Verbs that consume drafted prose
(continuity-check, voice-consistency, line-gate) skip stub chapters with
a typed `{status: "n/a", reason: "chapter is stub"}` rather than
failing. The `pre-draft` gate (108) WARNs (not BLOCKs) when stubs exist
beyond chapter 5; the writer confirms intentional stubs at the hard
gate.

### Skip-write support

`Chapter.write_order` (102 iter-3 addition) tracks the order chapters
WERE written (independent of `narrative_order` for reader-facing
sequence). `extract_inline_todos` + `chapter-drafting` skill walk
respect `write_order`: a chapter 30 drafted before chapter 10 emits a
`forward-reference` flag if it mentions events that haven't been written
yet, but doesn't block.

### Genre-specific verbs

Mystery / thriller / romance / fantasy / sci-fi share the base prose
verbs but each genre has discipline-specific patterns. Implemented as
optional verb extensions (opt-in via `Novel.genres`):

| Genre | Verb | Discipline |
|---|---|---|
| mystery | `track_clues` (transform) | Per-clue placement + reveal-distance; flags clues planted too late or never used |
| mystery | `check_red_herring_distribution` (transform) | Red-herring density should be 1.5x clue density per genre-convention |
| thriller | `analyze_pacing` (transform) | Beat-density per chapter; flags slow-pace chapters in act 2/3 |
| thriller | `check_tension_curve` (transform) | Tension should rise; flags tension drops outside breather scenes |
| romance | `track_relationship_beats` (transform) | Meet-cute / first-conflict / first-kiss / dark-moment / declaration / HEA — reports beat coverage |
| romance | `check_tropes_used` (transform) | Match against declared `Novel.romance_tropes: list[str]` |
| fantasy | `check_magic_consistency` (transform) | Reads `MagicSystem` node; flags scenes where magic violates declared rules (e.g. hard-magic system used unpredictably) |
| sci-fi | `check_scientific_accuracy` (transform) | Delegates to 105 research with `scientific` domain; flags claims without supporting `ResearchClaim` |
| literary | `check_thematic_density` (transform) | Identifies recurring motifs; flags chapters where the central theme is absent |

These verbs are opt-in (CALLED ONLY when the genre matches); they emit
WARNINGS not gates. Implementations may ship with empty stubs (`{status:
"n/a", reason: "not yet implemented"}`) in the initial wave.

## Open questions

1. **Generated-prose attribution**: every LLM-drafted artefact carries a
   `generated_by` field. Test asserts this can NOT be silently flipped.
2. **Voice signature drift threshold**: `check_voice_consistency` default
   sensitivity is 2-sigma. Per-novel override via novel frontmatter
   `voice_drift_sigma`.
3. **Style sheets (copy stage)**: copy-stage style adherence reads a
   per-novel `style-sheet.yaml`. Default ships under `data/reference/
   prose/default-style-sheet.yaml`. Per-novel override in a followup.

## Followup

(Populated when the PR ships.)
