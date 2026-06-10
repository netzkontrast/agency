---
spec_id: "203"
slug: analyze-graph-query-language
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "084"
depends_on: ["084", "125", "147", "146"]
vision_goals: [2, 1]
affects:
  - agency/capabilities/analyze/_main.py
  - tests/test_analyze_graph_query.py
---

# Spec 203 — analyze.graph query language (NL → traversal)

## Why

Spec 084 ships `analyze.graph` (census of node labels + typed listing) —
"code-mode's read-the-graph surface". It answers structural questions
(how many Intents, list Invocations) but not RELATIONAL ones ("every
action that SERVES intent Q1, the agent that ran it, the gate it
passed" — the exact provenance-moat query GOALS.md Goal 2 promises).
Spec 125 gives `ctx.neighbors` (one hop). This spec adds a bounded
query surface, and — with the Spec 147 Driver — an NL→traversal
front-end so an agent can ask the moat question in plain language.

## Done When

- [ ] **`analyze.graph_query(pattern)`** — a bounded traversal DSL
      (start label + edge path + filter) returning the matched subgraph,
      built on `ctx.neighbors` (Spec 125) so it stays one-hop-composable.
- [ ] **Optional NL front-end** — the Spec 147 Driver compiles a plain-
      language question into a `graph_query` pattern
      (`output_config.format`); degrades to the DSL without `[anthropic]`.
- [ ] **The GOALS.md moat query works** — "actions SERVING intent X +
      their agent + their gate" returns in one call.
- [ ] **Result honors the output budget** (Spec 146/154).
- [ ] Test: the moat query returns the expected subgraph on a fixture;
      NL compiles to the right pattern (mocked Driver).
- [ ] TODO row + drift clean.

## Interconnects

- Spec 125 (neighbors) is the traversal primitive.
- **LLM-driver chain** (147) — NL front-end · **output-budget** (146).
- This is the queryable face of the provenance moat (Goal 2).

## Open questions

1. Full Cypher or a bounded DSL? **Recommend**: bounded DSL (the engine
   already speaks Cypher internally; expose a safe subset).
