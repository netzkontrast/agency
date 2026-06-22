---
spec_id: "332"
slug: frugal-core-discipline
status: draft
state: done
last_updated: 2026-06-19
owner: "@agency"
vision_goals: [1, 3, 4]
depends_on: ["062", "076", "146", "280", "292", "295", "328"]
domain: core
wave: core-discipline
---

# Spec 332 — Frugal core discipline (agency's minimal-code reflex)

> Give agency its own **frugal** discipline — a *write-only-what-the-task-needs*
> reflex — embedded into **core**, NOT a capability. The minimal-code ladder + a
> non-negotiable safety floor become **core state** (active level, **default
> `full`**) governing **every pillar and every verb**: injected at every session
> start / prompt **and** referenced by a **compact stamp in every verb's
> response-envelope prefix** (cache-stable, Spec 146). This is GOALS.md Goal 1
> (token-efficient loops) at the *code-output* layer, present uniformly across
> every agent surface (Goal 3).
>
> **This is a redevelopment, not a port** — the ladder (YAGNI → stdlib → native →
> dep → one line → minimum) is general engineering wisdom; agency implements its
> own from first principles. Design notes:
> [`reference/DISCIPLINE.md`](reference/DISCIPLINE.md). **Panel-hardened**
> (2026-06-19): durable+scoped level state, decided token budget, additive-envelope
> compat, silent-degrade, cache semantics, Gherkin. Provenance `intent:7509dac0`.

## Why (evidence + doctrine)

Agency has no *coding* discipline that holds on every action — nothing stops an
agent over-building a 404-line date-picker when `<input type="date">` is the
answer. Over-building is the dominant waste in agentic coding: speculative
abstractions, needless dependencies, boilerplate "for later." A frugal reflex at
the **code-output** layer is Goal 1 made concrete — *fewer, necessary lines* cut
LOC, tokens, cost, and latency together — and it complements code-mode (which
trims the *tool-call* layer). The rule is **never "fewest tokens"**: it is *write
only what the task needs, and never cut validation, error handling, security, or
accessibility* — the code ends up small because it is necessary, not golfed.

**Why core, not a capability (explicit Goal-4 trade-off).** GOALS.md lists "fixed
*domains* in the core" as a non-goal — but this is a **cross-cutting discipline,
not a domain**, with direct precedent: the **assumption-guard already lives in
core and injects every prompt** (`[agency] AVOID ASSUMPTIONS`) via the same hook
seam. A discipline that must govern *every* verb cannot be opt-in. The open-set
capability invariant (Goal 4) is untouched — no domain enters the core; one
engine-level discipline does, exactly like the assumption-guard.

## The discipline (single source of truth)

One canonical module in core — `agency/_frugal.py` — owns the text and its
rendering. Everything derives from it: the session injection, the per-verb stamp,
and Spec 333's per-agent rules files. No second copy to drift.

1. **The ladder** — before writing code, stop at the first rung that holds:
   `1. Does this need to exist? (YAGNI) → 2. stdlib → 3. native platform feature
   → 4. installed dependency → 5. one line → 6. the minimum that works.`
2. **The safety floor (non-negotiable — a first-class gate, Slice 4):**
   trust-boundary validation · error handling that prevents data loss · security ·
   accessibility · anything explicitly requested are **never** cut. *"Frugal code
   without its check is unfinished"* — non-trivial logic leaves ONE runnable check
   behind (an assert-based self-check or one small `test_*.py`).
3. **Levels** — `lite` (build it, name the leaner alternative) · **`full`** (the
   ladder enforced, default) · `ultra` (deletion before addition) · `off`.
4. **The marker convention** — deliberate simplifications get a `# frugal:`
   comment naming the ceiling + upgrade path
   (`# frugal: global lock, per-account locks if throughput matters`).
