---
spec_id: "004"
slug: "template-schema-coverage"
status: superseded
state: superseded
superseded_by: "032"
last_updated: 2026-05-31
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

# Spec 004 — Wire the Generate/Validate Loop End-to-End for Two Recorded Artefact Kinds

> **SUPERSEDED by Spec 032 (2026-05-31).** The materialiser core ("registry without enforcement" gap) is preserved in `Plan/superseded/032-templates-schemas-oop-extensions/spec.md` §D — Spec 032 generalizes it: schemas + templates become file-based OOP capability extensions (`ArtefactSchemas` / `RenderTemplates` dataclasses on `CapabilityBase`), and the materialiser uses bi-temporal supersede on shape change rather than destructive upsert (panel F-4). Spec 004's 2 specific artefact kinds (`jules-session`, `reduction`) migrate as part of Spec 032 Tasks 4.2 + 4.3. **Do not implement this spec directly — work from Spec 032.**

*(RUNG 1 toward verb-param schema-as-single-source — see "Where this sits" below.)*

## Why

CORE.md:66 names the generate/validate pair — `Schema` and `Template` as ordinary
Memory nodes — as the typed/generative layer: a capability `act` renders an Artefact
`DERIVED_FROM` a `Template`, which `VALIDATES_AGAINST` its `Schema`, checked by
`Memory.validate_schema` (`agency/memory.py:144`) against the schema node's
`required` fields. **In the live engine today that loop is test-proven, not
production-wired.** `grep -rn 'validate_schema\|VALIDATES_AGAINST' agency/` returns
only the definition (`memory.py:144`) and a docstring (`templates.py:6`); the only
place the pair runs end-to-end is the test suite (`tests/test_agency.py:324-357`,
`:501-508`), where the **test itself** hand-records the `Schema` node
(`mem.record("Schema", …)`, `:332`/`:503`) and hand-links the edge (`:344`). So
CORE.md:78-80's "Proven runnable in `agency/`" reads correctly only as
*test-proven*; in production `Ontology.schemas` is a registry with no enforcement
point — no code records a `Schema` node, links `VALIDATES_AGAINST`, or calls
`validate_schema`. 004's purpose is to close that gap *in production* for the two
uncovered recorded kinds, via the `Schema`-node materialiser promoted into Design
below. (This is the exact "registry without enforcement" gap the spec exists to
close — stated up front, not buried.)

Today the strict required-field schemas live in `REQUIRED`
(`agency/templates.py:72`) and cover exactly **5 kinds**:

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

## Where this sits — RUNG 1 of the isomorphism ladder

The canon names a larger prize than this spec delivers, and 004 must point AT that
axis instead of silently deferring it. CORE.md:67-72 makes the **verb-param schema**
first-class — "**Design intent:** one schema per verb renders three ways (MCP
`inputSchema`, the Skill's frontmatter, the bash CLI's arg parser) — the
*isomorphism glue* … making the ontology schema the single source is **the next
step**." That is the canon's stated single-source-of-truth, and it is shaped by the
verb's INPUT contract, not an artefact's output contract.

004 deliberately covers the *narrower, output* axis — artefact-kind schemas for two
recorded kinds — because it is the **minimal runnable proof** of the node+edge
mechanism (`Schema` node → `VALIDATES_AGAINST` → Artefact) that the verb-param work
will reuse. Position 004 as **RUNG 1**: prove the generate/validate loop runs
end-to-end in production for two kinds. The next rung is its own future spec:

- **NEXT RUNG (its own spec, 006) — verb-param schema as the single source.**
  Materialise one `Schema` node per verb signature so the MCP `inputSchema`, the
  Skill frontmatter, and the bash CLI arg parser all derive from one ontology node
  (CORE.md:68-72, "the isomorphism glue"). 004 builds the materialiser this rung
  reuses; it does NOT itself touch verb-params.
- **PARALLEL FOLLOW-UP (spec 005) — slots→artefacts.** Rewrite `develop`/`plugin`
  verbs so each `produces:` slot is recorded as an Artefact and schema'd (see the
  namespace audit below). A separate feature, not the isomorphism axis.

