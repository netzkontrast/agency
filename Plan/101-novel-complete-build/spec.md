---
spec_id: "101"
slug: novel-complete-build
status: draft
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["001", "002", "020", "044", "047", "054", "076", "079", "080", "081", "092", "093"]
affects:
  - agency/capabilities/novel/
  - tests/test_novel_*.py
source-material:
  - "Dramatica theory of story (4 throughlines / 4 classes / 8 archetypes / Class→Type→Variation→Element pyramid / 65 dynamic pairs / 35 quads)"
  - "netzkontrast/the-agency-system: `templates/novel/` (11 templates), Plan/{010,011,013,014,015,021}-novel-* (7 prior specs), `dramatica-decidability.md` (15-row matrix), `parity-table.md` (30-row music↔novel skill map)"
  - "NCP v1.3.0 schema (463 appreciation enums + 144 narrative_function enums); `ontology.json` (304 entries across 11 kinds); `scenarios.json` (12 scenarios)"
  - "Spec 093 (music) as the proven clustered-Capability template"
mvp-source-imported-at: "Plan/_research/novel-mvp-source/ (templates + references + prior-specs)"
domain: novel / cluster-integration / capability
wave: 8
research_first: false
---

# Spec 101 — Novel Complete Build (master)

> **Master spec** — coordinates the seven child specs (102–108), one per
> cluster. Mirrors Spec 093 (music) shape exactly. **Grounded in the rich
> source material from `netzkontrast/the-agency-system`** (11 templates +
> 7 prior novel specs + the Dramatica Decidability Matrix + the Novel-Craft
> Parity Table), imported under `Plan/_research/novel-mvp-source/`.

## First-Principles Minimum (iter-12 — critical-thinking-driven)

The 5-verb path from idea to manuscript is the **minimum viable
novel** (see `MINIMAL-VIABLE-NOVEL.md`). A simple-novel writer uses:

1. `conceptualize` (102)
2. `create_novel` (102)
3. `create_chapter` (102)
4. `chapter_report` (104)
5. `render_manuscript` (107)

Plus the walkable skill `novel-concept` (102). That's it. Storyform,
multi-POV, worldbuilding, audiobook prep, prompt engineering, research
entities — all opt-in. Complex novels turn features ON; simple novels
ship in 5 verbs.

## Invariants That Cannot Be Broken (iter-12 — inversion pass)

Seven hard-NEVERs whose violation = design failure:

1. **Drop-in bar**: zero edits to `agency/engine.py`,
   `agency/capability.py`, `agency/registry.py`, `agency/ontology.py`,
   `agency/toolresult.py`. Enforced by `scripts/check-drop-in-bar`.
2. **No canon translation** (ADR-1): canon prose preserved in source
   language; no `translate_prose` verb exists.
3. **No silent generated_by flip**: `generated_by="llm"` can become
   `"mixed"` (via `mark_human_edited`) but NEVER becomes `"human"`.
4. **Iter-2+ features are opt-in only**: simple novels work with the
   base schema; complex features activate via novel frontmatter
   (`outline_hierarchy`, `pov_count`, `subplot_count`, `multilingual`,
   `genres`).
5. **Driver protocol cap = 6**: `StateDriver` / `TextDriver` /
   `AudioDriver` / `DBDriver` / `CloudDriver` / `FormatDriver`. Plus
   the shared `llm` substrate driver. A 7th cluster-specific protocol
   = design failure.
6. **Every hard gate has an `elicit` escape valve**: no walkable skill
   can block the user without offering a human-confirm path.
7. **No direct cluster-to-cluster imports**: cross-cluster use goes
   through `ctx.call(cap, verb, **kw)` (returns unwrapped dict per
   `capability.py:138`).

## Assumption Manifest (iter-12 — assumptions pass)

**Load-bearing** (failure = design re-architecture):
- Dramatica as story-design framework (103) — *mitigation: 103 is
  optional for simple novels*
- Graph-canonical, file-derived (CLAUDE.md rule 2) — *mitigation:
  iter-6 import/export bridges Scrivener/Word*
- LLM availability for Path B (092 G3) — *mitigation: Path A
  rule-based default*
- Markdown as primary prose format — *mitigation: import discipline
  handles rich-text sources*

**Incidental** (can swap without re-arch):
- pytest as test framework
- SQLite as graph store
- YAML vs JSON for config

## Why this isn't a kitchen sink (iter-12 — steelman pass)

**Concern**: "30+ verbs in 104 alone, 11 iterations of additions,
multi-volume + multi-POV + multi-language + multi-author + audiobook
+ marketing + prompt engineering — kitchen sink, not focused product."

**Response**:
- **Opt-in discipline**: 5 verbs ship simple novels. Everything beyond
  activates by frontmatter declaration.
- **Walkable skills as discoverability**: writers don't read the verb
  list; they walk a skill and the engine surfaces relevant verbs.
- **`agency novel help` (Spec 079 CLI mirror)**: lists every verb
  organized by cluster + walkable skill discovery via `intent
  suggests`.
- **The 30 verbs in 104 are addressable surface, not required surface**:
  simple novels use 1 (chapter_report); complex multi-POV uses 8;
  research-heavy + LLM-assisted uses all 30.
- **Per-cluster extras** (`[novel-format]`, `[novel-db]`,
  `[novel-cloud]`, `[novel-llm]`): users install only what they need.

The kitchen-sink concern is real for hand-rolled APIs. The agency
substrate's discoverability primitives + walkable-skill + verb-mirror
ergonomics make breadth tolerable.

## Downstream Predictions (iter-12 — second-order pass)

After 101 → Shipped, the consequence chain:

1. Writers using it generate large provenance graphs → researchers
   study creative process via the data
2. Publishers integrate with catalogue + manuscript clusters for
   streamlined acquisition
3. Some writers reject over privacy concerns → need clear data-
   ownership story
