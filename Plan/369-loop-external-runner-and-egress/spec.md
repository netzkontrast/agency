<!-- agency-node: spec-369 -->
---
spec_id: "369"
slug: loop-external-runner-and-egress
status: draft
last_updated: 2026-06-21
owner: "@agency"
vision_goals: [3, 8]
depends_on: ["002", "040", "192", "271", "328", "334", "339", "345", "349", "362", "366", "368"]
parent_spec: "362"
affects:
  - agency/_lifecycle_data/loop/          # emitted run-loop.py template + model-detection rubric + seed probes (data)
  - agency/_loop.py                        # spine module: emit_runner + egress evaluator (control evaluator lands in 366)
  - agency/capabilities/delegate/          # detect_models / register_model over the DriverRegistry (no new cap)
  - agency/capabilities/gate/              # the egress_consent gate registration
domain: loop / boundary / lifecycle-spine
wave: looper-port
---

# Spec 369 — Loop external runner, model detection & egress (the spine's out-of-session twin)

> Child of Spec 362 (ships LAST — composes the upstream children). **Reframed
> 2026-06-21: the loop is the lifecycle SPINE, not a `capabilities/loop/`
> capability.** Lifecycle IS the system's **state machine + event bus** (Spec
> 339/345 + 349b) and wires both **loops and workflows** onto one substrate, so
> looper's loop maps 1:1. 369 ports looper's **external `run-loop.py`**, **model
> detection** (§6), and **egress consent** (§9) as the *out-of-session twin* of
> walking the `loop` machine. Frugal port: reuse `shell` / DriverRegistry /
> `config` / `gate`; the net-new is one emitted template + one gate + seed data +
> the two closing tests.

## Why — two surfaces over one spine

The loop runs in two places over ONE resolved contract (`loop.resolved.json`, 368):

- **In-session = the spine walk.** `ctx.lifecycle.open(intent, machine="loop")`
  then `.move(...)` per transition (Spec 345; `move` is the sole state writer).
  Every transition fans onto the **lifecycle event bus** (Spec 349b), so the
  gate (364), council (365), and control evaluator (366) **react as subscribers**
  — looper's `state.json` / `run-log.md` are graph reads, recorded for free.
- **External = looper's `run-loop.py`.** A fixed, **stdlib-only** runner that
  reads ONLY `loop.resolved.json` and makes no design decisions: gather context →
  host drafts → plan_gate → deliver → delivery_gate → stop. Argv + timeout on
  every model call; lenient judge parse (degrade → revise + warn); consent-gated
  cross-vendor sends.

Both honour the same resolved spec. The spine is the source of truth; the runner
is the portable projection. Looper is honest that it is "a scaffolder + handoff,
not a durable orchestrator" (its principle #6); 369 keeps that boundary — the
external runner is for non-agency execution, the spine walk is canonical in-agency.

## Frugal mapping — agency already owns these boundaries

| Looper piece | Agency primitive (REUSE) | Net-new |
|---|---|---|
| `call_model` (subprocess, argv + timeout) | **`shell`** (Spec 192) — the safe argv/timeout boundary | — |
| `detect-models` / `register-model` / `~/.looper/models.json` | **DriverRegistry** (002) + **`config`** (334) | a probe over the allowlist; seed `MODEL_PROBES` |
| `ensure_consent` / `redactions_for` (§9) | a **`gate`** (Spec 328 shape) | the `egress_consent` gate (the one genuinely new gate) |
| `run-loop.py` (542 LOC) | the resolved Document (368) it reads | the template, emitted ~verbatim |
| `state.json.consent` | **provenance** (a graph node) | — (free; survives the session) |

**No new capability.** `detect_models`/`register_model` extend the existing driver
surface (`delegate`); `emit_runner` is a `document`-rendered template; the egress
gate registers like any `gate`; the walk is the lifecycle pillar.

### `detect_models` / `register_model` — over the DriverRegistry (002) + config (334)

