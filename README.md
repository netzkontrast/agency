# agency

An **installable Claude Code plugin** and a running engine for its model
on the real substrate — [`graphqlite`](https://pypi.org/project/graphqlite/)
(SQLite + Cypher) + [`fastmcp`](https://github.com/PrefectHQ/fastmcp)
(incl. the experimental code-mode transform). One bi-temporal provenance
graph; four concepts (Intent · Capability · Lifecycle · Memory);
**code-mode IS the contract**, exposed isomorphically over MCP · Skills ·
a bash CLI.

> v0.1. Capabilities self-register by reflection, and the engine **authors
> and validates its own plugin install.** The live registry currently exposes
> **36 self-registering capabilities / ~470 verbs** — query the current set
> with `agency search <keyword>` or `/agency:help`, never a frozen list.

## Read first

- [`architecture.md`](architecture.md) — the **shorthand decision digest**
  (every recorded WH(Y) decision as a one-liner, grouped by architecture
  layer; DERIVED from the thematic ADRs, rebuilt on spec-done, and emitted by
  the SessionStart hook as `additionalContext`). **Read this first** — full
  rationale lives in [`docs/adr/`](docs/adr/).
- [`docs/vision/GOALS.md`](docs/vision/GOALS.md) — the **why** (8 goals
  + 5 non-goals + a goal-to-code map). One page.
- [`docs/vision/CORE.md`](docs/vision/CORE.md) — the **canon** (how the
  four concepts compose).
- [`AGENTS.md`](AGENTS.md) — the **operational guide** for any agent
  working in this repo (verify via `git ls-remote`, never local HEAD).
- [`AGENCY_PROTOCOL.md`](AGENCY_PROTOCOL.md) — the **remote-async-agent
  doctrine** (COMPLETED ≠ done; the four-case routing; recovery flow).
- [`CLAUDE.md`](CLAUDE.md) — the working rules for any Claude Code session
  here (dogfood the engine · graph↔files are peers · decide before
  dispatching · keep `TODO.md` current · address drift before committing).

## Install (Claude Code)

This repository **is** an installable Claude Code plugin **and** its own
single-plugin marketplace. The plugin ships:

```
.claude-plugin/plugin.json        # install descriptor (+ userConfig.jules_api_key, sensitive)
.claude-plugin/marketplace.json   # single-plugin marketplace catalogue
.mcp.json                         # declares the Agency MCP server (bare `agency-mcp` on PATH)
hooks/hooks.json                  # SessionStart hook (auto pipx-install on first session)
hooks/session-start               # the install script (pipx-only, Spec 065)
hooks/run-hook.cmd                # cross-platform CMD+bash polyglot wrapper (Spec 064)
skills/using-agency/SKILL.md      # the broad-trigger entry meta-skill
skills/help/SKILL.md              # the /agency:help macroskill (live capability map)
commands/help.md                  # the /agency:help slash command
```

> **One canonical install path: pipx** (Spec 055/065 doctrine).
> The legacy `.venv` bootstrap (`bin/agency-install`) AND the
> `bin/agency` / `bin/agency-mcp` shims have ALL been removed (Spec
> 065 — PR #19 review surfaced fragility in the multi-step fallback
> chain). The pipx-installed `agency` / `agency-mcp` / `agency-doctor`
> console-scripts ARE the install. `.mcp.json` references bare
> `agency-mcp` (PATH resolution) like episodic-memory does.

### Pipx install (canonical)

```bash
pipx install git+https://github.com/netzkontrast/agency@main
# …or for a local checkout:
pipx install --editable /path/to/agency

# Verify:
agency-doctor          # JSON health report; exit 0 if ok, 1 if degraded
agency-mcp             # MCP server on stdio (bind via .mcp.json)
agency search "any-keyword"  # bash CLI
```

The plugin ships three console-scripts (`agency-mcp`, `agency`,
`agency-doctor`) registered in `pyproject.toml`. After `pipx install`,
all three land on PATH. `.mcp.json` references bare `agency-mcp`
(resolved from PATH — episodic-memory pattern; no bin/ shim).

If `agency-mcp` isn't on PATH the MCP server simply fails to start.
The SessionStart hook (below) prevents this on first session.

### From the GitHub marketplace

In Claude Code:

```
/plugin marketplace add netzkontrast/agency
/plugin install agency@agency
```

This sets up the plugin tree under `${CLAUDE_PLUGIN_ROOT}`. A
**SessionStart hook** (Spec 062, `hooks/session-start`) auto-runs
`pipx install --editable ${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}` on the
first session so `agency-mcp` lands on PATH without a manual step.
The hook is idempotent — every subsequent session early-exits when
the binary is already installed. Editable mode means future
marketplace plugin updates flow through automatically.

> **Claude Code Web environments:** the hook removes the need to
> manually `pipx install` after a marketplace install. The first
> session shows a one-time `agency: installing via pipx (one-time)
> — this may take ~5s` line; thereafter the plugin just works.

> **Pipx-direct doctrine (Spec 065):** the SessionStart hook is a
> single-path install — pipx only. Spec 063's multi-step fallback
> (pip --user → per-project `.agency/.venv`) was removed after PR #19
> review surfaced 4 P2 correctness issues in the chain. If pipx
> isn't on PATH the hook prints a clear install hint
> (`https://pipx.pypa.io/stable/installation/`) and exits 0. Users
> install pipx once; the plugin just works thereafter.

> **Target-repo scaffold:** after pipx install succeeds, the hook
> runs `agency install --scaffold-db ${CLAUDE_PROJECT_DIR}` (using
> the pipx-installed binary — NOT system python3, PR #19 review #2)
> so the project's `.agency/session.db` + `.agency/README.md` +
> `.gitattributes` binary-marker land on first session. The graph DB
> is per-project; the install ensures the dir structure exists
> before the engine first writes.

> **Cross-platform + cross-IDE (Spec 064):** the SessionStart hook
> ships through `hooks/run-hook.cmd` — a polyglot CMD+bash wrapper
> that runs on Windows, macOS, and Linux from one entry. The hook
> command uses the `${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}` bash
> fallback so Cursor / Codex harnesses (which set `PLUGIN_ROOT`)
> also work. `using-agency` is the broad-trigger entry skill any
> session calls first — it teaches the **wire-naming rule** (bare
> substrate tools like `intent_bootstrap`/`memory_graph_provenance`
> vs the prefixed `capability_<cap>_<verb>`) and every generated
> per-capability skill now carries **code-mode `call_tool` examples**
> (bootstrap → chained verb calls), so a fresh agent learns *how to
> call*, not just *when* (Spec 390).

Claude Code prompts for your **Jules API key** (optional — only needed
for the `jules` remote-async-agent capability; stored in your system
keychain). On the next session the engine starts automatically as an
MCP server, and `/agency:help` lists the live capability set.

### Local-dev install (contributors)

```bash
git clone https://github.com/netzkontrast/agency.git
cd agency

# One-shot default (Spec 282): venv + .[dev] = everything but the heavy torch backend.
scripts/setup

# Manual equivalent:
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
#   .[dev] self-references [analyze] (ruff/bandit/radon) + [tokens] + [anthropic]
#   + [publish], so the full suite runs with ZERO skipped capability tests.

# Everything, INCLUDING the heavy sentence-transformers/torch recall backend (~2GB):
scripts/setup --all          # or: pip install -e ".[all]"
#   [recall] → sentence-transformers BGE embedder (Spec 045 — optional;
#              TF-IDF is the zero-dep default)

# Run tests (parallel; Spec 053):
python -m pytest -q -n auto -m "not e2e"   # full suite, ~2:43
scripts/test-cap analyze                    # only analyze tests, ~7s

# Drift check before committing (Spec 054 — recommended pre-commit):
scripts/check-drift

# Wire Claude Code at this checkout:
claude --plugin-dir .
```

### After `pip install -e`

The engine self-hosts its own install. After adding a capability,
modifying a verb, or changing a docstring:

```bash
agency install     # regenerates plugin.json, .mcp.json, marketplace.json,
                              # skills/help/SKILL.md, and commands/*.md from the live registry
```

The CI workflow runs this on every PR and fails if the regen would
have produced a diff that wasn't committed.

### Regenerate the install (dogfood)

The manifest, `.mcp.json`, `marketplace.json`, the `help` skill, and the
`/agency:help` command are all **generated by the engine itself** (via
the `plugin` capability). After adding a new capability or skill:

```bash
agency install        # rewrites the five files from the live registry
```

## What ships

**36 self-registering capabilities** — drop a file (or a folder, Spec
016/060) under `agency/capabilities/` and the engine `discover()`s it via
reflection, auto-wiring one MCP tool per `@verb`-decorated method. Each
capability owns its ontology fragment (nodes · edges · enums · skills ·
templates · schemas) and `home`s on one of the four concepts. The set is OPEN
— this table is a current snapshot; `agency search <kw>` / `/agency:help`
list the live registry.

**Memory** (the bi-temporal provenance graph):

| Capability | Verbs | What |
|---|---|---|
| `adr` | 19 | WH(Y) decision records: `extract_decisions` from a spec → `proposed` drafts, owner-only `approve`, thematic **living** ADRs per architecture layer, `render` to `docs/adr/`, `architecture` digest → `architecture.md`. |
| `document` | 14 | The graph↔markdown convergence surface: `render` (graph scopes) · `explain` (code→md) · `index_repo` · `ingest`/`sync`/`mirror`/`emit` (bi-directional keep-both round-trip, Spec 292) · **`compose`** (deterministic template scaffold + MCP-sampled custom sections, Spec 394) · `revisions` · `session`. |
| `dogfood` | 11 | Graph-native observation ledgers — `note` · `render` (→ DOGFOOD-NOTES.md) · `export`/`import` · `collect` (legacy md→graph). |
| `manage` | 18 | The graph read/management API — census, typed listing, provenance drills (`analyze.graph`'s surface). |
| `panel` | 2 | Multi-expert review panels (spec-panel / business-panel synthesis). |
| `reflect` | 6 | Durable scope-tagged cross-session memory: `note`/`batch_note`/`recall`/`search`/`recall_semantic` (TF-IDF default + optional BGE via `[recall]`). |
| `toolcalls` | 5 | The ephemeral hook tool-call store (pre/post capture, full — never truncated; rule 9). |

**Capability** (the open verb substrate):

| Capability | Verbs | What |
|---|---|---|
| `analyze` | 17 | Decidable analysis — quality/security/performance/architecture + `paths`, the Iron-Law (`review`) report, `graph` census. Composes optional ruff/bandit/radon via `[analyze]`. |
| `config` | 3 | `.agency/config.yaml` scaffold + non-destructive repair. |
| `discover` | 8 | Requirements interview/triage — `interview` · `acceptance` · `clarify` · `clarity_gate` · `scope`. |
| `doctrine` | 4 | Cite/resolve the repo's own rules — `cite` · `principles` · `resolve` · `rules`. |
| `intent` | 11 | Intent `capture`/`confirm`/`amend` + critical-thinking methods (assumptions, brooks_lint, …). |
| `music` | 103 | The **reference clustered domain capability** (Spec 093/094) — a full album-production lifecycle (lyrics · audio · catalogue · promo · research · gates). |
| `novel` | 95 | Clustered novel-writing domain capability (the MVN flow — conceptualize → chapters/scenes). |
| `plugin` | 12 | Author/lint Claude Code plugin artefacts — manifest · skill · command · marketplace · CSO + capability lints · help. |
| `prompt` | 19 | Prompt authoring/audit/evaluate — `audit` (clarity score) · `assemble_*` · `fragments_for`. |
| `recommend` | 1 | Route a request to the right verb. |
| `research` | 5 | Deep-research flow — `lead` → `specialist` (codebase/prior-reflections/doc-corpus/web) → `verify` (adversarial citation check). |
| `shell` | 5 | Allowlisted shell recipes + per-tool filter profiles (Spec 337). |
| `skill_generator` | 3 | Compose `plugin.author_skill` + `lint_skill` into one deploy-ready-skill verb. |
| `skills` | 6 | Skill walking/management surface. |
| `symbols` | 3 | Symbol/call-graph queries (CodeGraph-style). |
| `thinking` | 11 | Critical-thinking methods (socratic, first-principles, …) recorded as provenance. |

**Lifecycle** (walkable disciplines + remote orchestration):

| Capability | Verbs | What |
|---|---|---|
| `branch` | 3 | Finish a dev branch — `assess` · `finish` · `commit_smart` (decidable conventional-commit message). |
| `delegate` | 4 | Agent orchestration — `fan_out`/`join` + the **`dispatch-decision`** skill (eleven-signal token-economics heuristic). |
| `develop` | 20 | Dev disciplines as walkable skills — `brainstorm`·`plan`·`tdd`·`debug`·`verify`·`review`·`skill_walk`·`reference`·`scaffold_capability`, plus the **`develop-spec`** lifecycle. |
| `frugal` | 7 | Over-engineering review — the YAGNI floor (`review`·`level`·`debt`). |
| `gate` | 3 | Reusable hard-gate predicate — `check` records PASSED / BLOCKED_ON + an `input-required` pause. |
| `jules` | 22 | Full remote-Jules-session lifecycle — dispatch · read · drive · `COMPLETED ≠ done` `verify` · `watch` · `recover` · `apply_patch` · `review_comment`. |
| `loop` | 15 | The loop-library surface — design/audit/run **bounded feedback loops** (terminal states, not open autonomy). |
| `mode` | 3 | Session-mode switching. |
| `persona` | 3 | Summon a specialist persona — compose a dispatch brief + record provenance. |
| `select` | 2 | Selection helpers. |
| `subagent` | 1 | Subagent-driven development — dispatch a worker via `delegate` + two-stage gated review. |
| `workflow` | 9 | The **develop-spec** lifecycle — `index`/`board`/`move_spec`/`open_spec` over `Plan/<state>/` physical spec folders (Spec 353–359). |
| `workspace` | 2 | Isolate a worktree on a fresh branch + baseline its green/red test result. |

Plus the **engine substrate tools** (bare names, wired directly — not
capabilities): `search` · `get_schema` · `execute` (the code-mode contract) +
`agency_welcome` (live capability map) · `intent_bootstrap` · `agency_doctor`
· `agency_reload` (self-healing install sync) · `lifecycle_gate` (mid-flow
elicit) · `memory_graph_provenance` (the moat read).

Third-party domain capabilities live in [`examples/`](examples/), loaded via
`Engine(..., extra_capabilities=[…])`; `music`/`novel` have graduated into
the core tree as the reference clustered domain capabilities (Spec 094/121).

## What it proves (`tests/` — the real-substrate acceptance suite)

1. **The moat — cross-concern provenance is one graph traversal.**
   `Memory.provenance(intent)` returns, in one Cypher walk, every
   action that `SERVES` the intent, the agent that `PERFORMED_BY` it,
   the artefact it `PRODUCES`d, and the gate it `PASSED`.
2. **Code-mode IS the contract.** The engine surface is exactly
   `search` · `get_schema` · `execute`; tools are discovered via
   `search` and called from inside `execute`'s sandbox; only the
   `return` value crosses back (token efficiency).
3. **Bash ≡ MCP isomorphism.** The same code-mode contract via MCP
   *and* via a bash-only subprocess, over the same graph, yields
   identical results (see `AGENTS.md`).
4. **Capabilities self-register by reflection.** Adding a capability is
   adding a folder under `agency/capabilities/<name>/` (verbs + ontology +
   a docstring that derives its Agent Skill) — and nothing else.
5. **A micro-step skill walker.** Walks a skill one phase at a time
   (progressive disclosure), executes phases bound to real capability
   verbs, blocks at a hard gate until confirmed; every phase + every
   gate is provenance (Codex C3 makes pauses + resumes both first-class
   nodes).
6. **Bi-temporal memory.** The *what* changes while the *why* holds;
   any prior version is reconstructable `as_of` an earlier tick.
7. **`COMPLETED ≠ done`** — and the four-case routing (`AGENCY_PROTOCOL.md`
   §1): `COMPLETED` overloads four distinct situations; the watcher
   classifier discriminates via `plan_unapproved` + `branch_on_remote`
   + `patch_summary`.
8. **Code-mode chain = an executable graph.** An `execute` block chains
   `transform → effect → act` in plain Python; calls run in-sandbox;
   only the small delta crosses into context while every call records
   an Invocation, mirroring the dataflow into durable provenance.
9. **Gates / human-in-the-loop via `elicit`.** A gate asks a one-line
   question mid-flow and records the outcome as a `Gate{passed, paused,
   evidence}` node.
10. **Schemas + templates (typed/generative layer).** A Template
    generates an Artefact (`DERIVED_FROM`) that a Schema validates
    (`VALIDATES_AGAINST`).
11. **A strictly-enforced ontology** — per-node required-field schemas
    + an enumerated edge set + closed enums; `record`/`link`/`update`
    reject drift.
12. **Capability-owned ontology fragments** — the core defines a base;
    each capability contributes its own nodes/edges/enums/skills/
    template-schemas (`Capability.ontology`), merged STRICTLY onto the
    core (no extension may redefine a core node).
13. **The plugin-development chain** — manifest → skill → command →
    marketplace entry → hard confirm gate, each step a strict,
    provenance-recorded artefact.
14. **The macroskill/micro-skill map (`/agency:help`)** — the
    harness-in-harness map: micro-skills (verbs) grouped under
    macroskills (capabilities). Auto-generated from the live registry.
15. **The install is self-hosted** — the committed manifest, help
    skill, and command are exactly what the `plugin` capability
    regenerates from the live registry; the help skill passes its own
    CSO linter.
16. **The remote-async-agent boundary** — `jules.dispatch` opens a
    session; the watcher classifies state transitions into a closed
    9-action set (`review_and_approve_plan` · `answer_agent_question`
    · `verify_pr` · `recover_silent_fail` · `recover_apply_plan` ·
    `dispatch_fresh` · `inspect_and_resume` · `noop` · `terminal`);
    skill-driven recovery flow (`jules-recovery-when-stuck`) closes
    the loop.
17. **AGENCY_PROTOCOL — generalized doctrine for any remote async
    agent.** The §1 four-case `COMPLETED` routing, the §2 publish-tool
    naming rule, the §5 recovery flow, the §9 PR review-cycle
    handshake (`jules.review_comment` composes review-comment bodies
    with the mandatory `reply_to_pr_comments(...)` tail).
18. **The `delegate.dispatch-decision` skill.** Walks the token-
    economics heuristic before any Jules dispatch — keeps work inline
    unless context-heavy.
19. **Dogfood loop closes graph-natively** (`reflect.batch_note` +
    `dogfood.collect`; Spec 017 inverts further so observations land
    via `reflect.note` from code-mode, with markdown as the rendered
    view).

## Spec landscape

Specs live in **physical state folders** — `Plan/<state>/NNN-slug/spec.md`
where `<state>` ∈ `draft · open · inprogress · superseded · done`. The folder
IS the spec's lifecycle state, mirrored by a `SpecLifecycle` graph node
(keep-both, Spec 292); `scripts/check-drift` gates
`folder == frontmatter == node`. The set runs through **Spec 394**
(`document.compose`, this change). Query live state from the graph, never by
eyeballing the tree:

```bash
agency execute --code 'return await call_tool("capability_workflow_index", {"root":"Plan"})'   # every spec's state + drift flags
agency execute --code 'return await call_tool("capability_workflow_board", {"state":"inprogress"})'
```

Work on the repo runs through one walkable lifecycle — the **`develop-spec`**
skill (on `workflow.ontology.skills`) chaining the disciplines: intent →
triage → brainstorm → research → acceptance → spec → spec-panel → brooks-lint
→ improve → **open** → **adr-approve** (the ADR hinge — a spec can't reach
`/inprogress` until its extracted WH(Y) decisions are owner-`approved`) →
build (TDD) → done. **Code is the final decision**: ADRs and
[`architecture.md`](architecture.md) are DERIVED from what shipped, rebuilt on
spec-done via `adr.architecture(apply=True)`.

[`TODO.md`](TODO.md) is the binding cross-spec status roll-up (maintained per
CLAUDE.md Rule #4 — every spec-touching commit updates its row); each spec's
`## Followup — Implementation Status` section is the ground truth.
[`docs/vision/SPEC-VISION-ALIGNMENT.md`](docs/vision/SPEC-VISION-ALIGNMENT.md)
maps every spec to the 8 Vision goals.

## Layout

| Path | Concept |
|---|---|
| `agency/memory.py` | **Memory** — bi-temporal graph; `record·link·supersede` / `recall·find·validate`; `provenance` (the moat) |
| `agency/intent.py` | **Intent** — `capture·confirm·amend` |
| `agency/lifecycle.py` | **Lifecycle** — `open·move·complete·status`; A2A-aligned states + gates |
| `agency/capability.py` + `capabilities/` | **Capability** — open verbs, role-tagged `act·transform·effect`; discovered by reflection |
| `agency/skill.py` | The micro-step skill walker (progressive disclosure + hard-gate persistence per Codex C3) |
| `agency/ontology.py` | The strict ontology + skill schemas |
| `agency/templates.py` | Templates (manifest · SKILL.md · command · step-doc) |
| `agency/engine.py` | **Engine** — FastMCP; code-mode contract; reflection-based auto-wiring; `reload()` (self-healing install sync); lifespan starts the Jules watcher |
| `agency/_host_bridge.py` | **HostBridge** (Spec 285) — the one boundary a verb reaches the host LLM (`sample`) + the user (`elicit`) through; sync-over-async via AnyIO |
| `agency/cli.py` + `AGENTS.md` | Bash layer — same code-mode contract for bash-only / no-MCP agents |
| `agency/install.py` | Self-hosted Claude Code plugin install (generated by the engine) |
| `agency/capabilities/<name>/` | One folder per capability — verbs + ontology + a docstring that derives its Agent Skill (the drop-in bar) |
| `agency/capabilities/jules/` + `_jules_*.py` | The Jules remote-async-agent capability + the long-polling watcher + Mode A/B preamble assembler |
| `agency/capabilities/{document,adr,workflow}/` | The repo-development surface — graph↔markdown convergence · WH(Y) decision records · the `develop-spec` lifecycle |
| `examples/` | Third-party out-of-tree domain capabilities (extension-contract proofs) |
| `architecture.md` + `docs/adr/` | The DERIVED decision digest (one-liner per WH(Y) decision) + the full thematic ADRs |
| `Plan/<state>/NNN-slug/` | Specs in physical state folders (`draft·open·inprogress·superseded·done`) |
| `tests/` + `tests/acceptance/` | Real-substrate tests — `pytest-bdd` Gherkin acceptance scenarios are the contract (Spec 053; CI runs the full regression) |
| `.github/workflows/test.yml` | CI runs `pytest -n auto -m "not e2e"` on every PR + verifies the self-hosted install hasn't drifted |

## Develop

```bash
. .venv/bin/activate                      # always activate first
python -m pytest -q -n auto -m "not e2e"  # full suite, parallel (~2:43)
agency install                  # regen install when capabilities change
```

### Fast iteration (Spec 053)

`tests/conftest.py` auto-marks tests by file path so you can slice by
capability without per-test maintenance:

```bash
scripts/test-cap analyze       # tests/test_analyze_*.py — ~7s
scripts/test-cap research      # tests/test_research_*.py — ~12s
scripts/test-cap "analyze or research"
scripts/test-changed           # git-diff-driven; runs only touched capabilities
scripts/test-changed --with-e2e
```

CI (`.github/workflows/test.yml`): every PR runs
`pytest -n auto -m "not e2e"`; tagged builds (`v*`) also run the E2E suite.

### Optional extras

```bash
pip install -e ".[dev]"        # pytest + xdist + tiktoken
pip install -e ".[dev,analyze]"   # + ruff + bandit + radon (composed findings)
pip install -e ".[dev,recall]"    # + sentence-transformers BGE embedder
```

`agency_doctor` reports which extras are live (`embedder`, `analyze_extras`,
`install_method`, `drift` signals).

### Drift management (Spec 054)

The capability set is OPEN (reflection-based discovery), but a new
capability indirectly touches ~9 places (pyproject extras, install
regen, CLAUDE.md, TODO.md, SPEC-VISION-ALIGNMENT.md, test files,
CI workflow, agency_doctor, the spec's Followup section). Two
guardrails:

1. **AGENCY-DRIFT code tags** — `# AGENCY-DRIFT: <topic>` inline at
   every site where code reads a set/list that changes when
   capabilities change. `grep -rn AGENCY-DRIFT agency/ tests/` lists
   them all.
2. **`scripts/check-drift`** — runs install dry-run + capability-test
   gap check + tag inventory. CI runs this as a PR gate. Exit code 0
   = clean; 1 = drift.

Read [`Plan/done/054-drift-management/spec.md`](Plan/done/054-drift-management/spec.md)
for the rationale + the 8 canonical drift tags.

### Discipline

- Feature branches; PRs target `main`; additive history; never rewrite
  or force-push.
- Add a capability = add a file (folder-form for the heavier ones —
  see `agency/capabilities/{analyze,document,research}/`).
- Spec lifecycle: walk the **`develop-spec`** workflow (intent → triage →
  brainstorm → research → acceptance → spec → spec-panel → brooks-lint →
  improve → open → adr-approve → implement → done). Specs live in physical
  `Plan/<state>/` folders; per-phase TDD: RED → GREEN → green pytest →
  commit → push.
- **TODO.md update is MANDATORY** in every spec-touching commit
  (CLAUDE.md Rule #4).
- Doctrine evolves through dogfooding: `reflect.note(scope=
  "observation", …)` and `dogfood.note(observation, plan_slug)` — NOT
  new markdown files (Spec 017 closed the graph-vs-file inversion;
  use `dogfood.render(plan_slug)` to project on demand).
