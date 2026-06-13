---
spec: 282
title: error-severity-taxonomy
status: Shipped
depends_on: [001, 059]
clusters: [core, observability]
vision_goals: [2, 5, 6]
---

# Spec 282 — Error Severity Taxonomy

## Problem (evidence-grounded)

Verified by read-only SQL census against `kohaerenzprotokoll/.agency/session.db`
(one `scripts/ingest_canon.py` run):

| metric | value |
|---|---|
| Invocations | 1952 |
| `outcome='failed'` | 626 (32.1%) |
| `create_scene` total / failed | 531 / 513 |
| `capture_claim` failed | 60 (`domain='canon'` ∉ `RESEARCH_DOMAINS`) |
| `create_codex_entry` failed | 49 (`kind` ∉ `CODEX_ENTRY_KIND`) |

Every `create_scene` failure is `INVALID_ARGUMENT: pov=… not in
['first','second','third-limited','third-omniscient']` — a rich German voice
description rejected by a closed 4-value enum. The ingest driver retried each
impossible call ~34× (`scripts/ingest_canon.py` loops `for attempt in
range(1, 40)` "while progress is made").

**Root cause.** The engine cannot distinguish a PERMANENT failure (bad enum —
will never succeed) from a TRANSIENT one (graph contention — retry helps).
Both surface identically:

- `ToolResult.failure(code, msg)` → `Registry.invoke` records the error on the
  Invocation and unwraps the wire return to `result.data` = `None`
  (`capability.py:682`) → `engine._wire` returns `{"result": None}`
  (`engine.py:388`) → the sandbox `call_tool` caller sees a bare `None`.

A bare `None` carries no code, no message, no retry guidance. So the caller's
only safe move is to retry everything, and 32% of the "provenance moat" becomes
retry-storm noise.

## Design

### 1. Severity vocabulary (engine-level, fixed)

`code` stays a free string per Spec 001's ADR ("closed enums fragment across
capabilities"). Severity is a SEPARATE, small, fixed axis that classifies the
*retry semantics* of a failure — it does not partition the capability surface,
so it does not fragment. Three values (string constants in
`agency/toolresult.py`, mirroring `Codes`):

| `Severity` | meaning | caller action |
|---|---|---|
| `permanent` | validation / enum / schema / not-found / gate — retry NEVER helps | fix the input; do not retry |
| `transient` | contention / IO / timeout / boundary — retry MAY help | retry with backoff |
| `fatal` | internal invariant violation / unexpected crash | abort the batch; needs a fix |

### 2. `TypedError.severity`

`TypedError` gains `severity: str = ""` (frozen, additive, orthogonal to
`code`). Property `retryable` → `severity == Severity.TRANSIENT`. Empty
severity means "not yet classified" and is treated as `permanent` by the
`retryable` property (conservative: an unclassified failure is not retried).

### 3. `classify_severity(code, *, exc=None, message="")`

Pure function mapping a free-string `code` (and optionally the raising
exception / message) to a severity:

- **permanent**: `INVALID_ARGUMENT`, `validation_failed`, `not_found`,
  `gate_failed`, `unsupported`, `AMENDMENT_*`, `SKILL_PARSE_INVALID`,
  `PHASE_MISSING_FIELD`, `PHASE_UNKNOWN_KIND`, and any code/message containing
  `not in` / `invalid` / `unknown` / `required` / `missing` / `enum`.
- **transient**: `boundary_error`, and exception/message patterns for known
  contention/IO: `Failed to set property 'vfrom'`, `database is locked`,
  `OperationalError`, `TimeoutError`, `OSError`, `IOError`, `ConnectionError`.
- **fatal**: `internal`, plus any exception type not matched above
  (`KeyError`, `AttributeError`, `TypeError`, … — an engine bug, not a
  caller-fixable input).
