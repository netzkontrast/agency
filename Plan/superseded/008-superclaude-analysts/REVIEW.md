---
review_of: Plan/superseded/008-superclaude-analysts/spec.md
reviewer: spec-panel (sc:sc-spec-panel, critique mode)
source_of_truth: /root/.claude/plugins/marketplaces/superclaude/ (the deployed SuperClaude Plugin — the spec's named "deployed shape"; the ~/work/vendor/ Framework+Plugin clones do NOT exist in this environment, so all citations are into the deployed marketplace tree, which mirrors `src/superclaude/{commands,agents,modes,core}`)
date: 2026-05-27
---

# REVIEW — Spec 008 (SuperClaude Analysts + Command/Mode Framework)

## Verdict

**APPROVE WITH MUST-FIX.** The core thesis is sound and source-confirmed: the
`/sc:` analysis surface IS transform-shaped, and the analysis personas + the
business-panel experts ARE pure lenses (review-questions + frameworks as data),
not agent runtimes. The `analyze` capability + skills decomposition fits the
Agency `Capability`/`Skill`/`OntologyExtension` contract cleanly. BUT the spec
ships several source-inaccurate details (a phantom 5th `dimension`, an
over-broad mode enum, a mis-scoped `select_tool`) and leaves two
Open Questions unresolved that the source actually decides. These must be
fixed before coding, because they are baked into "Done When" acceptance
criteria (the `dimension` enum, the 7-mode enum) and tests will encode the
wrong shape.

The spec-panel was run in critique mode; findings are severity-tagged
(CRITICAL / MAJOR / MINOR) per expert lens.

---

## Source-grounded corrections (path:line into the SuperClaude tree)

### C1 — CRITICAL (Wiegers, testability): the `dimension` enum has a phantom 5th value
The spec's "Done When" mandates a **closed `dimension` enum
`{quality, security, performance, architecture, maintainability}`** and says it
"mirrors `/sc:analyze`'s axes" (spec.md:71-73).

The real `/sc:analyze` has **four** focus axes, not five:
`commands/sc-analyze.md:19` — `--focus quality|security|performance|architecture`.
`maintainability` is **not** an `analyze` axis; it is a *refactoring-expert*
concern (`agents/sc-refactoring-expert.md:2` — "reduce technical debt … clean
code"). The spec invents a fifth value and asserts it mirrors the source. It
does not.
**Fix:** make the enum `{quality, security, performance, architecture}` to match
`sc-analyze.md:19`, OR explicitly document `maintainability` as an Agency
*addition* (not a mirror) with rationale. The test "rejects a bad `dimension`"
will otherwise encode a wrong contract.

### C2 — CRITICAL (Fowler, boundaries): `select_tool` is mis-scoped; it is a DROP, not "net-new value"
The spec lists `analyze.select_tool` as a verb "complexity-scored — overlaps
engine `search`; see Open Questions" and leaves Q4 open
(spec.md:148, 174, 211-214).

The source is unambiguous: `/sc:select-tool` exists **solely to choose between
the Serena and Morphllm MCP servers** —
`commands/sc-select-tool.md:6-7` ("optimal MCP tool selection between Serena and
Morphllm"), `:33-36` ("Serena (semantic operations) vs Morphllm (pattern
operations)"). It is a SuperClaude-internal routing decision between two MCP
backends that **do not exist in Agency** (Agency is one FastMCP engine; CLAUDE.md
"ONE FastMCP engine"). It is neither a general recommender nor a duplicate of
`search` — it is install-environment plumbing for a two-MCP topology Agency
doesn't have.
**Fix (resolves Q4):** **DROP `select_tool`.** Remove the verb from the table.
Move `/sc:select-tool` into the **dropped** row of the coverage table alongside
the MCP-install machinery, with the Serena/Morphllm rationale. (`MODE_Orchestration`,
`modes/MODE_Orchestration.md:20-30`, is the same Serena/Morphllm/Magic routing
matrix — also drop-or-cover-by-`search`, see M2.)

### C3 — MAJOR (Cockburn, goal clarity): personas → lenses is CORRECT for the in-scope set, but two personas DO orchestrate — and the spec already drops them
Q1 asks "do any personas (`deep-research-agent`, `pm-agent`) actually
orchestrate/dispatch?" (spec.md:196-201). The answer from source is **YES, both
do — and both are already out of scope**, so the lens-not-agent thesis holds for
every persona the spec actually ports.

- `agents/sc-pm-agent.md:528` — "operates as a **meta-layer** above specialist
  agents"; `:519-520` "**Will Not:** Execute implementation tasks directly
  (delegates to specialist agents)"; `:530-548` a "Task Execution Flow" that
  selects and routes to specialist agents. **pm-agent orchestrates.** Its command
  `/sc:pm` is in the spec's **dropped** bucket (spec.md:175). Correct.
- `agents/sc-deep-research-agent.md:95-113` — a "Tool Orchestration" section that
  dispatches Tavily/Playwright/Context7 searches with "Parallel Optimization …
  Never sequential without reason". This is **effect-shaped external work**
  (web/search side-effects), not a pure lens. Its command `/sc:research` is also
  **dropped** (spec.md:175). Correct.

**Fix (resolves Q1):** State the resolution explicitly in the spec and port doc:
"Two personas (`pm-agent`, `deep-research-agent`) DO orchestrate/dispatch; both
are already out of analysis scope (their commands `/sc:pm`, `/sc:research` are
dropped). Every persona that remains in scope is a pure analysis lens →
`analyze.lens()` data. Confirmed at sc-pm-agent.md:528 and
sc-deep-research-agent.md:95." Remove "Decide before coding" — it is decided.

### C4 — MAJOR (Fowler/Nygard): persona-catalogue count and category tags are imprecise
The spec says "≈20 SuperClaude agents" and lists a persona set (spec.md:84, 41-44,
226-230). Source has **20 agent files** (`agents/sc-*.md`, excluding sc-README):
the spec's list omits `self-review` (`agents/sc-self-review.md:3` — "Post-
implementation validation and reflexion partner", category quality) and
`repo-index` (`agents/sc-repo-index.md:3`, category discovery), and double-counts
`deep-research` vs `deep-research-agent` (two files:
`sc-deep-research.md` category analysis, and `sc-deep-research-agent.md`).
Also note the **architect personas carry `category: engineering`** but explicitly
disclaim doing work: `agents/sc-system-architect.md:46` "**Will Not:** Implement
detailed code", `sc-backend-architect.md:46-47` "**Will Not:** … Manage
infrastructure deployment", `sc-devops-architect.md:46` "**Will Not:** Write
application business logic". So despite the engineering tag they are **design
lenses** — the lens thesis holds; the spec should cite this rather than assert it.
**Fix:** Replace "≈20 agents" with the exact enumerated catalogue, classify each
by `category:` frontmatter (analysis / quality / engineering / communication /
specialized / business / discovery / meta), and mark the two orchestrators
(pm-agent meta, deep-research-agent analysis-but-effecting) as
**dropped-not-lens**. The remaining ~16–17 become `analyze.lens()` rows.

### C5 — MINOR (Nygard, failure modes): `troubleshoot` is diagnose+fix at source; spec's transform-only is a deliberate narrowing — say so
`analyze.troubleshoot` is typed **transform** returning "ranked root-cause
hypotheses + next probes" (spec.md:75-76). The source `/sc:troubleshoot` has a
`--fix` flag and a "5. **Resolve**: Apply appropriate fixes" step
(`commands/sc-troubleshoot.md:20, 33`) — i.e. it *mutates* when asked. The spec
correctly routes the fix-loop to the existing `develop` `debug` discipline
(spec.md:168), which is the right Agency decomposition (diagnosis = transform,
fix = gated lifecycle). This is a sound narrowing, but it is currently implicit.
**Fix:** Add a one-line note: "`/sc:troubleshoot --fix` mutates; Agency splits it
— `analyze.troubleshoot` is diagnosis-only (transform), the fix path is
`develop` `debug` (gated). Cited sc-troubleshoot.md:33."

---

## Missing surface (things SuperClaude does that the spec omits)

### M1 — `/sc:design` is materially distinct from `plan` → ADD the `design` discipline (resolves Q2)
Source `/sc:design` (`commands/sc-design.md`) is architecture/API/component/
database design: flow `Analyze → Plan → Design → Validate → Document`
(`sc-design.md:23-27`), with `--type architecture|api|component|database` and
`--format diagram|spec|code` (`sc-design.md:19`). Agency's `develop` `plan`
discipline is an *implementation* phase-graph: `map (files,steps) →
self-review → approve` (develop.py:34-38). These are different artefacts: `plan`
produces an implementation step-list; `design` produces interface/architecture
specifications. **They are NOT the same phase-graph.**
**Fix (resolves Q2 = "distinct from plan"):** ADD a `design` discipline to
`DEV_SKILLS` in develop.py, e.g. `analyze (requirements,context) → design
(spec/interface) → validate (meets-requirements) [gate]`. Update the coverage
row from **needs-research** to **new (develop skill `design`)**.

### M2 — Mode classification: the "all-7-enum" assumption is wrong; classify each (resolves Q3)
The spec's draft "assumes (a) [enum] for all 7" modes (spec.md:206-210), then
its own Q3 admits this is wrong. Source forces a per-mode classification:

| MODE file (path) | What it is | Agency disposition |
|---|---|---|
| `MODE_Brainstorming.md:1-20` | Socratic requirements discovery | **covered** — backs `develop` `brainstorm`; descriptor via `analyze.mode("brainstorming")` |
| `MODE_Business_Panel.md:1-30` | the 9-expert panel *runtime* (Expert Engine + 3-phase pipeline) | **covered** — backs `skills/business-panel/`; NOT a thin descriptor |
| `MODE_Introspection.md:1-20` | meta-cognitive self-analysis ("analyze my reasoning", `--introspect`) | **cover-by-`reflect`** — maps to the `reflect` capability, not a generic descriptor |
| `MODE_Orchestration.md:20-30` | Serena/Morphllm/Magic tool-routing matrix | **drop / cover-by-`search`** — same plumbing as `select-tool` (C2); no Agency analogue |
| `MODE_Task_Management.md:1-25` | hierarchical Plan→Phase→Task→Todo + write_memory | **cover-by-Lifecycle+Memory** — this IS Agency's `Lifecycle`/`Memory` substrate (CLAUDE.md), not a descriptor |
| `MODE_Token_Efficiency.md:1-30` | symbol-compression communication styling | **drop** — pure system-prompt styling (the superpowers-port "pressure does NOT port" rule) |
| `MODE_DeepResearch.md:1-20` | research mindset backing `/sc:research` | **drop** — backs the dropped `/sc:research`/deep-research-agent |

So `analyze.mode()` is a **closed enum of at most 2–3 genuine descriptors**
(`brainstorming`, `business-panel`, arguably `introspection` as a pointer to
`reflect`), NOT 7. The "Done When" line "`mode` is a closed enum of the 7 modes"
(spec.md:88-89) is **wrong** and must be rewritten. Document the 4 dropped/covered
modes in the port doc.

### M3 — `/sc:reflect` ≠ Agency `reflect` (semantic gap, currently hidden behind "covered")
The coverage table marks `/sc:reflect` **covered** by the `reflect` capability
(spec.md:173). But `/sc:reflect` is **task-adherence/completion validation**
(`commands/sc-reflect.md:24-26` — `think_about_task_adherence`,
`think_about_whether_you_are_done`), whereas Agency's `reflect` is
**cross-session memory notes** (`reflect.py:1` "durable scope-tagged memory",
verbs `note`/`recall`/`search`). The "am I done?" validation is actually closer
to Agency's `gate.check` + the `verify` discipline (develop.py:52-56). The
overlap is partial; "covered" overstates it.
**Fix:** Refine the row: "`/sc:reflect`: cross-session-memory aspect →
`reflect` capability; task-adherence/'are we done' aspect → `gate.check` +
`develop` `verify`. **covered (split).**"

### M4 — MINOR: commands carry persona declarations — cite as lens-thesis evidence
`commands/sc-estimate.md:7` declares `personas: [architect, performance,
project-manager]`; `commands/sc-explain.md:7` declares `personas: [educator,
architect, security]`. This is direct source evidence that a command *iterates a
list of personas* — exactly the `verb iterates lenses` mechanism the spec
proposes (spec.md:81-82, 146). The spec should cite this; it strengthens the
thesis and confirms `lens` must accept the *command-declared* persona aliases
(`educator`→`learning-guide`, `project-manager`→`pm-agent`-as-lens).

---

## Open-Questions triage (resolved against source)

| Q | Resolution (source-grounded) |
|---|---|
| **Q1 persona-orchestration** | **RESOLVED → lenses, for all in-scope personas.** Two personas orchestrate (`pm-agent` meta-layer, sc-pm-agent.md:528; `deep-research-agent` tool-orchestration, sc-deep-research-agent.md:95) — both already dropped via `/sc:pm`,`/sc:research`. No in-scope persona orchestrates. Encode the citation; drop "decide before coding." |
| **Q2 design vs plan** | **RESOLVED → distinct; ADD `design`.** sc-design.md:23-27 (design/validate/document of interfaces) ≠ develop.py:34-38 (`plan` = implementation steps). See M1. |
| **Q3 modes enum/skills/drop** | **RESOLVED → per-mode (M2).** NOT all-7-enum. 2 back skills (Brainstorming→`brainstorm`, Business_Panel→`business-panel`), 1 covers-by-`reflect` (Introspection), 1 covers-by-Lifecycle/Memory (Task_Management), 3 drop (Orchestration→plumbing, Token_Efficiency→styling, DeepResearch→dropped command). `mode` enum ≤3. |
| **Q4 select-tool vs search** | **RESOLVED → DROP (C2).** sc-select-tool.md:6 is Serena-vs-Morphllm MCP routing; no Agency analogue. Not net-new, not a `search` duplicate — environment plumbing. Remove the verb. |
| **Q5 RULES/FLAGS/PRINCIPLES as structure** | **Partially resolvable now.** `core/PRINCIPLES.md`, `core/RULES.md`, `core/FLAGS.md` exist. Most are stylistic and drop per the superpowers-port "system-prompt pressure does NOT port" thesis. The HARD ones that should become `gate.check`/lint: evidence-before-claim ("are we done" validation → `gate.check`, matches develop `verify`), and the analyze severity-prioritization rule (findings MUST be severity-ranked, sc-analyze.md:31 "Severity-based prioritization") → a lint-style transform on the finding set. Enumerate these explicitly in the port doc; do not leave Q5 open-ended. |

---

## Must-fix list (blocking, before coding)

1. **C1 — `dimension` enum: drop `maintainability`** (or document it as an Agency
   addition, not a "mirror"). Source has 4 axes (sc-analyze.md:19). This is baked
   into a "Done When" acceptance test — wrong enum = wrong contract.
2. **C2 / Q4 — DROP `select_tool`.** It is Serena-vs-Morphllm MCP plumbing
   (sc-select-tool.md:6), not analysis; no Agency analogue. Remove the verb row;
   move to the dropped coverage row. Likewise drop/cover `MODE_Orchestration`.
3. **M2 / Q3 — Rewrite the `mode` enum from "the 7 modes" to ≤3 genuine
   descriptors** and classify the other 4 (Introspection→`reflect`,
   Task_Management→Lifecycle/Memory, Token_Efficiency→drop, DeepResearch→drop).
   The "Done When" line (spec.md:88-89) is currently false.
4. **M1 / Q2 — ADD the `design` develop discipline** (distinct from `plan`,
   sc-design.md:23-27). Flip the coverage row from needs-research to new.
5. **C3 / Q1 — Write the persona-orchestration resolution into the spec with
   citations** (pm-agent.md:528, deep-research-agent.md:95) and stop calling it
   undecided.

### Should-fix (non-blocking, improves fidelity)
- **C4** — replace "≈20 agents" with the exact 20-file catalogue, classified by
  `category:`; mark `self-review`+`repo-index` (omitted) and the 2 orchestrators.
- **C5** — note `troubleshoot --fix` mutates at source; Agency splits diagnosis
  (transform) from fix (`develop` `debug`).
- **M3** — refine `/sc:reflect` row to "covered (split)": memory→`reflect`,
  done-validation→`gate`+`verify`.
- **M4** — cite `personas:` frontmatter (sc-estimate.md:7, sc-explain.md:7) as
  lens-iteration evidence; ensure `lens()` resolves command-declared aliases
  (`educator`→`learning-guide`, `project-manager`).
- **Ontology nit** — the spec says the `dimension` enum is "closed", but
  `Ontology.extend` only WIDENS enums (ontology.py:112-113); it never closes.
  For a net-new `Analysis` node this is fine, but say "closed *for the Analysis
  node*, enforced by `violations()` (ontology.py:136-138)" rather than implying
  the merge closes it.

---

## What the spec gets RIGHT (confirmed against source)

- **Analysis surface is transform-shaped.** Every in-scope command's Behavioral
  Flow is read→findings with no external mutation (sc-analyze.md:23-27,
  sc-estimate.md:23-27, sc-explain.md:23-27). Typing them `transform` is correct.
- **Personas are lenses, business experts are data.** `agents/sc-business-panel-
  experts.md` is literally a YAML catalogue of `key_questions` + `focus_areas` +
  `analysis_framework` per expert — the exact "judgment-as-data" shape. Putting
  the catalogue in a table in `analyze.py` (not 20 agent files) is right.
- **Reusing existing `develop` `brainstorm`/`spec-panel` instead of re-porting**
  is correct: MODE_Brainstorming and the spec-panel command map 1:1 to
  develop.py:29-33, 57-61 and skills/spec-panel/SKILL.md.
- **Dropping the build/session/MCP-install surface** (`implement`,`build`,`test`,
  `git`,`task`,`spawn`,`pm`,`workflow`,`index`,`save`,`load`,`research`,
  `recommend`, `setup-mcp`,`verify-mcp`) is the right scope cut — those are in
  `commands/` but are not analysis disciplines.
- **OntologyExtension / self-registration fit** is accurate: the `Analysis` node
  + strict merge matches ontology.py:104-110, and "drop a file, engine discovers
  it" matches CapabilityBase.as_capability (capability.py:118-123).
