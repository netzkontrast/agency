# Troubleshooting Plugin Development (Generic)

> Generic Claude Code plugin failure modes. For agency-engine-specific
> failures (venv bootstrap, SERVES-guard, ontology-merge,
> `${user_config}` not populated) see [`agency-troubleshooting.md`](agency-troubleshooting.md).

## Plugin not loading

### Symptom
Plugin doesn't appear in `/plugin list` or components are missing.

### Debug steps

1. **Validate `plugin.json`:**
   ```bash
   cat .claude-plugin/plugin.json | jq .
   ```
2. **Verify structure:** `.claude-plugin/` must exist at plugin root and contain `plugin.json`.
3. **Check paths:** `grep -r "/Users/\|/home/" .claude-plugin/` should return nothing — use `${CLAUDE_PLUGIN_ROOT}`.
4. **Restart Claude Code** — changes only take effect after restart.
5. **Verify install:** `/plugin list` should show your plugin.

### Common causes

| Problem | Fix |
|---|---|
| `.claude-plugin/` missing | Create directory with `plugin.json` |
| Invalid JSON | `jq` or any JSON linter |
| Hardcoded paths | Replace with `${CLAUDE_PLUGIN_ROOT}` |
| Forgot to restart | Always restart after install/changes |

## Skill not triggering

### Symptom
Skill exists but Claude doesn't use it when expected.

### Debug steps

1. **YAML frontmatter:**
   ```markdown
   ---
   name: skill-name
   description: Use when [clear trigger] — [what it does]
   ---
   ```
   `---` delimiters, `name` and `description` required, **spaces not tabs**.

2. **Description starts with "Use when…"** — the host's matcher hooks onto that phrase.

   - Bad: `description: A helpful skill`
   - Good: `description: Use when debugging test failures — systematic approach to root cause`

3. **Test explicitly:** ask for a task that matches the trigger phrase verbatim.

4. **Location:** `skills/<skill-name>/SKILL.md` at plugin root — NOT `.claude-plugin/skills/`.

### Common causes

| Problem | Fix |
|---|---|
| Vague description | Make it specific, action-oriented, "Use when…" form |
| Skill in `.claude-plugin/skills/` | Move to `skills/` at plugin root |
| Missing frontmatter | Add YAML with name + description |
| Tabs in YAML | Spaces only |

## Command not appearing

### Symptom
Slash command doesn't show up.

### Debug steps

1. **Location:** `commands/<name>.md` at plugin root.
2. **Frontmatter:**
   ```markdown
   ---
   description: Brief description of what this command does
   ---

   # Command Instructions
   ...
   ```
3. **Restart** Claude Code — commands load at startup.
4. **Extension:** must be `.md`, not `.txt`.

## MCP server not starting

### Symptom
MCP tools not available; server fails silently.

### Debug steps

1. **`${CLAUDE_PLUGIN_ROOT}` everywhere** in MCP config paths.
2. **Executable bit:** `chmod +x server/index.js bin/server.sh`.
3. **Run standalone:** `node /path/to/server/index.js` — does it crash?
4. **Debug logs:** `claude --debug` shows MCP startup errors.
5. **Command exists on PATH:** `which node`, `which python3`.

### Common causes

| Problem | Fix |
|---|---|
| Hardcoded paths | `${CLAUDE_PLUGIN_ROOT}` |
| Not executable | `chmod +x` |
| Command not on PATH | Full path or detection script (e.g. agency's `bin/agency-mcp`) |
| Missing deps | `npm install` / `pip install` |
| Server crashes on startup | Run standalone; read stderr |

For agency-specific: read [`agency-troubleshooting.md`](agency-troubleshooting.md).

## Hooks not firing

### Symptom
Hook scripts exist but don't execute.

### Debug steps

1. **Location:** `hooks/hooks.json` at plugin root.
2. **Valid JSON:** `jq . hooks/hooks.json`.
3. **Matcher syntax** (regex on tool name):
   ```json
   { "matcher": "Write|Edit" }
   ```
4. **Script paths use `${CLAUDE_PLUGIN_ROOT}`.**
5. **Executable:** `chmod +x scripts/*.sh`.
6. **Test standalone:** run the script manually.

## Development workflow issues

### Can't install locally

`/plugin install my-plugin@my-dev` fails:

1. `.claude-plugin/marketplace.json` exists?
2. Marketplace added? `/plugin marketplace list`.
3. `marketplace.json` format:
   ```json
   {
     "name": "my-dev",
     "plugins": [{ "name": "my-plugin", "source": "./" }]
   }
   ```

### Changes not taking effect

1. Uninstall → modify → reinstall → restart:
   ```bash
   /plugin uninstall my-plugin@my-dev
   /plugin install my-plugin@my-dev
   ```
2. For hooks / MCP changes, restart is mandatory.
3. For SKILL.md / command content, sometimes works without restart — but always safer to restart.

## Common pitfalls

| Mistake | Why it fails | Fix |
|---|---|---|
| Skills in `.claude-plugin/skills/` | Host looks in `skills/` at root | Move to plugin root |
| Hardcoded absolute paths | Breaks on other systems | `${CLAUDE_PLUGIN_ROOT}` |
| Forgot to restart | Changes load at startup | Always restart |
| Script not executable | Shell can't run it | `chmod +x` |
| Invalid JSON | Parser fails silently | `jq` validation |
| Vague skill description | Claude doesn't know when to use it | "Use when…" + specific trigger |
| Testing without uninstall | Old version cached | Uninstall first |
| Bare `owner/name` marketplace source | Invalid shape | `{source: github, repo: "owner/name"}` |

## Debugging workflow

When something doesn't work:

1. **Validate all JSON:**
   ```bash
   jq . .claude-plugin/plugin.json
   jq . .claude-plugin/marketplace.json
   jq . hooks/hooks.json 2>/dev/null
   jq . .mcp.json 2>/dev/null
   ```
2. **Hunt hardcoded paths:** `grep -rE "/Users/|/home/[a-z]+/" .claude-plugin/ .mcp.json hooks/ 2>/dev/null`.
3. **Permissions:** `find . -name "*.sh" -o -name "*.cmd" | xargs ls -l` — check the `x` bit.
4. **Test independently** — MCP server / hook script in isolation.
5. **Clean reinstall:**
   ```bash
   /plugin uninstall my-plugin@my-dev
   /plugin marketplace remove /path/to/plugin
   /plugin marketplace add /path/to/plugin
   /plugin install my-plugin@my-dev
   ```
6. **Logs:** `claude --debug`.

## Getting help

1. Generic CC docs via `working-with-claude-code` skill.
2. Example plugins in `~/.claude/plugins/`.
3. **Simplify** — strip components until it works; add back one at a time.
4. Report: https://github.com/anthropics/claude-code/issues.

When asking, include: `plugin.json`, `tree -L 3 -a` of the plugin, exact error messages, what you tried.
