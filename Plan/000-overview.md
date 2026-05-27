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

| Spec | What it delivers | deps | Post-alignment home |
|---|---|---|---|
| `001-toolresult-and-typed-errors` | uniform return envelope + typed errors | — | **engine substrate** — an in-sandbox return serializer (does not cross the context boundary); carries the one remaining blocker (Q2) |
| `002-boundary-driver-protocol` | generic Boundary/Driver + DriverRegistry | 001 | **engine substrate** (`wire-handlers`, not a concept); Option B typed methods |
| `003-skill-phase-objects` | typed `Skill`/`Phase` parse/validate boundary | 001 | **Lifecycle** internals — skills stay Memory-stored templates; no new concept |
| `004-template-schema-coverage` | wire the generate/validate loop (2 uncovered kinds) | 003 | **Memory** — rung 1 of the verb-param schema-as-single-source ladder |
| `005-context-mode-and-token-economics` | output-overflow capture + recall | 001 | **engine middleware + a `transform`** (NOT a new capability — compaction is middleware per CORE.md:16-18); no hooks, no SQLite |
| `006-core-hardening` | red-team fixes (tick · pagination · verify · env) | — | **engine substrate** — fully aligned; enforces canon invariants |
| `007-music-domain-capability` | prove the clustered contract on a real domain | 001, 002 | **`examples/` extension** — ~14 representative verbs; 89-tool map = appendix (not a 1:1 bitwize port) |
| `008-superclaude-analysts` | the SuperClaude analysis surface | 001, 003 | **`transmute` cluster** — populates the canon's named-but-unbuilt `transform` facet (not a new `analyze` primitive) |
| `009-superpowers-remainder` | finish the superpowers port | 003 | **`develop` extension** — 1 discipline (`receive-review`) + references; no new capability |
| `010-novel-domain` | novel domain (Dramatica/NCP, gates) | 001,002,003 | **`examples/` extension** — capability-owned ontology; the heaviest proof of absorption |
| `011-agentic-capabilities` | agentic guardrails | 001, 003 | **middleware + `gate` predicates + a skill** — both proposed capabilities deleted; `detect_loop`=middleware, checks=`gate.check`, pressure-test=skill |

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

## Vision alignment (second pass)

Each spec went through a **vision-alignment review** (a `VISION-REVIEW.md` beside each
`spec.md`) judging it against the canon (`CORE.md`, `CAPABILITY-CLUSTERS.md`), then a
design pass applying the verdicts (**canon wins; code serves it**). The headline
outcome **validates the canon's "few primitives" thesis** — the alignment pass
*reduced* the net-new top-level capabilities rather than adding them:

- `005` context-mode and `011` agentic were demoted from "new capabilities" to **engine
  middleware + facets of `gate`/Memory + a skill** — because `CORE.md:16-18` lists
  compaction/loop-detection/quota as **middleware, not concepts**.
- `008` was **rehomed onto the existing `transmute` cluster** (`CLUSTERS:20`) instead of
  minting a new `analyze` primitive.
- `007`/`010` are confirmed **`examples/` extensions**, not core; `007` rescoped from a
  1:1 89-tool port to a representative-verb proof (89-map kept as an appendix).

After alignment, **no spec proposes a net-new top-level capability**: the set is
foundation/substrate (`001`–`004`, `006`), middleware+facets (`005`, `011`), an
existing-cluster populate (`008`), `develop`/skill extensions (`009`, `011`-skill),
and two domain examples (`007`, `010`). That is the four-concepts model holding under
the whole surveyed plugin surface — exactly the `CAPABILITY-CLUSTERS` verdict, now
re-derived spec-by-spec.

## Provenance

Source research lives under `research/` (committed, incl. each agent's `_ingest.md`
ledger). This plan supersedes the raw per-agent specs for *implementation* purposes;
the research is retained as evidence and for the citations each spec relies on.
