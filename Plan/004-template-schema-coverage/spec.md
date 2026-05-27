---
spec_id: "004"
slug: "template-schema-coverage"
status: draft
owner: "@agency"
depends_on: ["003"]
affects:
  - agency/templates.py
  - agency/ontology.py
  - agency/capabilities/delegate.py
  - agency/capabilities/jules.py
  - agency/capabilities/plugin.py
  - tests/test_agency.py
source-repos:
  - "https://github.com/netzkontrast/the-agency-system @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22"
estimated_jules_sessions: 2
domain: core
wave: 1
---

> **Jules: read `Plan/JULES_PROTOCOL.md` before starting** (if present). Confidence ≥ 0.90,
> TDD Red-Green-Refactor, Evidence pasted under `## Evidence`, Self-Review answered.
> Only modify paths under `affects:`. The scope is **settled** below (2 uncovered
> recorded artefact kinds: `jules-session`, `reduction`) — the old "do not start
> until Q1 is answered" gate is removed because the audit *is* the answer.

# Spec 004 — Schema Coverage for the Uncovered Recorded Artefact Kinds

## Why

The generate/validate loop is the typed spine of the graph: a capability `act`
renders an Artefact from a `Template`, and `Memory.validate_schema`
(`agency/memory.py:144`) checks the recorded node against a `Schema` node's
`required` fields. Today that loop only closes for a minority of artefacts. The
strict required-field schemas live in `REQUIRED` (`agency/templates.py:72`) and
cover exactly **5 kinds**:

```python
REQUIRED = {
    "plugin-manifest":   ["name", "version", "description"],
    "skill-md":          ["name", "description", "body"],
    "command-md":        ["name", "description", "body"],
    "marketplace-entry": ["name", "version", "description", "source"],
    "step-doc":          ["step", "output"],
}
```

`plugin_ontology` registers these (and only these) as the capability's `schemas`
(`agency/capabilities/plugin.py:179`, `schemas=dict(templates.REQUIRED)`), so they
are the only artefact kinds the graph carries a schema for. Two other artefact
kinds are *recorded as Artefact nodes* with no schema: the delegation reduction
`record("Artefact", {"kind": "reduction", "children": children})`
(`agency/capabilities/delegate.py:78`) and the Jules session
`{"kind": "jules-session", "session": ..., "url": ...}`
(`agency/capabilities/jules.py:88`), neither paired with a schema.

The templates-and-schemas research (`research/templates-and-schemas/`) proposed a
13-key `REQUIRED.update({...})` and claimed "18 kinds / 5 covered / 13 remaining".
**That count is wrong** — it conflates three distinct namespaces (artefact `kind`s,
skill `kind`s, and skill-phase `produces:` slot names). This spec carries the
audit that reconciles it (below) and scopes the work to the verified truth.

## Audit — the recorded artefact kinds (this spec's ruling, do not skip)

An Artefact reaches the graph by exactly two routes:

1. a verb returns `{"artefact": {...}}`, recorded by the engine at
   `agency/capability.py:178` (`memory.record("Artefact", dict(result["artefact"]))`);
2. a verb calls `self.ctx.record("Artefact", {...})` directly.

Grepping both routes across the whole `agency/` tree, the complete, deduplicated
set of artefact `kind` literals **actually recorded as Artefact nodes** is **7**:

| kind | recorded at (`path:line`) | schema today? |
|---|---|---|
| `plugin-manifest` | `agency/capabilities/plugin.py:43` | YES (`templates.py:73`) |
| `skill-md` | `agency/capabilities/plugin.py:53` | YES (`templates.py:74`) |
| `command-md` | `agency/capabilities/plugin.py:59` | YES (`templates.py:75`) |
| `marketplace-entry` | `agency/capabilities/plugin.py:65` | YES (`templates.py:76`) |
| `step-doc` | `agency/capabilities/plugin.py:74` | YES (`templates.py:77`) |
| `jules-session` | `agency/capabilities/jules.py:88` | **NO** |
| `reduction` | `agency/capabilities/delegate.py:78` | **NO** |

