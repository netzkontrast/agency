# Capability reference

<!-- doc-generated-by: scripts/gen-capability-docs (re-run; do not hand-edit) -->

> **Generated** from the live registry by `scripts/gen-capability-docs`. Every capability self-registers from `agency/capabilities/`; this page is rendered from the running engine, so it is always current. Per-capability deep docs (the L1/L2/L3 Agent Skill) live in `skills/<capability>/SKILL.md`.

**17 core capabilities.** Domain capabilities (e.g. `music`) load out-of-tree via `Engine(..., extra_capabilities=[…])` — see `examples/music.py` + [../vision/reference/drivers.md](../vision/reference/drivers.md).

The wire contract is always the same three substrate tools — **`search` · `get_schema` · `execute`** — plus a few bootstrap tools; every verb below is reached through `execute` (code-mode) or its `agency <cap> <verb>` CLI mirror.

---
## `analyze`  (capability)

Use when assessing a codebase or diff for quality, security, performance, or architecture problems before review or shipping — surfaces decidable findings as graph artefacts.

**Walkable skills:** `code-analysis`

| verb | role | summary |
|---|---|---|
| `analyze.architecture` | transform | Dependency-graph + structural checks: import cycles, file LOC thresholds. |
| `analyze.cleanup` | act | Focused mode: analyse for dead-code findings only, draft a patch plan. |
| `analyze.graph` | transform | Query the provenance graph — a census of node types + a typed listing (read the graph). |
| `analyze.improve` | act | Read prior Analysis findings, draft an improvement plan as a Reflection. |
| `analyze.paths` | transform | Spec 048 intent-path analysis: long chains + verb sequences. |
| `analyze.performance` | transform | AST-based hot-path lint: nested O(n²), += in loop, unbounded while True. |
| `analyze.quality` | transform | Decidable lint findings: unused imports, long lines, long functions, long files. |
| `analyze.run` | act | Run the requested axes; record an Analysis + per-Finding nodes. |
| `analyze.security` | transform | Decidable security patterns: eval/exec, hardcoded credentials, pickle.load, shell=True. |

## `branch`  (lifecycle)

Use when a development branch is ready to wrap up and its state must be detected to merge, open a PR, or report what blocks completion.

**Walkable skills:** `branch-usage`

| verb | role | summary |
|---|---|---|
| `branch.assess` | transform | Read the branch state (ahead/behind/dirty) and recommend merge/pr/keep/discard. |
| `branch.finish` | effect | Finish the branch by the chosen action (merge/pr/keep/discard); record the outcome. |

## `delegate`  (lifecycle)

Use when a task might be better handled by a subagent (local, Jules, or another driver) and the choice to dispatch versus stay inline must be weighed, then work fanned out and the results joined.

**Walkable skills:** `dispatch-decision`

| verb | role | summary |
|---|---|---|
| `delegate.dispatch_bash_hints` | transform | Compose the bash-hint context block for a dispatch prompt. |
| `delegate.dispatch_decision` | transform | Apply the dispatch-vs-inline heuristic and return a recommendation. |
| `delegate.fan_out` | effect | Open one child Lifecycle per item (capped at `quota`), dispatch the driver |
| `delegate.join` | act | Reduce a delegation over its children's Lifecycle state. |

## `develop`  (lifecycle)

Use when building the system further — walking a development discipline (tdd, plan, review), scaffolding a new capability, or running a skill to its first hard gate.

**Walkable skills:** `authoring-capabilities`, `brainstorm`, `debug`, `execute`, `plan`, `review`, `spec-panel`, `tdd`, `verify`

| verb | role | summary |
|---|---|---|
| `develop.checklist` | transform | Project a discipline (skill walk) into a step-by-step checklist. |
| `develop.record_authoring_outcome` | act | Record a Reflection at the end of an authoring-capabilities walk. |
| `develop.reference` | transform | Fetch a discipline's heavy how-to on demand (T3 disclosure). |
| `develop.scaffold_capability` | act | Emit a CAPABILITY-AUTHORING.md-compliant capability skeleton. |
| `develop.skill_walk` | act | Walk a registered skill to the first hard gate in ONE call (the atomic walker). |
| `develop.validate_skill` | transform | Validate a capability's Agent-Skill (its SkillDoc) — lint + dry-run emit. |

## `document`  (memory)

Use when a repository's structure must be understood or rendered — an explanation of a subsystem, a project index, or a graph-native rendering — without loading the whole tree.

**Walkable skills:** `repo-briefing`

| verb | role | summary |
|---|---|---|
| `document.explain` | act | Deterministic code → markdown explanation; emits a Reflection. |
| `document.index_repo` | effect | 94%-reduction repo briefing — deterministic; ≤ max_tokens. |
| `document.render` | transform | Project graph state to markdown; deterministic. |

## `dogfood`  (memory)

Use when recording or rendering observation ledgers in the graph — capturing a development note, exporting the graph for merge-recovery, or importing it back.

