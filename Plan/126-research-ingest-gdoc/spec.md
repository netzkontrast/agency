---
spec_id: "126"
slug: research-ingest-gdoc
status: draft
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["044"]
affects:
  - agency/capabilities/research/_main.py
  - tests/test_research_ingest_gdoc.py
domain: research / ingest / context-economics
mvp-source:
  - "User directive (2026-06-10): ingest large numbers of Google Docs as Markdown without polluting orchestrator context — substrate for novel research-source corpus and research-report reading"
---

# Spec 126 — `research.ingest_gdoc` (subagent-isolated Google Drive → Markdown)

## Why

The novel cluster needs to ingest large source corpora (hundreds of research
docs, beta-reader feedback, story bibles) and research reports authored in
Google Docs. The orchestrator can read them via `mcp__Google_Drive__*` today,
but each call returns the body in the tool result — N docs at K tokens each
means N×K tokens land in main context whether the orchestrator reads them or
not. That's the moat for a research corpus: usable when small, broken when
large.

The agency answer is **context isolation via subagent dispatch**: a verb
prepares the dispatch contract (prompt + tools + dest path); the orchestrator
runs a Claude Code subagent with the Google Drive MCP tools; the subagent
fetches, writes to disk, and returns *only* `{path, bytes, lines, sha256,
title}`. A sibling verb records the `Artefact(kind="ingested-source")` with
PRODUCES + SERVES edges. Body never crosses back.

The verb itself stays pure (no I/O, no MCP dependency) — it just composes the
dispatch contract — so unit tests don't need network. The MCP call lives
inside the subagent's throwaway context, which is exactly what subagent
dispatch is for.

## Done When

- [ ] **`research.ingest_gdoc(intent_id, source, dest=None) -> dispatch_contract`**
      — pure verb. Resolves `source` (URL or file_id) to a file_id; computes
      default `dest` (`.agency/sources/gdoc-<id>.md` if None); returns the
      dispatch contract:
      ```python
      {
          "action": "dispatch_subagent",
          "prompt": "<full prompt for the Agent tool>",
          "tools": ["mcp__Google_Drive__download_file_content",
                    "mcp__Google_Drive__get_file_metadata",
                    "Write", "Bash"],
          "model": "haiku",
          "dest": ".agency/sources/gdoc-<id>.md",
          "file_id": "<id>",
          "after": {
              "verb": "research.record_ingested_source",
              "kwargs": {"intent_id": "...", "source_url": "...", "dest": "..."},
          },
      }
      ```
      Records nothing yet; the dispatch hasn't happened.
- [ ] **`research.record_ingested_source(intent_id, source_url, dest, bytes, lines, sha256, title) -> {artefact_id}`**
      — effect verb. Records `Artefact(kind="ingested-source", source_url,
      path, bytes, lines, sha256, title)`; links `SERVES` to intent_id and
      `PRODUCES` (intent → artefact). Idempotent on `(intent_id, sha256)`:
      a second call with the same sha returns the existing artefact_id.
- [ ] **URL resolution**: accepts `https://docs.google.com/document/d/<ID>/...`,
      `https://drive.google.com/file/d/<ID>/...`, and bare file_ids. Invalid
      input returns a typed error `{error: "INVALID_SOURCE", ...}` — no
      partial state.
- [ ] **Subagent prompt** is the load-bearing artifact. Three invariants:
      1. **Structured-return contract**: the prompt mandates the subagent
         output a single JSON line `{"path", "bytes", "lines", "sha256",
         "title"}` and explicitly forbids echoing the doc body.
      2. **Tool budget**: only the 4 named tools — no Read, no Grep — so a
         leak via subagent reading-back is structurally impossible.
      3. **Write-then-stat pattern**: subagent calls
         `mcp__Google_Drive__download_file_content` with `mimeType="text/markdown"`,
         pipes the body to `Write` at `dest`, then computes sha256 + line
         count via Bash (`shasum -a 256 $dest` / `wc -l $dest`), then gets
         title via `mcp__Google_Drive__get_file_metadata`.
- [ ] **No network in the verb**: `research.ingest_gdoc` has zero I/O. Tests
      run without the Google Drive MCP installed; they assert the prompt
      shape, dest computation, file_id extraction, and callback contract.
- [ ] **Provenance moat preserved**: `analyze.graph` after a successful
      ingest shows the new `ingested-source` Artefact serving the intent.
- [ ] Drift check clean (`scripts/check-drift`).
- [ ] `TODO.md` row added; "Drafted — novel follow-up wave" row updated to
      include 126.

## Design notes

- **Why two verbs, not one**: the dispatch step is the orchestrator's
  responsibility — a verb returning a "go dispatch this" contract is the
  same shape as `delegate.dispatch_decision` returning a recommendation.
  The second verb closes the loop with provenance. Single-verb design
  would either embed the Agent tool dispatch in Python (wrong abstraction
  layer) or pollute context with the MCP call.
- **Why `research` cap**: source ingestion is what `research` does. The
  cap already has `lead/specialist/verify`; `ingest_gdoc + record_ingested_source`
  rounds out the corpus-building motion. **Zero engine edits.**
- **Batch later**: a batch verb is N parallel invocations of the contract;
  the orchestrator dispatches N Agent calls in one message. No special
  surface needed in v1 — defer until the first 50-doc ingest reveals
  what's actually awkward.
- **NCC binding**: `novel.dispatch_novel_research` can chain to
  `research.ingest_gdoc` for the source-fetching half of its motion.
- **Open-set traversal**: `ingested-source` Artefacts are queryable via
  `analyze.graph` + the future `ctx.neighbors` (Spec 125) by edge
  `PRODUCES` to enumerate the corpus.

## Open questions

1. **Default dest dir**: `.agency/sources/` (recommended; gitignored)
   vs `.agency/research/sources/` (more nested)? — Recommend `.agency/sources/`
   so non-research callers (raw doc ingest) work naturally.
2. **Model pin in the contract**: `haiku` (mechanical fetch + write)
   recommended. The orchestrator MAY override; the contract records the
   recommendation, not a hard constraint.
3. **Idempotence key**: `(intent_id, sha256)` recommended (same doc fetched
   twice under the same intent → same artefact). An alternative is
   `(intent_id, source_url)` — but the URL can survive a content change.
   sha256 is the honest key.

## Followup

(Populated when the PR ships.)
