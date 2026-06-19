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

> Port ponytail's Node multi-runtime installer to **Python** and fold it into
> `agency install` + the MCP server, so **agency can install *itself* across many
> agent runtimes** — exposing agency's **full functionality** on each (via MCP, or
> the Spec 079 `agency <cap> <verb>` CLI), not just the discipline. **Goal 3**
> (agent-uniform — *no special-casing per agent*) and **Goal 8** (compose with
> the ecosystem).
>
> **Wave 1 (this spec):** Claude Code (MCP, existing) + the **instruction-file
> agents** — Cursor, Windsurf, Cline, Kiro, GitHub Copilot — via native rules /
> `AGENTS.md`. Other MCP runtimes (Codex, Gemini, pi, opencode, openclaw) →
> **Wave 2** (Spec 329, deferred). Split from Spec 326; **panel-hardened**
> (2026-06-19 `/sc:spec-panel`): compact rules projection, CLI precondition +
> bootstrap, uninstall/update, partial-install reporting, per-agent validity,
> Gherkin. Provenance `intent:7509dac0`, `reflection:fe553a2e`; porting source
> under [`../326-ponytail-port/reference/`](../326-ponytail-port/reference/).

## Why (evidence + doctrine)

Ponytail's reach proves the pattern: **one source of truth, generated into every
agent's native format**, kept in lockstep by `check-rule-copies.js`. Agency has
the two halves already: a **generator** (`install.write()` emits the surface from
the live registry) and a **CLI that mirrors every verb** (`agency <cap> <verb>`,
Spec 079) so a no-MCP agent still reaches agency's full functionality from a
shell. What is missing is the **adapter layer** — turning agency's live surface +
the Spec 326 discipline into each agent's native instruction file.

## Design

### One canonical `surface_card` → many adapters (projections)

`install.surface_card(engine)` derives, from the live registry: the full
capability/verb list, the access recipe (MCP config *or* the `agency <cap>
<verb>` CLI), the `agency_welcome` pointer, and the Spec 326 discipline (imported
from `_discipline.py`, never re-authored). The card holds the **full** surface;
each adapter **projects** the slice that fits its host — single source of truth,
drift-gated.

**Compact projection for instruction files (panel ❌ Wiegers/Newman).** Rules
files must **NOT** inline the full ~200-verb index — that bloats every session in
that host and fights Goal 1 (and hits host size limits). Instead they carry: the
**discipline**, and **entry pointers** — `agency search "<task>"`, `agency help`,
`agency <cap> <verb>`, `agency_welcome`. The agent discovers verbs on demand via
the CLI, exactly as an MCP client does via `search`. (The full card still backs
the MCP/Claude adapter, where discovery is interactive.)

### CLI precondition + bootstrap (panel ❌ Hohpe)

