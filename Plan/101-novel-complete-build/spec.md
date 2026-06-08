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

## Why

Music proved that a hard creative-production domain fits the clustered
Capability contract (Spec 093). Novels are the next proof: a structurally-
anchored creative pipeline (concept → research → storyform → outline →
draft → revise → beta → query → publish) that gains everything music
gained (typed verbs, walkable gates, provenance audit) PLUS a domain-
specific **decidable structural backbone**.

**The decidable backbone is Dramatica + NCP v1.3.0**. Per the imported
**Dramatica Decidability Matrix** (`Plan/_research/novel-mvp-source/
references/dramatica-decidability.md` — embedded brief, source research
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
  report shape** (per the decidability brief): drop PASS-check items
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
| **104** | prose | TextDriver | music lyrics (095) | ~12 user + 3 gate (developmental/line/copy editorial passes) |
| **105** | research | delegates to `agency.research` | music research (099) | ~8 user + 1 gate (10 domains; reuses 099 verbatim) |
| **106** | catalogue | DBDriver+StateDriver | music catalogue (097) | ~10 user + 1 gate (beta-feedback + version-log; manuscript/series coherence split) |
| **107** | manuscript | FormatDriver (new) + StateDriver+CloudDriver | music audio + promo (096+098) | ~10 user + 1 gate (4-stage editorial: developmental→line→copy→proof; renders manuscript-format/epub/PDF/docx + query letter + synopsis + blurb) |
| **108** | gates | gate.check + elicit | music gates (100) | ~6 user + 4 gate (pre-draft/beta-ready/query-ready/publish-ready) |
| | | **Totals** | | **~73 user + 11 gate = 84 registered** |

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
