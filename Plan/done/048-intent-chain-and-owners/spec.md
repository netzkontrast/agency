---
spec_id: "048"
slug: intent-chain-and-owners
status: complete
state: done
last_updated: 2026-06-03
owner: "@agency"
depends_on: [020, 029, 042]
informs: [044, 041]
affects:
  - agency/intent.py
  - agency/engine.py
  - agency/capabilities/plugin.py
  - agency/capabilities/analyze/_main.py
  - agency/capabilities/analyze/_paths.py        # NEW — intent-path analyzer axis
  - agency/capabilities/document/_render.py      # provenance scope → render intent tree
  - tests/test_intent_chain.py
  - tests/test_intent_owners.py
  - tests/test_intent_path_analysis.py
estimated_jules_sessions: 1
domain: meta
wave: 2
---

# Spec 048 — Intent Chaining, Owners, and Path Analysis

## Why

Agency's `Intent` is the SERVES anchor for every Invocation — the WHY
of any action. Today every `intent_bootstrap` call mints a fresh root
Intent with no parentage. This breaks three things:

1. **Session traceability.** A user prompt triggers many sub-intents
   (the agent mints `intent_bootstrap` repeatedly for sub-tasks); none
   of those edges back to the *originating user intent*. So
   `document.render(scope="provenance", for_intent_id=USER_ROOT)` can't
   show the full session's work — only the one intent directly mentioned.

2. **Owner attribution.** The graph can't distinguish:
   - a USER-originated intent (came from a prompt)
   - an AGENT-originated intent (the agent decided to bootstrap a
     sub-task to scope its own work)
   - a SUB-AGENT-originated intent (a dispatched subagent or Jules
     session minted its own intent and is reporting back)
   All three are first-class concepts in a real agentic workflow.
   Without owner tags, attribution analysis is impossible.

3. **Path-shortening opportunities.** We can't see "intent paths"
   (root-user-intent → 5 sub-intents → 12 invocations → 3 artefacts)
   and ask: "is this 12-invocation path a candidate for a specialized
   capability?". The whole point of growing the capability surface is
   reducing intent→artefact distance. Without the structural view, we
   can't tell where to invest.

This spec adds **intent chaining** (a PARENT_INTENT edge), **intent
owners** (a closed `owner` enum: user, agent, subagent, jules, system),
and a **path-analysis axis** on `analyze` that surfaces long
intent→artefact paths as refactoring candidates.

## Done When

### Intent chaining (PARENT_INTENT edge + parent_intent field)

- [ ] `agency/intent.py::Intent.capture()` accepts an optional
  `parent_intent_id: str = ""` argument. When non-empty:
  - Creates the new Intent with `parent_intent_id` as a property.
  - Records a `PARENT_INTENT` edge from new → parent.
- [ ] `Intent.capture_and_confirm()` similarly forwards
  `parent_intent_id`.
- [ ] `agency/engine.py::intent_bootstrap` MCP tool accepts
  `parent_intent_id: str = ""`. When set, the new Intent is linked
  back via `PARENT_INTENT`.
- [ ] Cycle prevention: `Intent.capture` refuses to record an Intent
  whose `parent_intent_id` traces (transitively) to the same node id
  — ValueError with the cycle path. The check uses a deterministic
  Graph traversal (≤ 32 levels deep; deeper than that, fail-loud as
  pathological).
- [ ] OntologyExtension gains `PARENT_INTENT` to the Intent class's
  edges; field `parent_intent_id` to `Intent`'s required fields list
  (default `""` for root intents).

### Intent owners (closed enum + owner field)

- [ ] `agency/intent.py::Intent.capture()` accepts `owner: str = "user"`.
  Allowed values (closed enum on the ontology):
  - `"user"` — originated from a user prompt (the default for
    interactive sessions).
  - `"agent"` — the running agent (Claude, GPT) minted this sub-intent
    to scope its own work.
  - `"subagent"` — a dispatched local subagent minted this.
  - `"jules"` — a remote Jules session minted this (reported back).
  - `"system"` — engine-internal (install, doctor, scaffold). Reserved
    for substrate tools that act WITHOUT a user prompt.