4. Dramatica community contributes ontology improvements → versioning
   discipline (iter-9 schema migration covers this)
5. Forks for non-Dramatica frameworks emerge → pattern is reusable
6. The 10-builder prompt family gets copied by other domain caps
   (music, screenplay, journalism) → `agency.prompt-engineering`
   substrate capability may emerge
7. AI-use disclosure (ADR-7) becomes publishing-industry table-stakes
8. Translation services build on the multilingual layer

## Design Alternatives Considered (iter-12 — tradeoffs pass)

| Option | Drop-in | Accessibility | Decidability | Coverage | Cost | Wave-1 ship |
|---|---|---|---|---|---|---|
| **Selected: 7 clusters, opt-in iter-2+** | ✓ | medium | high | wide | high | ~3 weeks |
| Slim (102+104+108 only) | ✓ | **high** | medium | narrow | low | **~1 week** |
| Fat (all features mandatory) | ✓ | low | high | wide | very high | ~6 weeks |
| Plugin-per-cluster | medium | medium | high | wide | very high | ~6 weeks |
| Embed in music plugin | ✓ | medium | high | wide | medium | ~2 weeks |
| External Scrivener API | n/a | high | low | narrow | low | ~3 days |

**Selected**: best balance of coverage + decidability + drop-in
compliance. The extra 2 weeks over the slim path buy complex-novel
coverage that distinguishes from a Scrivener clone.

## Why

Music proved that a hard creative-production domain fits the clustered
Capability contract (Spec 093). Novels are the next proof: a structurally-
anchored creative pipeline (concept → research → storyform → outline →
draft → revise → beta → query → publish) that gains everything music
gained (typed verbs, walkable gates, provenance audit) PLUS a domain-
specific **decidable structural backbone**.

**The design holds a very complex novel** (iteration 2 — see
`COMPLEXITY-AUDIT.md`): multi-volume series (Series → Volume → Part →
Book → Chapter → Scene, 6-level hierarchy opt-in); multi-POV (5+ POV
characters with per-POV voice signatures + POV-balance gate); nested
storyforms (each subplot gets its own 4-throughline Dramatica argument);
non-linear narrative (narrative_order + story_time on every node);
worldbuilding depth (Culture/Religion/Language/MagicSystem/Politics/
Economy/Geography/Bestiary + WorldAxiom sub-graph); large cast
(Faction/House/Family hierarchy); character voice evolution (versioned
per arc-position); multilingual canon preservation (German canon NOT
translated per ADR-1); character arcs across volumes; series-level
coherence; genre-blending; provenance at scale.

The iteration-2 additions are **back-loaded**: simple novels work with
the base schema; complex-novel features activate when the user opts in
via novel frontmatter (`outline_hierarchy`, `multilingual`, `pov_count`,
`subplot_count`).

**The decidable backbone is Dramatica + NCP v1.3.0**. Per the imported
**Dramatica Decidability Matrix** (`Plan/_research/novel-mvp-source/
references/dramatica-decidability.md` — embedded dossier, source research
agent `a78bd055cd15ef572`):

- **11 decidable checks** (graph lookups, set-membership tests, permutation
  checks): dynamic-pair reciprocity · KTAD coverage · quad completeness ·
  slot-fill completeness · throughline partition · crucial-element
  placement · resolve↔outcome↔judgment consistency · approach↔concern ·
  mental-sex↔problem-solving · signpost permutation · storybeat→moment
  refs.
- **2 hybrid checks** (appreciation enum, narrative-function enum — table
  lookup).
- **2 judgement checks** (Q1–Q5 Scene-Level Bridge, encoding suggestions
  — surface to skills, NOT tools).

These 11 decidable checks become the storyform cluster's load-bearing
verb set (Spec 103). **Tools assert structure; skills assert meaning.**

User directive (2026-06-07): *"Create detailed Plans for a novel writing
capability similar to the music capability — use the Same Process."*

## What "complete" means here

Behavioural parity with the *intent* of a Dramatica + NCP grounded novel
production pipeline:

- Every step is a walkable skill with computed gates + terminal `elicit`.
- Every side-effect routes through a Driver (StateDriver/TextDriver/
  DBDriver/CloudDriver/FormatDriver). NO direct shell-outs.
- Every storyform choice is a typed graph node SERVES the intent — so a
  release audit traces every design choice + revision.
- Every coherence check is a verb returning the **lowest-token-cost
  report shape** (per the decidability dossier): drop PASS-check items
  arrays, use ontology ids not labels, cap violations at ~120 chars.
- The NCP `.ncp.json` document is the **structural source of truth**;
  storyform changes serialize through `ncp-author` patterns.

## Audit baseline (imported source)

`Plan/_research/novel-mvp-source/` carries the imported MVP source. The
children read from it rather than re-derive:

| Imported asset | Used by | Lines |
|---|---|---|
| `templates/novel/{README,work,premise,cast,dramatica,outline,chapter,scene,character,world}.md` + `ncp.json` (11 templates) | 102 (declared on `OntologyExtension.templates`; ported VERBATIM under `agency/capabilities/novel/templates/`) | 11 files |
| `references/dramatica-decidability.md` (15-row matrix) | 103 (defines the 11 decidable + 2 hybrid verbs verbatim) | 1 |
| `references/parity-table.md` (30-row music↔novel role map + 6 novel-specific additions + collapse/drop decisions) | 102–108 (defines the spirit-isomorphic skill set — 28 carried + 4 ported = 32 SKILL.md) | 1 |
| `prior-specs/010-on-disk-layout.md` | 102 (informs the StateDriver method delta) | 1 |
| `prior-specs/011-handlers-core.md` | 102 (informs the lifecycle verb set) | 1 |
| `prior-specs/013-handlers-structural.md` | 103 (informs the storyform verb set + report shape) | 1 |
| `prior-specs/014-gates-and-revision.md` | 108 (informs the gate predicates) | 1 |
| `prior-specs/015-skills-catalogue.md` | 102–107 (informs the per-cluster walkable skill set) | 1 |
| `prior-specs/021-prompt-builder.md` | 104 (informs the prose-generation-prompt-engineer family) | 1 |

