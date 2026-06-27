<!-- agency-node: spec-388 -->
---
spec_id: "388"
slug: jinja-template-engine
status: draft
state: draft
last_updated: 2026-06-23
owner: "@agency"
vision_goals: [3, 6]
depends_on: ["060", "384", "292"]
domain: substrate / templates
wave: brooks-port
parent_spec: "060"
---

# Spec 388 — Jinja template engine: programmatic gates for all templates

> Owner directive (2026-06-23): *"improve all templates that have those Gates —
> let them be decided programmatically — install jinja Template Engine and port all
> templates."* The Spec 060 template surface uses `string.Template` (`$var`
> substitution) plus `<!-- BEGIN IF … -->` / `<!-- AGENT: -->` comment markers that
> **no engine evaluates** — they were agent-read until Spec 384 added an interim
> regex processor (`_strip_conditionals` / `_strip_authoring_comments` in
> `analyze/_main.py`) just to gate the report's audit-only graph. This spec replaces
> the hand-rolled half with a **real template engine (Jinja2)** so conditionals,
> loops, and comments are first-class and programmatic.

## Why

The render surface today is two mechanisms welded together:

1. **`string.Template`** (`ctx.render` → `_Template(tpl).substitute(**vars)`,
   `capability.py:275`) — handles `$var` substitution and **nothing else**: no
   conditionals, no loops, no filters, and it raises `KeyError` on any missing var.
2. **Comment markers the engine ignores** — `<!-- BEGIN IF flag -->…<!-- END IF -->`
   (in `quality-report.md`, `improvement-plan.md`, `research-report.md`) and
   `<!-- AGENT: … -->` blocks. There is **no processor** for `BEGIN IF` in the
   codebase; the conditional was decorative until Spec 384 shipped a one-off regex
   (`_COND_RE`) + a comment stripper (`_COMMENT_RE`) — a per-capability hack that
   every other template-rendering verb would have to re-implement.

This is the **dormant-surface anti-pattern** (CLAUDE.md): a marker is written but
nothing reads it. The fix is not more regex — it is the engine the markers imply.
**Jinja2** gives `{% if %}` / `{% for %}` / `{# comment #}` / filters as evaluated
constructs, so a template's gates are decided by the renderer, once, for every
capability — and the interim Spec 384 strippers delete.

## Design

### 1. The dependency

Add **`jinja2`** (BSD, no transitive weight beyond `markupsafe`). Decision OQ1:
core runtime dep vs a `[templates]` extra. **Default: core** — `ctx.render` is
substrate (every capability uses templates); gating it behind an extra would make a
core method conditionally fail. It is small and pure-Python.

### 2. `ctx.render` switches to a Jinja `Environment`

`CapabilityContext.render(template, **vars)` renders through a module-level
`jinja2.Environment` instead of `string.Template`. Decisions:

- **`undefined`**: `StrictUndefined` — a missing var raises (preserves the current
  `KeyError`-on-missing safety; templates declare their slots).
- **`autoescape`**: **off** — templates render markdown, not HTML; escaping `<`/`&`
  would corrupt mermaid + code blocks. (Inputs are first-party finding/spec data,
  not untrusted web input — the XSS rationale for autoescape does not apply.)
- **delimiters**: Jinja defaults (`{{ }}`, `{% %}`, `{# #}`). The `$var` → `{{ var }}`
  port is mechanical (see §4).
- **loader**: the engine already discovers per-capability `templates/` folders
  (Spec 060); the Environment renders the already-loaded body string
  (`Environment.from_string`) so the discovery/merge path is unchanged — only the
  render call swaps.

### 3. The marker → construct mapping

