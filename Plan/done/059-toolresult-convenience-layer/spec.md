---
spec_id: "059"
slug: toolresult-convenience-layer
status: complete   # 2026-06-03: Codes + .success/.failure + trace_id stamp + next_cursor + doctrine
state: done
last_updated: 2026-06-03
owner: "@agency"
depends_on: ["001", "019"]
affects:
  - agency/toolresult.py                 # add Codes, .success/.failure, document context
  - agency/capability.py                 # Registry.invoke stamps error.trace_id via dataclasses.replace
  - docs/vision/CAPABILITY-AUTHORING.md  # "When to use ToolResult vs plain dict" addendum
  - tests/test_toolresult_convenience.py # NEW
estimated_jules_sessions: 0
domain: substrate
wave: 4
---

# Spec 059 — ToolResult convenience layer

## Why

Spec 001 shipped `ToolResult` + `TypedError` as Option C — an INTERNAL
Python envelope that `Registry.invoke` unwraps to `.data` before the
wire. Spec 019 then settled the plain-dict wire shape for the 90% of
verbs that never adopted `ToolResult`. That leaves a small carry-over
of useful work that was scoped into Spec 001 but didn't ship with the
original deliverable:

1. **`Codes` namespace** — string-constant sugar so call sites read
   `ToolResult.failure(Codes.UNSUPPORTED, ...)` instead of bare strings.
2. **`.success()` / `.failure()` convenience constructors** — verb-side
   code is cleaner without the full kwarg dance.
3. **`trace_id` stamping** — `Registry.invoke` should write `inv` (the
   recorded Invocation id) onto a returned `TypedError`'s `trace_id`
   field so a failure is joinable to its provenance in one hop. With
   `frozen=True` on the dataclass this means `dataclasses.replace()`.
4. **`next_cursor` field** — opt-in pagination metadata for verbs that
   return a paged data slice.
5. **"When to use `ToolResult` vs plain dict" doctrine** — a section in
   CAPABILITY-AUTHORING.md so future authors don't agonize. Pairs with
   Spec 016 Hint #7's docstring contract and Spec 019's wire-shape rule.

Each is small (< 30 LOC), low-risk, and high carry. Bundled in one spec
so the convenience layer ships coherently rather than as five drips.

## Done When

- [ ] **`agency/toolresult.py` gains a `Codes` namespace** with the
  string constants used today (free-string discipline preserved):
  ```python
  class Codes:
      VALIDATION_FAILED = "validation_failed"
      DEPENDENCY_MISSING = "dependency_missing"
      GATE_FAILED = "gate_failed"
      NOT_FOUND = "not_found"
      UNSUPPORTED = "unsupported"
      BOUNDARY_ERROR = "boundary_error"
      INTERNAL = "internal"
      UNSPECIFIED = "unspecified"
  ```
  Non-binding — `TypedError.code` accepts any string.
- [ ] **`ToolResult.success(*, data, warnings, next_suggested_tools,
  artefacts_written, archived_to, next_cursor) -> ToolResult`** —
  keyword-only constructor for the success path.
- [ ] **`ToolResult.failure(code, message, *, warnings, trace_id) ->
  ToolResult`** — sets `ok=False` and wires the `TypedError`. `trace_id`
  is left as-is when supplied; otherwise `Registry.invoke` stamps it.
- [ ] **`Registry.invoke` stamps `error.trace_id = inv` via
  `dataclasses.replace`** when the returned `ToolResult` carries a
  `TypedError` without an existing `trace_id`. The replace pattern
  honors `frozen=True` on the dataclass (Spec 001 Q-7 trade-off).
- [ ] **`next_cursor: Optional[str] = None`** lands on `ToolResult` as
  an opt-in field for paginated read verbs.
- [ ] **`docs/vision/CAPABILITY-AUTHORING.md` gains "When to use
  `ToolResult` vs plain dict"** — short section:
  > **Default: plain dict + Spec 019 wire-shape contract.** Use
  > `ToolResult` when the verb has ≥ 2 of: typed failure modes that need
  > a structured `code`, warnings that should appear on the Invocation
  > node, `archived_to` (Spec 005 context-mode overflow), or
  > `artefacts_written` paths that drive `PRODUCES` edges.
