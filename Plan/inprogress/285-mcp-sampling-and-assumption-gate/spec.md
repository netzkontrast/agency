---
spec: 285
title: mcp-sampling-and-assumption-gate
status: Implementing (Slice 1 shipped)
state: inprogress
depends_on: [114, 279]
clusters: [core]
vision_goals: [1, 3, 8]
---

# Spec 285 — MCP sampling + enforced assumption-gate (skill-walk)

> Status: **Design reviewed — OQ1–OQ4 resolved with the user (2026-06-13);
> ready for Slice 1 on go.** Assumption-rule = "enforce via elicit".
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
values the phase needs but the engine **cannot derive**. A `requires_input`
phase ALSO declares how to source the choices — **not** hardcoded option lists
in phase metadata, but a binding to a **FastMCP-annotated capability verb in the
skill's own capability** (user decision, OQ2): `resolve_via: {capability, verb}`
(the same shape as the existing `invoke:` phase binding, which `render_phase`
already delegates to). That resolver verb computes the structured options /
default for the missing key; because it is a real registered `@verb`, the
resolution is itself a discoverable, **provenance-recording Invocation** (not
ad-hoc walker code) — consistent with the moat. Constraint: the resolver MUST
belong to the same capability that owns the skill (no cross-capability option
sourcing at the gate).

When the walker reaches the phase:

```
missing = [k for k in phase.requires_input
           if accumulated.get(k) in (None, "")
           and inputs.get(k) in (None, "")]
if missing:
    # 1. source structured choices from the bound, FastMCP-annotated verb
    options = ctx.call(phase.resolve_via.capability, phase.resolve_via.verb,
                       keys=missing, context=accumulated)   # an Invocation
    if ctx.host.can_elicit():
        # 2. ask the user IN THE FLOW, structured (options) — never guess
        answer = ctx.host.elicit(
            f"Phase {phase.name!r} needs {missing}.", options=options)
        accumulated.update(answer)
    else:
        return {status: "input-required", blocked_on: f"assumption:{missing}",
                resume_with: missing, options: options, …}  # pause, never guess
```

The walk **cannot advance past a `requires_input` phase on an assumed value** —
either the user picks from the resolver-sourced options via `elicit`, or it
pauses for resume (non-elicit clients degrade gracefully; the options ride the
pause envelope). This is the hard guardrail. The `Gate`/`BLOCKED_ON` provenance
records the elicited answer as the gate's evidence — an audit trail of "asked,
here's the resolver's options, here's what the user chose".

### B2. Doctrine ↔ enforcement parity

Rule 0 in the CLAUDE.md snippet (already shipped) now has teeth: the snippet's
"hard skill-gates pause for sign-off / verbs fail LOUD" lines become literally
true for `requires_input` phases. No snippet change needed beyond what shipped.

## Sampling cost control (OQ3 — resolved: yes)

A `sampling_enabled` config flag (default **on**) gates server-initiated
sampling, since `ctx.sample` spends the user's tokens. When off,
`HostBridge.can_sample()` returns False regardless of client capability, so
`complete_or_delegate` falls back to the Spec 279 envelope (host runs inference
under its own visible control). Resolution order for the flag: explicit
`Engine(..., sampling_enabled=)` kwarg → `AGENCY_SAMPLING_ENABLED` env →
default True. Surfaced in `agency_doctor.host`.

## Surfacing (no new wire tools)

`agency_doctor` gains a `host` block: `{sampling: bool, elicitation: bool,
sampling_enabled: bool}` (client capability ∧ the config flag) so a session can
SEE whether it's in sample/elicit-capable mode or envelope-fallback mode —
closes the "why did it round-trip?" debugging gap. `agency_welcome` notes the
mode in `body` (per-call, cache-safe).

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
   `blocked_on="assumption:…"` AND the resolver-sourced `options`; never
   advances on a guess.
10. `requires_input` satisfied by `inputs` up front → no resolver call, no
    elicit, advances.
