---
spec_id: "056"
slug: type-safe-node-id-discipline
status: draft
last_updated: 2026-06-03
owner: "@agency"
depends_on: ["016", "019"]
affects:
  - agency/memory.py                     # NEW recall_typed(id, label) helper
  - agency/intent.py                     # use recall_typed for parent_intent_id guard
  - agency/capabilities/research/_specialist.py   # use recall_typed for research_id guard
  - agency/capabilities/gate.py          # use recall_typed for lifecycle_id guard
  - agency/capabilities/document/_main.py # explain target validation
  - agency/capabilities/plugin.py        # NEW _check_node_id_guards lint rule
  - tests/test_recall_typed.py           # NEW
  - docs/vision/CAPABILITY-AUTHORING.md  # codify the convention
estimated_jules_sessions: 0
domain: substrate
wave: 4
---

# Spec 056 — Type-safe node-id discipline

## Why

Three independent bugs surfaced in PR #17's review pass — all the same
shape: a verb takes a node id as a parameter, guards its existence via
`memory.recall(id)`, but doesn't verify the node's **label**.

Concrete sites + symptoms:

1. **`research.specialist`** (`agency/capabilities/research/_specialist.py:35`).
   The first-round fix added `_validate_research_id` that called
   `memory.recall()`. The second-round review caught it: any existing
   node id passes — an `intent_id` typo'd as `research_id` still
   recorded `Citation` nodes anchored at the wrong endpoint. Later
   `research.verify`'s `MATCH (r:Research)-[:CITES]->(c)` traversal
   silently lost them.

2. **`intent.capture`** (`agency/intent.py:48`). First-round fix
   added a `recall()` guard for `parent_intent_id`. Second-round review
   caught it: an Agent/Citation/Reflection id passed the guard, the
   child Intent was recorded, `PARENT_INTENT` linked to a non-Intent
   endpoint, and provenance traversals dropped the child.

3. **A latent class of similar bugs** across the substrate: `gate.check`
   takes `lifecycle_id` (no label check); `document.explain` takes a
   `target` that's expected to be an Intent (no label check); future
   verbs that take node ids will recur.

The fixes all wrote the same boilerplate:

```python
node = self.ctx.memory.g.get_node(node_id)
if node is None or "ExpectedLabel" not in (node.get("labels") or []):
    return {"error": "..."}
```

Three independent duplicates in one session = systemic. Worth a
substrate helper + a lint rule.

## Done When

- [ ] **`agency/memory.py` gains `recall_typed(node_id, label) ->
      Optional[dict]`**. Returns the node's properties only when the
      node exists AND carries `label` in its labels list; returns
      `None` otherwise. Pure read; no provenance side effects.
- [ ] **Three existing guards migrate** to use it:
  - `research/_specialist.py::_validate_research_id`
  - `intent.py::capture` parent-id guard
  - `gate.py::check` lifecycle-id guard (currently uses a Cypher MATCH
    that already filters by label — keep, but document the equivalence)
- [ ] **One new guard lands** in `document/_main.py::explain` to verify
  the `target` parameter when it's expected to be an Intent id.
- [ ] **`plugin.lint_capability` gains `_check_node_id_guards`** — a
      seventh rule that scans verb sources for a parameter named
      `<label>_id` (research_id, intent_id, lifecycle_id, …) and flags
      verbs that read `memory.recall(<param>)` without a corresponding
      `recall_typed` call OR a Cypher MATCH with the expected label.
      The rule is WARN-mode initially; flip to BLOCK once the existing
      guards migrate.
- [ ] **`tests/test_recall_typed.py`** — 5 tests:
  - existing node with matching label → returns props.
  - existing node with non-matching label → returns None.
  - missing node id → returns None.
  - empty / None id → returns None.
  - props returned are a copy (mutation safety).
- [ ] **CAPABILITY-AUTHORING.md gains a section** "Node-id parameters
      must be label-checked" with the `recall_typed` pattern + the
      anti-pattern that bypasses it.