Probe the looper allowlist (`claude`, `codex`, `gemini`, `llm`, `ollama`) by
`PATH` + a `--version` check; report which are authed. **Records invocation
metadata ONLY — argv + family + local flag — NEVER API keys/tokens** (looper File
Rule; auth stays in each CLI's keychain). `MODEL_PROBES` and `agents/openai.yaml`
port as seed data; `references/model-detection.md` ships verbatim to
`agency/_lifecycle_data/loop/rubrics/`. Persisted via `config` (334), not a
`~/.looper/models.json` file. `register_model` rejects a non-argv invoke and any
secret-shaped value.

### `emit_runner` — the ported `run-loop.py` template

Writes `<target>/run-loop.py`: the stdlib-only runner that reads ONLY
`loop.resolved.json` and executes the SAME contract the spine walk runs. Copied
with a fixed contract (looper File Rule: copy `run-loop.py` exactly unless the
runner contract changes). The template ships under `agency/_lifecycle_data/loop/`;
emission goes through `document.render` (368).

### The `egress_consent` gate (the one genuinely new gate)

A cross-family council member means context leaves the machine. A narrow gate
(Spec 328 shape), consulted before any cross-vendor send **in-session AND in the
external runner**:

- local member → permit (no egress);
- no `consent:required` policy → permit;
- first cross-vendor send → require explicit consent (`elicit` in-session; prompt
  in the runner) and record it as **provenance** (not `state.json`);
- apply redaction globs (default `.env`, `.env.*`, `secrets/**`, `**/*.key`)
  before the send; redacted paths are stubbed, not transmitted.

Ports looper's `ensure_consent` + `redactions_for`. Safe-by-construction (looper
principle #7) is enforced as acceptance, not prose: every external call is argv +
timeout (`shell`, 192); no secret is ever written into `loop.yaml` /
`loop.resolved.json` / the registry; redaction applies before the first byte.

### The 362 closers (carried here — they flip the master to Shipped)

1. **`test_loop_e2e`** — drive the full pipeline (frame goal Intent → add criteria
   → add members → open the `loop` machine → advance through plan_gate +
   delivery_gate → compile → emit), then assert `manage.provenance(intent_id)`
   (Spec 330) returns the whole chain: goal Intent, criteria, members, verdicts,
   artefacts. The provenance moat lit on a real loop — the thing looper (flat
   files) cannot do.
2. **`test_loop_roundtrip`** — using looper's ported fake-host / fake-judge /
   bad-judge / check-contains fixtures: the SAME resolved loop run **in-session**
   (the spine walk) and by the **emitted `run-loop.py`** reaches the **same gate
   decisions and the same `stop_reason`**. Proves the two surfaces honour one
   contract.

## Acceptance (Gherkin)

```gherkin
Scenario: detect_models records invocation metadata only, never secrets
  When I detect_models on a machine with claude and ollama installed
  Then the registry lists their argv invocations, families, and local flags
  And no API key or token appears anywhere in the registry

Scenario: register_model rejects a non-argv or secret-shaped invocation
  When I register_model with invoke "claude -p --key sk-abc123"
  Then it is rejected (argv-only; no secret material)

Scenario: the emitted runner reads only the resolved spec
  When I emit_runner and inspect run-loop.py
  Then it loads loop.resolved.json and imports only the Python stdlib

Scenario: a cross-vendor send requires first-send consent, recorded as provenance
  Given a non-local judge member with consent required and no prior consent
  When the spine walk (or the runner) is about to send the plan
  Then it requires explicit consent before sending and records the consent as a graph node

Scenario: a local member sends with no consent prompt
  Given an ollama judge member flagged local
  When it is convened
  Then no egress consent is required

Scenario: redaction globs apply before any send
  Given egress redact globs include "secrets/**"
  When context including secrets/key.txt would be sent
  Then that path is stubbed/redacted, not transmitted

Scenario: in-session and external runs agree (round-trip parity)
  Given the ported fake-host and fake-judge fixtures
  When the same resolved loop runs in-session (the spine walk) and via the emitted run-loop.py
  Then both reach the same gate decisions and the same stop_reason

Scenario: the provenance moat is lit end-to-end
  When I run the full loop pipeline and call manage.provenance(intent_id)
  Then it returns the goal Intent, every criterion, every member, every verdict, and every artefact
```

## Done When

- [ ] `detect_models` / `register_model` resolve models over the DriverRegistry (002) + `config` (334); metadata-only, secret-free (enforced), no new capability.
- [ ] `emit_runner` writes the stdlib-only `run-loop.py` (reads only `loop.resolved.json`) via `document.render`; template ships under `agency/_lifecycle_data/loop/`.
- [ ] the `egress_consent` gate ports `ensure_consent` + redaction; consent recorded as provenance; fires for the spine walk AND the external runner.
- [ ] argv + timeout on every external call (`shell`, 192); no secret in any emitted artefact (acceptance-tested).
- [ ] `model-detection.md` + the looper fake fixtures ship; `MODEL_PROBES` + `agents/openai.yaml` seed the registry.
- [ ] **`test_loop_e2e`** (provenance moat) + **`test_loop_roundtrip`** (spine ↔ external parity) pass — the 362 closers.
- [ ] `TODO.md` row updated; 362 master flips to Shipped when this lands Green.

## Followup — Implementation Status (2026-06-21)

**Verdict:** Re-drafted spine-framed (2026-06-21). The external execution surface
as the **out-of-session twin of the lifecycle-spine walk**: model resolution over
the DriverRegistry (002) + `config` (334), looper's stdlib `run-loop.py` emitted
as a `document`-rendered template reading the resolved spec (368), and one narrow
`egress_consent` gate (cross-vendor consent + redaction) firing for both surfaces.
Carries the master E2E (provenance moat via `manage.provenance`) + round-trip
parity tests that flip 362 to Shipped. **Frugal port — net-new is one template,
one gate, seed probes, two tests; everything else reuses `shell`/driver/`config`/
`gate`.** Depends on 366 (the `loop` machine on the spine) + 368 (the resolved
Document).
