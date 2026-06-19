---
spec_id: "326"
slug: ponytail-port
status: draft
last_updated: 2026-06-19
owner: "@agency"
vision_goals: [1, 3, 4]
depends_on: ["062", "076", "146", "280", "292", "295", "328"]
domain: core
wave: core-discipline
---

# Spec 326 — Core-embedded minimal-code discipline ("ponytail-in-core")

> Port the third-party **ponytail** discipline (DietrichGebert/ponytail, MIT)
> into agency **as a core cross-cutting concern — NOT a capability**. The
> minimal-code ladder + the non-negotiable safety floor become **core state**
> (active level, **default `full`**) that governs **every pillar and every
> verb**: injected at every session start / prompt **and** referenced by a
> **compact stamp in every verb's response-envelope prefix** (cache-stable,
> Spec 146). This is GOALS.md Goal 1 (token-efficient loops) at the *code-output*
> layer, present uniformly across every agent surface (Goal 3).
>
> **★ Supersedes the v1 capability-folder design** (2026-06-19 directive); the
> multi-agent self-installer is split into **Spec 327**. **★ Panel-hardened**
> (2026-06-19 `/sc:spec-panel`): durable+scoped level state, decided token
> budget, additive-envelope compat, silent-degrade, cache semantics, Gherkin
> sketches. Provenance: `intent:7509dac0`; pivots `reflection:fe553a2e`,
> `4a4b94a7`; vendored source under [`reference/`](reference/).

## Why (evidence + doctrine)

Agency has no *coding* discipline that holds on every action — nothing that stops
an agent over-building a 404-line date-picker when `<input type="date">` is the
answer. Ponytail is exactly that, and it is **measured**: a headless agent
editing a real FastAPI+React repo (Haiku 4.5, n=4) cut **−54% LOC, −22% tokens,
−20% cost, −27% time at 100% safety** — the only arm to cut every metric without
dropping a guard
([`reference/benchmarks/results/2026-06-18-agentic.md`](reference/benchmarks/results/2026-06-18-agentic.md)).
That is Goal 1 at the code-output layer, complementing code-mode at the tool-call
layer.

**Why core, not a capability (explicit Goal-4 trade-off).** GOALS.md lists "fixed
*domains* in the core" as a non-goal — but this is a **cross-cutting discipline,
not a domain**, with direct precedent: the **assumption-guard already lives in
core and injects every prompt** (`[agency] AVOID ASSUMPTIONS`) via the same hook
seam. A discipline that must govern *every* verb cannot be opt-in. The open-set
capability invariant (Goal 4) is untouched — no domain enters the core; one
engine-level discipline does, exactly like the assumption-guard.

## The discipline (single source of truth)

One canonical module in core — `agency/_discipline.py` — owns BOTH the text and
its **rendering** (per-level + the two projections below). Everything derives
from it: the session injection, the per-verb stamp, and Spec 327's per-agent
rules files. No second copy to drift (the rule ponytail enforces upstream with
`check-rule-copies.js`).

1. **The ladder** — before writing code, stop at the first rung that holds:
   `1. Does this need to exist? (YAGNI) → 2. stdlib → 3. native platform feature
   → 4. installed dependency → 5. one line → 6. the minimum that works.`
2. **The safety floor (non-negotiable)** — *lazy, not negligent*: trust-boundary
   validation, data-loss handling, security, and accessibility are **never** cut.
   A **first-class, tested clause**, not prose (Slice 4 gate).
3. **Levels** — `lite / full / ultra / off`, scaling strictness; `off` → nothing
   injected, nothing stamped.
4. **Two projections** (decided, see Q2): a **full** render (the whole ladder +
   floor — used by M1 session injection) and a **compact** render (a one-line
   pointer + the floor — used by the M2 per-verb stamp, to bound prefix tokens).

## Design — core embedding (mechanism **M1 + M2**)

### Core state — lifetime & scope (panel ❌ Nygard)

