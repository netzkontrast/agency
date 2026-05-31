---
spec_id: 008
slug: superclaude-analysts
status: draft
owner: "@agency"
depends_on: [001, 003]
affects:
  - agency/capabilities/transmute.py
  - agency/capabilities/develop.py
  - skills/analyze/SKILL.md
  - skills/brainstorm-discovery/SKILL.md
  - skills/business-panel/SKILL.md
  - docs/vision/specs/superclaude-analysts-port.md
  - tests/test_transmute_capability.py
  - tests/test_transmute_skills.py
source-repos:
  - "https://github.com/SuperClaude-Org/SuperClaude_Framework @ 226c45cc93b865108843a669c6545d421784b68c"
  - "https://github.com/SuperClaude-Org/SuperClaude_Plugin @ de431dcc37aa6754be4a8d1be8c83cc834ac9dd5"
estimated_jules_sessions: 4
domain: capability
wave: 1
---

> **Read `Plan/JULES_PROTOCOL.md` (or `AGENTS.md`) before starting.** This is an
> ADDITIVE spec: BUILD the named-but-unbuilt `transmute` capability file
> (`transmute.py`) that self-registers and auto-wires; extend `develop` only where
> a phase-graph belongs. Only modify the paths under `affects:`. Source repos are
> clone-and-read-only into `~/work/vendor/` — never commit them. **The canon wins;
> code serves it** (`docs/vision/CORE.md`): this port POPULATES a cluster the canon
> already maps (`CAPABILITY-CLUSTERS.md:20`), it does NOT mint a new primitive. If
> anything is ambiguous, stop and open `[BLOCKED: clarification]` — do not guess.

# Spec 008 — transmute: the analysis/transform facet (SuperClaude port)

## Why

SuperClaude ships its craft as **two layers Agency does not yet have a home for**:

1. **An analysis surface** (`/sc:` commands): `brainstorm`, `spec-panel`,
   `analyze`, `design`, `troubleshoot`, `business-panel`, `explain`, `estimate`,
   `reflect`. These are *transform-shaped* analytical disciplines — they read a
   target and emit findings/recommendations, mutating nothing external. (`/sc:`
   commands that are NOT analysis — the build/session/MCP-install surface,
   including `select-tool` which only routes between the Serena/Morphllm MCP
   backends Agency does not have — are out of scope; see the coverage table.)
2. **A persona + mode model**: 20 analyst agent files (`requirements-analyst`,
   `quality-engineer`, `root-cause-analyst`, `system-architect`,
   `security-engineer`, `performance-engineer`, `refactoring-expert`, …) and 7
   behavioral MODE files (`Brainstorming`, `Business_Panel`, `Introspection`,
   `Orchestration`, `Task_Management`, `Token_Efficiency`, `DeepResearch`). Only
   `Brainstorming` and `Business_Panel` back real skills; the other five either
   map onto existing Agency substrate or are dropped (see the mode table).

In SuperClaude these lean on **system-prompt pressure** (persona prose, FLAGS,
RULES, PRINCIPLES). Agency's thesis (per `docs/vision/specs/superpowers-port.md`)
is that this pressure becomes **structure**: an analytical discipline is a
role-tagged verb or a walkable gated skill; a persona is an *expert lens* the
verb iterates over (judgment-as-data), not a separate agent runtime. This spec
ports the `sc:` analysis surface and the persona/mode model into Agency's
`Capability` + `Skill` model, REPLACING the SuperClaude install for analysis use.

