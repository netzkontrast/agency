# Plugin Structure Reference

> Generic Claude Code plugin contract. For agency-engine-specific patterns
> (capability folder, scaffold marker, lint gate, install regen) see
> [`agency-patterns.md`](agency-patterns.md).

## Standard Directory Layout

All paths relative to plugin root:

```
my-plugin/
├── .claude-plugin/
│   ├── plugin.json          # REQUIRED - plugin metadata
│   └── marketplace.json     # Optional - for local dev/distribution
├── skills/                  # Optional - Agent Skills
│   └── skill-name/
│       ├── SKILL.md         # Required for each skill
│       ├── scripts/         # Optional - executable helpers
│       ├── references/      # Optional - documentation
│       └── assets/          # Optional - templates/files
├── commands/                # Optional - custom slash commands
│   └── command-name.md
├── agents/                  # Optional - specialized subagents
│   └── agent-name.md
├── hooks/                   # Optional - event handlers
│   └── hooks.json
├── .mcp.json                # Optional - MCP server config
├── LICENSE
└── README.md
```

## Critical Rules

### 1. `.claude-plugin/` contains ONLY manifests

**WRONG:**
```
.claude-plugin/
├── plugin.json
├── skills/              # NO — skills don't go here
└── commands/            # NO — commands don't go here
```

**CORRECT:**
```
.claude-plugin/
├── plugin.json          # Only manifests
└── marketplace.json     # Only manifests

skills/                  # Skills at plugin root
commands/                # Commands at plugin root
```

### 2. Always use `${CLAUDE_PLUGIN_ROOT}` for paths in config

**WRONG — hardcoded:**
```json
{ "mcpServers": { "my-server": { "command": "/Users/name/plugins/my-plugin/server.js" } } }
```

**CORRECT — variable:**
```json
{ "mcpServers": { "my-server": { "command": "${CLAUDE_PLUGIN_ROOT}/server.js" } } }
```

`${CLAUDE_PLUGIN_ROOT}` is provided by the harness at launch. `${CLAUDE_PROJECT_DIR}` is the user's project working directory — different concept, often confused. See [`agency-troubleshooting.md`](agency-troubleshooting.md) for the agency `.mcp.json` pattern.

### 3. Use relative paths in `plugin.json`

All paths in `plugin.json` must start with `./` and be relative to plugin root.

## Plugin Manifest (`plugin.json`)

### Minimal

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Brief description of what the plugin does",
  "author": { "name": "Your Name" }
}
```

### Complete

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Comprehensive plugin description",
  "author": { "name": "Your Name", "email": "you@example.com" },
  "homepage": "https://github.com/you/my-plugin",
  "repository": "https://github.com/you/my-plugin",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"],
  "mcpServers": {
    "server-name": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/path/to/server.js"],
      "env": { "ENV_VAR": "value" }
    }
  }
}
```

### Path conventions in `plugin.json`

- `skills` (path) — **extends** the default `skills/` directory.
- `commands` (path) — **replaces** the default `commands/` directory.
- `agents` (path) — **replaces** the default `agents/` directory.

This asymmetry catches first-time authors. If you set `"commands": "./custom-commands/"`, the default `commands/` is no longer scanned.

## Development Marketplace (`marketplace.json`)

For local testing, create in `.claude-plugin/`:

```json
{
  "name": "my-plugin-dev",
  "description": "Development marketplace",
  "owner": { "name": "Your Name" },
  "plugins": [
    {
      "name": "my-plugin",
      "description": "Plugin description",
      "version": "1.0.0",
      "source": "./",
      "author": { "name": "Your Name" }
    }
  ]
}
```

**Install:**
```bash
/plugin marketplace add /path/to/my-plugin
/plugin install my-plugin@my-plugin-dev
```

### Marketplace `source` shapes

| Shape | Use for |
|---|---|
| `"./"` | Local dev marketplace (relative to marketplace.json) |
| `{"source": "github", "repo": "owner/name"}` | GitHub repo |
| `{"source": "url", "url": "https://..."}` | Generic git URL |

> Common mistake: bare `"owner/name"` as `source` is invalid — must be a `{source: github, repo: ...}` object.

## Component Formats

### Skills (`skills/skill-name/SKILL.md`)

```markdown
---
name: skill-name
description: Use when [triggering conditions] — [what it does]
---

# Skill Name

## Overview
What this skill does in 1-2 sentences.

## When to Use
- Specific scenario 1
- Specific scenario 2

## Workflow
1. Step one
2. Step two
```

Skill name must be **kebab-case**. Description must start with **"Use when…"** — that phrase is what the host's skill-matcher hooks onto. See the agency `skill-creation` skill for the full Claude-Skill Ontology lint.

### Commands (`commands/command-name.md`)

```markdown
---
description: Brief description of what this command does
---

# Command Instructions
What Claude should do when this command is invoked.
```

### Hooks (`hooks/hooks.json`)

> **WARNING — duplicate hooks file:** `hooks/hooks.json` is auto-loaded. Do NOT also reference it in `plugin.json`'s `hooks` field — that causes "Duplicate hooks file detected" errors.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command",
            "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd\" format.sh" }
        ]
      }
    ]
  }
}
```

**Cross-platform hooks:** use the polyglot `run-hook.cmd` wrapper — see [`polyglot-hooks.md`](polyglot-hooks.md).

**Available hook events:** `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `SessionStart`, `SessionEnd`, `Stop`, `SubagentStop`, `PreCompact`, `Notification`.

### MCP servers — two patterns

**A) In `plugin.json` (inline):**
```json
{
  "mcpServers": {
    "server-name": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/server/index.js"],
      "env": { "API_KEY": "${user_config.api_key}" }
    }
  }
}
```

**B) Separate `.mcp.json` file (the agency pattern):**
```json
{
  "mcpServers": {
    "agency": {
      "command": "${CLAUDE_PLUGIN_ROOT}/bin/agency-mcp",
      "args": [],
      "env": {
        "PYTHONPATH": "${CLAUDE_PLUGIN_ROOT}",
        "AGENCY_DB": "${CLAUDE_PROJECT_DIR}/.agency/session.db",
        "JULES_API_KEY": "${user_config.jules_api_key}"
      }
    }
  }
}
```

`${user_config.X}` reads from the `userConfig` block in `plugin.json` — Claude Code surfaces these in the install UI and stores secrets in the OS keychain.

### Agents (`agents/agent-name.md`)

```markdown
---
description: What this agent specializes in
capabilities: ["capability1", "capability2"]
---

# Agent Name
When to invoke this specialized agent.
```

## File Permissions

Scripts must be executable. Set the bit AND commit it:
```bash
chmod +x scripts/helper.sh bin/server
git update-index --chmod=+x scripts/helper.sh bin/server
```

The second line matters: `chmod` without `git update-index` will revert on the next `git stash`/`checkout`.
