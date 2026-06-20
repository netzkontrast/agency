---
spec_id: "107"
slug: novel-manuscript-cluster
status: draft
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["102", "104", "106", "101"]
affects:
  - agency/capabilities/novel/clusters/manuscript.py
  - agency/capabilities/novel/drivers.py        # NEW: FormatDriver
  - agency/capabilities/novel/ontology.py
  - agency/capabilities/novel/templates/        # query-letter, synopsis, blurb, back-cover
  - tests/test_novel_manuscript.py
domain: novel / manuscript / publishing / format-render
wave: 8
parent_spec: "101"
mvp-source:
  - "Plan/_research/novel-mvp-source/references/parity-table.md (copy-editor, proofreader, blurb-writer, cover-art-director, publication-director)"
  - "Plan/098 music-promo-cluster (the LLM-driver opt-in pattern)"
  - "Plan/096 music-audio-cluster (the failure-mode pattern)"
---

# Spec 107 — Novel Manuscript Cluster

## Why

The output cluster: renders the novel to manuscript / epub / PDF / docx
and prepares the publication package (query letter, synopsis, blurb,
back-cover). Introduces the **FormatDriver** boundary — pandoc / LaTeX /
wkhtmltopdf / calibre shell-outs behind a typed Spec-002 Option B
protocol.

Per the parity table, this cluster owns: `copy-editor`, `proofreader`,
`cover-art-director`, `blurb-writer`, `marketing-copy-director`,
`publication-director`, `revert-to-clean-draft`, `manuscript-dashboard`.

## Done When

- [ ] **10 user-facing verbs ship** (see manifest).
- [ ] **1 composite gate verb** ships: `publication_gate`.
- [ ] **FormatDriver protocol** declared in `drivers.py` with deterministic
      fake (no real pandoc/LaTeX/wkhtmltopdf binaries in CI).
- [ ] **Walkable skills ship**: `manuscript-pass`, `publish-prep`.
- [ ] **4 templates land** under `agency/capabilities/novel/templates/`:
      `query-letter.md`, `synopsis.md`, `blurb.md`, `back-cover.md`.
- [ ] **Deferred-import discipline** (matches music's 097/098 iteration-5
      fix): pandoc/wkhtmltopdf availability checked at first call,
      degrades with typed `DEPENDENCY_MISSING` per-verb (NOT engine bootstrap).
- [ ] **`tests/test_novel_manuscript.py` Green** (~12 tests; zero binaries).
- [ ] **`TODO.md` updated** with 107 row.

## Verb manifest

| # | Verb | Role | Driver | Music analog |
|---|---|---|---|---|
| 1 | `copy_edit` | effect | TextDriver | `mastering-engineer` |
| 2 | `proofread` | effect | TextDriver | `mastering-engineer (final polish)` |
| 3 | `render_manuscript` | effect | FormatDriver | `master_album` |
| 4 | `render_epub` | effect | FormatDriver | (new) |
| 5 | `render_pdf` | effect | FormatDriver | (new) |
| 6 | `render_docx` | effect | FormatDriver | (new) |
| 7 | `draft_query_letter` | act | StateDriver+(optional LLM) | `promo_copy` |
| 8 | `draft_synopsis` | act | StateDriver+(optional LLM) | `promo_copy` |
| 9 | `draft_blurb` | act | StateDriver+(optional LLM) | `promo_copy` |
| 10 | `publish_package` | act | StateDriver+FormatDriver+CloudDriver | `release_package` |

**Internal gate**:

| # | Verb | Composes |
|---|---|---|
| G1 | `publication_gate` | manuscript-rendered + query-letter-drafted + synopsis-drafted + cover-art-ready + metadata-complete + gate.check |

**Total: 10 user + 1 gate = 11 registered verbs.**

## Design

### FormatDriver protocol (new — Spec-002 Option B)

```python
class FormatDriver(Boundary):
    """Manuscript-format / epub / PDF / docx render via pandoc + LaTeX +
    wkhtmltopdf + calibre. Deferred imports (Codex P2 iteration 5
    discipline): driver __init__ does NOT touch the binaries; first
    method call lazy-imports + raises DependencyMissing if absent.
    """
    def pandoc(self, args: list[str], input_text: str = "") -> str: ...
        # shell-out to pandoc; returns rendered output
    def latex_compile(self, tex_body: str) -> bytes: ...
        # latex → PDF bytes
    def epub_pack(self, html_body: str, manifest: dict) -> bytes: ...
        # html + manifest → epub bytes
    def wkhtmltopdf(self, html_body: str) -> bytes: ...
    def docx_render(self, html_body: str, style: str = "") -> bytes: ...
```

Fake produces deterministic stub bytes keyed on novel slug:
`b"<format-stub:%s:%s>" % (kind, slug)`.

### Failure modes (per the music 096/097/098 discipline)

