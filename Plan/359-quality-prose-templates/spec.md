---
spec_id: "359"
slug: quality-prose-templates
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [4, 2, 6]
depends_on: ["353", "354", "355", "357", "060", "292"]
domain: analyze
wave: brooks-port
parent_spec: "353"
---

# Spec 359 — Brooks prose → agency templates + references (the develop-lint output surface)

> Part of the Spec 353 brooks-lint port. This slice carries the **prose** —
> brooks-lint's twelve markdown files (`_shared/common.md` Report Template + Iron
> Law, the six `{mode}-guide.md` walk guides, `remedy-guide.md`,
> `source-coverage.md`, `decay-risks.md` / `test-decay-risks.md`,
> `custom-risks-guide.md`) — onto agency's **template doctrine** (Spec 060:
> `<!-- AGENT: -->` instruction blocks rendered via `ctx.render`) and the
> **on-demand reference** surface (`develop.reference`, the T3 disclosure
> pattern). Owner directive (2026-06-20): *"port the prose from the Brooks linter
> into templates — for the new develop lint verb."*

## Why

brooks-lint is **mostly prose**. Its engine is a few `.mjs` plumbing files; its
*value* is the twelve markdown documents that tell the model HOW to diagnose
decay and HOW to shape the report. Specs 354–358 port the structured half
(findings, score, SARIF, config, evals); without the prose they are a skeleton
with no diagnostic voice. "Use everything from the Brooks-Lint system" (Spec 353)
is not satisfied until the prose lands too.

Agency already has the right home: **per-capability `templates/`** (Spec 060) —
markdown files with `<!-- AGENT: <imperative> -->` blocks, rendered by
`ctx.render(name, **vars)` / read verbatim via `ctx.template(name)`, lint-gated to
*require* an agent-instruction block (codegraph: `plugin/clusters/lint.py:446`
`RenderSliceRule`). The precedent is live: `analyze/templates/improvement-plan.md`
already carries `<!-- AGENT: -->` blocks and `<!-- BEGIN IF … -->` conditionals.
The brooks Report Template is the same shape — it IS a render template. So this
slice is **porting markdown into an existing, lint-enforced surface**, not new
machinery.

The split is principled, and it is the crux of this spec:

| Prose's job | agency home | mechanism |
|---|---|---|
| shapes **output** (the report a human reads) | a render **template** (`<cap>/templates/`) | `ctx.render` → `document.render` (357) |
| shapes **judgment during the walk** (how to diagnose, what NOT to flag) | an on-demand **reference** | `develop.reference("<topic>")` |
| is **fact/registry** (risk defs, book matrix, score weights) | **data** (`<cap>/data/*.json`) | 354 / 356 / 358 |

## Design

### 1. The Report Template — the flagship (`analyze/templates/quality-report.md`)

`_shared/common.md`'s Report Template ports verbatim-in-spirit to a Spec 060
template, rendered graph→file by `document.render` (357 §4). It carries the
brooks structure as `<!-- AGENT: -->` blocks so the rules travel WITH the
template (not in a separate guide that drifts):

```markdown
<!-- agency-node: $report_node_id -->
# Quality Review — $mode

**Scope:** $scope
**Health Score:** $score/100$trend_suffix
<!-- AGENT: render the Config: line here ONLY when a config was applied
     (preset, N disabled, M ignored) — Spec 356 §2. Omit otherwise. -->

$verdict

<!-- AGENT: Module Dependency Graph (mermaid) — audit mode ONLY (R5). Omit for
     all other modes. classDef colors per the quality-audit template. -->
$module_graph

## Findings
<!-- AGENT: sort by tier critical→warning→suggestion; OMIT an empty tier's
     heading. Each finding renders the iron-law-finding template. -->
$findings_block

<!-- AGENT: collapsed "Suppressed" section when suppressions matched (356 §4);
     not counted in the score. -->
$suppressed_block

## Summary
<!-- AGENT: 2–3 sentences. Under legacy-friendly, LEAD with the three
     highest-leverage fixes (356 §1). -->
$summary

<!-- AGENT: Language rule — render finding prose + verdict in the user's
     language; keep Iron Law labels (Symptom/Source/Consequence/Remedy), book
     titles, smell names, and structural headers in English. -->
```

