---
spec_id: "327"
slug: multi-agent-installer
status: draft
last_updated: 2026-06-19
owner: "@agency"
vision_goals: [3, 4, 8]
depends_on: ["062", "065", "079", "280", "326"]
domain: install
wave: core-discipline
---

# Spec 327 — Multi-agent self-installer (agency installs itself across agents)

> Port ponytail's Node multi-runtime installer to **Python** and fold it into
> `agency install` + the MCP server, so **agency can install *itself* across many
> agent runtimes** — exposing agency's **full functionality** on each, not just
> the discipline. The way ponytail ships one skill to 14 agents, agency ships its
> *whole surface* (capability verbs + the Spec 326 discipline) to each agent in
> that agent's native instruction format. **Goal 3** (agent-uniform lifecycle —
> *no special-casing per agent*) and **Goal 8** (harness-in-harness — compose
> with the ecosystem, don't replace it).
>
> **Wave 1 scope (this spec):** Claude Code (MCP, already installed) + the
> **instruction-file agents** — Cursor, Windsurf, Cline, Kiro, GitHub Copilot —
> via native rules / `AGENTS.md`. The other MCP runtimes (Codex, Gemini, pi,
> opencode, openclaw) are **deferred to Wave 2** (a follow-up spec). Split out of
> Spec 326 per the 2026-06-19 directive; provenance `intent:7509dac0`,
> `reflection:fe553a2e`. Porting source vendored under
> [`../326-ponytail-port/reference/`](../326-ponytail-port/reference/).

## Why (evidence + doctrine)

Ponytail's reach is the proof of pattern: **one source of truth, generated into
every agent's native format** (`.cursor/rules/`, `.windsurf/rules/`,
`.clinerules/`, `.kiro/steering/`, `AGENTS.md`, `.github/copilot-instructions.md`,
plus MCP/extension configs), kept in lockstep by `check-rule-copies.js` +
`build-openclaw-skills.js`. Agency already has the two halves this needs:
- a **generator** — `install.write()` emits the plugin surface from the live
  registry (Spec 029/031/065);
- a **CLI that mirrors every verb** — `agency <cap> <verb>` (Spec 079), so an
  agent with no MCP can still reach agency's *full* functionality from a shell.

What is missing is the **adapter layer**: turn agency's live surface + the Spec
326 discipline into each agent's native instruction file. That is what porting
ponytail's installer buys us, generalized from "a discipline" to "all of agency."

## Design

### One canonical "agency surface card" → many adapters

A single derived descriptor (`install.surface_card(engine)`) — the live
capability/verb list, how to reach agency (MCP config *or* `agency <cap> <verb>`
CLI), the `agency_welcome` pointer, and the Spec 326 discipline (imported from
`_discipline.py`, never re-authored). **Every adapter renders from this card** —
single source of truth, so no per-agent copy can drift (the invariant
`check-rule-copies.js` enforces upstream; here a `scripts/check-drift` assertion).

### The adapters (Wave 1)

`agency/install/adapters/` — one small renderer per target, each a pure
`card → {path: content}`:

| Agent | Channel | Writes |
|---|---|---|
| **Claude Code** | MCP (full verb surface) | the existing `install.write()` output + the Spec 326 core handlers |
| **Cursor** | instruction-file | `.cursor/rules/agency.mdc` — discipline + "reach agency via `agency <cap> <verb>`" + the verb index |
| **Windsurf** | instruction-file | `.windsurf/rules/agency.md` |
| **Cline** | instruction-file | `.clinerules/agency.md` |
| **Kiro** | instruction-file | `.kiro/steering/agency.md` |
| **GitHub Copilot** | instruction-file | `.github/copilot-instructions.md` |
| **(universal)** | instruction-file | `AGENTS.md` — the zero-config fallback every AGENTS-reading agent picks up |

"**Cover all functionality**": MCP-capable hosts get the full verb surface over
`.mcp.json`; instruction-file hosts get the **agency CLI** (`agency <cap> <verb>`,
Spec 079 mirrors every verb) + the live verb index + the discipline + the
`agency_welcome` entry — so every adapter exposes the *whole* agency, through the
channel that agent supports.

