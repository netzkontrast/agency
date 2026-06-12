---
spec_id: "280"
slug: hooks-install-and-doctor
status: partial
last_updated: 2026-06-12
owner: "@agency"
enhances: "076"
depends_on: ["076", "062", "064", "073", "075", "170", "055", "148", "195"]
vision_goals: [2, 5, 8]
affects:
  - agency/_hooks.py
  - agency/install.py
  - agency/engine.py
  - hooks/dispatch
  - tests/test_hooks_install.py
---

# Spec 280 — hooks install verification + foreign-hook wrapping

## Why

The agency plugin **already ships hooks** (Spec 076 unified-event-hook
SHIPPED): `hooks/hooks.json` declares PreToolUse / PostToolUse /
SessionStart / UserPromptSubmit / Stop / SubagentStop / SessionEnd, all
routed through `${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd dispatch` to
`agency hook` which records `Event` nodes in the graph. Spec 062
auto-installs the engine on SessionStart. Spec 148 surfaces the
intent-capture interview.

But in a **fresh repo, fresh Claude Code install**, none of this
fires. The actual end-user gaps:

1. **Plugin not enabled** — the user's `.claude/settings.json`
   `enabledPlugins` block doesn't list `agency@netzkontrast`
   (marketplace install hasn't happened or was skipped). Hooks DON'T
   FIRE because Claude Code only reads them from enabled plugins.
2. **`agency` CLI not on PATH** — Spec 062's auto-pipx-install can
   silently fail (no internet, permission denied, …). The dispatcher
   then exits 0 with no recording; nothing in the graph reveals it.
3. **Foreign hooks colliding** — the user has other plugins
   (`bitwize-music`, `superpowers`, hand-authored) whose hooks already
   matched the same events. Today agency-then-foreign run independently
   and the foreign hook escapes the provenance umbrella. Per the
   user directive, foreign hooks must be **merged via the `shell`
   capability** so:
   - The foreign hook still runs (no behavior loss).
   - Its stdin/stdout/stderr is captured as a `shell.run` Invocation.
   - The Event node Spec 076 records carries the wrapped command's
     exit_code + summary on its `properties.foreign_hook` field.
   - The provenance moat (Goal 2) extends to every hook on the box.
4. **No diagnostic surface** — there's no `agency_doctor.hooks` field
   to verify the state, and no `agency hook --self-test` command to
   prove the dispatcher path end-to-end.
5. **No bypass-routing advice** — when the AI runs `Bash("git commit
   …")` instead of `branch.commit_smart`, the Spec 076 dispatcher
   records the Event but doesn't EMIT routing advice. Spec 195 + Spec
   229 cover the BoundaryUse recording surface; Spec 280 Slice 1 ships
   the **advisory stderr** path so the user gets immediate routing
   feedback before the heavier BoundaryUse loop lands.

This spec is the verification + repair + composition surface that
makes the whole hook stack reliably load-bearing in a fresh repo.

## Done When

- [ ] **`agency/_hooks.py` ships** as the single source of truth:
      - `CANONICAL_SETTINGS_PATCH` — the `.claude/settings.json`
        snippet that enables the agency plugin (`enabledPlugins`
        entry + marketplace entry; no hooks block, since hooks live
        in the plugin's own `hooks/hooks.json`).
      - `merge_settings(user_settings, canonical=CANONICAL_SETTINGS_PATCH)`
        — pure function. Folds the canonical patch into a settings
        dict, preserving every other key.
      - `detect_foreign_hooks(user_settings)` →
        `list[ForeignHook{event, matcher, command, source: Literal["user-settings","unknown"]}]`
        — pure function. Walks the user's `hooks` block (when present
        — users CAN author hooks at the `.claude/settings.json` level)
        and classifies any entry whose `command` doesn't already
        invoke the agency dispatcher.
      - `wrap_foreign_hook(foreign_hook)` → wrapped entry whose
        command is `agency shell run --capture --provenance --hook-wrap
        -- <original_command>`. The original still runs; agency
        captures the run + the dispatched Event carries the wrapped
        exit_code / tail-output.
      - `check_install(user_settings, env, plugin_root=…)` →
        `InstallStatus{plugin_enabled: bool, cli_on_path: bool,
        hook_scripts_present: bool, foreign_hooks: list,
        wrapped_count: int, drift: list[str], next_steps: list[str]}`
        — pure invariant check. Reads the user settings + env + the
        plugin root's `hooks/` dir. No side effects.
- [ ] **`agency_doctor.hooks`** field returns the
      `InstallStatus.to_dict()` per call, including
      `next_steps` (copy-pasteable repair calls per the existing
      doctor convention).
- [ ] **`agency.install` writes/merges** `.claude/settings.json`:
      1. If the file exists, the prior content lands at
         `.claude/settings.json.bak` (overwriting any prior backup);
      2. `merge_settings` folds in the canonical patch (preserves
         existing `enabledPlugins`, `extraKnownMarketplaces`, …);
      3. `detect_foreign_hooks` + `wrap_foreign_hook` runs against
         the `hooks` key; each foreign entry is rewritten to the
         shell-wrapped form. The original command is preserved at
         `entry.hooks[0]._wrapped_from` so users can audit;
      4. The merged file is written; the result is byte-identical to
         a second run (idempotent invariant).
- [ ] **Self-test command** — `python -m agency.cli hook self-test`
      runs each hook event with a synthetic JSON payload, verifies the
      dispatcher emits an `Event` node, and reports `{ok, events,
      missing}`. Reused by the doctor when called with
      `--probe-hooks=true`.
- [ ] **Slice 1 routing advice in `hooks/dispatch`** — extend the
      existing dispatcher so when it receives a PreToolUse payload
      whose `tool_name == "Bash"` and whose `tool_input.command`
      starts with `git commit` / `git push` / `pytest` /
      `python -m pytest`, the dispatcher prints a one-line stderr
      hint pointing at the capability verb. ADVISORY only (exit 0;
      no blocking). Same for Edit / Write of `Plan/*/spec.md`.
- [ ] **Idempotence invariant** — running `agency.install` twice
      yields a byte-identical `.claude/settings.json`. (Drift test
      compares JSON-normalized output across two install runs.)
- [ ] **Preservation invariant** — every top-level key the user
      authored that isn't part of the canonical patch (e.g.
      `enabledPlugins` for non-agency plugins,
      `extraKnownMarketplaces`, custom `hooks` entries on unrelated
      tools) survives the merge unchanged.
