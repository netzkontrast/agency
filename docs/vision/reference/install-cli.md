# The three surfaces — install, CLI, MCP

<!-- doc-source: agency/install.py agency/cli.py -->
<!-- doc-hash: ae39bdc0f7ea4944 -->

Agency presents the same capability surface three ways, all generated from the live
registry. Code-mode (MCP) is canonical; the others are mirrors.

## 1. MCP code-mode (canonical)

The engine's `build_mcp` exposes `search · get_schema · execute` over JSON-RPC (what
`.mcp.json` launches as `agency-mcp`). In code-mode the agent writes a program that
chains `call_tool("capability_<cap>_<verb>", {...})` in the sandbox; only the return
crosses back. This is the contract — see [overview.md](overview.md).

## 2. The bash CLI (`agency/cli.py`, Spec 079)

A Click CLI for non-MCP / bash-only agents, **auto-generated** from the registry:

- **Per-verb mirror** — `agency <capability> <verb> --param … --intent-id …`, one Click
  group per capability with its verbs as subcommands, built at import from `discover()`.
  Routes through the *same* engine path (`call_tool` → `registry.invoke`).
- **Static commands** — `execute`, `get-schema`, `search`, `intent` (the capture
  side-pipe), `welcome`, `doctor`, `provenance`, `install`, `uninstall`, `hook`.
- **Collision rule (OQ-3)** — a capability whose name matches a static command (e.g.
  `intent`) has its CLI *group* skipped (the legacy command wins); the capability stays
  reachable via MCP, code-mode, and the `bin/agency-<cap>-<verb>` wrappers.

`--intent-id` defaults to `$AGENCY_INTENT` (Spec 018) so a bash agent stays
self-sufficient.

## 3. The plugin install (`agency/install.py`)

`python -m agency.install` (or `agency install`) regenerates the Claude Code plugin
surface from the registry — **everything is derived**:

- `skills/<cap>/SKILL.md` + `references/<verb>.md` (the Agent Skills, Spec 080/081),
- `bin/agency-<cap>-<verb>` per-verb wrappers,
- `hooks/` (the unified event hook, Spec 076), `commands/`, the manifest + marketplace
  entry.

Because it's all rendered, **adding a capability folder regenerates a complete install**
— the drop-in bar. A self-hosted install-drift check gates merge (the regen must equal
what's committed). The regen also **prunes** generator-owned files (`bin/agency-<cap>-*`
wrappers + `skills/<cap>/references/*.md`) that no longer map to a live verb (Spec 092
G1), and `check-drift` flags any committed orphan the prune removes — so a removed/renamed
verb never leaves a stale file behind.

## 4. Multi-agent self-install (`--agent`, Spec 333)

`agency install --agent <name>` projects the live **`surface_card`** (the capability
roster + the access recipe + the Spec 332 frugal discipline, imported from `_frugal`)
into another agent's native instruction file — `cursor` · `windsurf` · `cline` ·
`kiro` · `copilot` · `agents` (the universal `AGENTS.md`), or `all`. Each file carries
the **compact** projection — the discipline + the `agency search` / `agency <cap>
<verb>` / `agency_welcome` entry pointers, **not** the ~200-verb index (the agent
discovers verbs on demand via the CLI, exactly as an MCP client does via `search`) —
and opens with the pipx **bootstrap** line. The block is wrapped in a fenced
`<!-- agency:auto:start -->…<!-- agency:auto:end -->` anchor (Spec 292) and **merged,
never clobbered**: a re-install replaces the block, an unfenced user file gets a fresh
appended block. Each adapter succeeds or fails **independently** (a per-adapter report;
re-running is the idempotent recovery), and the single `surface_card` is drift-gated
(every adapter must carry the safety floor). `claude` (the default — no `--agent`) is
the MCP plugin install in §3; `agency uninstall --agent <name>` removes only the block;
MCP exposes the same via `agency_install(agent=…)`. Wave 2 MCP runtimes
(Codex/Gemini/pi/opencode) are deferred to Spec 335.

The unified config (`.agency/config.yaml`, Spec 334) is scaffolded by `agency install`
/ `scripts/setup` and repaired on SessionStart; `agency-doctor --write-config`
regenerates any missing keys non-destructively, and `agency_doctor` reports each key's
resolved value + source (secrets redacted), the frugal level, and the installed agents.
