# Plugin Patterns (as agency uses them)

> Reframe the canonical Claude Code plugin patterns through how THIS plugin
> composes them. For the inner engine patterns (capability, skill-walker,
> driver, substrate tool) see [`agency-patterns.md`](agency-patterns.md).

The agency plugin is itself a composition of several patterns. This file
walks each pattern, names where agency uses it (or deliberately doesn't),
and gives the rule for when you'd add the pattern.

## Pattern: MCP plugin with skill (the spine of agency)

**Agency uses this as its primary shape.** The FastMCP server provides the
*capability* (`search` / `get_schema` / `execute` + 50+ auto-wired tools);
the bundled skills provide the *judgement* (when to call what, in what
order, with which gates).

```
agency/
├── .claude-plugin/plugin.json         # advertises the plugin
├── .mcp.json                          # points at bin/agency-mcp
├── bin/agency-mcp                     # the MCP entrypoint
├── agency/                            # the server (python package)
└── skills/
    ├── plugin-development/            # outer lens (this skill)
    ├── authoring-capabilities/        # inner lens
    ├── skill-creation/                # skill authoring
    └── …
```

**Key insight:** code-mode IS the contract. The MCP server exposes
`search`/`get_schema`/`execute`; the skills teach you what to do with that
tiny surface (mint an intent, search for a verb, get its schema, execute
the chain).

**When to add this pattern (to a new plugin):**
- Your plugin ships tool capability (an MCP server).
- AND you want Claude to use it idiomatically — not just technically.
- Don't ship MCP without a skill teaching its use.

## Pattern: Skill with bundled resources (this skill IS this pattern)

When a skill needs reference material that would bloat SKILL.md, pull it
out into `references/`:

```
skills/plugin-development/         ← this skill
├── SKILL.md                       ← the workflow + pointers
└── references/
    ├── plugin-structure.md
    ├── common-patterns.md         ← this file
    ├── polyglot-hooks.md
    ├── troubleshooting.md
    ├── agency-patterns.md
    ├── release-and-distribution.md
    └── related-skills.md
```

The SKILL.md tells Claude "read `references/agency-patterns.md` for the
inner engine patterns". The references stay loaded only when actually
needed — keeps token cost low.

`skills/authoring-capabilities/` is the opposite extreme — 43 LOC,
references-free, because the deep doctrine lives in
`docs/vision/CAPABILITY-AUTHORING.md` (a doctrine doc, not a skill ref).

**When to add bundled resources:**
- A SKILL.md crosses ~150 LOC and you can name a coherent sub-topic.
- Multiple tasks under the same skill need different deep dives.
- You want token cost to scale with what's needed, not skill size.

## Pattern: Command collection (auto-generated)

Agency ships slash-commands at `commands/agency-*.md` but **never authors
them by hand**. The generator (`python -m agency.install`) writes one
command file per macroskill (capability cluster), listing its verbs.

```
commands/
├── agency-plugin.md       # auto: lists capability_plugin_*  verbs
├── agency-develop.md      # auto: lists capability_develop_* verbs
└── …
```

Format (per command file):
```markdown
---
description: <macroskill summary>
---

# /agency:<macroskill>
List of verbs (verb → brief slice from docstring)
```

**When to add a command collection (manually):**
- Project-specific workflows the engine can't infer (`/deploy-staging`,
  `/incident-report`).
- Don't compete with the auto-generated ones — name them outside
  `agency-*` to avoid confusion.

## Pattern: Hook-enhanced workflow (agency doesn't ship hooks today)

Agency ships **zero hooks**. Three reasons:
1. The engine's `lifespan` (FastMCP) already starts/stops the Jules watcher
   at server bind/unbind — that's where lifecycle hooks would otherwise
   land.
2. SessionStart for `.agency/` scaffolding could be a hook, but the
   substrate tool `agency_install` does it on demand instead (idempotent,
   no auto-fire).
3. Doctrine: every effect should record provenance. A hook that auto-runs
   has no `intent_id` to SERVES against — would violate the SERVES guard.