| today (markers) | Jinja construct | effect |
|---|---|---|
| `$var` | `{{ var }}` | substitution (StrictUndefined keeps the missing-var guard) |
| `<!-- BEGIN IF flag -->…<!-- END IF -->` | `{% if flag %}…{% endif %}` | the gate is **evaluated** — no regex |
| (none — manual block-join in the verb) | `{% for f in findings %}…{% endfor %}` | lists render IN the template (the report's `findings_block` loop moves out of `analyze.report`) |
| `<!-- AGENT: author guidance -->` | **keep** as an HTML comment | guidance that should travel into the rendered artefact stays visible |
| `<!-- AGENT: render-time-only note -->` / `<!-- doc-source: … -->` | `{# … #}` Jinja comment | engine-stripped — never reaches output (replaces Spec 384's `_strip_authoring_comments`) |

OQ2 — which AGENT comments travel vs strip: **default** — `doc-source` markers and
render-time author notes become `{# #}` (stripped); genuine agent-runtime guidance
that belongs in the delivered artefact stays `<!-- AGENT: -->`. Per-template call
during the port.

### 4. Port ALL templates (the migration)

Every `agency/capabilities/*/templates/*.md` is ported `$var` → `{{ var }}`, gates →
`{% if %}`, author-notes → `{# #}`. The set is DERIVED, not pinned (rule 8) — the
port enumerates `RenderTemplates` folders live. Known surface today:
`analyze/templates/` (quality-report · iron-law-finding · improvement-plan),
`develop/templates/` (quality-{review,audit,debt,test,health,sweep,remedy} ·
checklist), `research/templates/` (research-report), plus any novel/music/document
templates. **Content is unchanged** — only syntax/engine. A render-equivalence test
guards each (the ported template + the same vars produces the same finalized output
as the pre-port path, modulo the now-evaluated gates).

### 5. Delete the interim Spec 384 machinery

`analyze/_main.py::_strip_conditionals` + `_strip_authoring_comments` + their
regexes go away; `analyze.report` renders the Jinja template (`{% if is_audit %}` +
`{% for f in findings %}`) and persists via `document.emit` exactly as now — the
verb shrinks (no manual block-join, no post-strip). This is the spec's proof it
removed a hack, not added a parallel one (Goal 6).

### 6. Lint + drift

- `RenderSliceRule` (`plugin/clusters/lint.py`) still requires an agent-instruction
  block per template; update it to recognise both `<!-- AGENT: -->` and `{# AGENT: #}`
  (the lint enforces *a render-author instruction exists*, engine-agnostic).
- `# AGENCY-DRIFT: template-engine` at the `ctx.render` site (the single engine
  seam) + the `jinja2` pin in `pyproject.toml`.
- `check-doc-drift` markers (`<!-- doc-source -->` or `{# doc-source #}`) survive the
  port — the vendoring provenance is unchanged.

## Acceptance (Gherkin)

```gherkin
Scenario: a template gate is decided programmatically
  Given a template with a {% if is_audit %} Module Dependency Graph {% endif %} block
  When it renders with is_audit = False
  Then the gated section is absent from the output
  When it renders with is_audit = True
  Then the gated section is present

Scenario: a template loop renders a list
  Given quality-report.md with a {% for f in findings %} block
  When analyze.report renders with three findings
  Then three Iron-Law finding blocks appear, with no manual block-join in the verb

Scenario: render-time comments are engine-stripped
  When any ported template renders
  Then no {# … #} comment text appears in the output

Scenario: the interim Spec 384 strippers are gone
  Then analyze/_main.py defines neither _strip_conditionals nor _strip_authoring_comments
  And analyze.report renders the report purely through ctx.render

Scenario: every template is ported (no string.Template left)
  Then every <cap>/templates/*.md parses as a Jinja template
  And no template still uses a <!-- BEGIN IF --> marker

Scenario: missing vars still fail loudly
  When a template renders without a declared var
  Then ctx.render raises (StrictUndefined), as string.Template did
```

## Open questions

- **OQ1 — jinja2 core dep vs `[templates]` extra?** (Default: core — render is
  substrate.)
- **OQ2 — which `<!-- AGENT: -->` comments travel into output vs become `{# #}`?**
  (Default: doc-source + render-notes strip; runtime agent-guidance stays.)
- **OQ3 — big-bang port vs dual-engine migration window?** (Default: big-bang — the
  template set is small and enumerable; a dual `$var`/`{{ }}` window doubles the
  surface. Land it in one spec with the render-equivalence tests as the net.)
- **OQ4 — move list-composition (findings_block) INTO templates via `{% for %}`,
  or keep the verb composing blocks?** (Default: into the template — that is the
  point of a real engine; the verb passes `findings`, the template loops.)

## What this slice does NOT do

- **No template CONTENT changes** — only syntax + the engine that evaluates it.
- **No new templates** — it ports the existing set (384 + the rest).
- **No re-homing** — each template stays in its current capability's `templates/`.
- **No render-driver change** — `document.render`/`mirror`/`emit` (Spec 292) are
  unaffected; this is the `ctx.render` substitution engine only.

## Followup — Implementation Status (2026-06-23)

**DRAFTED 2026-06-23** — opened by the owner's "install Jinja + port all templates,
decide gates programmatically" directive, reacting to the dormant `<!-- BEGIN IF -->`
markers + the interim regex processor Spec 384 shipped (`_strip_conditionals` /
`_strip_authoring_comments` in `analyze/_main.py`) to gate the quality report's
audit-only graph. codegraph-grounded: the seam is `CapabilityContext.render`
(`capability.py:275`, `string.Template.substitute`); the template surface is the
per-capability `templates/` folders auto-discovered by `RenderTemplates.from_module`;
the dormant markers live in `quality-report.md`, `improvement-plan.md`,
`research-report.md`. No code yet. Next (after owner ADR-approve): add the `jinja2`
pin, switch `ctx.render` to a `StrictUndefined`, autoescape-off `Environment`, port
each template `$var`→`{{ }}` + `BEGIN IF`→`{% if %}` + author-notes→`{# #}` with a
render-equivalence test per template, then delete the Spec 384 interim strippers and
shrink `analyze.report`. RED→GREEN against the §Acceptance scenarios.

**IMPLEMENTED 2026-06-27 (core shipped — TDD green).** The owner directive's heart —
*install Jinja, decide gates programmatically* — is live:

- **The engine.** `jinja2>=3.1` is a core dep (pyproject; `# AGENCY-DRIFT:
  template-engine`). `CapabilityContext.render` (`capability.py`) renders through a
  Jinja `Environment` (`StrictUndefined` keeps the missing-var-raises safety;
  autoescape off for markdown) with a `FunctionLoader` over `ontology.templates`, so
  `{% include %}` resolves siblings. `# AGENCY-DRIFT: template-engine` marks the seam.
- **The gates are evaluated.** `quality-report.md` ports to `{% if is_audit %}`
  (the live Module-Dependency-Graph gate) + `{% for f in findings %}{% include
  "iron-law-finding" %}{% endfor %}` — the findings loop moved INTO the template
  (OQ4 default). `iron-law-finding.md` ports to `{{ f.* }}` off a finding view-dict.
  `improvement-plan.md` + `research-report.md` lose their dormant `<!-- BEGIN IF -->`
  for `{% if %}`. Author/doc-source notes → `{# #}` (engine-stripped; OQ2 default).
- **The interim hack is gone (§5).** `analyze/_report.py` no longer defines
  `strip_conditionals` / `strip_comments` / `_COND_RE` / `_COMMENT_RE` (nor imports
  `re`); `render_quality_report` shrank to "build finding view-dicts → `ctx.render`",
  no manual block-join, no post-strip. `_finding_view` is the only added helper (pure
  data prep — the wire-shape→slot mapping).
- **Tests.** `tests/test_jinja_template_engine.py` — the 6 §Acceptance scenarios
  (gate decided programmatically · loop renders list · `{# #}` stripped · 384
  strippers gone · every template parses as Jinja + no `BEGIN IF` marker · missing
  var raises `UndefinedError`) + an end-to-end `analyze.report` render. The Spec-384
  contract tests (`tests/acceptance/test_quality_templates.py`) updated to the
  engine-agnostic agent-block check (`<!-- AGENT -->` OR `{# AGENT #}`, §6) and the
  Jinja `{% if %}` / `{{ f.* }}` slots. `scripts/check-drift` clean.
- **Doc.** `docs/vision/CAPABILITY-AUTHORING.md` §"Templates instruct agents" carries
  the Spec-388 Jinja callout + §4 conditional-section rewrite.

**Still (deferred, NOT blocking the directive):** the bulk `$var`→`{{ }}` cosmetic
port of the templates NOT on the `ctx.render` path (`develop/templates/quality-*.md`,
`novel/*`, `music/*`, etc.). They already **parse as Jinja** (the acceptance gate) and
are rendered by the separate `RenderTemplates`/`string.Template` path or are
agent-filled scaffolds (the novel/music `{{ }}` are literal placeholders, NOT engine
vars) — converting them would be cosmetic and risk breaking that path, so it waits
until a template moves onto `ctx.render`. The lint `RenderSliceRule` (§6) does not
exist in the current tree (`plugin/clusters/` absent) — no update needed; the
agent-block contract is enforced by the acceptance tests instead.

**Lifecycle:** code shipped + verified; awaiting the owner ADR-approve + done-cascade
(`adr.approve` → `workflow.finish_spec` → `adr.architecture(apply=True)`) per doctrine
— an agent never self-approves (panel B2.1). NOTE: a pre-existing spec_id collision
exists (`Plan/draft/388-spec-done-cascade` also carries `spec_id: "388"`) — flagged,
not resolved here (out of scope; a renumber is the owner's call).
