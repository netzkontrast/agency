---
slug: spec-tool-result-envelope
type: spec
status: ready
summary: The frozen four-key tool return envelope. Root is fixed; all variation lives inside `data`.
---

# 02 — Tool result envelope

Every tool returns this exact root. No keys are added at the root.

```json
{
  "ok": true,
  "data": {},
  "warnings": [],
  "next_suggested_tools": []
}
```

| Key | Type | Rule |
|---|---|---|
| `ok` | bool | required |
| `data` | object | required; ALWAYS an object (never primitive/array) |
| `warnings` | string[] | required; may be empty |
| `next_suggested_tools` | string[] | required; tool names in `mcp__…` form |

## All variation lives in `data`

Domain- and tool-specific payloads go inside `data`, validated by a per-tool
schema at `context/_shared/schemas/tools/<domain>_<row>_<export>.schema.json`.
Common idioms: `audit_trail`, `gate_state` (workflow); `provenance`,
`artefact_metadata`, `artefact_ref`, `emitted_edges` (context);
`dispatch_target` (agentic).

`artefact_metadata` and `artefact_ref` are distinct:

- `data.artefact_metadata` — the full `Artefact` node fields ([06](06-context-base.md));
  PostToolUse validates and ingests it to register/update a product.
- `data.artefact_ref` — a lean pointer to an already-registered `Artefact`'s
  bytes, returned in place of inline bytes when a payload would exceed the wire
  budget. It registers nothing on its own.

## Constraints

- Wire size target ≤ 4 KB. Oversized payloads write bytes via an artefact
  driver and reference them with `data.artefact_ref` (a pointer, not the bytes).
- The harness validates every envelope against `tool_result.schema.json` before
  returning it. A failure is wrapped as
  `{"ok": false, "data": {"error": {"code": "ENVELOPE_INVALID", ...}}, "warnings": [], "next_suggested_tools": []}`.
