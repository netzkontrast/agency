---
spec_id: "326"
slug: ponytail-port
status: draft
last_updated: 2026-06-19
owner: "@agency"
vision_goals: [1, 3, 4]
depends_on: ["076", "146", "280", "292", "295"]
domain: core
wave: core-discipline
---

# Spec 326 — Core-embedded minimal-code discipline ("ponytail-in-core")

> Port the third-party **ponytail** discipline (DietrichGebert/ponytail, MIT)
> into agency **as a core cross-cutting concern — NOT a capability**. The
> minimal-code ladder + the non-negotiable safety floor become **core engine
> state** (active level, **default `full`**) that governs **every pillar and
> every verb**: injected at every session start / prompt **and** stamped into
> **every verb's response-envelope prefix** (cache-stable, Spec 146). This is
> GOALS.md Goal 1 (token-efficient agentic loops) expressed at the *code-output*
> layer, present uniformly across every agent surface (Goal 3).
>
> **★ Supersedes the v1 design (capability folder).** The 2026-06-19 user
> directive moved this OUT of `agency/capabilities/ponytail/` and INTO the core,
> so every verb is governed by default rather than an opt-in capability. The
> sibling **Spec 327** carries the multi-agent self-installer split out of this
> spec. Provenance: `intent:7509dac0`; pivot `reflection:fe553a2e`; vendored
> source under [`reference/`](reference/).

## Why (evidence + doctrine)

Agency has no *coding* discipline that holds on every action — nothing that stops
an agent over-building a 404-line date-picker when `<input type="date">` is the
answer. Ponytail is exactly that, and it is **measured**: on a headless agent
editing a real FastAPI+React repo (Haiku 4.5, n=4) it cut **−54% LOC, −22%
tokens, −20% cost, −27% time at 100% safety** — the only arm to cut every metric
without dropping a guard
([`reference/benchmarks/results/2026-06-18-agentic.md`](reference/benchmarks/results/2026-06-18-agentic.md)).
That is Goal 1 at the code-output layer, complementing code-mode at the tool-call
layer.

**Why core, not a capability (the explicit Goal-4 trade-off).** GOALS.md lists
"fixed *domains* in the core" as a non-goal — but this is a **cross-cutting
discipline, not a domain**, and it has direct precedent: the **assumption-guard
already lives in core and injects every prompt** (the `[agency] AVOID
ASSUMPTIONS` line) via the same hook seam. A discipline that must govern *every*
verb cannot be opt-in; making it core is what "present and known for each new
agent session, with every verb" *requires*. The open-set capability invariant
(Goal 4) is untouched — no domain enters the core; one engine-level discipline
does, exactly like the assumption-guard.

## The discipline (single source of truth)

One canonical constant in core (`agency/_discipline.py`) — everything else
derives from it (the injected text, the envelope stamp, the per-agent rules
files of Spec 327). No second copy to drift (the rule ponytail enforces upstream
with `check-rule-copies.js`).

1. **The ladder** — before writing code, stop at the first rung that holds:
   `1. Does this need to exist? (YAGNI) → 2. stdlib → 3. native platform feature
   → 4. installed dependency → 5. one line → 6. the minimum that works.`
2. **The safety floor (non-negotiable)** — *lazy, not negligent*: trust-boundary
   validation, data-loss handling, security, and accessibility are **never**
   cut. Ported as a **first-class, tested clause**, not prose.
3. **Levels** — `lite / full / ultra / off`, scaling how strict/loud the
   injected text is (`off` → nothing injected, nothing stamped).

## Design — core embedding (mechanism **M1 + M2**)

Core engine state: `engine.discipline_level` (default **`full`**; resolution
order `PONYTAIL_DEFAULT_MODE` env → `.agency` config → `full`). A change records
a `DisciplineLevel` provenance node so the active posture is queryable (Goal 2).

### M1 — Session / prompt injection (governs the agent's coding)

Register **core** `SessionStart` and `UserPromptSubmit` hook handlers
(`engine.register_hook_handler`, alongside the assumption-guard) that return
`{"inject": <ladder@level + safety floor>}`. `cli.py hook` already prints
`inject` to stdout for Claude Code to fold into the prompt — and the same path is
the CLI lane (`python -m agency.cli hook`). So a no-MCP agent that runs the hook
script is covered; a pure no-hook agent is covered by Spec 327's `AGENTS.md`.
*(`ultra` also fires on `UserPromptSubmit`; `full` on `SessionStart`; `off`
injects nothing.)*

