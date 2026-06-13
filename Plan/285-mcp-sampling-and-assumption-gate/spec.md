---
spec: 285
title: mcp-sampling-and-assumption-gate
status: Design
depends_on: [114, 279]
clusters: [core]
vision_goals: [1, 3, 8]
---

# Spec 285 — MCP sampling + enforced assumption-gate (skill-walk)

> Status: **Design — awaiting user review** (user directive 2026-06-13:
> "design spec only, then pause"; assumption-rule = "enforce via elicit").
> No code ships until this design is signed off.
> Branch: `claude/agency-error-enum-fixes-13tpnf`

## Why

Two user asks, one substrate seam:

1. **Use real MCP Sampling to improve skill-walking + LLM interaction.**
   agency runs *inside* an LLM host (Claude Code). MCP gives the SERVER a way
   to ask the CLIENT to run a completion — `sampling/createMessage`, exposed by
   FastMCP as `ctx.sample(...)`. Today the engine **works around** this with
   the Spec 279 `llm_delegate` envelope: a verb that needs generation returns
   `kind="llm_delegate"`, the host runs inference and **re-calls** the verb
   with `host_completion`. That round-trip is the tax for not reaching the
   client. Real `ctx.sample` collapses it to one hop and lets a skill-walk
   phase generate *inline*, mid-walk.

2. **Never assume — enforce it in the walk.** Rule 0 (now in the install
   CLAUDE.md snippet, Spec-284-adjacent commit) is agent *guidance*. The user
   wants it **enforced**: when a skill-walk phase needs a value the engine
   cannot resolve, the walk must **ask the user** (`ctx.elicit(...)`,
   ask-in-the-flow) instead of advancing on a guess.

Both need the same thing the engine lacks today: capability code that can
reach the **client** (sample) and the **user** (elicit) from inside a verb.

## The seam (the crux)

