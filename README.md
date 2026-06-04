# agency

An **installable Claude Code plugin** and a running engine for its model
on the real substrate — [`graphqlite`](https://pypi.org/project/graphqlite/)
(SQLite + Cypher) + [`fastmcp`](https://github.com/PrefectHQ/fastmcp)
(incl. the experimental code-mode transform). One bi-temporal provenance
graph; four concepts (Intent · Capability · Lifecycle · Memory);
**code-mode IS the contract**, exposed isomorphically over MCP · Skills ·
a bash CLI.

> v0.1. Capabilities self-register by reflection, and the engine **authors
> and validates its own plugin install.**

## Read first

- [`docs/vision/GOALS.md`](docs/vision/GOALS.md) — the **why** (8 goals
  + 5 non-goals + a goal-to-code map). One page.
- [`docs/vision/CORE.md`](docs/vision/CORE.md) — the **canon** (how the
  four concepts compose).
- [`AGENTS.md`](AGENTS.md) — the **operational guide** for any agent
  working in this repo (verify via `git ls-remote`, never local HEAD).
- [`AGENCY_PROTOCOL.md`](AGENCY_PROTOCOL.md) — the **remote-async-agent
  doctrine** (COMPLETED ≠ done; the four-case routing; recovery flow).
- [`CLAUDE.md`](CLAUDE.md) — three rules for any Claude Code session
  working here.

## Install (Claude Code)

This repository **is** an installable Claude Code plugin **and** its own
single-plugin marketplace. The plugin ships:

```
.claude-plugin/plugin.json        # install descriptor (+ userConfig.jules_api_key, sensitive)
.claude-plugin/marketplace.json   # single-plugin marketplace catalogue
.mcp.json                         # declares the Agency MCP server (stdio, via bin/agency-mcp)
bin/agency-mcp                    # thin PATH router to the pipx-installed `agency-mcp`
bin/agency                        # thin PATH router to the pipx-installed `agency`
skills/help/SKILL.md              # the /agency:help macroskill (live capability map)
commands/help.md                  # the /agency:help slash command
```

> **One canonical install path: pipx** (Spec 055 doctrine, 2026-06-03).
> The legacy `.venv` bootstrap (`bin/agency-install`) has been removed;
> `bin/agency-mcp` and `bin/agency` are thin PATH routers to the
> pipx-installed console-scripts. Marketplace install still works — the
> shim routes to the pipx binary.

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
all three land on PATH; `.mcp.json` references `${CLAUDE_PLUGIN_ROOT}/
bin/agency-mcp` which `exec`s the PATH-resolved `agency-mcp`.

If `agency-mcp` isn't on PATH, the shim exits 127 with the install
hint — no auto-bootstrap, no `.venv` surprises.

### From the GitHub marketplace

In Claude Code:

```
/plugin marketplace add netzkontrast/agency
/plugin install agency@agency
```

This sets up the plugin tree under `${CLAUDE_PLUGIN_ROOT}`. **You then
run `pipx install <plugin-root>`** to get `agency-mcp` on PATH so the
marketplace `.mcp.json` shim can route to it.

Claude Code prompts for your **Jules API key** (optional — only needed
for the `jules` remote-async-agent capability; stored in your system
keychain). On the next session the engine starts automatically as an
MCP server, and `/agency:help` lists the live capability set.

### Local-dev install (contributors)

```bash
git clone https://github.com/netzkontrast/agency.git
cd agency
python -m venv .venv && . .venv/bin/activate

# Core dev (pytest + xdist + tiktoken):
pip install -e ".[dev]"

# All optional extras (recommended for full local capability):
pip install -e ".[dev,analyze,recall]"
#   [analyze] → ruff, bandit, radon (Spec 050 composed lint/security/metric findings)
#   [recall]  → sentence-transformers BGE embedder (Spec 045 — optional;
#               TF-IDF is the zero-dep default)

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
python -m agency.install     # regenerates plugin.json, .mcp.json, marketplace.json,
                              # skills/help/SKILL.md, and commands/*.md from the live registry
```

The CI workflow runs this on every PR and fails if the regen would
have produced a diff that wasn't committed.

### Regenerate the install (dogfood)

The manifest, `.mcp.json`, `marketplace.json`, the `help` skill, and the
`/agency:help` command are all **generated by the engine itself** (via
the `plugin` capability). After adding a new capability or skill:

```bash
python -m agency.install        # rewrites the five files from the live registry
```

## What ships

**14 self-registering capabilities** — drop a file (or folder, per
Spec 060) in `agency/capabilities/` and the engine `discover()`s it
via reflection, auto-wiring one MCP tool per `@verb`-decorated method.
Each capability owns its ontology fragment (nodes · edges · enums ·
skills · templates · schemas).

| Capability | Role(s) | What |
|---|---|---|
| `analyze` | transform/effect/act | 4-axis decidable analysis (quality/security/performance/architecture) + Spec 048 `paths` axis. Composes optional ruff/bandit/radon via the `[analyze]` extra. `run` · `improve` · `cleanup` · `architecture` · `security` · `quality` · `performance` · `paths`. |
| `branch` | transform/effect | Finish a development branch: `assess` + `finish`. |
| `delegate` | transform/effect | Agent orchestration: `fan_out` + `join` + the **`dispatch-decision`** skill (eleven-signal token-economics heuristic for inline vs local-subagent vs Jules vs MCP). |
| `develop` | transform/act | Dev-workflow disciplines as walkable skills (brainstorm · plan · tdd · debug · verify · spec-panel · review) + `scaffold_capability` (light/medium/heavy skeletons). |
| `document` | transform/effect | Project graph state to markdown: `render` (5 scopes incl. `research-report` and `provenance`) · `explain` (3 depths) · `index_repo` (94% token reduction). |
| `dogfood` | transform/effect/act | Graph-native observation ledgers — `note` (write) + `render` (project to DOGFOOD-NOTES.md) + `export`/`import` (JSON for merge-conflict recovery) + `collect` (legacy markdown-to-graph migration). |
| `gate` | act | Reusable hard-gate predicate: `check` records PASSED or BLOCKED_ON + an `input-required` pause on failure. |
| `jules` | effect/transform | Full remote-Jules-session lifecycle: 22 verbs covering dispatch · read · drive · `COMPLETED ≠ done` `verify` · `watch` · `recover` · `apply_patch` · `lint_prompt` · `review_comment` · `detect_mode`. |
| `plugin` | act/transform | Develop plugins: scaffold manifest, author skill/command, marketplace entry, lint skills (CSO rules), lint capabilities (Hint #7 + wire-shape + reflection-link), help. |
| `reflect` | act/transform | Durable scope-tagged cross-session memory (`note`/`batch_note`/`recall`/`search`/`recall_semantic`) — the graph-native store for observations; TF-IDF default + optional BGE via the `[recall]` extra. |
| `research` | act | Deep-research flow: `lead` (mint a Research node) → `specialist` (4 roles: codebase / prior-reflections / doc-corpus / web) → `verify` (adversarial citation check). |
| `skill_generator` | act | Compose `plugin.author_skill` + `lint_skill` into one deploy-ready-skill verb. |
| `subagent` | effect | Subagent-driven development: dispatch a worker via `delegate` + two-stage gated review (spec → quality). |
| `workspace` | effect | Isolate a worktree on a fresh branch + baseline its green/red test result. |

Plus the **engine substrate tools** (not capabilities, wired directly):
`search` · `get_schema` · `execute` (the code-mode contract) +
`lifecycle_gate` (mid-flow elicit) + `memory_graph_provenance` (the moat
read).

Domain capabilities live in [`examples/`](examples/) — e.g.
`examples/music.py` (album conceptualizer), loaded via
`Engine(..., extra_capabilities=[…])`. The bootstrapping harness stays
minimal while proving the extension contract end to end.

## What it proves (`tests/`, 663 passing)

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
   adding a file (or a folder per Spec 016 when it lands).
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

[`Plan/000-overview.md`](Plan/000-overview.md) — the spec index. Active
push is wave-3 (specs 012-019). Read [`docs/vision/GOALS.md`](docs/vision/GOALS.md)
to see which goal each spec advances.

[`TODO.md`](TODO.md) is the binding cross-spec status roll-up
(maintained per CLAUDE.md Rule #4); each spec's `## Followup —
Implementation Status` section is the ground truth.
[`docs/vision/SPEC-VISION-ALIGNMENT.md`](docs/vision/SPEC-VISION-ALIGNMENT.md)
maps every spec to the 8 Vision goals.

Shipped (18 — across all waves):
- Substrate: **020** central .agency/session.db · **029** MCP bootstrap
  + self-explain · **030** Jules-key + doctor + stateful welcome
- Jules: **012** complete lifecycle + watcher · **013** skills + protocol
  doctrine · **015** architecture review (dogfood pass)
- Distribution: **039** pipx + E2E + console-scripts + discovery shims
- Memory + Provenance: **017** graph-native dogfood ledgers · **045**
  reflect.recall_semantic (TF-IDF + optional BGE) · **048** intent chain
  + owner enum + analyze.paths
- Capabilities: **040** subagent-decision heuristics · **042** analyze
  (4 axes + improve/cleanup) · **043** document (render/explain/index_repo)
  · **044** research (lead+specialist+verify) · **050** ruff+bandit+radon
  integration · **052** DuckDuckGo web specialist + reachability check
- Meta: **047** cluster-integration master · **053** test-suite-
  organization + CI

Drafted: **014** (observation → amendment) · **016** (capability authoring
doctrine) · **019** (engine output-shape) · **049** (naming + token
economy review) · **051** (analyze.architecture + networkx) · **054**
(drift management — code tags + scripts/check-drift).

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
| `agency/engine.py` | **Engine** — FastMCP; code-mode contract; reflection-based auto-wiring; lifespan starts the Jules watcher |
| `agency/cli.py` + `AGENTS.md` | Bash layer — same code-mode contract for bash-only agents |
| `agency/install.py` | Self-hosted Claude Code plugin install (generated by the engine) |
| `agency/capabilities/jules.py` + `_jules_*.py` | The Jules capability (folder migration scheduled in Spec 016) |
| `agency/capabilities/_jules_watch.py` | The long-polling watcher (state-aware adaptive cadence) |
| `agency/capabilities/_jules_preambles.py` | Mode A/B preamble assembler + `review_comment` helper |
| `examples/music.py` | Out-of-tree domain capability (album conceptualizer) |
| `Plan/` | Specs (one dir per spec; `000-overview.md` is the index) |
| `tests/` | Real-substrate tests (228 passing on `python -m pytest -q`) |
| `.github/workflows/test.yml` | CI runs pytest on every PR + verifies the self-hosted install hasn't drifted |

## Develop

```bash
. .venv/bin/activate                      # always activate first
python -m pytest -q -n auto -m "not e2e"  # full suite, parallel (~2:43)
python -m agency.install                  # regen install when capabilities change
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

Read [`Plan/054-drift-management/spec.md`](Plan/054-drift-management/spec.md)
for the rationale + the 8 canonical drift tags.

### Discipline

- Feature branches; PRs target `main`; additive history; never rewrite
  or force-push.
- Add a capability = add a file (folder-form for the heavier ones —
  see `agency/capabilities/{analyze,document,research}/`).
- Spec lifecycle: research → design → spec-panel → refine →
  IMPLEMENTATION-PLAN → TDD. Per-phase: RED → GREEN → green pytest →
  commit → push.
- **TODO.md update is MANDATORY** in every spec-touching commit
  (CLAUDE.md Rule #4).
- Doctrine evolves through dogfooding: `reflect.note(scope=
  "observation", …)` and `dogfood.note(observation, plan_slug)` — NOT
  new markdown files (Spec 017 closed the graph-vs-file inversion;
  use `dogfood.render(plan_slug)` to project on demand).
