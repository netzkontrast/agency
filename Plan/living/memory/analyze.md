---
capability: analyze
pillar: memory
vision_goals: []        # TODO(why-author): which GOALS.md goals this serves
status: living
last_generated: 2026-06-13
sources: []             # TODO(why-author): archived Plan/_archive/NNN specs that built this
---

# analyze — Analyze runs decidable transforms over source and reports findings on the quality, security, performance, and architecture axes as graph nodes the orchestrator can reason about, rather than prose opinions (memory pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
_TODO: authored intent._

## Verbs (generated · 9)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `analyze.architecture` | transform | path | Dependency-graph + structural checks: import cycles, file LOC thresholds. |
| `analyze.cleanup` | act | path · dry_run | Focused mode: analyse for dead-code findings only, draft a patch plan. |
| `analyze.graph` | transform | node_type · scope · limit | Query the provenance graph — a census of node types + a typed listing (read the graph). |
| `analyze.improve` | act | **analysis_id** · axes · apply | Read prior Analysis findings, draft an improvement plan as a Reflection. |
| `analyze.paths` | transform | root_intent_id · max_paths | Spec 048 intent-path analysis: long chains + verb sequences. |
| `analyze.performance` | transform | path · lang | AST-based hot-path lint: nested O(n²), += in loop, unbounded while True. |
| `analyze.quality` | transform | path · lang | Decidable lint findings: unused imports, long lines, long functions, long files. |
| `analyze.run` | act | path · axes · lang | Run the requested axes; record an Analysis + per-Finding nodes. |
| `analyze.security` | transform | path · lang | Decidable security patterns: eval/exec, hardcoded credentials, pickle.load, shell=True. |

## Ontology (generated)

**Nodes:** `Analysis`(path, axes, started_at) · `Finding`(rule, severity, file, line, message, evidence)
**Edges:** `CLEANS` · `HAS_FINDING` · `IMPROVES`
**Enums:** `('Finding', 'severity')` ∈ {fail, info, warn} · `('Analysis', 'axis')` ∈ {architecture, paths, performance, quality, security}

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/analyze -->
