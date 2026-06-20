---
spec_id: "353"
slug: looper-complete-port
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [1, 2, 3, 4, 6]
depends_on: ["003", "040", "043", "047", "091", "093", "152", "179", "283", "285", "292", "294", "297", "307", "322", "328", "334", "338", "339", "340", "345", "346"]
affects:
  - agency/capabilities/loop/
  - agency/_lifecycle_data/machines.json
  - docs/guide/capabilities.md
source-repos:
  - "looper @ netzkontrast/looper (Kevin Simback / @ksimback, MIT) — SKILL.md 7-stage wizard, scripts/looper.py (803 LOC), templates/run-loop.py (542 LOC), 2 JSON schemas, 4 rubrics + model-detection, 3 templates, ai-workflow-mapping example"
domain: loop / cluster-integration / capability
wave: looper-port
research_first: false
---

# Spec 353 — Looper Complete Port (master)

> **Master spec** — coordinates the seven child specs (354–360), one per concern.
> Child specs ship independently; this master tracks coherence, the looper→agency
> mapping, the ontology consolidation, and the "native-first with an export
> surface" reconciliation the user chose in the brainstorm gate.

## Why

[looper](https://github.com/ksimback/looper) is a Claude Code skill that
**designs agent loops before you run them**: it coaches a fuzzy automation idea
into a sharp goal, forces *checkable* verification (programmatic / judge / human),
wires in a **cross-model review council** (a reviewer or judge from a *different*
model family than the host), sets termination guards (iteration / revision /
no-progress / budget caps), and emits a portable loop spec + an in-session
handoff + an external Python runner. It is a **design layer that sits in front of
execution** — the layer where loops actually fail.

User directive (2026-06-20): *"Write several specs to completely Port looper into
Agency."* Brainstorm-gate decisions (recorded here so future audits do not flag
drift):

1. **Philosophy — native re-expression.** Looper's concepts are re-expressed on
   agency's substrate; there is **no standalone looper runtime** inside agency.
   The mapping is near 1:1 because looper and agency solve the same problem at
   the same layer.
2. **Scope — all four distinctive features preserved:** the cross-model council,
   the four coaching rubrics, the portable `loop.yaml` + compile, and the
   external `run-loop.py` runner.
3. **Decomposition — cluster master + children**, mirroring the Spec 093
   music-complete-port precedent.

The native re-expression + the kept portable-spec/external-runner reconcile to a
single doctrine: **native-first with a compatibility export surface.** The loop
lives natively on the substrate (an Intent, a Lifecycle machine, gates, a panel);
a dedicated emission verb projects it **out** to looper-compatible artefacts for
out-of-session / non-agency execution (§"The reconciliation").

### Why looper is the substrate's most natural port

Looper is not a domain application like music (Spec 093); it is a **meta-discipline
about agentic loops** — which is exactly what agency *is* (Goal 1: token-efficient
agentic loops; Goal 3: agent-uniform lifecycle). Every looper concept already has a
first-class agency primitive:

| Looper concept | Agency primitive | Anchor |
|---|---|---|
| goal + coaching | **Intent** (`intent_bootstrap` purpose/deliverable/acceptance) + clarity gate | Spec 307, 322; child **354** |
| typed verification (programmatic/judge/human) | **`gate`** capability — `gate.check`, typed `GateResult` | `agency/_coverage_gate.py`, Spec 328; child **355** |
| cross-model review council | **`panel`** + **`persona`** + **`delegate`/`jules`** | Spec 294, 297; child **356** |
| the loop shape + termination guards | a **Lifecycle machine** (`open · move · close`, any state machine) | Spec 339, 345; child **357** |
| the 7-stage wizard | a **walkable skill** (`SkillRun` phase-graph, `develop.skill_walk`) | Spec 003, 152, 346; child **358** |
| `state.json` / `run-log.md` | **Memory / provenance** — recorded by construction (Goal 2) | — (free); child **357** |
| `loop.yaml` / `loop.resolved.json` / `LOOP.md` | a **Document** + **Schema** (`CONFORMS_TO`) + `document.render` | Spec 043, 179, 283, 292; child **359** |
| `run-loop.py` external runner + `detect-models` | emitted runner template + **DriverRegistry** model resolution | Spec 002, 040; child **360** |
| cross-vendor egress consent + redaction | egress-consent gate + redaction globs (new, narrow) | child **360** |