**Where it lands — `transmute`, not a new primitive.** The `/sc:` analysis surface
is *stateless compute over a target* (read → findings, mutating nothing external) —
which is exactly the `transform` role. The canon already RESERVES a named home for
this: `transmute` | `transform` | "pure functions over artefacts: views, indexes,
summaries, tool-list shaping | **the open `transform` set**" (`CAPABILITY-CLUSTERS.md:20`).
That cluster is *specced-but-unbuilt* (`agency/capabilities/transmute.py` does not
yet exist). So this port does NOT mint a new `analyze` top-level primitive — that is
the exact bloat the canon warns against (`CAPABILITY-CLUSTERS.md:26-33`: "Most clusters
are **facets of the four concepts**, not new top-level primitives … Multiplying
concepts would re-introduce bloat"; `CORE.md:139-141`: the census found "the four
concepts + the engine absorb it all"). It instead BUILDS `transmute` by **populating
that facet** with the analytic read-verbs + the `Analysis` ontology. The surface grows
exactly as the canon prescribes — by dropping a file into `capabilities/` that fills a
cluster the map already lists (`CORE.md:143-144`). Net-new top-level primitives: **0**.

Agency already has `spec-panel` (the `develop` skill + `skills/spec-panel/`) and
`brainstorm` (the `develop` skill). Those are SuperClaude's `spec-panel` and
`brainstorm` in all but name — this spec must NOT re-port them; it must reuse the
existing `develop` skills and add only the **net-new** analytical verbs and the
persona/mode substrate that the existing two lean on implicitly.

## Done When

- [ ] The named-but-unbuilt `transmute` capability is BUILT as a self-registering
      file at `agency/capabilities/transmute.py` (home `capability`/`transform`), the
      canon's "open `transform` set" (`CAPABILITY-CLUSTERS.md:20`). The engine
      `discover()`s it and auto-wires one MCP tool per verb (no central registration).
      `python -c "from agency.engine import Engine; e=Engine(); assert 'transmute' in
      e.registry.names()"` passes.
- [ ] `transmute` carries an `OntologyExtension` registering an `Analysis` node type
      (fields: `target`, `dimension`, `findings`) and a `dimension` enum
      `{quality, security, performance, architecture}` — exactly the **four** focus
      axes of `/sc:analyze` (`commands/sc-analyze.md:20`, `--focus
      quality|security|performance|architecture`). There is NO fifth value:
      `maintainability` is a *refactoring-expert* concern (`agents/
      sc-refactoring-expert.md`), not an `analyze` axis. The enum is closed *for the
      `Analysis` node*, enforced by `Ontology.violations()` (`ontology.py:136-138`)
      — `Ontology.extend` only widens enums, it never closes them. Merge is strict
      (no core-label redefinition); tests assert the merged ontology accepts an
      `Analysis` node and rejects a bad `dimension` (e.g. `maintainability`).
- [ ] `transmute.analyze(target, dimension)` (**transform**) returns a structured,
      **severity-ranked** finding set over the named dimension (severity ordering is
      a hard rule from `commands/sc-analyze.md:31` "Severity-based prioritization",
      re-expressed as a lint-style transform on the finding set, not prose).
      `transmute.troubleshoot(symptom)` (**transform**) returns ranked root-cause
      hypotheses + next probes — **diagnosis only**. (Source `/sc:troubleshoot` has
      a `--fix` step that *mutates* — `commands/sc-troubleshoot.md:33` "Resolve:
      Apply appropriate fixes"; Agency splits it: diagnosis = `transmute.troubleshoot`
      transform, the fix loop = the existing gated `develop` `debug` discipline. This
      is canon-correct: `capability.md:67` "A capability spanning two roles … is split
      by role".) `transmute.estimate(scope)` (**transform**) returns an
      effort/complexity band. `transmute.explain(subject, level)` (**transform**)
      returns a layered explanation. Each records an Invocation that SERVES the intent.
- [ ] `transmute.lens(persona)` (**transform**) returns a named expert lens
      (the persona's review questions + priorities + anti-patterns) as DATA — the
      mechanism by which `spec-panel`/`analyze`/`business-panel` iterate experts.
      The persona catalogue lives as a table in `transmute.py`, NOT as separate agent
      files. SuperClaude ships **20** agent files (`agents/sc-*.md`, excluding
      `sc-README`); **18 are pure analysis lenses** and become `lens()` rows, **2
      orchestrate and are dropped-not-lens** (`pm-agent`, `deep-research-agent`; see
      below and the catalogue table under Design). `lens()` resolves command-declared
      persona aliases (`commands/sc-estimate.md:7` `personas: [architect,
      performance, project-manager]`; `commands/sc-explain.md:7` `personas:
      [educator, architect, security]`) — e.g. `educator`→`learning-guide`,
      `project-manager`→`pm-agent`-as-lens. `transmute.lens("requirements-analyst")`
      returns the requirements lens. (Persona-as-lens-DATA is canon-endorsed:
      `capability.md:62-66` and `CORE.md:64-80` "judgment-as-data"; a persona that does
      NO lifecycle work is correctly NOT an agent — `CORE.md:33-35`.)
- [ ] `transmute.mode(name)` (**transform**) returns a behavioral mode descriptor
      (trigger, posture, output-shape) so a caller can adopt a mode without a
      system-prompt edit. `mode` is a closed enum of **at most 3** genuine
      descriptors — `{brainstorming, business-panel, introspection}` — NOT 7.
      `brainstorming` backs the existing `develop` `brainstorm` skill;
      `business-panel` backs `skills/business-panel/`; `introspection` is a pointer
      to the `reflect` capability. The other four MODE files do not become
      descriptors (`Task_Management`→Lifecycle/Memory; `Orchestration`,
      `Token_Efficiency`, `DeepResearch`→dropped; see the mode table under Design).
- [ ] Three installable skills exist under `skills/`: `analyze` (walkable
      `analyze`-discipline phase-graph), `business-panel` (multi-expert business
      critique, a sibling of the existing `spec-panel`), and `brainstorm-discovery`
      (the Socratic requirements-discovery flavour — only if it is materially
      distinct from the existing `brainstorm` skill; see Open Questions). Each
      SKILL.md passes `plugin.lint_skill` (Use-when, third person, ≤500 chars).
- [ ] The `develop` skill set gains a `design` discipline (architecture/API/
      component/database design phase-graph). `/sc:design` is materially DISTINCT
      from `plan`: `commands/sc-design.md:24-28` is an *interface/architecture*
      flow (Analyze → Plan → Design → Validate → Document) producing
      specifications, whereas `develop`'s `plan` (`develop.py:34-38`) is an
      *implementation* step-list (`map → self-review → approve`). Different
      artefacts → a new discipline, e.g. `analyze (requirements, context) → design
      (spec/interface) → validate (meets-requirements) [hard gate]`.
- [ ] The persona/mode "pressure" (FLAGS, RULES, PRINCIPLES) is re-expressed as
      structure where it gates behaviour: any RULE that is actually a hard
      constraint becomes a `gate.check` call site or a `lint`-style transform, NOT
      prose. Pure stylistic guidance is dropped (documented in the port doc).
- [ ] `docs/vision/specs/superclaude-analysts-port.md` records the full coverage
      mapping (every `/sc:` command + every persona + every MODE → Agency target →
      covered/new/dropped) in the style of `superpowers-port.md`.
- [ ] `tests/test_transmute_capability.py` and `tests/test_transmute_skills.py` are
      GREEN; the existing suite still passes (`pytest -q`).
- [ ] No SuperClaude source is copied into the tree. We re-express its disciplines
      in Agency's model; vendor source stays read-only under `~/work/vendor/`.

## Source clones (run first)

```bash
git clone --depth=1 https://github.com/SuperClaude-Org/SuperClaude_Framework.git \
  ~/work/vendor/superclaude-framework   # SHA 226c45cc93b865108843a669c6545d421784b68c
git clone --depth=1 https://github.com/SuperClaude-Org/SuperClaude_Plugin.git \
  ~/work/vendor/superclaude-plugin      # SHA de431dcc37aa6754be4a8d1be8c83cc834ac9dd5
```

Read for the analysis surface: `src/superclaude/commands/{analyze,design,
troubleshoot,brainstorm,spec-panel,business-panel,explain,estimate,reflect}.md`
(NOT `select-tool` — it is dropped MCP-routing plumbing). For personas:
`src/superclaude/agents/*.md`. For modes:
`src/superclaude/modes/MODE_*.md`. For pressure-machinery: `src/superclaude/core/
{RULES,FLAGS,PRINCIPLES}.md`. The Plugin repo mirrors these under `commands/sc-*.md`,
`agents/`, `modes/`, `skills/` — diff the two; the Plugin is the deployed shape.

## Design

The port lands as **the built-out `transmute` capability (the open `transform` set)
+ a small set of skills + a `develop` skill**. Rationale, citing the canon map: the
`/sc:` analysis surface is stateless compute over a target (read → findings), which
is exactly the `transform` role — and the canon already NAMES that home as
`transmute` (`CAPABILITY-CLUSTERS.md:20`: `transmute` | `transform` | "pure functions
over artefacts: views, indexes, summaries, tool-list shaping | the open `transform`
set"). Severity-ranked findings, an effort band, a layered explanation, a persona
lens, a mode descriptor are *precisely* "pure functions over artefacts" (read →
derived view, no external mutation). So this port POPULATES the `transmute` facet
rather than minting a new `analyze` primitive the cluster census did not surface
(`CAPABILITY-CLUSTERS.md:26-33`, `CORE.md:139-141`) — the plan and the canon map now
agree. Personas are **not agents** in Agency — an Agency agent is a Lifecycle
parameterization (`delegate`), and analysis personas do no external work; they are
*lenses* (data the verb iterates). Modes are **not a runtime** — they are descriptors
a caller adopts.

### Verbs to add (capability `transmute`, home `transform`)

| verb | role | what |
|---|---|---|
| `analyze` | transform | severity-ranked findings over a `dimension` (quality/security/performance/architecture — the **4** `/sc:analyze` axes) |
| `troubleshoot` | transform | ranked root-cause hypotheses + next probes for a symptom (diagnosis only; fix loop = `develop` `debug`) |
| `estimate` | transform | effort/complexity band for a scope |
| `explain` | transform | layered explanation of a subject at a level |
| `lens` | transform | a named persona's expert lens (questions/priorities/anti-patterns) as data; resolves command-declared aliases |
| `mode` | transform | a named behavioral mode descriptor (trigger/posture/output-shape); enum ≤3 |

`select_tool` is **NOT a verb** here — `/sc:select-tool` only routes between the
Serena and Morphllm MCP backends (`commands/sc-select-tool.md:6,34`,
"Serena (semantic operations) vs Morphllm (pattern operations)"), neither of
which exists in Agency (one FastMCP engine). It is install-environment plumbing,
not analysis, and is dropped (see the coverage table). `reflect` from
`/sc:reflect` is the existing `reflect` capability (split-covered, see below) —
not re-ported.

### Skills to add (installable Lifecycle templates under `skills/`)

The walkable skill is still named `analyze` (the user-facing discipline keeps the
SuperClaude name); only the *capability* that hosts the verbs is `transmute`.

| skill | kind | phase-graph (→ hard gate) |
|---|---|---|
| `analyze` | discipline | `scope` (target, dimension) → `examine` (findings) → `report` (recommendations) [gate] |
| `business-panel` | discipline | `select-experts` → `critique` (per-lens findings) → `synthesize` [gate] |
| `brainstorm-discovery` | discipline | (only if distinct from existing `brainstorm`) Socratic `probe` → `converge` → `confirm` [gate] |

A new `design` discipline is also added to `develop`'s `DEV_SKILLS` (in
`develop.py`, not under `skills/` as a port artefact): `analyze (requirements,
context) → design (spec/interface) → validate (meets-requirements) [gate]`.

### Persona catalogue (the 20 agent files → lens rows)

The lens thesis holds for every IN-SCOPE persona: every remaining agent
explicitly disclaims doing external work (even the `engineering`-tagged
architects — `agents/sc-system-architect.md` "Will Not: Implement detailed code",
`sc-backend-architect.md` "Will Not: Manage infrastructure deployment",
`sc-devops-architect.md` "Will Not: Write application business logic") — so they
are pure **design/analysis lenses**, returned as data by `transmute.lens()`. The
**only** two personas that DO orchestrate are already out of scope (their commands
are dropped), so no in-scope persona is an agent:

| agent file | `category:` | disposition |
|---|---|---|
| `sc-requirements-analyst`, `sc-root-cause-analyst`, `sc-deep-research` | analysis | **lens** |
| `sc-quality-engineer`, `sc-performance-engineer`, `sc-refactoring-expert`, `sc-security-engineer`, `sc-self-review` | quality | **lens** |
| `sc-system-architect`, `sc-backend-architect`, `sc-frontend-architect`, `sc-devops-architect` | engineering | **lens** (design lenses; disclaim doing work) |
| `sc-learning-guide`, `sc-socratic-mentor`, `sc-technical-writer` | communication | **lens** |
| `sc-python-expert` | specialized | **lens** |
| `sc-repo-index` | discovery | **lens** |
| `sc-business-panel-experts` | business | **lens** (a YAML catalogue of `key_questions`+`focus_areas`+`analysis_framework` — judgment-as-data) |
| `sc-pm-agent` | meta | **dropped — orchestrates.** `agents/sc-pm-agent.md:528` "operates as a meta-layer above specialist agents", `:520` "Will Not: Execute implementation tasks directly (delegates …)". Command `/sc:pm` dropped. |
| `sc-deep-research-agent` | analysis | **dropped — effects.** `agents/sc-deep-research-agent.md:95` "Tool Orchestration" dispatches Tavily/Playwright/Context7 (external web side-effects), not a pure lens. Command `/sc:research` dropped. |

That is 18 lens rows + 2 dropped = the full 20-file catalogue.

### Mode classification (the 7 MODE files → disposition)

The earlier draft assumed all 7 modes become a `mode()` enum; the source forces a
per-mode call. `transmute.mode()` is a closed enum of **≤3** genuine descriptors:

| MODE file | what it is | Agency disposition |
|---|---|---|
| `MODE_Brainstorming` | Socratic requirements discovery | **covered** — backs `develop` `brainstorm`; descriptor `transmute.mode("brainstorming")` |
| `MODE_Business_Panel` | 9-expert panel runtime (Expert Engine + 3-phase pipeline) | **covered** — backs `skills/business-panel/`; descriptor `transmute.mode("business-panel")` |
| `MODE_Introspection` | meta-cognitive self-analysis (`--introspect`) | **cover-by-`reflect`** — descriptor `transmute.mode("introspection")` points at the `reflect` capability |
| `MODE_Task_Management` | hierarchical Plan→Phase→Task→Todo + write_memory | **cover-by-Lifecycle+Memory** — this IS Agency's `Lifecycle`/`Memory` substrate; NOT a descriptor |
| `MODE_Orchestration` | Serena/Morphllm/Magic tool-routing matrix | **dropped** — same two-MCP plumbing as `select-tool`; no Agency analogue |
| `MODE_Token_Efficiency` | symbol-compression communication styling | **dropped** — pure system-prompt styling (superpowers-port: "pressure does NOT port") |
| `MODE_DeepResearch` | research mindset backing `/sc:research` | **dropped** — backs the dropped `/sc:research`/deep-research-agent |

### Coverage table (counterpart → Agency target → status)

| SuperClaude item | Agency target | status |
|---|---|---|
| `/sc:brainstorm` + `MODE_Brainstorming` | `develop` skill `brainstorm` (exists) + `transmute.mode("brainstorming")` | **covered** |
| `/sc:spec-panel` | `develop` skill `spec-panel` + `skills/spec-panel/` (exists) | **covered** |
| `/sc:analyze` | `transmute.analyze` + `skills/analyze/` | **new** |
| `/sc:troubleshoot` | `transmute.troubleshoot` (diagnosis) + existing `develop` `debug` (the `--fix` loop) | **new (split)** |
| `/sc:design` | new `develop` skill `design` (distinct from `plan`; `sc-design.md:24-28`) | **new** |
| `/sc:estimate` | `transmute.estimate` | **new** |
| `/sc:explain` | `transmute.explain` | **new** |
| `/sc:business-panel` + `MODE_Business_Panel` | `skills/business-panel/` + `transmute.lens(business-expert)` | **new** |
| `/sc:reflect` | memory aspect → `reflect` capability; "are we done"/task-adherence aspect (`sc-reflect.md:24-26`) → `gate.check` + `develop` `verify` | **covered (split)** |
| `/sc:select-tool` + `MODE_Orchestration` | DROP — Serena-vs-Morphllm MCP routing (`sc-select-tool.md:6,34`); no Agency analogue (one FastMCP engine) | **dropped** |
| `/sc:{implement,build,test,document,improve,cleanup,git,task,spawn,pm,workflow,index,save,load,research,recommend}` | out of scope (build/session/MCP-install surface, not analysis) | **dropped** |
| 18 in-scope `agents/*.md` personas | `transmute.lens(persona)` — lenses as data | **new** |
| `agents/sc-pm-agent` (meta), `agents/sc-deep-research-agent` (analysis) | orchestrate/effect → not lenses; their commands `/sc:pm`,`/sc:research` already dropped | **dropped** |
| `MODE_{Brainstorming,Business_Panel,Introspection}` | `transmute.mode(name)` descriptors (≤3) — see mode table | **new/covered** |
| `MODE_Task_Management` | Agency `Lifecycle` + `Memory` substrate | **covered** |
| `MODE_{Token_Efficiency,DeepResearch}` | pure styling / dropped-command backing | **dropped** |
| `core/{RULES,FLAGS,PRINCIPLES}.md` | hard rules → `gate`/lint checks; stylistic → dropped | **partial** |
| MCP install machinery (`setup-mcp`, `verify-mcp`, `install.sh`, `cli/`) | out of scope (Agency is one FastMCP engine; no installer port) | **dropped** |

## Files

- **Create**:
  - `agency/capabilities/transmute.py` — BUILD the named-but-unbuilt `transmute`
    capability, the open `transform` set (`CAPABILITY-CLUSTERS.md:20`): the analytic
    read-verbs + `OntologyExtension` (`Analysis` node) + persona/mode tables.
  - `skills/analyze/SKILL.md` — walkable `analyze` discipline.
  - `skills/business-panel/SKILL.md` — multi-expert business critique.
  - `skills/brainstorm-discovery/SKILL.md` — Socratic discovery (conditional; see Open Questions).
  - `docs/vision/specs/superclaude-analysts-port.md` — the full coverage mapping.
  - `tests/test_transmute_capability.py`, `tests/test_transmute_skills.py`.
- **Modify**:
  - `agency/capabilities/develop.py` — add a `design` discipline to `DEV_SKILLS`
    (`/sc:design` is distinct from `plan`; Q2 resolved).
- **Move / Delete**: none. (No new top-level capability is minted; `transmute` is a
  cluster the canon already lists — this builds it.)

## Open Questions / Needs Research

Q1–Q4 are **RESOLVED against source** by the spec-panel review (see `REVIEW.md`)
and are now baked into the Design above. Q5 is narrowed. Q6 is the one genuinely
open canon-shape question (raised by `VISION-REVIEW.md`).

0. **`transmute` (fold) vs. amend-canon (mint a distinct `analyze`).** *(Open —
   canon-shape; the one real decision.)* This spec REHOMES the analysis surface onto
   the canon's already-named-but-unbuilt `transmute` cluster (`CAPABILITY-CLUSTERS.md:20`,
   the open `transform` set) rather than minting a new `analyze` top-level primitive —
   per the `VISION-REVIEW.md` ruling **FOLD, don't mint** (`CAPABILITY-CLUSTERS.md:26-33`
   warns a 12th primitive the cluster census never surfaced is bloat). **Alternative,
   if the maintainer judges `analyze` a *distinct* facet** (e.g. "transmute =
   data-shaping; analyze = judgment-bearing findings"): that case is legitimate, but
   "the canon wins; code serves it" (`CLAUDE.md`) requires it be made **in the canon
   FIRST** — amend `CAPABILITY-CLUSTERS.md:10-24` to add an `analyze` row + a
   fold-vs-distinct rationale in the verdict (`:26-43`) — landed BEFORE any code, so
   the map never silently disagrees with the tree. Pick one before coding; the spec as
   written takes the fold path (preferred — it matches the existing map, 0 net-new
   primitives).

1. **Personas → lenses, not agents.** **RESOLVED → lenses, for every in-scope
   persona.** Two personas DO orchestrate/dispatch — `pm-agent` is a meta-layer
   that delegates (`agents/sc-pm-agent.md:528,520`) and `deep-research-agent`
   orchestrates external Tavily/Playwright/Context7 calls
   (`agents/sc-deep-research-agent.md:95`) — but **both are already out of scope**
   (their commands `/sc:pm`, `/sc:research` are in the dropped bucket). So no
   in-scope persona orchestrates; every one that ports is a pure `transmute.lens()`
   row. Decided — not a blocker.
2. **`design` vs `plan`.** **RESOLVED → distinct; ADD `design`.**
   `commands/sc-design.md:24-28` is an interface/architecture flow producing
   specifications; `develop`'s `plan` (`develop.py:34-38`) is an implementation
   step-list. Different artefacts → new `develop` `design` discipline.
3. **Modes: enum vs skills vs nothing.** **RESOLVED → per-mode (see the mode
   table).** NOT all-7-enum. 2 back skills (`Brainstorming`→`brainstorm`,
   `Business_Panel`→`business-panel`); `Introspection`→`reflect`;
   `Task_Management`→Lifecycle/Memory; `Token_Efficiency`/`DeepResearch`/
   `Orchestration`→dropped. The `mode` enum is therefore **≤3**.
4. **`select-tool` vs the engine `search`.** **RESOLVED → DROP.**
   `/sc:select-tool` is solely Serena-vs-Morphllm MCP routing
   (`commands/sc-select-tool.md:6,34`); neither backend exists in Agency. It is
   neither net-new value nor a `search` duplicate — it is environment plumbing.
   The `select_tool` verb is removed; the command sits in the dropped coverage row.
5. **RULES/FLAGS/PRINCIPLES as structure.** *(Open — narrowed.)* Most of
   `core/{RULES,FLAGS,PRINCIPLES}.md` is stylistic and drops per the
   superpowers-port "system-prompt pressure does NOT port" thesis. The HARD rules
   to re-express as structure: (a) evidence-before-claim / "are we done"
   validation → `gate.check` + `develop` `verify`; (b) the analyze
   severity-prioritization rule (`commands/sc-analyze.md:31`) → a lint-style
   transform on the finding set. Enumerate the full hard set explicitly in the
   port doc; resolve the remainder during the port-doc pass.

## Evidence

- `~/work/vendor/superclaude-framework/src/superclaude/commands/*.md` — the `/sc:`
  analysis surface (analyze, design, troubleshoot, brainstorm, spec-panel,
  business-panel, explain, estimate, reflect). `select-tool` is read only to
  confirm it is Serena/Morphllm MCP plumbing (dropped).
- `~/work/vendor/superclaude-framework/src/superclaude/agents/*.md` — the **20**
  agent files (18 in-scope lenses: requirements-analyst, root-cause-analyst,
  deep-research, quality-engineer, performance-engineer, refactoring-expert,
  security-engineer, self-review, system-architect, backend-architect,
  frontend-architect, devops-architect, learning-guide, socratic-mentor,
  technical-writer, python-expert, repo-index, business-panel-experts; 2 dropped
  orchestrators: pm-agent, deep-research-agent).
- `~/work/vendor/superclaude-framework/src/superclaude/modes/MODE_*.md` — the 7 modes.
- `~/work/vendor/superclaude-framework/src/superclaude/core/{RULES,FLAGS,PRINCIPLES}.md`
  — the pressure machinery to re-express or drop.
- `~/work/vendor/superclaude-plugin/{commands/sc-*.md,agents/,modes/,skills/}` — the
  deployed shape (diff vs Framework).
- Agency prior art: `agency/capabilities/develop.py` (existing `brainstorm`,
  `spec-panel` disciplines — DO NOT re-port), `agency/capabilities/reflect.py`
  (covers `/sc:reflect`), `agency/capability.py` + `agency/ontology.py` (the
  `CapabilityBase`/`@verb`/`OntologyExtension` contract), `skills/spec-panel/SKILL.md`
  (the SKILL.md shape to mirror), `docs/vision/specs/superpowers-port.md` (the
  pressure→structure thesis and port-doc format).
- Canon (the rehome rationale): `docs/vision/CAPABILITY-CLUSTERS.md:20` (`transmute`
  = the open `transform` set, "pure functions over artefacts") + `:26-43` (the
  "few primitives" verdict — folding facets, not minting primitives);
  `docs/vision/CORE.md:139-144` (the cluster census; "grow the capability set by
  dropping files into `capabilities/`"). `agency/capabilities/transmute.py` does NOT
  exist yet — this spec BUILDS it (the cluster is specced-but-unbuilt).

## Followup — Implementation Status (2026-05-31)

> Consolidation pass on branch `claude/plan-spec-review-74gHM`. Frontmatter `status:` may be stale; this section reflects verified code state.

**Verdict:** Not started

### Done
- Nothing from this spec has shipped. `agency/capabilities/transmute.py` does not exist (`ls agency/capabilities/` confirms). No `skills/analyze/`, `skills/business-panel/`, or `skills/brainstorm-discovery/` directories exist under `skills/`. No `tests/test_transmute_capability.py` or `tests/test_transmute_skills.py`. No `docs/vision/specs/superclaude-analysts-port.md`.
- The `develop` capability already ships `brainstorm` and `spec-panel` disciplines that 008 must NOT re-port (`agency/capabilities/develop.py:29-61`) — these are prior art, not deliverables of this spec.

### Still to implement
- `agency/capabilities/transmute.py` — the entire `transmute` capability (verbs: `analyze`, `troubleshoot`, `estimate`, `explain`, `lens`, `mode`; `Analysis` node + `dimension` enum in `OntologyExtension`; 18-persona lens table; mode enum ≤3).
- `skills/analyze/SKILL.md`, `skills/business-panel/SKILL.md`, `skills/brainstorm-discovery/SKILL.md` — all three discipline skills.
- `develop` `design` discipline added to `DEV_SKILLS` — not present in `agency/capabilities/develop.py:28-99`.
- `docs/vision/specs/superclaude-analysts-port.md` — the coverage mapping doc.
- `tests/test_transmute_capability.py`, `tests/test_transmute_skills.py`.

### Refinement needed (given later specs)
- Spec 016 (`capability-authoring-doctrine`) landed `develop.scaffold_capability` (`develop.py:249`) and `plugin.lint_capability` (`plugin.py:279`) in block mode. Implementation of 008 MUST begin with `develop.scaffold_capability(name="transmute", kind="light")` and the resulting `transmute.py` MUST carry the `# agency-scaffold: v1` marker so `plugin.lint_capability("transmute")` runs in block mode.
- Spec 023 (adaptive-disclosure) requires every verb's docstring brief slice ≤ 120 chars; `lint_capability` enforces this in block mode. All six `transmute` verbs must satisfy the budget.
- Spec 024 (capability-authoring-discipline) requires the scaffold-first workflow; the `authoring-capabilities` skill in `DEV_SKILLS` (`develop.py:86-98`) is the prescribed entry point.
- The `Q0` open question (fold into `transmute` vs mint `analyze` as a distinct primitive) remains the key canon-shape decision and must be resolved in `CAPABILITY-CLUSTERS.md` before any code — the spec takes the fold path but notes the alternative explicitly.

### Evidence
- code: no `agency/capabilities/transmute.py`; `agency/capabilities/develop.py:29-61` (prior art `brainstorm`/`spec-panel` that must not be re-ported); `agency/capabilities/develop.py:249` + `agency/capabilities/plugin.py:279` (Spec 016 scaffold/lint substrate now available)
- tests: none for transmute
- commits/notes: `Plan/000-overview.md` classifies 008 as "Wave-1 backlog — revisit when canon needs new ground"; no implementation commit found in `git log --oneline --all`
