---
spec_id: "326"
slug: ponytail-port
status: draft
last_updated: 2026-06-19
owner: "@agency"
vision_goals: [1, 3, 4]
depends_on: ["076", "114", "280", "292", "295"]
domain: lifecycle
wave: domain-capability
---

# Spec 326 — Ponytail port: a native minimal-code discipline, present at every session

> Port the third-party **ponytail** plugin (DietrichGebert/ponytail, MIT) into
> agency as a **native capability** whose *minimal-code discipline* is **present
> and known at every agent session start** — Claude Code (MCP) **and** CLI-only
> (no-MCP) harnesses alike — embedded into `agency install`, project init, and
> SessionStart. Ponytail's whole reason for being (write only what the task
> needs; never cut validation/security/accessibility) is **GOALS.md Goal 1**
> (token-efficient agentic loops) expressed as a coding discipline; its
> cross-agent "always-on" presence is **Goal 3** (agent-uniform lifecycle); its
> shape — *add a folder under `agency/capabilities/`* — is **Goal 4** (open set).
>
> **Brainstorm hard-gate:** this spec IS the design artefact. Per the
> `brainstorm` discipline (`explore → present → confirm`), implementation does
> **not** begin until the human confirms this design. Provenance:
> `intent:7509dac0`; vendored source-of-truth under
> [`reference/`](reference/); exhaustive file Index in
> [`reference/INDEX.md`](reference/INDEX.md).

## Why (evidence + doctrine)

Agency has eight goals but no *coding* discipline that holds on every session —
nothing that stops an agent over-building a 404-line date-picker when
`<input type="date">` is the answer. Ponytail is exactly that discipline, and it
is **measured**, not asserted: on a headless Claude Code agent editing a real
FastAPI + React repo (12 tickets, Haiku 4.5, n=4) it cut **−54% LOC, −22%
tokens, −20% cost, −27% time while staying 100% safe** — the only arm that cut
every metric without dropping a safety guard
([`reference/benchmarks/results/2026-06-18-agentic.md`](reference/benchmarks/results/2026-06-18-agentic.md)).
Token-efficiency is GOALS.md Goal 1; ponytail delivers it at the *code-output*
layer, complementing code-mode's delivery at the *tool-call* layer.

The doctrinal fit is unusually clean:

| Ponytail trait | Agency goal it realizes |
|---|---|
| "Write only what the task needs" → less code/tokens/cost | **Goal 1** — token-efficient agentic loops |
| Present on every agent, same rule, no per-agent special-casing | **Goal 3** — agent-uniform lifecycle |
| Ships as a self-contained unit you install | **Goal 4** — open set; *adding = adding a folder* |
| Degrades gracefully where no hook system exists (rules files) | **Goal 3** + the MCP/CLI dual-surface contract |
| Single source of truth for the rule text (`check-rule-copies.js`) | The repo's **derivability** doctrine (CLAUDE.md) |

## What ponytail IS (the thing being ported)

The substance is small and portable as **data** (markdown, MIT-licensed):

1. **The ladder** — before writing code, stop at the first rung that holds:
   `1. Does this need to exist? (YAGNI) → 2. stdlib → 3. native platform feature
   → 4. installed dependency → 5. one line → 6. the minimum that works.`
2. **The safety floor** (non-negotiable) — *lazy, not negligent*: trust-boundary
   validation, data-loss handling, security, and accessibility are **never** on
   the chopping block. This clause is what keeps ponytail 100% safe; it must port
   as a **first-class gate**, not prose.
3. **Six skills** — `ponytail` (the always-on rule), `ponytail-review` (review a
   diff for over-engineering → delete-list), `ponytail-audit` (whole-repo
   sweep), `ponytail-debt` (harvest deferred `ponytail:` shortcuts into a
   ledger), `ponytail-gain` (the measured-impact scoreboard), `ponytail-help`.
4. **Intensity modes** — `lite / full / ultra / off` (default `full`), set per
   session via `PONYTAIL_DEFAULT_MODE` or `~/.config/ponytail/config.json`.
5. **Cross-agent presence MECHANISM** — Node lifecycle hooks inject the ruleset
   every session/prompt for hook-capable hosts (Claude/Codex/Copilot); for the
   rest it degrades to an **always-on rules file** (`AGENTS.md` / `.cursor/` /
   `.windsurf/` / `.kiro/` …). This is the part that must be **re-implemented on
   agency's substrate**, not copied.

## Design

### Port model (decision: **C — native capability + always-on injection, mode-aware**)

