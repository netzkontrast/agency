---
spec_id: "327"
slug: multi-agent-installer
status: draft
last_updated: 2026-06-19
owner: "@agency"
vision_goals: [3, 4, 8]
depends_on: ["062", "065", "079", "280", "326", "328"]
domain: install
wave: core-discipline
---

# Spec 327 — Multi-agent self-installer (agency installs itself across agents)

> Build a Python **multi-agent self-installer** folded into `agency install` + the
> MCP server, so **agency can install *itself* across many agent runtimes** —
> exposing agency's **full functionality** on each (via MCP, or the Spec 079
> `agency <cap> <verb>` CLI), plus the Spec 326 **frugal** discipline. **Goal 3**
> (agent-uniform — *no special-casing per agent*) and **Goal 8** (compose with the
> ecosystem).
>
> **Wave 1 (this spec):** Claude Code (MCP, existing) + the **instruction-file
> agents** — Cursor, Windsurf, Cline, Kiro, GitHub Copilot — via native rules /
> `AGENTS.md`. Other MCP runtimes (Codex, Gemini, pi, opencode) → **Wave 2**
> (Spec 329, deferred). **Panel-hardened** (2026-06-19): compact rules projection,
> CLI precondition + bootstrap, uninstall/update, partial-install reporting,
> per-agent validity, Gherkin. Design notes:
> [`reference/INSTALLER.md`](reference/INSTALLER.md). Provenance `intent:7509dac0`.

## Why (evidence + doctrine)

The reach pattern is well understood: **one source of truth, generated into every
agent's native format** (`.cursor/rules/`, `.windsurf/rules/`, `.clinerules/`,
`.kiro/steering/`, `AGENTS.md`, `.github/copilot-instructions.md`, plus MCP/
extension configs), kept in lockstep by a drift gate. Agency already has the two
halves this needs:

- a **generator** — `install.write()` emits the plugin surface from the live
  registry (Spec 029/031/065);
- a **CLI that mirrors every verb** — `agency <cap> <verb>` (Spec 079), so an
  agent with no MCP still reaches agency's *full* functionality from a shell.

What is missing is the **adapter layer**: turn agency's live surface + the Spec
326 frugal discipline into each agent's native instruction file. That is this
spec — generalized from "a discipline" to "all of agency."

## Design

### One canonical `surface_card` → many adapters (projections)

`install.surface_card(engine)` derives, from the live registry: the full
capability/verb list, the access recipe (MCP config *or* the `agency <cap>
<verb>` CLI), the `agency_welcome` pointer, and the Spec 326 frugal discipline
(imported from `_frugal.py`, never re-authored). The card holds the **full**
surface; each adapter **projects** the slice that fits its host — single source of
truth, drift-gated.

**Compact projection for instruction files.** Rules files must **NOT** inline the
full ~200-verb index — that bloats every session in that host and fights Goal 1
(and hits host size limits). Instead they carry: the **frugal discipline**, and
**entry pointers** — `agency search "<task>"`, `agency help`, `agency <cap>
<verb>`, `agency_welcome`. The agent discovers verbs on demand via the CLI, exactly
as an MCP client does via `search`. (The full card still backs the MCP/Claude
adapter, where discovery is interactive.)

### CLI precondition + bootstrap

