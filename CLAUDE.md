# agency — Claude Code plugin

This repo IS the plugin: a **FastMCP engine + bi-temporal GraphQLite graph**,
exposing exactly **`search` · `get_schema` · `execute`** as the wire contract.
Four concepts (Intent · Capability · Lifecycle · Memory) on one substrate.

> **Read first:** [`docs/vision/GOALS.md`](docs/vision/GOALS.md) (why),
> [`docs/vision/CORE.md`](docs/vision/CORE.md) (canon),
> [`AGENTS.md`](AGENTS.md) (operational), [`AGENCY_PROTOCOL.md`](AGENCY_PROTOCOL.md)
> (remote-agent doctrine).

> **ALWAYS use CodeGraph to discover and find code symbols (MANDATORY).** This
> repo is indexed by CodeGraph (a `.codegraph/` directory exists; run `codegraph
> init` once if it does not). For EVERY code lookup — "where is X", "what is X",
> "how does X work", any symbol / call-path / blast-radius question, and BEFORE
> editing an unfamiliar symbol — reach for CodeGraph FIRST, never grep / find /
> Read as the opening move. `codegraph_explore "<question or symbol names>"` (MCP)
> or `codegraph explore "<…>"` (CLI) answers most questions in ONE call — it
> returns the relevant symbols' verbatim source PLUS the call paths between them;
> treat that source as already read (don't re-grep to "confirm" it).
> `codegraph_node` / `query` / `callers` / `callees` / `impact` round it out (the
> CLI mirrors every MCP tool). grep / Glob / Read are the FALLBACK only — when
> CodeGraph is inactive (no `.codegraph/`) or for non-code text (docs, specs,
> config). When you reach for grep on a code question and `.codegraph/` exists,
> stop — that is the reflex this rule exists to correct. The full token-efficient
> guide travels on demand via `develop.reference("codegraph")`.

## Three rules for working in this repo

1. **Dogfood the engine — MCP-first when available.** When your harness has
   `mcp__plugin_agency_agency__{search,get_schema,execute}` (i.e. Claude
   Code with this plugin installed), use those tools directly — no
   subprocess hop, same per-project graph. The bash CLI (`python -m
   agency.cli execute` via `bin/agency`) is the fallback for Jules /
   no-MCP harnesses. Either surface chains tools inside the sandbox;
   only the return crosses back. Don't write code that bypasses the
   substrate.

2. **Graph and files are interconnected peers — the Document is where they
   meet (Spec 292).** The graph is the queryable spine; markdown files are an
   editable PEER surface that round-trips back into it. Edits flow BOTH ways:
   `document.render` projects graph→file; `document.ingest` / `document.sync`
   flow file→graph as append-only `DocRevision`s. Reconciliation is
   **keep-both, bi-temporal** — a graph-authored and a file-authored version
   coexist; latest `recorded_at` wins on read, history is retained (nothing is
   overwritten). The binding is a stable anchor — `<!-- agency-node: <id> -->`
   on the file's first line — naming the `Document` node that IS the file's
   identity. The **Document is the universal convergence artefact**: the point
   where the substrate's layers come together — datalayer (it's a graph node),
   templates + schemas + ontology (a Document binds its `template`/`schema` and
   `CONFORMS_TO` a Schema), **prompt** (every file is also a prompt —
   `ingest` scores the body via `prompt.audit`), and the four concepts
   (`document.session` renders Intent · Capability · Lifecycle · Memory for a
   Session). So: still prefer `reflect.note` over hand-writing parse-bait
   markdown — but a file edited on disk is no longer lost; `document.sync` it
   back. Canon/doctrine docs (CORE / AGENTS / AGENCY_PROTOCOL) remain
   file-authoritative — under keep-both that just means their file edits are
   always the latest valid fact.

3. **Decide before dispatching.** Walk the `dispatch-decision` skill
   (`skills/dispatch-decision/` + `delegate.ontology.skills`) before any
   subagent / Jules / future-MCP-client dispatch. The heuristic is the
   **eleven-signal** rule (Spec 040 §"eleven signals") with **two budget
   models** (local vs. Jules):
   - Work-shape signals: S1 (return tokens ≥ 5000), S2 (≥ 4 unfamiliar
     files), S3 (repeated exploration), S4 (≥ 3 parallel siblings),
     S5 (≥ 15 min wall-clock).
   - Role/safety: S6 (mutates — disqualifier without provenance),
     S7 (read-only amplifies), S8 (driver_hint as tie-breaker).
   - Cost-model: S9 (context_overlap ≥ 0.7 → re-load tax), S10
     (cache_warmth ≥ 0.6 → 10% cost), S11 (`local_budget_relevant=False`
     → Jules path; relaxes S1/S9/S10).
   Two disqualifiers run BEFORE positive scoring. Otherwise: any positive
   signal → dispatch (driver picked by the matrix); none → inline.

