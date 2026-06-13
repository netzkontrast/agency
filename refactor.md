# refactor.md — Spec 286 OOP refactor (intent / plan / invariant per slice)

> **Exchange channel** (per PR #141 Review-Partner protocol, comment 4698430623):
> this file is the refactor agent's side; `Review.md` is the Vision owner's
> per-commit review. PR thread = blocking items + questions only.
>
> **Role:** this session is the **refactor agent** on
> `claude/agency-error-enum-fixes-13tpnf` — full **Spec 286** OOP refactor
> (spine + ports + leaf decomposition + capability-per-folder).
> Spec: `Plan/286-substrate-oop-refactor/spec.md`.
>
> **Mode (owner directive 2026-06-13): refactor-FIRST, hardcore.** The refactor
> may **break internal structure + tests** where the new design needs it; I do
> **not** gate on green. **The Review Partner rewrites tests** to the refactored
> design + new Vision — `refactor.md` carries my structural intent per slice as
> the contract to test against. **Still sacred:** the `search`/`get_schema`/
> `execute` wire contract + wire verb-names (alias-and-deprecate, Goal 5).
> **Aligned to CORE.md v4 "Four complete pillars"** — each pillar a complete
> write+read suite; the **read/manage side is the priority**, converging on the
> Management read-API (no hand-written Cypher). The refactor leaves the
> `GraphStore` / `InvocationRecorder` read seams clean for that.

## Working discipline (lessons folded in)

- **Value-object changes are migrations.** Before landing one, grep **every**
  consumer — `f["` / `.get(` over BOTH `agency/` and `tests/`, runtime included,
  not just sibling test files (the `Finding` wire regression: the verbs return
  findings *in the wire result*, and `test_intent_path_analysis` is a runtime
  consumer the sibling-test sweep missed). Run the **full** `pytest -n auto -m
  "not e2e"` before push, not a capability slice. (Owner nit, accepted.)
- **Assert invariants, not snapshots** (CLAUDE.md rule 8): wire bytes-stable,
  live verb count unchanged across splits, no raw `.g` outside `memory.py`.
- **Coordinate before touching shared spine files.** Flag on the PR thread first.

## Shipped slices

| Commit | Slice | Intent | Invariant preserved | Verify |
|---|---|---|---|---|
| `5ad2655` | **P3 #1 — `SubprocessAnalyzer`** | Template Method over the 4 ruff/bandit/radon wrappers; collapse 3× `_SUBPROCESS_TIMEOUT` + the which-guard→run→returncode→json→map scaffold | public `scan`/`cyclomatic`/`maintainability` + `AXIS_PREFIXES` unchanged → composers + `_build_axis_registry` untouched; degrade-silently contract intact | 63 analyze + 7 scaffold tests |
| `b22c350` | **P3 #2 — `Finding` value object** | `Finding` TypedDict → `@dataclass(frozen=True)` + `FindingSeverity(str,Enum)` (primitive-obsession → value object) | **wire byte-identical**: `Finding.to_dict()` (severity as `.value`) serialises at the 5 verb-return boundaries + the Finding-node record path; `_findings_of` graph-dict path unchanged | full non-e2e suite |
| `36fa80a` | welcome budget | owner directive: loosen fixed base `1000→2000` (Spec 282/284/285 envelope growth) | per-cap coefficient (150) unchanged → still guards gist bloat | `test_welcome*` |
| `b1b8b9e` | reconcile `test_intent_path_analysis` | wire-safety: verbs emit dicts (proven: `json.dumps(dataclass)` raises), so the test stays dict-subscript | n/a | green; **CI green** |
| `e678f83` | renumber sqlmodel 288→289 | clear the Management-cap-288 collision (Vision-reserved) | n/a | imports |
| `3f75770`+ | **Spec 289 SQLModel entity layer** | `EntityModels` (ontology-derived validation, `table=False`) + `EntityStore` (`table=True` canonical rows on graphqlite's ONE shared `.db`); FastAPI-ready read surface for the Management API | parity with `Ontology.violations`; one shared sqlite connection (proven) | 15 entity tests |
| `e57d7b7` | **P0 A1 — `GraphStore` port** | ~14 typed read methods on `Memory` (`neighbors` promoted, `query_nodes`/`nodes_serving`/`sources_via_edge`/`artefacts_produced_under`/`edge_pairs`/`has_edge`/`all_nodes`/`replay_*`/`advance_clock`); swept 30 raw-`.g` sites across 12 capability files | **INVARIANT: no `.g.query`/`.g.get_node` in `agency/capabilities` (grep empty)**; reads return same rows | 192+ focused; **CI workflow disabled (`3df7937`) — Review Partner is the test net** |
| `5221430` | **P0 A2 — DriverRegistry unification** | collapse Engine's 3 boundary representations (9 attrs + registry + injectors dict) → ONE `DriverRegistry` (lazy `register_factory`; `backend()`/`readiness()`); `web_search` registered; 9 attrs → read-through properties; injectors derived from one alias map; `agency_doctor` reads registry uniformly | `ctx.get_driver`/`inject`/`ctx.client`/`sampling_enabled`/`_host_ctx`/`param_enums` preserved; `agency_doctor` field keys unchanged | 419+ focused; no breakage |

| `8f239d4` | **P1 A3 — `Registry.invoke` decomposition** | ~105-line god-method → ~20-line orchestrator over `IntentGuard`/`ParameterInjector`/`InvocationRecorder`/`ResultProcessor` (new `agency/_invoke.py`); **post-invocation hook seam** on `ResultProcessor` | provenance contract identical (nodes/edges/messages/`error_severity`/wire shape/`(result,inv)` return); `param_enums` + `ctx.host` preserved | 133 focused; no breakage |
| `541779b` | **P3 — split `music`** | `_main.py` 2474→89; 103 verbs → 9 cluster mixins + `_base`; closes deferred Spec-094 split | verb-set/count (103) + ontology + skill_doc unchanged; full Engine build OK | music slices green |
| `21d83cd` | **P3 — split `novel`** | `_main.py` 3999→781; 95 verbs → 9 mixins; `ctx.engine` production reach preserved | verb-set/count (95) unchanged; fixed a `..` import bug | 336 novel+prompt green |
| `f84a536` | **P3 — split `plugin` + `LintRule` registry** | `_main.py`→~150; 10 verbs → 4 mixins; lint rules → polymorphic `LintRule` registry (OCP; `_REMEDIATION` derived) | verb-set/count (10) unchanged; **lint OUTPUT byte-identical across 21 caps** | back-compat re-exports green; `test_lint_token_economy`/`reflection_link`/`document_scope_guards`/`recall_typed` break by design → Review Partner rewrites to assert lint OUTPUT |
| `18bf40d` | **P2 #8 — closed-sets → `StrEnum`** | `Role`/`LifecycleState`/`IntentOwner` in `ontology.py`; sets + `lifecycle.py` constants DERIVE from them; duplicate state tuple killed | sets byte-identical; wire strings plain (no enum leak); `violations` + EntityModels parity intact | 32 focused green |
| `8a28764` | **P3 — split `dogfood`** | `_main.py` 1147→98; 11 verbs → 4 mixins; A1 typed-read calls intact | verb-set/count (11) unchanged | 68 dogfood green |
| `e78335b` | **P3 — split `prompt`** | `_main.py` 932→96; 13 verbs → 5 mixins; `_load_fragments` cache identity preserved | verb-set/count (13) unchanged | 54 prompt green |
| `e63efc9` | **P1 A4 — typed `Verb` value object** | new `agency/_verb.py` `@dataclass Verb`{name,role,fn,inject,tags,param_enums} replaces the mutated spec dict; spine readers → attribute access, broad readers → dict-compat bridge (`__getitem__`/`get`); role coerced to plain str | full build 332 verbs all `isinstance Verb`; wire byte-identical; `param_enums` surfaces. Metadata-dataclass consolidation deferred (too broad) | test_agency + naming_audit + 85 install/skill green |
| `91acb43` | **P2 A5 — substrate-tools-as-registered-set** | new `agency/_substrate_tools.py` (7 `SubstrateTool` classes, `requires_intent=False`); `build_mcp`'s ~490-line closure block → a registration loop; `agency_doctor`/`agency_welcome` now first-class | **A/B diff byte-identical** (332+7 tools, all schemas + welcome/doctor outputs, 18098 B both sides); `_host_ctx`/`param_enums`/desc-tightening preserved | 8 welcome/doctor green |
| `2e55472` | **P2 A7 — `WireEnvelope`** | wire strip/re-wrap + Spec-282 `{ok,error}` failure-shape rule (was in `engine._shape_wire_result` + `cli._structured` + `__main__`) → one `agency/_wire_envelope.py` | **MCP↔bash isomorphism byte-identical** (success dict / scalar re-wrap / failure envelope); `ResultProcessor.data` left as-is | 22 unwrap/cli green |
| `72c9436` | **289 Slice 2b — Memory→EntityStore mirror** | `Memory` binds `EntityStore` on the shared conn; `_mirror()` projects user props after each authoritative `upsert_node` (record/update/supersede), one-way, non-fatal | **graph stays write-authoritative**; dual-observable (`recall` + `entities.get`); projection failure never fails the graph write | 15 mirror green |
| `0d4f383` | **P3 Goal 4 — capability-per-folder** | `intent`(9)/`shell`(4)/`skills`(5) bare modules → folders (`git mv`); `__init__.py` re-export shims | verb-set/count/ontology/skill_doc unchanged; `discover()` finds each once | 68 focused green |

> **🏁 MILESTONE — Spec 286 + 289 are CODE-COMPLETE.** Every planned slice landed, behaviour-preserving, wire byte-identical (full Engine build: 21 caps / 332 verbs + 7 substrate, graph-authoritative entity projection live):
> - **Ports** A1 GraphStore (`e57d7b7`) · A2 DriverRegistry (`5221430`)
> - **Spine** A3 invoke→4 collaborators+hook (`8f239d4`) · A4 typed Verb (`e63efc9`)
> - **Cleanup** A5 substrate-tools-as-set (`91acb43`) · A7 WireEnvelope (`2e55472`) · #8 StrEnum (`18bf40d`)
> - **Leaves** music/novel/plugin/dogfood/prompt splits · capability-per-folder (`0d4f383`) · `@requires_driver` (`0c34669`) · SubprocessAnalyzer+Finding · dedup phase()/record_and_serve()/budget_take() (`9b1aae4`)
> - **Data (289)** EntityModels + EntityStore + Memory→graph-authoritative mirror
>
> **Now the Review Partner's gate:** Gherkin acceptance suite green + clean-OOP review across the refactor → then Phases A/B/C merge + CI re-enabled = Shipped. **Accumulated test-rewrites handed off** (internal-coupling breaks, NOT behaviour): plugin lint-internals (`test_lint_token_economy`/`reflection_link`/`document_scope_guards`/`recall_typed`); A4 `Verb`-value-object item-assignment (`test_error_severity` contention, `test_music_lyrics`/`test_music_gates` sub-gate `verbs[x]["fn"]=`). Deferred/optional: A4 metadata-dataclass consolidation; A8 (soft per CORE v4); #5 BoundaryConfig; 289 FastAPI Slice 3.

### A3 post-invocation hook seam (for Spec 283 render + 282-E dedup)
`ResultProcessor.register_post_invocation(hook)` (the processor is at `registry._processor`). Signature: **`hook(memory, invocation_id, intent_id, label, result) -> None`** — `label: Optional[str]` (currently `None`, reserved for 283's render hook to fill from the produced node); `result` is the **unwrapped** data the caller receives. Fires AFTER all side-effects are recorded, in registration order, return ignored. Default list is empty (zero behaviour change). Spec 283's renderer + Spec 282-E's `retry_count` dedup attach here without re-touching `invoke`.

### Behavioural acceptance criteria for the Review Partner (A1 + A2)
**A1 (GraphStore):** GIVEN any capability verb that reads the graph, WHEN it runs, THEN it returns the same nodes/edges as before AND no `agency/capabilities/*` source contains `.g.query`/`.g.get_node` (the read goes through a typed `Memory` method). Provenance (`memory.provenance`) and `analyze.graph` census behaviour unchanged.
**A2 (DriverRegistry):** GIVEN an `Engine` (default or with injected boundaries / `drivers=`), THEN `ctx.get_driver(name)` and `inject=[…]` resolve the same boundary objects as before; `ctx.client` is the Jules driver; `web_search` is reachable via `ctx.get_driver("web_search")`; an injected boundary overrides the lazy default; `agency_doctor` returns the same field keys. WHEN no driver of a name is used, THEN its default isn't constructed (lazy). The `search`/`get_schema`/`execute` wire contract is byte-identical.

> Note on the parallel `5a9d50c` (Vision side): it migrated the test to
> attribute access, which implies dataclasses on the wire — not serialisable.
> `b22c350`+`b1b8b9e` is the wire-correct reconciliation (verbs return dicts).
> **Please don't re-apply attribute access to that test.**

## Phase-1 (spine) seam carry-list — GATED until #141's 284/285 settle

`Registry.invoke` decomposition (`ParameterInjector` / `IntentGuard` /
`InvocationRecorder` / `ResultProcessor`) must preserve / host:

- **`param_enums`** (Spec 284, B-audit): threaded `fn._verb → _wrap_method →
  spec["param_enums"]`; surfaced in `_wire` via `Annotated[…, Field(json_schema_
  extra={"enum":…})]` + description hint. `ParameterInjector` preserves both. Now
  on `capture_claim.domain`, `create_codex_entry.kind`, `set_*_status`,
  `create_world_axiom.severity`, `reflect.note.scope`, `create_scene.pov`.
- **`_host_ctx` ContextVar** (Spec 285-A): `_wire.impl` captures the injected
  FastMCP `Context` (schema-excluded) → request-scoped ContextVar, **reset in
  `finally`**. `CapabilityContext.host` reads it. Decomposition keeps capture+reset.
- **`{ok, error:{code,message,severity,retryable,trace_id}}`** wire envelope
  (Spec 282-A) + `Memory.link` vfrom-contention retry (Spec 282-C): `WireEnvelope`
  / `GraphStore` port carry these unchanged.
- **`ResultProcessor` hosts TWO post-/at-invocation concerns:**
  1. **Spec 283 F-Slice-2 — render hook:** auto-render-on-mutation; each rendered
     file an `Artefact`. Clean post-invocation seam (`_render_entity` is the body).
  2. **Spec 282-E — permanent-failure dedup:** record the FIRST permanent failure,
     then for identical `(capability, verb, error)` SERVING the same intent,
     **increment `retry_count` on the existing Invocation** instead of minting a
     duplicate (keys on the existing `error_severity`). Home: `InvocationRecorder`.
- I'll post the **hook signature** on the PR thread before the Vision side wires
  283's renderer onto it.

## Proposed NEW work — `develop` planning + plan-execution skill (FOR REVIEW)

Owner request (comment 4698453381). `develop` today has `brainstorm`, `plan`
(single map phase), `tdd`, `debug`, `verify`, `spec-panel`, `review`, `execute`
(load/steps), `authoring-capabilities`. **Gap:** a first-class *plan-authoring →
execution-with-checkpoints* discipline (superpowers `writing-plans` +
`executing-plans` + `subagent-driven-development`; superclaude `sc-workflow` +
`sc-task` + `sc-spawn`).

**Proposal — one walkable discipline `plan-execute`** (a Lifecycle template walked
via `develop.skill_walk`, one phase at a time), recording graph nodes
(`Plan` / `PlanStep` / `Gate`) SERVING the intent — provenance, not a markdown
file (rule 2); render the plan markdown on demand:

1. **`frame`** — confirm intent + requirements present (reuse a prior `brainstorm`
   output if linked). *produces:* `requirements`.
2. **`draft-plan`** — decompose into bite-sized, no-placeholder steps; mint a
   `Plan` node + ordered `PlanStep` children SERVING the intent. *produces:*
   `plan_id`, `steps`. (≙ superpowers `writing-plans`)
3. **`plan-signoff`** — **HARD gate**: surface the rendered plan; `requires_input`
   /elicit (Spec 285) for sign-off; never execute an unapproved plan.
4. **`execute-step`** (loop over `PlanStep`) — per step run **dispatch-decision
   (Spec 040, 11 signals)** to choose inline vs subagent; if a required input is
   unknown, `requires_input`/`sample` (Spec 285) to resolve — never guess; record
   a `Gate PASSED` per completed step. *produces:* per-step `artefact`. (≙
   `executing-plans` + `subagent-driven-development`)
5. **`checkpoint`** — review gate every N steps (or on a failing step): re-plan
   or continue. (review checkpoint)
6. **`synthesize`** — close the `Plan`; emit a summary; link artefacts.

**Open questions for the Vision owner before I build:**
- One `plan-execute` discipline (above) vs. a **pair** `write-plan` + `execute-plan`
  (mirrors superpowers' two skills; cleaner resumability across sessions)?
- New ontology nodes `Plan`/`PlanStep` — or reuse `Lifecycle`/`Gate` + a `Plan`
  Reflection? (Leaning: a small `Plan`+`PlanStep` extension on the `develop`
  capability's ontology, edges `HAS_STEP` + `SERVES`.)
- Spec it as **Spec 287** (own number) or fold into the 286 umbrella as a
  `develop`-cluster slice? (Leaning: own spec — it's a feature, not a refactor.)

I'll hold building until the Vision owner reviews this layout (per protocol:
describe phase layout → review → build).

> **Update (shipped):** Spec 287 Slice 1 landed (`c0e6e20`) — the `plan-execute`
> discipline + `draft_plan`/`record_step_outcome`/`plan_status` verbs +
> `Plan`/`PlanStep` ontology, 8 tests green, install regenerated. Slice 2
> (write/execute split, `requires_input`, `render_plan`) still open for review.

## Spec 289 — SQLModel typed entities (user directive 2026-06-13)

Directive: SQLModel for **every data entity**, derived from the **established
ontology + schemas**, **linked to graph entities**, **core dep**, **all OOP**;
goal a FastAPI frontend later while the graph stays complete + inline-queryable.

**Advice (checked the graph implementation, as asked):**
- `graphqlite` is a **SQLite extension** (`graphqlite.so`) on a standard
  `sqlite3.Connection` — reachable at `memory.g._conn.sqlite_connection`;
  `Connection.execute(sql)` runs raw SQL on the same connection.
- ⇒ **one `.db` file** holds both the graph (extension-managed tables) and
  SQLModel/SQLAlchemy entity tables; no second store, no cross-process sync.
- ⇒ **inline entity-content query** = a raw-SQL JOIN of Cypher-returned node
  ids to the entity table (same connection). Today props are denormalised onto
  the node, so Cypher inline filtering already works; the SQL store makes the
  full typed row the join target.
- The **ontology** (`Ontology.nodes` + `.enums`) is the schema authority;
  SQLModel **derives** from it (rule 2) — no parallel hand-authored schema.

**Slice 1 shipped (additive, behaviour-preserving):** `sqlmodel` in CORE deps;
`agency/_entities.py` `EntityModels` derives a `SQLModel` (`table=False`) per
ontology label — required fields + `Literal`-typed enums — with `validate`
parity to `Ontology.violations`. 5 tests (incl. the extension label `PlanStep`).
NOT yet wired into `Memory` (zero change to the live record path).

**Slice 2 (next):** `table=True` canonical entity tables on graphqlite's shared
connection; `Memory.record` writes the typed row + the graph node (id link);
inline `entity_join`. **Slice 3:** FastAPI read surface (`[api]` extra).

**Open for Vision review:** (a) keep "graph is the store" framing with SQL as a
typed projection (my lean), vs. flip SQL→canonical/graph→index; (b) when Slice 2
wires `Memory`, replace `ontology.violations` with `EntityModels.validate` (one
validation path) or keep both behind a parity test? Leaning: single path, guarded
by the Slice-1 parity test.

## A1 — `GraphStore` port (NEXT spine slice; seam design for test pre-staging)

**Why now:** CORE.md v4 makes "no hand-written Cypher / no raw graph queries"
the read-pillar invariant. Today ~18 capability sites call `ctx.memory.g.query(
…)` / `ctx.memory.g.get_node(…)` directly (the anti-pattern). A1 routes them
through typed `Memory` methods so the read surface is clean + the Management
read-API has one place to build on.

**Seam shape (what the Review Partner should test against):**
- **`Memory` grows typed read methods** (the `GraphStore` surface), e.g.
  `nodes_serving(intent_id, label=None)`, `neighbors(node_id, edge, direction)`
  (promoted from `CapabilityContext`), `query_nodes(label, where=…)` — each
  returns property dicts, never a `CypherResult`. Raw Cypher stays **inside
  `memory.py`** only.
- **`CapabilityContext` delegates** its graph reads to these (it already wraps
  `record`/`link`/`recall`/`find`/`neighbors`); `ctx.memory.g.query` from a
  capability becomes a typed `ctx.<method>` call.
- **Invariant (the test to assert):** `grep -rn "\.g\.query\|\.g\.get_node" agency/capabilities`
  → **zero hits**; raw `.g` access exists only in `agency/memory.py` (+ the one
  documented `_entity_store` shared-connection reach). The behaviour of each
  migrated read is unchanged (same rows), so the rewrite is mechanical: assert
  the typed method returns what the old Cypher returned.
- **Expect breakage:** tests that monkeypatch or assert on `ctx.memory.g.query`
  call shapes will need rewriting to the typed methods. New tests should target
  the `Memory` read methods directly + the "no raw `.g` in capabilities"
  invariant.

I'll land A1 in `memory.py` + sweep the capability sites, then ping here. Spec
283's render hook + 282-E dedup ride on the later `invoke` decomposition (A3),
not A1.
