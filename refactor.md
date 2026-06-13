# refactor.md — Spec 286 OOP refactor (intent / plan / invariant per slice)

> **Exchange channel** (per PR #141 Review-Partner protocol, comment 4698430623):
> this file is the refactor agent's side; `Review.md` is the Vision owner's
> per-commit review. PR thread = blocking items + questions only.
>
> **Role:** this session is the **refactor agent** on
> `claude/agency-error-enum-fixes-13tpnf` — full **Spec 286** OOP refactor
> (spine + ports + leaf decomposition + capability-per-folder), behavior-
> preserving (zero contract / wire / verb-name change), formal spec lifecycle.
> Spec: `Plan/286-substrate-oop-refactor/spec.md`.

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
