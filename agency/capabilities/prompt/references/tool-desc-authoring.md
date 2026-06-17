<!-- agency-generated: no — authored guidance; the canonical rules for verb (tool) descriptions (Spec 306, aligned to Spec 023). -->
# Rules for writing a capability-verb description

> An instruction prompt for any agent authoring or optimizing a **verb
> docstring**. Scored by `prompt.evaluate(target="tool-desc")`. A verb
> description is a **functional** prompt: its job is correct **invocation** and
> cheap **discovery**, not persuasion — and not routing (that is the
> capability's job). Canon: `docs/vision/CAPABILITY-AUTHORING.md`
> §"verb docstring contract" (Spec 023). Sibling: `skilldoc-authoring.md`
> (the capability-level paragraph).

## What this is NOT — the lesson the dogfood sweep taught

A verb does **not** carry a "when to route here" sentence, and it does **not**
restate its purpose for selection. **Routing happens at the capability layer** —
`search` ranks on the first sentence, `recommend` / `route_framework` score the
registry, and the capability's SkillDoc carries the "When to use". Duplicating
that per verb burns context on every discovery call (GOALS #1, token economy)
and drifts from the one place that owns it (GOALS #5, code-mode is the contract).
So a verb description is **lean**: a brief + the wire shape.

## The one rule that governs the rest

**A function needs no Role — it needs the wire shape.** Never write
`You are a/an <role>` / `Act as …`. State what the verb does and what crosses the
wire. (Fires `role_padding`.)

## The grammar (Spec 023 — every marker has a runtime consumer)

```
<first sentence>   ≤ 120 chars, ONE clause, verb-first, role-tagged (act|transform|effect)
                   → parse_slices["brief"] → the FastMCP tool description → `search` (T1)
Inputs:  name (type) — meaning, one per user-facing arg          → standard depth (T2)
Returns: the wire shape — {field, …} on success; the error / null cases too  → (T2)
chain_next: the verb to call after this one, or (terminal)        → deep depth (T3)
```

## The rules

1. **First sentence ≤ 120 chars, single clause, verb-first, role-tagged.** It is
   the brief `search` shows — and a 521-char result is 130 tokens vs 86 for a
   one-sentence brief (Spec 023 measured −35% on every search call). Two clauses
   joined by `;` or an em-dash → split; the second clause goes in the body.
   (Fires `long_brief`.)
2. **`Inputs:` on one line** — `name (type) — meaning` per user-facing arg. The
   snippet renderer parses names for `call_tool` args. (Fires `missing_inputs`.)
3. **`Returns:` is the wire shape** — `{field, …}` on success, AND the error
   codes / null returns a caller must handle. The orchestrator learns the shape
   without executing. (Fires `missing_returns`.)
4. **`chain_next:`** — the verb to call next, or `(terminal)`. It's free and
   saves the orchestrator a guess. (Advisory `no_chain_next` — terminal verbs
   legitimately omit it.)
5. **No Role, no persuasion, no "when to route here."** Routing is the
   capability's job; the verb states mechanism + wire shape only.
6. **Document the wrap honestly.** If the verb returns `{result: <delta>}` on the
   wire, the `Returns:` line says so (CAPABILITY-AUTHORING.md §"the wrap").

## Self-check before you ship

```python
prompt.evaluate(prompt_body=<the verb docstring>, target="tool-desc")
# expect: status "passed", flags == []  (no role_padding / long_brief /
#         missing_inputs / missing_returns / no_chain_next)
```

Each capability ships a generated `references/verb-rules.md` that runs this check
across its own verbs. The repo-wide sweep `scripts/optimize-verb-docs` emits an
optimized candidate for every flagged verb — advisory, writes no source.
