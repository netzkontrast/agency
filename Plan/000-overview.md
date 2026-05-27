# Plan — Agency Plugin Expansion

Consolidated, implementable spec set for growing the **Agency** plugin (one FastMCP
engine + one bi-temporal GraphQLite graph; capabilities self-register via `@verb`;
code-mode IS the contract). Distilled from the five-agent PR1 review under
`research/` (oo-architecture · capability-specs · templates-and-schemas · red-team ·
code-context-mode) into one spec per coherent area.

## How to use this plan

Each `Plan/NNN-slug/spec.md` is a standalone, Plan-style spec (frontmatter · Why ·
Done When · Design · Files · **Open Questions / Needs Research** · Evidence). They
are **drafts**, designed to be taken **one at a time**:

1. Pick the next spec in the implementation order below.
2. **Answer its `## Open Questions / Needs Research` first** — those are real
   blocking decisions/research, deliberately not guessed. Several are cross-cutting
   (see "Decide first" below).
3. Design + implement (ideally TDD); keep `pytest` green; flip `status: draft → done`.

`status: draft` everywhere = nothing here is implemented yet; this is the plan, not
the work. (`jules-orchestration` is the one capability already shipped — see
`research/capability-specs/specs/jules-orchestration.md`, the parity record.)

**Each spec has been through a spec-panel review grounded in the *real* inspiration
source** (a `Plan/NNN-slug/REVIEW.md` sits beside each `spec.md`), then refined
against that review. The panels caught — and the refinement fixed — a batch of
source-faithfulness errors the original drafts inherited from the research (e.g. the
ToolResult field set, an invented repair-tier premise, a PostgreSQL-not-SQLite
backend, a draft-07-not-2020-12 NCP schema, "304/75" counts that are really 303/54,
and a superpowers gap of 13 that is really 1). Read a spec's `REVIEW.md` for the
evidence trail behind its current shape.

## The spec set

| Spec | Replaces / enables | deps | Panel verdict → refined state |
|---|---|---|---|
| `001-toolresult-and-typed-errors` | a uniform return envelope + typed errors (foundation) | — | conditional → envelope corrected to shipped shape (`data`, `artefacts_written`, free-string codes + `trace_id`); **carries the one remaining blocker (Q2)** |
| `002-boundary-driver-protocol` | generic Boundary/Driver + DriverRegistry (foundation) | 001 | changes → resolved to **Option B** (typed methods); `fan_out` collision deferred |
| `003-skill-phase-objects` | typed `Skill`/`Phase` replacing the dict walker | 001 | approve w/ must-fix → don't-reject-empty-phases; validate in `Engine.__init__`; dicts stay |
| `004-template-schema-coverage` | ontology schema coverage for artefact kinds | 003 | approve ruling → **2** real uncovered kinds; superset dropped; validate-side wiring flagged |
| `005-context-mode-and-token-economics` | output-side context capture (context-mode) | 001 | conditional → field=`data`, hook lifecycle fixed, reimplement-in-tree; residual rides on 001-Q2 |
| `006-core-hardening` | red-team fixes (tick · pagination · verify · env) | — | approve → 3 fixes verified; **#4 reframed** (Monty-probe: not exploitable); `max()` not Clock-node |
| `007-music-domain-capability` | **bitwize-music** (all 89 tools → clusters/drivers) | 001, 002 | approve w/ must-fix → backends corrected (Postgres; urllib/boto3 split; 19 modules); 89-map intact |
| `008-superclaude-analysts` | **SuperClaude** `sc:` analysis surface + modes | 001, 003 | approve w/ must-fix → 4 axes; drop `select_tool`; modes ≤3; lens-not-agent confirmed |
| `009-superpowers-remainder` | **superpowers** disciplines not yet in `develop` | 003 | changes → real gap = **1** (`receiving-code-review`); no `lib/bin`; SHA fixed |
| `010-novel-domain` | **the-agency-system** novel domain (Dramatica/NCP) | 001,002,003 | conditional → NCP=draft-07, counts measured (303/54), honest maturity; v1 scope cut |
| `011-agentic-capabilities` | agentic invariants/loop-detection + skill pressure-tests | 001, 003 | approve w/ must-fix → transcript-as-input; `dry_run`-only v1; phantom `core.py` dropped |

## Implementation order (dependency-topological)

```
001 ToolResult ─┬─ 002 Driver ───┬───────────── 007 music
                │                 └───────────── 010 novel ── (also 003)
                ├─ 003 Skill/Phase ─┬─ 004 templates
                │                   ├─ 008 superclaude (also 001)
                │                   ├─ 009 superpowers
                │                   ├─ 011 agentic (also 001)
                │                   └─ 010 novel (also 002)
                └─ 005 context-mode
006 hardening ── independent (run any time; touches memory/jules/engine)
```

Suggested sequence: **006** + **001** first (006 is independent and de-risks the
core; 001 unblocks everything) → **002**, **003** → **004**, **005** → the
capability/domain specs **009, 008, 011, 007, 010**. Domains (007 music, 010 novel)
land last because they consume the most foundation.

## Decide first

The spec-panel pass **resolved five of the six** original cross-cutting questions
(now baked into the specs). **One true blocker remains** — answer it before building
`002`/`005`/`007`:

- **⛔ Code-mode return contract** (001 Q2 → gates 002, 005, 007). Does `Engine._wire`
  wrap verb results in the `ToolResult` envelope (so every `execute()`/CLI caller sees
  `{ok, data, …}`) or keep returning the unwrapped inner value? The panels showed the
  source (ADR-0005, "clients see the same JSON") steers toward **the envelope *is* the
  wire shape, field name `data`** — but this changes what existing `execute()` scripts
  receive, so it's the maintainer's call: accept the break, or run a dual surface
  during migration. Everything downstream assumes `data`.

Resolved by the panels (no longer open):

- ✅ **Driver shape** → **Option B**: typed named methods; `Driver` is a marker; the
  uniform contract is the *return type* (`ToolResult`), not the method name. (The cited
  "uniform dispatch" prior art actually uses named handlers.)
- ✅ **Core vs `examples/`** → domain caps (`music`, `novel`) live in **`examples/`**;
  the catalogue rows that said `agency/capabilities/` are stale.
- ✅ **Template-schema scope** → exactly **2** recorded artefact kinds lack schemas
  (`jules-session`, `reduction`); the "13" was an artefact-kind/phase-slot conflation.
  Cover the 2; the validate-side `Schema` producer is currently unwired (tracked in 004).
- ✅ **Third-party deps** → `jsonschema` ships as an **example** dep (core stays
  `fastmcp`-only); `context-mode` is **reimplemented in-tree** (ELv2 makes a runtime dep
  toxic) with the marketplace plugin as an opt-in companion.
- ✅ **Hook layer** → **out of scope for v1**: loop-detection ships as a pure verb,
  context-mode snapshot/restore is deferred (Plan-120 territory); no hook layer is built
  yet.

Residual per-spec open questions are all non-blocking and listed in each spec
(e.g. 007's driver-injection point depends on whether 002's registry shipped; 011's
`pressure.run` wet path needs a local LLM-bearing driver that doesn't exist yet).

## Provenance

Source research lives under `research/` (committed, incl. each agent's `_ingest.md`
ledger). This plan supersedes the raw per-agent specs for *implementation* purposes;
the research is retained as evidence and for the citations each spec relies on.