The template is the **Document convergence artefact** (Spec 292, CLAUDE.md #2):
it is a graph node (`<!-- agency-node: -->` anchor), it binds a `template` + a
schema, and it round-trips via `document.sync` — so an edited report is not lost.
This is why the report template lands in `analyze/` (where the `Finding`/score
engine is), rendered through `document.render`, not as a print-statement.

### 2. The Iron Law block (`analyze/templates/iron-law-finding.md`)

One finding's render, reused by §1's `$findings_block`:

```markdown
**$risk_name — $title**
Symptom: $symptom
Source: $source
Consequence: $consequence
Remedy: $remedy$fix_tier_label
<!-- AGENT: $fix_tier_label is the [quick-fix]/[guided]/[manual] tag ONLY under
     --fix (the remedy template §4); empty otherwise. A finding missing
     Consequence or Remedy is REJECTED upstream (the Iron Law gate, 355 §2) —
     this template never renders a partial finding. -->
```

This makes the Iron Law a **rendered invariant**: the template has four required
slots; the judgment gate (355) guarantees they are filled before render.

### 3. The six mode guides → walk templates (`develop/templates/quality-{mode}.md`)

Each brooks `{mode}-guide.md` becomes a `develop/templates/quality-{mode}.md`
template whose body is the numbered walk, each step an `<!-- AGENT: -->` block.
The mode skill (355 §2) renders its template at the matching phase, so the engine
still delivers ONE phase at a time (bounded context) but the *guidance prose*
lives in a template, not inlined in Python. Example (`quality-review.md`, porting
`pr-review-guide.md`):

```markdown
<!-- AGENT: Scope calibration — <50 LOC: steps 1–3 + 6a/6b conditionally;
     50–300: all steps; >300: sampled, note it; >500: flag PR size as a
     Change-Propagation signal in the Summary. -->
<!-- AGENT: Step 2 (Change Propagation) — scan FIRST; most visible in a diff. … -->
<!-- AGENT: Step 7 (Quick Test Check) — three signals only (Coverage Illusion,
     Mock Abuse, Test Obscurity); not a full Mode-4 audit. … -->
```

The brooks "skip unless condition applies" disclosure (common.md:16-19) maps to
the `<!-- BEGIN IF … -->` conditional the agency template loader already supports
(seen in `improvement-plan.md`). One template per mode = six files; the prose is
**derived into the walk**, not duplicated in the skill docstring (rule 2).

### 4. Remedy + scope prose → templates

- `develop/templates/quality-remedy.md` ← `remedy-guide.md`: the
  Target/Action/Rationale enrichment rules + the quick-fix/guided/manual
  fixability tiers + the Fix Summary table, as `<!-- AGENT: -->` blocks. Rendered
  in the remedy phase (355 §4, `--fix`). Carries brooks' "What NOT to do"
  (no file writes in the diagnosis phase) as an explicit block.
- The Auto-Scope rules (common.md:94-106) ride in each mode template's scope
  step (§3), not a separate file — they are mode-specific.

### 5. Judgment prose → on-demand references (`develop.reference`)

Prose that shapes *diagnosis* (not output) is **fetched, not rendered** — the T3
disclosure pattern (`develop.reference("codegraph")` precedent). New `REFERENCES`
entries in `develop/_main.py`, each backed by a vendored markdown file under
`develop/references/` (cited to brooks upstream):

| `develop.reference(...)` | brooks source | read when |
|---|---|---|
| `"decay-risks"` | `decay-risks.md` + `test-decay-risks.md` | before the judgment pass (355 §2 phase 3) |
| `"source-coverage"` | `source-coverage.md` | before writing findings (the cite-discipline, 358) |
| `"remedy"` | `remedy-guide.md` (the heavy how-to) | before `--fix` (paired with §4's template) |
| `"custom-risks"` | `custom-risks-guide.md` | when config declares `custom_risks` (356 §2) |

> **Tension resolved — template vs reference vs data (no triple-storage).** A
> brooks file lands in EXACTLY ONE home by its job: the Report Template + mode
> guides + remedy enrichment **render output** → templates; the decay-risk
> diagnostic prose + source-coverage cite-discipline **guide judgment** →
> references; the risk *definitions* + book *titles* + score *weights* are
> **facts** → JSON data (354/356/358). The reference prose POINTS AT the data
> (e.g. `decay-risks` reference explains how to read `decay-risks.json`); it never
> restates the risk list. One fact, one home (rule 2).

### 6. Drift coverage (Spec 054 / 060)

- Every new template carries an `<!-- AGENT: -->` block → passes the existing
  `RenderSliceRule` lint (no new lint needed; the gate already exists).
- A `<!-- doc-source: brooks-lint@<rev> _shared/<file> -->` marker on each ported
  template + reference, so `scripts/check-doc-drift` flags it if the upstream
  brooks prose changes (the vendoring-provenance discipline, like the Dramatica
  ontology in Spec 101).
- `# AGENCY-DRIFT: quality-templates` at the site that enumerates the mode
  templates (so adding a 7th mode template is caught if the skill set and the
  template set diverge).

### What this slice does NOT do

- **No finding/score/SARIF logic** (354/356/357) — it renders THEIR output and
  guides THEIR judgment; it ports prose, not engine.
- **No risk definitions in prose** — those are data (354); references point at the
  data, never restate it.
- **No second copy of a brooks file** — each lands in one home (§5 tension).
- **No hand-authored skill metadata** — the SkillDoc still derives from the
  docstring (Spec 080); templates are render assets, not skill metadata.
- **No prose-parsing** (`report-parse.mjs` stays dropped, 357) — templates render
  FROM structured findings; nothing parses prose back.

## Acceptance (Gherkin)

```gherkin
Scenario: the report renders from the ported template, not a print
  When a quality review report is rendered
  Then it uses analyze/templates/quality-report.md via document.render
  And the report is a Document graph node (round-trippable via document.sync)
  And finding blocks render the iron-law-finding template (Symptom/Source/Consequence/Remedy)

Scenario: audit-only sections are gated in the template
  When the report renders for mode "review"
  Then no Module Dependency Graph section appears
  When the report renders for mode "audit"
  Then a mermaid Module Dependency Graph section appears

Scenario: each mode guide is a template carrying agent instructions
  Then develop/templates/quality-{review,audit,debt,test,health,sweep}.md all exist
  And each carries at least one <!-- AGENT: --> block (passes RenderSliceRule lint)

Scenario: judgment prose is fetched on demand, not rendered
  When I call develop.reference("decay-risks")
  Then the brooks decay-risk diagnostic prose is returned
  And it points at decay-risks.json (it does not restate the risk list)

Scenario: every ported template is drift-tracked to its upstream
  Then each quality template + reference carries a <!-- doc-source: brooks-lint … --> marker
  And check-doc-drift flags it stale if the upstream brooks prose changes

Scenario: the language rule is carried by the template
  Given a user working in German
  When the report renders
  Then finding prose + verdict are in German
  And the Iron Law labels, book titles, and structural headers stay English
```

## Open questions

- **OQ1 — mode-guide home: `develop/templates/` vs `analyze/templates/`?**
  (Default: `develop/` — the walk guides bind to the `develop` mode skills;
  `analyze/` keeps only the *output* templates (report + iron-law-finding) next to
  the finding engine.)
- **OQ2 — references as files under `develop/references/` vs entries inlined in
  the `REFERENCES` dict?** (Default: files — the brooks prose is long; inlining it
  in Python bloats the module and dodges `check-doc-drift`. Files get a
  `doc-source` marker; the dict maps topic→file.)
- **OQ3 — render the report via `analyze`'s `render_templates` or `document`'s?**
  (Default: `analyze` owns `quality-report.md` + `iron-law-finding.md` as its
  `render_templates`; `document.render` is the *mechanism* that projects them —
  the template lives with the finding engine, the renderer stays generic.)

## Followup — Implementation Status (2026-06-20)

**DRAFTED 2026-06-20** — the prose/output slice of the Spec 353 program, opened by
the owner's "port the prose into templates" directive. No code yet.
codegraph-grounded: the template surface is live (`analyze/templates/`,
`develop/templates/`, `RenderSliceRule` lint at `plugin/clusters/lint.py:446`,
`ctx.render`/`ctx.template` at `capability.py:264/400`), so this is markdown into
an enforced surface, not new machinery. Splits the 12 brooks markdown files into
templates (render output), references (guide judgment), and data (354/356/358).
Depends on 354 (Iron Law fields the template renders), 355 (mode skills that bind
the walk templates), 357 (`document.render` path). Lands alongside 357/358. Next
(after 354/355): author `quality-report.md` + `iron-law-finding.md` +
`quality-{mode}.md` ×6 + `quality-remedy.md` + the four `develop.reference`
entries, each with a `doc-source` marker, RED→GREEN against the §Acceptance
scenarios.
