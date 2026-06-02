# Anti-patterns — when NOT to dispatch even if signals say yes

The heuristic catches most cases. These are the rare ones where the
heuristic looks like it favours dispatch but you should override and
inline anyway.

## 1. Known-path lookup

If you can name the file and the symbol, just `Read` it. Subagents
have a setup cost (envelope tokens + cold cache). A targeted Read
beats a dispatched grep every time.

**Smell.** You're tempted to dispatch because the work is small but
"feels different" from the rest. It isn't. Inline it.

## 2. One-shot mutation

A single file edit is cheaper inline than dispatch-and-review. Mutations
without provenance trip Disqualifier 1 anyway, but even WITH a verb
that has provenance, a single edit doesn't earn the dispatch envelope.

**Threshold.** ≥ 3 coordinated edits with their own gate? Then maybe
dispatch. < 3? Inline.

## 3. Loop-body dispatch

Dispatching INSIDE a loop is N× overhead. Hoist the dispatch OUT —
do the work once, fan out the N items as siblings (S4 fires; driver
picks `local`).

**Wrong.**
```python
for item in items:
    delegate.fan_out(driver="local", driver_verb="analyze", items=[item])
```

**Right.**
```python
delegate.fan_out(driver="local", driver_verb="analyze", items=items, quota=8)
```

## 4. Recursive dispatch (subagent dispatching another subagent)

Loop-detection middleware (planned) will guard this; for now, guard
manually. A dispatched subagent should NEVER dispatch its own subagent
— it should inline its sub-work or return for the parent to handle.

**Rationale.** Each layer of dispatch adds ~700 tokens of envelope and
a cold-cache start. Two-deep dispatch loses every cost battle to a
single inline pass.

## 5. Tasks the user is waiting on

The user is waiting on the parent context's reply. Don't punt them
into a subagent's queue, especially for Jules (async + wall-clock
latency). The interactive-flow tax beats the dispatch savings.

**Smell.** You're about to write "let me dispatch this to Jules"
in response to a direct user question. STOP. Inline.

## Counter-anti-pattern: don't OVER-inline either

The mirror failure: inlining everything because "dispatch feels
heavy". Heavy is precisely what dispatch is for. When the heuristic
says dispatch (signals fired, no disqualifier hit), trust it.

**Smell.** You're about to read 12 unfamiliar files into the parent
context "to be sure". That's S2 firing. Dispatch.
