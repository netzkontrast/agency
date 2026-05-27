# Capability reference

The plugin ships **10 core capabilities**. Each is a file in
`agency/capabilities/` that self-registers; the engine wires one tool per verb,
named `capability_<capability>_<verb>`. Verbs are role-tagged **act** (writes a
crafted artefact), **transform** (pure compute), or **effect** (touches the
world). Get the live map any time with `/agency:help` or `capability_plugin_help`.

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

## Orchestration

### `delegate` — fan a task across agents
An agent **is** a Lifecycle parameterization, so fan-out opens one child Lifecycle
per unit of work.

| verb | role | does |
|---|---|---|
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

### `jules` — remote async coding agent
| verb | role | does |
|---|---|---|
| `dispatch` | effect | start a remote Jules session (needs `JULES_API_KEY`) |
| `status` | transform | read a session's state |
| `verify` | transform | `COMPLETED ≠ done` — done only if completed AND the branch is on origin |

## Memory

### `reflect` — durable cross-session memory
| verb | role | does |
|---|---|---|
| `note` | act | write a scope-tagged insight (surfaces in provenance) |
| `recall` | transform | retrieve reflections, newest first, optionally by scope |
| `search` | transform | keyword search over reflection text |

## Domain capabilities live in `examples/`

Domain bundles are **not** in the core — they load via the extension point so the
bootstrapping harness stays minimal. See `examples/music.py` (an album
conceptualizer) and [extending.md](extending.md).
