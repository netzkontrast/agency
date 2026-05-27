---
spec_id: 001
slug: toolresult-and-typed-errors
status: draft
owner: "@agency"
depends_on: []
affects:
  - agency/capability.py
  - agency/engine.py
  - agency/capabilities/jules.py
  - agency/capabilities/delegate.py
  - agency/capabilities/gate.py
  - agency/capabilities/workspace.py
  - agency/capabilities/branch.py
  - agency/capabilities/subagent.py
  - agency/capabilities/plugin.py
  - agency/capabilities/reflect.py
  - agency/capabilities/develop.py
  - agency/capabilities/skill_generator.py
  - tests/test_agency.py
source-repos:
  - https://github.com/netzkontrast/the-agency-system.git @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22
  - https://github.com/SuperClaude-Org/SuperClaude_Framework.git @ 226c45cc93b865108843a669c6545d421784b68c
estimated_jules_sessions: 2
domain: cross
wave: A
---

> **Jules: read `Plan/JULES_PROTOCOL.md` before starting** (if present; otherwise
> follow the repo's contribution rules in `CLAUDE.md`). Run the gates in order:
> (1) Confidence ≥ 0.90, (2) TDD Red-Green-Refactor, (3) Evidence pasted under
> `## Evidence`, (4) Self-Review answered.
> Branch: `claude/extract-agency-plugin-o4JRc`. PRs target `main`. Only modify
> paths under `affects:` below. Additive commits; never rewrite history or
> force-push.
> If anything is ambiguous, open a draft PR labelled `[BLOCKED: clarification]`
> and stop — do not guess. Every guessable decision is parked under
> `## Open Questions / Needs Research`; answer those before coding the affected part.

# Spec 001 — Unified `ToolResult` Envelope + Typed Errors

## Why

The PR1 engine exposes a clean external surface (`search` · `get_schema` ·
`execute`; `agency/engine.py:1-16`), but **internally every capability verb
returns an ad-hoc dict**, and there are at least three incompatible shapes in the
tree today:

1. **Raw payload dicts** — `jules.dispatch` returns
   `{"status", "session", "url", "artefact"}` (`agency/capabilities/jules.py:80-89`);
   `jules.status`/`list`/`activities`/`plan` return whatever the backend returns.
2. **`{"result": {...}}` wrappers** — `delegate.fan_out`/`join`
   (`agency/capabilities/delegate.py:55-56,81`), `gate.check`
   (`agency/capabilities/gate.py:32`), `workspace.isolate`/`baseline`
   (`agency/capabilities/workspace.py:34,49`), `branch.assess`/`finish`
   (`agency/capabilities/branch.py:36,48`), `subagent.develop`
   (`agency/capabilities/subagent.py:39`).
3. **Stringly-typed error dicts** — `jules.stop` returns
   `{"error": "unsupported", ...}` (`agency/capabilities/jules.py:130-136`);
   `gate.check`, `delegate.fan_out`, `workspace.*`, `branch.finish` all return
   `{"result": {"error": "<free text>", ...}}` on the failure path. Failures that
   *raise* are captured by `Registry.invoke` as a **string**:
   `{"outcome": "failed", "error": f"{type(e).__name__}: {e}"}`
   (`agency/capability.py:174-175`).

`FINDINGS.md` names this the #1 rewrite vector: *"if the engine cannot reliably
distinguish a failed action, a requirement for more data, or a successfully
completed phase without complex heuristic string matching, the orchestration
layer will collapse"* (`research/oo-architecture/FINDINGS.md:21-24`). The
precedent is `the-agency-system`'s shared-envelope decision
(`vendor/the-agency-system/Plan/decisions/0005-shared-toolresult-envelope.md`) and
its repair-authority tiers
(`vendor/the-agency-system/Plan/decisions/0011-repair-authority-tiers.md`), which
need a typed error code to route a failure to the right tier. `PROPOSAL.md §1` and
`§4` sketch the target `ToolResult` and `TypedError` dataclasses
(`research/oo-architecture/PROPOSAL.md:5-42,129-167`).

The hard constraint: **code-mode IS the contract**. Tools are wired by reflection
in `Engine._wire` (`agency/engine.py:61-89`), and `_wire`'s `impl` already
unwraps `result["result"]` and re-wraps non-dicts as `{"result": out}`
(`agency/engine.py:73-74`). `Registry.invoke` additionally sniffs
`result["artefact"]` to record a `PRODUCES` edge (`agency/capability.py:177-179`).
A `ToolResult` envelope must thread through **both** seams without breaking the
JSON shape an `execute()` caller already relies on. This spec introduces the
envelope as the canonical *internal* verb return type and defines exactly how it
serialises at the `_wire` boundary.

## Done When

- [ ] `ToolResult` is a frozen-ish dataclass in `agency/capability.py` with fields
      `ok: bool`, `data: dict | None`, `warnings: list[str]`,
      `next_suggested_tools: list[str]`, `error: TypedError | None`, plus an
      `artefact: dict | None` field (preserves the `Registry.invoke` PRODUCES hook).
- [ ] `TypedError` is a dataclass with `code: ErrorCode` (an `Enum`),
      `message: str`, `context: dict | None`; `ErrorCode` covers at minimum
      `VALIDATION_FAILED`, `DEPENDENCY_MISSING`, `GATE_FAILED`, `NOT_FOUND`,
      `UNSUPPORTED`, `BOUNDARY_ERROR`, `INTERNAL` (final list resolved in Open Q-1).
- [ ] `ToolResult` has `to_dict()` producing a stable JSON-serialisable mapping and
      `from_dict()` round-tripping it; `TypedError.to_dict()`/`from_dict()` likewise.
      `assert ToolResult.from_dict(r.to_dict()) == r` holds for every constructed
      result in the test suite.
- [ ] Convenience constructors exist: `ToolResult.success(**data)` /
      `ToolResult.ok_with(data=..., warnings=..., next_suggested_tools=...,
      artefact=...)` and `ToolResult.failure(code, message, **context)`.
- [ ] `Registry.invoke` (`agency/capability.py:144-180`) accepts a `ToolResult`
      from a verb: it reads `.artefact` for the `PRODUCES` edge (replacing the
      `result["artefact"]` dict-sniff at `:177`) and, when a verb returns
      `ToolResult(ok=False, error=...)` **without raising**, records
      `{"outcome": "failed", "error": error.code.value, "error_message":
      error.message}` on the Invocation (typed, not the stringly-typed capture at
      `:174-175`). A raised exception still records a failed Invocation and
      re-raises (behaviour preserved; the string capture stays only for the
      raised-exception path — see Open Q-4).
- [ ] `Engine._wire`'s `impl` (`agency/engine.py:69-74`) serialises a `ToolResult`
      return via `.to_dict()` so the MCP/code-mode JSON shape is deterministic and
      documented. The exact wire shape is decided in Open Q-2; the implementation
      must match whatever that resolves to and a test must pin it.
- [ ] At least one verb per capability is migrated to return `ToolResult`:
      `jules.dispatch` and `jules.stop` (the raw-dict and error-dict exemplars),
      `gate.check`, `delegate.fan_out`, `branch.finish` — and the migration pattern
      is documented in the module docstrings so the remaining verbs follow it.
- [ ] `tests/test_agency.py` keeps passing (currently 56) and gains tests for:
      (a) `ToolResult`/`TypedError` round-trip, (b) `Registry.invoke` records a
      typed `error.code` for a non-raising `ok=False` return, (c) `Registry.invoke`
      still records `PRODUCES` from `ToolResult.artefact`, (d) `_wire` serialises a
      `ToolResult` to the pinned wire shape, (e) the success path of a migrated verb
      is unchanged at the JSON boundary (regression guard against Open Q-2).
- [ ] No verb anywhere returns a bare `{"error": ...}` or `{"result": {"error":
      ...}}` once migrated; failures go through `ToolResult.failure(...)`.

## Source clones (run first)

```bash
git clone --depth=1 https://github.com/netzkontrast/the-agency-system.git \
  ~/work/vendor/the-agency-system        # SHA 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22
git clone --depth=1 https://github.com/SuperClaude-Org/SuperClaude_Framework.git \
  ~/work/vendor/superclaude-framework     # SHA 226c45cc93b865108843a669c6545d421784b68c
```

Read `~/work/vendor/the-agency-system/Plan/decisions/0005-shared-toolresult-envelope.md`
for the envelope-field rationale and `.../0011-repair-authority-tiers.md` for the
error-code → repair-tier mapping that motivates `ErrorCode`. Do not copy code;
consume the design only.

## Design

### `agency/capability.py` — the envelope + typed error

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ErrorCode(Enum):
    VALIDATION_FAILED = "validation_failed"   # bad/insufficient input to a verb
    DEPENDENCY_MISSING = "dependency_missing" # a prerequisite (env var, prior node) absent
    GATE_FAILED = "gate_failed"               # a programmatic hard-gate predicate returned False
    NOT_FOUND = "not_found"                   # a referenced node/session/workspace is unknown
    UNSUPPORTED = "unsupported"               # the boundary API does not expose this op (e.g. jules.stop)
    BOUNDARY_ERROR = "boundary_error"         # an injected Driver/boundary failed (subprocess, HTTP, ...)
    INTERNAL = "internal"                     # an unexpected raise captured by Registry.invoke
    # NOTE: final set + repair-tier mapping is Open Q-1.


@dataclass
class TypedError:
    code: ErrorCode
    message: str
    context: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code.value, "message": self.message,
                "context": self.context or {}}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TypedError":
        return cls(code=ErrorCode(d["code"]), message=d["message"],
                   context=d.get("context") or None)