Three options were weighed against the must-haves *session-start presence
(MCP+CLI)* and *safety-floor preserved* (trade-off matrix on `intent:7509dac0`):
**A** (capability only) fails "present every session"; **B** (injection only)
loses the review/audit/debt verbs and emit/walkability; **C** wins. We ship
both a discoverable capability **and** always-on injection.

### 1 — The capability (`agency/capabilities/ponytail/`)

Folder-per-capability (mirrors `mode/`): `__init__.py` + `_main.py`, auto-discovered
by reflection (Goal 4 — *no central registry edit*). Verbs:

| Verb | Role | Does |
|---|---|---|
| `review` | act (read-only) | Score the current diff for over-engineering; emit findings as graph `Analysis`/`AntiPattern` artefacts + a delete-list. |
| `audit` | act (read-only) | Same, whole-repo not just the diff. |
| `debt` | act | Harvest deferred `ponytail:` shortcuts into a `PonytailDebt` ledger so "later" ≠ "never". |
| `gain` | act | Render the measured-impact scoreboard (the benchmark numbers, ported as data). |
| `level` | effect | Get/set the active intensity (`lite/full/ultra/off`); records a `PonytailLevel` provenance node. |
| `help` | act | Quick reference (derived). |

**SkillDoc derives from the module docstring** (`Use when:` / `Triggers:` /
`Red flags:`) per the derivability audit — no authored skill literal.

**Ontology extension** (`OntologyExtension`): `nodes={PonytailLevel:[level],
PonytailDebt:[note, location]}`, `enums={(PonytailLevel, level):
{lite,full,ultra,off}}`, `skills={ponytail-review, ponytail-audit, …}` as
walkable Lifecycle templates. Edges are *declared ⇒ traversed* (dormant-surface
audit).

### 2 — Always-on presence (THE critical path)

The seam already exists and is dual-surface by construction
(`engine.register_hook_handler(event, fn)` → `dispatch_hook` → a handler
returning `{"inject": <text>}`, which `cli.py hook` prints to stdout for Claude
Code to fold into the prompt — `engine.py:631-646`, `cli.py:269-283`; the same
path as the "AVOID ASSUMPTIONS" UserPromptSubmit guard).

- **MCP (Claude Code) + any hook-running harness:** register a `SessionStart`
  (and optionally `UserPromptSubmit`) handler that injects the ladder + safety
  floor **at the active level**. Reached via `hooks/dispatch → agency.cli hook →
  hook_event → dispatch_hook`. Works for *any* agent whose harness runs the
  agency hook script — that is the CLI lane too.
- **Pure no-MCP / no-hook CLI (e.g. Jules):** two carriers — (a) the
  `agency_welcome` onboarding payload (`_substrate_tools.py:535`) gains a
  `coding_discipline` field (ladder + active level), so every agent that opens
  with `agency_welcome` sees it; (b) `agency install` writes/updates the
  project's **`AGENTS.md`** with the always-on ponytail rule — exactly how
  ponytail itself degrades for instruction-only agents.

**Drop-in-bar design point (Open Q1):** today hook handlers register
imperatively. To keep the *add-a-folder-and-nothing-else* invariant, a
capability should be able to **declare** its hook handlers (e.g.
`hook_handlers = {"SessionStart": fn}` on the capability class) and the engine
auto-registers them on `discover()`, mirroring how `OntologyExtension` auto-merges.
This small substrate extension is in-scope and is what makes ponytail a true
drop-in rather than an engine edit.

### 3 — Intensity is a SEPARATE axis from agency's `mode`

Grounding caught this: the `mode` capability's enum is agency's **five
behavioral postures** (brainstorming, …) — a different axis from ponytail's
*code-minimalism intensity*. Ponytail therefore **owns** `lite/full/ultra/off`
as a `PonytailLevel` node + `PONYTAIL_DEFAULT_MODE` env + an `.agency` config
default (`full`). Do **not** widen the `mode` enum. The injected text scales with
the level (`off` injects nothing; `ultra` is the strict rung-ladder).

### 4 — Setup / init / session-start embedding (zero manual steps)