5. **Two projections** (decided, Q2): a **full** render (whole ladder + floor —
   M1 session injection) and a **compact** render (one-line pointer + floor — the
   M2 per-verb stamp, to bound prefix tokens).

## Design — core embedding (mechanism **M1 + M2**)

### Core state — lifetime & scope (via Spec 334)

Level resolution on READ goes through **Spec 334's `config_get("frugal.level")`** —
`AGENCY_FRUGAL_LEVEL` env → `.agency/config.yaml` `frugal.level` → **`full`**.
SET (`frugal_level(level)`) calls **`config_set` → persists to
`.agency/config.yaml`** (durable, so the **CLI — a fresh process per invocation —
sees it next run**) **and** records a `FrugalLevel` provenance node. The in-process
cache (`engine.frugal_level`) is a **per-process** read-through; the long-lived MCP
server is assumed **single-session per project** — documented, not load-bearing
(config is the source of truth, not the attr).

### M1 — Session / prompt injection (governs the agent's coding)

Core `SessionStart` + `UserPromptSubmit` hook handlers
(`engine.register_hook_handler`, beside the assumption-guard) return
`{"inject": <FULL render @ level>}`. `cli.py hook` already prints `inject` to
stdout — the same path is the **CLI lane** (`python -m agency.cli hook`), so a
no-MCP agent that runs the hook script is covered; a pure no-hook agent is covered
by Spec 333's `AGENTS.md`. Cadence (Q1): `SessionStart` for all levels; **`ultra`
additionally fires on `UserPromptSubmit`**; `off` injects nothing.

### M2 — Per-verb envelope stamp ("with every verb there is")

`ResponseEnvelope.prefix` (Spec 146) gains a `frugal` key carrying the **COMPACT
render** (`"<level> · YAGNI→stdlib→native→dep→1-line · floor: validate/secure/a11y
never cut"` — one line, **≤ ~40 tokens**, decided Q2). Living in the byte-stable
**prefix**, it rides every verb return yet is ~free on a cache hit. The envelope
only **references** `_frugal.py`'s compact render — it holds no discipline logic
(coupling bounded). `off` omits the key.

**Backward-compat:** the `frugal` key is **additive**; existing Spec 146 envelope
consumers ignore unknown keys; the wire contract (search/get_schema/execute) is
unchanged; Spec 146 prefix tests are updated (Slice 2). **Failure posture:** any
render failure → M1 injects nothing, M2 omits the key, **the verb/session still
succeeds** (the assumption-guard precedent).

### "Every pillar directly uses it" — structurally, not per-pillar

Consumed at the two choke points all verbs share — the **envelope builder** (every
return) and the **hook layer** (every session/prompt). No per-capability edits; a
new pillar inherits the discipline for free.

## Slices (TDD)

1. **Core module + durable state.** `_frugal.py` (ladder + floor + full & compact
   renders) and `frugal_level` substrate tool (read/SET → Spec 334 config +
   `FrugalLevel` node, default `full`).
2. **M2 — compact envelope stamp.** `prefix.frugal` on every verb; omitted at
   `off`; Spec 146 prefix tests updated.
3. **M1 — session/prompt injection.** Core handlers (full render; `ultra` adds
   prompt cadence).
4. **Safety-floor gate.** A `gate`-recordable predicate: the rendered/injected
   discipline never omits validate/secure/a11y at any level but `off`.
5. **Doctor + install wiring.** `agency_doctor` reports `frugal.level`; `install`
   emits the core handlers (zero-manual-step setup).

## Acceptance criteria

- **C1** — Default `full`, no opt-in: every verb return carries the compact stamp
  and every new session is injected — core, not a capability.
- **C2** — The safety floor is a first-class, tested clause no level (bar `off`)
  can strip.
- **C3** — Cache-safe **at a fixed level**: the stamp is byte-identical across
  calls; a **level change is an intentional one-time cache bust**.
- **C4** — Single source of truth in `_frugal.py`; both injection paths, the
  per-verb stamp, and Spec 333's files derive from it (drift-gated).
