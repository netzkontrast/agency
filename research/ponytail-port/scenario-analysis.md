# Ponytail — Usage-Scenario Catalog (port → agency)

Read-only analysis of `/home/user/ponytail` to inform a native port into agency
(Spec 332 `frugal` discipline / Spec 333 self-installer). Citations are
`path:line` into the ponytail tree. Nothing here was modified.

The surface is **two layers** that must be ported as one:

1. A **persistent MODE** (`ponytail` itself: `lite|full|ultra|off`) injected into
   every turn by hooks, with resolution `env → config.json → "full"`.
2. **One-shot SKILLS** (`review`, `audit`, `debt`, `gain`, `help`) that render a
   report and persist nothing.

The single most load-bearing finding for the port is in **section 4**: only
`ponytail` (mode) and `ponytail-review` are wired into the hook layer
(`ponytail-mode-tracker.js:24-32`). `audit`, `debt`, `gain`, `help` are
pure slash/skill invocations with NO hook state. The mode↔skill split is the
porting seam.

---

## 1. Surface inventory

| Command / Skill | Trigger phrases | Reads | Writes / Emits | MODE or one-shot | Boundaries (when NOT to fire) |
|---|---|---|---|---|---|
| **`/ponytail [lite\|full\|ultra\|off]`** (`commands/ponytail.toml:1-2`; `skills/ponytail/SKILL.md`) | "ponytail", "be lazy", "lazy mode", "simplest/minimal solution", "yagni", "do less", "shortest path"; complaints about over-engineering/bloat/boilerplate/deps (`SKILL.md:8-12`) | The active mode flag (`.ponytail-active`), the SKILL body filtered by mode (`ponytail-instructions.js:80-85`), the code/task being built | Mode flag write (`ponytail-runtime.js:15-18`); ruleset injected as turn context; `ponytail:` comments left in the code it writes (`SKILL.md:51`); a runnable check for non-trivial logic (`SKILL.md:88-93`) | **Persistent MODE** (`SKILL.md:24-27`: "ACTIVE EVERY RESPONSE … Level persists until changed or session end") | Never simplify away: trust-boundary validation, data-loss-preventing error handling, security, accessibility, anything explicitly requested, hardware calibration knobs (`SKILL.md:77-86`). Governs what you build, not how you talk (`SKILL.md:96-99`). |
| **`/ponytail-review`** (`commands/ponytail-review.toml`; `skills/ponytail-review/SKILL.md`) | "review for over-engineering", "what can we delete", "is this over-engineered", "simplify review", `/ponytail-review` (`ponytail-review/SKILL.md:7-10`) | The **current diff** (`ponytail-review/SKILL.md:13`) | A delete-list, one line per finding `L<line>: <tag> <what>. <replacement>.`; ends `net: -<N> lines possible.` or `Lean already. Ship.` (`ponytail-review/SKILL.md:14-48`) | **Hybrid**: hook tracks a `review` mode (`ponytail-mode-tracker.js:24-25`) but the skill body is one-shot ("Does not apply the fixes", `ponytail-review/SKILL.md:56`) | Scope is over-engineering ONLY; correctness/security/performance explicitly out of scope → route to a normal review (`ponytail-review/SKILL.md:51-55`). Never flag the ponytail-minimum smoke test for deletion. |
| **`/ponytail-audit`** (`commands/ponytail-audit.toml`; `skills/ponytail-audit/SKILL.md`) | "audit this codebase", "audit for over-engineering", "what can I delete from this repo", "find bloat", `/ponytail-audit` (`ponytail-audit/SKILL.md:7-9`) | The **whole tree** (`ponytail-audit/SKILL.md:13`), hunting deps/single-impl interfaces/factories/wrappers/dead flags (`ponytail-audit/SKILL.md:26-29`) | Ranked delete-list `<tag> <what>. <replacement>. [path]`; ends `net: -<N> lines, -<M> deps possible.` or `Lean already. Ship.` (`ponytail-audit/SKILL.md:32-35`) | **One-shot** ("Lists findings, applies nothing. One-shot." `ponytail-audit/SKILL.md:40`) | Same out-of-scope list as review (correctness/security/perf). No hook mode exists for it. |
| **`/ponytail-debt`** (`commands/ponytail-debt.toml`; `skills/ponytail-debt/SKILL.md`) | "ponytail debt", `/ponytail-debt`, "what did ponytail defer", "list the shortcuts", "ponytail ledger", "what did we mark to do later" (`ponytail-debt/SKILL.md:7-8`) | Grep of the repo for `(#\|//) ?ponytail:` markers, skipping `node_modules/.git`/build (`ponytail-debt/SKILL.md:18-22`); optional `git blame -L` for owners | Ledger grouped by file: `<file>:<line>, <what>. ceiling: <…>. upgrade: <…>.`; `no-trigger` tag for markers with no upgrade path; ends `<N> markers, <M> with no trigger.` or `No ponytail: debt. Clean ledger.` (`ponytail-debt/SKILL.md:26-38`) | **One-shot** ("Reads and reports only, changes nothing", `ponytail-debt/SKILL.md:42`). Will write `PONYTAIL-DEBT.md` only if the user asks. | No hook mode. Only `ponytail:`-**prefixed comments** count — prose merely mentioning the convention is excluded (`ponytail-debt/SKILL.md:23-24`). |
| **`/ponytail-gain`** (`commands/ponytail-gain.toml`; `skills/ponytail-gain/SKILL.md`) | `/ponytail-gain`, "ponytail gain", "what does ponytail save", "show ponytail impact", "ponytail scoreboard" (`ponytail-gain/SKILL.md:8`) | NOTHING in the repo — figures are **published benchmark medians** baked into the skill text (`ponytail-gain/SKILL.md:11-14`, `:40-45`) | A fixed ASCII-bar scoreboard (LOC 6–20%, cost 23–53%, speed 3–6× — `ponytail-gain/SKILL.md:26-37`); points at `/ponytail-debt` + `/ponytail-audit` for real per-repo numbers | **One-shot display** ("do NOT change mode, write flag files, or persist anything", `ponytail-gain/SKILL.md:14-15`) | **Honesty boundary**: NEVER print a per-repo savings number — the unbuilt version was never written, so there is no baseline (`ponytail-gain/SKILL.md:40-45`). |
| **`/ponytail-help`** (`commands/ponytail-help.toml`; `skills/ponytail-help/SKILL.md`) | `/ponytail-help`, "ponytail help", "what ponytail commands", "how do I use ponytail" (`ponytail-help/SKILL.md:6`) | NOTHING (static card); documents env/config resolution (`ponytail-help/SKILL.md:43-59`) | A reference card: levels, skills, deactivation, default-mode config, update flow | **One-shot display** ("do NOT change mode, write flag files…", `ponytail-help/SKILL.md:12-13`) | Pure reference; never mutates. |

