---
slug: vision-example
type: vision
status: ready
summary: A worked spec walkthrough — "fix the failing auth test, via jules" — tracing one trip through intent + who/how/when/where. Shows the canonical verb frame, the who↔when DRIVES boundary, harness-in-harness handoff, and the silent-fail-recovery lesson. A SPEC walkthrough, NOT a shipped path.
---

# Worked example — "fix the failing auth test, via jules"

> **Status: specced — not built.** This is a walkthrough of how the v2.1 model
> composes, written to make the design concrete. It is NOT a shipped execution
> path. Names use the code-mode form (`domain.capability.verb()`); the MCP and
> skill forms derive identically.

The task: *fix the failing auth test*, delegated to the `jules` async-coding
agent. One trip through **why** + **who / how / when / where**.

## 0. Intent (why / what) — the human's root

```
why.capture(text="fix the failing auth test on main")
why.confirm(...)                       # → Intent node I1, pinned once
```

`I1` is now referenced by id everywhere; the text is never re-pasted (cache-
safe). Every node below carries a `SERVES_INTENT → I1` edge.

## 1. who.dispatch — open a session (dispatcher vs dispatchee)

```
S1 = who.jules.dispatch(role="jules", intent="I1")   # who.jules is the DISPATCHER; role is a PARAMETER
```

- `dispatch` is the **who** `open` verb. It creates a **Session** node `S1` and
  a per-hop **Dispatch** correlation node (so a later handoff can nest —
  harness-in-harness).
- `S1 —SERVES_INTENT→ I1`.

## 2. when.start + the DRIVES boundary

```
T1 = when.jules.start(task="fix-auth-test", phases=["investigate","patch","verify","pr"],
                      gate="tests-green")
where.link(S1, T1, rel="DRIVES")        # the who↔when join
```

- `start` is the **when** `open` verb. `T1` is the **Task** node owning the
  process: phases `investigate → patch → verify → pr`, with a hard gate
  `tests-green`.
- The **`DRIVES`** edge links the who-session `S1` to the when-task `T1` it
  advances. Session state lives in `who`; phase/gate state lives in `when`;
  **neither duplicates the other.**

## 3. how.jules.patch — the craft (open domain, frame-role tagged)

```
result = how.jules.patch(session="S1")  # frame role: this how-verb fills "move" for the craft
```

- `how` is OPEN: `patch` is a jules-specific craft verb, TAGGED with the frame
  role it fills. Discoverable via `how.jules.help`.

## 4. where.record + where.link — append-only memory

```
A1 = where.jules.record(kind="patch", produced_by="S1", task="T1")   # where `open`
where.jules.link(A1, T1, rel="PRODUCES")                             # where `move`
```

- `record` writes an **Artefact** node `A1` for the patch (bytes via a driver);
  `link` connects it. **Append-only** — nothing is overwritten.

## 5. who.poll / who.verify — COMPLETED ≠ done (the silent-fail lesson)

```
status = who.jules.poll(session="S1")     # who `read` → "COMPLETED"
ok     = who.jules.verify(session="S1")   # who `check` → branch on remote?
```

- A jules `COMPLETED` means "idle, awaiting input," NOT "pushed." `verify`
  confirms the branch exists on the remote.
- If `verify` fails but a patch already exists: `who.jules.retry(...)` to probe,
  then recover by applying the API patch. **NEVER `respawn`** while a patch
  exists (canon guard) — respawn only if the patch is empty.

## 6. when.advance — gate, then move the task

```
when.jules.check(task="T1", gate="tests-green")   # when `check` (gate)
when.jules.advance(task="T1", to="pr")            # when `move`
```

## 7. who.handoff — harness-in-harness (context, not a baton)

```
S2 = who.jules.handoff(from_="S1", role="codex", shared_context=SC1)  # who `move`
```

- `handoff` opens a nested session `S2` (a new actor, `codex`) under the same
  Dispatch correlation chain — **harness-in-harness**. A **SharedContext** node
  `SC1` ensures `S2` inherits what `S1` knew (context, not just a baton).

## 8. when.complete · who.release — close out

```
when.jules.complete(task="T1")    # when `close`
who.jules.release(session="S2")   # who `close`
```

- `complete` closes the **task**; `release` closes the **session**. The
  `where` graph retains the full append-only trail; `where.project()` will
  surface only ranked deltas of it, never the raw history.

## What this shows

- The **two-axis verb frame** in action: `open` (dispatch/start/record),
  `move` (advance/handoff/link), `close` (complete/release), `read`/`check`
  (poll/verify/gate).
- The **who ↔ when DRIVES boundary** — one join edge, zero duplicated state.
- **Harness-in-harness** via nested Dispatch + SharedContext on handoff.
- The **silent-fail-recovery** lesson encoded as `poll → verify → retry/recover`
  with the respawn guard.
- INTENT as the pinned root every node serves.