- [ ] **`tests/test_toolresult_convenience.py`** — 6 tests:
  - `Codes.UNSUPPORTED == "unsupported"` (lock the canonical strings).
  - `ToolResult.success(data={...})` returns `ok=True` with the right
    field values.
  - `ToolResult.failure(Codes.UNSUPPORTED, "msg")` returns `ok=False`
    with `error.code == "unsupported"` and `error.message == "msg"`.
  - `Registry.invoke` stamps `error.trace_id = <inv>` on a returned
    `ToolResult.failure` without trace_id.
  - `Registry.invoke` preserves a caller-supplied `trace_id` (doesn't
    overwrite).
  - `next_cursor` round-trips through `ToolResult.success(next_cursor=
    "abc")`.
- [ ] `python -m pytest -q -n auto -m "not e2e"` stays green.

## Design

### `dataclasses.replace` for trace_id stamping

Spec 001 Q-7 noted that `frozen=True` on `ToolResult` / `TypedError`
prevents in-place mutation. The convenience layer resolves it by using
`dataclasses.replace`:

```python
# agency/capability.py — inside Registry.invoke, after the ToolResult check
from dataclasses import replace
if not result.ok and result.error and not result.error.trace_id:
    new_error = replace(result.error, trace_id=inv)
    result = replace(result, error=new_error)
```

Two replaces because both dataclasses are frozen. Cheap (no copies of
the `list` defaults — `replace` shares references), explicit, and
preserves Spec 001's freeze discipline.

### `success` / `failure` keyword-only signatures

```python
@classmethod
def success(cls, *, data: Any = None,
            warnings: Optional[list] = None,
            next_suggested_tools: Optional[list] = None,
            artefacts_written: Optional[list] = None,
            archived_to: str = "",
            next_cursor: Optional[str] = None) -> "ToolResult":
    return cls(
        data=data, ok=True,
        warnings=warnings or [],
        next_suggested_tools=next_suggested_tools or [],
        artefacts_written=artefacts_written or [],
        archived_to=archived_to,
        next_cursor=next_cursor,
    )

@classmethod
def failure(cls, code: str, message: str, *,
            warnings: Optional[list] = None,
            trace_id: str = "") -> "ToolResult":
    return cls(
        data=None, ok=False,
        warnings=warnings or [],
        error=TypedError(code=code, message=message, trace_id=trace_id),
    )
```

Note: `data=None` on failure (the current dataclass requires it). Callers
that want extra failure context use `TypedError.context: dict` (the
existing field — Spec 001 dropped it in the original draft but the
shipped code added it; this spec acknowledges + documents the field
rather than removing it).

### Doctrine addendum example

```
## When to use `ToolResult` vs plain dict (Spec 059)

**Default: plain dict + Spec 019 wire-shape contract.**

Use `ToolResult` when the verb has ≥ 2 of:
- Typed failure modes that need a structured `code` (not just
  `{"error": "..."}`).
- Warnings that should appear on the Invocation node (Memory.update
  reads `result.warnings` and stores them).
- `archived_to` — the verb's primary return is >4 KB and Spec 005's
  context-mode middleware archives the body.
- `artefacts_written` — the verb writes one or more files that need
  `PRODUCES` edges (Registry.invoke derives them automatically).

If none of the above apply, return a plain dict and document the wire
shape per Spec 019.
```

## Files

- **Create:**
  - `tests/test_toolresult_convenience.py`.
- **Modify:**
  - `agency/toolresult.py` — add `Codes`, `.success`, `.failure`,
    `next_cursor`.
  - `agency/capability.py` — `Registry.invoke` stamps `error.trace_id`
    via `dataclasses.replace`.
  - `docs/vision/CAPABILITY-AUTHORING.md` — new section.

## Open Questions

