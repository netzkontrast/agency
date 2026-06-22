---
name: memory
description: "Use when you need to understand or work with Memory — agency's bi-temporal graph where every node, edge, and revision is recorded (never overwritten), giving a session queryable provenance via record/recall/link instead of a one-shot transcript."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: pillar v1 -->

# Memory pillar

Memory is the fourth of agency's four concepts (Intent · Capability · Lifecycle ·
Memory) and the substrate the other three are written into. It is a bi-temporal
graph: every fact carries BOTH when it was true in the world (valid time) and when
it was recorded (transaction time). Nothing is overwritten — a new value is a new
revision; the old one is retained. Reads resolve "latest `recorded_at` wins," so
you see current truth while the full history stays queryable (keep-both, Spec 292).

Three primitives. `record` writes a typed node (Intent, Invocation, Artefact,
Skill, Decision, …) with a deterministic id so a re-record is an upsert, not a
duplicate. `link` draws a typed edge between nodes (SERVES, PRODUCES, HAS_PHASE,
CONFORMS_TO, …). `recall` queries them back. Because every verb invocation records
its own provenance — an Invocation that SERVES the intent, an Artefact that the
invocation PRODUCES — the graph accumulates a walkable record of WHY each thing
exists. That provenance moat is the moat: a raw-tool action leaves no trace and is
lost when the session ends; a verb action is queryable forever.

Edges are load-bearing, not decoration: a declared edge must be TRAVERSED
(`neighbors(node_id, edge)`), never simulated by scanning a label and filtering a
foreign-key prop in Python. Declare an edge ⇒ walk it.

## When to use

- Recording a fact, artefact, or decision so it survives the session — `record` + `link`.
- Asking "why does X exist / what served this intent?" — `recall` / provenance walk.
- Relating two nodes — `link` a typed edge, then traverse it via `neighbors`.

## When not to use

- Ephemeral scratch state within a single call — a local variable, not a graph write.

## Example

```python
# Record an artefact and link it to the intent it serves (provenance).
nid = await call_tool("capability_reflect_note",
                      {"intent_id": iid, "agent_id": "agent:me",
                       "scope": "observation", "text": "<lesson>"})
```

A Reflection node written into the bi-temporal graph, linked back to the
intent — recoverable later via a provenance walk, not lost with the session.