End-state target across the three namespaces (audited below): artefact-`kind`s →
`Schema` nodes (004 + 005); **verb-params → the single `Schema` node rendered three
ways (006, the canonical glue)**; skill-`kind`s stay skill metadata, not artefacts.
004 is rung 1; without naming the ladder it would point the wrong way.

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
004 wires the validate side via the **`Schema`-node materialiser** specified in
Design — it is the load-bearing change, not an optional extra. In brief: the engine
records one `Schema` node per `Ontology.schemas` entry, and the two newly covered
verbs link their recorded Artefact `VALIDATES_AGAINST` the matching `Schema` node
(the `VALIDATES_AGAINST` edge already exists in `EDGE_TYPES`, `ontology.py:43`), so
the provenance subgraph is complete and the round-trip test has a real `schema_id`
to assert on. See Design → "The `Schema`-node materialiser" for placement,
idempotency, and the all-entries scope.

(Note the generate half — recording `Template` nodes and the `DERIVED_FROM` edge —
stays unproven in production; 004 wires only the validate half, by design. This is
no longer optional-vs-wire: wiring the validate side is the spec's reason to exist,
since an unwired schema is the same "registry without enforcement" gap 004 closes.)

## Done When

- [ ] `agency/capabilities/jules.py` and `agency/capabilities/delegate.py` carry a
      capability-owned schema for their recorded kind (see Design); no schema is
      added for any kind no code records.
- [ ] `delegate.join` records a `reduction` Artefact with the full required field
      set (`parent_intent`, `children`, `summary`), derived from `join`'s own
      query rows.
- [ ] `jules.dispatch` records a `jules-session` Artefact with the full required
      field set (`session_id`, `url`, `state`, `history`).
- [ ] `Ontology.materialise_schemas(memory)` runs once at engine construction (after
      all extensions merge) and records one `Schema` node per `Ontology.schemas`
      entry — including the 5 existing covered kinds, retroactively wiring them — and
      is idempotent (upsert-keyed on `schema:{name}`). Each new verb links its
      Artefact `VALIDATES_AGAINST` the matching `Schema` node, so
      `Memory.validate_schema` has a `schema_id` to check against.
- [ ] A round-trip test, per new kind, records the Artefact and asserts
      `Memory.validate_schema(artefact_id, schema_id)` returns `True`; an Artefact
      missing a required field returns `False` (the schema bites). The round-trip is
      **validate-only**: the generate-side `DERIVED_FROM` → `Template` edge is
      explicitly OUT of scope for 004 (no `Template` nodes recorded; the new
      generators stay `string.Template` constants — see Design).
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

### The `Schema`-node materialiser (the load-bearing change)

This is the single architectural advance in 004 and the thing the verb-param rung
(006) reuses, so it lives in Design, not in an Open Question. It turns
`Ontology.schemas` from an inert in-memory registry into `Schema` *nodes* on the
graph that `Memory.validate_schema` can target.

**What it does.** Materialise one `Schema` node per `Ontology.schemas` entry:
`node_id = f"schema:{name}"`, `props = {"name": name, "required": ",".join(required)}`
(the `Schema` node schema is `["name", "required"]`, `ontology.py:25`;
`validate_schema` splits `required` on commas, `memory.py:152`).

**Where it runs.** A small `Ontology.materialise_schemas(memory)` helper invoked once
during engine construction, **after every discovered capability's `OntologyExtension`
has been merged** (so the effective `Ontology.schemas` is complete) and after Memory
is wired with the effective ontology (so the `Schema` records pass enforcement).
Placement decision is settled here — it is not an Open Question.

**Idempotency.** Materialising is keyed by the deterministic `node_id =
f"schema:{name}"`, so a re-init (or a second engine over the same Memory) upserts the
same node rather than duplicating. Use an upsert/`record`-if-absent on that id; the
helper must be safe to call more than once.

**Scope — it runs for ALL `Ontology.schemas` entries, not just the 2 new ones.**
The materialiser does not special-case `reduction`/`jules-session`. It iterates the
whole registry, so the **5 already-covered plugin kinds get `Schema` nodes too**,
retroactively wiring them — 004 silently makes the existing 5 production-validatable
as well, a bigger change than the title admits and one the canon applauds. State this
in the PR. (The 5 keep their `REQUIRED` field lists byte-identical; only their graph
presence as `Schema` nodes is new.)