Instruction-file adapters tell the agent to "reach agency via `agency <cap>
<verb>`," which **presupposes agency is installed and on PATH**. Each generated
file therefore **opens with a bootstrap line** — *"If `agency` is not found:
`pipx install agency` (or see <repo>)"* — mirroring the SessionStart pipx
auto-install (Spec 062). The precondition is stated, not assumed.

### The adapters (Wave 1)

`agency/install/adapters/` — one pure `card → {path: content}` renderer per
target. **Claude is routed through the card too** (panel ⚠️ Fowler): the `claude`
adapter calls `surface_card` then delegates to `install.write()` for the MCP
plugin surface — symmetry preserved, card stays the single source.

| Agent | Channel | Writes | Validity criterion (Wiegers) |
|---|---|---|---|
| **Claude Code** | MCP (full surface) | `install.write()` output + Spec 326 handlers | existing install tests |
| **Cursor** | rules | `.cursor/rules/agency.mdc` | parses as `.mdc` with required frontmatter keys |
| **Windsurf** | rules | `.windsurf/rules/agency.md` | non-empty rules block |
| **Cline** | rules | `.clinerules/agency.md` | non-empty rules block |
| **Kiro** | steering | `.kiro/steering/agency.md` | non-empty steering doc |
| **Copilot** | rules | `.github/copilot-instructions.md` **and** `AGENTS.md` | both present (Q2 decided: both) |
| **(universal)** | rules | `AGENTS.md` | the zero-config fallback any AGENTS-reader picks up |

### Idempotency, partial-install & uninstall (panel ⚠️ Nygard/Hightower)

- **Merge, never clobber:** each file gets a fenced `<!-- agency:auto:start -->`
  … `<!-- agency:auto:end -->` block. Existing file **with** the fence → replace
  the block; **without** the fence → **append a fresh block**, leaving the user's
  content intact (Spec 292 anchor pattern).
- **Per-adapter independent report (no global transaction):** each adapter
  succeeds/fails independently and is reported; one failure never half-writes
  another. Re-running is the recovery (idempotent), so no rollback machinery.
- **Uninstall / update:** `agency uninstall --agent <name>` removes the fenced
  block; update = re-merge (replace the block). Mirrors ponytail's `uninit`.

### Invocation surface

`agency install --agent <name>` (repeatable / `--agent all`); default (no
`--agent`) keeps today's Claude-Code behaviour. MCP `agency_install(agent=…)`.
Target dir = the **consumer project** (`$CLAUDE_PROJECT_DIR`/cwd); `--global`
opts into the agent's user config dir (Q1 decided).

### Ported from ponytail's Node (→ Python)

per-agent file **shapes** (vendored) → adapter renderers · `check-rule-copies.js`
→ a `scripts/check-drift` assertion (derived == card) · `build-openclaw-skills.js`
→ the `surface_card` derive step · `uninit` → `agency uninstall --agent`.

## Slices (TDD)

1. **Surface card + framework + bootstrap.** `surface_card(engine)`, the adapter
   registry, the `--agent` CLI flag / MCP param, and the bootstrap-line helper.
2. **Claude adapter (via card).** Wrap `install.write()` behind the card.
3. **Instruction-file adapters.** Cursor/Windsurf/Cline/Kiro/Copilot — compact
   projection, fenced-block merge.
4. **AGENTS.md generation.** The universal fallback (discipline + entry pointers).
5. **Uninstall + drift guard + doctor.** `agency uninstall --agent`;
   `scripts/check-drift` asserts derived == card; `agency_doctor` lists installed
   agents + discipline level (Spec 326).

## Acceptance criteria

- **C1** — `agency install --agent <name>` writes a valid (per the table's
  criterion), idempotent native surface carrying agency's **full** verb *access*
  (MCP, or the CLI entry pointers) + the Spec 326 discipline.
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
  And it contains the discipline and the "agency <cap> <verb>" entry pointer
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

## Open questions (remaining)

- **Q4** — Should `AGENTS.md` generation MERGE into agency's own repo `AGENTS.md`
  (doctrine, file-authoritative) or only write the *consumer project's*? *Rec:
  consumer-project only; never rewrite the repo's canon AGENTS.md.*

*(Q1 project-dir default, Q2 Copilot both-forms, Q3 Wave-2-as-Spec-329 — decided
above.)*

## Followup — Implementation Status (2026-06-19)

**Verdict: Not started** (design drafted + panel-hardened; awaiting gate approval; pairs with Spec 326).

- **Done:** Wave-1 scope set per directive; surface-card + adapter design grounded
  on `install.write` + the Spec 079 CLI mirror + the Spec 326 discipline;
  `/sc:spec-panel` folded — compact rules projection, CLI precondition/bootstrap,
  fenced-merge + partial-install reporting, uninstall/update, per-agent validity,
  Gherkin.
- **Still:** gate approval, then Slice 1 (after Spec 326 Slice 1 lands
  `_discipline.py`).
- **Blocker / Next step:** confirm Q4; Spec 326 Slice 1 first so the card imports
  the canonical discipline.