### M2 — Per-verb envelope stamp ("with every verb there is")

`agency/_envelope.py`'s `ResponseEnvelope.prefix` (Spec 146) gains a
`discipline` key carrying the ladder@level + safety floor. Because it lives in
the **prefix** (the byte-stable, cache-controlled half), it is present on
**every verb's return** yet costs ~nothing on a cache hit and never churns the
cache. `off` omits the key. This is the literal "every pillar/verb uses it":
the envelope is built for every verb, so the discipline rides every response —
without editing a single pillar's code.

### "Every pillar directly uses it" — structurally, not per-pillar

The discipline is consumed at exactly two choke points that *all* verbs pass
through — the **envelope builder** (every return) and the **hook layer** (every
session/prompt). No per-capability edits; adding a pillar inherits the discipline
for free. That is the core-embed payoff.

### Level control (core, not a capability verb)

A substrate tool `discipline_level(level)` (+ CLI `agency discipline <level>`)
reads/sets `engine.discipline_level`. Substrate, not a `capability_*_*` verb —
it configures the engine, it doesn't SERVE an intent (same class as
`agency_welcome` / `hook_event`).

## Slices (TDD — Gherkin acceptance is the contract; behaviour, not internals)

1. **Core discipline module + state.** `_discipline.py` (the canonical ladder +
   safety floor + per-level rendering) and `engine.discipline_level` (default
   `full`, env/config resolution) + the `discipline_level` substrate tool.
   *Acceptance:* default level is `full`; `off`/`lite`/`ultra` resolve; the
   safety-floor clause is always in the rendered text; level change records a
   `DisciplineLevel` node.
2. **M2 — envelope stamp.** `ResponseEnvelope.prefix.discipline` on every verb
   return, omitted at `off`. *Acceptance:* an arbitrary verb's wire return
   carries the discipline at `full`; none at `off`; the prefix stays byte-stable
   across calls (cache invariant, Spec 146).
3. **M1 — session/prompt injection.** Core `SessionStart`/`UserPromptSubmit`
   handlers. *Acceptance:* a `SessionStart` `hook_event` returns an `inject`
   containing the ladder at the active level (empty at `off`) — proving presence
   on the MCP-hook and CLI lanes.
4. **Safety-floor gate.** A test + a `gate`-recordable predicate asserting the
   rendered/injected discipline NEVER omits validation/security/accessibility,
   at any level except `off`. *Acceptance:* the gate fails if the floor clause is
   stripped.
5. **Doctor + install wiring.** `agency_doctor` reports `discipline_level`;
   `install` emits the core handlers so a fresh setup is governed with zero
   manual steps. *Acceptance:* fresh install → doctor reports `full`.

## Acceptance criteria (the contract)

- C1 — Default `full`: every verb return carries the discipline and every new
  session is injected with it, with **no opt-in** — core, not a capability.
- C2 — The safety floor is a first-class, tested clause that no level (bar `off`)
  can strip.
- C3 — Cache-safe: the envelope stamp lives in the byte-stable prefix; the Spec
  146 cache invariant still holds.
- C4 — Single source of truth in `_discipline.py`; Spec 327's per-agent files and
  both injection paths derive from it (drift-gated).
- C5 — `off` fully disables (no inject, no stamp); `lite/full/ultra` scale the
  text. Wire contract (search/get_schema/execute) unchanged.

## Open questions

- **Q1** — `ultra` firing on `UserPromptSubmit` (every prompt) vs SessionStart
  only: confirm the per-level injection cadence. *Rec: SessionStart for all; add
  UserPromptSubmit at `ultra`.*
- **Q2** — Should the envelope `discipline` stamp be the FULL ladder or a
  one-line pointer (`discipline: full — see SessionStart`) to save prefix tokens?
  *Rec: a compact one-liner in the per-verb prefix; the full ladder only in the
  session injection* — keeps the cache prefix small.

## Followup — Implementation Status (2026-06-19)

**Verdict: Not started** (design redrafted for core-embed; awaiting gate approval).

- **Done:** v1 capability design superseded per user directive; agency-thinking
  pivot pass (`reflection:fe553a2e`); M1+M2 mechanism chosen and grounded against
  live code (`register_hook_handler`/`dispatch_hook`/`_envelope.ResponseEnvelope`/
  `cli.py hook`); this rewrite.
- **Still:** human gate approval, then Slice 1.
- **Blocker / Next step:** confirm Q1/Q2, then build Slice 1 under TDD. Pairs
  with **Spec 327** (multi-agent self-installer).
