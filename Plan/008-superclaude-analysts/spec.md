---
spec_id: 008
slug: superclaude-analysts
status: draft
owner: "@agency"
depends_on: [001, 003]
affects:
  - agency/capabilities/analyze.py
  - agency/capabilities/develop.py
  - skills/analyze/SKILL.md
  - skills/brainstorm-discovery/SKILL.md
  - skills/business-panel/SKILL.md
  - docs/vision/specs/superclaude-analysts-port.md
  - tests/test_analyze_capability.py
  - tests/test_analyze_skills.py
source-repos:
  - "https://github.com/SuperClaude-Org/SuperClaude_Framework @ 226c45cc93b865108843a669c6545d421784b68c"
  - "https://github.com/SuperClaude-Org/SuperClaude_Plugin @ de431dcc37aa6754be4a8d1be8c83cc834ac9dd5"
estimated_jules_sessions: 4
domain: capability
wave: 1
---

> **Read `Plan/JULES_PROTOCOL.md` (or `AGENTS.md`) before starting.** This is an
> ADDITIVE spec: drop a new capability file (`analyze.py`) that self-registers and
> auto-wires; extend `develop` only where a phase-graph belongs. Only modify the
> paths under `affects:`. Source repos are clone-and-read-only into `~/work/vendor/`
> — never commit them. **The canon wins; code serves it** (`docs/vision/CORE.md`).
> If anything is ambiguous, stop and open `[BLOCKED: clarification]` — do not guess.

# Spec 008 — SuperClaude Analysts + Command/Mode Framework

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

Agency already has `spec-panel` (the `develop` skill + `skills/spec-panel/`) and
`brainstorm` (the `develop` skill). Those are SuperClaude's `spec-panel` and
`brainstorm` in all but name — this spec must NOT re-port them; it must reuse the
existing `develop` skills and add only the **net-new** analytical verbs and the
persona/mode substrate that the existing two lean on implicitly.

## Done When

- [ ] A new self-registering `analyze` capability exists at
      `agency/capabilities/analyze.py`. The engine `discover()`s it and auto-wires
      one MCP tool per verb (no central registration). `python -c "from
      agency.engine import Engine; e=Engine(); assert 'analyze' in
      e.registry.names()"` passes.
- [ ] `analyze` carries an `OntologyExtension` registering an `Analysis` node type
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
- [ ] `analyze.analyze(target, dimension)` (**transform**) returns a structured,
      **severity-ranked** finding set over the named dimension (severity ordering is
      a hard rule from `commands/sc-analyze.md:31` "Severity-based prioritization",
      re-expressed as a lint-style transform on the finding set, not prose).
      `analyze.troubleshoot(symptom)` (**transform**) returns ranked root-cause
      hypotheses + next probes — **diagnosis only**. (Source `/sc:troubleshoot` has
      a `--fix` step that *mutates* — `commands/sc-troubleshoot.md:33` "Resolve:
      Apply appropriate fixes"; Agency splits it: diagnosis = `analyze.troubleshoot`
      transform, the fix loop = the existing gated `develop` `debug` discipline.)
      `analyze.estimate(scope)` (**transform**) returns an effort/complexity band.
      `analyze.explain(subject, level)` (**transform**) returns a layered
      explanation. Each records an Invocation that SERVES the intent.
