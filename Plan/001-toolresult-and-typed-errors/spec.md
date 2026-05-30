---
spec_id: 001
slug: toolresult-and-typed-errors
status: done
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
layer will collapse"* (`research/oo-architecture/FINDINGS.md:21-24`).

**The precedent — and the authoritative schema this spec adopts — is
`the-agency-system`'s shipped `ToolResult` envelope** (ADR-0005
`Plan/decisions/0005-shared-toolresult-envelope.md`; schema canvas §5,
`docs/superpowers/specs/_drafts/2026-05-19-agency-base-canvas.md:156-179`). That
envelope is *already* hand-rolled in every shipped handler
(`servers/agency-mcp/.../handlers/shared/skills.py:47-54`,
`.../shared/search.py:85-87,132-134`, `.../shared/config.py:16-34`,
`.../shared/session.py:21-92`). Its field set is the source of truth for this
spec:

```
required: ok, warnings, artefacts_written
optional: data, next_suggested_tools, error, archived_to   (+ next_cursor for read verbs)
```

Two corrections to the original draft, made after reconciling against the source:

- **There is no closed `ErrorCode` enum and no `tier` in the source.** The
  source's `error` sub-object is `{code: string, message: string, trace_id?:
  string}` (canvas §5 `:168-176`) — `code` is a **free string** (real values
  `"unsupported"`, `"illegal_transition"`, `"PRE_DRAFTING_GATES_FAILED"`,
  `"NOT_IMPLEMENTED"`, `"MANIFEST_DRIFT"`). ADR-0011 (repair-authority tiers,
  `Plan/decisions/0011-repair-authority-tiers.md:17-48`; `VOCABULARY.md:269-280`)
  classifies **document/code mutations** into T1-T4 — it is change-governance,
  **not** a runtime error→recovery-tier map. The earlier draft conflated the two;
  there is no source-sanctioned `tier` on errors. This spec drops it.
- **`artefacts_written: list[str]` is on the wire** (canvas §5, every handler),
  not a private singular `artefact` dict stripped from the payload. It carries the
  caller-visible "what did this write" contract; the engine's `PRODUCES` edge is
  *derived from it*, not from a smuggled side channel.

ADR-0005 is `adr_status: Proposed` and ships via a `@domain_tool` decorator that
agency does **not** adopt: agency's `Engine._wire` reflection seam
(`agency/engine.py:61-89`) already centralises emission, so this spec serialises
the envelope at `_wire` instead of decorating each verb. This is a deliberate
divergence from ADR-0005's enforcement surface, not from its schema.

**Scope guard (canon).** `ToolResult`/`TypedError` are an **Engine-substrate
return SERIALIZER** (CORE.md:90 category — "a serializer detail, not a top-level
concern"), **NOT a fifth concept** (the concepts are exactly four, CORE.md:7) and
**NOT the verb input-schema**. The schema-as-single-source isomorphism — one
ontology schema per verb rendering three ways (MCP `inputSchema` / Skill
frontmatter / bash arg parser, CORE.md:64-73) — is a **separate, untouched axis**
(spec 004's ladder). This spec is the *output/return* contract only; do not
conflate `ToolResult.to_dict()` with "the schema."

The hard constraint: **code-mode IS the contract**. Tools are wired by reflection
in `Engine._wire`, and `_wire`'s `impl` already unwraps `result["result"]` and
re-wraps non-dicts as `{"result": out}` (`agency/engine.py:73-74`).
`Registry.invoke` additionally sniffs `result["artefact"]` to record a `PRODUCES`
edge (`agency/capability.py:177-179`). The envelope must thread through **both**
seams. Per ADR-0005's own "Neutral" clause — *"the schema does not change the MCP
wire format; clients see the same JSON shape they always did"* (`:90`) — **the
envelope IS the wire shape**: callers read `data`. Agency's current unwrapping at
`_wire` is the deviation to migrate *away* from (see Q-2).

**The canon's two boundaries (CORE.md:11-13).** Code-mode distinguishes two
distinct boundaries, and the envelope lives on the first one only:

1. The **in-sandbox `call_tool` boundary** — what a verb returns to the Python the
   agent runs *inside* `execute`. The canon places **no leanness constraint** here:
   these are "intermediate results [that] stay in-sandbox." The `ToolResult`
   envelope lives here as an intermediate value; `_wire` is reached only as
   `await call_tool(...)` from inside `execute` (`specs/engine.md:30-31`), so its
   return is an in-sandbox value. The envelope does **NOT auto-cross into context.**
2. The **context boundary** — what `execute` *itself* returns. Only here does
   "only deltas cross into context" apply, and that delta is whatever the agent's
   code chooses to return after reading `r["ok"]`/`r["data"]` and filtering
   in-sandbox.

Serializing the full envelope at `_wire` therefore crosses boundary 1 (no leanness
constraint) and **never** boundary 2. The lean surface
(`search`/`get_schema`/`execute`) is untouched.

## Done When

- [ ] `ToolResult` is a dataclass in `agency/capability.py` whose fields match the
      **source schema**: `ok: bool`, `data: Any = None` (NOT `dict` — read verbs
      return lists, e.g. `skills.py:49` `data: limited_skills`), `warnings:
      list[str]`, `artefacts_written: list[str]`, `next_suggested_tools:
      list[str]`, `error: TypedError | None`, `archived_to: str | None`, and
      `next_cursor: str | None` (shipped for paginating read verbs,
      `skills.py:45,52`).
- [ ] `TypedError` is a dataclass with `code: str` (a **free string**, not a closed
      enum), `message: str`, `trace_id: str | None` (NOT `context`). A non-binding
      `Codes` namespace of common string constants (`"validation_failed"`,
      `"dependency_missing"`, `"not_found"`, `"unsupported"`, `"boundary_error"`,
      `"internal"`, …) may be provided as call-site sugar, but `code` accepts any
      string so source-style values (`"illegal_transition"`) are never rejected.
      Whether agency upgrades to a closed enum later is Open Q-1 — default is the
      free string.
- [ ] `trace_id` is the `Invocation` node id: `Registry.invoke` wires `inv` into
      any returned `TypedError` that does not already carry one, so a failure is
      joinable to its provenance in the bi-temporal graph.
- [ ] `ToolResult.to_dict()` produces the **full wire envelope** (every field
      above, including `artefacts_written`, `next_cursor`, `archived_to`) and
      `from_dict()` round-trips it; `TypedError.to_dict()`/`from_dict()` likewise.
      `assert ToolResult.from_dict(r.to_dict()) == r` holds for every constructed
      result in the test suite — the round-trip is **lossless-aware**: no wire
      field is dropped (the original draft's `artefact`-excluded-from-`to_dict()`
      trick is removed precisely because it broke this invariant).
- [ ] Convenience constructors exist: `ToolResult.success(data=..., warnings=...,
      next_suggested_tools=..., artefacts_written=..., next_cursor=...)` and
      `ToolResult.failure(code, message, *, warnings=..., trace_id=...)`.
- [ ] `Registry.invoke` (`agency/capability.py:144-180`) accepts a `ToolResult`
      from a verb and records provenance correctly across **three** cases:
      - `ok=False` **with** a `TypedError` (non-raising typed failure) →
        `{"outcome": "failed", "error_code": error.code, "error_message":
        error.message}`, after stamping `error.trace_id = inv` if unset.
      - `ok=False` **without** an `error` object (warnings-only soft failure — the
        source does this routinely, `handlers/novel/promo.py:14,59,65,69`) → still
        recorded as `{"outcome": "failed", "error_code": "unspecified",
        "warnings": [...]}`. This must NOT be mis-recorded as a success; the
        condition keys off `not result.ok`, **not** off `result.error is not None`.
      - `ok=True` → success; if `artefacts_written` is non-empty, record an
        `Artefact` per entry and link `PRODUCES` (replacing the
        `result["artefact"]` dict-sniff at `:177-179`).
      A raised exception still records a failed Invocation with a default
      `error_code="internal"` and re-raises (behaviour preserved; the string
      capture stays only for the raised-exception path — see Open Q-4).
- [ ] `Engine._wire`'s `impl` (`agency/engine.py:69-74`) serialises a `ToolResult`
      return via `.to_dict()` so the MCP/code-mode JSON shape is the full,
      deterministic, documented envelope. The migration target (full envelope on
      the in-sandbox `call_tool` return, callers read `data`) is the
      canon-faithful resolution of Open Q-2; the accept-the-break-vs-dual-surface
      call is the maintainer's, and tests pin **both** the success and failure
      wire shapes.
- [ ] **bash↔MCP isomorphism test.** `agency/cli.py` and the MCP `_wire` path emit
      a **byte-identical** `ToolResult.to_dict()` envelope for the same call — this
      is the canon's litmus for the "three isomorphic renderings" (CORE.md:13-17;
      `specs/engine.md:33-34`), so the bash-only agent (Jules) reads `ok`/`data`
      identically to an MCP client.
- [ ] At least one verb per capability is migrated to return `ToolResult`:
      `jules.dispatch` and `jules.stop` (the raw-dict and error-dict exemplars),
      `gate.check`, `delegate.fan_out`, `branch.finish` — and the migration pattern
      is documented in the module docstrings so the remaining verbs follow it.
- [ ] `tests/test_agency.py` keeps passing (currently 56) and gains tests for:
      (a) `ToolResult`/`TypedError` lossless round-trip incl. `artefacts_written`,
      `next_cursor`, `archived_to`; (b) `Registry.invoke` records `error_code` for a
      non-raising `ok=False` **with** error; (c) `Registry.invoke` records a failed
      Invocation for `ok=False` **without** error (warnings-only); (d)
      `Registry.invoke` records `PRODUCES` from `artefacts_written`; (e) `_wire`
      serialises a `ToolResult` to the full pinned wire shape; (f) `trace_id` on a
      returned failure equals the `Invocation` id; (g) the migrated success path is
      the full envelope at the JSON boundary (regression guard for Open Q-2).
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
for the envelope rationale and the authoritative schema at
`~/work/vendor/the-agency-system/docs/superpowers/specs/_drafts/2026-05-19-agency-base-canvas.md:156-179`.
Read `.../Plan/decisions/0011-repair-authority-tiers.md` only to confirm it governs
**document-change authority (T1-T4)**, NOT runtime error tiers — do not derive an
`ErrorCode.tier` from it. Do not copy code; consume the design only.
(Path note: `~/work/vendor/...` is the clone target; this repo has no `vendor/`
directory — cite the clone path, not a `vendor/` path inside agency.)

## Design

### `agency/capability.py` — the envelope + typed error

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


# Non-binding call-site sugar. `code` is a FREE STRING (source uses inconsistent
# values by design: "unsupported", "illegal_transition", "PRE_DRAFTING_GATES_FAILED").
# These constants are conveniences, not a closed set; any string is legal.
class Codes:
    VALIDATION_FAILED = "validation_failed"
    DEPENDENCY_MISSING = "dependency_missing"
    GATE_FAILED = "gate_failed"
    NOT_FOUND = "not_found"
    UNSUPPORTED = "unsupported"
    BOUNDARY_ERROR = "boundary_error"
    INTERNAL = "internal"
    UNSPECIFIED = "unspecified"       # ok=False with no structured error (warnings-only)


@dataclass
class TypedError:
    code: str                          # free string (source canvas §5 :168-176)
    message: str
    trace_id: Optional[str] = None     # the Invocation id; stamped by Registry.invoke

    def to_dict(self) -> dict[str, Any]:
        d = {"code": self.code, "message": self.message}
        if self.trace_id is not None:
            d["trace_id"] = self.trace_id
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TypedError":
        return cls(code=d["code"], message=d["message"], trace_id=d.get("trace_id"))


@dataclass
class ToolResult:
    ok: bool
    # `data` is unconstrained in the source schema (canvas §5 :164) — read verbs
    # return a LIST (skills.py:49 `data: limited_skills`), write verbs a dict.
    data: Any = None
    warnings: list[str] = field(default_factory=list)
    # ON THE WIRE (source: required field, every handler). The PRODUCES edge is
    # derived from this — it is NOT a private provenance channel.
    artefacts_written: list[str] = field(default_factory=list)
    next_suggested_tools: list[str] = field(default_factory=list)
    error: Optional[TypedError] = None
    archived_to: Optional[str] = None  # set when a >4 KB body is trimmed (ADR-0005 :69)
    next_cursor: Optional[str] = None  # pagination for read verbs (skills.py:45,52)

    # --- constructors -------------------------------------------------------
    @classmethod
    def success(cls, *, data: Any = None, warnings: Optional[list] = None,
                next_suggested_tools: Optional[list] = None,
                artefacts_written: Optional[list] = None,
                next_cursor: Optional[str] = None) -> "ToolResult":
        return cls(ok=True, data=data, warnings=warnings or [],
                   next_suggested_tools=next_suggested_tools or [],
                   artefacts_written=artefacts_written or [], next_cursor=next_cursor)

    @classmethod
    def failure(cls, code: str, message: str, *,
                warnings: Optional[list] = None,
                trace_id: Optional[str] = None) -> "ToolResult":
        return cls(ok=False, warnings=warnings or [],
                   error=TypedError(code, message, trace_id))

    # --- serialisation: the FULL envelope IS the wire shape (Q-2; ADR-0005 :90) --
    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "ok": self.ok,
            "data": self.data,
            "warnings": list(self.warnings),
            "artefacts_written": list(self.artefacts_written),
            "next_suggested_tools": list(self.next_suggested_tools),
            "error": self.error.to_dict() if self.error else None,
        }
        if self.archived_to is not None:
            d["archived_to"] = self.archived_to
        if self.next_cursor is not None:
            d["next_cursor"] = self.next_cursor
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ToolResult":
        err = d.get("error")
        return cls(ok=d["ok"], data=d.get("data"),
                   warnings=list(d.get("warnings") or []),
                   artefacts_written=list(d.get("artefacts_written") or []),
                   next_suggested_tools=list(d.get("next_suggested_tools") or []),
                   error=TypedError.from_dict(err) if err else None,
                   archived_to=d.get("archived_to"),
                   next_cursor=d.get("next_cursor"))
```