- [ ] **Foreign-hook wrap invariant** — for every foreign-hook entry
      detected pre-install, there is exactly ONE corresponding
      shell-wrapped entry post-install; its `_wrapped_from` field
      matches the original command verbatim; running install twice
      does NOT double-wrap.
- [ ] **Sync/async preservation invariant** — `wrap_foreign_hook`
      preserves the foreign entry's `async` flag verbatim. A
      sync-blocking foreign hook stays sync (blocks the wrapped
      command); an async foreign hook stays async (records but
      doesn't gate). Changing this would silently flip the foreign
      hook's semantics.
- [ ] **Async-flag correction for the agency hooks** — the canonical
      patch sets `async=false` on PreToolUse + UserPromptSubmit and
      `async=true` elsewhere (per the table in §"Sync vs async per
      event" below). The install side-effect corrects a stale
      `hooks.json` if needed.
- [ ] **Failure modes** (Spec 151 Codes):
      - `Codes.HOOKS_FILE_UNWRITABLE` when `.claude/settings.json`
        parent can't be created or written;
      - `Codes.HOOKS_INVALID_JSON` when the prior file isn't valid
        JSON (backup is still written; doctor reports the parse
        error so the user can repair manually);
      - `Codes.HOOKS_FOREIGN_UNWRAPPABLE` when a foreign hook's
        command can't be safely shell-quoted (e.g. carries a literal
        unescaped quote we can't reason about) — install reports the
        offender and SKIPS the wrap (preserves the original).
- [ ] **Tests** (`tests/test_hooks_install.py`):
      - `CANONICAL_SETTINGS_PATCH` shape (plugin entry + marketplace
        entry present);
      - `merge_settings` preserves other keys (preservation invariant);
      - `merge_settings` is idempotent (byte-identical 2nd run);
      - `detect_foreign_hooks` finds an entry the user authored at
        `.claude/settings.json` hooks level;
      - `wrap_foreign_hook` produces the shell-wrapped form with
        `_wrapped_from` carrying the original;
      - install rewrites foreign hooks ONCE — re-running install
        doesn't double-wrap;
      - install creates `.bak` on first run; subsequent runs
        overwrite it;
      - `check_install` reports `plugin_enabled=False`
        + `next_steps[0]` carries the marketplace install pointer
        when the plugin isn't enabled;
      - `agency_doctor()` returns a `hooks` field with the documented
        shape;
      - the routing-advice dispatcher emits the `git commit` →
        `branch.commit_smart` hint on stderr; exit_code 0
        (advisory invariant).
- [ ] **TODO row + drift clean.**

## Worked example (Given/When/Then)

```text
Given:  fresh clone of agency; `~/.claude/settings.json` carries only
        `enabledPlugins: {"bitwize-music@bitwize-music": true}` and
        NO agency entry; `agency` CLI not on PATH
When:   user runs `python -m agency.install`
Then:   `.claude/settings.json.bak` preserves the prior file;
        `.claude/settings.json` adds `agency@netzkontrast` to
        `enabledPlugins` AND the `extraKnownMarketplaces` entry;
        bitwize-music entry SURVIVES UNCHANGED;
        doctor reports `plugin_enabled=True`, `cli_on_path=False`,
        `next_steps[0]` = "agency CLI not on PATH — install via
        `pipx install git+https://github.com/netzkontrast/agency`"

Given:  user-level `~/.claude/settings.json` carries a hand-authored
        hook `{event: PreToolUse, matcher: "Bash", command: "/usr/local/
        bin/audit-cmd.sh"}`
When:   `python -m agency.install` runs
Then:   detect_foreign_hooks returns 1 entry;
        the new settings.json wraps it as
        `{type: command, command: 'agency shell run --capture
        --provenance --hook-wrap -- "/usr/local/bin/audit-cmd.sh"',
        _wrapped_from: "/usr/local/bin/audit-cmd.sh"}`;
        the original behavior is preserved (the audit script still
        runs); agency captures its stdin/stdout/stderr as a shell.run
        Artefact linked into the Spec 076 Event chain;
        running install AGAIN produces a byte-identical file
        (no double-wrap).

Given:  AI runs `Bash(command="git commit -m 'spec(279)'")` mid-session
When:   the dispatcher fires under PreToolUse
Then:   stderr prints "→ prefer `branch.commit_smart('spec(279)')` for
        provenance + smart conventional-commit formatting"
        AND the tool still runs (advisory only in Slice 1);
        the Event node carries `routed=False` so the dogfood loop can
        track the bypass-rate baseline (Spec 195 records BoundaryUse
        when it lands).

Given:  `~/.claude/settings.json` exists but is malformed JSON
When:   `python -m agency.install` runs
Then:   the prior content STILL lands at `.bak` (preservation);
        install raises `Codes.HOOKS_INVALID_JSON` with the parse error
        AND the line number;
        the original file is NOT overwritten (we don't clobber
        unreadable user state).

Given:  `agency_doctor()` after a clean install
When:   the user calls it
Then:   `hooks.enabled=True`, `hooks.cli_on_path=True`,
        `hooks.hook_scripts_present=True`, `hooks.foreign_hooks=[]`,
        `hooks.wrapped_count=0`, `hooks.next_steps=[]`
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Settings shadowed | user-level `~/.claude/settings.json` overrides repo-level | doctor reads BOTH and reports `shadowed_by_user=True` | doctor's `next_steps` print the override path + advice |
| Invalid prior JSON | malformed `.claude/settings.json` | install fails fast with `HOOKS_INVALID_JSON`; doesn't clobber | typed code + manual-repair pointer |
| Foreign-hook double-wrap | install runs twice and wraps an already-wrapped entry | the wrapped form carries `_wrapped_from`; detect_foreign_hooks SKIPS entries whose command already starts with `agency shell run --hook-wrap` | invariant test pins the no-double-wrap rule |
| Foreign hook can't be quoted | original command embeds a literal unescaped quote | `wrap_foreign_hook` returns None; install reports `HOOKS_FOREIGN_UNWRAPPABLE` and PRESERVES the original | typed code + manual-fix pointer; the foreign hook still runs unwrapped (no behavior loss) |
| Stale hooks block | the canonical patch version bumped, user has old block | `_version` field on the patch; doctor reports drift | re-run install (idempotent merge) |
| `agency` CLI missing at runtime | PATH change after install | dispatcher exits 0 silently (Spec 076 best-effort); doctor reports `cli_on_path=False` next session | `next_steps` carries the pipx install command |

## Interconnects

- **Spec 076** (unified-event-hook, SHIPPED) — Spec 280 IS the
  install + verification + foreign-hook composition layer on top of
  the existing dispatcher. It does NOT replace Spec 076; it makes
  sure the dispatcher actually fires in a fresh repo.
- **Spec 062** (SessionStart auto-pipx install, SHIPPED) — Spec 280's
  doctor checks whether 062 succeeded; when it didn't, the doctor
  surfaces the manual `pipx install` step.
- **Spec 064** (plugin-reference compliance, SHIPPED) — defined the
  current `hooks/hooks.json` shape that Spec 280 verifies.
- **Spec 073 / 075** (shell capability, SHIPPED) — the wrapping
  mechanism. Foreign hooks become `shell.run` Invocations under
  agency's umbrella; the existing filter/allowlist surface applies.
  May require extending `shell.run`'s allowlist to accept a
  `--hook-wrap` mode that runs the literal command bypassing the
  allowlist (because the user explicitly opted in by authoring the
  hook in their settings; the wrapper is for provenance, not
  sandboxing).
- **Spec 148** (slash-family + SessionStart Intent capture, Partial)
  — the SessionStart hook Spec 148 extends is the SAME dispatcher
  Spec 280 verifies. The two compose: Spec 148 owns the offer
  surface; Spec 280 owns the wiring verification.
- **Spec 170** (doctor deepening, Partial) — Spec 280 lands the
  `hooks` field that 170's deeper readiness surface needs.
- **Spec 175** (install-surface derived, draft) — when 175 ships,
  the canonical patch CAN be derived from the live registry +
  marketplace shape; Spec 280's `CANONICAL_SETTINGS_PATCH` becomes
  a derived constant rather than a hand-edited one.
- **Spec 195** (unified-hook event replay + BoundaryUse capture,
  draft) — Slice 1 of 280 ships the advisory routing hints;
  Slice 2 (or Spec 195) records the bypass as a `BoundaryUse` node
  so the dogfood loop sees the pattern.
- **Spec 229** (session-driver Slice 2, draft) — the cross-session
  handoff that consumes the Event chain Spec 280 ensures actually
  fires.
- **Spec 151** (Codes coverage) — supplies
  `HOOKS_FILE_UNWRITABLE` / `HOOKS_INVALID_JSON` /
  `HOOKS_FOREIGN_UNWRAPPABLE`.
- **Goal 2** (provenance moat) — direct: foreign-hook wrapping
  extends the moat to behavior the engine doesn't author.
- **Goal 5** (code-mode is the contract) — direct: the routing
  advice surfaces the verb path even when the AI bypasses MCP.
- **Goal 8** (harness-in-harness) — direct: agency composes with
  other plugins' hooks rather than replacing them.

## Sync vs async per event (the user-raised point)

Today `hooks/hooks.json` sets every event to `"async": true` EXCEPT
SessionStart. That is wrong for what the user actually wants:

| Event | Current | Should be | Why |
|---|---|---|---|
| **SessionStart** | sync | **sync** ✓ | the engine auto-install (Spec 062) must complete before any tool runs; an async install can race a `Bash("pytest")` and miss it. Already correct. |
| **PreToolUse** | async | **sync (for tools we route)** | to BLOCK a `git commit` and route to `branch.commit_smart` we need exit-non-zero authority; async hooks can't block. Slice 1 ships advisory-only (so async works), but the `async` flag should already flip to false because Slice 2 is around the corner and a stale async flag would mute the block. |
| **UserPromptSubmit** | async | **sync** | when present (Spec 176 / Spec 148), the hook injects intent context into the prompt; async would let the prompt reach the model before the injection lands. |
| **PostToolUse** | async | **async** ✓ | record-only — the tool already ran; speeding it up isn't worth the race. |
| **Stop / SessionEnd / SubagentStop** | async | **async** ✓ | cleanup + summary; non-blocking. |
| **PostToolUseFailure** (if added) | — | **async** | record-only. |

The async flag is part of `CANONICAL_SETTINGS_PATCH` so the install
side-effect can correct a stale flag without the user touching
`hooks.json` by hand. The flip is doctrine, not configuration.

**Foreign-hook wrap MUST PRESERVE the original `async` flag.** A foreign
hook that the user authored as sync was sync for a reason (it BLOCKS
the tool — e.g. an `audit-cmd.sh` that rejects unsafe commands).
Wrapping it as async would silently change semantics. Conversely, a
foreign async hook stays async (we don't want a slow side-effect to
become a blocking call). Invariant: `wrap_foreign_hook(entry).async ==
entry.async`.

## Open questions

1. **Block vs warn for Slice 1?** **Recommend**: warn-only.
   Blocking is Slice 2 once the bypass-rate baseline is established
   (Spec 058 WARN→error doctrine + Spec 054 drift pattern). Flipping
   to error before the baseline measures the cost of routing through
   verbs adds friction without measured benefit.
2. **Should foreign-hook wrapping bypass `shell.run`'s allowlist?**
   **Recommend**: yes, gated by an explicit `--hook-wrap` flag the
   wrap function passes. The user authored the foreign hook in their
   settings; the wrap is for provenance, not sandboxing. Without
   bypass, every wrap fails (the foreign command isn't in
   `_ALLOWED_TOOLS`).
3. **Detect hooks across BOTH `.claude/settings.json` AND
   `.claude/settings.local.json`?** **Recommend**: yes. The
   `.local.json` is git-ignored personal overrides; Spec 280
   detects + wraps foreign hooks in BOTH but only writes the
   canonical patch to the committed `.claude/settings.json`.
4. **Self-test command — separate verb or integrated into
   `agency_doctor`?** **Recommend**: separate `agency hook self-test`
   so doctor stays fast (the self-test runs the dispatcher with
   synthetic payloads — too slow for first-touch doctor). Doctor's
   `next_steps` points at the self-test when needed.
5. **What happens when the user UNINSTALLS the agency plugin?**
   **Recommend**: out of scope for Slice 1. Slice 5 ships
   `agency install --uninstall` that restores from `.bak` and
   unwraps foreign hooks.

## Slice plan

- **Slice 1 (this)** — pure `_hooks.py` library + install side-effect
  + doctor `hooks` field + dispatcher advisory routing. Foreign-hook
  wrap supported. Self-test stubbed (returns `{ok:True}` without
  actually invoking; full self-test is Slice 1.5).
- **Slice 1.5** — `agency hook self-test` actually runs each hook
  event with a synthetic JSON payload and verifies an Event node
  lands. Doctor integrates.
- **Slice 2** — flip the clearest routes (`git commit`, `git push`,
  raw `pytest`) to blocking (exit 2 with the routing advice). Gated
  by the bypass-rate baseline (Spec 195 BoundaryUse counts).
- **Slice 3** — MCP-aware suggestions: the dispatcher queries
  `mcp__agency__search` to derive routing hints from the live
  registry (so renames don't drift the hints).
- **Slice 4** — user-level fallback repair: doctor's
  `next_steps` can patch `~/.claude/settings.json` (not just
  project-level) when the repo block is shadowed.
- **Slice 5** — uninstall: `agency install --uninstall` reverses
  Slice 1's merge (restores from `.bak`; unwraps foreign hooks).
- **Slice 6** — Spec 047 cluster pre-amble integration: the
  SessionStart routing hint is the pre-amble for every walkable
  skill (Spec 047 assumes this).

## Followup — Implementation Status (Slice 1, 2026-06-12)

To be filled when Slice 1 ships.
