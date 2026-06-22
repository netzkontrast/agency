<!-- agency-note: design reference for Spec 332; intent:7509dac0 -->
# The frugal discipline — agency's minimal-code reflex (design reference)

> Agency's own design for the **frugal** core discipline (Spec 332). This is the
> canonical text the implementation (`agency/_frugal.py`) renders from — a
> redevelopment from first principles, not a port. Companion installer design:
> [`../../333-multi-agent-installer/reference/INSTALLER.md`](../../333-multi-agent-installer/reference/INSTALLER.md).

## 1. What it is

A *write-only-what-the-task-needs* reflex that holds on **every** action. Frugal
means **efficient, not careless**: the best code is the code never written, but a
guard is never the thing cut. It is **content** (the ladder + the safety floor +
intensity levels) embedded as a **core** cross-cutting concern — present at every
session start and stamped on every verb return — with a default level of **`full`**.

## 2. The ladder (canonical — `_frugal.py` renders this)

Before writing code, stop at the **first rung that holds**:

1. **Does this need to exist at all?** Speculative need = skip it, say so in one line. (YAGNI)
2. **Stdlib does it?** Use it.
3. **Native platform feature covers it?** `<input type="date">` over a picker lib; CSS over JS; a DB constraint over app code.
4. **Already-installed dependency solves it?** Use it. Never add a new one for what a few lines do.
5. **Can it be one line?** One line.
6. **Only then:** the minimum code that works.

The ladder is a reflex, not a research project. Two rungs work → take the higher
one and move on.

## 3. Rules

- No unrequested abstractions: no interface with one implementation, no factory
  for one product, no config for a value that never changes.
- No boilerplate / scaffolding "for later"; later can scaffold for itself.
- Deletion over addition; boring over clever; fewest files; shortest working diff.
- Complex request? Ship the frugal version **and** question it in the same
  response — never stall on a default you can take.
- Two stdlib options the same size → take the one correct on edge cases. Frugal
  means writing *less* code, not picking the flimsier algorithm.
- **Output:** code first, then ≤3 short lines — *what was skipped, when to add it*
  (`[code] → skipped: [X], add when [Y]`). If the explanation is longer than the
  code, delete the explanation. Explanation the user explicitly asked for is not
  debt — give it in full.

## 4. The safety floor (the Slice-4 gate invariants)

**Never** simplify away — these substrings must survive in every rendered/injected
form (the drift + gate test pins them):

- `input validation at trust boundaries`
- `error handling that prevents data loss`
- `security`
- `accessibility`
- anything the user explicitly asked to keep
- *"Frugal code without its check is unfinished"* — non-trivial logic (a branch, a
  loop, a parser, a money/security path) leaves **ONE runnable check** behind: an
  assert-based self-check or one small `test_*.py`. Trivial one-liners need none.

## 5. Levels & projections

| Level | Behaviour |
|---|---|
| `lite` | Build what's asked, name the leaner alternative in one line. |
| **`full`** | The ladder enforced; stdlib + native first; shortest diff. **Default.** |
| `ultra` | Deletion before addition; ship the one-liner and challenge the rest of the requirement in the same breath. |
| `off` | Disabled — nothing injected, nothing stamped. |

Only the level *label* changes the strictness/voice; the ladder + floor are
constant across `lite/full/ultra`. Two **projections**:
- **full render** — the whole ladder + floor (M1 session injection).
- **compact render** — one line + the floor clause, **≤ ~40 tokens** (M2 per-verb
  stamp), e.g. `full · YAGNI→stdlib→native→dep→1-line · floor: validate/secure/a11y never cut`.

## 6. The marker convention

Deliberate simplifications get a `# frugal:` comment that names the ceiling **and**
the upgrade path, so a shortcut reads as intent, not ignorance:

```python
# frugal: global lock; per-account locks if throughput matters
```

`develop`/`analyze` can later harvest these into a debt ledger (a follow-up verb).

## 7. Mechanism (how it embeds in core — Spec 332 M1 + M2)

| Concern | Implementation |
|---|---|
| **Level state** | Spec 334 `config_get("frugal.level")`: `AGENCY_FRUGAL_LEVEL` env → `.agency/config.yaml` → `full`. `frugal_level(level)` SET → `config_set` + a `FrugalLevel` node. |
| **M1 — session/prompt inject** | core `SessionStart` + `UserPromptSubmit` handlers (`register_hook_handler`, beside the assumption-guard) → `{inject: full render}`. `ultra` adds the prompt cadence. CLI lane = `agency hook`. |
| **M2 — per-verb stamp** | `ResponseEnvelope.prefix.frugal` = compact render (Spec 146, cache-stable). `off` omits it. |
| **Degrade** | any render failure → no inject, no stamp, verb still succeeds. |
| **Doctor** | `agency_doctor` reports the resolved `frugal.level` + source. |

**Two lanes (MCP + CLI parity):** hosts with lifecycle hooks get M1 live; no-hook
agents get the discipline from the Spec 333 `AGENTS.md`/rules file. Either way the
discipline is present every session.

## 8. Why core, not a capability

A discipline that must govern *every* verb can't be opt-in. Precedent: the
**assumption-guard already lives in core** and injects every prompt via the same
hook seam. This is a cross-cutting *discipline*, not a *domain* — so GOALS Goal 4
("no fixed domains in core") is intact; Goal 1 (token-efficient loops) is served
at the code-output layer.

## 9. Prior art

Minimal-code agent disciplines exist in the ecosystem; this is an **independent
redevelopment** — the ladder is general engineering wisdom, implemented as
agency's own core feature with agency-native mechanism (the M2 per-verb envelope
stamp has no external analogue; it exists because agency has a wire envelope).
