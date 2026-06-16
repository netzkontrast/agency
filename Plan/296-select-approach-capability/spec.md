---
spec: 296
title: select-approach-capability
status: Partial (Slice 1 shipped)
depends_on: [040, 294, 295]
clusters: [develop, analyze]
vision_goals: [1, 4]
---

# Spec 296 — `select`: complexity-scored approach selection, first-class

> Third extract→spec→reimplement slice.

SuperClaude's `sc-select-tool` routes between its Serena/Morphllm MCP servers by
complexity scoring. Those servers aren't in agency — but the **generalizable**
idea is: decidably score an operation and route between **approach archetypes**.
Reimplemented natively, generalized away from SC's specific tools.

## Extracted understanding (from `sc-select-tool.md`)

- Multi-dimensional **complexity scoring** (file count, operation type, speed vs
  accuracy).
- **Direct mappings**: symbol/memory operations → semantic; pattern/bulk edits →
  fast pattern engine.
- **Thresholds**: score > 0.6 → semantic, < 0.4 → pattern, 0.4-0.6 →
  feature/native.
- **Fallback chain**: semantic → pattern → native.

## Design — generalized, decidable

Agency has no Serena/Morphllm, so archetypes generalize the trade-off:

| Approach | When | Trade-off |
|---|---|---|
| `semantic` | symbol/rename/refactor/navigate/memory ops | accurate, slower, structure-aware |
| `pattern` | bulk/regex/replace-across edits, speed priority | fast, less precise |
| `native` | middling/ambiguous ops | built-in tools, safe default |

`select.route(operation, file_count=1, speed_priority=False)` — decidable score
in [0,1] (semantic-ness) from operation keywords + file count + speed flag;
direct mappings (memory/context → semantic) override; threshold routing; returns
`{approach, score, confidence, rationale, fallback}` and records a `Selection`
node SERVING the intent. `select.archetypes()` lists the archetypes.

This complements `delegate.dispatch_decision` (inline-vs-dispatch) — it answers a
different question: *which approach* for the operation.

## Done-When

- [x] `route` computes a decidable semantic-ness score + threshold routing +
  direct-mapping overrides + a fallback chain.
- [x] `archetypes` lists the three approaches with their trade-offs.
- [x] `Selection` node + `(Selection, approach)` enum; records provenance;
  auto-registers.
- [x] Acceptance scenarios (symbol→semantic, bulk→pattern, speed flag bias,
  memory direct-mapping, provenance).
- [ ] **Follow-up:** next SuperClaude part (own spec).

## Followup — Implementation Status (2026-06-16)

**Done.** `agency/capabilities/select/` — `route` + `archetypes`; decidable
scoring; `Selection` node.

**Still.** Subsequent SuperClaude parts, each its own extract→spec→reimplement.
