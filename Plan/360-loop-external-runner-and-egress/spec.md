---
spec_id: "360"
slug: loop-external-runner-and-egress
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [3, 8]
depends_on: ["002", "040", "192", "271", "334", "353", "356", "357", "359"]
parent_spec: "353"
domain: loop / boundary
wave: looper-port
---

# Spec 360 — Loop external runner, model detection & egress consent

> Child of Spec 353 (ships LAST — composes all upstream children). Ports looper's
> **external `run-loop.py` runner**, its **model detection/registry** (§6,
> `detect-models` / `register-model`, `~/.looper/models.json`,
> `references/model-detection.md`), and its **privacy/security model** (§9 —
> cross-vendor egress consent + redaction globs). These three are one concern:
> *executing a resolved loop outside agency by shelling to external model CLIs,
> safely.* Carries the master 353 E2E + round-trip parity tests.

## Why

Looper has two execution surfaces over one resolved spec. The in-session surface
is the Lifecycle machine walk (357). The **external surface** is `run-loop.py`: a
fixed, small, **stdlib-only** runner that reads ONLY `loop.resolved.json` and
makes **no design decisions** — it parses the resolved spec, gathers context,
invokes model CLIs via **argv + timeouts**, runs gates, enforces caps, and stops.
Its contract (from `templates/run-loop.py`, 542 LOC):

- `gather_context` — read `context_sources` (file/cmd) into the workspace, redacted
- `run_host` / `run_gate` — host drafts plan/delivery; gate runs
  programmatic/human/reviewer/judge; `revise_until_clean` / `fixed_passes`
- `call_model` — `subprocess.run(argv, timeout=…)`, never a shell string
- `parse_judge_output` — lenient structured-verdict parse (degrade → revise + warn)
- termination — `enforce_wall_clock`, `no_progress_reached`, `max_revisions`,
  `max_iterations`
- privacy — `ensure_consent` (first cross-vendor send), `redactions_for`,
  `is_redacted`

Model resolution (§6): on first run, `detect-models` probes `PATH` for an
allowlist (`claude`, `codex`, `gemini`, `llm`, `ollama`), records **invocation
metadata only — never API keys** (`MODEL_PROBES` in `scripts/looper.py`), and
writes a registry. The wizard offers detected/authed models; unknowns are added
via `register-model`.

Agency already owns these boundaries: the **DriverRegistry** (Spec 002,
`ctx.get_driver`) resolves named drivers; **`delegate`/`jules`** (040/271) dispatch
to other models; **`shell`** (192) is the safe subprocess boundary (argv,
timeouts); **config** (334) persists settings durably. 360 binds them so the
runner and the in-session walk share one model-resolution + egress-consent path.

## Design

### `loop.detect_models` / `register_model` — over the DriverRegistry

```python
@verb(role="transform")
def detect_models(self, ctx) -> dict:
    """Probe for available model CLIs (the looper allowlist: claude, codex,
    gemini, llm, ollama) by checking PATH + a --version probe, and report which
    are authed. Records invocation metadata ONLY (argv + family + local flag) —
    NEVER API keys / tokens (looper File Rule; auth stays in each CLI's own
    keychain). Persists to the agency config (Spec 334), not ~/.looper/models.json.
    Returns {models: {id: {invoke, family, local, authed}}}. chain_next:
    loop.add_member (356) offers these; loop.register_model for unknowns.
    """

@verb(role="effect")
def register_model(self, ctx, mid: str, invoke: list[str], *, family: str = "",
                   local: bool = False) -> dict:
    """Register a custom model CLI by invocation metadata (argv array).
    Rejects non-argv invoke and any value that looks like a secret. This is
    looper's `register-model`, persisted to agency config + exposed as a driver."""
```

`MODEL_PROBES` (claude/codex/gemini/llm/ollama + their `invoke`/`probe`/`local`/
`install` metadata) ports verbatim as seed data; `agents/openai.yaml` becomes a
seed registry entry. The registry holds **invocation metadata only** — the
secret-free invariant is enforced (a registered `invoke` containing something
key-shaped is rejected). `references/model-detection.md` ships verbatim to
`data/rubrics/`.

### `loop.emit_runner` — the ported `run-loop.py` template

```python
@verb(role="effect")
def emit_runner(self, ctx, loop_id: str, target: str) -> dict:
    """Write <target>/run-loop.py — the stdlib-only external runner. The runner
    reads ONLY loop.resolved.json (359) and executes the SAME contract the
    in-session machine (357) walks: gather context → host → plan_gate →
    deliver → delivery_gate → stop. Argv + timeouts on every call; lenient judge
    parse; consent-gated cross-vendor sends. Copied with a fixed contract
    (looper File Rule: copy run-loop.py exactly unless the runner contract is
    explicitly changed). Returns {path}."""
```