> The imported source is **read-only research**, not source-of-truth. Each
> child spec re-anchors against agency idioms (verbs / Driver / ontology
> / walkable skills). The prior specs were authored for a different MCP
> server; agency idioms differ from theirs (e.g. they use `agency_mcp.
> handlers.novel.coherence` modules — agency uses `clusters/storyform.py`
> verbs).

## Spec layout (the seven children)

| Spec | Cluster | Driver(s) | Music analog | Verb count target |
|---|---|---|---|---|
| **102** | lifecycle | StateDriver | music lifecycle (094) | ~14 user + 0 gate |
| **103** | storyform | TextDriver (structured) | (no music analog — net new) | ~13 user (11 decidable checks + 2 hybrid) + 1 gate |
| **104** | prose | TextDriver | music lyrics (095) | ~12 base + 10 builders + 5 engineer + 3 inject (iter-11) user + 3 gate (developmental/line/copy editorial passes + token-budget gate) |
| **105** | research | delegates to `agency.research` + Research-Entity ontology (iter-10) | music research (099) | ~8 base + 16 iter-10 user + 1 gate (verbatim 099 pattern + 4-stage research-to-prompt-snippet pipeline) |
| **106** | catalogue | DBDriver+StateDriver | music catalogue (097) | ~10 user + 1 gate (beta-feedback + version-log; manuscript/series coherence split) |
| **107** | manuscript | FormatDriver (new) + StateDriver+CloudDriver | music audio + promo (096+098) | ~10 user + 1 gate (4-stage editorial: developmental→line→copy→proof; renders manuscript-format/epub/PDF/docx + query letter + synopsis + blurb) |
| **108** | gates | gate.check + elicit | music gates (100) | ~6 user + 4 gate (pre-draft/beta-ready/query-ready/publish-ready) + **4 iter-2 gates** (pov_balance / subplot_resolution / timeline_continuity / world_canon) |
| | | **Totals (base + iter-2)** | | **~73 user + 11 gate base + ~5 iter-2 user + 4 iter-2 gate = 93 registered** |

**Iteration-2 verb additions** (opt-in for complex novels):
- 102: `create_volume`, `create_part`, `create_book` + 8 world-subschema effect verbs
- 103: `list_storyforms` (transform) — multi-Storyform discovery
- 104: `extract_language`, `pov_balance_check` (transforms)
- 106: `arc_coverage_report`, `cast_hierarchy_report`, `worldbuilding_coverage` (transforms)
- 107: `render_series_boxset`, `render_per_volume_manuscript` (effects)
- 108: `pov_balance_gate`, `subplot_resolution_gate`, `timeline_continuity_gate`, `world_canon_gate`

All iteration-2 verbs degrade gracefully on simple novels (return
`{status: "n/a", reason: "novel lacks <field>"}` per CLAUDE.md rule 8 —
no surprise failures).

Per the parity table, the cluster surface maps to **28 spirit-isomorphic
skills + 4 ported storyform/theory skills = 32 walkable SKILL.md** entries
(Spec 015's count). Each cluster owns a subset; 102 + 103 own the
lifecycle/storyform skill set, 104 owns the editorial-stage skills,
107 owns the publication-prep skills.

## Drivers (5 reused + 1 new)

| Driver | Reuse from music? | What it owns for novels |
|---|---|---|
| StateDriver | ✓ (extends 094 method surface) | Novel/Series/Chapter/Scene file tree, NCP serialize/deserialize, state cache |
| TextDriver | ✓ (extends 095 method surface) | Prose analysis (readability, voice, POV); Dramatica decidable checks (ontology + NCP lookups) |
| DBDriver | ✓ (reuse 097) | Beta-feedback rows, version-log rows, edit-note tracking |
| CloudDriver | ✓ (reuse 097/098) | Manuscript distribution (R2/S3 upload for beta delivery) |
| **FormatDriver** | **NEW (107)** | Pandoc + LaTeX + wkhtmltopdf + calibre shell-outs for manuscript-format/epub/PDF/docx |
| AudioDriver | ✗ (not used) | Novels are text — no audio surface |

FormatDriver mirrors AudioDriver's shape (Spec-002 Option B typed-named
methods): `pandoc(args) -> str`, `latex_compile(tex) -> bytes`,
`epub_pack(html, manifest) -> bytes`, `wkhtmltopdf(html) -> bytes`,
`docx_render(html, style) -> bytes`. Fake produces deterministic stub
bytes; CI runs zero pandoc/LaTeX/wkhtmltopdf binaries.

## Ontology (consolidated — declared in 102, extended additively by children)

```python
# Lifecycle (102):
Novel       (status, slug, author, genre, target_length, premise, created_at)
Series      (slug, author, novel_count)
Chapter     (slug, novel, number, word_count, status, body)
Scene       (slug, chapter, pov_character, location, time_of_day, status)

# Dramatica/Storyform sub-graph (103) — grounded in NCP v1.3.0 schema:
Storyform        (slug, novel, status, completeness, resolve, growth,
                  approach, mental_sex)
Throughline      (slug, storyform, kind)
Class            (throughline, name)
Type             (throughline, signpost_order, type_id)
Variation        (type, variation_id)
Element          (variation, element_id, ktad_position)
Character        (slug, novel, archetype, role_in_OS, voice_signature,
                  big_five, enneagram)
Beat             (chapter, beat_number, type, summary)
Storybeat        (storyform, id)            # NCP storybeats[]
Moment           (storybeat, id)            # NCP moments[]

# Prose + revision (104):
Draft            (chapter, version, body, created_at)
RevisionNote     (draft, note, severity, lens)   # lens: developmental/line/copy/proof

# Research (105 — reuses 099 verbatim):
ResearchClaim    (text, source_uri, domain, confidence, verified, captured_at)
VerificationRecord (claim, verified_by, verified_at, verdict)

# Catalogue + Beta (106):
BetaReader       (slug, name, email, novels_read)
BetaFeedback     (beta_reader, novel, chapter, text, sentiment)
EditNote         (novel, chapter, text, status)
ManuscriptVersion (novel, version, created_at, body_hash, change_log)

# Manuscript outputs (107):
ManuscriptArtefact (novel, kind, body_uri)  # kind: manuscript/epub/pdf/docx/query/synopsis/blurb
```

