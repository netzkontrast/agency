# Frugal — the minimal-code discipline

<!-- doc-source: agency/_frugal.py agency/capabilities/frugal/_main.py Plan/332-frugal-core-discipline/spec.md Plan/348-frugal-capability-port/spec.md -->
<!-- doc-hash: 3f3553821a5761bf -->

> **Lazy means efficient, not careless. The best code is the code never written.**

Frugal is agency's always-on minimal-code reflex — a redevelopment of the
upstream MIT [ponytail](https://github.com/DietrichGebert/ponytail) skill as a
native discipline (Spec 332) and a first-class capability (Spec 348). It channels
a senior dev who has seen every over-engineered codebase: question whether the
task needs to exist at all, reach for the stdlib before custom code, a native
platform feature before a dependency, one line before fifty.

## Before / after

You ask for a date picker. A typical agent installs a date-picker library, writes
a wrapper component, adds a stylesheet, and opens a discussion about timezones.
With frugal:

```html
<!-- frugal: browser has one -->
<input type="date">
```

A date picker drops from ~400 lines to one. The cut is biggest where a real
over-build trap exists and near zero on code that is already minimal — see
`agency/capabilities/frugal/data/benchmark.json` for the published medians
(`frugal.gain` renders them).

## The ladder

Stop at the **first rung that holds**:

1. **Does this need to exist at all?** (YAGNI) Speculative need → skip it, say so in one line.
2. **Stdlib does it?** Use it.
3. **Native platform feature covers it?** `<input type="date">` over a picker lib, CSS over JS, a DB constraint over app code.
4. **Already-installed dependency solves it?** Use it — never add a new one for what a few lines do.
5. **Can it be one line?** One line.
6. **Only then:** the minimum code that works.

The ladder is a reflex, not a research project — two rungs work, take the higher
and move on.

## The safety floor — never simplified away

Frugal is lazy, not negligent. These are never on the chopping block (the
`safety_floor_intact` gate pins them at every level bar `off`):

- input validation at trust boundaries
- error handling that prevents data loss
- security measures
- accessibility basics
- anything explicitly requested

*Frugal code without its check is unfinished* — non-trivial logic leaves ONE
runnable check behind. Mark a deliberate shortcut with a `# frugal:` comment
naming the ceiling + upgrade path (`# frugal: global lock, per-account if
throughput matters`) so `frugal.debt` can surface it later.

## Levels

The active level resolves env `AGENCY_FRUGAL_LEVEL` → `.agency/config.yaml`
(`frugal.level`) → `full`. Switch with `frugal.set_level(level)`.

| Level | What changes |
|---|---|
| **lite** | Build what's asked; name the leaner alternative in one line — you pick. |
| **full** (default) | The ladder enforced; stdlib + native first; shortest diff, shortest explanation. |
| **ultra** | YAGNI extremist: deletion before addition; ship the one-liner and challenge the rest in the same breath. |
| **off** | Discipline injection silent (the safety floor invariant still holds). |

## How it reaches you (always-on)

- **SessionStart inject** — the full discipline lands once per session (deduped over
  startup/resume/compact via the Spec 349a event bus). Detail is tunable:
  `frugal.session_inject = off | discipline | full`.
- **Per-verb stamp** — every capability verb's envelope carries the compact
  one-line discipline (Spec 332 M2).
- **First-use hint** — the first time you reach for `Bash`/`Write`/`Edit` in a
  session, a one-line frugal nudge rides the PreToolUse hook (once per tool).

## The capability verbs

The discipline above is single-sourced in `agency/_frugal.py`; the `frugal`
capability makes it actionable **and queryable** (every run records provenance):

| verb | use |
|---|---|
| `frugal.level` / `frugal.set_level(level)` | read / switch the active level |
| `frugal.instructions(level)` | pull the ruleset for a host with no always-on hook (the ponytail-MCP port) |
| `frugal.review(scope="diff"\|"repo")` | flag over-engineering; records `FrugalFinding` nodes |
| `frugal.debt(paths)` | harvest `frugal:` shortcut markers into a queryable `DebtMarker` ledger |
| `frugal.gain` | the published benchmark scoreboard + the live debt count |
| `frugal.help` | the full reference card |

The heavy how-to travels on demand: `develop.reference("frugal")`.

## See also

- [`docs/guide/capabilities.md`](capabilities.md) — the generated verb reference (frugal section).
- `Plan/332-frugal-core-discipline/spec.md` · `Plan/348-frugal-capability-port/spec.md` — the design.
- `.claude/skills/ponytail/SKILL.md` — the upstream reference pointer.