> `archived_to` reserves ADR-0005's oversize-body trim (`:69`, `:79`): the
> decorator there routes any return body > 4 KB to the spec-117 archive and
> replaces it with a pointer. Agency reserves the field now; the >4 KB intercept
> at `_wire` (or `Registry.invoke`) is a follow-up spec, but for an engine that
> fans out across child lifecycles (`delegate.fan_out`) the field must exist on
> the wire from day one or it reproduces the exact token sink ADR-0005 closed.

### `Registry.invoke` migration (`agency/capability.py:144-180`)

```python
# ... after `inv = memory.record("Invocation", {...})` and the SERVES link ...
try:
    result = spec["fn"](**call)
except Exception as e:                                   # raised path: shape preserved
    memory.update(inv, {"outcome": "failed",
                        "error_code": Codes.INTERNAL,
                        "error": f"{type(e).__name__}: {e}"})
    raise

if isinstance(result, ToolResult):
    if not result.ok:                                    # keys off ok, NOT off error
        if result.error is not None:
            if result.error.trace_id is None:            # thread the provenance id
                result.error.trace_id = inv
            memory.update(inv, {"outcome": "failed",
                                "error_code": result.error.code,
                                "error_message": result.error.message})
        else:                                            # warnings-only soft failure
            memory.update(inv, {"outcome": "failed",     # (promo.py:14 pattern)
                                "error_code": Codes.UNSPECIFIED,
                                "warnings": list(result.warnings)})
    for path in (result.artefacts_written or []):        # PRODUCES from the wire field
        art = memory.record("Artefact", {"path": path})
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
        return result.to_dict()                  # FULL envelope on the wire — see Q-2
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
        return ToolResult.failure(Codes.BOUNDARY_ERROR,
                                  "Jules backend returned no session id")
    return ToolResult.success(
        data={"status": s.get("state", "submitted"), "session": sid, "url": s.get("url")},
        artefacts_written=[f"jules-session:{sid}"])    # on the wire; PRODUCES derives from it
    # next_suggested_tools is a forward-looking router hook (ADR-0005 :58); always []
    # in the shipped source today — leave it at its empty default, do NOT block on it.
```