**This is the next stress test of the drop-in-capability bar** (`CLAUDE.md`): if
the bar holds, the entire looper port is *one folder* under
`agency/capabilities/loop/` — verbs + ontology + docstrings-that-derive-skills + a
templates/ dir + a data/ dir for the four rubrics — plus **one** documented
substrate touch: a named `loop` machine in `agency/_lifecycle_data/machines.json`
(the Spec 345 registry is *designed* to be extended this way — adding a machine
is data, not an engine edit). Any edit beyond that is the bug to fix.

### The full looper surface (audit baseline)

Every path under the looper repo root gets a disposition. Appendix A is the
per-file verdict table; this is the roll-up.

| Looper aspect | Count / Description | Disposition |
|---|---|---|
| `SKILL.md` 7-stage wizard | 1 interview procedure | → walkable skill `loop-design` (child **358**) |
| `scripts/looper.py` | 803 LOC: `compile` / `render` / `session-prompt` / `detect-models` / `register-model` | `compile`/`render`/`session-prompt` → `loop.compile` + `document.render` (**359**); `detect-models`/`register-model` → `loop.detect_models` over DriverRegistry (**360**) |
| `templates/run-loop.py` | 542 LOC stdlib external runner | → `templates/run-loop.py` emitted verbatim-shaped by `loop.emit_runner` (**360**); its in-process twin is the Lifecycle machine walk (**357**) |
| `scripts/detect-models.py` | 12 LOC wrapper | → folds into `loop.detect_models` (**360**) |
| `schemas/loop.v1.schema.json` (190 LOC) + `loop.resolved.v1.schema.json` (25 LOC) | authoring + resolved JSON Schemas | → two agency **Schema** nodes; verbs `CONFORMS_TO` them (**359**) |
| `references/*.md` (4 rubrics + model-detection) | goal / verification / council / control rubrics | → `agency/capabilities/loop/data/rubrics/` (verbatim), surfaced per wizard stage (**354–357**, loaded by **358**) |
| `templates/loop.yaml`, `templates/README.md` | authoring scaffold | → `agency/capabilities/loop/templates/` + `document.render` (**359**) |
| `agents/openai.yaml` | a registered non-Claude council member | → a seed entry for `loop.detect_models` registry (**360**) |
| `commands/looper.md` | the `/looper` slash command | → absorbed by the walkable-skill slash mirror (`/agency-loop-design`, Spec 018) (**358**) |
| `examples/ai-workflow-mapping/` | end-to-end demo (loop.yaml + resolved + LOOP.md + RUN_IN_SESSION.md + run-loop.py) | → `agency/capabilities/loop/examples/` + the master E2E test (**360**) |
| `install.sh` / `install.ps1` | global-skill installer | **dropped** — agency installs via its own plugin install (Spec 333) |
| `pyproject.toml`, `LICENSE`, `.gitattributes`, `.gitignore` | packaging | **dropped/absorbed** — agency packaging; MIT attribution preserved in the cap docstring |
| `tests/` (fixtures + `test_looper.py`) | fake host/judge + runner tests | → behavioural parity in `tests/acceptance/test_loop_*.py` (invariants, not a test-count clone — `CLAUDE.md` rule 8) |

> **Nothing-left-on-the-floor check:** every file in Appendix A has a verdict.
> The four rubrics + templates + example are CONTENT artefacts — they ship as-is
> into `agency/capabilities/loop/{data,templates,examples}/`. The behaviour ports
> through verbs + a Lifecycle machine + a walkable skill. The infrastructure
> (installer, packaging, the looper CLI process, the model registry file)
> evaporates into agency substrate. ZERO unaccounted looper content.

### What "complete" means here (operating definition)

Complete behavioural parity, NOT 1:1 verb-name parity:

- **Every looper capability either becomes a verb / phase / machine on the
  substrate OR is explicitly DROPPED with justification** (Appendix A).
- **The seven looper wizard stages become the seven phases of one walkable skill**
  (`loop-design`), each loading its rubric at its stage (progressive disclosure,
  Spec 031) and **critiquing** before accepting — the coaching is the value.
- **Every verification criterion routes through `gate`** — programmatic via
  `gate.check`, judge via a council member's structured verdict, human via
  `elicit`. No bespoke check runner.
