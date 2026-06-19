<!-- agency-note: knowledge reference authored 2026-06-19 for Spec 326/327; intent:7509dac0 -->
# Ponytail — analysis, Index, and core port-crosswalk

> My (Claude's) accumulated knowledge of the vendored **ponytail** source
> (DietrichGebert/ponytail, MIT, "works with 14 agents"), saved as reference for
> Specs **326** (core-embedded discipline) and **327** (multi-agent installer).
> Companion: [`../../327-multi-agent-installer/reference/PACKAGING.md`](../../327-multi-agent-installer/reference/PACKAGING.md).
> Raw source is this `reference/` tree; this doc is the map + the synthesis.

## 1. What ponytail IS

A single always-on **discipline** that makes a coding agent write the *laziest
solution that actually works* — "lazy means efficient, not careless." It is a
**ladder** (stop at the first rung that holds) plus a hard **safety floor** that
is never cut, delivered to ~14 agent runtimes by injecting the ruleset every
session. It is **content** (one canonical skill + 5 helper skills + intensity
levels) wrapped in a thin **mechanism** (Node lifecycle hooks + per-runtime
adapter files generated from one source). Default level **`full`**. MIT.

> The thesis (README): *"The rule was never 'fewest tokens.' It is: write only
> what the task needs, and never cut validation, error handling, security, or
> accessibility. The code ends up small because it is necessary, not golfed."*

## 2. The discipline — the port source for `_discipline.py`

Verbatim core (from [`skills/ponytail/SKILL.md`](skills/ponytail/SKILL.md) — the
runtime source of truth):

**The ladder** — stop at the first rung that holds:
1. **Does this need to exist at all?** Speculative need = skip it (YAGNI).
2. **Stdlib does it?** Use it.
3. **Native platform feature covers it?** (`<input type="date">` over a picker lib, CSS over JS, DB constraint over app code.)
4. **Already-installed dependency solves it?** Use it. Never add a new one for what a few lines do.
5. **Can it be one line?** One line.
6. **Only then:** the minimum code that works.

**Rules** — no unrequested abstractions (no interface w/ one impl, no factory for
one product); no boilerplate "for later"; deletion over addition; boring over
clever; fewest files, shortest diff; ship the lazy version AND question the
complex request in the same response (never stall); between two same-size stdlib
options pick the one correct on edge cases; mark deliberate simplifications with a
`ponytail:` comment that names the ceiling + upgrade path
(`# ponytail: global lock, per-account locks if throughput matters`).

**Output** — code first, then ≤3 short lines: what was skipped, when to add it.
Pattern: `[code] → skipped: [X], add when [Y].`

**The safety floor (★ never simplify away — port as a first-class gate, Spec 326
Slice 4):** input validation at trust boundaries · error handling that prevents
data loss · security · accessibility basics · the calibration real hardware
needs · anything explicitly requested. *"Lazy code without its check is
unfinished"* — non-trivial logic leaves ONE runnable check behind (assert-based
`demo()`/`__main__` or one small `test_*.py`; no frameworks). These exact
phrases are **drift invariants** pinned by `check-rule-copies.js` (§7).

**Levels** — `lite` (build it, name the lazier alt in one line) · **`full`** (the
ladder enforced, default) · `ultra` (YAGNI extremist, deletion before addition) ·
`off` (revert). Only the intensity-table row + the worked example are
mode-specific; everything else is constant across levels (see
[`hooks/ponytail-instructions.js`](hooks/ponytail-instructions.js) `filterSkillBodyForMode`).

## 3. Exhaustive per-file Index (the vendored `reference/` tree)

### Root
| File | Purpose |
|---|---|
| `README.md` / `README.es.md` | Main docs (EN/ES): discipline, install across 14 agents, benchmark numbers, commands. |
| `AGENTS.md` | **Canonical compact ruleset** — the single source every instruction-file copy is diffed against (`check-rule-copies.js`). The zero-config fallback any AGENTS-reader loads. |
| `LICENSE` | MIT. |
| `package.json` | npm metadata, scripts (`test`, the build/check scripts), packaged `files`. |
| `gemini-extension.json` | Gemini CLI / Antigravity extension manifest (always-on context + `/ponytail` commands). |
| `opencode.json` | OpenCode plugin pointer (`{ "plugin": ["./.opencode/plugins/ponytail.mjs"] }`). |

