# Import / Export Patterns — Novel Lifecycle

> Iteration 6 (2026-06-07). Writers come to the novel capability with
> existing work in Scrivener, Word, or plain markdown. This document
> defines the import path + the round-trip integrity discipline.

## Import sources (initial wave)

| Source | Verb | Maps to |
|---|---|---|
| Markdown directory tree | `import_from_markdown` | Each `.md` → Chapter or Scene; frontmatter → properties |
| Scrivener project (`.scriv` zip) | `import_from_scrivener` | Each "document" → Scene; "folder" → Chapter; "binder" → Outline |
| Word document (`.docx`) | `import_from_docx` | Heading-1 → Chapter; Heading-2 → Scene; body → draft body |
| Single markdown file | `import_from_md_file` | Splits on `# Chapter` headings → Chapter; `## Scene` → Scene |

All four are EFFECT verbs (write to graph + filesystem). They share a
common pattern:

```python
@verb(role="effect")
def import_from_scrivener(self, scriv_path: str,
                          author: str, title: str,
                          genre: str = "literary",
                          dry_run: bool = True) -> ToolResult:
    """Parse a Scrivener project. dry_run=True (default) returns the
    proposed mapping WITHOUT writing. dry_run=False creates the Novel
    + Chapter + Scene nodes + renders templates + writes the draft
    bodies.

    Returns {novel_slug, chapters_created, scenes_created,
    warnings: [...]}. Warnings emitted for: unparseable frontmatter,
    embedded scrivener annotations (carried over verbatim as
    <!-- TODO --> markers), POV character not yet defined."""
```

## Import → graph mapping discipline

For every imported chapter/scene:

1. Body text → `Chapter.body` or `Scene.body` (raw markdown)
2. Frontmatter title → `.title`
3. Frontmatter POV → `Scene.pov_character` (creates Character node if
   missing — flagged as warning)
4. Embedded annotations / comments → extracted as `EditNote` rows (106)
5. `generated_by = "human"` (no LLM provenance on imported content)
6. `canon_language` defaulted via `extract_language` on first chapter

## Round-trip integrity

A core invariant: `import → export → import` round-trips losslessly for
the BODY text. Properties may transform (e.g. POV string → Character node
id resolution) but body text is preserved character-for-character.

Test: `tests/test_novel_roundtrip.py` ships fixtures for each format
and asserts `assert_imported_body_equal(original, roundtripped)`.

### Edge cases the round-trip MUST handle

- **Unicode characters** (German umlauts, smart quotes, em dashes):
  preserved verbatim
- **Markdown formatting** (bold, italic, blockquotes): preserved
- **Embedded annotations** (Scrivener inline comments): extracted to
  EditNotes; original positions preserved on re-export via marker comments
- **Image references**: image paths rewritten relative to the novel
  workspace; original references preserved as fallback
- **Footnotes / endnotes**: preserved; converted to markdown footnote
  syntax

## Export paths

The `render_*` verbs in 107 handle export — but they're "render for
consumption" not "export for editing". The lifecycle cluster ships
ONE additional export verb for editorial round-tripping:

```python
@verb(role="effect")
def export_for_editor(self, novel: str,
                      format: str = "docx",
                      track_changes: bool = True) -> ToolResult:
    """Export the manuscript in editor-friendly format. format options:
    docx (with track-changes), scrivener (.scriv zip), markdown
    (per-chapter files). track_changes=True annotates the document
    with REVISES edge history as Word comments."""
```

## Schema migration (iteration 6)

The agency substrate supports additive schema changes (per CLAUDE.md
rule 2: graph is the store). When iteration-2 or -3 ships new node
types (Volume / Part / Book / World subschema), existing simple novels
need a migration path.

### Migration discipline

1. **Additive only**: new node types + new optional fields. Never:
   rename existing types, remove required fields, change enum sets.
2. **Per-axis migrations**: each iteration-2 axis (Volume hierarchy,
   World sub-graph, Character arcs) ships its own one-shot migration
   verb that adds the new nodes WITHOUT touching existing state.

```python
@verb(role="effect")
def migrate_to_volume_hierarchy(self, novel: str,
                                 dry_run: bool = True) -> ToolResult:
    """Wrap existing Chapter set in a single default Volume (and Book if
    multi-Volume). dry_run shows the mapping. Writes a MIGRATED edge
    from old root → new root for audit."""
```

3. **Migration provenance**: every migration records a `Migration` node
   SERVES the intent, with `from_schema_version` + `to_schema_version`
   fields. The provenance moat preserves the pre-migration shape.

### Schema version tagging

Each Novel carries a `schema_version` field. Capability bootstrap reads
the current capability version; if a Novel's version is older, it can
be migrated lazily on first read (the `find_novel` verb returns a
warning + migration suggestion).

## Git / version-control coexistence

The novel capability's state lives in `.agency/session.db` (graph) +
rendered files under `agency/capabilities/novel/data/<author>/<slug>/`
(filesystem view).

### Writer workflow with git

A writer who tracks their novel in git:

1. Sets `output_root` to a git-tracked directory.
2. The `render_outline` / `render_chapter` verbs write to that
   directory (Spec 060 substrate path).
3. Writer commits the rendered output — they get standard git tooling
   (diff, log, branch) on top of agency's graph-native provenance.
4. The graph remains the source of truth; rendered files derive from
   the graph at any commit.

### Round-trip vs git: graph wins

If a writer edits a rendered file (out-of-band) AND the graph is
updated by a verb, the graph wins on next render. The lifecycle cluster
ships a `reconcile_disk_with_graph` verb that:

- Detects out-of-band edits (compares disk body against graph body)
- Reports diffs as findings
- Offers two resolution paths: (a) replace disk with graph, OR
  (b) ingest disk changes back into the graph as a new Draft
- Never silently overwrites disk

```python
@verb(role="transform")
def reconcile_disk_with_graph(self, novel: str) -> ToolResult:
    """Diff disk-rendered output against graph-canonical body. Returns
    findings. Does NOT mutate; reconciliation is a separate effect
    verb (ingest_disk_changes OR rerender_from_graph)."""
```

### Why graph-canonical (carried from ADR-3 of kohaerenz SYNTHESIS)

- The graph queries: "who edited chapter 7 in revision pass 3?" — git
  blame can't answer this across renders
- Provenance crosses renders: a single intent's chain doesn't reset
  when the writer regenerates a chapter
- Multi-author concurrent edits work via the lifecycle phase
  protocol (one writer per chapter at a time per scope)

## Backup / disaster recovery

For long novels (500K words, 1000s of graph nodes):

1. `.agency/session.db` is a SQLite file — copy it for backup
2. Rendered files under `data/<author>/<slug>/` can be committed to
   git for off-host backup
3. Per-novel `export_for_editor(format="markdown")` produces a
   plaintext representation that can survive any future schema
   migration; it's the disaster-recovery backstop
4. `agency_doctor` (substrate) reports DB size + last-write time

The substrate provides the storage; this cluster relies on it. No new
backup machinery in the novel capability.