**Inventory note (drift for the port):** the help card (`ponytail-help/SKILL.md:26-31`)
and `docs/agent-portability.md:35-40` list only `ponytail / review / gain / help`
in their skill tables — `audit` and `debt` exist as commands + SKILLs but are
omitted there. The README command table (`README.md:212-219`) is the complete
list of 6. Port from the README/commands set, not the help card.

---

## 2. Hook & MCP mechanics (file-by-file)

### Event bindings (exact names)

- **Claude / Codex** (`hooks/claude-codex-hooks.json`):
  - `SessionStart` with `"matcher": "startup|resume|clear|compact"` →
    `node …/hooks/ponytail-activate.js` (`:3-15`). `timeout: 5`. Windows variant
    gated on `Get-Command node`.
  - `UserPromptSubmit` (no matcher → every prompt) →
    `node …/hooks/ponytail-mode-tracker.js` (`:17-29`).
  - Both wrap the command as `command -v node >/dev/null 2>&1 && node … || exit 0`
    (`:9`, `:22`) — **node-not-on-PATH ⇒ silent no-op**, skills still work.
- **Copilot** (`hooks/copilot-hooks.json`): lowercase event names `sessionStart`
  (`:4-11`) and `userPromptSubmitted` (`:12-19`), `${PLUGIN_ROOT}` instead of
  `${CLAUDE_PLUGIN_ROOT}`, `timeoutSec` instead of `timeout`. Same two scripts.

### `hooks/ponytail-activate.js` — SessionStart

1. Resolves mode via `getDefaultMode()` (`:24`).
2. If mode `=== "off"` (`:27-32`): `clearMode()` (deletes the flag), emits `"OK"`
   on Claude / `""` on Codex+Copilot, `exit 0`. No flag, no rules.
3. Else writes the flag file with `setMode(mode)` (`:35-39`, best-effort, swallows
   errors).
4. Emits the **mode-filtered SKILL body** via `getPonytailInstructions(mode)`
   (`:42`).
5. Claude-only statusline detection (`:45-74`): reads `$CLAUDE_CONFIG_DIR/settings.json`
   (strips a UTF-8 BOM, `:49`), and if `settings.statusLine` is absent, appends a
   `STATUSLINE SETUP NEEDED:` nudge with a ready-made `statusLine` JSON snippet
   pointing at `ponytail-statusline.sh` / `.ps1` (`:56-71`).