4. **Keep `TODO.md` current — MANDATORY in every spec-touching commit.**
   `TODO.md` in the repo root is the **binding spec status index** —
   verdict per spec (Shipped / Partial / Not started), one-line summary,
   blocker / next step. **No spec-touching commit ships without updating
   the corresponding row** — this is a HARD rule, not a soft preference.
   Failure to update IS a doctrine violation that future audits will
   flag. The same commit MUST update `TODO.md` when it:
   - ships a spec (status flip → Shipped — also flip Verdict-counts
     at top + add the new row entry to "Suggested next 5" if applicable),
   - makes meaningful progress on one (Not started → Partial; note WHAT
     is now done + WHAT remains in the "Blocker / Next step" column),
   - opens a new spec (add row),
   - closes / supersedes / cancels one (note in row),
   - renumbers (rare; only after a naming collision on merge).

   `TODO.md` ONLY carries the cross-spec roll-up — verdict + one-line +
   pointer. Per-spec deep state (test counts, file:line evidence, verbatim
   Done / Still / Refinement) lives in each `Plan/NNN-…/spec.md`'s
   `## Followup — Implementation Status (…)` section. No drift between
   the two; `TODO.md` rolls up, the Followup section grounds.

7. **Test behaviour, not implementation** — Gherkin acceptance scenarios
   (`tests/acceptance/`, `pytest-bdd`) are the contract; no unit tests on
   internals; structural cleanliness is a review concern. Canon:
   [`docs/vision/TESTING.md`](docs/vision/TESTING.md). Regression runs in CI,
   not locally (Spec 053; CI may be disabled during a large refactor while the
   reviewer gates via the acceptance suite). Per user directive (2026-06-03):
   - Locally, run **only** focused slices (`scripts/test-cap <marker>`,
     `scripts/test-changed`) — typically < 30 seconds. Full-suite
     wall-clock is too expensive in a tight TDD loop.
   - The **full regression** (`pytest -n auto -m "not e2e"` + E2E on
     tag) runs in GitHub Actions on every PR + push to `main`. The
     workflow is `.github/workflows/test.yml`.
   - When pushing a feature branch, **always subscribe to PR activity**
     via `subscribe_pr_activity` so CI failures and review comments
     arrive as session notifications (no polling, no manual recheck).
     The subscription is the default, not opt-in.
   - If CI is red, the watching session investigates + fixes
     autonomously (per the GitHub Integration §"PR Activity Events"
     handling rules above). Push fixes; let CI re-run; reply only
     when the loop converges or a question genuinely needs the user.

6. **Address drift before committing.** Spec 054 ships TWO guardrails
   for keeping the open-set substrate (capabilities, skills, ontology
   enums, extras) in sync across the ~9 places code/docs depend on
   the set:
   - **Inline tags.** `# AGENCY-DRIFT: <topic>` at every site where
     code reads a set/list that changes with the capability surface.
     `grep -rn AGENCY-DRIFT agency/ tests/ scripts/` lists them all.
   - **Drift detection script.** `scripts/check-drift` (called by CI on
     every PR) runs install dry-run, capability-test-gap check, and
     tag inventory. Exit 0 = clean; 1 = drift detected.
   When adding a new capability / extra / substrate tool, run
   `scripts/check-drift` BEFORE commit. Failure to do so is a doctrine
   violation; future audits flag it.
   - **Doc drift.** The engineering docs live in [`docs/`](docs/) (start at
     `docs/README.md`; `docs/vision/reference/` is the module-by-module
     reference). Hand-written docs carry a `<!-- doc-source: … -->` marker
     naming the code/specs they describe; `scripts/check-doc-drift` hashes
     those sources and flags any doc gone stale (`--update` re-stamps,
     `--strict` flags unmarked). The capability reference
     (`docs/guide/capabilities.md`) is GENERATED — `scripts/gen-capability-docs`,
     never hand-edit. When you change a documented module, run
     `scripts/check-doc-drift`, review what it flags, and update the page.

