---
slug: vision-example
type: vision
status: ready
summary: A worked walkthrough — "fix the failing auth test, via jules" — tracing one trip through Intent + Capability + Lifecycle + Memory. Shows the verb frame, the agent-as-Lifecycle-parameterization (COMPLETED != done), the gate-as-elicit step, code-mode tool-chaining, and cross-concern provenance in one traversal. NOW EXECUTABLE in seed/.
---

# Worked example — "fix the failing auth test, via jules"

> **Status: now executable.** This walkthrough is no longer spec-only — its
> shape runs in [`seed/`](../../seed/README.md) (`run_scenario` +
> `test_codemode_chaining_is_an_executable_graph` +
> `test_gate_elicits_human_in_flow`, 6/6 green on `graphqlite` + `fastmcp`).
> Names below use the seed's verbs; the MCP tool form is
> `<concept>_<capability>_<verb>`.

The task: *fix the failing auth test*, delegated to the `jules` async-coding
agent. One trip through **Intent + Capability + Lifecycle + Memory**.

## 0. Intent — the human's root (why/what merged)

```python
iid = intent.capture(purpose="ship green CI",
                     deliverable="auth test passes",
                     acceptance="tests green")
intent.confirm(iid)                       # confirmed in place; SERVES edges stay stable
```

`iid` is referenced by id everywhere; the text is never re-pasted (cache-safe).
Every node below carries a `SERVES → iid` edge. If the *what* changes while the
*why* holds, `intent.amend(iid, deliverable=...)` is a bi-temporal supersede (the
old version is still reconstructable `as_of`).

## 1. Lifecycle.open — an agent is a Lifecycle parameterization

```python
lc = lifecycle.open(iid, agent="jules")   # Lifecycle SERVES iid; DISPATCHED_TO agent:jules
```

`open` creates a Lifecycle node in state `working`, `SERVES` the Intent, and is
`DISPATCHED_TO` an `Agent` node. The agent is **not** a separate concept — this
Lifecycle is parameterized to insert a `verify` step because `COMPLETED ≠ done`.

## 2. Capability steps — the craft (role-tagged), chained in code-mode

```python
# a stateless transform: pick the line with the most syllables
scored = [(syllables.count(text=ln), ln) for ln in lines]   # role: transform
best = max(scored)[1]
# feed the winner into the agent capability (role: act)
p = jules.patch(spec=best, agent_id="agent:jules", pushed=True)   # PRODUCES an Artefact, PERFORMED_BY the agent
```

Run inside one `execute(code)` block, these are **4 in-sandbox calls returning
ONE small delta** (token-efficient). Each call records an Invocation that `SERVES`
the Intent — so the executable chain mirrors into the provenance graph.

## 3. Gate — askuser-in-the-flow via `elicit`

```python
res = await ctx.elicit("Approve release?", response_type=["approve", "reject"])
# pauses the Lifecycle at input-required; the answer resumes it
```

The human's `approve` is recorded as a `human-confirm` `Gate` node, `PASSED` by
the Lifecycle. "askuser" is just one node in the chain.

## 4. COMPLETED ≠ done — the silent-fail lesson

```python
paused = jules.patch(spec=..., pushed=False)   # status: COMPLETED, branch_pushed: False
jules.verify(branch_pushed=paused["branch_pushed"])  # -> {"done": False}
```

A jules `COMPLETED` means "idle, awaiting input," NOT "pushed." The inserted
`verify` step confirms a real branch before trusting it. Canon guard: **never
`respawn` while a patch exists; respawn only if the patch is empty.**

## 5. Lifecycle.move / complete — gate then close

```python
lifecycle.move(lc, gate="tests-green", ok=True)  # records a PASSED Gate, advances
lifecycle.complete(lc)                            # -> "completed"
```

## 6. The moat — cross-concern provenance in ONE traversal

```python
prov = memory.provenance(iid)
# {
#   "serves":    [the syllables transform, the jules patch, ...],   # every action SERVES iid
#   "agents":    [agent:jules],                                     # who PERFORMED_BY it
#   "artefacts": [the patch],                                       # what it PRODUCES
#   "gates":     [tests-green, human-confirm],                      # the gates it PASSED
# }
```

This is a **single graph traversal** from the Intent — not a join across four
systems. **This is the moat**, and the seed answers it end to end.

## What this shows

- The **verb frame** in action: Intent `capture/confirm/amend`; Lifecycle
  `open/move/close` + `read/check`; Memory `record/link` + `provenance`.
- **An agent IS a Lifecycle parameterization** — the inserted `verify`,
  `COMPLETED ≠ done`.
- **Gate = `elicit`** — human-in-the-flow as one atomic, token-tiny step.
- **Code-mode tool-chaining = an executable graph** mirrored into provenance.
- **Cross-concern provenance in one traversal** — the moat.