- **The loop's runtime IS a Lifecycle machine** — `plan → plan_gate → deliver →
  delivery_gate → done`, with revise edges and termination guards; the in-session
  run is the machine being walked, and `state.json`/`run-log.md` are replaced by
  graph reads (provenance is free).
- **The cross-model council routes through `delegate`/`jules` drivers + `panel`/
  `persona`** — a council member is a persona bound to a model driver; "a
  different family than the host" is coaching, not a hard rule.
- **The portable spec + external runner are an EXPORT surface**, not the primary
  runtime — `loop.compile` + `document.render` project the graph-native loop out
  to `loop.yaml` / `loop.resolved.json` / `LOOP.md` / `RUN_IN_SESSION.md` /
  `run-loop.py` for non-agency execution.

### What gets DROPPED (explicit non-port)

| Looper file/feature | Why dropped |
|---|---|
| `install.sh` / `install.ps1` | Global-skill installers; agency has its own plugin install (Spec 333) |
| `pyproject.toml` / `.gitattributes` / `.gitignore` | Looper packaging; agency packaging governs |
| the `looper.py` long-lived CLI process | Absorbed — the looper CLI's jobs become agency verbs (`loop.compile`, `loop.detect_models`) reached via `mcp__agency__{search,get_schema,execute}` |
| `~/.looper/models.json` registry file | Replaced by the agency config (Spec 334) + DriverRegistry (Spec 002) |
| `commands/looper.md` slash command | Absorbed by the walkable-skill slash mirror (Spec 018) |

That is ~6 items that **disappear into substrate**, not 6 missing features.

## The reconciliation — native-first, export-second (load-bearing)

The user kept BOTH "native re-expression" AND "portable `loop.yaml` + external
`run-loop.py`". These are not in tension; they are two surfaces over one resolved
loop:

```
            ┌──────────────────────  the loop lives in the graph  ──────────────────────┐
            │  Intent (goal)  ·  VerificationCriterion×N  ·  CouncilMember×N             │
            │  Lifecycle{machine:"loop"}  +  loop_control  ·  EgressPolicy               │
            └───────────────┬───────────────────────────────────────┬──────────────────┘
                            │ walk it natively                       │ project it out
                            ▼                                        ▼
              in-session execution (357)                  loop.compile + document.render (359)
              the agent advances the machine,             loop.yaml · loop.resolved.json
              gates fire, council convenes,               LOOP.md · RUN_IN_SESSION.md
              provenance recorded by construction         run-loop.py  (360, external runner)