### Invocation surface

- CLI: `agency install --agent <name>` (repeatable / `--agent all`); default (no
  `--agent`) keeps today's Claude-Code behaviour.
- MCP: `agency_install(agent=…)` substrate tool gains the `agent` selector.
- Idempotent + additive: never clobbers a user's existing rules file — merges a
  fenced `<!-- agency:auto -->` block (the Spec 292 anchor pattern), like
  `install` already does for `CLAUDE.md`.

### Ported from ponytail's Node (→ Python)

- per-agent file **shapes** (vendored) → adapter renderers;
- `check-rule-copies.js` → a `scripts/check-drift` assertion (derived == source);
- `build-openclaw-skills.js` → the `surface_card` derive step;
- the `PONYTAIL_DEFAULT_MODE` / config notion → Spec 326's `discipline_level`.

## Slices (TDD)

1. **Surface card + framework.** `install.surface_card(engine)` (live verbs +
   CLI access + discipline) and the adapter registry + `agency install --agent`
   CLI flag / MCP `agent` param. *Acceptance:* the card lists the full live verb
   set and embeds the discipline from `_discipline.py`.
2. **Claude Code adapter.** Wrap `install.write()` as the `claude` adapter (+ Spec
   326 handlers). *Acceptance:* `--agent claude` reproduces today's surface, no
   drift.
3. **Instruction-file adapters.** Cursor / Windsurf / Cline / Kiro / Copilot,
   each rendered from the card. *Acceptance:* `--agent cursor` writes a valid
   `.cursor/rules/agency.mdc` carrying the discipline + CLI access to all verbs;
   re-running is idempotent (fenced-block merge).
4. **AGENTS.md generation.** The universal fallback carrying agency's full
   surface + discipline. *Acceptance:* an AGENTS-reading agent has the verb index
   + discipline with zero other setup.
5. **Drift guard + doctor.** `scripts/check-drift` asserts every adapter output
   derives from the card; `agency_doctor` reports installed agents + the
   discipline level (with Spec 326). *Acceptance:* drift exits 0; doctor lists the
   targets.

## Acceptance criteria

- C1 — `agency install --agent <name>` produces a valid, idempotent native
  instruction surface for each Wave-1 agent, carrying agency's **full** verb
  access (MCP or CLI) + the Spec 326 discipline.
- C2 — Single source of truth: every adapter renders from `surface_card`; a
  drift check gates that no copy diverges.
- C3 — Additive: an existing user rules file is merged (fenced block), never
  clobbered.
- C4 — Default behaviour (no `--agent`) is unchanged (Claude Code).
- C5 — Wave-2 runtimes (Codex/Gemini/pi/opencode/openclaw) are named as
  out-of-scope follow-ups, not silently dropped.

## Open questions

- **Q1** — `agency install --agent` targets the **consumer project** dir
  (`$CLAUDE_PROJECT_DIR`/cwd) vs a global agent config dir (`~/.cursor/…`)?
  *Rec: project dir by default, `--global` opt-in* (mirrors ponytail + Spec 065).
- **Q2** — Does Copilot get the `.github/copilot-instructions.md` form, the
  `AGENTS.md` form, or both? *Rec: both* (ponytail ships both; Copilot reads
  either).
- **Q3** — Wave 2 (the deferred MCP runtimes) as slices here or a separate Spec
  328? *Rec: separate spec* once Wave 1 ships and the adapter contract is proven.

## Followup — Implementation Status (2026-06-19)

**Verdict: Not started** (design drafted; awaiting gate approval; pairs with Spec 326).

- **Done:** scope set to Wave 1 (Claude + instruction-file agents) per user
  directive; surface-card + adapter design grounded on `install.write` + the Spec
  079 CLI mirror + the Spec 326 discipline; this spec.
- **Still:** gate approval, then Slice 1.
- **Blocker / Next step:** confirm Q1–Q3; Spec 326 Slice 1 (`_discipline.py`)
  should land first so the card can import the canonical discipline.