### `skills/` — canonical runtime skills (behavior source of truth)
| File | Purpose |
|---|---|
| `ponytail/SKILL.md` | **THE discipline** (§2): ladder, rules, output, intensity, safety floor. |
| `ponytail-review/SKILL.md` | Review the current diff for over-engineering → a delete-list, one line per finding. |
| `ponytail-audit/SKILL.md` | Audit the whole repo (not just the diff) for over-engineering → ranked delete/simplify list. |
| `ponytail-debt/SKILL.md` | Harvest every `ponytail:` shortcut comment into one debt ledger so deferrals are tracked. |
| `ponytail-gain/SKILL.md` | Show the measured-impact scoreboard (less code/cost, more speed) from the benchmark. |
| `ponytail-help/SKILL.md` | Quick reference for modes/skills/commands. |

### `hooks/` — the "present every session" mechanism (Node)
| File | Purpose |
|---|---|
| `claude-codex-hooks.json` | Wires **SessionStart** (`startup\|resume\|clear\|compact` → `ponytail-activate.js`) + **UserPromptSubmit** (→ `ponytail-mode-tracker.js`); both guarded by `command -v node` so they **degrade quietly** if node is absent. |
| `copilot-hooks.json` | Same wiring for GitHub Copilot CLI event names. |
| `ponytail-activate.js` | SessionStart handler — emits the discipline injection at the active level (startup banner). |
| `ponytail-mode-tracker.js` | UserPromptSubmit handler — detects `/ponytail <level>` switches + `stop ponytail`/`normal mode` deactivation, persists, re-injects. |
| `ponytail-instructions.js` | **Shared instruction builder** — `getPonytailInstructions(mode)` reads `SKILL.md`, filters mode-specific rows, prefixes `PONYTAIL MODE ACTIVE — level: X`; hardcoded `getFallbackInstructions()` if the file read fails. |
| `ponytail-config.js` | **Level resolver** — `PONYTAIL_DEFAULT_MODE` env → `~/.config/ponytail/config.json` `defaultMode` → `full`; `writeDefaultMode()` persists; `isDeactivationCommand()`; `RUNTIME_MODES` vs `VALID_MODES` (`review` is config-only). |
| `ponytail-runtime.js` | Shared runtime helpers (per-session mode state path + IO). |
| `ponytail-statusline.sh` / `.ps1` | Statusline showing the current mode (bash / PowerShell). |

### `commands/` — host slash commands (`.toml`)
`ponytail`, `ponytail-review`, `ponytail-audit`, `ponytail-debt`, `ponytail-gain`,
`ponytail-help` — the `/ponytail*` command definitions for skill-capable hosts.

### `.opencode/` — OpenCode adapter
`plugins/ponytail.mjs` (injects the ruleset every turn at the active level + adds
the commands) · `command/ponytail*.md` ×6 (OpenCode `/ponytail*` commands).

### `.openclaw/skills/` — generated OpenClaw package
`ponytail`, `-review`, `-audit`, `-debt`, `-gain`, `-help` `/SKILL.md` —
**generated** from `skills/` by `build-openclaw-skills.js` (verbatim body, short
rewritten frontmatter); `tests/openclaw-skills.test.js` fails if stale.

### Instruction-file adapters (compact copies of `AGENTS.md`)
`.cursor/rules/ponytail.mdc` · `.windsurf/rules/ponytail.md` ·
`.clinerules/ponytail.md` · `.kiro/steering/ponytail.md` — kept byte-equal to the
canonical `AGENTS.md` body by `check-rule-copies.js`. *(Upstream also lists
`.github/copilot-instructions.md` + `.agents/rules/ponytail.md`; not in this
vendored subset.)*

### Plugin manifests
`.claude-plugin/plugin.json` + `marketplace.json` (Claude Code) ·
`.codex-plugin/plugin.json` (Codex).

### `pi-extension/`
`index.js` (pi agent harness extension, uses `ponytail-instructions.js`) ·
`package.json` · `test/extension.test.js` + `test/helpers.test.js`.

### `scripts/` — the single-source-of-truth guards (→ Spec 327 §7)
`check-rule-copies.js` (drift gate: copies == canonical `AGENTS.md` + safety
invariants present in both `SKILL.md` and `AGENTS.md`) · `build-openclaw-skills.js`
(generate `.openclaw/skills/` from `skills/`).

