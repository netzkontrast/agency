---
slug: vision-lessons
type: vision
status: ready
summary: Durable engineering knowledge for building and operating the plugin — Jules orchestration safety, dispatch as a critical section, deriver-path authority, FastMCP registration, store singleton, honest gates.
---

# Lessons — durable engineering knowledge

Hard-won, model-agnostic guidance. Apply when building the engine or operating
the `jules` capability.

## Operating the jules capability

- **`COMPLETED` is not success.** A Jules session state of `COMPLETED` means
  "idle, awaiting input" — not "work done and pushed." A session can pause
  before pushing (a silent fail). **Always verify the branch exists on the
  remote** before trusting completion.
- **Recover, don't re-dispatch.** When a session completed but no branch
  landed: probe it with one focused message; if still nothing, extract the
  patch from the API and apply it via signed commits. Never re-dispatch a fresh
  session for the same work — the patch already exists in the API, and a
  respawn wastes a slot and risks divergent output.
- **Dispatch is a critical section.** Parallel fan-out can duplicate-dispatch,
  and the second dispatch inherits the first's incomplete state. Guard dispatch
  so it cannot fire twice for the same task.

## Building the engine

- **The deriver's paths are canonical.** Names and file locations come from the
  deriver: handlers at `<domain>/<capability>/handlers/<export>.py`, skills at
  `<domain>/<capability>/skills/<export>/SKILL.md`. When delegating work,
  cross-check a brief against the deriver — the deriver wins, not the brief.
- **FastMCP `add_tool` is strict.** It takes a `Tool` or callable and no `name=`
  kwarg, and rejects `**kwargs` wrapper functions. Bind tool name and function
  as closure defaults in the wrapper. Exercise the real boot path in tests — an
  empty-cwd fixture can hide a broken registration loop.
- **One store accessor.** A single `get_store()` singleton (rather than
  injected mocks) removes whole classes of test-setup bugs. It assumes a
  single-threaded process; revisit if a second concurrent consumer appears.
- **Keep gates honest.** A placeholder gate that returns success
  unconditionally must say so in its prose. Never let phase text overstate what
  a gate actually checks.