**The new verbs link the edge.** `delegate.join` and `jules.dispatch` link their
recorded Artefact `VALIDATES_AGAINST` `schema:reduction` / `schema:jules-session`,
so the round-trip test has a real `schema_id` to assert on.

**Half the canon pair only — `DERIVED_FROM` stays unproven in production.** 004 wires
the *validate* side (`Schema` node + `VALIDATES_AGAINST`). It does **not** record
`Template` nodes, so the canon's generate-provenance edge `Artefact -DERIVED_FROM->
Template` (CORE.md:74-76) remains test-only after 004 — the new `JULES_SESSION` /
`DELEGATION_REDUCTION` stay `string.Template` constants (mirroring the existing 5,
which are also never recorded as `Template` nodes in production). This is a deliberate
RUNG-1 cut: prove the validate half end-to-end now; recording `Template` nodes and
closing `DERIVED_FROM` is left to a follow-up (alongside the 006 single-source work).
The round-trip test 004 ships is therefore validate-only; do not claim the generate
half is production-wired.

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
  - `agency/ontology.py` — add `Ontology.materialise_schemas(memory)`: records one
    idempotent `Schema` node per `Ontology.schemas` entry (all entries, incl. the
    existing 5). The engine calls it once at construction after all extensions merge
    (see Design → "The `Schema`-node materialiser"). State the exact call site in the PR.
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
2. **RESOLVED (moved to Design → "The `Schema`-node materialiser").** Placement,
   idempotency, and the all-entries scope of the `Schema`-node materialiser are no
   longer open: it is `Ontology.materialise_schemas(memory)`, run once at engine
   construction after all extensions merge, upsert-keyed on `f"schema:{name}"`, and
   it materialises a `Schema` node for **every** `Ontology.schemas` entry (incl. the
   existing 5). See Design. The only remaining latitude is the exact module the
   helper's body lives in (`ontology.py` recommended); state the choice in the PR.

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

## Followup — Implementation Status (2026-05-31)

> Consolidation pass on branch `claude/plan-spec-review-74gHM`. Frontmatter `status:` may be stale; this section reflects verified code state.

**Verdict:** Not started

### Done
- `VALIDATES_AGAINST` edge type exists in the core ontology (`agency/ontology.py:43`); `Memory.validate_schema` is defined (`memory.py:144`); `Ontology.schemas` is populated by the plugin capability (`plugin.py:179` via `templates.REQUIRED`). These are pre-existing.
- `REQUIRED` in `agency/templates.py:93-99` still covers exactly the 5 plugin-owned kinds — unchanged from the pre-spec state.

### Still to implement
- `JULES_SESSION` and `DELEGATION_REDUCTION` `string.Template` constants are absent from `agency/templates.py`.
- `delegate.join` (`delegate.py:189`) records a `reduction` Artefact with only `{"kind": "reduction", "children": children}` — missing the required fields `parent_intent`, `summary`; no `schemas=` in `delegate`'s `OntologyExtension` (`delegate.py:57-62`).
- `jules.dispatch` (`jules.py:214`) records `{"kind": "jules-session", "session": sid, "url": ...}` — field named `session`, not `session_id`; missing `state` and `history`; `JulesCapability.ontology` (`jules.py:140-153`) has no `schemas=` entry.
- `Ontology.materialise_schemas(memory)` helper is absent — no `Schema` nodes are ever recorded in production; `validate_schema` has no `schema_id` to target.
- Round-trip generate/validate tests per new kind are absent.

### Refinement needed (given later specs)
- The spec positions itself as "RUNG 1 toward verb-param schema-as-single-source" pointing at Spec 006 for the next rung. Spec 006 in this plan is `core-hardening` (unrelated). The verb-param schema rung likely maps to Spec 019 (`engine-output-shape-contract`) in the current plan — coordinate naming.
- Plan/000-overview.md:57 lists Spec 004 in the Wave-1 backlog. No active work; depends on Spec 003 (`skill-phase-objects`) which is also not started.

### Evidence
- code: `agency/templates.py:93-99` (5 kinds, unchanged); `agency/capabilities/delegate.py:57-62,189`; `agency/capabilities/jules.py:140-153,214`; `agency/memory.py:144` (`validate_schema` defined but has no production callers)
- tests: none for the new kinds or the materialiser
- commits/notes: frontmatter `status: draft`; Plan/000-overview.md:57 lists in Wave-1 backlog.