### Before / After — `jules.stop` (the stringly-typed error, `:124-136`)

**Before:** `return {"error": "unsupported", "session": session, "message": "..."}`

**After:**
```python
return ToolResult.failure(
    Codes.UNSUPPORTED,
    "The Jules v1alpha API has no session cancellation. Use `message` to ask the "
    "agent to stand down, or wait for COMPLETED/FAILED.")
# Note: `code="unsupported"` matches the source's real value verbatim
# (handlers/jules/lifecycle.py:476). No next_suggested_tools on the failure path —
# the field stays top-level + empty (Q-1 resolved: it does NOT live in error context).
```

### Migration of the `{"result": {...}}` wrapper verbs

`delegate`/`gate`/`workspace`/`branch`/`subagent` currently wrap in
`{"result": {...}}` *specifically so* `_wire`'s unwrap (`engine.py:73`) hands the
inner dict to the caller. Under `ToolResult` that wrapper is replaced by
`ToolResult.success(data={...})`; the error branches (e.g.
`gate.py:26-27`, `delegate.py:34,37`, `branch.py:42`, `workspace.py:30-31,41-42`)
become `ToolResult.failure(code, ...)`. A `gate.check(passed=False)` is a
domain outcome, **not** an error — it stays `ok=True` with the failure encoded in
`data` (source-confirmed: domain outcomes are `ok=True` with the result in `data`;
only an *illegal* call is `ok=False`, `handlers/novel/status.py`). Reserve
`code="gate_failed"` only for callers who *want* a hard stop on a malformed
cross-intent call. **Q-6 is closed: the proposal is source-aligned.**