6. `writeHookOutput('SessionStart', mode, output)` (`:76-80`), EPIPE-safe.

### `hooks/ponytail-mode-tracker.js` — UserPromptSubmit

- Reads stdin JSON, strips BOM, lowercases `data.prompt` (`:8-14`).
- Fires only when the prompt **starts with** `/`, `@`, or `$` + `ponytail`
  (`/^[/@$]ponytail/`, `:17`). Normalizes the command (`@`/`$` → `/`, `:19`).
- Routing (`:24-32`):
  - `/ponytail-review` (or `/ponytail:ponytail-review`) → mode `review`.
  - `/ponytail` + arg → `lite|full|ultra|off`; **no/other arg → `getDefaultMode()`**.
  - **Only `ponytail` and `ponytail-review` are matched** — `audit/debt/gain/help`
    are invisible to this hook.
- `mode && mode !== "off"` → `setMode(mode)` + emit `PONYTAIL MODE CHANGED — level: <mode>`
  (`:34-40`). `off` → `clearMode()` + `PONYTAIL MODE OFF` (`:41-44`).
- Separately, `isDeactivationCommand(prompt)` → `clearMode()` + `PONYTAIL MODE OFF`
  (`:48-51`).

### Mode resolution & persistence (`hooks/ponytail-config.js`)

- `getDefaultMode()` (`:67-87`): **1)** `PONYTAIL_DEFAULT_MODE` env (validated
  against `VALID_MODES`, `:69-72`) → **2)** `config.json.defaultMode`
  (`:75-83`) → **3)** `"full"` (`:86`). This is the canonical `env → config → full`
  chain.
- Config dir (`getConfigDir`, `:45-56`): `$XDG_CONFIG_HOME/ponytail` → (Windows)
  `%APPDATA%\ponytail` → `~/.config/ponytail`. File is `config.json` (`:58-60`).
- `VALID_MODES = ['off','lite','full','ultra','review']` (`:17`);
  `RUNTIME_MODES = ['off','lite','full','ultra']` (`:18`) — `review` is config-only,
  never a runtime intensity.
- `isDeactivationCommand` (`:40-43`): matches **only** the whole trimmed,
  punctuation-stripped message `=== "stop ponytail"` or `=== "normal mode"` — a
  deliberate fix so "add a normal mode toggle" does NOT deactivate (`:36-39`).
- `writeDefaultMode` (`:89-97`) persists `{defaultMode}` (used by config tooling,
  not the hot path).

### Flag-file persistence (`hooks/ponytail-runtime.js`)

- Flag is `.ponytail-active` (`:5`) in: `~/.claude` (or `$CLAUDE_CONFIG_DIR`) on
  Claude; `$PLUGIN_DATA` on Codex; `$COPILOT_PLUGIN_DATA` on Copilot (`:6-13`).
  Host is detected purely from env vars (`:6-7`).
- `setMode` writes the bare mode string (`:15-18`); `clearMode` unlinks (`:20-22`).
- `writeHookOutput` (`:24-43`) is the per-host serializer:
  - **Copilot**: `{additionalContext: ctx}` on SessionStart only, else `{}` (`:25-30`).
  - **Codex**: `{systemMessage: "PONYTAIL:<MODE>", hookSpecificOutput:{hookEventName,additionalContext}}` (`:31-41`).
  - **Claude**: raw `process.stdout.write(context)` (`:42`).

### Mode-filtered instruction injection (`hooks/ponytail-instructions.js`)

- `getPonytailInstructions(mode)` (`:71-86`):
  - `review` is in `INDEPENDENT_MODES` (`:8`) → returns a one-liner pointer
    `… Behavior defined by /ponytail-review skill.` (`:74-76`), NOT the ladder.
  - Else reads `skills/ponytail/SKILL.md` (`SKILL_PATH`, `:9`), filters by mode,
    prefixes `PONYTAIL MODE ACTIVE — level: <mode>` (`:80-82`). On any read error
    → `getFallbackInstructions` (a hard-coded compact ruleset, `:39-69`, `:83-84`).
- `filterSkillBodyForMode` (`:11-37`): strips frontmatter (`:13`), then keeps every
  line EXCEPT mode-table rows / worked-example bullets whose **label is a mode name**
  and ≠ the active mode (`:20-34`). Crucially, a bullet whose label is NOT a mode
  (e.g. `- No unrequested abstractions:`) is kept verbatim (`:16-18`, `:28-31`) —
  this is the subtle correctness rule. Net effect: `full` strips the lite/ultra
  rows of the Intensity table (`SKILL.md:66-70`) and the lite/ultra example lines
  (`SKILL.md:73-75`), leaving the universal ladder + rules intact.

