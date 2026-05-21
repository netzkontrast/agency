---
slug: spec-gate
type: spec
status: ready
summary: Gate definition (YAML) and the evaluator return contract. A passing hard gate emits a SATISFIES_PHASE edge into the graph.
---

# 03 — Gate

A gate guards a phase. It lives at `workflow/<row>/gates/<id>.yaml`. The workflow
runner OWNS evaluation; the context PostToolUse hook INGESTS any emitted edge.

```yaml
id: research-complete           # ^[a-z][a-z0-9-]{0,60}$
type: hard-blocking             # hard-blocking | advisory
description: "…"                # optional
blocks_phase: "02"              # required when type=hard-blocking

evaluator:                      # required
  kind: callable                # callable | schema | sql | manual
  module: "agentic.jules.gates"
  callable: "research_complete"
  args: {}

on_success:
  emit_edge:
    type: SATISFIES_PHASE       # constant
    from: artefact              # node id, or "artefact"
    to: "phase/jules/02"
on_failure:
  message: "research not complete"
  fix_hint_tools: ["mcp__agentic_jules_research"]
```

## Evaluator return contract

Every evaluator returns exactly:

```python
{"ok": bool, "message": str}
```

On pass, the runner writes the `on_success.emit_edge` relation into
`tool_result.data.emitted_edges[]`; the context hook persists it. An advisory
gate never blocks — its result is surfaced as a warning.
