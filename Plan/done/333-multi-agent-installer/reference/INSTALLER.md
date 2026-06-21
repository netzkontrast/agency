<!-- agency-note: design reference for Spec 333; intent:7509dac0 -->
# Multi-agent self-installer — agency's adapter design (design reference)

> Agency's own design for installing **itself** across agent runtimes (Spec 333),
> exposing its full surface + the Spec 332 frugal discipline in each agent's native
> format. Companion discipline design:
> [`../../332-frugal-core-discipline/reference/DISCIPLINE.md`](../../332-frugal-core-discipline/reference/DISCIPLINE.md).

## 1. The pattern: one source → many native formats, drift-gated

Never hand-maintain N copies. Keep **one source** and **generate / verify**
everything else. Agency's source is the live registry; the deriving pieces:

- **`install.surface_card(engine)`** — the canonical descriptor: the live
  capability/verb list, the access recipe (MCP config *or* `agency <cap> <verb>`
  CLI), the `agency_welcome` pointer, and the Spec 332 frugal discipline (imported
  from `_frugal.py`).
- **Adapters** — pure `card → {path: content}` renderers, one per target.
- **Drift gate** — `scripts/check-drift` asserts every adapter output still derives
  from the card (the copies are the liability; the source + generator + gate are
  the asset).

## 2. The adapters (Wave 1)

| Runtime | Channel | Carrier file | Validity |
|---|---|---|---|
| **Claude Code** | MCP (full surface) | `.mcp.json` + plugin (via `install.write()`) + Spec 332 handlers | existing install tests |
| **Cursor** | rules | `.cursor/rules/agency.mdc` | `.mdc` frontmatter keys present |
| **Windsurf** | rules | `.windsurf/rules/agency.md` | non-empty rules block |
| **Cline** | rules | `.clinerules/agency.md` | non-empty rules block |
| **Kiro** | steering | `.kiro/steering/agency.md` | non-empty steering doc |
| **Copilot** | rules | `.github/copilot-instructions.md` + `AGENTS.md` | both present |
| **(universal)** | `AGENTS.md` | `AGENTS.md` | zero-config fallback any AGENTS-reader loads |

Wave 2 (deferred → **Spec 335**): the other MCP runtimes — Codex, Gemini, pi,
opencode.

## 3. "Cover all functionality of agency" — by channel

- **MCP host (Claude):** `.mcp.json` exposes the full verb surface interactively
  (`search`/`get_schema`/`execute`) — already shipped.
- **Instruction-file host:** the rules file carries the **frugal discipline +
  entry pointers** — `agency search "<task>"` to discover, `agency <cap> <verb>`
  to run any verb (Spec 079 mirrors every verb), `agency_welcome` for onboarding.
  The full surface is reachable from a shell with **zero per-verb bloat** in the
  rules file (the ~200-verb index stays in the card, never inlined — Goal 1).

## 4. Preconditions & degradation

- **CLI must be installed / on PATH** — every instruction file **opens with a
  bootstrap line**: *"If `agency` is not found: `pipx install agency`"* (mirrors the
  SessionStart pipx auto-install, Spec 062). Stated, not assumed.
- **Level via config** — the frugal level comes from Spec 334's
  `.agency/config.yaml` / `AGENCY_FRUGAL_LEVEL`, so the installer bakes no level
  into the files.

## 5. Idempotency, partial install & uninstall

- **Merge, never clobber:** a fenced `<!-- agency:auto:start -->` … `:end -->`
  block. Existing file **with** the fence → replace the block; **without** → append
  a fresh block (Spec 292 anchor pattern). Agency installs into the *user's* project
  — it must not overwrite their content.
- **Per-adapter independent report:** each adapter succeeds/fails on its own; one
  failure never half-writes another. Re-running is the recovery (idempotent).
- **Uninstall / update:** `agency uninstall --agent <name>` removes the fenced
  block; update = re-merge.

## 6. Invocation

`agency install --agent <name>` (repeatable / `--agent all`, `--global`);
default (no `--agent`) = today's Claude-Code behaviour. MCP `agency_install(agent=…)`.
Target = the consumer project dir by default.

## 7. Prior art

Multi-runtime agent installers exist in the ecosystem; this is an **independent
design** reusing agency's existing halves (`install.write` generator + the Spec 079
CLI verb-mirror) — the novelty is exposing agency's *full* surface per agent, not a
single discipline, and merging into the user's project rather than owning the file.