@dataclass
class ToolResult:
    ok: bool
    data: Optional[dict[str, Any]] = None
    warnings: list[str] = field(default_factory=list)
    next_suggested_tools: list[str] = field(default_factory=list)
    error: Optional[TypedError] = None
    # carried through to Registry.invoke so a successful verb can still emit a
    # PRODUCES edge (replaces today's result["artefact"] dict-sniff).
    artefact: Optional[dict[str, Any]] = None

    # --- constructors -------------------------------------------------------
    @classmethod
    def success(cls, *, data: Optional[dict] = None, warnings: Optional[list] = None,
                next_suggested_tools: Optional[list] = None,
                artefact: Optional[dict] = None) -> "ToolResult":
        return cls(ok=True, data=data or {}, warnings=warnings or [],
                   next_suggested_tools=next_suggested_tools or [], artefact=artefact)

    @classmethod
    def failure(cls, code: ErrorCode, message: str, *,
                warnings: Optional[list] = None, **context) -> "ToolResult":
        return cls(ok=False, warnings=warnings or [],
                   error=TypedError(code, message, context or None))

    # --- serialisation (the wire boundary; see Open Q-2) --------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "data": self.data or {},
            "warnings": list(self.warnings),
            "next_suggested_tools": list(self.next_suggested_tools),
            "error": self.error.to_dict() if self.error else None,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ToolResult":
        err = d.get("error")
        return cls(ok=d["ok"], data=d.get("data") or {},
                   warnings=list(d.get("warnings") or []),
                   next_suggested_tools=list(d.get("next_suggested_tools") or []),
                   error=TypedError.from_dict(err) if err else None)
