# SOURCES.md — source repositories for the PR1 review

Candidate repositories each research agent may read. **You decide which you can
cleanly check out** (per `JULES_RESEARCH_PROTOCOL.md` §3): try each clone; if one
fails (auth / 404 / network), record `[BLOCKED: source <name>]` in your PR body
with the exact error and continue with the sources you do have. Public repos clone
without credentials; private repos require the Jules GitHub app to have access.

Clone **read-only** into `~/work/vendor/<name>/` — never inside the work repo,
never committed into the Agency repo. Cite by URL + the cloned commit SHA.

## Work repo (clone to commit into)

| Name | URL | Branch | Role |
|---|---|---|---|
| `agency` | `https://github.com/netzkontrast/agency` | `claude/extract-agency-plugin-o4JRc` | **PR1** — your primary subject AND your work repo; open your PR into this branch |

```bash
# work repo (already your checkout; this is the branch under review)
git clone --branch=claude/extract-agency-plugin-o4JRc \
  https://github.com/netzkontrast/agency.git ~/work/agency
```

## Reference repos (read-only)

| Name | URL | Ref | Why |
|---|---|---|---|
| `the-agency-system` | `https://github.com/netzkontrast/the-agency-system` | default (`Master`) | the **`Plan/` dir** (specs 001–023, `harness/`, `decisions/`, `REFACTOR_DESIGN.md`, `JULES_PROTOCOL.md`) — the prior art for code-mode + context-mode + ontology graph |
| `superpowers-marketplace` | `https://github.com/obra/superpowers-marketplace` | `main` | **all superpowers plugins/skills** — the disciplines PR1's `develop`/`gate`/`workspace`/`branch` port |
| `SuperClaude_Framework` | `https://github.com/SuperClaude-Org/SuperClaude_Framework` | default | the SuperClaude analyst agents + command framework (capability-mapping input) |
| `SuperClaude_Plugin` | `https://github.com/SuperClaude-Org/SuperClaude_Plugin` | default | the SuperClaude Claude-Code plugin packaging (skills/commands/agents) |
| `bitwize-music` | `https://github.com/bitwize-music-studio/claude-ai-music-skills` | `v0.91.0` | the music-domain handlers/skills PR1's `examples/music.py` distils |

```bash
git clone --depth=1 https://github.com/netzkontrast/the-agency-system.git        ~/work/vendor/the-agency-system
git clone --depth=1 https://github.com/obra/superpowers-marketplace.git          ~/work/vendor/superpowers-marketplace
git clone --depth=1 https://github.com/SuperClaude-Org/SuperClaude_Framework.git ~/work/vendor/superclaude-framework
git clone --depth=1 https://github.com/SuperClaude-Org/SuperClaude_Plugin.git    ~/work/vendor/superclaude-plugin
git clone --depth=1 --branch=v0.91.0 \
  https://github.com/bitwize-music-studio/claude-ai-music-skills.git             ~/work/vendor/bitwize-music
```

## Framework docs (read via WebFetch, not cloned)

| Doc | URL |
|---|---|
| Claude Code Plugins | https://code.claude.com/docs/en/plugins |
| Claude Code Plugins Reference | https://code.claude.com/docs/en/plugins-reference |
| FastMCP | https://gofastmcp.com |
| FastMCP Code Mode | https://gofastmcp.com/servers/transforms/code-mode |