### MCP server (`ponytail-mcp/`)

- **Why it exists** (`README.md:8-11`, `ponytail-mcp/README.md:8-11`): the always-on
  hooks inject every turn, but there is no portable MCP primitive for "inject into
  every turn". The MCP is the clean fallback for hosts whose only injection point
  is the prompt menu / tool calls.
- `index.js` registers exactly two things over stdio:
  - **Prompt `ponytail`** (`:19-29`): user-invoked, optional `mode` enum
    (`lite|full|ultra`, `:14-17`), returns `buildInstructions(mode)` as a user message.
  - **Tool `ponytail_instructions`** (`:31-46`): same text + `structuredContent
    {mode, instructions}`, `readOnlyHint:true, openWorldHint:false` (`:36-38`).
- `instructions.js`: `MODES = ["lite","full","ultra"]` (`:11`); `resolveMode`
  (`:16-22`) maps unknown/empty/`off` → default → `"full"`; `buildInstructions`
  (`:24-26`) **reuses the same `getPonytailInstructions` builder as the hooks**
  (`:6-8`) so every host emits identical rules. The MCP serves NONE of the
  review/audit/debt/gain/help skills — only the mode ladder.

---

## 3. Scenario catalog (≥6 per command)

Conventions: **FIRES** = which hook/skill; **READS** = files/state; **EMITS** =
what is executed/printed/written; **EDGE** = mode/edge interaction.

### `/ponytail` (the persistent mode)

1. **Fresh session, default config.** Situation: user opens Claude Code, no
   `PONYTAIL_DEFAULT_MODE`, no config.json. FIRES: `ponytail-activate.js` on
   `SessionStart` (`startup`). READS: `getDefaultMode()` falls through env+config
   to `"full"` (`config.js:86`); `skills/ponytail/SKILL.md`. EMITS: writes
   `.ponytail-active`="full" (`runtime.js:15`); injects `PONYTAIL MODE ACTIVE —
   level: full` + the ladder with lite/ultra rows stripped; appends a statusline
   nudge because `settings.json` has no `statusLine` (`activate.js:56-71`). EDGE:
   happy path; the nudge appears once and stops after the user adds the statusline.

2. **`export PONYTAIL_DEFAULT_MODE=ultra` then new session.** FIRES: activate.
   READS: env wins at `config.js:69-72`. EMITS: flag="ultra"; injected body keeps
   the **ultra** Intensity row + ultra example only (`instructions.js:20-34`),
   prefixed `level: ultra`. EDGE: env beats a `{"defaultMode":"lite"}` config.json
   — env > config > full (`config.js:67-87`).

3. **Mid-session `/ponytail ultra`.** FIRES: `ponytail-mode-tracker.js` on
   UserPromptSubmit (`/^[/@$]ponytail/` matches, `:17`; arg `ultra` → `:29`).
   READS: nothing but the prompt. EMITS: `setMode("ultra")` overwrites the flag;
   stdout `PONYTAIL MODE CHANGED — level: ultra`. EDGE: the **mode flip is by the
   tracker; the ladder text is NOT re-injected this turn** — only the activate hook
   injects the full body. So the LLM sees the CHANGED banner now and the
   ultra-filtered ladder on the *next* SessionStart. (Port implication: a native
   port should re-inject on switch, not only at session start.)

4. **`/ponytail` with no argument.** FIRES: tracker; `arg=""` → `mode =
   getDefaultMode()` (`:31`). EMITS: re-asserts the default mode (flag rewritten),
   `MODE CHANGED — level: <default>`. EDGE: README documents this as "reports the
   current level" (`README.md:214`) but the code actually **re-applies the default**
   — if you were in `ultra` and type bare `/ponytail`, you drop to `full` (unless
   env/config set otherwise). Subtle behavior to preserve or deliberately fix.