## Files

- **Modify** `agency/capability.py`: add `Codes`, `TypedError`, `ToolResult`;
  migrate `Registry.invoke` to derive PRODUCES from `artefacts_written`, handle the
  three `ok`/`error` cases, and stamp `trace_id = inv`.
- **Modify** `agency/engine.py`: `_wire.impl` serialises `ToolResult` via
  `to_dict()` (full envelope on the wire).
- **Modify** `agency/capabilities/jules.py`: migrate `dispatch`, `stop` (+ document
  the pattern for the read verbs — they return `data` as a list and may carry
  `next_cursor`).
- **Modify** `agency/capabilities/{gate,delegate,branch,workspace,subagent}.py`:
  migrate the listed exemplar verbs; convert `{"result": {"error": ...}}` to
  `ToolResult.failure`.
- **Modify** `agency/capabilities/{plugin,reflect,develop,skill_generator}.py`:
  migrate remaining verbs to `ToolResult` (follow-up within this spec; can be a
  second Jules session).
- **Modify** `tests/test_agency.py`: add the lossless round-trip, typed-error +
  warnings-only provenance, PRODUCES-from-`artefacts_written`, `trace_id`, and
  `_wire` full-envelope wire-shape tests.
- **Create**: none (envelope lives in the existing `capability.py`).

