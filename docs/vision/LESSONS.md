---
slug: vision-lessons
type: vision
status: ready
summary: Durable engineering knowledge for building and operating the plugin — jules/agent orchestration safety (silent-fail recovery, respawn guard, dispatch as a critical section), engine registration discipline, the store singleton, and honest gates. Model-agnostic. Aligned to the v4 four-concept vocabulary.
---

# Lessons — durable engineering knowledge

Hard-won, model-agnostic guidance. Apply when building the Engine or operating an
agent capability (an agent is a Lifecycle parameterization). Vocabulary aligned
to v4 (Intent / Capability / Lifecycle / Memory).

## Operating an agent capability (e.g. `jules`)

- **`COMPLETED` is not success.** An agent Lifecycle state of `COMPLETED` means
  "idle, awaiting input" — not "work done and pushed." A session can pause before
  pushing (a silent fail). After the Lifecycle `read` returns `COMPLETED`, run the
  inserted `verify` step (the parameterization difference) to confirm the branch
  exists on the remote before trusting it. **Proven** in
  the `agency/` package.
- **Recover, don't respawn.** When a session completed but no branch landed:
  probe it with one focused message (`retry`); if still nothing, extract the patch
  from the API and apply it via signed commits. The canon guard: **NEVER
  `respawn` if a patch already exists; DO respawn only if the patch is empty.** A
  needless respawn wastes a `Slot` and risks divergent output.
- **Dispatch is a critical section.** Parallel `fan_out` can duplicate-dispatch,
  and the second dispatch inherits the first's incomplete state. Guard the
  Lifecycle `open` so it cannot fire twice for the same Intent/task — the
  `DISPATCHED_TO` / `SERVES` edges are the idempotency key.
- **Handoff passes context, not a baton.** A handoff MUST attach the prior
  session's context so the receiving session inherits what the prior one knew; a
  bare baton loses the work.

## Building the Engine

- **Names come from structure.** Every public name derives from
  `<concept>_<capability>_<verb>` (see VOCABULARY.md) — underscores, ≤64, no dots;
  the client injects `mcp__`. When delegating work, cross-check a brief against
  the derivation rules — the deriver wins, not the brief.
- **FastMCP tool registration is strict.** Bind tool name and function as closure
  defaults in the wrapper rather than passing `**kwargs`. Exercise the real boot
  path in tests — an empty-cwd fixture can hide a broken registration loop. The
  seed's `engine.py` registers real `@mcp.tool` functions and is exercised by a
  real FastMCP `Client`.
- **One store accessor / one graph.** A single graph (Memory) removes whole
  classes of dual-store drift bugs — there is no cache to re-sync. The engine runs a
  single thread-safe GraphQLite connection; revisit if a second concurrent
  consumer appears.
- **Keep gates honest.** A placeholder gate that returns success unconditionally
  must say so in its prose. Never let step text overstate what a gate actually
  checks. A gate that needs a human is an `elicit` step recorded as a `Gate`.