5. **`/ponytail off` then a coding task.** FIRES: tracker, `arg=off` → `mode=off`
   → `clearMode()` + `PONYTAIL MODE OFF` (`:30`,`:41-43`). READS: deletes
   `.ponytail-active`. EMITS: subsequent turns inject NOTHING (the activate hook
   only injects at SessionStart; the flag is gone but in-session there's no
   per-turn injector, so the rules simply aren't re-stated). EDGE: the LLM may
   still "feel lazy" from the SessionStart context already in history — `off`
   prevents *future* re-assertion, not retroactive forgetting.

6. **`stop ponytail` as a standalone message.** FIRES: tracker via
   `isDeactivationCommand` (`:48`). EMITS: `clearMode()` + `PONYTAIL MODE OFF`.
   EDGE: "add a normal-mode toggle to the UI" does NOT deactivate — the whole-message
   equality guard (`config.js:40-43`) is the explicit fix for that false positive.

7. **Resume / compact.** FIRES: activate (matcher includes `resume|clear|compact`,
   `claude-codex-hooks.json:5`). READS: re-resolves mode from env/config (NOT from
   the prior flag — resolution always recomputes). EMITS: re-writes the flag, re-injects
   the ladder. EDGE: if the user had switched to `ultra` mid-session via the tracker
   (flag="ultra") but env/config say `full`, a **compact reverts to full** — the
   live runtime switch is not durable across SessionStart. Port hazard: decide whether
   a runtime switch should survive compaction.

8. **node not on PATH (nvm/Nix).** FIRES: nothing — `command -v node … || exit 0`
   (`claude-codex-hooks.json:9,22`). EMITS: no flag, no injection, no error
   (`README.md:99`). EDGE: the `/ponytail*` SKILLs still work (host loads SKILL.md
   directly); only always-on activation goes quiet. The statusline `.sh` also no-ops
   (`ponytail-statusline.sh:4`).

9. **Complex request under `full`.** Situation: "build a plugin system with
   hot-reload." FIRES: in-context ladder (already injected). EMITS (model behavior
   per `SKILL.md:49`): ships the lazy version AND questions it in the same response
   — "Did X; Y covers it. Need full X? Say so." EDGE: never stalls asking for
   clarification it can default; leaves a `ponytail:` comment marking the ceiling.

10. **Codex host, `@ponytail ultra`.** FIRES: tracker normalizes `@`→`/` (`:19`),
    arg `ultra`. EMITS via Codex serializer: `{systemMessage:"PONYTAIL:ULTRA",
    hookSpecificOutput:{additionalContext:"PONYTAIL MODE CHANGED — level: ultra"}}`
    (`runtime.js:31-41`). EDGE: flag lives under `$PLUGIN_DATA`, not `~/.claude`.

### `/ponytail-review`

1. **`/ponytail-review` on a staged diff.** FIRES: tracker sets mode `review`
   (`:24`) AND the SKILL/command body runs. READS: the current `git diff`
   (`ponytail-review/SKILL.md:13`). EMITS: per-finding lines + `net: -<N> lines
   possible.` EDGE: the hook writes flag="review", but `getPonytailInstructions`
   returns only a pointer line for `review` (`instructions.js:74-76`), so the
   ladder is NOT injected — review is a one-shot dressed as a mode.

2. **Diff with nothing to cut.** READS: a lean diff. EMITS: exactly `Lean already.
   Ship.` and stops (`ponytail-review/SKILL.md:48`). EDGE: must NOT invent findings
   to look useful.

3. **Diff with a reinvented stdlib function.** EMITS: e.g. `L30-44: shrink: manual
   loop builds dict. dict(zip(keys, values)), 1 line.` (`ponytail-review/SKILL.md:42`).
   EDGE: tag discipline — `stdlib:`/`native:`/`yagni:`/`delete:`/`shrink:` only
   (`ponytail-review/SKILL.md:22-28`).

4. **Diff contains a correctness bug.** EMITS: nothing about the bug — out of scope,
   routed to a normal review (`ponytail-review/SKILL.md:51-55`). EDGE: the boundary
   is a feature; a native port must NOT bleed correctness findings into this verb.

5. **Diff whose only "extra" is the ponytail smoke test.** EMITS: the test is NOT
   flagged — it's the ponytail minimum, not bloat (`ponytail-review/SKILL.md:54-55`).
   EDGE: self-referential exemption.

6. **Multi-file diff.** EMITS: findings switch to `<file>:L<line>:` form
   (`ponytail-review/SKILL.md:14-15`). EDGE: format adapts to scope.

7. **"is this over-engineered?" (NL trigger, no slash).** FIRES: the SKILL by
   description match (`ponytail-review/SKILL.md:7-9`); the **tracker does NOT fire**
   (no `/ponytail` prefix), so no `review` flag is written. EDGE: skill-only path —
   identical output, no hook state. Confirms review works without the hook.

8. **`/ponytail ultra` then `/ponytail-review`.** EDGE: the review output is
   unchanged by intensity — review has no lite/full/ultra variants. The prior
   `ultra` flag is overwritten to `review` by the tracker (`:24`); after the review,
   nothing restores `ultra` (port hazard: mode is lost).

### `/ponytail-audit`

1. **`/ponytail-audit` on a small repo.** FIRES: command/SKILL only (the tracker
   has NO audit branch, `ponytail-mode-tracker.js:24-32`). READS: the whole tree
   (`ponytail-audit/SKILL.md:13`). EMITS: ranked list biggest-cut-first + `net:
   -<N> lines, -<M> deps possible.` EDGE: no flag is ever written for audit.