Instruction-file adapters tell the agent to "reach agency via `agency <cap>
<verb>`," which **presupposes agency is installed and on PATH**. Each generated
file therefore **opens with a bootstrap line** — *"If `agency` is not found:
`pipx install agency` (or see <repo>)"* — mirroring the SessionStart pipx
auto-install (Spec 062). The precondition is stated, not assumed.

### The adapters (Wave 1)

`agency/install/adapters/` — one pure `card → {path: content}` renderer per
target. **Claude is routed through the card too**: the `claude` adapter calls
`surface_card` then delegates to `install.write()` for the MCP plugin surface —
symmetry preserved, card stays the single source.

| Agent | Channel | Writes | Validity criterion |
|---|---|---|---|
| **Claude Code** | MCP (full surface) | `install.write()` output + Spec 326 handlers | existing install tests |
| **Cursor** | rules | `.cursor/rules/agency.mdc` | parses as `.mdc` with required frontmatter keys |
| **Windsurf** | rules | `.windsurf/rules/agency.md` | non-empty rules block |
| **Cline** | rules | `.clinerules/agency.md` | non-empty rules block |
| **Kiro** | steering | `.kiro/steering/agency.md` | non-empty steering doc |
| **Copilot** | rules | `.github/copilot-instructions.md` **and** `AGENTS.md` | both present (Q2: both) |
| **(universal)** | rules | `AGENTS.md` | the zero-config fallback any AGENTS-reader picks up |

### Idempotency, partial-install & uninstall

- **Merge, never clobber:** each file gets a fenced `<!-- agency:auto:start -->`
  … `<!-- agency:auto:end -->` block. Existing file **with** the fence → replace
  the block; **without** the fence → **append a fresh block**, leaving the user's
  content intact (Spec 292 anchor pattern).
- **Per-adapter independent report:** each adapter succeeds/fails independently and
  is reported; one failure never half-writes another. Re-running is the recovery
  (idempotent), so no rollback machinery.
- **Uninstall / update:** `agency uninstall --agent <name>` removes the fenced
  block; update = re-merge (replace the block).

### Invocation surface

`agency install --agent <name>` (repeatable / `--agent all`); default (no
`--agent`) keeps today's Claude-Code behaviour. MCP `agency_install(agent=…)`.
Target dir = the **consumer project** (`$CLAUDE_PROJECT_DIR`/cwd); `--global` opts
into the agent's user config dir (Q1).

## Slices (TDD)

1. **Surface card + framework + bootstrap.** `surface_card(engine)`, the adapter
   registry, the `--agent` CLI flag / MCP param, the bootstrap-line helper.
2. **Claude adapter (via card).** Wrap `install.write()` behind the card.
3. **Instruction-file adapters.** Cursor/Windsurf/Cline/Kiro/Copilot — compact
   projection, fenced-block merge.
4. **AGENTS.md generation.** The universal fallback (discipline + entry pointers).
5. **Uninstall + drift guard + doctor.** `agency uninstall --agent`;
   `scripts/check-drift` asserts derived == card; `agency_doctor` lists installed
   agents + the frugal level (Spec 326).

## Acceptance criteria

- **C1** — `agency install --agent <name>` writes a valid (per the table's
  criterion), idempotent native surface carrying agency's **full** verb *access*
  (MCP, or the CLI entry pointers) + the Spec 326 frugal discipline.
- **C2** — Instruction files carry **entry pointers, not the full verb index**
  (token-bounded); the full surface stays in the card.
- **C3** — Single source of truth: every adapter renders from `surface_card`;
  drift-gated.
- **C4** — Additive: existing user files are merged via the fenced block, never
  clobbered; unfenced files get a fresh appended block.
- **C5** — Each file states the CLI precondition + bootstrap; default `--agent`
  behaviour (Claude) is unchanged.
- **C6** — `agency uninstall --agent <name>` cleanly removes the block;
  per-adapter failures are reported independently.
- **C7** — Wave-2 runtimes named as out-of-scope follow-ups (Spec 329).

## Acceptance scenarios (Gherkin sketch)

```gherkin
Scenario: install into a clean Cursor project
  When I run "agency install --agent cursor" in a project dir
  Then .cursor/rules/agency.mdc exists with valid frontmatter
  And it contains the frugal discipline and the "agency <cap> <verb>" entry pointer
  And it does NOT inline the full verb index
  And it opens with the pipx bootstrap line

Scenario: re-install is idempotent
  Given .cursor/rules/agency.mdc already has the agency fenced block
  When I run "agency install --agent cursor" again
  Then the agency block is replaced, not duplicated
  And any non-agency content in the file is unchanged

Scenario: merge into an existing unfenced file
  Given .github/copilot-instructions.md exists with user content and no fence
  When I run "agency install --agent copilot"
  Then a fresh agency fenced block is appended
  And the original user content is preserved

Scenario: uninstall removes only the agency block
  Given an agency block is present
  When I run "agency uninstall --agent cursor"
  Then the fenced block is gone and user content remains

Scenario: partial install reports per-adapter
  Given one adapter target dir is read-only
  When I run "agency install --agent all"
  Then the writable adapters succeed and are reported
  And the failing one is reported without aborting the others
```

## Open questions

- **Q4** — Should `AGENTS.md` generation MERGE into agency's own repo `AGENTS.md`
  (doctrine, file-authoritative) or only the *consumer project's*? *Rec:
  consumer-project only; never rewrite the repo's canon AGENTS.md.*

*(Q1 project-dir default, Q2 Copilot both-forms, Q3 Wave-2-as-Spec-329 — decided.)*

## Followup — Implementation Status (2026-06-19)

**Verdict: Not started** (design drafted + panel-hardened; reframed native; awaiting gate approval; pairs with Spec 326 + 328).

- **Done:** Wave-1 scope set; surface-card + adapter design grounded on
  `install.write` + the Spec 079 CLI mirror + the Spec 326 frugal discipline;
  panel findings folded; third-party framing/source removed per directive.
- **Still:** gate approval, then Slice 1 (after Spec 326/328 Slice 1).
- **Blocker / Next step:** confirm Q4; Spec 328 (`_config.py`) + Spec 326
  (`_frugal.py`) Slice 1 land first so the card imports the canonical discipline.