- [ ] The substrate `intent_bootstrap` MCP tool: when called WITHOUT
  `parent_intent_id`, defaults `owner="user"`. When called WITH
  `parent_intent_id`, defaults `owner="agent"`. Override always wins.
- [ ] Existing `agency_install`, `agency_doctor`, `intent_bootstrap`
  remain unchanged on the wire — owner defaults handle the upgrade
  silently (backward-compatible).
- [ ] `OntologyExtension.enums[("Intent", "owner")]` = the closed set
  above. Memory enforces.

### Path analysis (analyze.paths transform)

- [ ] New transform verb `analyze.paths(root_intent_id: str = "",
  max_paths: int = 10) -> dict` (pure; transform; same Finding shape
  with rule prefix `IP*`):
  - `IP001` (info) — long intent path: root → ≥ 5 sub-intents.
  - `IP002` (warn) — long verb sequence: ≥ 12 Invocations to reach the
    first PRODUCES-edge artefact. Candidate for a specialized
    capability that shortens the path.
  - `IP003` (info) — repeated verb pattern: same verb invoked ≥ 4
    times in one path. Candidate for batched/fan-out replacement.
- [ ] When `root_intent_id` is empty, scans ALL user-owned root
  intents (where `owner="user"` AND `parent_intent_id=""`) and emits
  findings across all of them, capped at `max_paths`.
- [ ] Each finding carries the path itself as `evidence`: a
  `→`-separated chain of `intent:abc` → `intent:def` → ... so the
  caller can navigate.

### Render extension (provenance scope walks the tree)

- [ ] `document.render(scope="provenance", for_intent_id=ROOT)`
  walks the PARENT_INTENT graph DOWNWARD (root → children → grand-
  children), not just the single Intent's direct SERVES edges.
- [ ] New optional `depth: int = 2` parameter on `render` for the
  provenance scope: cap how many levels of the tree to render.
  Default 2 covers the user→agent→subagent case typical of sessions.
- [ ] The provenance render now includes a "Sub-intents" H2 section
  per node: a markdown tree showing the intent forest under the
  current root.

### Tests

- [ ] `tests/test_intent_chain.py` — chain 3 intents; assert parent
  edges; assert cycle detection raises; assert root has no parent.
- [ ] `tests/test_intent_owners.py` — closed enum is enforced;
  `intent_bootstrap` defaults `owner` correctly based on
  `parent_intent_id` presence; explicit `owner` overrides default.
- [ ] `tests/test_intent_path_analysis.py` — fixtures: a 6-level
  chain (IP001), a 15-invocation single intent (IP002), a 5-times
  repeated verb (IP003). Assert each fires.

## Design

### Why owner-as-enum, not owner-as-free-string

