<!-- agency-note: knowledge reference authored 2026-06-19 for Spec 327; intent:7509dac0 -->
# Ponytail multi-agent packaging — mechanism + agency installer crosswalk

> How ponytail ships ONE ruleset to ~14 agent runtimes from a single source, and
> how that maps onto agency's self-installer (Spec 327, Wave 1). Source analysis +
> per-file Index live in
> [`../../326-ponytail-port/reference/OVERVIEW.md`](../../326-ponytail-port/reference/OVERVIEW.md);
> raw vendored source is under `326-ponytail-port/reference/`.

## 1. The pattern: one source → many native formats, drift-gated

Ponytail never hand-maintains 14 copies. It keeps **two canonical sources** and
**generates / verifies** everything else:

- **`AGENTS.md`** — the canonical *compact* ruleset body. Every instruction-file
  adapter is a frozen copy of it (host-specific frontmatter stripped).
- **`skills/ponytail/SKILL.md`** — the *runtime* source (fuller than AGENTS.md);
  the hook lane and the OpenClaw package render from it.

Two guards keep the set honest (`scripts/`):

- **`check-rule-copies.js`** — asserts each copy (`.cursor/rules/ponytail.mdc`,
  `.windsurf/rules/`, `.clinerules/`, `.agents/rules/`, `.github/copilot-instructions.md`,
  `.kiro/steering/`) is **byte-equal to the canonical `AGENTS.md` body**, AND that
  a set of **safety invariants** (`input validation at trust boundaries`,
  `prevents data loss`, `security`, `accessibility`, `ONE runnable check`, …)
  appear verbatim in BOTH `SKILL.md` and `AGENTS.md`. A reworded rule trips it →
  the reminder to propagate everywhere.
- **`build-openclaw-skills.js`** — *generates* `.openclaw/skills/*/SKILL.md` from
  `skills/` (verbatim body, short rewritten frontmatter); a test fails if stale.

**Lesson for agency:** the copies are the liability; the **source + the
generator + the drift gate** are the asset. Spec 327 keeps ONE source
(`install.surface_card` + `_discipline.py`) and treats every adapter output as
*derived + drift-checked*, never hand-written.

## 2. The runtimes & how each receives ponytail

| Runtime | Channel | Carrier file(s) | Install command (upstream) |
|---|---|---|---|
| Claude Code | plugin + hooks | `.claude-plugin/*`, `hooks/*` | `/plugin install ponytail@ponytail` |
| Codex | plugin + hooks | `.codex-plugin/plugin.json`, `hooks/*` | `codex plugin marketplace add …` |
| Copilot CLI | plugin + hooks | `hooks/copilot-hooks.json` | `copilot plugin install …` |
| pi | extension | `pi-extension/*` | `pi install git:…` |
| OpenCode | plugin | `.opencode/plugins/ponytail.mjs` + `command/*` | `opencode.json` plugin path |
| Gemini / Antigravity | extension | `gemini-extension.json` | `gemini extensions install …` |
| OpenClaw | skill pkg | `.openclaw/skills/*` (generated) | `clawhub install ponytail` |
| **Cursor** | rules file | `.cursor/rules/ponytail.mdc` | copy the file |
| **Windsurf** | rules file | `.windsurf/rules/ponytail.md` | copy the file |
| **Cline** | rules file | `.clinerules/ponytail.md` | copy the file |
| **Kiro** | steering | `.kiro/steering/ponytail.md` | copy to `~/.kiro/steering/` |
| **Copilot (editor)** | instructions | `.github/copilot-instructions.md` | copy the file |
| CodeWhale / any | `AGENTS.md` | `AGENTS.md` | zero-config, auto-read |

**Two tiers:** *plugin/hook/extension* hosts (dynamic, can mode-switch) vs
*instruction-file* hosts (static always-on rules, no switching). **Bold rows =
Spec 327 Wave 1** (instruction-file tier + Claude Code). The dynamic non-Claude
hosts (Codex/Gemini/pi/OpenCode/OpenClaw) are **Wave 2 → Spec 328**.

## 3. Degradation & preconditions (ponytail's lessons → Spec 327)

- **Hooks need `node` on PATH** — every hook command is `command -v node … || exit 0`,
  so a missing runtime is a silent no-op, not an error (README: *"the skills still
  work, the always-on activation just stays quiet"*). → Spec 327 states the **CLI
  precondition + a pipx bootstrap line** in each generated file.
- **Instruction-file hosts get no commands** — only the always-on ruleset. →
  agency's instruction-file adapters carry the **discipline + CLI entry pointers**
  (`agency search`/`help`/`<cap> <verb>`), *not* the full verb index (token bound).
- **Level via env/config** — `PONYTAIL_DEFAULT_MODE` / `config.json` (Spec 326's
  `discipline_level`), so the installer doesn't bake a level into the files.

## 4. Crosswalk → agency self-installer (Spec 327)

| Ponytail | Agency installer (Spec 327) |
|---|---|
| `AGENTS.md` canonical body | `install.surface_card(engine)` → **compact projection** |
| `skills/ponytail/SKILL.md` runtime source | `_discipline.py` (Spec 326) |
| `check-rule-copies.js` (copies == canonical + invariants) | `scripts/check-drift` assertion (adapter output == card) |
| `build-openclaw-skills.js` (generate from source) | adapter renderers (`card → {path: content}`) |
| `.cursor/.windsurf/.clinerules/.kiro/.github` copies | Wave-1 instruction-file adapters (same targets) |
| `.claude-plugin/*` + hooks | `claude` adapter = `surface_card` → `install.write()` + Spec 326 handlers |
| per-host install commands (`/plugin`, `npx`, `clawhub`, …) | one `agency install --agent <name>` (+ `--agent all`, `--global`) |
| *(ponytail has `uninit`)* | `agency uninstall --agent <name>` (remove the fenced block) |
| frozen full-file copies | **fenced `<!-- agency:auto -->` block merge** (additive; unfenced file → append) — agency installs into *consumer* projects, so it must not clobber |
| node-guarded silent skip | per-adapter independent success/report (partial install never half-writes) |

**Key divergence:** ponytail's copies are *whole-file* (it owns the file). Agency
installs into a user's existing project, so each adapter **merges a fenced block**
rather than overwriting — and carries **CLI access to the full verb surface**
(via `agency <cap> <verb>`, Spec 079), where ponytail carried only one discipline.

## 5. "Cover all functionality of agency" — how

- **MCP host (Claude):** `.mcp.json` exposes the full verb surface interactively
  (`search`/`get_schema`/`execute`) — already shipped.
- **Instruction-file host:** the rules file points at the **CLI mirror** —
  `agency search "<task>"` to discover, `agency <cap> <verb>` to run any verb
  (Spec 079 mirrors every verb), `agency_welcome` for onboarding — so the full
  surface is reachable from a shell with zero per-verb bloat in the rules file.

## 6. License / provenance
MIT. Provenance `intent:7509dac0`; design `reflection:fe553a2e`; panel-fold
`reflection:197d8531`.