```

> `artefact` is intentionally **not** in `to_dict()` — it is a provenance signal
> consumed by `Registry.invoke`, never surfaced to the caller (mirrors today's
> behaviour where `artefact` is stripped from the user payload). Confirm in Open Q-3.

### `Registry.invoke` migration (`agency/capability.py:144-180`)

```python
# ... after `inv = memory.record("Invocation", {...})` and the SERVES link ...
try:
    result = spec["fn"](**call)
except Exception as e:                                  # raised-exception path: unchanged shape today
    memory.update(inv, {"outcome": "failed",
                        "error_code": ErrorCode.INTERNAL.value,
                        "error": f"{type(e).__name__}: {e}"})
    raise

if isinstance(result, ToolResult):
    if not result.ok and result.error is not None:      # NON-raising typed failure
        memory.update(inv, {"outcome": "failed",
                            "error_code": result.error.code.value,
                            "error_message": result.error.message})
    if result.artefact:                                 # PRODUCES from the envelope
        art = memory.record("Artefact", dict(result.artefact))
        memory.link(inv, art, "PRODUCES")
    return result, inv

# legacy dict path retained until every verb is migrated (Open Q-5: keep or drop?)
if isinstance(result, dict) and result.get("artefact"):
    art = memory.record("Artefact", dict(result["artefact"]))
    memory.link(inv, art, "PRODUCES")