**7 recorded artefact kinds; 5 schema'd; exactly 2 uncovered: `jules-session`,
`reduction`. The scope of 004 is to cover those 2 — nothing else.**

### Why "18 / 13 / 8" are all wrong

The research's "uncovered" rows are mostly **not Artefact records**:

- **Skill `kind`s, never recorded as Artefacts.** `authoring`
  (`SKILL_CREATION_SKILL["kind"]` / `PLUGIN_DEV_SKILL["kind"]`,
  `plugin.py:136,155`) and `discipline` (the eight discipline skills,
  `develop.py:29-74`) are values of a *skill's* `kind` field, not `"kind"` keys
  in any `record("Artefact", ...)` call.
- **`produces:` phase-slot names, never recorded as Artefacts.** `baseline`,
  `findings`, `lint`, `manifest`, `entry`, `rationalizations`,
  `rationalization_table`, `red_flags`, `user_confirmed`, `skill_md`,
  `command_md` are snake_case strings the skill walker validates per phase
  (`plugin.py:139-169`, `develop.py:67`). Nothing calls
  `record("Artefact", {"kind": "findings"})` (or any of these) anywhere.

So three namespaces exist and only one is validatable by
`Memory.validate_schema`: **artefact `kind`s** (kebab, 7 total) — because only
they become `Artefact` nodes — versus **skill `kind`s** (`authoring`,
`discipline`) and **`produces:` slots** (snake, ~11). The research merged them;
the "18" was (artefact-kinds ∪ skill-kinds ∪ slots), the "13" was that minus the
5 covered, and the "8" was an internal inconsistency in the research's own prose.
**STOP counting skill `kind`s and `produces:` slots as artefacts.** Adding a
schema for a kind no code records produces a dead schema and is forbidden by the
prior art (`the-agency-system Plan/131-manifest-coverage-lint/spec.md`: no
placeholder entries for unemitted things — "auto-defaulting placeholder entries
would mask the human decision").

Slots-become-artefacts (rewriting `develop`/`plugin` verbs so every `produces:`
slot is recorded as an Artefact of that kind, then schema'ing them) is a
legitimate but **separate** feature — split to a follow-up spec (005), not 004.

## The validate side is not wired yet (must be addressed, not assumed)

`Memory.validate_schema(node_id, schema_id)` (`agency/memory.py:144-153`) takes a
**`Schema` node id** and reads that node's comma-joined `required` field. But in
the live tree **nothing records a `Schema` node and nothing calls
`validate_schema`** outside its own definition and a docstring
(`grep -rn 'validate_schema\|VALIDATES_AGAINST' agency/` shows only `memory.py:144`
and `templates.py:6`). `Ontology.schemas` is populated (via
`schemas=dict(templates.REQUIRED)`, `plugin.py:179`) but it is an in-memory
registry — it never becomes a `Schema` *node*, so there is no `schema_id` to pass.

Therefore adding a `REQUIRED`/`schemas` entry alone does **not** make a kind
validatable: the round-trip in `Done When` would have nothing to validate against.
004 must wire the validate side. Decision: **wire it** with the minimal driver —

- The engine bootstrap records **one `Schema` node per `Ontology.schemas` entry**
  (`name` = the kind, `required` = the comma-joined required-field list). This is
  the missing link between the registry and the enforcement point.
- The two newly covered verbs link their recorded Artefact `VALIDATES_AGAINST`
  the matching `Schema` node (the `VALIDATES_AGAINST` edge already exists in
  `EDGE_TYPES`, `ontology.py:43`), so the provenance subgraph is complete and the
  round-trip test has a real `schema_id` to assert on.

(If wiring is judged out of scope at implementation time, the alternative is to
explicitly scope the validate round-trip OUT and assert only registry membership
— but the recommendation is to wire it, because an unwired schema is the same
"registry without enforcement" gap this spec exists to close.)

## Done When

- [ ] `agency/capabilities/jules.py` and `agency/capabilities/delegate.py` carry a
      capability-owned schema for their recorded kind (see Design); no schema is
      added for any kind no code records.
- [ ] `delegate.join` records a `reduction` Artefact with the full required field
      set (`parent_intent`, `children`, `summary`), derived from `join`'s own
      query rows.
- [ ] `jules.dispatch` records a `jules-session` Artefact with the full required
      field set (`session_id`, `url`, `state`, `history`).
- [ ] The engine records a `Schema` node per `Ontology.schemas` entry and each new
      verb links its Artefact `VALIDATES_AGAINST` the matching `Schema` node, so
      `Memory.validate_schema` has a `schema_id` to check against.
- [ ] A round-trip test, per new kind, records the Artefact and asserts
      `Memory.validate_schema(artefact_id, schema_id)` returns `True`; an Artefact
      missing a required field returns `False` (the schema bites).
- [ ] The verb result-shape changes (`session`→`session_id`; the grown reduction
      dict) are reflected in the existing `tests/test_agency.py` jules/delegate
      assertions enumerated in Open Q1.
- [ ] All other existing tests pass (the 5 currently-covered kinds keep their
      schemas byte-identical).

## Design

### Schemas — capability-owned, 2 keys only

Schemata live with the capability that owns them (`agency/ontology.py:60-86`), so
`jules-session` and `reduction` go into their *own* capabilities' extensions, NOT
into the plugin-owned `templates.REQUIRED`. `templates.REQUIRED` stays exactly the
5 plugin-owned kinds.

```python
# agency/capabilities/delegate.py — ADD `schemas=` to the EXISTING extension
# (delegate.py:23 already defines nodes + edges incl. REDUCES_INTO; no edge work needed):
ontology = OntologyExtension(
    nodes={"Delegation": ["driver", "driver_verb", "count", "quota"]},
    edges={"DELEGATES_TO", "REDUCES_INTO"},
    schemas={"reduction": ["parent_intent", "children", "summary"]},
)

# agency/capabilities/jules.py — JulesCapability currently has NO `ontology`
# (it inherits the empty default at capability.py:29); ADD one:
class JulesCapability(CapabilityBase):
    name = "jules"
    home = "lifecycle"
    ontology = OntologyExtension(
        schemas={"jules-session": ["session_id", "url", "state", "history"]},
    )
```

There is **no `REQUIRED.update({...})`** in this spec. The 13-key superset from
`research/.../schemas-catalogue.md` is deliberately deleted: 11 of its keys are
skill `kind`s or `produces:` slots nothing records (dead schemas), and its
`baseline` key collides by name with the `Baseline` *node* schema
(`workspace.py:21` = `["command", "passed"]`, output recorded at `:46` but not
required) while having a different shape — a trap, not a requirement.

### Templates — 2 constants only

The generate side: one `string.Template` per newly covered kind, in
`agency/templates.py`, mirroring the existing `---`-frontmatter shape.

```python
from string import Template

JULES_SESSION = Template(                       # pairs with kind "jules-session"
    "---\nkind: jules-session\nsession-id: $session_id\n"
    "url: $url\nstate: $state\n---\n\n# Session Log\n\n$history\n")

DELEGATION_REDUCTION = Template(                # pairs with kind "reduction"
    "---\nkind: reduction\nparent-intent: $parent_intent\n"
    "children: $children\n---\n\n# Reduction Summary\n\n$summary\n")
```

### Verb changes for the two uncovered kinds

**`delegate.join` (`agency/capabilities/delegate.py:78`) — BEFORE:**

```python
children = len(rows)
done = children > 0 and states.get("completed", 0) == children
red = self.ctx.record("Artefact", {"kind": "reduction", "children": children})
self.ctx.link(delegation, red, "REDUCES_INTO")
self.ctx.link(red, self.ctx.intent_id, "SERVES")
```

**AFTER** — `join` derives its own child ids and state tally from the `rows` it
already queried (`delegate.py:69-75`); there is no `child_ids`/`states`-as-list in
scope to borrow, so build them here. `children` becomes the comma-joined child
Lifecycle ids (the schema field), and the count is kept separately for the result:

```python
child_ids = [r["lc"]["properties"].get("id", r["lc"]["id"]) for r in rows]
count = len(rows)
done = count > 0 and states.get("completed", 0) == count
red = self.ctx.record("Artefact", {
    "kind": "reduction",
    "parent_intent": self.ctx.intent_id,
    "children": ",".join(child_ids),                 # list of child ids, not the count
    "summary": f"reduced {count} children: {states}",
})
self.ctx.link(delegation, red, "REDUCES_INTO")
self.ctx.link(red, self.ctx.intent_id, "SERVES")
# link the Artefact to its Schema node so validate_schema has a target:
self.ctx.link(red, "schema:reduction", "VALIDATES_AGAINST")
return {"result": {"children": count, "states": states, "done": done, "reduction": red}}
```

(Note: `states` is the existing `dict[str, int]` tally built at `delegate.py:72-75`;
`rows` is the existing query result. The result dict keeps `children` as the count
for backward-compatible callers — see Open Q1 for the test impact.)

**`jules.dispatch` (`agency/capabilities/jules.py:88`) — BEFORE:**

```python
return {
    "status": s.get("state", "submitted"),
    "session": sid,
    "url": s.get("url"),
    "artefact": {"kind": "jules-session", "session": sid or "", "url": s.get("url") or ""},
}
```

**AFTER** — the artefact carries the full `jules-session` required set
(`session`→`session_id`, plus `state`/`history`); the engine records it
(`capability.py:178`) and links `VALIDATES_AGAINST` its `Schema` node:

```python
return {
    "status": s.get("state", "submitted"),
    "session": sid,
    "url": s.get("url"),
    "artefact": {
        "kind": "jules-session",
        "session_id": sid or "",
        "url": s.get("url") or "",
        "state": s.get("state", "submitted"),
        "history": s.get("history", ""),
    },
}
```

### Wiring the `Schema` nodes (the validate side)

Per "The validate side is not wired yet" above: the engine bootstrap iterates
`Ontology.schemas` and records one `Schema` node per entry — `node_id =
f"schema:{name}"`, `props = {"name": name, "required": ",".join(required)}` (the
`Schema` node schema is `["name", "required"]`, `ontology.py:25`; `validate_schema`
splits `required` on commas, `memory.py:152`). The two new verbs then link their
Artefact `VALIDATES_AGAINST` `schema:reduction` / `schema:jules-session`. This is
the single addition that turns `Ontology.schemas` from an inert registry into a
checkable loop, and is what makes the round-trip test pass.

## Files

- **Modify**:
  - `agency/templates.py` — add `JULES_SESSION` and `DELEGATION_REDUCTION`
    `Template` constants. `REQUIRED` is **unchanged** (stays the 5 plugin kinds).
  - `agency/capabilities/delegate.py` — `join` records the full `reduction`
    artefact and links `VALIDATES_AGAINST`; add `schemas={"reduction": [...]}` to
    the existing `OntologyExtension` (`delegate.py:23`).
  - `agency/capabilities/jules.py` — `dispatch` records the full `jules-session`
    artefact; add `ontology = OntologyExtension(schemas={"jules-session": [...]})`
    to `JulesCapability` (it currently has none).
  - `agency/ontology.py` — only if the `Schema`-node bootstrap is best placed here
    (e.g. a helper that materialises `Ontology.schemas` into `Schema` nodes);
    otherwise the bootstrap lives in the engine. Pick one and state it in the PR.
  - `tests/test_agency.py` — round-trip generate/validate tests per new kind, plus
    the assertion updates from Open Q1.
- **Create**: none. Tests extend the single `tests/test_agency.py` (repo
  convention), not a new file.

## Open Questions / Needs Research

1. **Which existing `tests/test_agency.py` assertions move under the verb
   result-shape change?** (Not blocking — must be enumerated before/at PR.) The
   `jules.dispatch` artefact renames `session`→`session_id` and adds
   `state`/`history`; the top-level result still returns `session` (kept), so only
   assertions reading the *artefact* sub-dict shape change. The `delegate.join`
   result keeps `children` as the count, so callers asserting `result["children"]`
   are unaffected; assertions on the *reduction Artefact node's* fields change.
   List the exact jules/delegate test functions touched so "all existing tests
   pass" is verifiable.
2. **Where does the `Schema`-node bootstrap live — engine or `ontology.py`?**
   (Not blocking; an implementation-placement choice.) Recommend a small
   `Ontology.materialise_schemas(memory)` (or engine-init step) that records one
   `Schema` node per `Ontology.schemas` entry. Confirm it runs once at engine
   construction, after all capability extensions are merged.

## Evidence

- `agency/templates.py:72-78` — `REQUIRED` covers exactly 5 kinds.
- `agency/capabilities/plugin.py:179` — `schemas=dict(templates.REQUIRED)`, the
  only place schemas reach `Ontology.schemas`; `plugin.py:43,53,59,65,74` — the 5
  covered artefact records.
- `agency/capability.py:178` — the engine's single record-from-result site.
- `agency/capabilities/delegate.py:78` — `reduction` recorded with only `children`
  (= `len(rows)`, an int, `delegate.py:76`), no schema; `delegate.py:23-26` — the
  existing `OntologyExtension` (nodes + `REDUCES_INTO` edge, **no schemas**);
  `delegate.py:69-75` — the `rows`/`states` `join` already has in scope.
- `agency/capabilities/jules.py:88` — `jules-session` artefact with `session`/`url`
  only, field named `session` not `session_id`; `jules.py:72` — `JulesCapability`
  defines no `ontology` (inherits the empty default, `capability.py:29`).
- `agency/capabilities/workspace.py:20-21` — `Baseline` *node* schema =
  `["command", "passed"]` (output recorded at `:46` but not required); distinct
  namespace from artefact schemas, hence the `baseline` superset key is a name trap.
- `agency/capabilities/plugin.py:136,155` — `"kind": "authoring"` skill kinds;
  `plugin.py:139-169` — snake_case `produces:` slots; `agency/capabilities/develop.py:29-74`
  — `"kind": "discipline"` skill kinds, `develop.py:67` — `produces:["findings"]`.
  None are `record("Artefact", ...)` calls.
- `agency/memory.py:144-153` — `validate_schema(node_id, schema_id)`; **no
  production caller, no `Schema`-node creation** anywhere in `agency/`.
- `agency/ontology.py:25` — `Schema` node schema `["name", "required"]`;
  `ontology.py:43` — `VALIDATES_AGAINST` edge already enumerated; `ontology.py:60-86`
  — `OntologyExtension.schemas` "schemata live with the capability that owns them";
  `ontology.py:97` — `Ontology.schemas` starts empty.
- `research/templates-and-schemas/FINDINGS.md:6-29` — the 18-row matrix conflating
  slots/skill-kinds with artefact kinds (root of "18/13").
- `research/templates-and-schemas/schemas-catalogue.md:10-24` — the rejected 13-key
  `REQUIRED.update` superset.
- `the-agency-system/Plan/131-manifest-coverage-lint/spec.md` — prior-art
  keyspace-parity lint + "no placeholder entries for unemitted things" doctrine
  (the acceptance model for the slots→artefacts follow-up, spec 005).
