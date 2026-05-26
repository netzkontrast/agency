---
slug: vision-lessons
type: vision
status: ready
summary: Durable engineering knowledge for building and operating the plugin — jules orchestration safety (silent-fail recovery, respawn guard, dispatch as a critical section), engine registration discipline, the store singleton, and honest gates. Model-agnostic.
---

# Lessons — durable engineering knowledge

Hard-won, model-agnostic guidance. Apply when building the engine or operating
the `jules` capability (home domain `who`).

## Operating the jules capability (`who`)

- **`COMPLETED` is not success.** A jules session state of `COMPLETED` means
  "idle, awaiting input" — not "work done and pushed." A session can pause
  before pushing (a silent fail). After `who.poll` returns `COMPLETED`, run
  `who.verify` to confirm the branch exists on the remote before trusting it.
- **Recover, don't respawn.** When a session completed but no branch landed:
  probe it with one focused message (`retry`); if still nothing, extract the
  patch from the API and apply it via signed commits. The canon guard: **NEVER
  `respawn` jules if a patch already exists; DO respawn only if the patch is
  empty.** A needless respawn wastes a `Slot` and risks divergent output.
- **Dispatch is a critical section.** Parallel `fan_out` can duplicate-dispatch,
  and the second dispatch inherits the first's incomplete state. Guard
  `who.dispatch` so it cannot fire twice for the same task — the `DRIVES` edge
  to the when-task is the idempotency key.
- **Handoff passes context, not a baton.** A `who.handoff` MUST attach a
  `SharedContext` node so the receiving session inherits what the prior one
  knew; a bare baton loses the work.

## Building the engine

- **Names come from the deriver.** Every public name derives from
  `(domain, capability, verb)` (see VOCABULARY.md). When delegating work,
  cross-check a brief against the derivation rules — the deriver wins, not the
  brief.
- **FastMCP `add_tool` is strict.** It takes a `Tool` or callable and no
  `name=` kwarg, and rejects `**kwargs` wrapper functions. Bind tool name and
  function as closure defaults in the wrapper. Exercise the real boot path in
  tests — an empty-cwd fixture can hide a broken registration loop.
- **One store accessor.** A single `get_store()` singleton (rather than injected
  mocks) removes whole classes of test-setup bugs. It assumes a single-threaded
  process; revisit if a second concurrent consumer appears.
- **Keep gates honest.** A placeholder `when` gate that returns success
  unconditionally must say so in its prose. Never let task text overstate what a
  gate actually checks.