return result, inv
```

### `Engine._wire` migration (`agency/engine.py:69-74`)

```python
def impl(**kwargs):
    intent_id = kwargs.pop("intent_id")
    agent_id = kwargs.pop("agent_id", "") or None
    result, _ = reg.invoke(mem, intent_id, cap_name, verb, agent_id=agent_id, **kwargs)
    if isinstance(result, ToolResult):
        return result.to_dict()                 # the pinned code-mode wire shape — see Open Q-2
    # legacy unwrap (existing behaviour) until all verbs migrate:
    out = result["result"] if isinstance(result, dict) and "result" in result else result
    return out if isinstance(out, dict) else {"result": out}
```

### Before / After — `jules.dispatch` (`agency/capabilities/jules.py:79-89`)

**Before:**
```python
@verb(role="effect")
def dispatch(self, source: str, starting_branch: str, prompt: str) -> dict:
    "Spawn a remote Jules session (external effect). Returns its id/url/state."
    s = self._backend().create(prompt=prompt, source=source, starting_branch=starting_branch)
    sid = s.get("id") or s.get("name")
    return {
        "status": s.get("state", "submitted"),
        "session": sid,
        "url": s.get("url"),
        "artefact": {"kind": "jules-session", "session": sid or "", "url": s.get("url") or ""},
    }
```

**After:**
```python
@verb(role="effect")
def dispatch(self, source: str, starting_branch: str, prompt: str) -> ToolResult:
    "Spawn a remote Jules session (external effect). Returns its id/url/state."
    s = self._backend().create(prompt=prompt, source=source, starting_branch=starting_branch)
    sid = s.get("id") or s.get("name")
    if not sid:                                        # backend gave us nothing actionable
        return ToolResult.failure(ErrorCode.BOUNDARY_ERROR,
                                  "Jules backend returned no session id", raw=s)
    return ToolResult.success(
        data={"status": s.get("state", "submitted"), "session": sid, "url": s.get("url")},
        artefact={"kind": "jules-session", "session": sid, "url": s.get("url") or ""},
        next_suggested_tools=["capability_jules_status", "capability_jules_verify"])
```

### Before / After — `jules.stop` (the stringly-typed error, `:124-136`)

**Before:** `return {"error": "unsupported", "session": session, "message": "..."}`

**After:**
```python
return ToolResult.failure(
    ErrorCode.UNSUPPORTED,
    "The Jules v1alpha API has no session cancellation. Use `message` to ask the "
    "agent to stand down, or wait for COMPLETED/FAILED.",
    session=session,
    next_suggested_tools=["capability_jules_message"])  # passed via warnings/context — see Open Q-1
