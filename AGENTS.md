# AGENTS.md — the one-screen guide for agents working in this repo

**What this repo is.** `agency` *is* a Claude Code plugin: a **FastMCP engine**
over a **bi-temporal GraphQLite graph**, exposing exactly three tools on the wire
— **`search` · `get_schema` · `execute`** — with everything else discovered, not
enumerated. Four concepts (**Intent · Capability · Lifecycle · Memory**) on one
substrate.

**Read order.** This file (orientation) → [`CLAUDE.md`](CLAUDE.md) (the BINDING
rules — they override defaults) → [`docs/vision/CORE.md`](docs/vision/CORE.md)
(canon) → [`docs/vision/GOALS.md`](docs/vision/GOALS.md) (why) →
[`AGENCY_PROTOCOL.md`](AGENCY_PROTOCOL.md) (remote-agent doctrine). Module-level
reference: [`docs/vision/reference/`](docs/vision/reference/).

> CLAUDE.md is the source of truth for the numbered rules. This file summarizes
> them so a fresh agent can onboard fast; when they disagree, CLAUDE.md wins.

---

## Architecture decisions (the load-bearing ones)

- **One wire contract, forever.** No matter how many capabilities/verbs exist,
  the engine exposes only `search`/`get_schema`/`execute` + a fixed set of
  **8 bootstrap "substrate tools"** (`SUBSTRATE_TOOLS` in `_substrate_tools.py`:
  `intent_bootstrap`, `agency_welcome`, `agency_doctor`, `agency_install`,
  `agency_reload`, `lifecycle_gate`, `memory_graph_provenance`, `hook_event`).
  Adding verbs never widens the wire. **Never add a flat/N-verb public surface.**
- **Code-mode is the contract.** `execute(code)` runs a Python block in a sandbox
  where `await call_tool(name, params)` chains verbs locally; only the `return`
  value crosses back. Chain N calls, return a small delta — never a dump.
- **The four concepts, one graph.** Everything is nodes/edges in ONE provenance
  graph: **Intent** (human-owned why/what — the root every action serves),
  **Capability** (the how — verbs grouped by domain, self-registered),
  **Lifecycle** (`Lifecycle`/`Gate` — task state + the gates that pause it),
  **Memory** (the bi-temporal graph itself + recall/provenance). No fifth concept
  ships without deleting equivalent weight.
- **The provenance moat.** Every capability-verb call auto-records an
  `Invocation` that `SERVES` the intent (BEFORE running, so failures are
  auditable) + `PRODUCES` artefact edges. Raw-tool actions don't. A full audit of
  any goal is one traversal (`memory_graph_provenance`). **Dogfood the engine** —
  prefer a capability verb over the raw tool so provenance accrues.
- **Bi-temporal, keep-both (Spec 292).** Nodes carry `recorded_at`/`valid_at`;
  reconciliation never overwrites — latest `recorded_at` wins on read, history is
  retained. The **Document** is the convergence artefact: graph and markdown files
  are editable peers (`document.render` graph→file; `document.ingest`/`sync`
  file→graph), bound by a `<!-- agency-node: <id> -->` anchor on line 1.
- **Boundaries behind Drivers (Spec 002).** Every external side-effect (git,
  Jules, web, audio, DB, token counting, LLM) is isolated behind a **Driver** on
  the `DriverRegistry`, registered as **lazy factories** (materialized on first
  `get`; an unused boundary costs nothing; explicit injection wins). Tests inject
  fakes. Nine boundaries today: `runner · jules · vcs · embedder · web_search ·
  token_counter · skills_client · llm · anthropic`.
- **The drop-in-capability bar.** Add a folder under `agency/capabilities/<name>/`
  — verbs + an `OntologyExtension` + a docstring that *derives* its Agent Skill —
  **and nothing else**, and agency gains a complete, discoverable, walkable,
  CLI-exposed, MCP-wired, emittable capability. If adding a capability needs an
  edit anywhere else, **that coupling is the bug to fix.**

## Code map (where things live)