- **unknown code, no exception → `permanent`** (documented default: the
  failure mode we are fixing is over-retrying, so the safe default is "do not
  retry"; a genuinely transient code should be added to the transient set).

### 4. `ToolResult.failure(code, message, *, severity=None, …)`

When `severity is None`, derive via `classify_severity(code, message=message)`.
An explicit `severity=` wins. The attached `TypedError` carries it.

### 5. `Registry.invoke` records severity

Two recording sites:

- **ToolResult failure path** (`capability.py:664-666`): record
  `error_severity` (from `result.error.severity`, re-classifying if empty)
  alongside the existing `error` prop on the Invocation.
- **Caught-exception path** (`capability.py:641`): classify the exception
  (`classify_severity("", exc=e, message=str(e))`) and record
  `error_severity`. The known `Failed to set property 'vfrom' on edge N`
  contention thus records `transient`.

The Invocation node now carries `error_severity` → a census can separate the
~600 permanent retries from real signal (partial Workstream E).

### 6. Wire surfacing (compatibility break — authorized)

`engine._wire.impl` — after `reg.invoke`, read the recorded Invocation node;
when `outcome == 'failed'`, return a typed error envelope instead of
`{"result": None}`:

```json
{"ok": false,
 "error": {"code": "INVALID_ARGUMENT",
           "message": "pov='…' not in [...]",
           "severity": "permanent",
           "retryable": false,
           "trace_id": "invocation:7acab598"}}
```

The success path is unchanged. `reg.invoke`'s internal `(data, inv)` contract is
unchanged (`data` is still `None` on failure), so the 41 tests reading
`memory.recall(inv).get("error")` stay green — only the WIRE shape changes.

### 7. `retry_transient` primitive

`agency/_retry.py`: `retry_transient(call, *, attempts=4, backoff=2.0,
sleep=time.sleep)` runs `call()`; if the return is a wire error envelope with
`severity == transient`, retries with exponential backoff up to `attempts`;
`permanent`/`fatal` → return immediately. The correct replacement for the
ingest's blind 40× loop. `sleep` is injectable so tests run instantly.

## Tests (RED → GREEN)

`tests/test_error_severity.py`:

1. `classify_severity("INVALID_ARGUMENT") == "permanent"` (replay create_scene).
2. enum-style message `"pov='…' not in [...]"` → permanent.
3. `classify_severity("", exc=RuntimeError("Failed to set property 'vfrom' on edge 5")) == "transient"`.
4. `classify_severity("", exc=KeyError("x")) == "fatal"`.
5. unknown code `"weird_code"` → permanent (documented default).
6. `ToolResult.failure("INVALID_ARGUMENT","m").error.severity == "permanent"` and `.retryable is False`.
7. explicit `severity="transient"` override wins and `.retryable is True`.
8. `reg.invoke` on a real `create_scene` bad-`pov` failure records
   `error_severity='permanent'` on the Invocation (replays the exact kohaerenz scenario).
9. exception path: a verb that raises the contention RuntimeError records
   `error_severity='transient'`.
10. wire path (`engine` execute of a bad-`pov` `create_scene`) returns
    `{"ok": False, "error": {"severity": "permanent", "retryable": False, …}}`.
11. `retry_transient`: a permanent-failing call is invoked exactly ONCE;
    a transient-failing call is invoked `attempts` times.

## Acceptance (scoped to Workstream A)

- Every failure carries a severity (classified or explicit).
- Provenance records `error_severity` — the moat distinguishes permanent
  retries from real signal.
- The wire surfaces severity so a caller branches and stops retrying permanent
  failures (would have prevented ~600 of the 626 evidence failures).
- `retry_transient` ships as the correct retry primitive.
- The exact evidence scenarios (`pov`, `domain='canon'`, codex `kind`)
  classify `permanent` in regression tests.

## Migration

Additive only. The seeded v0.1.0 graph is untouched; old Invocations simply
lack `error_severity`. An opt-in backfill (`classify_severity` over each old
Invocation's stored `error` string) is documented but NOT run against the
read-only evidence DB.

## Followup — Implementation Status (2026-06-13)

- **Done (15 tests, `tests/test_error_severity.py`, full suite 2258 green, drift exit 0):**
  - `agency/toolresult.py` — `Severity` (permanent/transient/fatal),
    `classify_severity(code, *, exc, message)`, `TypedError.severity` +
    `retryable` property, `ToolResult.failure(..., severity=None)` derivation.
  - `agency/capability.py:638-651` — `Registry.invoke` caught-exception path
    classifies + records `error_severity` (contention `vfrom` → transient).
  - `agency/capability.py:670-679` — ToolResult-failure path records
    `error_severity` (re-classifies if the verb omitted it).
  - `agency/engine.py` — `Engine._shape_wire_result(result, inv)` extracted
    from `_wire.impl`; failure now returns the typed envelope (compat break).
  - `agency/_retry.py` — `retry_transient(call, attempts, backoff, sleep)`.
  - Evidence replay: `pov` enum + `domain='canon'` classify `permanent`;
    contention exception classifies `transient`; wire surfaces severity.
- **Still (separate specs / workstreams):**
  - **B** — `get_schema` enum-member surfacing + non-lossy projected-enum
    typing for `SCENE_POV`.
  - **C** — durable PRECEDES batch writes (atomic node+edge; the 12/97 drop).
  - **D** — `create_storyform` verb + Character ontology.
  - **E** — provenance hygiene: dedupe/suppress permanent-failure retries
    (now classifiable via `error_severity`).
  - **F** — capture materialized chapter files as Artefact nodes.
- **Migration note:** additive only. An opt-in backfill that classifies each
  old Invocation's stored `error` string into `error_severity` is documented
  here but deliberately NOT run against the read-only evidence DB.

## Workstream close-out (A–H, 2026-06-13)

The originating prompt scoped **A–H**, not A–F. Honest final status:

- **A** error taxonomy — ✅ shipped (this spec).
- **B** enum discoverability + non-lossy SCENE_POV — ✅ shipped (Spec 284):
  the `param_enums` surfacing mechanism + the audit APPLIED to every named
  closed enum — `create_scene.pov` (projected), `capture_claim.domain`
  (RESEARCH_DOMAINS, the 60× bucket), `create_codex_entry.kind`
  (CODEX_ENTRY_KIND, the 49× bucket), `set_novel_status`/`set_chapter_status`
  status, `create_world_axiom.severity`, `reflect.note.scope`. Test:
  `test_projected_enum.test_evidence_enums_surface_in_get_schema`.
- **C** durable writes — ✅ shipped (this spec, Workstream C).
- **D** (1) Storyform verb — ✅ shipped (Spec 103 Slice 2). (2) Character
  ontology — **DEFERRED to Spec 138** (plural-character-system, drafted): a
  full ontology slice, out of scope for the hardening pass; characters stay
  CodexEntry stand-ins until then (documented carve-out).
- **E** provenance hygiene — **DECIDED + coordinated.** Decision: permanent-
  failure retries should be **deduped, not suppressed** — record the FIRST
  permanent failure (audit needs one record) and increment a `retry_count` on
  it for identical repeats `(capability, verb, error)` SERVING the same intent,
  rather than minting N duplicate Invocations (the 513-for-1 noise). It is NOT
  implemented inline here: the dedup decision belongs in the parallel OOP
  refactor's `InvocationRecorder` component (PR #141 coordination) — that
  component's literal responsibility is "what to record", and changing
  `Registry.invoke`'s recording now would collide with its active
  decomposition + risk invocation-count regressions. Lands on that seam.
- **F** graph/disk Artefact bridge — ✅ Slice 1 shipped (Spec 283); auto-hook
  Slice 2 coordinated onto the same refactor seam.
- **G** ergonomics — ✅ shipped: `agency_welcome.sandbox_constraints`
  (≤50 call_tool/block, no file I/O, partial-write persistence) + the install
  CLAUDE.md snippet's code-mode section. Tests in `test_install_verb.py`.
- **H** walker/gate UX — ✅ shipped: the hard-gate pause (`skill.py`) +
  `develop._skill_walk` now return `resume_from` (the PHASE NAME),
  `resume_with` (the outputs), and a `hint` naming the exact resume call —
  no more bare `blocked_on: gate-id`. Test:
  `test_skill_walk_part_b.test_hard_gate_pause_carries_resume_from_and_hint`.

**Acceptance re-run (ingest_canon.py → <2% failed) is a kohaerenz-side
validation** against a fresh graph — not run here (the evidence DB is
read-only); the engine-side fixes that enable it are all shipped above.
