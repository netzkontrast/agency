# ToolResult — the return envelope

<!-- doc-source: agency/toolresult.py -->
<!-- doc-hash: e7e3c888f8c80adf -->

`agency/toolresult.py` defines the in-sandbox return envelope (Spec 001/059). A verb may
return a plain `dict` (simple path) or a `ToolResult` (when it needs typed errors,
warnings, artefacts, or pagination).

## `ToolResult`

```python
ToolResult.success(data=…, warnings=[…], artefacts_written=[…], next_cursor=…)
ToolResult.failure(code="GATE_FAILED", message="…")
```

Fields: `data` (the primary return), `ok`, `warnings`, `next_suggested_tools`, `error`
(a `TypedError`), `artefacts_written`, `archived_to`, `trace_id`, `next_cursor`.

## How the Registry handles it

`Registry.invoke` (see [capability-system.md](capability-system.md)) **unwraps** a
`ToolResult`:

- `ok=False` / an attached `error` → the Invocation's `outcome` becomes `failed`, with
  `error = "{code}: {message}"`; the **caller receives `None`** (the lean wire shape) and
  the typed failure lives on the provenance node.
- `warnings` / `archived_to` → recorded on the Invocation.
- `artefacts_written` (file paths) → `Artefact{kind:file}` nodes + `PRODUCES` edges.
- `error.trace_id` is stamped to the Invocation id when the verb didn't supply one — so
  a failure is traceable in one provenance hop.

## `TypedError`

`{code, message, trace_id, context}`. `code` is a **free string**, not a closed enum
(per the-agency-system's ADR — closed enums fragment across capabilities). Conventions:
`GATE_FAILED`, `DEPENDENCY_MISSING`, `INVALID_ARGUMENT`, `NOT_FOUND`, `INTERNAL`.

## Why both shapes

The plain-dict path keeps trivial verbs trivial; the `ToolResult` path gives the verbs
that need it typed failures + artefact provenance **without** widening the wire — after
unwrap, the wire still sees only `.data`. `act` verbs that produce a document return
`data={"result": …, "artefact": {…}}` so the `PRODUCES` edge fires.