**Walkable skills:** `dogfood-usage`

| verb | role | summary |
|---|---|---|
| `dogfood.collect` | transform | Walk ``plan_dir`` for ``DOGFOOD-NOTES.md`` files; extract observations. |
| `dogfood.export` | effect | Dump the provenance store to a portable JSON file. |
| `dogfood.import` | effect | Replay a JSON export into this graph, preserving ids + windows. |
| `dogfood.note` | act | Record an observation Reflection tagged with plan_slug. |
| `dogfood.render` | transform | Project plan_slug observations into DOGFOOD-NOTES.md. |

## `gate`  (lifecycle)

Use when a programmatic, reusable predicate must pass before work proceeds — an acceptance check recorded as a Gate in the provenance graph.

**Walkable skills:** `gate-usage`

| verb | role | summary |
|---|---|---|
| `gate.check` | act | Record a gate outcome on a Lifecycle: PASSED, or BLOCKED_ON + |

## `intent`  (capability)

Use when examining a goal before committing to an approach — decomposing it, surfacing its assumptions, stress-testing it with a premortem, or weighing trade-offs.

**Walkable skills:** `critical-thinking`

| verb | role | summary |
|---|---|---|
| `intent.assumptions` | transform | Surface + classify the implicit assumptions a goal rests on (load-bearing vs not). |
| `intent.decompose` | transform | Decompose a goal into MECE sub-problems — the structured break-down method. |
| `intent.first_principles` | transform | Strip a goal to fundamental truths and rebuild — bypassing inherited assumptions. |
| `intent.inversion` | transform | Invert the goal — ask what would GUARANTEE failure, then avoid exactly that. |
| `intent.premortem` | transform | Premortem — assume the goal FAILED, reason backward to causes + mitigations. |
| `intent.second_order` | transform | Trace second- and third-order consequences — 'and then what?' past the first effect. |
| `intent.steelman` | transform | Build the STRONGEST version of the opposing or alternative position. |
| `intent.suggests` | transform | Project the serving intent + the last verb's state to the next applicable |
| `intent.tradeoffs` | transform | Build an explicit trade-off matrix — options × criteria — for a decision. |

## `jules`  (lifecycle)

Use when fanning a coding task out to a remote Jules agent session and driving it to a verified PR — dispatching, sending follow-ups, approving plans, and recovering completed-but-unpushed work.

**Walkable skills:** `jules-fanout`, `jules-pr-review-cycle`, `jules-protocol-preamble`, `jules-recovery-when-stuck`, `jules-self-improvement`, `jules-tool-discipline`

| verb | role | summary |
|---|---|---|
| `jules.activities` | transform | A session's activity stream, trimmed to summaries (the costliest Jules read). |
| `jules.alias` | act | Read or upsert a stable alias for a Jules sid. |
| `jules.apply_patch` | transform | Compute a recovery plan for a session's patch (verb mirror of `recover_apply_plan`). |
| `jules.approve_awaiting` | effect | Bulk-approve every session in AWAITING_PLAN_APPROVAL (up to `limit`). |
| `jules.approve_plan` | effect | Approve a plan in AWAITING_PLAN_APPROVAL — the one state that times out. |
| `jules.detect_mode` | transform | Mode A (dogfood) vs Mode B (delegate) — pure decision on dispatch source. |
| `jules.dispatch` | effect | Spawn a remote Jules session (external effect). Returns id/url/state. |
| `jules.lint_prompt` | transform | Lint a dispatch prompt against the canonical must-name tool list. |
| `jules.list` | transform | Enumerate sessions (trimmed to id/state/title/url; one page — walk via token). |
| `jules.message` | effect | Send a message into a session (feedback / plan-revision / nudge to push). |
| `jules.patch` | transform | Per-output stats (``files``, ``lines``, ``bytes``) from the session's outputs — NO body. |
| `jules.patch_body` | transform | Explicit, capped unidiff retrieval for one of the session's outputs. |
| `jules.plan` | transform | The latest generated plan — show it before approve_plan (no PR exists yet). |
| `jules.quota` | transform | Count sessions created today (UTC). |
| `jules.recover` | effect | Promote a session to the watcher's recovery-in-flight tracker. |
| `jules.resolve_source` | transform | Resolve `owner/repo` to the opaque `sources/<id>` the API expects. |
| `jules.review_comment` | transform | Compose an @jules PR review-comment with the mandatory handshake tail. |
| `jules.status` | transform | Read a session's full state from the backend. |
| `jules.status_all` | transform | Paginated, grouped-by-state listing of every session on the account. |
| `jules.stop` | transform | UNSUPPORTED by design: the Jules v1alpha API exposes no cancel/delete/stop. |
| `jules.verify` | transform | COMPLETED != done — verifies the branch landed on origin. |
| `jules.watch` | transform | Await the next `WatchEvent` for a session or intent. |

## `plugin`  (capability)