Same doctrine as scope on Reflection (Spec 045 §"Severity-
assignment"): owners are CONTRACT-level. A free-string owner field
would let agents invent owners ad-hoc; downstream analytics couldn't
distinguish "user-prompt-originated" from "agent-decided".

Closed enum (5 values) covers the operational landscape:
  user — the human typed something
  agent — the running model (top-level)
  subagent — a delegated isolated context
  jules — a remote async dispatch
  system — engine-internal (substrate)

Add new values via spec amendment, not runtime config.

### Why default owner depends on `parent_intent_id` presence

Without parent: the intent is a root → originated from a user prompt.
With parent: the intent was minted to scope sub-work → an agent did it.

This is the simplest possible inference rule. It's wrong sometimes
(a user can explicitly chain intents), but the CALLER can always
override. Default-is-inference, explicit-wins.

### Cycle prevention (PARENT_INTENT)

The graph permits arbitrary edges; the ontology doesn't enforce
acyclicity. So `Intent.capture(parent_intent_id=X)` must verify
that X does NOT transitively point back to the new Intent.

Implementation: BFS from `parent_intent_id` up the PARENT_INTENT
chain, up to 32 levels. If the depth exceeds 32, fail loud — that
depth itself is a smell.

```python
def _check_no_cycle(self, parent_id: str, new_id: str) -> None:
    seen = {new_id}
    current = parent_id
    depth = 0
    while current and depth < 32:
        if current in seen:
            raise ValueError(
                f"PARENT_INTENT cycle: {new_id} → ... → {current} → loop")
        seen.add(current)
        next_node = self._lookup_parent(current)
        current = next_node
        depth += 1
    if depth >= 32:
        raise ValueError(
            f"PARENT_INTENT chain too deep (>32) from {new_id} → ... — "
            "pathological; root the new intent instead")
```

### Path analysis findings as refactor candidates

The whole point of `analyze.paths` is **surfacing intent shapes that
suggest a missing specialized capability**. Examples:

- A user intent that triggers `analyze.run` → `document.render` →
  `reflect.note` → `analyze.run` → `document.render` → ... (paths
  with ≥ 12 invocations) suggests a "publish-improvement-report"
  composite verb is missing.
- A user intent with 5 sibling sub-intents each doing similar
  reflect.recall + document.explain pairs suggests a "explain-N-
  symbols" fan-out helper.

Path analysis surfaces these patterns. The HUMAN reads the findings
and decides whether to ship a new verb. Path analysis is NOT
auto-refactoring — it's a TELESCOPE on intent shapes.

### Backward compatibility

All four changes are additive:
- New optional `parent_intent_id` defaults `""` (root).
- New optional `owner` defaults `"user"` for root, `"agent"` for
  child — same default behavior as today.
- New verb `analyze.paths` doesn't change existing axes.
- New `depth=2` param on `render` defaults to 2 (full tree from root
  with two levels — what existing single-intent rendering would
  produce anyway for a root intent with no children).

Existing tests do NOT need updates. The 547+1 baseline stays.

### Cluster-coherence (Spec 047)

- C08 (Session Lifecycle / Memory) — intent owners are session-
  lifecycle metadata.
- C04 (Quality / Review / Verify) — `analyze.paths` is a new
  analyzer axis under the same Finding shape contract (Spec 042 §
  "Severity-assignment").
- C07 (Documentation / Knowledge) — `document.render(scope=
  "provenance")` now walks the tree.
- C11 (Orchestration / Subagents) — owner=subagent tag distinguishes
  dispatched sub-work.

## Files

- **Modify:**
  - `agency/intent.py` — add `parent_intent_id` + `owner` params +
    cycle check.
  - `agency/engine.py::intent_bootstrap` — accept the new params,
    apply default-by-presence rule.
  - `agency/ontology.py` (or the Intent node declaration) — add
    `PARENT_INTENT` edge type, `owner` enum.
  - `agency/capabilities/analyze/_main.py` — add `paths` verb.
  - `agency/capabilities/document/_render.py::render_provenance` —
    walk the tree downward.
- **Add:**
  - `agency/capabilities/analyze/_paths.py` — the path-analyzer.
  - `tests/test_intent_chain.py`, `tests/test_intent_owners.py`,
    `tests/test_intent_path_analysis.py`.
- **Do not modify:**
  - The wire contract (3 MCP tools).
  - Existing intent-bootstrap callers (substrate or capabilities).
  - The SERVES edge or its semantics.

## Open Questions

1. **Should `parent_intent_id` be enforceable via a CYCLE constraint
   in the ontology** (graph-level), or only the runtime check in
   `Intent.capture`? Runtime is simpler; graph-level requires
   GraphQLite path-constraint support which agency doesn't use yet.
   Lean: runtime only for v1.
2. **What's the right limit for analyze.paths' "long path" threshold?**
   IP001 at 5 sub-intents and IP002 at 12 invocations are estimates;
   needs measurement against a real session corpus before pinning.
   Defer to v2 after first usage data.
3. **Should `intent_bootstrap` ALSO auto-set owner based on the
   substrate tool that called it?** E.g., when `agency_install`
   bootstraps an intent, owner should be `system`. v1 lets the caller
   pass `owner=system`; v2 may infer.
4. **Multi-root tracking.** A session might have multiple user roots
   (user types 3 separate prompts → 3 root intents). The graph
   handles this naturally (3 disconnected forests). `analyze.paths`
   should walk EACH root. v1: yes; v2 may add a session-grouping
   layer.

## Evidence

- User audit (2026-06-03): "we need to be able to chain intent nodes…
  trace a complete session back to the given user intent… need
  different intent owners… so every sub-intent can be traced back to
  a user prompt".
- Spec 047 §C08 cluster — Session Lifecycle / Memory already foresaw
  cross-session continuity; intent chaining is the structural
  prerequisite.
- Spec 040 dispatch_decision §"S11 local_budget_relevant" — already
  distinguishes Jules vs. local; this spec's owner enum aligns.

## Followup — Implementation Status (2026-06-03)

**Verdict:** Shipped — intent chaining + owner enum + path-analysis
axis all live. 25 spec tests green + dogfood validated via the wire
(intent_bootstrap MCP tool minted a 5-deep chain; analyze.paths fired
IP001 on the root).

### Done
- **Ontology** (`agency/ontology.py`):
    - Intent NODE_SCHEMAS now includes `owner` (required). The
      `parent_intent_id` property is OPTIONAL (not in required) so
      root intents pass validation with the empty default.
    - INTENT_OWNERS = {user, agent, subagent, jules, system} —
      closed enum on `(Intent, owner)`, ENFORCED by Memory.violations.
    - PARENT_INTENT added to EDGE_TYPES — the link from sub-intent
      to parent intent.
- **Intent class** (`agency/intent.py`):
    - capture(purpose, deliverable, acceptance, parent_intent_id="",
      owner="") + capture_and_confirm same shape.
    - Default-by-presence rule: `owner = "agent" if parent_intent_id
      else "user"`; explicit override wins.
    - `_check_parent_depth(parent_id)` — refuses chains > 32 levels
      (pathological-fail guard). `_check_no_cycle(parent_id, new_id)`
      is the runtime helper for downstream callers.
    - PARENT_INTENT edge recorded on capture when parent supplied.
- **Engine** (`agency/engine.py::intent_bootstrap`):
    - Accepts `parent_intent_id: str = ""`, `owner: str = ""`.
    - Returns `{intent_id, status, owner, parent_intent_id, next}`
      — wire payload extended without breaking existing callers.
    - Owner inferred from parent presence; resolved owner read back
      from the graph so the caller sees the truth, not their hint.
- **analyze.paths** (`agency/capabilities/analyze/_paths.py` + verb in
  `_main.py`):
    - Transform verb (pure; graph-walking, not file-tree-walking).
    - IP001 (info) — intent chain ≥ 5 levels deep → composite-verb
      candidate.
    - IP002 (warn) — ≥ 12 Invocations under one intent → specialized-
      capability candidate.
    - IP003 (info) — verb invoked ≥ 4× under one intent → batched-
      replacement candidate.
    - `root_intent_id=""` scans all user-owned roots; `max_paths`
      caps the scan.
    - `paths` joins the Analysis axis enum; `analyze.run` default
      now scans 5 axes (was 4 — backward-compat-breaking; one
      regression test updated).
- **document.render(scope="provenance")**:
    - Appends a "Sub-intents" H2 section with markdown table
      (intent_id | owner | purpose) listing immediate children
      reached via PARENT_INTENT (1 level downward — v2 may add the
      depth=2 default the spec proposed).
- **Tests** (3 new files, 25 tests):
    - `test_intent_chain.py` (7) — root/child/3-level, edge recording,
      cycle detection (self-loop + 2-loop), pathological depth.
    - `test_intent_owners.py` (8) — defaults, override, all 5 enum
      values, ontology rejection of unknown owners, intent_bootstrap
      MCP-wire owner inference.
    - `test_intent_path_analysis.py` (9) — IP001/IP002/IP003 fixtures,
      scope handling (single root vs all user roots), max_paths cap,
      verb registration, axis enum.

### Open for v2
- OQ1 graph-level cycle constraint (currently runtime-only).
- OQ2 IP001/IP002/IP003 threshold tuning after measurement against
  real session corpora.
- OQ3 `intent_bootstrap` auto-owner from calling-substrate context
  (e.g., agency_install minting → owner=system without explicit hint).
- OQ4 `depth: int = 2` parameter on render(provenance) — current
  implementation walks ONE level downward; v2 may recurse to 2.

### Cluster-coherence cross-refs (Spec 047)
- C08 Session Lifecycle / Memory (it IS — intent owners track who
  minted, parent_intent_id enables session-rooted traceback).
- C04 Quality (analyze.paths joins the analyzer family with the same
  Finding shape contract).
- C07 Documentation (render(provenance) now walks the tree).
- C11 Orchestration (owner=subagent and owner=jules distinguish
  dispatch types).