2. **Repo with a single-implementation interface.** EMITS: `yagni: AbstractRepository
   with one implementation. Inline it…` (cf. `ponytail-review/SKILL.md:38`); hunts
   the list at `ponytail-audit/SKILL.md:26-29`. EDGE: ranking — biggest cut first.

3. **Repo depending on a lib the stdlib ships.** EMITS: `native:`/`stdlib:` finding
   naming the platform feature (e.g. `moment.js` → `Intl.DateTimeFormat`,
   `docs/platform-native.md:65`). EDGE: counts toward `-<M> deps`.

4. **Already-lean repo.** EMITS: `Lean already. Ship.` (`ponytail-audit/SKILL.md:35`).

5. **Huge monorepo.** EDGE: SKILL gives no pagination/scoping guidance — the
   model must scope itself; a native port should add a path/glob arg (port gap).
   READS: still "the whole tree" — potentially very large, no budget guard.

6. **User asks to apply the cuts.** EMITS: refuses to apply — "Lists findings,
   applies nothing. One-shot." (`ponytail-audit/SKILL.md:40`). EDGE: report-only
   invariant; mutation would need a separate verb.

### `/ponytail-debt`

1. **`/ponytail-debt` with several `# ponytail:` comments.** FIRES: SKILL only
   (no tracker branch). READS/EXECUTES: `grep -rnE '(#|//) ?ponytail:' .` skipping
   `node_modules/.git`/build (`ponytail-debt/SKILL.md:18-22`). EMITS: one row per
   hit grouped by file with ceiling+upgrade parsed from the comment
   (`ponytail-debt/SKILL.md:28-30`).

2. **A `ponytail:` comment with no upgrade path.** EMITS: that row tagged
   `no-trigger` (`ponytail-debt/SKILL.md:36-37`) — the rot-risk flag. EDGE: this is
   the comment-with-no-upgrade-path scenario; it's surfaced, not dropped.

3. **No markers anywhere.** EMITS: `No ponytail: debt. Clean ledger.`
   (`ponytail-debt/SKILL.md:38`).

4. **Prose that mentions "ponytail:" outside a comment.** EMITS: excluded — the
   `(#|//)` prefix requirement keeps non-comment prose out (`ponytail-debt/SKILL.md:23-24`).
   EDGE: precision guard. (Note: a Python `#` and JS `//` are covered; other comment
   syntaxes need the user to "add other comment prefixes", `ponytail-debt/SKILL.md:20`.)

5. **User wants owners.** EMITS: appends `git blame -L<line>,<line>` per row
   (`ponytail-debt/SKILL.md:31-33`). EDGE: optional enrichment, needs git.

6. **User says "persist the ledger".** EMITS: writes `PONYTAIL-DEBT.md` — but ONLY
   when asked (`ponytail-debt/SKILL.md:42-43`). EDGE: the one write path in the
   whole one-shot family; default is read-only.

7. **Stack with non-`#`/`//` comments (e.g. SQL `--`, HTML `<!-- -->`).** EDGE:
   the default grep MISSES them (`ponytail:` in `<!-- ponytail: browser has one -->`
   from `README.md:43` would need `<!--` added). Port hazard: the marker scanner must
   be comment-syntax-aware, not hardcoded to two prefixes.

### `/ponytail-gain`

1. **`/ponytail-gain`.** FIRES: SKILL only. READS: NOTHING from the repo. EMITS:
   the fixed ASCII scoreboard (`ponytail-gain/SKILL.md:26-37`) — LOC 6–20%, cost
   23–53%, speed 3–6×. EDGE: figures are static benchmark medians.

2. **User asks "how much did I save in THIS repo?"** EMITS: refuses a per-repo
   number; explains the unbuilt version was never written (`ponytail-gain/SKILL.md:40-45`),
   redirects to `/ponytail-debt` + `/ponytail-audit`. EDGE: the honesty boundary —
   the single most important rule of this command.

3. **Invoked while in `ultra`.** EMITS: scoreboard unchanged; does NOT touch the
   flag (`ponytail-gain/SKILL.md:14-15`). EDGE: one-shot purity — mode survives.

4. **Invoked right after `/ponytail off`.** EMITS: still renders (it's static text,
   independent of mode). EDGE: gain is decoupled from activation state.

5. **Plain-terminal host (no ANSI).** EDGE: bars are "plain ASCII" with ANSI only
   in the *statusline* script, not the card — renders fine; but the box-drawing
   chars (`█▌·▸▼`) assume UTF-8. Port hazard: ASCII-only fallback for dumb terminals.