Level resolution on READ goes through **Spec 328's `config_get("ponytail.level")`**
— `PONYTAIL_DEFAULT_MODE` env → `.agency/config.yaml` `ponytail.level` → **`full`**.
SET (`discipline_level(level)`) calls **`config_set` → persists to
`.agency/config.yaml`** (durable, so the **CLI — a fresh process per invocation —
sees it next run**) **and** records a `DisciplineLevel` provenance node. *(Config
home is Spec 328's unified `.agency/config.yaml`; supersedes the v1 `config.json`.)* The
in-process cache (`engine.discipline_level`) is a **per-process** read-through of
that config; the long-lived MCP server is assumed **single-session per project**
(one `agency-mcp` per `CLAUDE_PROJECT_DIR`) — documented, not load-bearing for
correctness because config is the source of truth, not the attr.

### M1 — Session / prompt injection (governs the agent's coding)

Core `SessionStart` + `UserPromptSubmit` hook handlers
(`engine.register_hook_handler`, beside the assumption-guard) return
`{"inject": <FULL render @ level>}`. `cli.py hook` already prints `inject` to
stdout — the same path is the **CLI lane** (`python -m agency.cli hook`), so a
no-MCP agent that runs the hook script is covered; a pure no-hook agent is
covered by Spec 327's `AGENTS.md`. Cadence (Q1 decided): `SessionStart` for all
levels; **`ultra` additionally fires on `UserPromptSubmit`**; `off` injects
nothing.

### M2 — Per-verb envelope stamp ("with every verb there is")

`ResponseEnvelope.prefix` (Spec 146) gains a `discipline` key carrying the
**COMPACT render** (`"<level> · YAGNI→stdlib→native→dep→1-line · floor: validate/
secure/a11y never cut"` — one line, **≤ ~40 tokens**, decided Q2). Living in the
byte-stable **prefix**, it rides every verb return yet is ~free on a cache hit.
The envelope only **references** `_discipline.py`'s compact render — it holds no
discipline logic itself (panel ⚠️ Fowler: coupling named + bounded). `off` omits
the key.

**Backward-compat (panel ⚠️ Newman):** the `discipline` key is **additive**;
existing Spec 146 envelope consumers ignore unknown keys. The wire *contract*
(search/get_schema/execute) is unchanged; the *envelope shape* gains one optional
prefix key — Spec 146 prefix tests are updated to allow/assert it (named in
Slice 2). Not a breaking change.

**Failure posture (panel ⚠️ Nygard):** if `_discipline.py` render throws, M1
injects nothing and M2 omits the key — **the verb/session still succeeds**. The
discipline degrades silently, never fails an action (the assumption-guard
precedent).

### "Every pillar directly uses it" — structurally, not per-pillar

Consumed at exactly two choke points all verbs share — the **envelope builder**
(every return) and the **hook layer** (every session/prompt). No per-capability
edits; a new pillar inherits the discipline for free.

## Slices (TDD — Gherkin acceptance is the contract)

1. **Core module + durable state.** `_discipline.py` (ladder + floor + full &
   compact renders) and `discipline_level` substrate tool (read/SET → config +
   `DisciplineLevel` node, default `full`).
2. **M2 — compact envelope stamp.** `prefix.discipline` on every verb at the
   active level; omitted at `off`; Spec 146 prefix tests updated.
3. **M1 — session/prompt injection.** Core `SessionStart`/`UserPromptSubmit`
   handlers (full render; `ultra` adds prompt cadence).
4. **Safety-floor gate.** A `gate`-recordable predicate: the rendered/injected
   discipline never omits validate/secure/a11y at any level but `off`.
5. **Doctor + install wiring.** `agency_doctor` reports `discipline_level`;
   `install` emits the core handlers (zero-manual-step setup).

## Acceptance criteria (the contract)

- **C1** — Default `full`, no opt-in: every verb return carries the compact stamp
  and every new session is injected — core, not a capability.
- **C2** — The safety floor is a first-class, tested clause no level (bar `off`)
  can strip.
- **C3** — Cache-safe **at a fixed level**: the stamp lives in the byte-stable
  prefix and is identical byte-for-byte across calls; a **level change is an
  intentional one-time cache bust** (acknowledged, not a regression).
- **C4** — Single source of truth in `_discipline.py`; both injection paths, the
  per-verb stamp, and Spec 327's files derive from it (drift-gated).
- **C5** — `off` fully disables (no inject, no stamp). The per-verb stamp is
  **token-bounded** (compact render ≤ ~40 tokens); full ladder only in the
  session injection (Goal-1 self-consistency).
- **C6** — Durable + degrading: SET survives process exit (CLI next-run sees it);
  any render failure degrades silently without failing the verb.

## Acceptance scenarios (Gherkin sketch — behaviour, not internals)

```gherkin
Scenario: default level governs every verb
  Given a fresh engine with no PONYTAIL_DEFAULT_MODE and no config
  When any verb returns
  Then the envelope prefix.discipline is the compact render at "full"
  And it contains the safety-floor clause

Scenario: off disables both paths
  Given discipline_level is set to "off"
  When a verb returns and a SessionStart hook fires
  Then prefix has no discipline key
  And the SessionStart inject is empty

Scenario: SET persists across a fresh CLI process
  Given "agency discipline ultra" has run
  When a brand-new CLI process reads the level
  Then it resolves "ultra" from .agency/config.yaml

Scenario: render failure degrades silently
  Given _discipline.render raises
  When a verb returns
  Then the verb result is unchanged and succeeds
  And prefix has no discipline key

Scenario: stamp is byte-stable at a fixed level
  Given level "full"
  When the same verb is called twice
  Then the two prefix.discipline values are byte-identical
```

## Open questions (remaining)

- **Q3** — Should `lite` drop the per-verb stamp entirely (session-only) to save
  tokens on low-stakes work? *Rec: keep the compact stamp at `lite` (it's already
  ≤40 tok); revisit if budget lint flags it.*

*(Q1 cadence and Q2 token budget — decided above.)*

## Followup — Implementation Status (2026-06-19)

**Verdict: Not started** (design redrafted + panel-hardened; awaiting gate approval).

- **Done:** v1 capability design superseded; agency-thinking pivot
  (`reflection:fe553a2e`); M1+M2 grounded on live code
  (`register_hook_handler`/`dispatch_hook`/`_envelope.ResponseEnvelope`/
  `cli.py hook`); `/sc:spec-panel` folded — durable/scoped state, compact-stamp
  token budget, additive-envelope compat, silent-degrade, C3 cache semantics,
  Gherkin sketches (`reflection` pending).
- **Still:** human gate approval, then Slice 1 (`_discipline.py`).
- **Blocker / Next step:** confirm Q3, then build Slice 1 under TDD. Pairs with
  **Spec 327**.