Per Goal 9 criterion 5 (*`agency install` + SessionStart yield a working
substrate with zero manual steps*): `install.write()` already emits the
SessionStart hook + `using-agency` skill + `.mcp.json` (and now preserves
external MCP servers — PR #170). This spec adds: the ponytail injection wiring is
live the moment the capability folder exists (handler auto-registered), the
`AGENTS.md` rule is written on install, and `agency_doctor` reports ponytail
presence + active level so a fresh setup is verifiably green.

### 5 — Single source of truth + drift guard

One canonical ruleset lives in the capability (the ladder + safety floor as a
module constant); the SkillDoc, the injected text, the `AGENTS.md` block, and
the `gain` scoreboard all **derive** from it — no second copy to drift (the rule
that `check-rule-copies.js` enforces upstream). Add an `# AGENCY-DRIFT:
ponytail-rule` tag at each read site and a `scripts/check-drift` assertion that
the derived copies match the source.

### What is NOT ported

The 14-agent JS packaging (`.cursor/`, `.windsurf/`, `.kiro/`, `.openclaw/`,
`pi-extension/`, `gemini-extension.json`, Copilot hooks, `scripts/*.js`) is
**out of scope** — agency targets exactly two surfaces (MCP + its CLI). We reuse
ponytail's *AGENTS.md degradation concept*, not its Node implementation. The
promptfoo/benchmark harness is vendored as evidence, not ported.

## Slices (TDD — Gherkin acceptance is the contract; behaviour, not internals)

1. **Capability skeleton.** `agency/capabilities/ponytail/` with the canonical
   ladder+safety-floor constant, the `level` verb, and a derived SkillDoc.
   *Acceptance:* `search("ponytail")` finds the capability; `level` round-trips
   and records a `PonytailLevel`; the safety-floor clause is present in the rule.
2. **Always-on injection (critical path).** SessionStart/UserPromptSubmit handler
   + `agency_welcome.coding_discipline`. *Acceptance:* a `SessionStart`
   `hook_event` returns an `inject` containing the ladder at the active level
   (and empty when `off`); `agency_welcome` payload carries the discipline —
   proving presence on **both** the MCP-hook and CLI lanes.
3. **The review/audit/debt/gain/help verbs.** *Acceptance:* `review` on a diff
   with an over-built block emits findings + a delete-list as graph artefacts;
   `debt` ledgers a deferred shortcut; `gain` renders the scoreboard.
4. **Setup/init embedding + drift guard.** install writes the `AGENTS.md` rule;
   `agency_doctor` reports ponytail presence + level; `scripts/check-drift`
   asserts the derived copies match the source. *Acceptance:* a fresh
   `install` → doctor-green with ponytail active; drift check exits 0.
5. **Intensity defaults.** `PONYTAIL_DEFAULT_MODE` + `.agency` config default
   (`full`). *Acceptance:* the env/config sets the level a new session injects at.

## Acceptance criteria (the contract)

- C1 — After `agency install` + SessionStart, the ponytail discipline is present
  in a new Claude Code session (MCP) **and** surfaced via `agency_welcome` for a
  CLI/no-MCP agent — zero manual steps.
- C2 — The safety floor is a first-class, tested gate: the injected/ported rule
  never omits validation/security/accessibility (a test asserts it).
- C3 — Ponytail is a true drop-in: the capability folder + a declared hook
  handler is the *only* change to make it live (no engine special-casing).
- C4 — Single source of truth: every derived copy matches the canonical rule
  (`check-drift` gates it).
- C5 — `TODO.md` row added; this spec's frontmatter carries `vision_goals`.

## Open questions

- **Q1** — Capability-declared hook handlers (the drop-in mechanism): confirm the
  `hook_handlers` class attr + auto-register on `discover()` as the substrate
  extension (vs. a one-line engine registration). *Recommend the declarative
  form* — it preserves Goal 4.
- **Q2** — Inject on `SessionStart` only, or also `UserPromptSubmit` (stronger
  presence, more tokens/prompt)? *Recommend SessionStart by default, with the
  level controlling whether UserPromptSubmit also fires (`ultra`).*
- **Q3** — Should `review`/`audit` reuse the existing `analyze` capability's
  finding artefacts (`Analysis`/`AntiPattern`) rather than minting ponytail-only
  nodes? *Recommend reuse* (cluster coherence, Spec 047).

## Followup — Implementation Status (2026-06-19)

**Verdict: Not started** (spec drafted; awaiting brainstorm hard-gate approval).

- **Done:** agency-thinking dissection (assumptions / decompose / premortem /
  trade-off matrix on `intent:7509dac0`); vendored source-of-truth under
  `reference/`; mechanism grounded against the live code (`register_hook_handler`
  / `dispatch_hook` / `agency_welcome` / `mode` / `install.write`); this spec.
- **Still:** human confirmation of the design (the gate), then Slice 1.
- **Blocker / Next step:** approve or adjust the port model (Q1–Q3), then begin
  Slice 1 under TDD.