```

`loop.resolved.json` is the **shared contract**: in-session execution and the
external runner both honour it. The graph is the source of truth; the resolved
JSON is a faithful projection. This is `CLAUDE.md` rule 2 (graph ⇄ files as peers,
the Document is where they meet) applied to a loop.

## Spec layout (the seven children)

| Spec | Concern | Substrate seam | Looper source |
|---|---|---|---|
| **354** | goal coaching | `intent` + clarity gate (322) + goal rubric | goal stage, `goal-rubric.md` |
| **355** | verification as gates | `gate` (`gate.check`, typed verdict) | verification stage, `verification-rubric.md`, criteria schema |
| **356** | cross-model council | `panel` + `persona` + `delegate`/`jules` | council stage, `council-rubric.md`, §6 detection |
| **357** | the loop control machine | a derived **Lifecycle machine** (345) + loop_control | `loop_control`, `control-rubric.md`, in-session run |
| **358** | the design wizard | a walkable skill (`SkillRun`, 346) | `SKILL.md` 7-stage interview, `/looper` |
| **359** | spec + emission | Document + Schema + `document.render` | `loop.yaml`/`.resolved.json`, schemas, `LOOP.md`/`RUN_IN_SESSION.md` |
| **360** | external runner + egress | emitted runner + DriverRegistry + consent gate | `run-loop.py`, `detect-models`, privacy/§9 |

### Verb manifest (target — per child; sums computed, not pinned)

| Child | User-facing verbs | Internal `*_gate`/helper | Notes |
|---|---|---|---|
| 354 goal | `frame_goal`, `critique_goal` | — | goal → root Intent + critique |
| 355 verify | `add_criterion`, `check`, `verify_report` | `criterion_gate` | typed verification on `gate` |
| 356 council | `add_member`, `convene`, `recommend_council` | `verdict_gate` | reviewer/judge, cross-family coaching |
| 357 machine | `open_loop`, `advance`, `loop_status`, `stop_reason` | `control_gate` | the Lifecycle `loop` machine + guards |
| 358 wizard | (walkable skill `loop-design`; no new verbs beyond `skill_walk`) | — | composes 354–357 + 359 |
| 359 emit | `compile`, `emit`, `render_handoff` | — | graph → `loop.yaml`/resolved/LOOP.md |
| 360 runner | `emit_runner`, `detect_models`, `register_model` | `egress_consent_gate` | external run-loop.py + model resolution |

> Counts are **targets**, refined in each child's manifest; the cap's live verb
> count is computed by `scripts/gen-capability-docs`, never pinned (`CLAUDE.md`
> rule 8).

## Design — the shared substrate (concerns common to all children)

### The `loop` capability (one folder)

```
agency/capabilities/loop/
├── __init__.py
├── _main.py            # LoopCapability(CapabilityBase); home = "lifecycle"
├── _compile.py         # graph → resolved spec (359)
├── _machine.py         # the "loop" machine definition + control evaluator (357)
├── schemas/            # ArtefactSchemas.from_module — loop-plan, delivery, review, verdict
├── data/rubrics/       # goal / verification / council / control (verbatim from looper)
├── templates/          # loop.yaml, run-loop.py, README, LOOP.md, RUN_IN_SESSION.md
├── examples/ai-workflow-mapping/
└── skills.py           # the loop-design walkable skill (358), OR derived on ontology
```

`home = "lifecycle"` clusters it with the lifecycle pillar (it parameterizes HOW
agentic work proceeds — like `frugal`, `mode`, `select`).

### Ontology (one `OntologyExtension`, merged via children)

```
LoopGoal          (statement, definition_of_done, context_sources)   # 354 — wraps the root Intent
VerificationCriterion (loop, kind, check, expect, rubric, prompt)     # 355  kind: programmatic|judge|human
CouncilMember     (loop, role, cli, model, family, scope, local)      # 356  role: reviewer|judge
LoopControl       (loop, max_iterations, max_revisions, budget, no_progress, human_checkpoints)  # 357
EgressPolicy      (loop, member, sends, redact, consent)              # 360
LoopArtefact      (loop, kind, iteration, path)                       # 357/359  kind: plan|delivery|review|verdict
```

Closed enums (relaxed per Spec 345 where they feed the machine):
- `(VerificationCriterion, kind)`: `programmatic / judge / human`
- `(CouncilMember, role)`: `reviewer / judge`
- the `loop` machine's states (registered in `machines.json`; the `(Lifecycle,
  state)` enum is the *union* of registered machines per Spec 345).

Artefact schemas (`act` verbs that produce a document): `loop-plan`, `delivery`,
`review`, `judge-verdict`, `loop-spec`, `run-in-session`.

### The `loop` Lifecycle machine (registered, not hard-coded — Spec 345)

A single named machine added to `agency/_lifecycle_data/machines.json`
(`# AGENCY-DRIFT: lifecycle-machines`), child **357** owns it:

```jsonc
"loop": {
  "initial": "planning",
  "states": ["planning","plan_gate","delivering","delivery_gate","completed","failed","canceled"],
  "transitions": {
    "planning":      ["plan_gate","canceled","failed"],
    "plan_gate":     ["planning","delivering","failed","canceled"],   // revise→planning | pass→delivering
    "delivering":    ["delivery_gate","canceled","failed"],
    "delivery_gate": ["delivering","completed","failed","canceled"],  // revise→delivering | pass→completed
    "completed": [], "failed": [], "canceled": []
  },
  "terminal": ["completed","failed","canceled"]
}
```

The orphan/terminal floor (Spec 340/345) holds per machine at load. Adding it is
**data, not an engine edit** — the drop-in bar survives.

### The provenance moat (the headline — net-new vs looper)

Looper writes `state.json` + `run-log.md` by hand; nothing connects a verdict to
the criterion it judged to the goal it served. In agency the whole loop is one
`memory_graph_provenance(intent_id)` traversal:

```python
result = await call_tool("memory_graph_provenance", {"intent_id": loop_goal_intent_id})
# result["serves"]    — every plan/delivery/revision invocation
# result["artefacts"] — every plan.md / delivery-N / review-N / verdict (LoopArtefact)
# result["gates"]     — every gate.check + judge verdict ledger entry
# result["agents"]    — every council member (persona+driver) that judged
```