`ctx.sample()` / `ctx.elicit()` live on the FastMCP **`Context`**, which is
injected ONLY into `@mcp.tool` functions that declare `ctx: Context` (the
engine's `lifecycle_gate` already does exactly this — the pattern exists).
Capability verbs — including the `develop.skill_walk` walker — instead receive
the **agency `CapabilityContext`** (`memory`/`registry`/`intent_id`/`ontology`/
`drivers`). They have **no handle to the FastMCP Context**. *That gap is the
entire reason Spec 279 returns an envelope instead of sampling directly.*

### Proposal — a request-scoped `HostBridge`

Bridge the live FastMCP `Context` into the capability layer, request-scoped:

1. **Capture.** `engine._wire.impl` gains a hidden `ctx: Context = None` param
   (FastMCP injects the live Context per call; it never appears in the tool's
   user-facing schema — it's filtered like the existing `inject` params). On
   entry, `impl` stashes the Context in a `contextvars.ContextVar`
   (`_HOST_CTX`). Request-scoped + async-safe; no global leak across
   concurrent calls.
2. **Expose.** `CapabilityContext` gains a `host` property returning a
   `HostBridge(_HOST_CTX.get(None))`. `HostBridge` wraps the FastMCP Context
   with a narrow, agency-typed surface:
   - `can_sample() -> bool` / `can_elicit() -> bool` — MCP capability
     negotiation (the client may not support either; FastMCP raises if so —
     the bridge probes + caches).
   - `sample(messages, *, system=None, max_tokens=…, ...) -> Completion` —
     awaits `ctx.sample(...)`, normalises the result into the existing
     `agency._drivers._anthropic.Completion` shape so call-sites are
     driver-agnostic.
   - `elicit(message, schema=None) -> ElicitOutcome` — awaits `ctx.elicit(...)`;
     maps accepted / declined / cancelled to a typed outcome.
   - When no Context is bound (CLI, bare unit tests, code-mode without client
     support): `can_*()` → False; `sample`/`elicit` raise a typed
     `HOST_UNAVAILABLE` the callers convert to their documented fallback.

`HostBridge` is the ONE new boundary. It is injected the same way `client` /
`drivers` already ride on `CapabilityContext` — no new public wire surface
(code-mode stays the only contract).

> **Why a ContextVar, not a param on every verb:** threading `ctx: Context`
> into all ~250 verb signatures would explode the wire schema and break the
> `inject` discipline. The hidden-capture-once + ContextVar pattern keeps the
> verb signatures clean and the bridge reachable from anywhere in the call
> tree (including `ctx.call(...)` siblings and the walker).

## Part A — sampling integration

### A1. `HostBridge.sample` fronts the Spec 279 boundary

`agency/_host_llm.py::complete_or_delegate` gains a branch ordered BEFORE the
`llm_delegate` fallback:

```
1. host_completion given          → resume (unchanged)
2. driver.backend() != "none"     → driver.complete(...) (unchanged)
3. ctx.host.can_sample()          → ctx.host.sample(...)        ← NEW
4. else                           → HostLLMRequest(llm_delegate) (unchanged)
```

So the precedence is: an explicitly-wired API-key driver wins (deterministic,
testable); else **real MCP sampling** when the client supports it; else the
envelope round-trip. **Spec 279 is not removed — it becomes the
capability-negotiated fallback** for hosts without sampling. Every LLM-using
verb (`novel.generate_scene_body`, `dogfood.*`, future `research.fetch`
summarisation) gets sampling for free because they already wrap
`complete_or_delegate`.

Provenance: a sampled completion records the SAME Invocation shape as a
delegated one, with `outcome="host_sampled"` (parallels `host_delegated` /
`host_resumed`) so a census can tell the three inference paths apart.

### A2. Skill-walk phases can sample to advance

A phase may declare `sample: {system, prompt_template, produces_key}`. When the
walker reaches such a phase and `ctx.host.can_sample()`, it builds the prompt
from `accumulated` + phase inputs, calls `ctx.host.sample(...)`, and feeds the
result into `produces` — the walk advances **without a wire round-trip**.
Without sampling support it falls back to the existing `input-required` pause
(the host supplies the value on resume). This makes generative phases
(brainstorm drafting, spec prose, scene bodies) first-class in the walk while
preserving the bounded one-phase-at-a-time contract.

## Part B — enforced assumption-gate (elicit)

### B1. A phase declares what it must NOT assume

Extend `_phase(...)` with `requires_input: [keys]` (distinct from `produces`):
values the phase needs but the engine **cannot derive**. When the walker
reaches the phase:

```
missing = [k for k in phase.requires_input
           if accumulated.get(k) in (None, "")
           and inputs.get(k) in (None, "")]
if missing:
    if ctx.host.can_elicit():
        answer = ctx.host.elicit(  # ask-in-the-flow, mid-walk
            f"Phase {phase.name!r} needs: {missing}. …", schema=…)
        accumulated.update(answer)         # proceed with the USER's value
    else:
        return {status: "input-required", blocked_on: f"assumption:{missing}",
                resume_with: missing, …}    # pause, never guess
```

The walk **cannot advance past a `requires_input` phase on an assumed value** —
either the user answers via `elicit`, or it pauses for resume. This is the hard
guardrail the user asked for. It reuses the existing `input-required` /
`resume_from` machinery (so non-elicit clients degrade gracefully) and the
`Gate`/`BLOCKED_ON` provenance (the elicited answer records as the gate's
evidence — an audit trail of "asked, here's what the user said").

### B2. Doctrine ↔ enforcement parity

Rule 0 in the CLAUDE.md snippet (already shipped) now has teeth: the snippet's
"hard skill-gates pause for sign-off / verbs fail LOUD" lines become literally
true for `requires_input` phases. No snippet change needed beyond what shipped.

## Surfacing (no new wire tools)

`agency_doctor` gains a `host` block: `{sampling: bool, elicitation: bool}`
(probed from the bound Context's client capabilities) so a session can SEE
whether it's in sample/elicit-capable mode or envelope-fallback mode — closes
the "why did it round-trip?" debugging gap. `agency_welcome` notes the mode in
`body` (per-call, cache-safe).

## Tests (plan — written at implement time, RED first)

`tests/test_host_bridge.py`:
1. `HostBridge(None).can_sample()/can_elicit()` → False; `sample`/`elicit`
   raise `HOST_UNAVAILABLE`.
2. With a fake Context exposing `sample`, `HostBridge.sample(...)` returns a
   normalised `Completion`; `can_sample()` True.
3. `_wire` captures the FastMCP Context into the ContextVar; a probe verb reads
   `self.ctx.host` and sees it; concurrent calls don't cross-bind (async task
   isolation).
4. `complete_or_delegate` precedence: driver wins over sample; sample wins over
   envelope; no-sample-support → envelope (Spec 279 path intact).
5. sampled completion records `outcome="host_sampled"` on the Invocation.

`tests/test_skill_walk_sampling.py` / extend `test_skill_walk_slices.py`:
6. a `sample:`-phase advances via a fake sampling Context (no input-required).
7. same phase with no-sample Context → `input-required` (graceful fallback).
8. a `requires_input` phase with a missing key + elicit-capable fake Context →
   walker elicits, applies the answer, advances; records the gate evidence.
9. same phase, no elicit support → `input-required` with
   `blocked_on="assumption:…"`; never advances on a guess.
10. `requires_input` satisfied by `inputs` up front → no elicit, advances.

`agency_doctor` test: `host` block reports `{sampling, elicitation}` booleans.

## Migration / risk

- **Additive.** Verbs/phases without `sample:`/`requires_input:` are untouched.
  Spec 279 envelope stays as fallback — no behaviour change for envelope hosts.
- **The ContextVar capture is the one load-bearing change to `_wire`.** Risk:
  a leaked/stale Context across calls. Mitigated by ContextVar (task-scoped) +
  setting to the live Context on every `impl` entry and never persisting it.
- **Code-mode interaction.** `ctx.sample`/`ctx.elicit` round-trip to the client
  *within* a single `call_tool`, so they work inside an `execute` block (the
  sandbox awaits the tool, the tool awaits the client). Must verify FastMCP's
  CodeMode transform forwards the Context into wired tools under code-mode (it
  forwards it to `lifecycle_gate` today — to confirm at implement time;
  **OQ1**).

## Open questions (for the review)

- **OQ1 — Context under code-mode.** Confirm the CodeMode/Monty sandbox path
  still injects the FastMCP Context into wired tool `impl`s (it does for the
  non-codemode `lifecycle_gate`; needs a code-mode probe). If NOT, sampling
  works only on the per-verb (`codemode=False`) surface + substrate tools, and
  skill-walk sampling needs the walker promoted to a substrate `@mcp.tool`.
- **OQ2 — elicit UX shape.** `ctx.elicit` supports a typed `response_type`
  (str / list-of-options / dict-schema). Do we want `requires_input` phases to
  offer **structured options** (like `AskUserQuestion`) where the phase can
  enumerate them, falling back to free-text otherwise? Recommend: yes, when the
  phase declares `options`.
- **OQ3 — sampling cost/consent.** Server-initiated sampling spends the user's
  tokens. MCP says the client gates/approves sampling; should agency ALSO add a
  per-session cap or a `sampling_enabled` config flag (default on) for
  budget-conscious users? Recommend: a config flag, default on, surfaced in
  `agency_doctor`.
- **OQ4 — scope of A2 adoption.** Which existing walkable skills get `sample:`
  phases in Slice 1? Recommend: none — ship the mechanism + tests in Slice 1;
  adopt per-skill in follow-ups (drop-in-phase bar), so the substrate lands
  before any skill depends on it.

## Suggested slicing (when approved)

- **Slice 1 — the seam.** `HostBridge` + ContextVar capture in `_wire` +
  `complete_or_delegate` sample branch + `agency_doctor.host` + tests 1–5.
  Pure substrate; no skill changes. (This alone retires the Spec 279
  round-trip for sample-capable hosts.)
- **Slice 2 — the walk.** `sample:` + `requires_input:` phase fields in the
  walker + the elicit assumption-gate + tests 6–10.
- **Slice 3 — adoption.** Add `sample:`/`requires_input:` to chosen skills
  (per OQ4), one skill at a time.