**If we ever add a hook**, the cross-platform polyglot pattern (see
[`polyglot-hooks.md`](polyglot-hooks.md)) is mandatory. Hook events:
`PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `SessionStart`,
`SessionEnd`, `Stop`, `SubagentStop`, `PreCompact`, `Notification`.

**When to add hooks (to any plugin):**
- You need to automate actions in response to host events Claude can't
  trigger explicitly.
- The automation is genuinely a side-effect, not something the agent
  should choose to do.
- Warning: hooks that block operations disrupt flow. Make failure
  messages clear.

## Pattern: Domain extension via `examples/`

Agency demonstrates a non-core extension pattern: domain capabilities load
from `examples/` (not `agency/capabilities/`) via the
`extra_capabilities=` engine argument.

```python
# examples/music.py
class MusicCapability(CapabilityBase):
    name = "music"
    home = "domain"
    ontology = OntologyExtension(...)
    @verb(role="act")
    def conceptualize(self, ...): ...

# in a host script:
from examples.music import MusicCapability
engine = Engine(":memory:", extra_capabilities=[MusicCapability.as_capability()])
```

This is the **third-party extension seam** — a way to ship domain
capabilities OUT of the core engine's package while still using the
auto-discovery contract. Auto-discovery doesn't reach `examples/`; the
host must wire it explicitly.

Counter-example: Spec 010 elevates `novel` from `examples/` to
`agency/capabilities/novel/` — because the Kohärenz-Protokoll project
IS the substrate's primary application, not a third-party demo.

**When to add a capability to `examples/` vs. `agency/capabilities/`:**
- `examples/` → demonstration, third-party domain, optional dep.
- `agency/capabilities/` → core or canonical user-facing, always available,
  auto-discovered.

## Pattern: Full-featured plugin (agency at scale)

Agency combines:
- **MCP+skill** (FastMCP server + multiple bundled skills)
- **Skill with bundled resources** (this skill — SKILL.md + 7 references)
- **Auto-generated command collection** (commands/agency-*.md)
- **Domain extension seam** (examples/)
- **Substrate tools** beyond the per-capability auto-wire (the four bootstrap
  tools — see [`agency-patterns.md`](agency-patterns.md))

That's a lot. **Caution from CLAUDE.md:** "start simple, add complexity
only when justified." Most plugins don't need all components. Agency's
breadth is justified by being a meta-tool (an engine on which to build),
not by the slot existing.

## Pattern: Hidden / not-yet-built — multi-server MCP client

A pattern agency **deliberately doesn't ship** but has a slot for: an MCP
client that talks to *other* MCP servers (stdio or HTTP). Today the
`delegate` capability fans out to local subagents and to Jules; an MCP
client would let it fan out to any installed MCP server in the host.

That's tracked as a follow-up to Spec 039 (architecture-review finding
F6 in this branch's audit conversation). Until shipped: don't reach
across MCP servers from inside agency.

## Choosing the right pattern

| Your goal | Pattern |
|---|---|
| Add a capability/verb to the agency engine | "Add a file" in `agency/capabilities/` — see [`agency-patterns.md`](agency-patterns.md) |
| Build a domain extension that lives outside core | Domain via `examples/` |
| Add a multi-step authoring discipline with phases + gates | Skill walker — `OntologyExtension.skills` |
| Add an external integration (effect verb) | Boundary driver — see [`agency-patterns.md`](agency-patterns.md) |
| Add a slash-command that lists my new verb | Nothing — regen via `python -m agency.install` |
| Add a SKILL.md to teach Claude a new workflow | Skill (this directory) — use `agency:skill-creation` |
| Make a SKILL.md grow without bloating | Bundled resources — `references/` |
| Build a generic Claude Code plugin (not agency-based) | See the Superpowers `developing-claude-code-plugins` skill |

## Combining patterns — the agency authoring loop

A real authoring session in this repo typically chains:

1. **Substrate** — `agency_welcome` → `agency_install` → `intent_bootstrap`
   (mint the Intent; only substrate tools work without an intent_id).
2. **Capability** — `capability_develop_scaffold_capability` (scaffold a
   new file with the `# agency-scaffold: v1` marker).
3. **Lint** — `capability_plugin_lint_capability` ok=True in block mode.
4. **Skill walker** (if needed) — declare the walker in the capability's
   `OntologyExtension.skills`.
5. **Driver** (if needed) — boundary client injected via `Engine(...,
   jules_client=…)` for tests, real one in prod.
6. **Regen + commit** — `python -m agency.install` to refresh
   `plugin.json` / `.mcp.json` / slash-commands.

Each step uses a pattern from this file or [`agency-patterns.md`](agency-patterns.md).
Composition is the whole point — none of these patterns is meant to stand
alone.