Use when building or extending a Claude Code plugin — scaffolding a manifest, authoring a skill or command, or linting a capability against the authoring doctrine.

**Walkable skills:** `plugin-dev`, `skill-creation`

| verb | role | summary |
|---|---|---|
| `plugin.author_command` | act | Render a slash-command markdown stub. |
| `plugin.author_skill` | act | Render a CSO-compliant SKILL.md. |
| `plugin.help` | transform | Map the engine's capabilities (macroskills) to their verbs — via ctx.registry. |
| `plugin.lint_capability` | transform | Lint a capability against Hint #7 structural + role-tag + render-slice rules. |
| `plugin.lint_explain` | transform | Return the rework recipe for a lint rule kind (Spec 074) — so you learn HOW to fix it. |
| `plugin.lint_skill` | transform | Lint a skill description against the CSO + length rules. |
| `plugin.marketplace_entry` | act | Render a marketplace.json entry. |
| `plugin.publish_skill` | effect | Publish a capability's Agent Skill to the Anthropic Skills API (Spec 083). |
| `plugin.scaffold` | act | Render the plugin scaffold (plugin.json + .mcp.json). |
| `plugin.step_doc` | act | Render a step-doc markdown block (audit trail entry). |

## `reflect`  (memory)

Use when durable, scope-tagged memory must cross sessions — recording an insight, or recalling prior observations by scope or semantic similarity.

**Walkable skills:** `reflect-usage`

| verb | role | summary |
|---|---|---|
| `reflect.batch_note` | act | Bulk version of ``note``: one Reflection node per text. |
| `reflect.note` | act | Write a scope-tagged insight node; edged OBSERVED_DURING + SERVES the intent. |
| `reflect.recall` | transform | Retrieve reflections, newest first, optionally filtered by scope. |
| `reflect.recall_semantic` | transform | Semantic top-k recall over Reflection nodes; backend-injectable. |
| `reflect.search` | transform | Keyword search over reflection text (deterministic substring match). |

## `research`  (capability)

Use when an open question needs cited evidence from multiple sources — driving a research question through a lead, fan-out specialists, and an adversarial verifier.

**Walkable skills:** `deep-research`

| verb | role | summary |
|---|---|---|
| `research.lead` | act | Scope a research question + plan specialists; mints a Research node. |
| `research.specialist` | act | One bounded sub-search; records Citations under the research_id. |
| `research.verify` | act | Adversarial citation check; emits a Verification node. |

## `shell`  (capability)

Use when running a host CLI command whose output should be token-filtered and recorded — an allowlisted command, a reusable template, or a pure output filter.

**Walkable skills:** `shell-usage`

| verb | role | summary |
|---|---|---|
| `shell.define` | act | Define a named shell template (command + output filter + doc) in the graph. |
| `shell.filter` | transform | Filter text to a token-bounded slice — pure, no execution (hook-ready). |
| `shell.run` | effect | Run an ALLOWLISTED command (or a named template), FILTER its output, record it. |
| `shell.templates` | transform | Discover named query templates — built-in seeds ∪ graph-defined (Spec 075). |

## `skill_generator`  (capability)

Use when a deploy-ready skill should be produced in one call — a complete, CSO-clean SKILL.md generated from a description.

**Walkable skills:** `skill_generator-usage`

| verb | role | summary |
|---|---|---|
| `skill_generator.generate` | act | Author a SKILL.md and lint it against the CSO rules; flag if not deploy-ready. |

## `skills`  (capability)

Use when discovering which walkable skills exist, reading one skill's phases at a chosen depth, or validating a skill's phase-graph shape — before walking, emitting, or authoring a skill.

**Walkable skills:** `skills-triage`

| verb | role | summary |
|---|---|---|
| `skills.find` | transform | Enumerate the walkable skills across all capabilities, with light filters. |
| `skills.index` | effect | Promote walkable skills into the graph as Skill + Phase nodes (Spec 026). |
| `skills.lint` | transform | Validate a skill's phase-graph shape — the structural contract a walk relies on. |
| `skills.render` | transform | Render one skill to markdown at a chosen depth (progressive disclosure). |

## `subagent`  (lifecycle)

Use when a unit of work should be composed as subagent-driven development — isolating a task to a dispatched subagent that returns a verified result.

**Walkable skills:** `subagent-usage`

| verb | role | summary |
|---|---|---|
| `subagent.develop` | effect | Dispatch a worker child via delegate, then gate it spec-review→quality-review; done iff both pass. |

## `workspace`  (lifecycle)

Use when work should be isolated in a git worktree with a recorded green baseline — a clean, provably-green starting point before risky changes.

**Walkable skills:** `workspace-usage`

| verb | role | summary |
|---|---|---|
| `workspace.baseline` | effect | Run the baseline test command in the workspace and record the green/red result. |
| `workspace.isolate` | effect | Create an isolated git worktree on a fresh branch off `base`; record the Workspace. |
