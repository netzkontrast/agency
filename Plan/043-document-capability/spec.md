---
spec_id: "043"
slug: document-capability
status: draft
last_updated: 2026-06-02
owner: "@agency"
depends_on: [016, 017, 020, 023, 040, 042]
affects:
  - agency/capabilities/document/__init__.py            # NEW heavy capability
  - agency/capabilities/document/_main.py
  - agency/capabilities/document/_render.py             # graph → markdown projection
  - agency/capabilities/document/_explain.py            # code segment → educational text
  - agency/capabilities/document/_index_repo.py         # the 94%-reduction repo briefing
  - agency/capabilities/document/_templates.py          # rendering templates per kind
  - skills/repo-briefing/SKILL.md                        # walker for index_repo
  - skills/repo-briefing/references/template-shapes.md
  - tests/test_document_render.py
  - tests/test_document_explain.py
  - tests/test_document_index_repo.py
estimated_jules_sessions: 2
domain: meta
wave: 2
closes_doctrine_gap_for: [017]
informs: [044]
---

# Spec 043 — `document` Capability (Graph-Native Rendering & Briefing)

## Why

Two unrelated-looking problems share a substrate:

1. **Spec 017** (graph-native dogfood ledgers) — agency's doctrine says
   "the graph is the store; files are a rendered view" (`CLAUDE.md`
   Rule #2). Today `agency/install.py` writes files directly, and
   `dogfood.collect` parses markdown. The fix needs **a render verb**
   that emits markdown from the graph on demand.
2. **`sc-index-repo`** — SuperClaude ships a command that produces a
   single `PROJECT_INDEX.md` capturing the whole repo's structure in
   ~3K tokens (vs. the 58K of a naive scan). That's a 94% reduction
   amortising across ≥10 sessions. Agency has no equivalent. The
   user-facing value is enormous.

Both reduce to the same shape: **deterministic projection from structured
data (graph or filesystem) into a token-efficient markdown artefact**.
This spec ships them as **one capability** (`document`) with three verbs:

- `document.render(scope, intent_id?) -> str` — projects a slice of the
  graph (e.g. `scope="install-artefacts"` or `scope="reflections"`) into
  markdown. The single source of truth for any "render the graph"
  request. **Closes Spec 017 §"Open Question 1"**: returning payloads
  enforces separation; the caller decides whether to write to disk.
- `document.explain(target: str, depth: str = "standard") -> str` —
  reads a Python module / function / class and emits an educational
  explanation. Depth `brief | standard | deep` mirrors the adaptive-
  disclosure pattern. Subagent-dispatchable for `deep` on heavy targets.
- `document.index_repo(path: str = ".", apply: bool = False) -> dict` —
  walks the repo, records a `RepoIndex` node, returns the rendered
  PROJECT_INDEX.md text (and writes it to `apply=True` per the
  graph-canonical doctrine). The 94%-reduction goal: ≤ 3000 cl100k
  tokens for a 50-file repo.

The capability is **not** about generating SKILL.md / README.md / API
docs from scratch (the `develop.scaffold_*` family + the
plugin-development skill do that). It's about **rendering existing
structured state** into a token-economical view.

## Done When

### Folder-form capability

- [ ] `agency/capabilities/document/` exists with the scaffolded
  skeleton, marker on line 1 of `_main.py`.
- [ ] `plugin.lint_capability("document")` returns `ok=True` in block mode.

### `document.render` (the graph→markdown projection)

- [ ] Verb signature: `render(scope: str, intent_id: str = "",
  format: str = "markdown") -> dict` returning
  `{"content": str, "tokens": int, "node_count": int, "scope": str}`.
- [ ] Supported scopes (v1) — each with a **fixed output schema**
  (Wiegers — every scope's output shape is contract-pinned, not vibes):
  - `"install-artefacts"` — `Reflection` nodes where `kind=install-
    artefact`. Schema: H1 "Install artefacts"; one H2 per artefact
    sorted by `name`; H2 body = fenced code block with rendered `body`
    + italic footer `<vfrom> · <id>`.
  - `"reflections"` — recent Reflections, optionally filtered by
    `intent_id`. Schema: H1 "Reflections (intent=<id|all>)"; one H2
    per Reflection sorted newest-first by `vfrom`; H2 body = `text`
    truncated to 500 chars + italic header `scope: <scope>`.
  - `"provenance"` — per-intent provenance brief. Schema: H1 "Intent
    <id> provenance"; H2 "Acceptance" (the intent's acceptance line);
    H2 "Invocations" (markdown table: timestamp | verb | role |
    duration_ms); H2 "Artefacts" (markdown table: kind | id | size).
  - `"capability-catalogue"` — engine's capability map. Schema: H1
    "Capability catalogue"; H2 per capability sorted by `name`; H2
    body = bullets `<verb>` (brief slice + role tag); footer counts
    (capabilities, verbs).
  All schemas are fixture-tested in `tests/test_document_render.py`.
- [ ] Format: `"markdown"` (v1). `"json"` and `"text"` deferred.
- [ ] Token counts are computed via `tiktoken` (cl100k) — the same
  tokenizer Spec 023 uses.
- [ ] Render is a **transform** (pure; no graph writes). Caller chooses
  whether to write to disk.

### `document.explain` (code → educational text)

- [ ] Verb signature: `explain(target: str, depth: str = "standard",
  intent_id: str) -> dict` (role `act` — emits a Reflection of
  `kind=explanation`). Returns `{"reflection_id": str, "content": str,
  "tokens": int}`.
- [ ] `target` is one of:
  - A file path (`agency/capabilities/reflect.py`)
  - A `module.symbol` reference (`agency.capabilities.reflect.recall`)
  - A `module` (`agency.capabilities.reflect`)
- [ ] `depth` ∈ `{brief, standard, deep}`:
  - `brief` — 1–2 sentences (≤ 200 tokens) — what does this do?
  - `standard` — 1 paragraph + signature (≤ 600 tokens) — what + how + when.
  - `deep` — full educational walkthrough (≤ 2500 tokens) — what + how +
    when + why this design + alternatives + caveats. **Subagent-
    dispatchable** at the `deep` level (Spec 040 S1:tokens signal fires).
- [ ] The verb itself does NOT call an LLM — it composes deterministic
  features (signature, docstring brief-slice, ast-derived call-sites,
  Reflection nodes via `reflect.recall_semantic`) and emits a structured
  template. The "education" comes from the SHAPE, not from generation.
- [ ] Rendered explanation includes a "see also" section sourced from
  `reflect.recall_semantic(query=<symbol>)` — pulls prior reflections
  about the same symbol into the explanation.

### `document.index_repo` (the 94%-reduction repo briefing)

- [ ] Verb signature: `index_repo(path: str = ".",
  apply: bool = False, max_tokens: int = 3000, intent_id: str) -> dict`
  returning `{"index_id": str, "content": str, "tokens": int,
  "files_scanned": int, "writeup": str}`.
- [ ] Output structure (markdown; deterministic template):
  ```
  # Project Index — <repo name>

  ## Substrate
  - language: …
  - top-level: <dirs>
  - test runner: <inferred>

  ## Macro-structure
  - <package> (<file count>) — <one-line synthesis from each module's brief slice>
    - <subpackage> — <one-line>
    - …

  ## Entry points
  - <bin/entry script or [project.scripts]>

  ## Notable patterns
  - <auto-detected: capability folder, plugin manifest, MCP config>

  ## Recent activity (intent_id-scoped if provided)
  - <newest 5 Reflection nodes, scope=technical or project>
  ```
- [ ] The synthesis reads **first-sentence brief slices** from module
  docstrings (Spec 023 substrate — already populated for every agency
  module). No LLM generation; deterministic projection.
- [ ] `apply=True` writes to `${target}/PROJECT_INDEX.md` AND records a
  `RepoIndex` node with `{path, content_sha, token_count, generated_at}`.
- [ ] `max_tokens=3000` is enforced (the briefing truncates with an
  `... (N modules omitted)` marker rather than exceeding budget).
- [ ] Self-test: on the agency repo, `document.index_repo()` produces a
  briefing under 3000 cl100k tokens.
- [ ] **Dispatch via delegate.dispatch_decision** (Spec 040) — the verb
  ALWAYS hits the S1:tokens signal because the raw scan is ~50K tokens
  and the return is ~3K. The implementation runs the scan in a subagent
  by construction (the orchestrator never sees the raw scan).

### Skill walker

- [ ] `skills/repo-briefing/SKILL.md` exists with the standard frontmatter.
- [ ] Lifecycle template on `DocumentCapability.ontology.skills["repo-briefing"]`
  has four phases:
  ```
  scope → scan → render → publish(hard)
  ```
  `scope` picks the path + max-tokens; `scan` calls `index_repo` (subagent
  dispatch via Spec 040); `render` returns the markdown; `publish`
  optionally writes the file (`apply=True`).

### Ontology fragment

- [ ] Nodes: `RepoIndex` (`required: [path, content_sha, token_count,
  generated_at]`). Reflection-kind extensions are NOT new node types
  — they're constrained by the existing `kind` field on Reflection
  (Spec 017 will add `kind` as an enum; this spec depends on 017
  landing it).
- [ ] Edges: `INDEXES` (RepoIndex → Workspace or implicit-path). No new
  edge for explanations — they reuse `OBSERVED_DURING` like all
  Reflections.
- [ ] Schemas: `repo-index` artefact `[path, content_sha, token_count]`.
  `explanation` artefact `[target, depth, content]`.
- [ ] Skills: `repo-briefing` (walker above).

### Tests

- [ ] `tests/test_document_render.py` — for each of the 4 v1 scopes,
  assert that the rendered markdown contains the expected sections and
  the token count matches `tiktoken` cl100k.
- [ ] `tests/test_document_explain.py` — for each depth level, assert
  the token budget is respected; assert `reflection_id` is recorded.
- [ ] `tests/test_document_index_repo.py` — run against the agency repo
  itself; assert ≤ 3000 tokens; assert the writeup names every top-level
  capability.

## Design

### Render is the doctrinal fix for Spec 017

Today `agency/install.py` writes files directly — graph-vs-file misuse,
weakness W1+W2 in `Plan/015-architecture-review/ARCHITECTURE-REVIEW.md`.
Spec 017 documents the fix; this spec ships the **render primitive that
makes the fix viable**. The flow after both ship:

```python
# agency/install.py (post-Spec-017 + post-Spec-035)
for artefact in MANIFESTS:
    rid = memory.record("Reflection", {
        "scope": "technical", "kind": "install-artefact",
        "name": artefact.name, "body": artefact.content,
    })
    memory.link(rid, intent_id, "PRODUCES")
    if apply:
        content = document.render(scope="install-artefacts",
                                   intent_id=intent_id)["content"]
        write_disk(artefact.path, content)
```

The graph is canonical; disk is a render. Re-running `install` is
idempotent because the render is a pure function of the graph state.

### Explain is composition, not generation

`explain` is the strongest demonstration of the agency-native
"composition > generation" pattern. The educational value comes from
**arranging deterministic features**:

```
explain("agency.capabilities.reflect.recall", depth="standard")
└─ extract: signature from inspect.signature
└─ extract: brief slice from parse_slices(docstring)["brief"]
└─ extract: callers via ast walking
└─ pull: prior Reflections via reflect.recall_semantic("reflect.recall")
└─ template: signature + brief + "called from: <files>" + "see also: <reflections>"
```

No LLM. The structure IS the explanation. `deep` adds one more
recursion (caller-of-caller, more reflection context).

This is also the answer to "what does subagent-dispatch buy here?" — at
`deep`, the extraction walks many files; the subagent runs the walk
without polluting the main context, then returns the rendered string.

### index_repo's 94%-reduction mechanism

The 58K → 3K reduction comes from three things:

1. **Brief slices over full docstrings** — Spec 023 already gives every
   module a ≤120-char first sentence. The briefing reads only those.
2. **Macro-structure over file-by-file listing** — a package becomes
   `(<count>) <synthesis>`, not 30 file paths.
3. **Subagent dispatch** — the orchestrator never loads the raw scan.
   The scan happens in a subagent; only the rendered briefing crosses
   back (Spec 040 S1:tokens signal).

This is the literal generalisation of sc-index-repo. Agency's version
**adds** the graph-recording so the briefing is durable across sessions
(re-running on unchanged code returns the cached `RepoIndex` node
content — content_sha comparison).

### Capability-catalogue rendering (the agency.install slash-command path)

Today `agency.install` regenerates `skills/help/SKILL.md` from the
capability registry. With `document.render(scope="capability-catalogue")`,
that regen flow becomes:

```python
content = document.render(scope="capability-catalogue")["content"]
write_disk("skills/help/SKILL.md", content)
```

One source of rendering logic; `install` becomes a thin orchestrator.

### Why depth=deep dispatches a subagent (vs. inline)

`brief` and `standard` return < 800 tokens of context they read; safe
inline. `deep` walks the AST, pulls callers, semantically searches
Reflections — easily 5–15K tokens of intermediate context. The
orchestrator only needs the final ≤ 2500-token explanation; everything
else is wasted budget. Per Spec 040 S1:tokens, dispatch wins.

## Files

- **Scaffold first** via `develop.scaffold_capability(name="document",
  kind="heavy")`.
- **Create:**
  - `agency/capabilities/document/__init__.py`
  - `agency/capabilities/document/_main.py`
  - `agency/capabilities/document/_render.py`
  - `agency/capabilities/document/_explain.py`
  - `agency/capabilities/document/_index_repo.py`
  - `agency/capabilities/document/_templates.py`
  - `skills/repo-briefing/SKILL.md`
  - `skills/repo-briefing/references/template-shapes.md`
  - `tests/test_document_*.py` (3 files)
- **Modify (after this lands):**
  - `agency/install.py` — switch to render-then-write (Spec 017 closes
    too).

## Open Questions

1. **Should `document.render` support a `since: timestamp` query?**
   The bi-temporal graph (`as_of`) makes "render the install-artefacts as
   of yesterday" possible. v1 ships current-state only; v2 adds
   bi-temporal projection.
2. **PROJECT_INDEX.md location.** SC writes it at repo root. Agency
   should write under `.agency/` (the graph DB's home, already in
   .gitattributes per Spec 020) to keep the repo root clean. Or write
   to `docs/` per CLAUDE.md doctrine. Lean: `.agency/PROJECT_INDEX.md`
   for the canonical copy + a thin pointer in `docs/`.
3. **`explain` LLM optionality.** Some users will want a generated
   prose paragraph at `deep`. Should `[project.optional-dependencies]`
   carry a `[document-llm]` extra that adds a `prose_paragraph` field?
   v1 says no — the deterministic walkthrough is sufficient; LLM
   prose is the user's choice via their own tooling.
4. **Caching by content_sha.** v1 always re-runs `index_repo`. A cache
   keyed on the directory tree's combined sha would let re-runs be O(1).
   Defer to v2 unless users complain.

## Evidence

- Spec 017 — the graph-vs-file weakness this spec closes the render-side
  of. Spec 017 § "Open Question 1" → resolution: return payloads, write
  via render.
- sc-index-repo (PR #17 subagent report) — the 94%-reduction pattern
  generalised.
- sc-document + sc-explain — the explain/render shape (agency removes
  the persona injection and replaces it with composition over the
  agency-graph).
- Spec 023 (adaptive disclosure) — brief slices ARE the input to
  index_repo and explain.
- Spec 045 (reflect.recall_semantic) — `explain` calls it for the "see
  also" section.

## Followup — Implementation Status (2026-06-02)

**Verdict:** Not started — spec drafted; agency has no rendering
capability.

### Done
- Substrate: `agency/render.py::parse_slices` + Spec 023 brief slices
  already populate every module — `index_repo` and `explain` only need
  to read them.
- The `_jules_reference.md` pattern (a markdown file colocated with the
  jules capability) shows how the capability already structures rich
  documentation; this spec generalises that.

### Still to implement
- Folder + 5 modules.
- Three verbs (render transform, explain act, index_repo act).
- The walker template + SKILL.md + reference.
- Three test files.
- agency.install switch (after both 017 and 035 ship).

### Refinement needed
- Open Question 2 (PROJECT_INDEX.md location) needs a one-line policy
  call before v1.
- Open Question 1 (bi-temporal projection) defers to v2 cleanly.
