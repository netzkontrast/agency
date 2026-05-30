# JULES_RESEARCH_PROTOCOL.md

> **Audience:** a Jules research/critique agent working on the **Agency** plugin
> repo (`netzkontrast/agency`). This is the contract for the PR1 review effort.
> It adapts `the-agency-system`'s `Plan/JULES_PROTOCOL.md` from *implementation*
> to *exhaustive research + spec authoring*. Every agent prompt defers to it.

## 0. Mission

PR1 is the complete Agency plugin (a FastMCP "code-mode" engine over one
bi-temporal graph). Your job is to **ingest the whole of PR1 and its source
context, dissect it with a named critical-thinking method, and produce concrete
improvement artifacts** — more/better templates, schemas, and object-oriented
design. You do **not** modify the plugin. You write only under your own research
directory. Disciplined, fully-evidenced output outranks fast output: a thorough,
cited critique landing in eight hours beats a plausible-looking one in two.

## 1. The four research gates (run in order, do not skip)

### Gate 1 — Ingestion completeness (before writing any finding)

This is a **context-heavy** task. You may not critique what you have not read.

1. Enumerate the full file set in scope: `git ls-files` for the work repo and
   `find ~/work/vendor/<repo> -type f` for each cloned source. Save the lists.
2. Maintain an **ingestion ledger** at `research/<agent>/_ingest.md`: one row per
   file in your scope — `path · read? (y/n) · one-line summary`. You may not mark
   Gate 1 passed until every in-scope file is `y`.
3. Read **recursively and exhaustively**, the way a research agent ingests a
   corpus: breadth-first over the tree, then depth on the files your method flags
   as load-bearing. Read code AND its tests AND its docs/specs — they triangulate
   intent. Re-read a file before citing it (the bytes, not your memory of them).
4. Batch large trees (read many files per `run_in_bash_session`/`read_file` pass)
   and record each in the ledger as you go. Do not sample-and-guess.

### Gate 2 — Evidence

Every claim is backed by a citation, never an assertion:

| Claim about… | Required citation |
|---|---|
| PR1 code/docs | `path:line` in the work repo (quote the relevant lines) |
| A source repo | `vendor/<repo>/path:line` **+** the repo URL and the cloned commit SHA |
| A framework fact | the doc URL + the version you verified |

A finding without a citation is an opinion; delete it or cite it.

### Gate 3 — Synthesis (artifacts, not advice)

Your deliverables are **concrete artifacts**, not vague recommendations. "Add a
result envelope" is advice; a `ToolResult` dataclass sketch with field types, a
before/after of one verb, and the migration cost is an artifact. Every proposal
includes: the concrete shape (code/schema/template), one worked example, a cited
OSS or in-repo precedent, and the trade-off you are accepting.

### Gate 4 — Self-review (before requesting merge)

End your top finding doc with a `## Self-Review`:
1. **Coverage:** paste your ingestion-ledger tally (`N of M files read`). If < 100%,
   list what you skipped and why.
2. **Residual risk / unknowns:** what you could not verify.
3. **Method reflection:** one sentence on what your assigned method surfaced that a
   plain read would have missed.

## 2. Working in the Agency repo

- **Work repo & branch:** clone `netzkontrast/agency` at branch
  `claude/extract-agency-plugin-o4JRc` (this is PR1's head). Open your PR **into
  that same branch** (`base = claude/extract-agency-plugin-o4JRc`), never `main`.
- **Spatial awareness first:** `list_files` + `read_file` before any write.
- **Write only under `research/<your-agent-dir>/`.** Never modify `agency/`,
  `tests/`, `docs/`, or another agent's `research/*` directory. If `git status`
  shows a change outside your dir, back it out before submitting.
- **Commits:** imperative, ≤72-char subject; reference your agent id.
- **Publish:** when the four gates are green, publish your work via the standard
  flow as **one ready PR** (not draft) into the PR1 branch. After publishing, stop
  — do not poll or re-verify.
- **Ambiguity:** if a prompt sentence has two materially different readings, state
  both in your findings and proceed on the more conservative one; do not stall.

## 3. Source repositories (read-only)

See [`SOURCES.md`](SOURCES.md) for the candidate repos + clone commands. **You
decide which you can cleanly check out:** attempt each clone; if one fails (auth,
404, network), note `[BLOCKED: source <name>]` in your PR body with the exact
error and **continue with the sources you do have**. Do not stall the whole
work-unit on one unreachable source.

- Clone read-only into `~/work/vendor/<name>/` via `run_in_bash_session`. Never
  inside the work repo. Pin with `--depth=1 --branch=<ref>` where given.
- **Never commit vendor files** into the Agency repo. Cite them by URL + SHA.
  If `git status` shows anything under `vendor/`, you have erred — back it out.

## 4. Recursive ingestion method (how to read "everything")

Treat the corpus the way a deep-research agent would:

1. **Map** — build the file tree(s) and a ledger; group files by subsystem.
2. **Sweep** — read every file once, breadth-first, summarising each into the
   ledger (one line). This is the coverage guarantee.
3. **Dive** — for files your method flags as load-bearing (the engine, the
   capability base, the ontology, the relevant specs), read deeply and cross-link
   to tests and docs.
4. **Triangulate** — reconcile code ↔ tests ↔ docs/specs; contradictions are
   findings.
5. **Synthesise** — produce the artifacts in §Gate 3, citing as you go.

Do not begin synthesis until the Sweep is complete and the ledger shows full
coverage of your scope.

## 5. Anti-patterns (do NOT)

1. Critique a file you have not read (Gate 1 violation).
2. State a finding without a `path:line` / URL+SHA citation.
3. Deliver advice instead of a concrete artifact.
4. Write outside your `research/<agent>/` directory or commit vendor files.
5. Target `main` or force-push.
6. Stall the entire work-unit because one source repo would not clone — note it
   and proceed.
7. Treat your own session `state=COMPLETED` as the deliverable. The deliverable is
   the published PR with your artifacts. Publish via the standard flow.

## 6. Required PR body sections

`## Agent` (which work-unit) · `## Sources used` (repos + SHAs, plus any
`[BLOCKED: source …]`) · `## Coverage` (ledger tally) · `## Artifacts` (the files
you added under `research/<agent>/`, with a one-line each) · `## Self-Review`.