Closed enums (full set declared in 102):
- `(Novel, status)`: `concept / outlining / drafting / revising / beta / querying / published`
- `(Chapter, status)`: `outlined / drafted / revised / final`
- `(Scene, status)`: `outlined / drafted / revised`
- `(Throughline, kind)`: `OS / MC / IC / RS`
- `(Class, name)`: `Universe / Mind / Physics / Psychology`
- `(Character, archetype)`: `Protagonist / Antagonist / Reason / Emotion / Sidekick / Skeptic / Guardian / Contagonist / supporting / non-archetypal`
- `(RevisionNote, lens)`: `developmental / line / copy / proof / polish`
- `(BetaFeedback, sentiment)`: `praise / concern / question / suggestion`
- `(ResearchClaim, verified)`: `pending / human-confirmed / rejected`
- `(ManuscriptArtefact, kind)`: `manuscript / epub / pdf / docx / query-letter / synopsis / blurb / back-cover`

Edges (declared in 102's OntologyExtension):
- Reused from music: `SERVES`, `PRODUCES`, `RELATES_TO`
- Novel-specific: `OUTLINES` (Beat → Scene), `EMBODIES` (Character →
  Throughline-kind via archetype), `REVISES` (Draft → Draft),
  `ENCODES` (Scene → Storybeat), `MANIFESTS` (Moment → Element)

## Walkable skills

Per the parity table (28 spirit-isomorphic + 4 ported = 32):

| Skill | Cluster | Source role |
|---|---|---|
| `novel-concept` | 102 | `album-conceptualizer` |
| `novel-ideas` / `subgenre-creator` | 102 | `album-ideas` / `genre-creator` |
| `import-chapter` / `import-manuscript` / `import-cover` | 102 | `import-track` / `import-audio` / `import-art` |
| `storyform-architect` | 103 | (ported verbatim from `agency/skills/novel-architect/`) |
| `dramatica-validator` | 103 | (surfaces `novel_coherence_check`) |
| `ncp-author` | 103 | (ported verbatim from `agency/skills/ncp-author/`) |
| `scene-bridge-auditor` | 103 | (Q1–Q5 audit gate) |
| `character-architect` | 103 | (novel-specific addition) |
| `world-bible-architect` | 102/103 | (novel-specific addition) |
| `prose-drafter` (chapter-writer) | 104 | `lyric-writer` |
| `developmental-editor` (prose-reviewer) | 104 | `lyric-reviewer` |
| `line-editor` (prose-refiner) | 104 | `lyric-refiner` |
| `revision-engineer` (prose-revision-engineer) | 104 | `mix-engineer` |
| `polish-pass` | 104 | `polish-audio`/`polish-album` (collapsed) |
| `voice-consistency-checker` | 104 | `voice-checker` |
| `narrator-voice-specialist` (proper-noun-curator) | 104 | `pronunciation-specialist` |
| `plagiarism-checker` | 104 | (verbatim carry-over) |
| `content-warning-checker` | 104 | `explicit-checker` (split) |
| `sensitivity-reader` | 104 | `explicit-checker` (split) |
| `prose-generation-prompt-engineer` | 104 | `suno-engineer` |
| `researchers-*` (10 domains) | 105 | (verbatim carry-over × 10) |
| `document-hunter` | 105 | (verbatim carry-over) |
| `verify-sources` | 105 | (verbatim carry-over) |
| `alpha-reader` / `critique-partner` / `beta-reader` | 106 | (no music source; baseline novel practice) |
| `manuscript-coherence-check` | 106 | `album-coherence-check` (split) |
| `series-coherence-check` | 106 | `album-coherence-check` (split) |
| `validate-manuscript` (validate-work) | 106 | `validate-album` |
| `copy-editor` | 107 | `mastering-engineer` |
| `proofreader` | 107 | `mastering-engineer (final polish)` |
| `cover-art-director` | 107 | `album-art-director` |
| `blurb-writer` (book-promo-writer) | 107 | `promo-writer` |
| `marketing-copy-director` (book-promo-director) | 107 | `promo-director` |
| `publication-director` | 107 | `release-director` |
| `revert-to-clean-draft` | 107 | `reset-mastering` |
| `manuscript-dashboard` (work-dashboard) | 107 | `album-dashboard` |
| `pre-drafting-gate` (pre-drafting-check) | 108 | `pre-generation-check` |
| Lifecycle/admin: `rename`/`next-step`/`resume`/`session-start`/`health-check`/`configure`/`tutorial`/`about`/`help`/`setup` | 102 | (verbatim carry-over) |

**Dropped** (per parity table justifications): `master-with-reference`,
`sheet-music-publisher`.

## Templates (ported VERBATIM from the-agency-system)

11 templates already exist under `Plan/_research/novel-mvp-source/
templates/`. 102 lands them VERBATIM under `agency/capabilities/novel/
templates/` and registers each on `OntologyExtension.templates`:

| Imported file | agency template name | Renders |
|---|---|---|
| `README.md` | `novel-readme` | Novel workspace README (per-novel root) |
| `work.md` | `work` | Central work meta-information |
| `premise.md` | `premise` | Premise/logline/central question |
| `cast.md` | `cast` | Roster of characters/players + throughlines |
| `character.md` | `character` | Per-character sheet (archetype, big_five, enneagram, ifs_parts) |
| `dramatica.md` | `dramatica` | Storyform sheet (resolve, growth, approach, mental_sex, OS/MC/IC/RS classes) |
| `outline.md` | `outline` | Plot points + signposts + act-level structure |
| `chapter.md` | `chapter` | Chapter scaffold |
| `scene.md` | `scene` | Scene scaffold |
| `world.md` | `world` | World-building details |
| `ncp.json` | `ncp` | NCP v1.3.0 storyform document (storyform / players / scenes / metadata) |

## Done When

- [ ] All seven child specs (102–108) ship Green with their own Done-When
      gates met.
- [ ] `agency/capabilities/novel/` is the live novel cap.
- [ ] **Drop-in bar holds**: ZERO edits to `agency/engine.py`,
      `agency/registry.py`, `agency/ontology.py`, `agency/capability.py`,
      `agency/toolresult.py`. Enforced by `scripts/check-drop-in-bar`
      (re-uses the music-093 CI gate).
- [ ] **Decidability matrix shipped intact**: 103 ships ALL 11 decidable
      + 2 hybrid checks as registered verbs. `novel_coherence_check`
      composite returns the low-token report shape (PASS-check items
      dropped; ontology ids; ≤120-char violations).
- [ ] **NCP v1.3.0 round-trip**: 102 can read AND write `ncp.json` such
      that `validate(read(write(x))) == x` for every NCP fixture in
      `tests/fixtures/novel/ncp/`.
- [ ] **Provenance moat lit on a real novel lifecycle**: E2E test in
      108 drives the full pipeline (capture → conceptualize → research →
      storyform-build → outline → draft chapter 1 → revise → beta →
      manuscript-pass) and asserts `eng.memory.provenance(intent_id)`
      returns the full chain.
- [ ] `TODO.md` updated with 101 + each child row.
- [ ] `scripts/check-drift` Green; install regen committed.

## Migration order

```
102 lifecycle ─→ 103 storyform ─┬─→ 104 prose    ─┐
                                ├─→ 105 research ─┤  Wave 2 parallel-safe
                                └─→ 106 catalogue ┘
                                       │
                                       └─→ 107 manuscript
                                              │
                                              └─→ 108 gates (carries E2E test)
```

102 first (foundation: ontology + StateDriver + templates). 103 second
(storyform is the gate the rest of the pipeline reads). 104/105/106
parallel after 102+103. 107 after 104+106. 108 LAST.

## Deployment

```bash
# Default install — lifecycle + storyform + prose + research + gates work
# out of the box (no pandoc, no postgres, no boto3).
pipx install --editable agency

# Per-cluster opt-in:
pipx install agency[novel-format]   # pandoc + wkhtmltopdf + calibre system bins
pipx install agency[novel-db]       # psycopg2-binary (reuses [music-db])
pipx install agency[novel-cloud]    # boto3 (reuses [music-cloud])
pipx install agency[novel-llm]      # routes prose-gen through `llm` driver
pipx install agency[novel]          # all of the above
```

## ADRs (iteration 2 — see `COMPLEXITY-AUDIT.md` for the full table)

Six load-bearing decisions for very complex novels:

| ADR | Decision | Where it lands |
|---|---|---|
| ADR-1 | Canon prose MUST NOT be translated (see edge cases below) | 101 (this section), 104 (translation-refusal verb behaviour), 107 (multilingual epub metadata) |
| ADR-2 | Each subplot gets its own Storyform sub-graph; H1–H12 run per-Storyform | 103 (subplot manifest) |
| ADR-3 | Every Chapter+Scene carries both `narrative_order` and `story_time` | 102 (ontology), 106 (series_coherence's timeline-alignment axis), 108 (timeline_continuity_gate) |
| ADR-4 | World is a typed sub-graph with closed taxonomy | 102 (8 sub-schema nodes + WorldAxiom + Canon edges) |
| ADR-5 | Volume/Part/Book hierarchy is opt-in via `Novel.outline_hierarchy` | 102 (ontology + lifecycle verbs gated on declaration) |
| ADR-6 | Per-POV voice signatures + arc-versioned signatures | 104 (`check_voice_consistency` POV-parameterized), 102 (Arc + ArcPhase nodes) |

The base schema (simple novel) works without ANY of the iteration-2
additions. They activate when the novel's frontmatter declares the
relevant complexity field.

### ADR-14: Novel delegates to dossier + prompt + thinking capabilities (iteration 13)

User directive (2026-06-07): *"Those Research Parts - Need to be its
own capability - that Feed into Research agents - so that we can freely
combine capabilities - novel is only the First one to make use of the
Research capability."*

The novel spec set's iter-10 (research-entity ontology) + iter-11
(prompt-engineering layer) + iter-12 (critical-thinking analysis +
research-prompt-optimizer ports) describe a general pattern. iter-13
PROMOTES these to three first-class agency capabilities:

| New capability | Spec | What it owns |
|---|---|---|
| `prompt` | 109 | Prompt engineering + optimization + 10-builder family + research-prompt-optimizer + token-budget composition + A/B variants + scoring + anti-pattern library |
| `thinking` | 110 | 14 critical-thinking methods (8 from Spec 091 + 6 net-new: red_team / socratic / pre_commitment / if_then_else / bayesian_update / analogy_map) + 3 composite verbs (apply_full_review / apply_decision_discipline / apply_design_review) |
|  `dossier` | 112 | Research-dossier authoring (intent_capture / brief_render / dossier.audit / brief_finalize / catalog_list) + corpus management (ingest / chunk / extract_entities / taxonomize / link / list) + context mapping (declare_context / infer_context / render_dossier / render_snippet) |

Novel's iter-10 + iter-11 verbs become **thin wrappers delegating to
the three new caps** via `ctx.call`. Per Spec 111 (capability migration
plan):

- 105 iter-10 research-entity stack → delegates to `dossier.*`
- 105 iter-12 research-prompt-optimizer verbs → delegate to `dossier.*`
- 104 iter-11 10 prompt builders → registered as domain-specific
  builders via `prompt.register_builder`
- 104 iter-11 engineering verbs → delegate to `prompt.*`
- 101 CRITICAL-ANALYSIS.md → uses `thinking.apply_design_review`
- The novel-specific behaviors (chapter-scoped context, voice-
  signature injection, beat-sheet binding) ride OVER the generic
  cap surface — wrappers add domain-specific logic, generic cap
  handles the substrate.

**The handshake** (per Spec 112):
```
USER → dossier.intent_capture → dossier.dispatch_research_via_dossier
                                    ↓
                              research.lead + research.specialist
                                    ↓
                              dossier.extract_entities + dossier.taxonomize
                                    ↓
                              dossier.declare_context (scope=chapter)
                                    ↓
                              dossier.render_snippet (snippet_kind=writing-assist)
                                    ↓
                              prompt.engineer (builder=chapter,
                                               context_refs=[snippet_id],
                                               voice_refs=[...],
                                               constraints=...)
                                    ↓
                              novel.chapter_draft_assisted
                                    ↓
                              LLM (via Spec 092 G3 llm driver)
                                    ↓
                              novel.score_prompt_output
                                    ↓
                              prompt.score_output (accepted=True)
                                    ↓
                              novel Draft node PRODUCES the canonical chapter
```

**Why this matters**:
- **Composability**: music's research-heavy concept albums can use
  `dossier.*` without re-implementing the entity pipeline. Screenplay,
  journalism, legal, academic — same story.
- **Substrate over duplication**: the prompt-engineering pattern
  becomes one capability serving many domains, not duplicated per-cap.
- **Critical-thinking as first-class**: ANY capability can call
  `thinking.apply_design_review` on its own specs. The pattern that
  produced novel iter-12's CRITICAL-ANALYSIS.md generalizes.
- **Research-capability handshake**: `dossier.dispatch_research_via_dossier`
  is the bridge — domain caps ask dossier, dossier asks research.

### ADR-13: Distribution channels + post-pub feedback loop (iteration 12 — decompose pass)

Critical-thinking decompose surfaced two MECE gaps:

**Distribution-channel optimization** (107 cluster gains per-channel
metadata):
```python
DistributionChannel  (slug, name, kind)
                      # kind: kdp | apple | ingramspark | smashwords |
                      #       draft2digital | other
ChannelMetadata      (channel, novel, metadata: dict)
                      # platform-specific: BISAC codes, keywords,
                      #  series name, pricing tier, etc.
```

Two new verbs in 107:
- `prepare_for_channel(novel, channel_slug)` (act): renders the
  manuscript + metadata for a specific channel; per-channel format
  validation
- `validate_channel_metadata(novel, channel_slug)` (transform): checks
  every required field for the platform

**Post-publication feedback loop** (106 catalogue gains):
```python
PostPubFeedback      (slug, novel, source, rating, body,
                      sentiment, published_at)
                      # source: amazon | goodreads | apple | direct |
                      #         reviewer-org
```

Three new verbs in 106:
- `ingest_review(novel, source, rating, body)` (effect): records a
  review/rating; cross-references existing analytics
- `review_sentiment_aggregate(novel)` (transform): per-novel sentiment
  distribution + chapter-level keyword analysis
- `trigger_revision_from_feedback(novel, threshold)` (effect): when
  rating drops below threshold, creates EditNotes from the lowest-
  rated reviews; feeds a follow-up revision pass

IP-extension framework (audio drama / TTRPG / video game / film
adaptation) is **deferred** to a future spec — too out-of-scope for
this wave but documented for downstream planning.

### ADR-12: Prompt + context engineer for writing-assist (iteration 11)

User directive (2026-06-07): *"We also Need a prompt and context
engineer for writing assist prompts."*

Lands in 104 prose cluster (where prompts run + LLM is consumed) with
the following shape:

- **10 prompt builders** ported verbatim from the imported
  `021-novel-prompt-builder-family.md` (world/character/scene/
  storyform/throughline/bridge/chapter/revision/theme/relationship)
- Uniform signature: `build_<entity>_prompt(work_id, entity_id, mode,
  dry_run)` → `{prompt, sources, composes_with, preview, mode}`
- Read-only + idempotent + source-traceable + preview ≤ 200 tokens +
  acyclic composes-with DAG (021 contract)
- Anchored in 8 prompt-engineering research sources (Anthropic
  long-context · Sudowrite · NovelCrafter · Lee CHI 2024 · Weaver ·
  DraftSmith · K.M. Weiland · Matt Bell)

**Engineering pass layer** (iter-11 net-new beyond 021):
- `engineer_writing_prompt` (HEADLINE verb): composes builder backbone
  + voice signature + storyform context + beat sheet + PromptSnippets
  (iter-10) + anti-patterns; token-budget enforced
- `score_prompt_output` (effect): human evaluates LLM output;
  promote-to-draft via `accepted=True`
- `analyze_prompt_iteration` (transform): A/B compares prompt variants
- `register_anti_pattern` (effect): records known failure modes;
  appears as DO-NOT-DO-THIS examples in future prompts
- 3 context-injection helpers (voice / storyform / beats)

**Walkable skill** `prompt-engineering-pass` (6 phases): select-builder
→ inject-context → specify-constraints → render-prompt → iterate-
variants → score-output (hard human-eval gate).

**Load-bearing handshake**: `engineer_writing_prompt` (iter-11)
consumes `PromptSnippet` (iter-10) — the research-entity pipeline
feeds the writing-assist prompt composer. A complex novel's chapter
draft uses: builder backbone + voice + storyform + beats + N research
snippets + anti-patterns, all composed within the token budget.

**New ontology nodes** (declared in 102):
- `PromptTemplate` (builder_kind + body + version)
- `PromptInstance` (template + entity_refs + voice_sig_ref +
  storyform_refs + rendered_body)
- `PromptOutput` (instance + response_body + score + accepted)
- `PromptVariant` (parent_instance + variant_kind: tone-shift|
  length-target|constraint-relax|constraint-tighten)
- `AntiPattern` (kind: on-the-nose-dialogue|filter-word-overload|
  adjective-heavy|telling-not-showing|...)

**Doctrine alignment**:
- 021 contract preserved (read-only, idempotent, source-traceable,
  ≤200-token preview, acyclic DAG)
- ADR-1: prompts preserve canon_language (no translation)
- ADR-7 (AI-use): every PromptOutput stamped generated_by="llm";
  accepted=True drafts inherit; ai_use_report (104) factors them
- ADR-11 integration: PromptSnippets (research entities) bundle into
  prompts; the same research effort serves both pipelines
- **Canon prose protection**: prompts contain entities + voice
  instructions + storyform constraints + beats + anti-patterns — NOT
  the novel's prior canon prose. The author's voice is never re-fed
  to the LLM as training context.

### ADR-11: Research-entity ontology for writing-assist (iteration 10)

User directive (2026-06-07): *"we Need Complex Research World Ontology
Workflows — to ingest background Research (Physics, Philosophy, etc...)
and we Need a way to map those into Chapters. Also a way to rebuild it
into entities tagged to address specific aspects we can directly use as
prompt snippet for writing assist."*

The cluster extends from "claim verification" (099 pattern: ResearchClaim
+ VerificationRecord) to **research-informed writing assistance**: a
four-stage pipeline (ingest → extract → map → render) that turns
long-form background research into per-chapter prompt snippets the LLM
driver consumes during drafting.

**The four-stage pipeline** (full design in 105 iteration-10):

```
ResearchSource → ResearchChunk → ResearchEntity → ChapterContext → PromptSnippet
                                  + EntityTag      (CONTEXTUALIZES)   (BUNDLES)
                                  + EntityRelation
```

**Key node types** (declared in 102's consolidated ontology):
- `ResearchSource` (kind: paper/book/treatise/lecture-transcript/
  interview/dataset/image-set)
- `ResearchChunk` (paragraph/section/quote/figure-caption)
- `ResearchEntity` (concept/mechanism/definition/example/counterexample/
  lineage/theorem/anecdote/quote/analogy/empirical-fact)
- `EntityTag` (taxonomies: subject/discipline/era/author/applicability/mood)
- `EntityRelation` (depends-on/contradicts/illustrates/refines/
  derives-from/inspired-by)
- `ChapterContext` (purposes: backbone/flavor/factcheck/counterpoint/
  metaphor-source)
- `PromptSnippet` (snippet kinds: writing-assist/dialogue-prompt/
  description-prompt/exposition-prompt/metaphor-prompt)

**Two new walkable skills** (in 105):
- `research-ingest-pipeline` (5 phases: source-upload → chunk → extract
  → taxonomize → human-review)
- `chapter-context-build` (4 phases: infer-candidates → declare-context
  → build-snippet → confirmation)

**Integration with 104 prose**: `chapter_draft_assisted` gains an
`inject_prompt_snippet` parameter; when set + a cached `PromptSnippet`
exists for the chapter, the snippet's body prepends the LLM prompt as
research-context prefix. The snippet replaces the `voice_notes` slot
in the existing prompt template.

**Integration with 099 base** (ResearchClaim → ResearchEntity):
`materialize_claims_as_entities` bridges 099's claim-verification
pattern into iter-10's writing-assist pattern — every verified
ResearchClaim becomes a ResearchEntity (kind=quote/empirical-fact)
that can flow into ChapterContext + PromptSnippet.

**Doctrine alignment**:
- ADR-1 (no canon translation): entity bodies preserve source language;
  the agent decides integration (paraphrase / quote / footnote)
- ADR-7 (AI-use disclosure): ResearchEntity carries `generated_by` so
  entity-derived prose factors into the AI-use report
- Canon prose protection: prompt snippets contain RESEARCH entities,
  NOT the novel's draft prose; the author's voice is never used as
  training context

### ADR-8: Multi-author collaboration (iteration 8 — was deferred at iter-1)

A complex novel may have multiple authors — co-writers, ghostwriters,
editors with write-access. The capability supports this via
**per-scope authorship**:

- The `Novel` node carries `authors: list[str]` (slug list).
- The `Chapter` node carries `primary_author: str` + `contributors: list[str]`.
- The `Scene` node inherits its chapter's authorship by default; can be
  overridden.
- The `Character` node has `owned_by: str` for character-ownership in
  POV-rotation novels.

Conflict resolution:
- One writer per Chapter at a time (lifecycle phase serializes edits).
- The `claim_chapter` verb (102 iter-8) marks a chapter `locked_by:
  <author>` for the duration of an editing session.
- `release_chapter` releases the lock; auto-released after 60-min idle.
- Concurrent reads are always allowed; writes are serialized.

Provenance: every Draft has `author_slug` matching the contributing
author. The ai_use_report (104) breaks out per-author percentages.

### ADR-9: Marketing & comp-title tracking (iteration 8)

For traditional publishing, query letters and synopsis need comp titles
(comparable books) and BISAC categories. The capability declares:

```python
# Added to 102's consolidated ontology:
CompTitle    (slug, novel, title, author, year, similarity_axis,
              market_performance)
              # similarity_axis: theme | genre | tone | structure | hook
              # market_performance: bestseller | strong | mid | weak

BisacCategory (slug, novel, code)  # e.g. "FIC027070"
```

107 verbs (added in iter-8):
- `add_comp_title` (effect) — declares a comp; records similarity_axis
- `add_bisac_category` (effect) — primary + up to 2 secondary BISACs
- `comp_title_report` (transform) — summarizes for query letter
- `validate_bisac` (transform) — checks BISAC code against the official
  list (data file under `data/reference/marketing/bisac-codes.yaml`)

### ADR-10: Legal/IP awareness (iteration 8)

Beyond plagiarism check, biographical/historical fiction has libel risk;
some fiction uses public-domain characters. The capability adds:

- `LegalNote` node (102, iter-8): `slug, novel, kind: libel-risk|
  public-domain-character|trademark-usage|real-person-portrayal, text,
  resolved: bool, resolution_note`
- `check_libel_risk` (105, iter-8): scans prose for real-person mentions;
  cross-references against 105's research claims; WARNs on unverified
  attribution
- `check_public_domain_usage` (105, iter-8): flags use of named
  characters (Sherlock Holmes, Anne Shirley) and reports their PD
  status by jurisdiction
- The `publish-ready` skill (108) gates on `LegalNote.resolved=true` for
  every flagged risk

These are diagnostic — they surface concerns; they don't litigate. The
human-curator (or an actual lawyer) resolves them.

### ADR-7: AI-use disclosure (iteration 5)

Traditional publishing increasingly requires authors to disclose
LLM-generated prose. The novel capability ships an **AI-use disclosure**
discipline:

- Every artefact (Draft, Chapter, Scene body) carries a `generated_by`
  field — one of `human`, `agent`, `llm`, or `mixed`.
- A new transform verb `ai_use_report` (104) aggregates per-novel:
  `{total_words, words_by_source: {human: N, agent: N, llm: N, mixed: N},
  percentages, chapters_with_llm_content: [N]}`.
- The `publish-ready` skill (108) requires a hard `elicit` gate on
  "review AI-use report"; the artefact is part of the publication
  package (recorded as `ManuscriptArtefact, kind: ai-use-report`).
- The `query_letter` template (107) carries a `disclose_ai_use: bool`
  field; when set, the rendered letter includes a paragraph drawn from
  the AI-use report.
- The `chapter_draft_assisted` verb (104 Path B) MUST stamp
  `generated_by: llm`; manual edits flip to `mixed` (verb
  `mark_human_edited` in 104).

Test asserts: no verb can silently set `generated_by` to `human` once a
prior version was `llm` or `mixed` (audit-trail integrity).

### ADR-1 edge cases (multilingual canon details)

The "no translation" rule has 6 specific behaviours that need
implementation discipline:

1. **Code-switching dialogue** (a German character speaks one English
   sentence): the sentence stays English in the canon; `extract_
   language` reports a `mixed` rather than a `de` classification; voice-
   consistency check uses the dominant language's signature.

2. **Translation drafts** (an English version OF the German canon): a
   SEPARATE artefact `kind: translation-draft` with explicit
   `source_language: de`, `target_language: en`, `generated_by` field.
   These are renders of the canon, NOT the canon. The base novel state
   reads ONLY the canon.

3. **Multilingual epub `<dc:language>`**: the dominant language; per-
   chapter `xml:lang` reflects the chapter's `canon_language`.

4. **Foreign-language single-word terms** (named items, place names):
   left in source language; `extract_proper_nouns` (104) does not
   translate them.

5. **LLM Path B drafting**: when the LLM is bound and used to draft
   prose, the prompt explicitly instructs "respond in `<canon_language>`";
   if the response is detected (via `extract_language`) in a different
   language, the verb returns `CANON_LANGUAGE_VIOLATION` and discards
   the draft.

6. **Query letter / synopsis as separate works**: a German-canon novel
   may have an ENGLISH query letter — but the query letter is its own
   artefact authored from scratch by the agent, NOT a translation of
   the canon prose. The query letter template's `target_language`
   field declares the language; the body is composed independently.

## Open questions

1. **NCP schema embedding**: the NCP v1.3.0 schema (463 appreciation
   enums + 144 narrative_function enums) lands as a static JSON under
   `agency/capabilities/novel/data/schemas/ncp-schema-v1.3.0.json`.
   Validation runs via `jsonschema` (already a transitive dependency of
   `[dev]`).
2. **ontology.json hosting**: the 304-entry Dramatica ontology lands as
   `agency/capabilities/novel/data/dramatica/ontology.json`. Decidable
   checks load it once at first TextDriver call (memoized).
3. **Element-level granularity (deferred)**: 103 ships Class · Type ·
   Variation as queryable nodes; full Element-level subgraph (256 leaves)
   ships in a v2 spec when usage justifies. The decidability matrix's
   element-level checks (KTAD, Quad completeness) still pass — they use
   the ontology.json directly without graph nodes per Element.
4. **Multi-author / collaboration**: out of scope. v1 is single-author.
5. **Generated-prose attribution**: Path B (LLM-driven drafting) must
   tag generated text in the artefact metadata. Tested.

## Followup — Implementation Status (2026-06-07)

**Verdict:** Drafted (spec set authored + spec-panel reviewed).

### Done
- Master spec authored (this file).
- Seven cluster specs (102–108) drafted.
- MVP source imported from `netzkontrast/the-agency-system` under
  `Plan/_research/novel-mvp-source/` (11 templates + 2 reference docs +
  6 prior specs).
- Dramatica Decidability Matrix referenced (15 rows).
- Novel-Craft Parity Table referenced (30 rows + 6 novel-specific
  additions).
- Cluster coherence mapped to Spec 047's 13-cluster taxonomy.
- Migration order documented.
- Spec-panel pass via `sc:sc-spec-panel` recorded in `REVIEW.md`.

### Still
- Implementation phase: each child spec drives its own RED→GREEN→Refactor.
- The E2E provenance test lands in 108.