The template is looper's `run-loop.py`, parameterized only by the resolved spec it
loads — so the external runner and the in-session walk are two readers of one
contract. The **round-trip parity test** (below) proves they agree.

### Egress consent + redaction (the one genuinely new gate)

A council member in a different family means **context leaves the machine**. 360
adds a narrow `egress_consent_gate` (a `gate`, Spec 328 shape) consulted before
any cross-vendor send — in-session (`delegate`/`jules` to a non-local family) AND
in the external runner:

```python
def egress_consent_gate(member: CouncilMember, policy: EgressPolicy, state) -> dict:
    """Ports run-loop.py ensure_consent + redactions_for:
      - local member → permit (no egress)
      - no consent:required policy → permit
      - first cross-vendor send → require explicit consent (elicit in-session;
        prompt in the runner), record consent in provenance (state.consent)
      - apply redaction globs (default: .env, .env.*, secrets/**, **/*.key)
        before the send; redacted paths are stubbed, not sent
    Returns {permit, redactions, needs_consent}."""
```

The `EgressPolicy` node (per member: `sends`, `redact`, `consent`) is the
`privacy.egress` block (354/356 author it; 359 carries it into the resolved spec).
Consent is recorded as provenance (a graph node), so "consented once" survives the
session — better than looper's `state.json.consent`.

> **Safe-by-construction (looper principle #7), enforced:** every external
> invocation is an argv array with a timeout (via `shell`, Spec 192); no secret is
> ever written into `loop.yaml` / `loop.resolved.json` / the registry; redaction
> applies before the first byte leaves. These are acceptance scenarios, not just
> prose.

### The master E2E + round-trip parity (the 353 closers)

360 carries the two tests that flip 353 to Shipped:

1. **`test_loop_e2e.py`** — `frame_goal → add_criterion → add_member → open_loop →
   advance×N (plan_gate + delivery_gate) → compile → emit`, then assert
   `memory_graph_provenance(intent_id)` returns the full chain (goal Intent,
   criteria, members, verdicts, artefacts) — the provenance moat lit on a real
   loop.
2. **`test_loop_roundtrip.py`** — using looper's ported fake-host / fake-judge /
   bad-judge / check-contains fixtures: a loop run **in-session** (357) and the
   SAME loop run by the **emitted `run-loop.py`** (360) over the same fixtures
   reach the **same gate decisions** (pass/revise, stop_reason). Proves the two
   surfaces honour one contract.

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

Scenario: a cross-vendor send requires first-send consent
  Given a non-local judge member with consent required and no prior consent
  When the runner (or in-session walk) is about to send the plan
  Then it requires explicit consent before sending and records the consent

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
  When the same resolved loop runs in-session and via the emitted run-loop.py
  Then both reach the same gate decisions and the same stop_reason

Scenario: the provenance moat is lit end-to-end
  When I run the full loop pipeline and call memory_graph_provenance(intent_id)
  Then it returns the goal Intent, every criterion, every member, every verdict, and every artefact
```

## Done When

- [ ] `loop.detect_models` / `register_model` resolve models over the DriverRegistry (002) + config (334); metadata-only, secret-free (enforced).
- [ ] `loop.emit_runner` writes the stdlib-only `run-loop.py` reading only `loop.resolved.json`.
- [ ] `egress_consent_gate` ports `ensure_consent` + redaction; consent recorded as provenance; fires in-session AND external.
- [ ] argv+timeout on every external call (192); no secrets in any emitted artefact (acceptance-tested).
- [ ] `model-detection.md` + the looper fake fixtures ship; `MODEL_PROBES` + `agents/openai.yaml` seed the registry.
- [ ] **`test_loop_e2e.py`** (provenance moat) + **`test_loop_roundtrip.py`** (in-session ↔ external parity) pass — the 353 closers.
- [ ] `TODO.md` row updated; 353 master flipped to Shipped when this lands Green.

## Followup — Implementation Status (2026-06-20)

**Verdict:** Not started — drafted under the 353 wave (ships LAST). The external
execution surface: model detection/registry over the DriverRegistry (002), the
ported stdlib `run-loop.py` reading the resolved spec (359), and a narrow
egress-consent gate (cross-vendor consent + redaction) that fires for both
surfaces. Carries the master E2E (provenance moat) + round-trip parity tests that
flip 353 to Shipped. Depends on 356 (members/families), 357 (the walk contract),
359 (the resolved spec).
