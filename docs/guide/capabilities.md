# Capability reference

The plugin ships **14 core capabilities**. Each is a folder in
`agency/capabilities/<cap>/` (Spec 060 folder form) that self-registers; the
engine wires one tool per verb, named `capability_<capability>_<verb>`.
Verbs are role-tagged **act** (writes a crafted artefact), **transform**
(pure compute), or **effect** (touches the world). Each capability owns its
own `templates/` + `schemas/` (Spec 060 file-based extension). Get the live
map any time with `/agency:help` or `capability_plugin_help`.

## Authoring

### `plugin` — develop Claude Code plugins
The plugin-development craft: scaffold a manifest, author skills/commands,
marketplace entries, and lint skills (the skill-description rules as enforceable
compute). The engine uses it to author its own install.

| verb | role | does |
|---|---|---|
| `scaffold` | act | render a `plugin.json` manifest |
| `author_skill` | act | render a `SKILL.md` (frontmatter + body) |
| `author_command` | act | render a slash-command markdown |
| `marketplace_entry` | act | render one marketplace `plugins[]` entry |
| `step_doc` | act | render a prestructured step document |
| `lint_skill` | transform | check a skill name/description against the rules |
| `lint_capability` | transform | 7-rule lint (Hint #7 docstring contract, wire-shape, render-slice, role-tag, token-budget, reflection-link, node-id guards) |
| `help` | transform | map every capability to its verbs |

### `skill_generator` — one-shot, deploy-ready skill
| verb | role | does |
|---|---|---|
| `generate` | act | compose `plugin.author_skill` + `lint_skill` into a lint-clean SKILL.md |

### `develop` — the development disciplines
The dev-workflow disciplines as walkable, gated skills: `brainstorm · plan · tdd ·
debug · verify · spec-panel · review · execute`.

| verb | role | does |
|---|---|---|
| `checklist` | transform | return a discipline's ordered phases |
| `reference` | transform | fetch a discipline's heavy how-to on demand (testing-skills, skill-descriptions, best-practices) |
| `scaffold_capability` | act | emit a CAPABILITY-AUTHORING.md-compliant folder skeleton (light/medium/heavy) — lint-clean by construction |
| `record_authoring_outcome` | act | record a Reflection at the end of the authoring-capabilities walk |

## Orchestration

### `delegate` — fan a task across agents
An agent **is** a Lifecycle parameterization, so fan-out opens one child Lifecycle
per unit of work.

| verb | role | does |
|---|---|---|
| `dispatch_decision` | transform | 11-signal heuristic — inline vs local-subagent vs Jules vs MCP (Spec 040) |
| `dispatch_bash_hints` | transform | compose `grep`/`find` hints (shlex-quoted) for a dispatch prompt |
| `fan_out` | effect | dispatch a driver across items (capped by a quota); each child `SERVES` the intent |
| `join` | act | reduce over the children's state; `done` only when all completed |

### `subagent` — subagent-driven development
| verb | role | does |
|---|---|---|
| `develop` | effect | dispatch a worker child (via `delegate`), then a two-stage gated review (spec → quality); done iff both gates pass |

### `gate` — a reusable hard-gate predicate
| verb | role | does |
|---|---|---|
| `check` | act | record a PASSED gate, or a BLOCKED_ON gate + an `input-required` pause on failure |

## Development workflow (VCS)

These reach git through an injected boundary, so tests never touch a real repo.

### `workspace` — isolate work
| verb | role | does |
|---|---|---|
| `isolate` | effect | create a worktree on a fresh branch; record the Workspace |
| `baseline` | effect | run the test command in the workspace; record the green/red baseline |

### `branch` — finish a development branch
| verb | role | does |
|---|---|---|
| `assess` | transform | read ahead/behind/dirty; recommend merge / pr / keep / discard |
| `finish` | effect | execute the chosen action; record the outcome |

## Agents

### `jules` — remote async coding agent (22 verbs)
Full v1alpha session lifecycle plus the four-case `COMPLETED ≠ done` recovery
flow per `AGENCY_PROTOCOL.md`.

| verb | role | does |
|---|---|---|
| `dispatch` | effect | start a remote Jules session (needs `JULES_API_KEY`) |
| `status` / `list` / `activities` / `plan` | transform | read session state |
| `approve_plan` / `message` / `approve_awaiting` | effect | drive the session |
| `verify` | transform | `COMPLETED ≠ done` — done only if completed AND the branch is on origin |
| `watch` | transform | await the next `WatchEvent` for a session or intent |
| `recover` / `apply_patch` | effect/transform | silent-fail recovery — promote to the recovery-in-flight tracker and compute the recovery plan |
| `lint_prompt` / `review_comment` / `detect_mode` | transform | dispatch-prompt CSO lint, @jules review-comment composer, Mode-A/B detection |
| `patch` / `patch_body` | transform | per-output diff stats; capped unidiff retrieval |
| `quota` / `status_all` / `resolve_source` / `alias` / `stop` | mixed | operational hygiene |

## Analysis

### `analyze` — decidable code analysis (Spec 042 + Spec 048)
4-axis analysis (quality/security/performance/architecture) + Spec 048 `paths`
axis. Composes optional ruff / bandit / radon via the `[analyze]` extra.

| verb | role | does |
|---|---|---|
| `run` | act | walk a path, emit Findings tagged by axis + severity |
| `improve` | act | render an improvement plan from an Analysis (axis-filtered, IP* paths-aware) |
| `cleanup` | effect | apply mechanical cleanups surfaced by `architecture` |
| `quality` / `security` / `performance` / `architecture` / `paths` | transform | per-axis run for targeted scans |

### `research` — deep-research flow (Spec 044)
| verb | role | does |
|---|---|---|
| `lead` | act | mint a Research node with the question + status enum |
| `specialist` | act | run one bounded specialist (codebase / prior-reflections / doc-corpus / web), records Citations |
| `verify` | act | adversarial citation check; emits a Verification node + rolls verdict back onto the Research node |

### `document` — graph state → markdown (Spec 043)
| verb | role | does |
|---|---|---|
| `render` | transform | project graph state to markdown (5 scopes: install-artefacts, reflections, provenance, capability-catalogue, research-report) |
| `explain` | act | deterministic code → markdown explanation; emits a Reflection (3 depths) |
| `index_repo` | effect | walk a repo, render PROJECT_INDEX.md (94% token reduction; self-test < 3K tokens) |

## Memory

### `reflect` — durable cross-session memory
| verb | role | does |
|---|---|---|
| `note` | act | write a scope-tagged insight (surfaces in provenance) |
| `batch_note` | act | bulk-write one Reflection per text (handy for `dogfood.collect` migration) |
| `recall` | transform | retrieve reflections, newest first, optionally by scope |
| `search` | transform | keyword search over reflection text |
| `recall_semantic` | transform | top-k semantic recall (TF-IDF default; BGE via `[recall]` extra; zero-score filtered) |

### `dogfood` — graph-native observation ledgers (Spec 017 + Spec 020)
| verb | role | does |
|---|---|---|
| `note` | act | record a per-plan Reflection (replaces DOGFOOD-NOTES.md markdown round-trips) |
| `render` | transform | project per-plan Reflections back to DOGFOOD-NOTES.md (token-budgeted) |
| `export` | effect | dump the bi-temporal graph to JSON (merge-conflict recovery; Spec 020) |
| `import` | effect | replay a JSON export preserving original ids + vfrom/vto windows |
| `collect` | transform | legacy walk of `Plan/**/DOGFOOD-NOTES.md` → texts (one-shot migration only) |

## Substrate tools (not capabilities — wired directly)

The engine ships 4 substrate tools alongside the 3 code-mode contract verbs
(`search` · `get_schema` · `execute`):

| tool | does |
|---|---|
| `agency_welcome` | onboarding payload — the live capability list + bootstrap example; **call first** |
| `intent_bootstrap` | mint AND confirm an Intent; the only tool that doesn't require an existing `intent_id` |
| `agency_install` | scaffold `.agency/` + CLAUDE.md snippet in the current target repo (idempotent) |
| `agency_doctor` | health check (python version, deps, DB reachability, JULES_API_KEY presence) |

## Domain capabilities live in `examples/`

Domain bundles are **not** in the core — they load via the extension point so the
bootstrapping harness stays minimal. See `examples/music.py` (an album
conceptualizer) and [extending.md](extending.md).