| Boundary call | Failure mode | Driver returns | Verb returns |
|---|---|---|---|
| `pandoc` not installed | `FileNotFoundError` at first call | raises `DependencyMissing("pandoc")` | `ToolResult.failure(DEPENDENCY_MISSING, "pandoc not on PATH — install agency[novel-format]")` |
| `pandoc` segfault | non-zero exit | `RuntimeError` with stderr tail | `ToolResult.failure(BOUNDARY_FAILED, "pandoc segfault")` |
| `pandoc` timeout (default 60s) | `subprocess.TimeoutExpired` | `TimeoutError` | `ToolResult.failure(BOUNDARY_TIMEOUT, …)` |
| `wkhtmltopdf` missing | same pattern | raises `DependencyMissing` | per-verb `DEPENDENCY_MISSING` |
| `calibre` (`ebook-convert`) missing | same | raises `DependencyMissing` | per-verb `DEPENDENCY_MISSING` |
| `latex` missing | same | raises | per-verb `DEPENDENCY_MISSING` |

### Templates added in this cluster

| Template | Renders |
|---|---|
| `query-letter.md` | Agent query letter (hook + comp titles + bio + author photo URL) |
| `synopsis.md` | 1-page + 3-page synopsis variants |
| `blurb.md` | Back-cover blurb |
| `back-cover.md` | Full back-cover (blurb + bio + early reviews) |

All registered on the consolidated `OntologyExtension.templates` (102).

### Walkable skill: `manuscript-pass` (5 phases)

```python
MANUSCRIPT_PASS_SKILL = {
    "name": "manuscript-pass",
    "kind": "workflow",
    "phases": [
        {"index": 1, "name": "format-pick",
         "produces": ["formats_selected"]},
        {"index": 2, "name": "render",
         "produces": ["all_formats_rendered"]},
        {"index": 3, "name": "validate",
         "produces": ["format_validity_confirmed"]},
        {"index": 4, "name": "distribute",
         "produces": ["distribution_uploads_complete"]},
        {"index": 5, "name": "confirmation",
         "produces": ["manuscript_locked"], "gate": "hard"},
    ],
}
```

**Primary actor**: agent (technical pipeline); human-curator signs off at
phase 5.

### Walkable skill: `publish-prep`

4 phases (gather-assets → render → catalogue → announce). Mirrors music's
`release-publish` skill.

## Test plan

```python
# tests/test_novel_manuscript.py — ~12 tests
def test_manuscript_cluster_discovers_all_verbs(): ...
def test_format_driver_deferred_import_no_pandoc_at_init(): ...
def test_format_driver_first_call_raises_dependency_missing(): ...
def test_render_manuscript_uses_fake_format_driver_in_test(): ...
def test_render_epub_produces_deterministic_artefact(): ...
def test_render_pdf_handles_pandoc_timeout(): ...
def test_render_docx_records_manuscript_artefact(): ...
def test_draft_query_letter_uses_template_path_a_by_default(): ...
def test_draft_synopsis_falls_back_when_llm_unbound(): ...
def test_draft_blurb_records_blurb_artefact(): ...
def test_publish_package_composes_all_outputs(): ...
def test_manuscript_pass_skill_walks_to_phase_5(): ...
def test_publication_gate_blocks_when_query_letter_missing(): ...
```

## Audiobook prep (iteration 9 — carries forward bitwize's pronunciation discipline)

Music's `pronunciation-specialist` skill (095) ports to novels as the
`narrator-voice-specialist` per the parity table. For audiobook
production, the manuscript cluster ships:

```python
@verb(role="effect")
def generate_audiobook_pronunciation_key(self, novel: str) -> ToolResult:
    """Per-novel proper-noun pronunciation guide. Extracts every Character.
    name, place name (from World subgraph), made-up word, and foreign
    term. For each, declares phonetic pronunciation (IPA + plain spelling)
    + per-character voice direction (age, accent, register).

    Output: a markdown file the narrator/director uses during recording.
    Artefact kind: 'audiobook-pronunciation-key'."""

@verb(role="effect")
def render_audiobook_script(self, novel: str,
                            with_direction: bool = True) -> ToolResult:
    """Renders chapter prose with stage-direction annotations: POV
    character voice cues, emotional beats, scene-transition markers,
    dialogue speakers explicit. Format suitable for narrator script."""

@verb(role="transform")
def detect_pronunciation_risks(self, novel: str) -> ToolResult:
    """Mirrors music's check_pronunciation_enforcement. Scans for
    homographs, foreign words, proper nouns lacking the pronunciation
    key entry, and reports candidates needing IPA annotation."""
```

The `narrator-voice-specialist` skill is the agency-skill front-end;
the verbs above are its tool surface.

## Series-arc tracking (iteration 9 — multi-book novels)

For multi-book series (10-book epic), character arcs span volumes.
iteration 9 adds:

```python
# Added to 102's consolidated ontology:
SeriesArc      (slug, series, character, arc_phases: list[dict])
                # arc_phases: [{volume: N, phase_name, growth_state,
                #               key_events}]

@verb(role="effect")
def declare_series_arc(self, character: str, series: str,
                       arc_phases: list[dict]) -> ToolResult: ...

@verb(role="transform")
def series_arc_coverage(self, series: str) -> ToolResult:
    """For each Character with a SeriesArc, report which phases have
    been narratively realized (cross-references Beat + Scene nodes)
    vs which remain pending across the series."""

@verb(role="transform")
def character_continuity_across_series(self, character: str,
                                       series: str) -> ToolResult:
    """Tracks character age math, motivation continuity, relationship
    states across volumes. Flags inconsistencies (character 'forgets'
    a vow taken 3 books ago)."""
```

## Reader-experience modeling (iteration 9)

Different readers experience the novel differently. The cluster ships:

```python
@verb(role="transform")
def first_read_pacing_check(self, novel: str) -> ToolResult:
    """Simulates a first-time reader's pacing experience. Flags chapters
    likely to lose first-time readers: information overload, too many
    new characters, opaque worldbuilding without context."""

@verb(role="transform")
def reread_signal_check(self, novel: str) -> ToolResult:
    """For literary fiction that rewards rereading: identifies callbacks
    + foreshadowing density. Heavy callback density = high reread
    value; novels lacking callback structure may underperform on
    rereads."""

@verb(role="transform")
def binge_friendliness_check(self, novel: str) -> ToolResult:
    """For genre fiction read in single sittings: per-chapter cliffhanger
    density. Flags chapters that end on a 'low note' (no question, no
    forward momentum) — binge-resistant chapters."""
```

## Full-export disaster recovery (iteration 9)

For novel-DR purposes, a single verb that exports EVERYTHING in
machine-readable form:

```python
@verb(role="effect")
def export_full_archive(self, novel: str,
                        format: str = "tar.gz") -> ToolResult:
    """Export the complete novel state — all chapters, scenes, characters,
    storyform, NCP, world, beta-feedback, edit-notes, version log,
    AI-use report, legal notes, comp titles, BISAC, audiobook prep,
    series arcs — as a single tarball.

    Restorable via import_full_archive. Designed as the disaster-
    recovery backstop independent of session.db format changes.

    Format options: tar.gz (default), zip, json-bundle."""
```

## Complex-novel extensions (iteration 2)

### Series-boxset rendering

For multi-volume / series novels, the cluster ships two additional verbs:

| # | Verb | Composes |
|---|---|---|
| 11 | `render_series_boxset` | Iterates Volumes (102 ontology) + renders a combined epub/PDF per volume + a single boxset epub bundling all volumes |
| 12 | `render_per_volume_manuscript` | Renders manuscript-format per Volume (for individual-Volume agent queries) |

The `publish_package` verb (existing #10) gains a `mode` parameter:
`single-novel | series-boxset | per-volume`. Default `single-novel`
matches base behaviour.

### Per-format multilingual metadata (ADR-1 honored)

For multilingual novels:
- The rendered epub/PDF carries `<dc:language>` metadata matching the
  CHAPTER's `canon_language`
- A novel that mixes languages (e.g. German narration + English
  dialogue) ships a single epub with `dc:language` = the dominant
  language and per-chapter `xml:lang` attributes
- No machine translation step is offered — agency cannot translate
  canon prose (per ADR-1)

### Manuscript-format for agents (query-letter context)

The query-letter template (already declared) gains a `target_language`
field — for German canon, an English query-letter is a SEPARATE artefact
draft (`generated_by: agent`), NOT a translation of canon prose. The
agent drafts an English query OF the German novel from scratch.

## Open questions

1. **Format options**: v1 ships pandoc / wkhtmltopdf / calibre via
   FormatDriver. LaTeX-pure rendering deferred to v2.
2. **EPUB vs MOBI**: epub3 only for v1. KDP-flavored mobi via calibre
   is a `[novel-format]` extra (already covered).
3. **Cover-art generation**: cover art is sourced externally (not
   generated). `cover-art-director` skill provides design brief; image
   is supplied by the user.

## Followup — Implementation Status (2026-06-09)

**Slice 1 SHIPPED** on branch `claude/spec-102-novel-lifecycle` (PR #80).

### Done in Slice 1

3 driver-free renderers, all acts producing typed artefacts:
- `render_blurb(novel_id, hook, stakes)` → blurb artefact
- `render_query_letter(novel_id, agent_name, comp_titles)` → query-
  letter artefact
- `render_synopsis(novel_id)` → synopsis artefact (chapters in order)

Each verb runs `_require_novel` for NOT_FOUND on bogus novel_id. The
Registry records PRODUCES edges automatically when verbs return
`data["artefact"]`.

6 tests in `tests/test_novel_manuscript.py` (registration + happy +
NOT_FOUND for each renderer).

### Deferred to Slice 2+

- FormatDriver protocol declaration (pandoc / wkhtmltopdf / calibre
  shell-outs behind a deterministic fake)
- 7 FormatDriver-backed verbs: render_epub / render_pdf / render_docx
  / render_print_proof / etc.
- Composite `publication_gate`
- 2 walkable skills: manuscript-pass, publish-prep
- 4 publication templates port (query-letter.md / synopsis.md /
  blurb.md / back-cover.md)
