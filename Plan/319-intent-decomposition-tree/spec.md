---
spec_id: "319"
slug: intent-decomposition-tree
status: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [2, 3]
depends_on: ["048", "110", "307", "308", "310", "318"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 319 — Intent decomposition into a sub-intent tree (`discover.decompose_intent`)

> Child of the intent-pillar deep program (Spec 307), **structure layer**. A large
> discovered Intent is rarely one unit of work — this slice splits it into a
> CONFIRMED sub-intent TREE so every leaf SERVES the root through a real
> PARENT_INTENT chain, not a paragraph of prose.

## Why (evidence + doctrine)

Spec 307 §"verb surface" locks `decompose_intent` to the `scope` cluster as the
structure verb that turns a broad intent into children. Today the substrate
*can* chain intents — `agency/intent.py:capture(parent_intent_id=…)` mints a
child, links `PARENT_INTENT`, and defaults `owner="agent"` (Spec 048) — but
**nothing in the discovery suite drives that chaining from a decomposition**. An
agent either keeps one giant intent (every downstream `SERVES` edge inherits the
vagueness — Spec 307 §"thesis") or hand-mints children with no MECE discipline
and no provenance of *why* the split is exhaustive-and-disjoint.

The doctrine this serves: CORE.md names Intent the human-owned root that
"everything edges back to via SERVES." A *tree* of intents makes SERVES
load-bearing — work attaches to the leaf it actually serves, and the root rolls
up. This is the **provenance moat (Goal 2)** applied to scope, and the
**agent-uniform lifecycle (Goal 3)**: every sub-intent is a first-class Intent
any driver can pick up, walk, and confirm independently.

Spec 318 (`scope`) already separates in-/out-of-scope boundaries; its
**out-of-scope items are not waste** — they are candidate *deferred* sub-intents.
Decomposition is where they land as real nodes instead of evaporating.

## Design

**Cluster path.** `agency/capabilities/discover/clusters/scope.py` (the same
module as `scope`/`acceptance`, per Spec 307 §"Architecture"). Composes the
`DiscoverCluster` mixin (`_base.py`) for `_recall_intent` / `_session_of`.

**Verb signature.**

```python
@verb(role="act")
def decompose_intent(self, intent_id: str = "", confirm: bool = False) -> ToolResult:
    """Split a large Intent into a confirmed sub-intent tree (act).

    Inputs: intent_id (defaults to ctx.intent_id), confirm.
    Returns: {root, children: [{intent_id, purpose, deliverable}]}.
    chain_next: discover.clarity on each child; discover.scope to bound them.
    """
```

**Substrate composition.**

1. **Propose (MECE).** `decompose_intent` composes `thinking.decompose`
   (Spec 110 — `ctx.call("thinking", "decompose", …)`) over the root's
   `{purpose, deliverable, acceptance}` to produce MECE sub-problems
   (mutually-exclusive, collectively-exhaustive). The split is *derived* from the
   root, never invented (CLAUDE.md derivability audit). Spec 318's recorded
   out-of-scope `ScopeBoundary` nodes (`side="out"`) are folded in as candidate
   **deferred** children.
2. **Review (`confirm=False`, the default).** Returns the PROPOSED tree for
   human review via the AskUser primitive (`discover.ask`, Spec 310) — no graph
   writes beyond the Invocation. The agent can amend the split before persisting.
3. **Persist (`confirm=True`).** For each sub-problem, mint a child via the
   substrate `intent.capture(parent_intent_id=root_id)` — which links the
   **`PARENT_INTENT`** edge and defaults `owner="agent"` (Spec 048). Each child is
   then confirmed (`intent.confirm`) so the tree is ready to serve work.

**Spec-307 ontology used (by name).** The tree edges are the substrate's
**`PARENT_INTENT`** (child→root) plus the existing **`SERVES`** traversal; no
new node type is needed — decomposition reuses the Intent node. The
`DiscoverySession` of the root gains no new edge (children are Intents, recalled
via `SERVES`/`PARENT_INTENT`). This honours Spec 307 §coherence rule 4 ("no
second source of truth") — chaining is the substrate's, not a re-implementation.

**Guard composition (substrate, by name).** `intent.capture` runs the Spec 048
cycle/depth guards before recording: `_check_parent_depth` enforces
`_MAX_CHAIN_DEPTH` (agency/intent.py:18) and `recall_typed(parent, "Intent")`
refuses a non-Intent parent. `decompose_intent` does NOT re-implement these — a
too-deep or malformed split fails loud through the substrate. A root already at
max depth refuses new children (the leaf should be re-rooted, not chained).

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **PARENT_INTENT completeness (invariant):** after `confirm=True`, EVERY child
  returned has a `PARENT_INTENT` edge to the root — assert
  `set(children_ids) == set(ctx.neighbors(root_id, "PARENT_INTENT", reverse=True))`,
  computed from the live graph, not a pinned child count.
- **SERVES reaches every leaf (invariant):** the root→leaf `SERVES`/PARENT_INTENT
  traversal reaches each child (no orphaned sub-intent) — assert every child id is
  in the root's transitive parent-closure.
- **Review is read-only:** `confirm=False` adds zero Intent nodes (graph
  Intent-count delta == 0 beyond the Invocation); `confirm=True` adds exactly
  `len(children)` Intents — delta computed against a live census.
- **Owner provenance:** every minted child has `owner == "agent"` (Spec 048
  default for `parent_intent_id != ""`), asserted by reading the node, not assumed.
- **Depth guard honoured:** decomposing an intent already at `_MAX_CHAIN_DEPTH`
  raises the substrate `ValueError` (no silently-dropped child) — assert the
  guard fires rather than a hand-coded limit.
- **Deferred out-of-scope:** an out-of-scope `ScopeBoundary` (Spec 318) on the
  root surfaces as a child in the proposed tree (derivability — it came from the
  graph, not invented).

## Acceptance

An agent points `decompose_intent` at a broad confirmed Intent, reviews a MECE
proposed tree (no writes), and on `confirm=True` gets a persisted sub-intent
tree where every leaf has a real `PARENT_INTENT` edge to the root and `SERVES`
traverses root→leaf — work now attaches to the sub-intent it serves, and the
root rolls up. No hand-minted children; the Spec 048 guards hold.

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** Structure-layer child of Spec 307. Builds directly on the
  shipped substrate (`agency/intent.py` chaining + Spec 048 guards) and the
  shipped `thinking.decompose` (Spec 110); the only new surface is the
  composition + the propose/persist split.
- **Slice plan:** Slice 1 — typed propose/persist with `thinking.decompose`
  behind the typed contract (deterministic MECE for the test fixture); Slice 2 —
  the AskUser review round-trip (`discover.ask`, Spec 310) for `confirm=False`;
  Slice 3 — fold Spec 318 out-of-scope boundaries as deferred children.
- **Open question (resolve at build):** whether a confirmed child should inherit
  the root's acceptance scaffold or derive its own via `discover.acceptance`
  (Spec 317). Default: leave each child's acceptance empty and recommend
  `discover.acceptance` per leaf, so decomposition stays a pure split.