```
agency/
  engine.py            Engine: build graph, discover caps, wire 9 boundaries, build_mcp
  capability.py        CapabilityBase, @verb, OntologyExtension, CapabilityContext, Registry
  _invoke.py           Registry.invoke decomposed: IntentGuard·ParameterInjector·
                       InvocationRecorder·ResultProcessor (Spec 286)
  _verb.py             the typed `Verb` value object (Spec 286)
  _substrate_tools.py  the 8 SubstrateTool bootstrap tools (extracted from build_mcp)
  toolresult.py        ToolResult (success/failure envelope) + Codes + TypedError + Severity
  ontology.py          core Ontology + OntologyExtension merge + Role/enum sets
  memory.py            the bi-temporal GraphQLite store (record/recall/validate_schema)
  intent.py lifecycle.py   Intent + Lifecycle concept modules
  skill.py skill_emit.py   skill walker (one phase at a time) + Agent-Skill emission
  cli.py install.py disclosure.py templates.py cache.py   CLI · self-install · tiered discovery
  _drivers/ _llm.py _runner.py _tokens.py …   boundary backends
  capabilities/<name>/      ONE folder per capability (30 today)
    __init__.py _main.py    the CapabilityBase subclass (+ clusters/ mixins for big caps)
    ontology.py             this cap's OntologyExtension (nodes/edges/enums/skills/schemas)
    drivers.py data/ templates/ schemas/ references/   optional cap-local assets
scripts/   check-drift · check-doc-drift · check_codes_coverage.py · check_schema_coverage.py ·
           check_architecture.py · gen-capability-docs · setup · test-cap · test-changed
tests/acceptance/   Gherkin .feature + pytest-bdd step files (the contract; see below)
Plan/NNN-name/spec.md   per-spec state (293 specs); TODO.md is the cross-spec roll-up
docs/      engineering docs; docs/vision/ is canon; docs/vision/reference/ is module-by-module
```

## Coding standards / conventions

- **A capability = a folder.** `_main.py` holds a `CapabilityBase` subclass with
  `name`, `home` (`capability`/`lifecycle`/`memory`), `ontology`, and `@verb`
  methods. Big caps split verbs into `clusters/*.py` mixins composed into one class.
- **Verb roles** (`@verb(role=…)`): `transform` (pure compute) · `act` (produces an
  artefact/node) · `effect` (external side-effect) · `gate` (pass/block). The role
  is recorded on every Invocation.
- **Return `ToolResult`** (`ToolResult.success(data=…)` / `ToolResult.failure(code,
  message)`). Failure `code`s use **`Codes.X`** (canonical values are **lowercase**
  per Spec 059, e.g. `Codes.NOT_FOUND == "not_found"`) — never a bare string
  literal (the codes-coverage gate flags those). `TypedError.severity` drives retry.
- **The one handle is `self.ctx`** (`CapabilityContext`): `ctx.memory`,
  `ctx.intent_id`, `ctx.record`/`record_and_serve`/`link`, `ctx.call`/`ctx.spawn`
  (sibling verbs, depth-guarded, recorded), `ctx.get_driver`, `ctx.template`/
  `ctx.schema`/`ctx.validate`, `ctx.neighbors`. Never open a new public surface.
- **A capability OWNS its ontology fragment**, merged STRICTLY onto core (a label
  collision is a hard bootstrap error). Declare an edge ⇒ traverse it
  (`ctx.neighbors`); a declared-but-unwalked edge is dormant surface.
- **Derive, don't duplicate.** `as_capability()` derives the `SkillDoc` from the
  module docstring (`Use when:`/`Triggers:`/`Red flags:`) and injects a
  `<cap>-usage` walkable skill when none is authored. Authored metadata that
  duplicates a source is drift waiting to happen.
- **No hardcoded values.** Assert invariants/relationships computed from the live
  source (`wire_tok > bare_tok*2.5`), never frozen snapshots ("exactly 73 verbs").
  Genuine tunable budgets are documented config, kept few and named.

## Repo rules (hard — see CLAUDE.md for the binding text)

1. **MCP-first / dogfood.** Use the `mcp__…__{search,get_schema,execute}` tools (or
   the bash CLI fallback) over raw tools; don't bypass the substrate.
2. **`TODO.md` is mandatory in every spec-touching commit** — flip the verdict
   (Shipped/Partial/Not started), one-line summary, blocker/next step. Per-spec
   deep state lives in `Plan/NNN-…/spec.md`'s `## Followup` section.
