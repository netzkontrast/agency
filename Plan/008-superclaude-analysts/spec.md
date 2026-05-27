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
   `reflect`, `select-tool`. These are *transform-shaped* analytical disciplines —
   they read a target and emit findings/recommendations, mutating nothing external.
2. **A persona + mode model**: ~20 analyst agents (`requirements-analyst`,
   `quality-engineer`, `root-cause-analyst`, `system-architect`,
   `security-engineer`, `performance-engineer`, `refactoring-expert`, …) and 7
   behavioral MODE files (`Brainstorming`, `Introspection`, `Orchestration`,
   `Task_Management`, `Token_Efficiency`, `DeepResearch`, `Business_Panel`).

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
      (fields: `target`, `dimension`, `findings`) and a closed `dimension` enum
      `{quality, security, performance, architecture, maintainability}` (mirrors
      `/sc:analyze`'s axes). Merge is strict (no core-label redefinition); tests
      assert the merged ontology accepts an `Analysis` node and rejects a bad
      `dimension`.
- [ ] `analyze.analyze(target, dimension)` (**transform**) returns a structured
      finding set over the named dimension. `analyze.troubleshoot(symptom)`
      (**transform**) returns ranked root-cause hypotheses + next probes.
      `analyze.estimate(scope)` (**transform**) returns an effort/complexity band.
      `analyze.explain(subject, level)` (**transform**) returns a layered
      explanation. Each records an Invocation that SERVES the intent.
- [ ] `analyze.lens(persona)` (**transform**) returns a named expert lens
      (the persona's review questions + priorities + anti-patterns) as DATA — the
      mechanism by which `spec-panel`/`analyze`/`business-panel` iterate experts.
      The persona catalogue (≈20 SuperClaude agents) lives as a table in
      `analyze.py`, NOT as ~20 separate agent files. `analyze.lens("requirements-
      analyst")` returns the requirements lens.
- [ ] `analyze.mode(name)` (**transform**) returns a behavioral mode descriptor
      (the 7 SuperClaude MODE files distilled to: trigger, posture, output-shape)
      so a caller can adopt a mode without a system-prompt edit. `mode` is a closed
      enum of the 7 modes.
- [ ] Three installable skills exist under `skills/`: `analyze` (walkable
      `analyze`-discipline phase-graph), `business-panel` (multi-expert business
      critique, a sibling of the existing `spec-panel`), and `brainstorm-discovery`
      (the Socratic requirements-discovery flavour — only if it is materially
      distinct from the existing `brainstorm` skill; see Open Questions). Each
      SKILL.md passes `plugin.lint_skill` (Use-when, third person, ≤500 chars).
- [ ] The `develop` skill set gains a `design` discipline (architecture/API design
      phase-graph) ONLY IF it is not adequately covered by `plan` (see Open
      Questions) — otherwise it is documented as covered-by-`plan` in the coverage
      table and NOT added.
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
troubleshoot,brainstorm,spec-panel,business-panel,explain,estimate,reflect,
select-tool}.md`. For personas: `src/superclaude/agents/*.md`. For modes:
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
| `analyze` | transform | findings over a `dimension` (quality/security/perf/arch/maintainability) |
| `troubleshoot` | transform | ranked root-cause hypotheses + next probes for a symptom |
| `estimate` | transform | effort/complexity band for a scope |
| `explain` | transform | layered explanation of a subject at a level |
| `lens` | transform | a named persona's expert lens (questions/priorities/anti-patterns) as data |
| `mode` | transform | a named behavioral mode descriptor (trigger/posture/output-shape) |
| `select_tool` | transform | recommend the right capability.verb for a task (complexity-scored) — overlaps engine `search`; see Open Questions |

(`reflect` from `/sc:reflect` is already covered by the `reflect` capability —
listed covered, not re-ported.)

### Skills to add (installable Lifecycle templates under `skills/`)

| skill | kind | phase-graph (→ hard gate) |
|---|---|---|
| `analyze` | discipline | `scope` (target, dimension) → `examine` (findings) → `report` (recommendations) [gate] |
| `business-panel` | discipline | `select-experts` → `critique` (per-lens findings) → `synthesize` [gate] |
| `brainstorm-discovery` | discipline | (only if distinct from existing `brainstorm`) Socratic `probe` → `converge` → `confirm` [gate] |

### Coverage table (counterpart → Agency target → status)

| SuperClaude item | Agency target | status |
|---|---|---|
| `/sc:brainstorm` + `MODE_Brainstorming` | `develop` skill `brainstorm` (exists) + `analyze.mode("brainstorming")` | **covered** |
| `/sc:spec-panel` | `develop` skill `spec-panel` + `skills/spec-panel/` (exists) | **covered** |
| `/sc:analyze` | `analyze.analyze` + `skills/analyze/` | **new** |
| `/sc:troubleshoot` | `analyze.troubleshoot` (+ existing `develop` `debug` for the fix loop) | **new** |
| `/sc:design` | `develop` skill `plan` (cover) OR new `develop` skill `design` | **needs-research** |
| `/sc:estimate` | `analyze.estimate` | **new** |
| `/sc:explain` | `analyze.explain` | **new** |
| `/sc:business-panel` + `MODE_Business_Panel` | `skills/business-panel/` + `analyze.lens(business-expert)` | **new** |
| `/sc:reflect` | `reflect` capability (exists) | **covered** |
| `/sc:select-tool` | engine `search` (cover) OR `analyze.select_tool` | **needs-research** |
| `/sc:{implement,build,test,document,improve,cleanup,git,task,spawn,pm,workflow,index,save,load,research,recommend}` | out of scope (build/session/MCP-install surface, not analysis) | **dropped** |
| ~20 `agents/*.md` personas | `analyze.lens(persona)` — lenses as data | **new** |
| 7 `MODE_*.md` | `analyze.mode(name)` — descriptors as data | **new** |
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
  - `agency/capabilities/develop.py` — add a `design` discipline to `DEV_SKILLS` ONLY if Open-Question Q2 resolves "distinct from plan".
- **Move / Delete**: none.

## Open Questions / Needs Research

1. **Personas → lenses, not agents.** This spec asserts SuperClaude personas
   become `analyze.lens()` DATA, not Agency agents, because they do no external
   work. Confirm against the agent files: do any personas (e.g. `deep-research-
   agent`, `pm-agent`) actually orchestrate/dispatch? If so, those specific ones
   route to `delegate` drivers instead and leave this spec for the analysis-only
   ones. **Decide before coding.**
2. **`design` vs `plan`.** Is SuperClaude `/sc:design` (architecture/API/interface
   design) materially distinct from Agency's existing `develop` `plan` discipline,
   warranting a new `design` skill, or is it the same phase-graph with a different
   framing? If the latter, do NOT add a skill; document covered-by-`plan`.
3. **Modes: enum vs skills vs nothing.** Should the 7 MODE files become (a) a
   closed `mode` enum returned by `analyze.mode()` as descriptors, (b) installable
   skills, or (c) dropped as pure system-prompt styling? Draft assumes (a) for all
   7, but `MODE_Brainstorming`/`MODE_Business_Panel` clearly back skills, and
   `MODE_Token_Efficiency` may be pure styling (drop). Classify each of the 7.
4. **`select-tool` vs the engine `search`.** SuperClaude's `/sc:select-tool` scores
   tools by complexity. Agency's contract is already `search`/`get_schema`/`execute`
   for discovery. Is `analyze.select_tool` net-new value (a complexity-aware
   recommender layered on `search`) or a duplicate of `search`? If duplicate, drop.
5. **RULES/FLAGS/PRINCIPLES as structure.** Which of SuperClaude's behavioral
   rules are *hard constraints* that should become `gate.check`/lint call-sites,
   versus stylistic guidance that Agency deliberately drops (per superpowers-port
   "system-prompt pressure does NOT port")? Enumerate the hard ones explicitly in
   the port doc.

## Evidence

- `~/work/vendor/superclaude-framework/src/superclaude/commands/*.md` — the `/sc:`
  analysis surface (analyze, design, troubleshoot, brainstorm, spec-panel,
  business-panel, explain, estimate, reflect, select-tool).
- `~/work/vendor/superclaude-framework/src/superclaude/agents/*.md` — ~20 personas
  (requirements-analyst, quality-engineer, root-cause-analyst, system-architect,
  security-engineer, performance-engineer, refactoring-expert, backend/frontend-
  architect, devops-architect, technical-writer, python-expert, learning-guide,
  socratic-mentor, self-review, deep-research-agent, pm-agent, business-panel-experts).
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