11. the `resolve_via` binding invokes a real FastMCP-annotated verb in the
    skill's own capability → records an Invocation (provenance), and a
    cross-capability `resolve_via` is rejected at registration/lint.

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

## Resolved decisions (user review, 2026-06-13)

- **OQ1 — Context under code-mode → RESOLVED YES (probed).** A wired tool
  declaring `ctx: Context` receives a live Context **with `.sample`** even when
  called through the code-mode `execute` sandbox (probe: `ctx_present=True`,
  `has_sample=True`). So the ContextVar-capture seam works under code-mode; the
  `skill_walk` walker stays a normal capability verb — **no substrate-tool
  promotion needed.** This was the load-bearing unknown; it's clear.
- **OQ2 — elicit shape → RESOLVED: structured, sourced from a bound verb.**
  Options are NOT hardcoded in phase metadata; a `requires_input` phase binds a
  `resolve_via: {capability, verb}` to a FastMCP-annotated verb **in the
  skill's own capability** that computes the choices (provenance-recording
  Invocation; mirrors the existing `invoke:` binding). See §B1.
- **OQ3 — sampling cost → RESOLVED: yes.** `sampling_enabled` config flag,
  default on, surfaced in `agency_doctor`. See §"Sampling cost control".
- **OQ4 — Slice-1 adoption → RESOLVED: brainstorm + scene-writer now.** Slice 1
  proves the mechanism on those two skills (not seam-only, not all skills).

## Slicing

- **Slice 1 — seam + walk + two proving skills (this spec's deliverable).**
  `HostBridge` + ContextVar capture in `_wire` + `complete_or_delegate` sample
  branch + `sampling_enabled` flag + `agency_doctor.host` + the `sample:` /
  `requires_input:`+`resolve_via:` phase fields in the walker + the elicit
  assumption-gate. Adopt the new phase fields in **`develop.brainstorm`**
  (a `sample:` drafting phase) and **`scene-writer`** (a `requires_input:`
  assumption-gate phase with a novel-capability `resolve_via` verb). All tests
  1–10 + the doctor `host`-block test.
- **Slice 2 — wider adoption.** Roll `sample:` / `requires_input:` into the
  remaining generative skills, one at a time (drop-in-phase bar).

## Followup — Implementation Status (2026-06-13)

**Slice 1 SHIPPED (Part A seam + Part B walk).**

- **Part A — the seam** (commit `feat(285): Slice 1 Part A`): `agency/_host_bridge.py`
  (`HostBridge` sync `sample`/`elicit` bridged via `anyio.from_thread`; `bind/
  reset/current_host_context` ContextVar) + `_wire` `_host_ctx` capture →
  `CapabilityContext.host` + `complete_or_delegate` sample branch (driver >
  sample > Spec-279 envelope; `host_sampled`) + `Engine(sampling_enabled=)` +
  `agency_doctor.host`. 13 tests.
- **Part B — the walk**: `_phase` gains `sample` / `requires_input` /
  `resolve_via`; the `develop._skill_walk` walker runs `_assumption_gate`
  (elicit-or-pause; options sourced from a FastMCP verb in the skill's own
  capability via `resolve_via` — a provenance Invocation) then `_sample_phase`
  (host-sample to advance, else pause) before each `submit`. Adopted in
  `develop.brainstorm` (`explore` samples `questions`) + the novel
  `scene-writer` skill (`validate-constraints` `requires_input=["pov_choice"]`
  → `resolve_via novel.pov_options`). New `novel.pov_options` resolver verb.
  5 tests (`test_skill_walk_part_b.py`): sample advances / pauses; requires_input
  elicits+advances (+records the resolver Invocation) / pauses with options /
  is skipped when supplied. Existing brainstorm/scene-writer walks unaffected
  (the `input-required` status is already in their accepted set).

**Slice 2 (wider adoption)** — roll `sample:`/`requires_input:` into the
remaining generative skills one at a time (drop-in-phase bar).