3. **Decide before dispatching.** Walk the `dispatch-decision` skill (eleven-signal
   rule) before any subagent/Jules dispatch.
4. **Address drift before committing.** Run `scripts/check-drift` (+
   `check-doc-drift` for docs you changed) before commit; tag set-reading sites
   with `# AGENCY-DRIFT:`.
5. **Test behaviour, not implementation.** Gherkin acceptance scenarios
   (`tests/acceptance/`, pytest-bdd) are the contract — no unit tests on internals.
6. **Check cluster coherence** (`Plan/047-…`) before adding a verb/skill.
7. **Additive history.** Feature branches; PRs target `main`; never rewrite or
   force-push. Conventional commits, one concern each.
8. **Evolve doctrine through dogfooding** — surface lessons via
   `reflect.note(scope="observation", …)`, not new markdown files.

## Workflow

- **Setup:** `scripts/setup` (venv + `.[dev]`; `--all` adds the heavy torch recall
  backend), then `. .venv/bin/activate`. **Always activate the venv** before
  `python -m agency.cli` / `python -m pytest` (bare `pytest` may miss venv deps).
- **Spec lifecycle:** research → design → spec-panel → refine → IMPLEMENTATION-PLAN
  → TDD. Per phase: **RED → GREEN → focused tests → commit → push.**
- **Tests:** locally run focused slices — `scripts/test-cap <marker>` /
  `scripts/test-changed` (< 30s). The **full regression runs in CI**
  (`.github/workflows/test.yml`: `pytest -n auto -m "not e2e"`), not in the local
  loop. When you push a branch, **subscribe to PR activity** so CI/review events
  arrive; if CI is red the watching session fixes it autonomously.
- **After changing capabilities:** `python -m agency.install` regenerates the
  self-hosted install (`.claude-plugin/`, `skills/`, `commands/`).

---

## Running the engine from a bash-only shell (Jules / no-MCP harnesses)

Same contract as an MCP client — **code-mode** — over the CLI. State is one graph
file (`--db <path>`, persists across calls). MCP/CLI isomorphism is proven in
`tests/acceptance/test_search_isomorphism.py` (Spec 023 §F3.1): the MCP and CLI
forms return structurally identical results.

```bash
agency --db graph.db intent --purpose "…" --deliverable "…" --acceptance "…"  # → {"intent_id": …}
agency --db graph.db search "lint skill"                 # discover tools
agency --db graph.db get-schema capability_plugin_lint_skill   # one verb's schema
agency --db graph.db execute --code '
r = await call_tool("capability_plugin_lint_skill", {"name": "x", "description": "d", "intent_id": "intent:abc"})
return r["violations"] if isinstance(r, dict) and "violations" in r else r'
```

Every verb is ALSO a CLI command (Spec 079): `agency <cap> <verb> --param … --intent-id …`
(`--intent-id` defaults to `$AGENCY_INTENT`). `agency --help` lists the surface.
Code-mode stays the canonical, token-cheapest way to chain calls.

## Remote-agent dispatch (Jules) — name the tools literally

Prose alone leaves work stranded in the agent's VM (the silent-fail mode
[`AGENCY_PROTOCOL.md`](AGENCY_PROTOCOL.md) exists to close; `COMPLETED ≠ done` —
verify via `git ls-remote`, never local HEAD). Canon (see
`agency/capabilities/jules/reference.md` §3): **`submit(branch, msg, title, desc)`**
is the one publish tool — always name it; `request_user_input(message)` is the
ONLY blocking ask (never `message_user`); `replace_with_git_merge_diff` for
multiline edits; `request_code_review()` before submit; **`reply_to_pr_comments(...)`
is required after `submit` when responding to a `@jules` review comment**. Compose
agency-posted `@jules` comments via `jules.review_comment(body)` (appends the
handshake tail).

- **Mode A (dogfood):** Jules works directly in this repo (R+W); inherits these
  root docs via lexical scoping.
- **Mode B (delegate):** the plugin is installed in another project; Jules clones
  agency READ-ONLY for reference and writes only in the target repo.