## Open Questions / Needs Research

1. **Free-string `code` vs. a closed enum (RESOLVED to the source default; the
   upgrade is the only open part).** The source uses a **free string** `code`
   (canvas §5 `:168-176`) with no closed enum and **no `tier`** — ADR-0011's
   T1-T4 tiers govern *document-change authority*, not runtime error recovery
   (`0011:17-48`, `VOCABULARY.md:269-280`), so the earlier `ErrorCode.tier`
   premise is dropped. `next_suggested_tools` is a **top-level** field, always
   `[]` in the source, populated later — it does NOT live in error context.
   *Genuinely open:* whether agency later upgrades the free string to a closed,
   extensible enum for loop-recovery routing. Default for now: free string + the
   non-binding `Codes` sugar. Recommend deciding this in the spec that builds the
   recovery loop, not here.
2. **[THE load-bearing decision] Full envelope on the in-sandbox `call_tool`
   return — accept the break, or dual-surface during migration?** Today an
   in-sandbox `await call_tool(...)` resolves to the *inner* dict (e.g.
   `gate.check` → `{"passed": ..., "gate": ...}`). After migration it resolves to
   the full envelope `{"ok": true, "data": {...}, "warnings": [...],
   "artefacts_written": [...], ...}`.

   **This is a `call_tool`-boundary change, NOT a context-boundary change
   (CORE.md:11-13).** The envelope is an *intermediate, in-sandbox value* — the
   agent reads `r["ok"]`/`r["data"]`, joins/filters in-sandbox, and returns its own
   delta from `execute`. The envelope never auto-crosses into context; only
   `execute`'s chosen delta does. So the blast radius is **narrow**: it is
   **(a) `agency/cli.py`'s own result-printing/unwrap** and **(b) any in-sandbox
   snippet that assumes `call_tool` hands back the pre-unwrapped inner dict** — it
   is **NOT** "every `execute()` script," and it is **NOT** a break of the lean
   public surface (`search`/`get_schema`/`execute`).

   The canon and ADR-0005 agree on the target. CORE.md:11-13: intermediate
   `call_tool` results stay in-sandbox (no leanness constraint there); ADR-0005's
   "Neutral" clause (`:90`): *"the schema does not change the MCP wire format;
   clients see the same JSON shape they always did"* — the envelope **IS** the
   in-sandbox return shape and callers read `data`. Agency's current unwrapped
   inner dict is the deviation to migrate *away* from. **Q-2's resolution is
   canon-faithful: surface the full envelope on the `call_tool` return, callers
   read `data`.** The only open part is sequencing — the maintainer chooses
   **(a) accept the documented break now** (cleaner, canon-faithful; do the
   `cli.py` + in-sandbox-unwrap audit, NOT a per-script `execute()` audit)
   **vs. (b) dual-surface during migration** (keep unwrapping behind a flag until
   all verbs move, then flip). "Keep unwrapping forever" is **not** an option — it
   is unfaithful to the canon. Downstream specs **002/005/007 depend on this
   resolution and on the field name being `data`.** Pin both the success and
   failure in-sandbox wire shapes in tests, plus the bash↔MCP isomorphism test
   (Done-When) proving `cli.py` and `_wire` emit byte-identical envelopes.
