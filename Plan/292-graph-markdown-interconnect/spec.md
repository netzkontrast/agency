---
spec: 292
title: graph-markdown-interconnect
status: Partial (Slice 1 shipped)
depends_on: [043, 109]
clusters: [memory, document]
vision_goals: [6, 7, 9]
---

# Spec 292 — Graph↔Markdown Interconnect · the Document as convergence artefact

**Status:** Partial (Slice 1 shipped — bi-directional round-trip + keep-both +
prompt-audit + session view; convergence model in place, binding/render-mirror
follow-ups tracked below).

## Premise flip (owner directive, 2026-06-16)

The old central premise — *"the graph is the store; files are a one-way
rendered view"* (CLAUDE.md rule 2) — is replaced:

> **Graph and markdown files are interconnected peers.** The graph is the
> queryable spine; files are an editable surface that round-trips back into
> it. Reconciliation is **keep-both, bi-temporal**: graph- and file-authored
> versions coexist, latest wins on read, nothing is overwritten.

Four owner messages shaped the scope:

1. Graph and markdown should be **interconnected / bi-directional**.
2. **Integrate the prompt capability** — *every file is also a prompt*.
3. The **datalayer, templates, schemas, and ontologies** must be integrated —
   **Documents are the new artefact in which everything comes together**.
4. Documents also document **Intent · Capability · Lifecycle · Memory for a
   Session**.

## Design — the Document is the universal convergence artefact

**Identity + anchor.** A participating `.md` carries a stable anchor on its
first line — `<!-- agency-node: document:<id> -->` — reusing the HTML-comment
marker convention. The anchor names a `Document` node that IS the file's
identity. The content hash is computed on the *body* (anchor stripped), so
re-stamping never changes the hash → idempotent.

**Keep-both, bi-temporal.** Every ingest/render appends an append-only
`DocRevision` (`source ∈ {graph, file}`) linked `REVISION_OF` the Document.
`update()` (in-place) would lose history; `supersede()` would move the node id
and break the anchor — so the model is **event-sourced**: stable anchor node +
append-only revision children. Latest by `recorded_at` wins on read; the rest
is retained history.

**Convergence — the layers that meet on a Document:**

| Layer | How it lands on the Document |
|---|---|
| **Datalayer** | A Document is an ordinary graph node — queryable like any other. |
| **Templates / Schemas / Ontology** | `Document` binds optional `template` + `schema` props and `CONFORMS_TO` a `Schema` node; structure typed by the ontology. |
| **Prompt** | *Every file is also a prompt*: `ingest` scores the body via `prompt.audit`, recording `clarity_score` on the revision. |
| **Four concepts** | `document.session` renders **Intent · Capability · Lifecycle · Memory** for a Session into one Document. |

**Verb surface (added to the `document` capability):**

- `document.ingest(path, audit=True, template="", schema="")` — file → graph;
  mints/anchors a Document, appends a file-sourced revision, prompt-audits.
  `action ∈ created | revised | unchanged`.
- `document.sync(path=".", audit=True)` — batch idempotent ingest over `**/*.md`
  (the verb-now, hook-later entry point).
- `document.revisions(document_id)` — keep-both read surface: `{count, latest,
  history}` (latest-first).
- `document.session(for_intent_id="", apply_path="")` — render the four
  concepts for a Session as a graph-authored Document; `apply_path` writes the
  anchored file so it round-trips.

## Done-When

- [x] `ingest` mints a Document + writes the anchor back for an un-anchored file.
- [x] Re-ingesting an unchanged file is idempotent (`unchanged`, no new revision).
- [x] A changed file keeps both versions (graph + file revisions coexist).
- [x] Every ingested file carries a `clarity_score` from `prompt.audit`.
- [x] `sync` ingests every changed `.md`; a second run reports zero.
- [x] `session` renders Intent · Capability · Lifecycle · Memory as a Document.
- [x] Doctrine flipped: CLAUDE.md rule 2 + CORE.md canon section.
- [ ] **Follow-up:** `render` mirrors into a graph-sourced `DocRevision` so the
  graph→file direction is also event-sourced (today render returns content;
  the caller writes — only `session`/`ingest` append revisions).
- [ ] **Follow-up:** opt-in pre-commit hook calling `document.sync` on changed
  `.md` (the "hook later" half of the trigger decision).
- [ ] **Follow-up:** schema-conformance check on `ingest` when a Document
  `CONFORMS_TO` a Schema (validate front-matter against the bound schema).

## Followup — Implementation Status (2026-06-16)

**Done.** `agency/capabilities/document/_interconnect.py` (anchor/hash helpers)
+ `_main.py` verbs `ingest` / `sync` / `revisions` / `session`; ontology adds
`Document` + `DocRevision` nodes, `REVISION_OF` + `CONFORMS_TO` edges, and the
`(DocRevision, source)` enum. 6 new acceptance scenarios in
`tests/acceptance/features/document.feature` (steps in `test_document.py`) —
**39 document scenarios green**. Doctrine flipped in `CLAUDE.md` rule 2 and
`docs/vision/CORE.md` ("The Document — where everything comes together").

**Still.** The three follow-ups above (render→revision mirror, pre-commit hook,
schema-conformance on ingest). These are additive; Slice 1 stands alone.

**Friction surfaced while dogfooding (logged as graph reflections).**
(1) `skill_walk` "Missing required keyword only argument" does not name the
field; (2) `skill_walk` `resume_from='gate:<id>'` restarts the skill from
`explore` instead of resuming at the blocked gate (state loss); (3) `reflect`
ontology has no `friction`/`dogfood` scope. Tracked for a follow-up hardening
pass.
