---
spec_id: "310"
slug: askuser-question-primitive
status: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [1, 2]
depends_on: ["147", "307", "308"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 310 — AskUser well-formed-question primitive (`discover.ask`)

> Child of the intent-pillar deep program (Spec 307), the **guided-exploration**
> layer. This is the single reusable AskUser primitive that `interview` (309),
> `clarify` (311), and `scope` (318) all compose — the one place the
> well-formed-question rules live.

## Why

**The gap (Spec 307 §coverage matrix).** Three clusters need to ask the user a
question: `interview` (a beat), `clarify` (a targeted ambiguity probe), `scope`
(an in-/out boundary). If each hand-rolls its own `AskUserQuestion` payload, the
well-formed-question rules — option count, recommended-first, `multiSelect` only
on independent axes, header length — drift across three call sites. Spec 307
§coherence rule 2 makes the contract explicit; this spec is **where that
contract is enforced once**.

**Why a primitive (token economy, Goal 1).** Spec 307 §thesis: a sharp AskUser
question **collapses N research turns into one user interaction**. Instead of the
agent spending a research budget guessing what the user meant, it presents 2–4
*derived* options and the user picks. One well-formed question is worth a
fan-out — but only if it is *well-formed*: bad options waste the interaction and
push the agent back into guessing. Centralizing the construction is what makes
the economy real.

**The hard contract — derive, never invent (CLAUDE.md derivability audit,
Spec 307 rule 2).** The options are **DERIVED from the supplied context/evidence**
— never invented by the verb. Authored options that duplicate no source are
drift waiting to happen; worse, an invented option asks the user to choose
between hallucinations. `ask` takes the evidence in and projects options out; it
refuses to manufacture an option the context does not support.

**Doctrine.** Read-only (Spec 307 rule 3) — `ask` is `role="transform"`: it
builds and returns a payload and records a `ClarificationQuestion` node, but it
does **not** mutate the Intent (the *caller* folds the answer back). The
provenance value (Goal 2) is that every question the engine ever asked is a graph
node with its options and ambiguity kind — the discovery is replayable down to
the questions, not just the answers.

## Design

**Cluster module:** `agency/capabilities/discover/clusters/ask.py`
(`AskCluster` mixin; shared helpers from `clusters/_base.py`).

**Verb:** `discover.ask(context: str, n_options: int = 3, multi: bool = False)`
— `role="transform"` (READ-ONLY beyond the one `ClarificationQuestion` node it
records; no Intent mutation).

It **BUILDS ONE** `AskUserQuestion`-shaped payload for the harness to render:

```python
class AskOption(TypedDict):
    label: str            # short; the RECOMMENDED one suffixed " (Recommended)"
    description: str      # one line of WHY, derived from the evidence

class AskPayload(TypedDict):
    question: str         # the well-formed question text
    header: str           # <= 12 chars (the AskUserQuestion column header)
    options: list[AskOption]   # 2..4 options, RECOMMENDED-first
    multiSelect: bool     # True only when the axes are independent

class AskResult(TypedDict):
    payload: AskPayload   # what the harness renders via the real AskUserQuestion tool
    question_id: str      # the recorded ClarificationQuestion node
```

**The well-formed-question rules (enforced here, once):**

- **Option count 2–4.** `n_options` is clamped to `[2, 4]`; fewer than 2 is not a
  choice, more than 4 is a survey. A documented, tunable budget (CLAUDE.md #8) —
  named constants `MIN_OPTIONS=2`, `MAX_OPTIONS=4`, not a frozen snapshot.
- **Recommended-first.** Options are ordered with the recommended option first,
  its `label` suffixed `" (Recommended)"`. The recommendation is **derived** from
  the evidence's strongest signal, never a default index.
- **multiSelect only for independent axes.** `multi=True` sets `multiSelect`
  only when the options are independent dimensions (pick several) rather than a
  single mutually-exclusive choice; the primitive is the one gate on this rule.
- **Header ≤ 12 chars.** The column header is truncated/derived to ≤ 12 chars
  (an `AskUserQuestion` constraint) — a named budget, not a magic number.

**Derivation seam (Spec 147).** Turning `context` into options runs through the
Driver structured-output seam **behind the typed `AskPayload` shape**: given the
evidence, the Driver returns candidate `{label, description}` options grounded in
that evidence. With no Driver, a **deterministic fallback** extracts options from
the context's structured signals (e.g. the distinct values/bullets the caller
passed) — so the primitive is fully exercised with zero LLM. Either way the
verb **rejects** an option whose `description` is not traceable to the supplied
`context` (the derivability contract is a runtime check, not a comment).

**Record the node.** `ask` records a **`ClarificationQuestion`** node (Spec 307
ontology — `text`, `options`, `ambiguity_kind`); the `ambiguity_kind` (Spec 307
enum) is passed by the caller (`clarify` supplies the detected kind; `interview`
supplies the beat's kind mapped to a default). The `CLARIFIES` edge to the
Intent is **not** written here — that is the *caller's* job once an answer
exists (`clarify`, Spec 311), keeping `ask` read-only and reusable.

**Return, don't render.** `ask` returns the payload for the **harness** to render
via the real `AskUserQuestion` tool (Goal 8 — the human is in the loop); the
answer is folded back by the caller. `ask` never blocks on a user; it is a pure
payload builder + recorder.

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **Option-count invariant:** for any `n_options`, `2 <= len(payload["options"]) <= 4`
  — computed against the returned payload across a range of inputs, never a
  pinned length; passing `n_options=9` clamps to `MAX_OPTIONS`.
- **Recommended-first:** `payload["options"][0]["label"]` ends with
  `" (Recommended)"` and **no other** option carries the suffix — asserted on the
  live payload, the relationship not a fixed string.
- **Derive-not-invent (the hard contract):** every option's `description` is
  traceable to a token/signal present in the supplied `context` — assert the
  overlap predicate holds for **all** options; an option with no support is
  rejected (raises / is dropped), proving the verb cannot manufacture options.
- **Header budget:** `len(payload["header"]) <= MAX_HEADER_LEN` for arbitrary
  context — the bound is the named budget, computed, not snapshotted.
- **multiSelect gate:** `multi=False` yields `multiSelect == False`; `multi=True`
  on independent axes yields `True` — asserted as the function of the flag, not a
  hardcoded payload.
- **Read-only (Goal 2):** invoking `ask` records exactly one
  `ClarificationQuestion` node and **no** `CLARIFIES` edge / Intent mutation —
  graph node-count delta equals the single `ClarificationQuestion` plus the
  Invocation (the read-only invariant, computed from a live census).

## Acceptance

Any discovery cluster that needs to ask the user a question calls
`discover.ask(context, …)` and gets back a **well-formed** `AskUserQuestion`
payload — 2–4 options, recommended-first, header ≤ 12 chars, `multiSelect` only
where the axes are independent, **every option derived from the supplied
evidence** — plus a recorded `ClarificationQuestion` node. The well-formed-rules
live in exactly one place, and one sharp question collapses a research fan-out
(Goal 1).

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** The reusable AskUser primitive; **Slice-1-typed-shape-first**
  — land `AskPayload` / `AskOption` / `AskResult` as the typed contract with the
  **deterministic option-derivation fallback** wired and tested (option-count
  clamp, recommended-first, header budget, derivability check all enforced on the
  fallback path), and the **LLM option-generation Driver seam (Spec 147) behind
  the typed shape** (the harness renders via the real `AskUserQuestion` tool; the
  caller folds the answer). No live LLM in the acceptance suite.
- **Next step:** build immediately after 308 (scaffold) and before 309 —
  `interview` (309), `clarify` (311), and `scope` (318) all compose this primitive,
  so it is the lowest brick in the guided-exploration layer.