```

### Migration of the `{"result": {...}}` wrapper verbs

`delegate`/`gate`/`workspace`/`branch`/`subagent` currently wrap in
`{"result": {...}}` *specifically so* `_wire`'s unwrap (`engine.py:73`) hands the
inner dict to the caller. Under `ToolResult` that wrapper is replaced by
`ToolResult.success(data={...})`; the error branches (e.g.
`gate.py:26-27`, `delegate.py:34,37`, `branch.py:42`, `workspace.py:30-31,41-42`)
become `ToolResult.failure(ErrorCode.X, ...)`. A `gate.check(passed=False)` is a
domain outcome, **not** an error — it stays `ok=True` with the failure encoded in
`data`; only a *malformed call* (cross-intent lifecycle) returns
`ToolResult.failure(GATE_FAILED|VALIDATION_FAILED, ...)`. Resolve the
gate-semantics ambiguity in Open Q-6.

## Files

- **Modify** `agency/capability.py`: add `ErrorCode`, `TypedError`, `ToolResult`;
  migrate `Registry.invoke` to read `ToolResult.artefact`/`.error`.
- **Modify** `agency/engine.py`: `_wire.impl` serialises `ToolResult` via `to_dict()`.
- **Modify** `agency/capabilities/jules.py`: migrate `dispatch`, `stop` (+ document
  the pattern for the read verbs).
- **Modify** `agency/capabilities/{gate,delegate,branch,workspace,subagent}.py`:
  migrate the listed exemplar verbs; convert `{"result": {"error": ...}}` to
  `ToolResult.failure`.
- **Modify** `agency/capabilities/{plugin,reflect,develop,skill_generator}.py`:
  migrate remaining verbs to `ToolResult` (follow-up within this spec; can be a
  second Jules session).
- **Modify** `tests/test_agency.py`: add the round-trip, typed-error provenance,
  PRODUCES-from-envelope, and `_wire` wire-shape tests.
- **Create**: none (envelope lives in the existing `capability.py`, per `PROPOSAL.md §1`).

## Open Questions / Needs Research

1. **Final `ErrorCode` set + repair-tier mapping.** The enum above is a proposal.
   `the-agency-system` 0011-repair-authority-tiers maps error classes to repair
   tiers — should `ErrorCode` carry a `tier` so the engine's loop-recovery can
   route automatically, or is tier a separate concern? Also: where do
   `next_suggested_tools` live on a *failure* (top-level field vs. inside
   `TypedError.context`)? The `jules.stop` after-sketch shows the tension.
2. **Does serialising `ToolResult.to_dict()` at `_wire` break the code-mode return
   contract?** Today an `execute()` caller receives the *inner* dict (e.g.
   `gate.check` yields `{"passed": ..., "gate": ...}`). After migration it would
   receive `{"ok": true, "data": {"passed": ..., "gate": ...}, "warnings": [...],
   ...}`. Is that acceptable, or must `_wire` keep returning the unwrapped `data`
   for back-compat and surface `ok`/`error` some other way? **This is the single
   load-bearing decision** — it determines whether 001 is additive or breaking for
   existing `execute()` scripts and the bash CLI (`agency/cli.py`).
3. **Should `artefact` be excluded from `to_dict()`?** Proposed yes (provenance-only,
   matches today's stripping). Confirm no caller needs the artefact in the payload.
4. **Raised exceptions vs. returned failures.** Should verbs ever raise, or must all
   failures be returned as `ToolResult.failure`? If raising stays legal, the
   `Registry.invoke` exception path records `ErrorCode.INTERNAL` — is that the right
   default, or should specific exception types map to specific codes?
5. **Legacy-dict coexistence window.** Keep `Registry.invoke` / `_wire` dual-path
   (dict + `ToolResult`) until every verb migrates, or migrate all verbs in this
   spec and drop the legacy branches? Affects whether `plugin/reflect/develop/
   skill_generator` migration is in-scope-mandatory or follow-up.
6. **`gate.check(passed=False)` — `ok` or not-`ok`?** A failed gate is a real domain
   outcome that records `BLOCKED_ON` provenance, not a tool error. Proposal:
   `ok=True`, failure in `data`, and reserve `ErrorCode.GATE_FAILED` for callers who
   *want* a hard stop. Maintainer to confirm.
7. **Frozen dataclass?** `ToolResult` with mutable `list` defaults can't be
   `frozen=True` trivially. Acceptable to leave mutable, or require immutability
   (tuples + `frozen=True`)?

## Evidence

- `agency/capability.py:144-180` — `Registry.invoke`: the Invocation record, the
  `result["artefact"]` PRODUCES sniff (`:177-179`), the stringly-typed failure
  capture (`:174-175`).
- `agency/engine.py:61-89` — `_wire`; the `result["result"]` unwrap + non-dict
  re-wrap at `:73-74` (the code-mode wire boundary).
- `agency/capabilities/jules.py:79-89,124-136` — `dispatch` raw-dict return +
  `artefact`; `stop` stringly-typed `{"error": "unsupported"}`.
- `agency/capabilities/delegate.py:34,37,55-56,81`, `gate.py:26-27,32`,
  `workspace.py:30-34,41-49`, `branch.py:36,42-48`, `subagent.py:39` — the
  `{"result": {...}}` wrapper + `{"result": {"error": ...}}` failure idiom.
- `research/oo-architecture/FINDINGS.md:13-24` — ad-hoc return types + stringly-typed
  errors named as the rewrite vector.
- `research/oo-architecture/PROPOSAL.md:5-42,129-167` — `ToolResult` (§1) and
  `TypedError` (§4) sketches + before/after.
- `vendor/the-agency-system/Plan/decisions/0005-shared-toolresult-envelope.md`,
  `.../0011-repair-authority-tiers.md` @ `0a6a9e71f6c26bc120a8fc1db02f8990b7916f22`.