6. **User asks to update the numbers.** EDGE: the figures are frozen in the SKILL
   body sourced from `benchmarks/` + README (`ponytail-gain/SKILL.md:11-13`). A
   native port should derive them from a data file, not inline prose, or they rot
   (and they'd violate agency's "no hardcoded values / no frozen snapshot" rule —
   see hazards).

### `/ponytail-help`

1. **`/ponytail-help`.** FIRES: SKILL only. READS: nothing. EMITS: the levels +
   skills tables, deactivation, config, update sections (`ponytail-help/SKILL.md:15-65`).

2. **"how do I use ponytail" (NL).** FIRES: by description match
   (`ponytail-help/SKILL.md:6`). EMITS: same card. EDGE: no slash needed.

3. **User asks how to change the default.** EMITS: the env/config block —
   `PONYTAIL_DEFAULT_MODE` and `~/.config/ponytail/config.json`, resolution
   `env > config > full` (`ponytail-help/SKILL.md:43-59`). EDGE: this is the only
   surface that documents the resolution chain to the user.

4. **User asks how to turn it off.** EMITS: "stop ponytail" / "normal mode" /
   `/ponytail off` (`ponytail-help/SKILL.md:38-41`).

5. **Invoked in any mode.** EMITS: card unchanged; mutates nothing
   (`ponytail-help/SKILL.md:12-13`). EDGE: one-shot.

6. **Help lists fewer commands than exist.** EDGE: the card omits `audit` + `debt`
   from its skills table (`ponytail-help/SKILL.md:26-31`) — a real drift the port
   should fix by generating help from the command registry, not hand-maintaining it.

---

## 4. Fires-on-hooks vs. fires-on-skill-invocation (the port-critical section)

| Command | Hook-injected (always-on)? | Slash/skill (explicit)? | Tracker has a branch? | Classification & WHY |
|---|---|---|---|---|
| **`ponytail` (mode)** | **YES** — injected every SessionStart by `ponytail-activate.js`; re-asserted on resume/clear/compact | YES — `/ponytail lite\|full\|ultra\|off` switches it | YES (`mode-tracker.js:26-32`) | **BOTH, hook-primary.** It is a *standing posture*, not an action. The hook puts the ladder in context every turn so the model can't drift back to over-building (`SKILL.md:24-27`). The slash form only flips intensity. Port: this MUST become a persistent, per-session/per-turn injected discipline + a switch verb. |
| **`ponytail-review`** | NO ruleset injection (the `review` flag yields only a pointer line, `instructions.js:74-76`) | **YES** — the real behavior | YES, but cosmetic (`mode-tracker.js:24`) | **Explicit skill** that the hook merely *labels*. The `review` "mode" is vestigial — it tracks the last verb for the statusline, it does not change per-turn behavior. Port: model as a one-shot verb over the diff; the mode flag is droppable. |
| **`ponytail-audit`** | NO | **YES** | **NO** | **Pure explicit skill.** A whole-repo scan is an action you run on demand, never a standing posture. Port: one-shot verb, repo-wide input. |
| **`ponytail-debt`** | NO | **YES** | **NO** | **Pure explicit skill** (a grep-and-tabulate). Run when you want the ledger. The ONLY family member that can write a file, and only on request. Port: one-shot verb; optionally persist to a node/file. |
| **`ponytail-gain`** | NO | **YES** | **NO** | **Pure explicit display.** Static benchmark card. Port: one-shot verb; back the numbers with a data source, not frozen prose. |
| **`ponytail-help`** | NO | **YES** | **NO** | **Pure explicit display.** Port: generate from the live command registry to avoid the audit/debt drift. |

**The one sentence for the port:** *only `ponytail` itself is genuinely a hook —
an always-on injected discipline — and `ponytail-review` borrows the hook only for
a status label. The other four (`audit`, `debt`, `gain`, `help`) are plain
on-demand skills with no runtime state.* So a native agency port is:
**one persistent discipline (`frugal`, injected per turn, with a `lite/full/ultra/off`
switch that resolves env → config/graph → full) + five stateless verbs.** The
mode-vs-skill seam (`mode-tracker.js:24-32`) is exactly where ponytail itself draws
the line — mirror it.

---

## 5. Port hazards (JS→Python / agency substrate)

- **No portable "inject every turn" primitive.** The whole always-on effect rests on
  Claude/Codex `SessionStart` + `UserPromptSubmit` hooks; the MCP README explicitly
  concedes there's no cross-host per-turn injection (`ponytail-mcp/README.md:8-11`).
  In agency, the equivalent is a session-scoped discipline re-asserted each turn
  (closer to a per-turn context contributor than a one-shot skill). Don't port it as
  a slash-only skill or the "persistence" guarantee (`SKILL.md:24-27`) is lost.