- [ ] `analyze.lens(persona)` (**transform**) returns a named expert lens
      (the persona's review questions + priorities + anti-patterns) as DATA — the
      mechanism by which `spec-panel`/`analyze`/`business-panel` iterate experts.
      The persona catalogue lives as a table in `analyze.py`, NOT as separate agent
      files. SuperClaude ships **20** agent files (`agents/sc-*.md`, excluding
      `sc-README`); **18 are pure analysis lenses** and become `lens()` rows, **2
      orchestrate and are dropped-not-lens** (`pm-agent`, `deep-research-agent`; see
      below and the catalogue table under Design). `lens()` resolves command-declared
      persona aliases (`commands/sc-estimate.md:7` `personas: [architect,
      performance, project-manager]`; `commands/sc-explain.md:7` `personas:
      [educator, architect, security]`) — e.g. `educator`→`learning-guide`,
      `project-manager`→`pm-agent`-as-lens. `analyze.lens("requirements-analyst")`
      returns the requirements lens.
- [ ] `analyze.mode(name)` (**transform**) returns a behavioral mode descriptor
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
- [ ] `tests/test_analyze_capability.py` and `tests/test_analyze_skills.py` are
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

The port lands as **one new `transform`-home capability (`analyze`) + a small set
of skills + an optional `develop` skill**. Rationale: the `/sc:` analysis surface
is stateless compute over a target (read → findings), which is exactly the
`transform` role. Personas are **not agents** in Agency — an Agency agent is a
Lifecycle parameterization (`delegate`), and analysis personas do no external
work; they are *lenses* (data the verb iterates). Modes are **not a runtime** —
they are descriptors a caller adopts.

### Verbs to add (capability `analyze`, home `transform`)

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
are pure **design/analysis lenses**, returned as data by `analyze.lens()`. The
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
per-mode call. `analyze.mode()` is a closed enum of **≤3** genuine descriptors:

| MODE file | what it is | Agency disposition |
|---|---|---|
| `MODE_Brainstorming` | Socratic requirements discovery | **covered** — backs `develop` `brainstorm`; descriptor `analyze.mode("brainstorming")` |
| `MODE_Business_Panel` | 9-expert panel runtime (Expert Engine + 3-phase pipeline) | **covered** — backs `skills/business-panel/`; descriptor `analyze.mode("business-panel")` |
| `MODE_Introspection` | meta-cognitive self-analysis (`--introspect`) | **cover-by-`reflect`** — descriptor `analyze.mode("introspection")` points at the `reflect` capability |
| `MODE_Task_Management` | hierarchical Plan→Phase→Task→Todo + write_memory | **cover-by-Lifecycle+Memory** — this IS Agency's `Lifecycle`/`Memory` substrate; NOT a descriptor |
| `MODE_Orchestration` | Serena/Morphllm/Magic tool-routing matrix | **dropped** — same two-MCP plumbing as `select-tool`; no Agency analogue |
| `MODE_Token_Efficiency` | symbol-compression communication styling | **dropped** — pure system-prompt styling (superpowers-port: "pressure does NOT port") |
| `MODE_DeepResearch` | research mindset backing `/sc:research` | **dropped** — backs the dropped `/sc:research`/deep-research-agent |

### Coverage table (counterpart → Agency target → status)

| SuperClaude item | Agency target | status |
|---|---|---|
| `/sc:brainstorm` + `MODE_Brainstorming` | `develop` skill `brainstorm` (exists) + `analyze.mode("brainstorming")` | **covered** |
| `/sc:spec-panel` | `develop` skill `spec-panel` + `skills/spec-panel/` (exists) | **covered** |
| `/sc:analyze` | `analyze.analyze` + `skills/analyze/` | **new** |
| `/sc:troubleshoot` | `analyze.troubleshoot` (diagnosis) + existing `develop` `debug` (the `--fix` loop) | **new (split)** |
| `/sc:design` | new `develop` skill `design` (distinct from `plan`; `sc-design.md:24-28`) | **new** |
| `/sc:estimate` | `analyze.estimate` | **new** |
| `/sc:explain` | `analyze.explain` | **new** |
| `/sc:business-panel` + `MODE_Business_Panel` | `skills/business-panel/` + `analyze.lens(business-expert)` | **new** |
| `/sc:reflect` | memory aspect → `reflect` capability; "are we done"/task-adherence aspect (`sc-reflect.md:24-26`) → `gate.check` + `develop` `verify` | **covered (split)** |
| `/sc:select-tool` + `MODE_Orchestration` | DROP — Serena-vs-Morphllm MCP routing (`sc-select-tool.md:6,34`); no Agency analogue (one FastMCP engine) | **dropped** |
| `/sc:{implement,build,test,document,improve,cleanup,git,task,spawn,pm,workflow,index,save,load,research,recommend}` | out of scope (build/session/MCP-install surface, not analysis) | **dropped** |
| 18 in-scope `agents/*.md` personas | `analyze.lens(persona)` — lenses as data | **new** |
| `agents/sc-pm-agent` (meta), `agents/sc-deep-research-agent` (analysis) | orchestrate/effect → not lenses; their commands `/sc:pm`,`/sc:research` already dropped | **dropped** |
| `MODE_{Brainstorming,Business_Panel,Introspection}` | `analyze.mode(name)` descriptors (≤3) — see mode table | **new/covered** |
| `MODE_Task_Management` | Agency `Lifecycle` + `Memory` substrate | **covered** |
| `MODE_{Token_Efficiency,DeepResearch}` | pure styling / dropped-command backing | **dropped** |
| `core/{RULES,FLAGS,PRINCIPLES}.md` | hard rules → `gate`/lint checks; stylistic → dropped | **partial** |
| MCP install machinery (`setup-mcp`, `verify-mcp`, `install.sh`, `cli/`) | out of scope (Agency is one FastMCP engine; no installer port) | **dropped** |

## Files

- **Create**:
  - `agency/capabilities/analyze.py` — the new capability (verbs + `OntologyExtension` + persona/mode tables).
  - `skills/analyze/SKILL.md` — walkable `analyze` discipline.
  - `skills/business-panel/SKILL.md` — multi-expert business critique.
  - `skills/brainstorm-discovery/SKILL.md` — Socratic discovery (conditional; see Open Questions).
  - `docs/vision/specs/superclaude-analysts-port.md` — the full coverage mapping.
  - `tests/test_analyze_capability.py`, `tests/test_analyze_skills.py`.
- **Modify**:
  - `agency/capabilities/develop.py` — add a `design` discipline to `DEV_SKILLS`
    (`/sc:design` is distinct from `plan`; Q2 resolved).
- **Move / Delete**: none.

## Open Questions / Needs Research

Q1–Q4 are **RESOLVED against source** by the spec-panel review (see `REVIEW.md`)
and are now baked into the Design above. Only Q5 remains genuinely open (and is
narrowed).

1. **Personas → lenses, not agents.** **RESOLVED → lenses, for every in-scope
   persona.** Two personas DO orchestrate/dispatch — `pm-agent` is a meta-layer
   that delegates (`agents/sc-pm-agent.md:528,520`) and `deep-research-agent`
   orchestrates external Tavily/Playwright/Context7 calls
   (`agents/sc-deep-research-agent.md:95`) — but **both are already out of scope**
   (their commands `/sc:pm`, `/sc:research` are in the dropped bucket). So no
   in-scope persona orchestrates; every one that ports is a pure `analyze.lens()`
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