- [ ] `python -m pytest -q -n auto -m "not e2e"` stays green.

## Design

### Substrate helper

```python
# agency/memory.py
def recall_typed(self, node_id: str, label: str) -> Optional[dict]:
    """Return node properties iff the node exists AND has `label` in
    its labels list. Returns None for missing / wrong-label / empty-id
    cases — all three are caller-recoverable misses.

    Pure read; no provenance side effects. Faster than a Cypher
    MATCH (n:label) WHERE n.id = $id RETURN n round-trip when the
    caller only needs existence-+-label confirmation.
    """
    if not node_id:
        return None
    node = self.g.get_node(node_id)
    if node is None:
        return None
    if label not in (node.get("labels") or []):
        return None
    return dict(node.get("properties", {}))
```

### Lint rule heuristic

`_check_node_id_guards` walks each verb's source for parameter names
matching `^(.+)_id$`. For each, infer the expected label from the
prefix (`research_id` → `Research`, `intent_id` → `Intent`,
`lifecycle_id` → `Lifecycle`, etc., with a small mapping table for
the irregular cases). If the verb's source then does any of:

- `recall_typed(<param>, <Label>)` ✓
- `MATCH ... (n:<Label>) WHERE n.id = $<param> ...` ✓
- explicit error guard with a `label not in labels` check ✓

…the verb passes. Otherwise flag with a `node_id_guard` finding
naming the parameter + expected label.

The mapping table starts small (5-6 entries) and grows organically
as new node types land. Unknown prefixes (e.g. `foo_id`) skip the
rule rather than guessing.

### Migration ordering

1. Land `recall_typed` + tests (no callers yet).
2. Migrate the three existing guards.
3. Add the lint rule in WARN mode.
4. Audit all verbs via the lint output; migrate any remaining
   call sites.
5. Flip the lint rule to BLOCK mode.

## Files

- **Create:**
  - `tests/test_recall_typed.py`.
- **Modify:**
  - `agency/memory.py` — add `recall_typed`.
  - `agency/intent.py` — replace the parent-id guard.
  - `agency/capabilities/research/_specialist.py` — replace `_validate_research_id`.
  - `agency/capabilities/gate.py` — optional: refactor the MATCH to use `recall_typed`.
  - `agency/capabilities/document/_main.py` — add explain target guard.
  - `agency/capabilities/plugin.py` — add `_check_node_id_guards`.
  - `docs/vision/CAPABILITY-AUTHORING.md` — new section.

## Open Questions

1. **Mapping table for irregular prefixes.** `intent_id` → `Intent` is
   trivial; `parent_intent_id` → `Intent` needs the table. Recommend a
   small explicit dict in the lint rule; new entries land alongside
   the verbs that introduce them.

2. **Should `recall_typed` be a method on `Memory` or a free function?**
   Method keeps the `Memory.ont` available for future label-validation
   refinements (e.g. checking against the ontology's known labels).
   Free function would be more uniform with other read helpers. Recommend
   method.

3. **WARN→BLOCK timeline.** WARN immediately; BLOCK once the audit
   shows zero remaining bare-`recall()` patterns on `*_id` parameters.
   Expect ~10 sites to migrate.

## Evidence (cites)

- `agency/capabilities/research/_specialist.py:35-46` — the
  round-2 fix (label-check via `g.get_node` + `'Research' in labels`).
- `agency/intent.py:43-60` — the round-3 fix (label-check via
  `g.get_node` + `'Intent' in labels`).
- `agency/capabilities/gate.py:33-39` — existing Cypher MATCH guard
  that effectively label-checks.
- PR #17 review comments r3343808289 + r3343808276 (research_id /
  parent_intent_id label-check gaps).
- Spec 016 Hint #7 (`Inputs:` / `Returns:` / `chain_next:` markers)
  — this spec adds the missing structural cousin: `<param>_id`
  parameters carry a label expectation that lint can verify.
