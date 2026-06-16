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
- [x] **C1** schema-conformance + all document verbs name the missing field on error.
- [x] **C3** schema-conformance gate on `ingest` (validates frontmatter against the
  bound Schema, names missing fields) + `document.convergence` audit (flags a
  Document carrying none of template/schema/clarity/four-concepts as a defect).
- [x] **C4** `document.reopen` ingests an archived session Document and
  reconstructs the four `## Intent/Capability/Lifecycle/Memory` sections.
- [x] **C5** opt-in pre-commit hook `hooks/pre-commit-doc-sync.sh` + `agency
  install` now OFFERS the `--patch-claude-settings` one-liner when the plugin
  isn't enabled.
- [x] **Indexer ported + auto-run.** `develop.index` ports the repo indexer to
  the development-workflow surface (delegates to `document.index_repo`, DRY);
  the SessionStart hook (generated from `install.py`) runs it backgrounded each
  session so every session opens with a fresh `PROJECT_INDEX.md` / `RepoIndex`
  node (`AGENCY_INDEX_ON_START=0` opts out).
- [x] **Hooks drive core mechanics.** (1) **UserPromptSubmit injection** (sync,
  per directive) returns an assumption-guard wiring in `intent.assumptions` +
  `thinking`/`AskUserQuestion` so the agent surfaces assumptions and asks
  questions before acting; `agency hook` prints it to stdout, the dispatcher
  passes it to the prompt. (2) **SessionEnd → `document.session`** auto-archives
  the four-concept Document. (3) **Session Graph** — every hook event links
  `IN_SESSION` a `Session` node (keyed by `session_id`); `document.restore_session`
  reconstructs the complete session (event timeline + archived Document) from
  the graph alone, so a session survives its process ending. (4) **Session
  Graph analytics** — `Memory.session_analytics` (extensive Cypher per the
  Management read-API doctrine) + `document.session_analytics`: single-session
  report (event-type + tool breakdown, raw-tool bypass profile, attached
  Documents, intents, tick-span) and cross-session aggregate (status counts,
  busiest sessions, top tools/events, bypass totals).
- [ ] **Follow-up:** `render` mirrors into a graph-sourced `DocRevision` so the
  graph→file direction is also event-sourced (today render returns content;
  the caller writes — only `session`/`ingest`/`reopen` append revisions).
- [ ] **Follow-up:** the wire-layer "Missing required keyword only argument"
  (pydantic validation at the MCP boundary, e.g. `skill_walk`) still doesn't
  name the field — a substrate-wide envelope improvement.

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
