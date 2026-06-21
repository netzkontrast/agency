<!-- doc-source: docs/vision/SKILL-CONTRACT.md agency/skill_emit.py agency/capabilities/plugin/clusters/lint.py -->
# Assembled skill best-practices (the foundation for Spec 370)

> Synthesis of the three authorities for skill authoring, distilled into numbered
> rules and mapped to what they demand of the v2 **schema** and the **skill-creator
> prompts**. Spec 370 (skill-system-v2) and its children cite these rule IDs.
>
> Sources: superpowers `writing-skills` (TDD-for-skills) · Anthropic
> `anthropic-best-practices.md` (official) · agency `skill-creation`
> (red→green→lint→refactor→deploy) · the existing `docs/vision/SKILL-CONTRACT.md`.

## Part 1 — Universal rules

### Discovery / metadata
- **R1 — description = when, not what.** Third person, "Use when…", ≤1024 chars,
  packed with search keywords (errors, symptoms, synonyms, tools). NEVER summarize
  the workflow — a workflow summary becomes a shortcut the agent takes *instead of*
  reading the skill (empirically verified in `writing-skills`).
- **R2 — name.** ≤64 chars, kebab on the wire, gerund/active-voice preferred.

### Structure / progressive disclosure
- **R3 — body ≤500 lines.** Overflow → reference files.
- **R4 — references one level deep** from SKILL.md (agents partial-read nested refs).
- **R5 — reference files >100 lines start with a table of contents.**
- **R6 — organize references by domain/feature,** descriptively named; zero context
  cost until read.

### Content / degrees of freedom
- **R7 — concise.** Only what the agent doesn't already know; every paragraph
  justifies its tokens.
- **R8 — match freedom to fragility.** high (text heuristics) / medium
  (parameterized template) / low (exact "run this, don't modify" script). A skill
  (or phase) DECLARES its level.
- **R9 — one excellent example** — concrete, runnable, real; not multi-language,
  not a fill-in-the-blank template.
- **R10 — hygiene.** Consistent terminology; no time-sensitive info (use an
  "old patterns" `<details>`); forward-slash paths; fully-qualified MCP tool names
  (`Server:tool`); don't assume packages installed.

### Workflows / feedback
- **R11 — workflows = numbered steps + a copyable checklist;** small inline
  flowchart only at non-obvious decision points.
- **R12 — feedback loops** for quality-critical work (validate → fix → repeat) +
  verifiable intermediate outputs (plan → validate → execute).

### Testing (the Iron Law)
- **R13 — no skill without a failing test first** (RED baseline → GREEN minimal →
  REFACTOR loopholes). **Match the form to the failure:** discipline-failure →
  prohibition + rationalization table + red-flags; wrong-shaped output → positive
  recipe/contract; omitted element → structural required slot; conditional
  behavior → predicate-keyed conditional. Prohibitions BACKFIRE on shaping problems.
- **R14 — eval-driven:** ≥3 scenarios, baseline-first, test across Haiku/Sonnet/Opus.

### Type
- **R15 — every skill is one type,** each with a different required shape AND a
  different test method: **Technique** (steps) · **Pattern** (mental model) ·
  **Reference** (API/docs) · **Discipline** (enforced rule).

## Part 2 — agency-specific rules

- **A1 — self-contained.** Every instruction inline so a non-skill-walk agent
  (Cursor/Copilot/read-only) can follow top-to-bottom; skill-walk is an
  *enhancement*, never a requirement. (Reconciled with R3/R4: the skill's own
  workflow/phases are inline; heavy per-verb API detail lives in one-deep references.)
- **A2 — phase = single source.** The phase graph carries the instructions and
  powers BOTH the walk and the rendered file — no divergence, no truncation.
- **A3 — provenance trace.** Every `act`/`effect` verb's reference names the nodes
  recorded + edges linked + the return delta; a `transform` notes "pure".
- **A4 — derive then author.** Mechanical content derived (no drift); judgment
  content authored once, schema-required.
- **A5 — grounded generation.** A skill is generated from the capability's CODE +
  its governing SPEC(s) + the ontology — never the docstring alone.
- **A6 — capability-authored skills.** A capability may register its own custom
  skills (beyond the auto one), validated by the same schema.
- **A7 — reproducible install (agency invariant).** `install regen` produces no
  diff. Therefore: LLM sampling is an AUTHORING-TIME generator whose reviewed
  output is COMMITTED; install renders the committed schema deterministically (no
  LLM). A staleness gate flags when source drifted from the committed skill — it
  never auto-rewrites.

## Part 3 — implications for the schema
The v2 `Skill`/`Phase` schema must express (a powerful, layered document — small
required core per type + optional rich extensions, YAGNI on the rest):
type (R15) · per-phase degrees-of-freedom (R8) · progressive-disclosure tree with
one-deep refs + ToC flags (R4/R5) · phases with `goal`/`instructions`/`example`/
`done_when` (A2) · workflow checklists + feedback loops (R11/R12) · input/output
example pairs (R9) · per-verb provenance trace (A3) · per-field `source`
(derived|authored|sampled, A4/A5) · `owner` (auto|capability, A6) · eval scenarios
(R14) · a source-hash stamp for the staleness gate (A7).

## Part 4 — implications for the skill-creator (MCP sampling)
"Optimized content, not docstring extracts" = the authoring-time generator SAMPLES
the host LLM (agency's `host.sample`/Driver seam, surfaced as MCP sampling) with a
**per-type skill-creator prompt**, grounded in: the capability's verbs + signatures
+ docstrings, its governing spec(s), the ontology — and **these rules (R1–A7) as
the system prompt**. The output fills the schema, is validated against the live
registry (every referenced verb must exist) + the type schema (R13 form-matching +
R1/R3/R4 checks), is reviewed, then committed (A7). The skill-creator prompts are
where R1–R15 become operational — Anthropic's "Agent A", run programmatically.
