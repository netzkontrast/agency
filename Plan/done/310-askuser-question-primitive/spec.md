---
spec_id: "310"
slug: askuser-question-primitive
status: draft
state: done
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
class ContextItem(TypedDict):
    # the caller passes context as a LIST of identified items, not a blob —
    # each is a derivation source an option can point back to.
    id: str               # stable handle: a Citation id (from ground, 312),
                          #   a ScopeBoundary id, or "ctx:<n>" for a passed signal
    text: str             # the evidence span itself

class AskOption(TypedDict):
    label: str            # short; the RECOMMENDED one suffixed " (Recommended)"
    description: str      # one line of WHY, derived from the evidence
    provenance: str       # REQUIRED — the ContextItem.id this option derives from
                          #   (the resolvable pointer the oracle checks; "" is illegal)

class AskPayload(TypedDict):
    question: str         # the well-formed question text
    header: str           # <= 12 chars (the AskUserQuestion column header)
    options: list[AskOption]   # 2..4 options, RECOMMENDED-first
    multiSelect: bool     # True only when the axes are independent

class AskResult(TypedDict):
    payload: AskPayload   # what the harness renders via the real AskUserQuestion tool
    question_id: str      # the recorded ClarificationQuestion node (the fold-back key)
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

**Derivation seam (Spec 147).** Turning the context items into options runs
through the Driver structured-output seam **behind the typed `AskPayload` shape**:
given the evidence items, the Driver returns candidate
`{label, description, provenance}` options. With no Driver, a **deterministic
fallback** projects one option per distinct `ContextItem` (label = a derived
summary, `provenance` = that item's `id`) — so the primitive is fully exercised
with zero LLM.

**The derivability oracle — a RESOLVABLE pointer, not token overlap (fixes the
spec-panel blocker).** The trivial check ("the option's words appear in the
context") passes on any shared stop-word and is no contract at all. Instead, the
oracle is **referential**: every `AskOption.provenance` MUST be the `id` of a
`ContextItem` that was passed in, AND the option's `description` must be entailed
by that *specific* item (the fallback derives it FROM that item, so entailment is
constructive; the Driver path is required to return a `provenance` that resolves).
`ask` **rejects** (raises `INVALID_ARGUMENT` / drops, per the caller's mode) any
option whose `provenance` is empty or does not resolve to a supplied item — so an
*invented* option (no backing item) cannot survive. The contract is thus a
**resolution check against the passed item set**, immune to incidental word
overlap.

**Record the node.** `ask` records a **`ClarificationQuestion`** node (Spec 307
ontology — `text`, `options`, `ambiguity_kind`); the `ambiguity_kind` (Spec 307
enum) is passed by the caller (`clarify` supplies the detected kind; `interview`
supplies the beat's kind mapped to a default). The `CLARIFIES` edge to the
Intent is **not** written here — that is the *caller's* job once an answer
exists (`clarify`, Spec 311), keeping `ask` read-only and reusable.

### The AskUser harness protocol — the testable seam (fixes the spec-panel blocker)

`ask` does not call `AskUserQuestion` itself (a verb cannot block on a human, and
the engine has no UI). The control-flow is a **two-phase, resolvable protocol** —
the keystone seam the 9 AskUser-consuming specs (309/311/318/323) share — defined
here as a typed interface, not prose in an unwritten reference doc:

1. **Emit.** `ask` records a `ClarificationQuestion` node in `pending` state and
   returns `AskResult{payload, question_id}`. `question_id` is the fold-back key.
2. **Render.** The *harness* (Claude Code / the CLI hook) renders `payload`
   through the real `AskUserQuestion` tool and obtains the user's selection(s).
   This is the only step that needs a human; it lives outside the engine (Goal 8).
3. **Fold.** The caller resolves the pending question via a shared
   `_base.fold_answer(question_id, answer)` helper (Spec 308): it updates the
   `ClarificationQuestion` to `answered` (storing the chosen `provenance`-bearing
   option) and writes the caller-appropriate edge — `CLARIFIES`→Intent for
   `clarify` (311), an `ElicitationTurn`/`ELICITS` for `interview` (309), a
   `ScopeBoundary`/`BOUNDS` for `scope` (318). `ask` itself never writes that edge
   (it stays read-only beyond the one node).

**Testable without a human.** The render step is injected behind a typed
`AnswerProvider` seam (mirroring the Spec 147 Driver seam): a test double returns
a canned selection keyed by `question_id`, so the full emit→fold round-trip is
exercised in the acceptance suite with **zero live AskUserQuestion call**. The
prose companion (`references/askuser-contract.md`, Spec 308) documents the seam;
the *contract* is this typed protocol + its tests, so it is falsifiable.

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **Option-count invariant:** for any `n_options`, `2 <= len(payload["options"]) <= 4`
  — computed against the returned payload across a range of inputs, never a
  pinned length; passing `n_options=9` clamps to `MAX_OPTIONS`.
- **Recommended-first:** `payload["options"][0]["label"]` ends with
  `" (Recommended)"` and **no other** option carries the suffix — asserted on the
  live payload, the relationship not a fixed string.
- **Derive-not-invent (the hard contract — referential, not overlap):** every
  option's `provenance` resolves to the `id` of a `ContextItem` that was passed
  in — assert `all(opt["provenance"] in {item["id"] for item in context})`. The
  **negative** is the load-bearing case: inject a Driver/fallback result carrying
  an option whose `provenance` is empty or points at an absent id, and assert
  `ask` rejects it (raises `INVALID_ARGUMENT` or drops it) — so a manufactured
  option provably cannot survive. This test must FAIL under a naive token-overlap
  oracle (an invented option reusing context words but with no resolvable
  `provenance` is caught), proving the oracle is referential.
- **Header budget:** `len(payload["header"]) <= MAX_HEADER_LEN` for arbitrary
  context — the bound is the named budget, computed, not snapshotted.
- **multiSelect gate:** `multi=False` yields `multiSelect == False`; `multi=True`
  on independent axes yields `True` — asserted as the function of the flag, not a
  hardcoded payload.
- **Read-only (Goal 2):** invoking `ask` records exactly one
  `ClarificationQuestion` node and **no** `CLARIFIES` edge / Intent mutation —
  graph node-count delta equals the single `ClarificationQuestion` plus the
  Invocation (the read-only invariant, computed from a live census).
- **Harness protocol round-trip (the seam is testable):** with an injected
  `AnswerProvider` test double, `ask` → render → `_base.fold_answer(question_id,
  answer)` transitions the `ClarificationQuestion` from `pending` to `answered`
  and the chosen option (with its `provenance`) is recorded — assert the
  state transition + the stored selection, with **no** live `AskUserQuestion`
  call. A fold against an unknown `question_id` raises (the key is load-bearing).

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