- **C5** — `off` fully disables; the per-verb stamp is **token-bounded** (≤ ~40
  tokens); full ladder only in the session injection (Goal-1 self-consistency).
- **C6** — Durable + degrading: SET survives process exit (CLI next-run sees it);
  any render failure degrades silently without failing the verb.

## Acceptance scenarios (Gherkin sketch)

```gherkin
Scenario: default level governs every verb
  Given a fresh engine with no AGENCY_FRUGAL_LEVEL and no config
  When any verb returns
  Then the envelope prefix.frugal is the compact render at "full"
  And it contains the safety-floor clause

Scenario: off disables both paths
  Given frugal_level is set to "off"
  When a verb returns and a SessionStart hook fires
  Then prefix has no frugal key
  And the SessionStart inject is empty

Scenario: SET persists across a fresh CLI process
  Given "agency frugal ultra" has run
  When a brand-new CLI process reads the level
  Then it resolves "ultra" from .agency/config.yaml

Scenario: render failure degrades silently
  Given _frugal.render raises
  When a verb returns
  Then the verb result is unchanged and succeeds
  And prefix has no frugal key

Scenario: stamp is byte-stable at a fixed level
  Given level "full"
  When the same verb is called twice
  Then the two prefix.frugal values are byte-identical
```

## Open questions

- **Q3** — Should `lite` drop the per-verb stamp (session-only)? *Rec: keep the
  compact stamp at `lite` (already ≤40 tok); revisit if budget lint flags it.*

## Followup — Implementation Status (2026-06-19)

**Verdict: Shipped** (all 5 slices).

- **Done — Slice 1** (`agency/_frugal.py`, PR #171): the ladder + safety-floor
  content, `LEVELS`/`DEFAULT_LEVEL='full'`, `frugal_level`/`set_frugal_level`
  (via Spec 334 config), `render(level, mode='full'|'compact')`, `off` → empty.
- **Done — Slice 3** (M1, PR #171): `engine._append_frugal` injects the
  discipline on `UserPromptSubmit` (compact; full at `ultra`) + `SessionStart`
  (full); `off` injects nothing; degrades silently.
- **Done — Slice 2** (M2, this change): `_frugal.frugal_prefix()` →
  `{"frugal": <compact>}` (gated by `frugal.stamp_every_verb`; `off` → `{}`;
  never raises). `engine._shape_wire_result` stamps **every capability verb**
  return (additive, byte-stable, degrades silently); `agency_welcome` carries it
  in its cache-stable Spec-146 prefix. 3 acceptance scenarios; verified additive
  across welcome budget/stability + the exact-eq suite (194 + 35 green).
- **Done — Slice 4** (safety-floor gate): `_frugal.safety_floor_intact(render_fn=None)`
  — a decidable predicate (`{ok, checked, findings}`) that at every non-off level
  the FULL render carries every `SAFETY_FLOOR_MARKER` and the COMPACT render names
  the floor; gate-recordable via `gate.check(passed=result['ok'])`. 3 acceptance
  scenarios (intact, catches a stripped marker via an injected render, records a
  passing Gate).
- **Done — Slice 5** (doctor + install wiring): `agency_doctor` gains a `frugal`
  block (`{level, source, stamp_active}`, derived from the config block +
  `frugal_prefix` — no dup logic) so "is frugal on?" is one glance. Install is
  zero-manual-step by composition: the M1 handlers are engine-resident (any
  engine injects on SessionStart/UserPromptSubmit), `frugal.level` is scaffolded
  by Spec 334 S3, and the M2 stamp fires on every verb (S2). 1 OOB integration
  scenario. (Q3 decided: keep the compact stamp at `lite`.)
- **Blocker / Next step:** none — 326 shipped. Pairs with Spec 333 (the installer
  projects the same `_frugal` discipline into per-agent rules files).
