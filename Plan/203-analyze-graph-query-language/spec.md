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

- [ ] **`QueryResult` typed return** — `QueryResult = {pattern:
      QueryPattern, nodes: list[Node], edges: list[Edge],
      truncated: bool, total_matches: int, payload_tokens: int,
      driver_used: bool}` where `QueryPattern = {start_label,
      edge_path: list[EdgeStep], filter: dict, max_hops: int}` and
      `EdgeStep = {edge_type, direction: Literal["out","in","any"]}`.
- [ ] **`analyze.graph_query(pattern)`** — a bounded traversal DSL
      (start label + edge path + filter) returning the matched subgraph,
      built on `ctx.neighbors` (Spec 125) so it stays one-hop-composable;
      `max_hops <= MAX_HOPS_HARD` (default 6) — beyond fails fast.
- [ ] **Optional NL front-end** — the Spec 147 Driver compiles a plain-
      language question into a `QueryPattern` (`output_config.format`);
      degrades to the DSL without `[anthropic]`, surfacing
      `driver_used=false`.
- [ ] **Invariant — neighbors-composability** (relationship): the
      DSL's traversal SHALL be expressible as N composed
      `ctx.neighbors` calls; an audit walk validates `graph_query`
      result equals the composed-neighbors result for every pattern in
      a fixture set (Spec 125 doctrine — declare an edge ⇒ traverse it).
- [ ] **Invariant — moat-query correctness** (relationship): for the
      canonical GOALS.md moat query ("actions SERVING intent X + agent
      + gate"), the result satisfies
      `every(node, node.label in {"Invocation","Agent","Gate"})` AND
      `every(edge, edge.type in {"SERVES","RUNS","PASSED"})`. Drift in
      either set fails the invariant.
- [ ] **Invariant — output budget** (relationship): `payload_tokens <=
      MAX_QUERY_PAYLOAD_TOKENS` (Spec 146/154); on overflow,
      `truncated=true` AND `total_matches > len(nodes)` — never
      silently drop without signaling.
- [ ] **Invariant — NL→DSL determinism** (relationship): for a frozen
      NL question + a frozen capability set, the compiled pattern bytes
      are stable across calls within `NL_COMPILE_TTL` (default 1h);
      drift signals a Driver non-determinism bug.
- [ ] **Failure mode coverage** — Driver REFUSAL / TIMEOUT / pattern
      schema violation each return `driver_used=false` with a typed
      error_code, never crash the analyze call.
- [ ] Test: the moat query returns the expected subgraph on a fixture;
      NL compiles to the right pattern (mocked Driver); composability
      audit asserts neighbors-equivalence; overflow signals truncation.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a graph with Intent(id="Q1"), Invocation(id="i1") SERVES Q1,
        Agent(id="a1") RUNS i1, Gate(id="g1") PASSED by i1
        AND [anthropic] installed
When:   analyze.graph_query(
            NL="every action that SERVES intent Q1, the agent that ran
                it, the gate it passed") runs
Then:   driver compiles to QueryPattern{start_label:"Intent",
            edge_path:[{edge_type:"SERVES",direction:"in"},
                       {edge_type:"RUNS",direction:"in"},
                       {edge_type:"PASSED",direction:"in"}],
            filter:{id:"Q1"}, max_hops:3}
        AND QueryResult{nodes: 3 items, edges: 3 items,
            truncated:false, driver_used:true}

Given:  the same query bypassing the Driver (DSL-direct)
When:   analyze.graph_query(pattern=<that QueryPattern>) runs
Then:   result is IDENTICAL to the NL-compiled call's result
        (composability invariant) — proves NL→DSL is a transparent
        front-end, not a parallel surface

Given:  a query matching 5000 nodes with MAX_QUERY_PAYLOAD_TOKENS=8000
When:   analyze.graph_query runs
Then:   QueryResult{truncated:true, total_matches:5000, nodes:<bounded>}
        AND a follow-up call with cursor returns the next slice
        (never silently drops)
```

## Failure modes (Nygard)

| Failure | Query response |
|---|---|
| Driver `REFUSAL` (Spec 147) | `driver_used=false`, error_code:"REFUSAL"; user must supply DSL |
| Driver `TIMEOUT` | same — degrade to "please supply pattern explicitly" |
| Pattern schema invalid | typed `BAD_REQUEST{detail:"pattern"}` with the offending field |
| `max_hops` exceeded | typed `BAD_REQUEST{detail:"max_hops"}`; suggest a tighter filter |
| Filter references unknown label | typed `BAD_REQUEST{detail:"label"}` with valid set |
| Result exceeds payload budget | `truncated=true` + cursor; never silent truncation |
| Composability audit divergence | hard invariant fail — implementation bug, not transient |

## Interconnects

- Spec 125 (neighbors) is the traversal primitive + the composability
  ground truth.
- **LLM-driver chain** (147) — NL front-end · **output-budget** (146).
- This is the queryable face of the provenance moat (Goal 2).
- Spec 198 (CLI parity) — `analyze.graph_query` reachable via both
  surfaces with shape-hash equality.
- Spec 202 (skill attach) — the ATTACHES_TO edge is queryable via the
  DSL; demonstrates the moat for skill provenance.
- Spec 205 (substrate hardening) — the composability audit is a
  standing check, not a one-time pass.
- Spec 154 (output overflow) — `truncated=true` is the body cap, never
  the prefix.

## Open questions

1. Full Cypher or a bounded DSL? **Recommend**: bounded DSL (the engine
   already speaks Cypher internally; expose a safe subset). Cypher
   power is queryable from inside the engine via direct GraphQLite calls
   when an internal verb needs it; the user surface stays safe.
2. NL-front-end caching? **Recommend**: yes — `(question_hash,
   capability_set_hash)` LRU; in-process only (counts as derivation,
   not provenance — CLAUDE.md rule 2).
3. How to teach agents the DSL? **Recommend**: `analyze.graph_query`
   carries `examples=True` returning fixture patterns from the
   capability's docstring — derived, never hand-authored.