Looper cannot do this (flat files, no graph). This is the one thing the complete
port exists to demonstrate at the loop layer.

## Done When (master-level coverage gates)

- [ ] **All seven child specs (354–360) ship Green** with their own Done-When
      gates met; each child's Followup is grounded (file:line evidence).
- [ ] **`agency/capabilities/loop/` is a live capability** discoverable via
      `python -m agency.cli search loop`, walkable via `develop.skill_walk`,
      CLI-mirrored, and MCP-wired — with no `examples/` shim (looper is a
      meta-discipline cap, first-class from the start, like the lifecycle pillar).
- [ ] **The drop-in bar holds AND is enforced:** porting looper requires ZERO
      edits to `agency/engine.py`, `agency/registry.py`, `agency/ontology.py`,
      `agency/capability.py` — the ONLY substrate touch is the `loop` entry in
      `machines.json` (data). `scripts/check-drop-in-bar` (from Spec 093) runs on
      every loop PR.
- [ ] **Looper-surface audit closed:** every row in Appendix A has a verdict
      (ported / dropped / absorbed). Regenerated on every child merge.
- [ ] **Provenance moat lit on a real loop:** an E2E test
      (`tests/acceptance/test_loop_e2e.py`) drives `frame_goal → add_criterion →
      add_member → open_loop → advance×N (through plan_gate + delivery_gate) →
      compile → emit` and asserts `memory_graph_provenance(intent_id)` returns the
      full chain. Lands in **360** (composes all upstream children).
- [ ] **Round-trip parity:** a loop authored natively, exported via `loop.compile`,
      and run by the emitted `run-loop.py` produces the same gate decisions as the
      in-session machine walk on the same fixtures (the looper fake-host/fake-judge
      fixtures, ported). Lands in **360**.
- [ ] **Doc-drift clean:** `docs/guide/capabilities.md` regenerates with the loop
      verbs (`scripts/gen-capability-docs`); `scripts/check-drift` Green.
- [ ] **`TODO.md` updated** with 353 + each child row (`CLAUDE.md` rule 4).
- [ ] **MIT attribution preserved** — the `loop` cap docstring credits looper
      (Kevin Simback, MIT) as the upstream design.

## Cluster coherence (CLAUDE.md rule 5)

Per Spec 047 (cluster-integration master), every new verb/skill lands in one of
the 13 SDLC+meta clusters. The loop children map to:

- 354 goal → **intent cluster** (extends goal framing/clarity)
- 355 verify → **gate cluster** (typed predicates + lifecycle pauses)
- 356 council → **delegation/review cluster** (panel/persona + cross-model dispatch)
- 357 machine → **lifecycle cluster** (a new registered machine; extends the pillar)
- 358 wizard → **skills cluster** (a walkable phase-graph; extends Spec 081 pattern)
- 359 emit → **document cluster** (graph→file render; extends Spec 179/283)
- 360 runner → **boundary cluster** (external process + driver resolution + egress)

No new cross-cluster decisions — each child extends an existing cluster's
integration pattern. The one genuinely new surface is the **egress-consent gate**
(360), a narrow specialization of the gate cluster.

## Migration order

```
354 goal ─┐
355 verify┤   foundation — parallel-safe (each touches an isolated seam:
356 council┤   intent / gate / panel+persona / machines.json)
357 machine┘
     │
     ▼
358 wizard (composes 354–357 as its phases; depends on all four)
     │
     ▼
359 emit (renders the machine + criteria + council to loop.yaml/resolved/LOOP.md)
     │
     ▼
360 runner (reads loop.resolved.json; carries the E2E + round-trip tests
            that flip 353 to Shipped)
```

**360 ships LAST** — it composes the resolved spec (359), drives the machine
(357), and its round-trip test cannot run until emission exists. The master 353
E2E lives in 360.

## Open questions (lean answers; resolved per child)

1. **Judge JSON enforcement** — looper degrades unparseable judge output to
   "revise + warn" (its `parse_judge_output`). Keep that (355/356): a malformed
   verdict is a `revise` with a `warning` field, never a hard crash.
2. **Host model in-session** — when running natively, the "host" that drafts
   plan/delivery is the current agent (via `ctx.host` sampling, Spec 285) or a
   delegated driver. The host is a council-adjacent role; 356 owns its resolution,
   357 consumes it.