1. **`Codes.context` — keep or drop the `TypedError.context: dict`
   field?** Spec 001 dropped it in the original draft; the shipped code
   added it back. Recommend KEEP — verbs use it for per-failure context
   that doesn't fit `message` (e.g. `{"missing": [...], "extras":
   [...]}`). The convenience layer documents it; no code change.

2. **Should `.failure` take `**context` kwargs that flow into
   `TypedError.context`?** Would let `ToolResult.failure(code, msg,
   missing=[...], extras=[...])`. Recommend NO — too magical;
   `ToolResult.failure(code, msg)` paired with explicit
   `TypedError(context={...})` is clearer.

3. **Does the doctrine block in CAPABILITY-AUTHORING.md belong here OR
   in Spec 019 as an addendum?** Recommend HERE — Spec 019 codifies the
   wire-shape contract for plain dicts; Spec 059 codifies when to step
   outside that default. Separate concerns.

## Evidence (cites)

- Spec 001 §"Followup — Superseded by Spec 019 + carry-over to Spec
  059 (2026-06-03)" — the supersede marker that names this spec as the
  carry-over target.
- Spec 019 — the wire-shape contract for plain dicts that this spec
  pairs with.
- `agency/toolresult.py` (current) — `ToolResult` + `TypedError` as
  shipped under Option C; this spec extends, never replaces.
- `agency/capability.py:357-386` — the `ToolResult` unwrap path that
  this spec extends with the `error.trace_id` stamp.
- GOALS.md goal #7 ("graph is the store; files are a rendered view")
  — the doctrinal grounding for the supersede pattern that birthed
  this spec.
- CLAUDE.md Rule #4 (TODO.md sync) — this spec's draft row already
  landed in TODO.md alongside the supersede marker on Spec 001.

## Followup — Shipped (2026-06-03)

**Verdict:** Shipped.

### Done
- **`Codes` namespace** landed in `agency/toolresult.py` with the 8
  canonical constants: VALIDATION_FAILED, DEPENDENCY_MISSING,
  GATE_FAILED, NOT_FOUND, UNSUPPORTED, BOUNDARY_ERROR, INTERNAL,
  UNSPECIFIED. Non-binding (`code` accepts any string per Spec 001's
  free-string discipline).
- **`ToolResult.success(...)`** keyword-only constructor — sets
  `ok=True`, defaults the list fields to fresh empties, accepts
  `data` / `warnings` / `next_suggested_tools` / `artefacts_written`
  / `archived_to` / `next_cursor`.
- **`ToolResult.failure(code, message, ...)`** keyword-only constructor
  — sets `ok=False`, builds the attached `TypedError` inline. The
  optional `trace_id` kwarg lets callers pre-stamp; otherwise
  `Registry.invoke` fills it.
- **`Registry.invoke` stamps `error.trace_id = inv`** via
  `dataclasses.replace` when the returned `ToolResult.error` carries an
  empty `trace_id`. Honors `frozen=True` on both dataclasses by
  rebuilding rather than mutating. The caller's explicit `trace_id`
  wins (the stamp only fills the empty case).
- **`next_cursor: Optional[str] = None`** opt-in field added to the
  `ToolResult` dataclass — paginated read verbs use it.
- **CAPABILITY-AUTHORING.md §"When to use `ToolResult` vs plain dict"**
  — new section between Spec 019 (§"Wire shape vs internal wrap") and
  Spec 016 Hint #8 (§"Universal input-required convention"). Pairs the
  decision rule ("≥ 2 of: typed failure modes / warnings / archived_to /
  artefacts_written → ToolResult; otherwise plain dict") with examples
  from `jules.dispatch` (ToolResult) and `branch.assess` (plain dict).

### Tests (tests/test_toolresult_convenience.py — 6 tests)
- `Codes.UNSUPPORTED == "unsupported"` + 7 sibling string-constant locks.
- `ToolResult.success(data={...}, warnings=[...])` returns `ok=True`
  with correct field values.
- `ToolResult.success(data=[...], next_cursor="abc")` round-trips the
  opt-in pagination field.
- `ToolResult.failure(Codes.UNSUPPORTED, "nope")` returns `ok=False`
  with the right `TypedError` shape.
- `Registry.invoke` stamps `error.trace_id` on a returned failure
  without trace_id (Invocation outcome=failed reads the typed error).
- `Registry.invoke` preserves a caller-supplied `trace_id` verbatim
  (the stamp only fills the empty case).

### Live measurements
- `pytest -q tests/test_toolresult_convenience.py`: 6/6 green in 0.62s.

### Cluster-coherence (Spec 047)
- C12 (Capability Authoring) — completes the carry-over from Spec 001
  so the "when to use ToolResult" decision tree is now documented
  doctrine alongside Spec 016/019/023 lint rules.
- C13 (Plugin/MCP Authoring) — `Registry.invoke`'s trace_id stamp
  closes the audit-trail gap from Spec 001's Q-7 frozen-dataclass
  trade-off; failures are now provenance-joinable in one hop.