3. **~~Exclude `artefact` from `to_dict()`?~~ MOOT — wrong question.** The source
   has no singular `artefact`; it ships `artefacts_written: list[str]` **on the
   wire** (canvas §5; every handler). It stays in `to_dict()` and the `PRODUCES`
   edge is derived from it. The earlier "strip artefact from the payload" approach
   is removed (it also broke the lossless round-trip invariant).
4. **Raised exceptions vs. returned failures.** Should verbs ever raise, or must
   all failures be returned as `ToolResult.failure`? No source equivalent (the
   source decorator wraps but does not specify raise-vs-return policy). Reasonable
   to keep raising legal and default the exception path to `code="internal"`;
   specific exception→code mapping is a nice-to-have, not blocking.
5. **Legacy-dict coexistence window.** Keep `Registry.invoke` / `_wire` dual-path
   (dict + `ToolResult`) until every verb migrates, or migrate all 12 verbs in
   this spec and drop the legacy branches? No source input. Recommend dual-path
   during this spec, drop legacy in a follow-up once `plugin/reflect/develop/
   skill_generator` are migrated.
6. **~~`gate.check(passed=False)` — `ok` or not-`ok`?~~ CONFIRMED → `ok=True`.**
   The source treats a domain outcome as `ok=True` with the result in `data`
   (`handlers/novel/status.py` dry-run is `ok=True`; only an illegal call is
   `ok=False`). A failed gate records `BLOCKED_ON` provenance and stays `ok=True`;
   reserve `code="gate_failed"` for a malformed call. Closed.
7. **Frozen dataclass?** `ToolResult` with mutable `list` defaults can't be
   `frozen=True` trivially, and `Registry.invoke` mutates `error.trace_id` in
   place — so the dataclass must stay mutable (or trace_id stamping must rebuild
   the object). Acceptable to leave mutable; note the trade-off.

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
- **Source schema (authoritative):**
  `~/work/vendor/the-agency-system/docs/superpowers/specs/_drafts/2026-05-19-agency-base-canvas.md:156-179`
  — `required: [ok, warnings, artefacts_written]`; optional `data` (any),
  `next_suggested_tools`, `error {code:str, message:str, trace_id?:str}`,
  `archived_to`.
- **Shipped hand-rolls (confirm the wire shape):**
  `servers/agency-mcp/.../handlers/shared/skills.py:45-53` (`data` as list +
  `next_cursor`), `.../shared/search.py:85-87,132-134`, `.../shared/config.py:16-34`,
  `.../shared/session.py:21-92`; `ok=False` warnings-only failures at
  `.../novel/promo.py:14,59,65,69`.
- `Plan/decisions/0005-shared-toolresult-envelope.md` (`adr_status: Proposed`;
  Neutral clause `:90`; `archived_to` / >4 KB trim `:69,:79`) and
  `.../0011-repair-authority-tiers.md:17-48` (T1-T4 = document-change governance,
  NOT error tiers) @ `0a6a9e71f6c26bc120a8fc1db02f8990b7916f22`.