3. **Egress when in-session** — the cross-vendor consent gate (360) fires for the
   *external runner* and for any in-session `delegate`/`jules` send to a non-local
   family. Local council members (e.g. `ollama`) are flagged no-egress.
4. **`loop` vs `looper` name** — the capability is **`loop`** (the noun agency
   reasons about); the upstream project is *looper*. No `/loop` collision: agency
   exposes `loop.*` verbs + the `loop-design` walkable skill, not a `/loop`
   scheduler (that is Claude Code's; see looper's own README comparison).

## Followup — Implementation Status (2026-06-20)

**Verdict:** Drafted (master + seven child specs authored this wave).

### Done
- Master spec authored (this file) with the looper→agency mapping, the
  native-first/export-second reconciliation, and Appendix A file audit.
- Brainstorm-gate decisions recorded (native re-expression; all four features;
  cluster master+children).
- Substrate seams grounded via CodeGraph: `Lifecycle.open/move/close`
  (`agency/lifecycle.py`), `phase`/`SkillRun` (`agency/skill.py`), `GateResult`
  (`agency/_coverage_gate.py`), `CapabilityContext` (`agency/capability.py`).
- Cluster coherence mapped to Spec 047; migration order fixed (360 last).

### Still
- Seven child specs drafted alongside this master (354–360) — each drives its own
  RED→GREEN→Refactor cycle.
- The E2E provenance test + the export round-trip test land in **360**.
- `scripts/check-drop-in-bar` extended to assert the loop port touches only
  `machines.json` (lands with the first implementation PR).

## Appendix A — looper file audit (per-path verdict)

Every path under the looper repo root (excluding `.git/`) has one verdict. This
table is the coverage gate: a child PR cannot close its Done-When if any row
mapped to its concern is still `unverdicted`.

| Looper path | Concern | Verdict | Lands in |
|---|---|---|---|
| `SKILL.md` | wizard | ported → walkable skill `loop-design` | 358 |
| `commands/looper.md` | wizard | absorbed → walkable-skill slash mirror | 358 |
| `references/goal-rubric.md` | goal | ported verbatim → `data/rubrics/` | 354 |
| `references/verification-rubric.md` | verify | ported verbatim → `data/rubrics/` | 355 |
| `references/council-rubric.md` | council | ported verbatim → `data/rubrics/` | 356 |
| `references/control-rubric.md` | machine | ported verbatim → `data/rubrics/` | 357 |
| `references/model-detection.md` | runner | ported verbatim → `data/rubrics/` | 360 |
| `scripts/looper.py` (`compile`/`render`/`session-prompt`) | emit | ported → `loop.compile` + `document.render` | 359 |
| `scripts/looper.py` (`detect-models`/`register-model`) | runner | ported → `loop.detect_models`/`register_model` | 360 |
| `scripts/detect-models.py` | runner | ported (folded into `loop.detect_models`) | 360 |
| `templates/run-loop.py` | runner | ported → `loop.emit_runner` template | 360 |
| `templates/loop.yaml` | emit | ported → `templates/` + `document.render` | 359 |
| `templates/README.md` | emit | ported → emitted README | 359 |
| `schemas/loop.v1.schema.json` | emit | ported → agency Schema node | 359 |
| `schemas/loop.resolved.v1.schema.json` | emit | ported → agency Schema node | 359 |
| `agents/openai.yaml` | runner | ported → seed registry entry | 360 |
| `examples/ai-workflow-mapping/*` | all | ported → `examples/` + E2E fixture | 360 |
| `tests/fixtures/*` (`fake_host`, `fake_judge`, `bad_judge`, `check_contains`) | runner | ported → acceptance fixtures | 360 |
| `tests/test_looper.py` | all | behavioural parity (invariants, not cloned) | 354–360 |
| `README.md`, `looper-spec.md` | docs | absorbed → this master + child specs | 353 |
| `install.sh`, `install.ps1` | infra | dropped — agency plugin install | n/a |
| `pyproject.toml`, `LICENSE`, `.gitattributes`, `.gitignore` | infra | dropped/absorbed (MIT credit in docstring) | n/a |

**Audit totals (computed, not pinned):** every repo path has a verdict —
ported, absorbed, or dropped — zero unverdicted. `scripts/audit-loop-port`
(lands with the 358 PR) regenerates this table from the looper tree and the
children's manifests and fails CI on any missing verdict.