5. **Check cluster coherence before adding a verb / skill.** Spec 047
   (cluster-integration master) maps the 13 SDLC+meta clusters onto the
   agency surface. Every new verb / skill / substrate tool lands in one
   of those clusters. Before adding, find the cluster's section in
   `Plan/047-cluster-integration/spec.md` and check the integration
   pattern + coherence interactions — does your addition extend the
   pattern, or break it? When the cluster's integration plan grows past
   ~150 lines OR you trigger ≥ 3 named cross-cluster decisions, promote
   it to a standalone spec (Spec-015→017/018/019 precedent). The master
   is the source of truth UNTIL promotion; the promoted spec wins
   thereafter.

8. **No hardcoded values — code (and tests) solve the problem, they don't
   gate a fixed solution.** Prefer COMPUTED / derived / discovered values
   over magic numbers and frozen snapshots. A test that pins a live-derived
   number (e.g. "the registry has exactly 73 verbs", "the payload is 1503
   tokens") breaks on every legitimate change and forces a hand-edit — it
   gates a fixed surface instead of guarding behaviour. Assert
   **invariants + relationships** (`wire_tok > bare_tok * 2.5`; "the known
   collisions are a SUBSET of live collisions"; "the substrate set equals
   the documented six") and compute expectations from the live source, not
   a constant. Genuine **tunable budgets** (a name-token limit, a payload
   byte cap) are fine — they are documented config with a rationale, not a
   snapshot of the current state; keep them few, named, and overridable.
   When you catch yourself updating a magic number to make a test pass, stop
   and make the test flexible instead.

9. **Never delete content from the project index to fit a budget — MANDATORY.**
   `PROJECT_INDEX.md` (the `document.index_repo` / `develop index` briefing) is a
   GROW/APPEND artefact. When it is **SAVED** (`apply=True`), every module and
   section MUST survive — the saved index is **never truncated** to fit a token
   budget and **never** carries an "… omitted to fit token budget" marker. A
   dropped entry makes the index LIE about the tree, which is worse than a larger
   file. The `max_tokens` budget governs only a **preview** (`apply=False`); on
   save the index renders in FULL (`_index_repo.render(..., full=True)`). If a
   saved index ever shows an omission marker, that is a defect — regenerate it
   complete (`document.index_repo(apply=True)`) before committing.

   **Generalised — never silently truncate CAPTURED DATA (MANDATORY; user
   directive 2026-06-19).** The index rule is the special case of a wider law:
   captured data — hook **tool calls (pre/post)**, command output, stderr, stored
   provenance text — is stored/returned in **FULL**, never sliced to a char
   budget or head/tail-filtered before persisting. A dropped tail makes the
   record LIE about what happened. When a value is unusually large, **warn — do
   not cut**: route it through `agency/_capture.py::keep_full(value, label=…)`,
   which returns the full value and logs a size warning. NOT in scope (these are
   not "data" and keep their slicing): content-hash prefixes (`sha[:16]`), top-N
   list selection (`ranked[:10]`), and pure display width (a CLI help column).
   When you catch yourself writing `data[:N]` on a captured/stored string, stop
   and use `keep_full` instead.

10. **Use CodeGraph for EVERY code lookup — MANDATORY (when `.codegraph/` exists).**
    For ANY "where is X / what is X / how does X work", symbol, call-path, or
    blast-radius question — and BEFORE editing an unfamiliar symbol — reach for
    CodeGraph **first**, never grep/find/Read as the opening move.
    `codegraph_explore` (MCP) or `codegraph explore "<q>"` (CLI) answers most in
    ONE call: it returns the relevant symbols' **verbatim source + the call paths
    between them** — treat that source as already read (don't re-grep to
    "confirm" it). `codegraph_node`/`query`/`callers`/`callees`/`impact` round it
    out (CLI mirrors every MCP tool). grep/Glob/Read are the **fallback** — only
    when CodeGraph is inactive (no `.codegraph/` dir → indexing is the user's
    call) or for non-code text (docs, specs, config). The full token-efficient
    guide travels on demand via `develop.reference("codegraph")`; don't memorize
    it. When you reach for grep on a code question and `.codegraph/` exists, stop
    — that's the reflex this rule exists to correct.

## Field-tested heuristics (dogfooded — grounded in graph reflections)

Cheap checks that caught real failures during the 076→080 build-out. Pointers,
not prose — `analyze.graph` to read the originating reflections.

- **Dormant-surface audit.** Before trusting a pipeline, count its live triggers:
  `grep` the gate predicate, count satisfiers; **zero = dead code**. (031/032 emit
  shipped + tested but produced nothing — 0/15 caps declared `skill_doc`.) Extends
  to **edges** (Spec 125): a declared edge that nothing traverses is dormant
  surface; **declare an edge ⇒ traverse it via `ctx.neighbors(node_id, edge)`**.
  The anti-pattern is `find(label)`+Python-filter on a foreign-key prop while the
  edge sits idle — both are written, only the scan is read.
- **Derivability audit.** Authored metadata that duplicates an existing source is
  drift waiting to happen — **derive it** (rule 2 applied to docstrings). SkillDocs
  derive from the module docstring (`Use when:`/`Triggers:`/`Red flags:`); the
  overview/briefs/example are free. No literal.
- **Enforcement blast-radius.** Before flipping a bootstrap invariant, `grep
  'Engine('` for synthetic-object call sites and ship a documented bypass
  (`_require_skill_doc=False` for probes/fixtures).
- **Sourcing-model first.** Decide the source-of-truth BEFORE any N>5 file
  migration — re-sourcing 15 caps twice is the tax for skipping it.
- **Full suite on a migration.** A migration touches repo-wide invariant/inventory
  tests (`test_naming_audit` substrate set), not just the changed slice. Run all of
  it before declaring green; CI is the net, not the first check.
- **Read the graph:** `analyze.graph` (census + typed listing) is the query
  surface — code-mode exposes only `call_tool`; `memory_graph_provenance` drills
  one intent. Don't claim to "read the graph" by reading intents you already know.

**The drop-in-capability bar.** Add a folder under `agency/capabilities/<name>/` —
verbs + ontology + a docstring that *derives* its Agent Skill — and **nothing
else**, and agency gains a complete, discoverable, walkable, CLI-exposed,
MCP-wired, emittable capability. If adding a capability needs an edit anywhere
else, that coupling is the bug to fix.

## Surface (discoverable; don't memorize)

Capabilities self-register from `agency/capabilities/`. Skills live on
`<capability>.ontology.skills` (Lifecycle templates, CORE.md:47-62).
`python -m agency.cli search <kw>` lists both. Jules needs `JULES_API_KEY`
at call time; see `AGENCY_PROTOCOL.md`.

Domain capabilities live in `examples/` (e.g. third-party domain proofs),
loaded via `Engine(..., extra_capabilities=[…])` — the bootstrapping harness
stays minimal.

**Spec 094 doctrine exception:** the `music` capability graduated from
`examples/music.py` to `agency/capabilities/music/` as the substrate's
first user-facing creative-production application (a clustered Capability
bundle spanning lifecycle / lyrics / audio / catalogue / promo / research /
gates per Spec 093). It's auto-discovered like any core cap; the legacy
`examples/music.py` + `music_drivers.py` remain as deprecation re-export
shims for one spec cycle (removed by Spec 110). Music remains the
**reference clustered domain capability** — third-party domain caps still
land in `examples/`.

## How to use the agency MCP (preferred runtime — Spec 114)

The agency plugin is the **primary driver of the session**, not just a
tool. Default to its surface over raw tools.

**Discovery — agency MCP search ALWAYS beats ToolSearch:**

```python
# Find capabilities by query — works on the live verb graph:
await call_tool("mcp__agency__search",
                {"query": "<keyword>", "detail": "brief"})
# Get schemas for verbs you found:
await call_tool("mcp__agency__get_schema",
                {"tools": ["capability_<cap>_<verb>", ...]})
# Execute code-mode block chaining multiple call_tool calls (one return):
await call_tool("mcp__agency__execute", {"code": """
    welcome = await call_tool("agency_welcome", {})
    intent = await call_tool("intent_bootstrap", {...})
    # chain N more calls
    return {...}
"""})
```

Use `mcp__agency__search` for ANY "where is X" question before
`ToolSearch`. The agency surface is the live capability registry;
ToolSearch is the deferred-schema fallback only.

**Session-start protocol (Spec 114):**

1. `agency_welcome` — read the live capability list + DB path
2. `intent_bootstrap(purpose, deliverable, acceptance)` — every session
   serves an intent
3. Walk a discipline skill rather than improvising — `develop.brainstorm`
   for design work, `develop.write_spec` for spec authoring,
   `develop.implement` for code

**Verb-first action routing** — prefer the capability verb over raw tool:

| Action | Verb (preferred) | Raw fallback |
|---|---|---|
| Edit a spec / write a doc | (use Write/Edit but call `dogfood.observe` to record) | Write / Edit |
| Run tests | `develop.test(scope)` | Bash `pytest` |
| Search code | `mcp__agency__search` + `analyze.*` | Grep / Glob |
| Understand/locate CODE (symbols · calls · blast radius) | `codegraph_explore`/`node`/`search` · CLI `codegraph <cmd>` — guide `develop.reference("codegraph")` | Grep / Read |
| Web fetch | `research.fetch(url, query)` (when shipped) | WebFetch |
| Commit | `branch.commit_smart(message)` | Bash `git commit` |
| Push + PR | `branch.finish_branch(...)` | Bash + gh CLI |
| Dispatch subagent | `subagent.dispatch(...)` | Agent tool |
| Dispatch Jules | `jules.dispatch(...)` | (no fallback) |
| Critical thinking | `intent.<method>` (8 methods per Spec 091) | (do it in chat — but lossy) |

**Skills as session mode** — every walkable skill IS a Lifecycle
template. Walk via `develop.skill_walk(intent_id, name)`. The engine
delivers ONE phase at a time so context stays bounded.

**Why this matters** — actions through capability verbs auto-record
provenance (`Invocation` SERVES intent + `Artefact` PRODUCES edges).
Raw-tool actions don't. The provenance moat IS the moat; bypass it
and the session is one-shot.

## Code navigation — CodeGraph (when `.codegraph/` exists)

This repo is indexed by **CodeGraph** — a pre-built symbol / call-graph /
impact-radius index. For ANY "where/what/how does X work", call-path, or
blast-radius question, reach for it **BEFORE** grep/find/Read: `codegraph_explore`
(MCP) or `codegraph explore "<q>"` (CLI) answers in one call — treat the returned
source as already read, don't re-verify with grep. `codegraph node <sym|file>`,
`query`, `callers`, `callees`, `impact` round it out (CLI mirrors every MCP tool).
The **complete token-efficient guide is `develop.reference("codegraph")`** — the
heavy how-to travels on demand, never in the system prompt. No `.codegraph/`
dir → CodeGraph is inactive and indexing is the user's call (`codegraph init`).

## Dev

```bash
scripts/setup                # Spec 282 — venv + .[dev] (everything but torch); the default
scripts/setup --all          # also install the heavy sentence-transformers/torch recall backend (~2GB)
. .venv/bin/activate
python -m pytest -q          # full default suite (slow — ~4 min sequential)
python -m pytest -q -n auto  # parallel via pytest-xdist (Spec 053; ~1 min on 4 cores)
python -m agency.install     # regen the plugin install when capabilities change
```

`.[dev]` now self-references every LIGHTWEIGHT runtime extra
(`analyze` · `tokens` · `anthropic` · `publish`), so the default setup runs the
full suite with ZERO silently-skipped capability tests (Spec 282, user directive
2026-06-13). Only the heavy `recall` torch backend is opt-in via `.[all]`.
Manual equivalent: `python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"`.

Spec 053 — fast local feedback:
```bash
scripts/test-cap analyze      # ~6s; tests/test_analyze_*.py only
scripts/test-cap research     # ~12s; tests/test_research_*.py only
scripts/test-cap "analyze or research"   # multi-marker via pytest expression
scripts/test-changed          # git-diff-driven: runs only the capabilities touched
```

CI (`.github/workflows/test.yml`):
- Push to main + every PR run `pytest -n auto -m "not e2e"`.
- Tagged builds (`v*`) ALSO run the E2E suite.
- Self-hosted install drift check still gates merge.

**Always activate the venv** (`. .venv/bin/activate`) before invoking
`python -m agency.cli` or `python -m pytest`. The bare `pytest` command
may resolve to a globally-installed pytest that does not see the venv's
deps (`graphqlite`, `fastmcp`) → silent collection errors. Use
`python -m pytest` to force venv-Python's site-packages.

- Feature branches; PRs target `main`; additive history; never rewrite or
  force-push.
- Add a capability = add a file (folder-per-capability when Spec 016 lands).
- Spec lifecycle: research → design → spec-panel → refine → IMPLEMENTATION-PLAN → TDD.
  Per-phase: RED → GREEN → green `python -m pytest -q` → commit → push.
- Doctrine evolves through dogfooding: surface lessons via
  `reflect.note(scope="observation", …)` — NOT new markdown files.