### `examples/` — "survivor" showcase (over-build → one-liner)
`README.md` + `csv-sum`, `debounce`, `deep-clone`, `email-validation`,
`group-by`, `infinite-scroll`, `modal-dialog`, `number-formatting`, `rate-limit`,
`react-countdown`, `url-params` (`.md` each).

### `benchmarks/`
`README.md` (reproduce) + `results/*.md` ×8 — the measured writeups
(`2026-06-18-agentic.md` is the headline; plus cost-verification, agentic-safety,
robustness-audit, llama-local, and three caveman/v4 comparisons).

## 4. How it's "present every session" (the mechanism)

1. **Hook lane (MCP/CLI hosts with lifecycle hooks):** `claude-codex-hooks.json`
   fires `ponytail-activate.js` on SessionStart and `ponytail-mode-tracker.js` on
   every prompt → both call `getPonytailInstructions(level)` → the ruleset is
   printed into the agent's context. `command -v node` guards mean **no node →
   silent skip**, not an error.
2. **Instruction-file lane (no hooks):** the agent auto-loads `AGENTS.md` or the
   per-host rules file (`.cursor/rules`, `.windsurf/rules`, …) — always-on, but no
   mode switching.
3. **Level state:** resolved `env → config.json → full`; a `/ponytail <level>`
   switch persists to `config.json` so it survives across sessions/processes.

This two-lane design (hooks where available, static rules file otherwise) is
exactly the MCP-vs-CLI parity agency needs.

## 5. The 6 skills (the verb surface — Spec 327 exposes these via the CLI)
- **ponytail** — the always-on discipline (the only one that's a *mode*).
- **ponytail-review** — diff over-engineering review → delete-list.
- **ponytail-audit** — whole-repo over-engineering audit.
- **ponytail-debt** — `ponytail:`-comment debt ledger.
- **ponytail-gain** — measured-impact scoreboard.
- **ponytail-help** — quick reference.

## 6. Benchmarks (headline, `benchmarks/results/2026-06-18-agentic.md`)
Headless agent editing a real FastAPI+React repo, 12 tickets, n=4, Haiku 4.5, vs
the same agent with no skill: **−54% LOC, −22% tokens, −20% cost, −27% time,
100% safe** — the only arm to cut every metric without dropping a guard. (Older
single-shot runs showed 80–94% less code; corrected down to a defensible agentic
mean.)

## 7. Port crosswalk → agency CORE (Spec 326)

| Ponytail (Node) | Agency core port (Spec 326) |
|---|---|
| `skills/ponytail/SKILL.md` (ladder + floor) | `agency/_discipline.py` — canonical text + `render(level, full\|compact)` |
| `ponytail-config.js` (`env → config.json → full`) | `discipline_level` resolution (`PONYTAIL_DEFAULT_MODE` → `.agency/config.json` → `full`) **— same precedence** |
| `writeDefaultMode()` persists to config | `discipline_level(level)` SET → `.agency/config.json` + `DisciplineLevel` node (durable for fresh CLI processes) |
| `getPonytailInstructions()` filter-by-mode | `_discipline.render(level, "full")` (M1) |
| `claude-codex-hooks.json` SessionStart/UserPromptSubmit | `engine.register_hook_handler` (M1) — beside the assumption-guard |
| `ponytail-activate.js` inject at start | M1 SessionStart handler → `{inject}` (CLI lane = `agency hook`) |
| `ponytail-mode-tracker.js` `/ponytail` switch + `stop`/`normal mode` | UserPromptSubmit handler + SET; `off` = deactivation |
| `command -v node` guard / `getFallbackInstructions()` | M1/M2 **silent-degrade** (render failure never fails the verb) |
| *(none — ponytail only injects)* | **M2** per-verb response-envelope-prefix stamp (agency-specific, Spec 146, cache-stable, compact render) |
| `ponytail-statusline.*` shows mode | `agency_doctor` reports `discipline_level` |

**Key divergence:** ponytail is purely an *injected instruction* (it never sees
tool calls). Agency additionally rides the discipline on **every verb return**
(M2) because agency *has* a wire envelope — that is the "with every verb there
is" the directive asks for, and it has no ponytail equivalent.

## 8. License / provenance
MIT (`reference/LICENSE`) — port freely with attribution. Provenance:
`intent:7509dac0`; pivots `reflection:fe553a2e`, `4a4b94a7`; panel-fold
`reflection:197d8531`.