- **Node-on-PATH dependence.** Every hook is `command -v node … || exit 0`
  (`claude-codex-hooks.json:9,22`); statusline is bash/ps1 (`ponytail-statusline.sh`,
  `.ps1`). A Python/graph port removes the Node dep entirely — good — but must
  replicate the **graceful-degrade** contract (silent no-op when the runtime is
  missing, skills still work).
- **Per-host hook JSON & env-var host detection.** Three event-name dialects
  (`SessionStart`/`startup|resume|clear|compact` vs `sessionStart` vs
  `userPromptSubmitted`) and three flag locations keyed off `CLAUDE_CONFIG_DIR` /
  `PLUGIN_DATA` / `COPILOT_PLUGIN_DATA` (`runtime.js:6-13`). agency has one substrate;
  collapse to a single in-graph state with no per-host branching.
- **Filesystem config/flag → graph DB.** Two pieces of state: `.ponytail-active`
  (the live mode) and `~/.config/ponytail/config.json` (the default). In agency both
  become graph/Document state. Preserve the **resolution order** env → persisted →
  `full` (`config.js:67-87`) exactly; it's user-visible (documented in
  `ponytail-help/SKILL.md:43-59`).
- **Statusline script.** `[PONYTAIL]` / `[PONYTAIL:ULTRA]` badge reads the flag file
  with ANSI 256-color (`ponytail-statusline.sh:8-12`). agency's statusline analogue
  would read the mode from the graph; the SessionStart "STATUSLINE SETUP NEEDED"
  nudge (`activate.js:56-71`) is Claude-Code-settings-specific and likely drops.
- **Mode-filtering parser is brittle string-munging.** `filterSkillBodyForMode`
  regex-filters the SKILL markdown by mode-keyed table rows / bullet labels
  (`instructions.js:11-37`), with a hand-tuned guard so non-mode bullets survive
  (`:16-18`). Porting this verbatim is fragile; better to author the three
  intensities as structured data (per-mode fields) rather than re-deriving by regex.
  (This also aligns with agency's "derive, don't duplicate" doctrine.)
- **`ponytail-gain` frozen numbers vs agency's no-snapshot rule.** The scoreboard
  hardcodes benchmark medians in prose (`ponytail-gain/SKILL.md:26-37`). agency
  CLAUDE.md rule 8 forbids frozen snapshots / magic numbers; the port should source
  the figures from a data file (or label them clearly as fixed published medians
  with a rationale), not inline literals that rot.
- **`ponytail-debt` grep is comment-syntax-limited.** Hardcoded to `#` and `//`
  (`ponytail-debt/SKILL.md:18`), missing SQL `--`, HTML `<!-- -->`, etc. — the repo's
  own example marker is an HTML comment (`README.md:43`). A native scanner should be
  language-aware. Also: the `git blame`/`grep` shell-outs assume a POSIX toolchain.
- **`/ponytail` (no-arg) semantics mismatch.** README says it "reports the current
  level" (`README.md:214`); the tracker actually re-applies the default
  (`mode-tracker.js:31`). Pick one for the port and make the docs match — agency's
  doc-drift guardrails will flag the divergence.
- **Runtime switch not durable across compaction.** A `/ponytail ultra` flag set by
  the tracker is overwritten by the next SessionStart's env/config resolution
  (scenario 7). Decide deliberately whether a live switch should persist; the graph
  makes durable per-session mode trivial, so this is an opportunity, not just a port.
- **Audit/debt have no input scoping or budget guard.** "Scan the whole tree"
  (`ponytail-audit/SKILL.md:13`) with no path/glob/size limit — fine for ponytail's
  prose, a real concern when wired to agency tooling on a monorepo. Add scoping +
  a budget guard (and never truncate captured findings — agency rule 9).
- **`audit`/`debt` invisible to the tracker.** If the port keeps a mode badge, note
  that ponytail itself never badges these four; don't add hook state they don't need.

---

## Appendix — provenance opportunity (agency-specific)

Every ponytail action is currently fire-and-forget. In agency, the natural win is to
record each run as provenance: a `frugal` discipline run, a review/audit producing
*finding* artefacts, a debt scan producing a ledger node, so "what did we defer" is a
graph query rather than a re-grep. ponytail's `ponytail:` comment convention
(`SKILL.md:51`) maps cleanly onto a typed debt edge. This is additive — out of scope
for a literal port, but it's where the substrate beats the original.
