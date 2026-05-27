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

## The spec set

| Spec | Replaces / enables | depends_on | Open Qs |
|---|---|---|---|
| `001-toolresult-and-typed-errors` | a uniform return envelope + typed errors (foundation) | — | 7 |
| `002-boundary-driver-protocol` | generic Boundary/Driver + DriverRegistry (foundation) | 001 | 7 |
| `003-skill-phase-objects` | typed `Skill`/`Phase` replacing the dict walker | 001 | 6 |
| `004-template-schema-coverage` | full ontology schema coverage for artefact kinds | 003 | 9 |
| `005-context-mode-and-token-economics` | output-side context capture (context-mode plugin) | 001 | 7 |
| `006-core-hardening` | red-team fixes (tick scan · pagination · verify · env) | — | 3 |
| `007-music-domain-capability` | **bitwize-music** (all 89 tools → 8 clusters / 5 drivers) | 001, 002 | 6 |
| `008-superclaude-analysts` | **SuperClaude** `sc:` analysis surface + personas/modes | 001, 003 | 5 |
| `009-superpowers-remainder` | the **superpowers** disciplines not yet in `develop` | 003 | 4 |
| `010-novel-domain` | **the-agency-system** novel domain (Dramatica/NCP, gates) | 001, 002, 003 | 6 |
| `011-agentic-capabilities` | agentic invariants/loop-detection + skill pressure-tests | 001, 003 | 6 |

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

## Decide first (cross-cutting questions that gate multiple specs)

These recur across the Open-Questions sections and should be answered before the
dependent specs are built:

1. **Code-mode return contract** (001 Q2 → gates 002, 005, 007). Does `Engine._wire`
   wrap results in `ToolResult` (so `execute()` callers see `{ok,data,…}`) or keep
   returning the unwrapped `data`? The single load-bearing decision for the envelope.
2. **Driver shape** (002 Q1 → gates 007, and whether `JulesBackend`/`VCSBackend`
   survive). Uniform `dispatch(op, **kw)` vs. typed named methods.
3. **Core vs `examples/` for domain capabilities** (007 Q1, 010 Q1). The repo rule
   says domain caps live in `examples/`; the capability-catalogue drafts put them in
   `agency/capabilities/`. Pick one; it only changes `affects:` paths.
4. **Template-schema scope** (004 Q1). The research's "13 remaining" conflates
   artefact-kinds with phase-slot names — only **2** real kinds (`jules-session`,
   `reduction`) lack schemas. Cover just those, or redefine verbs so phase slots
   become recorded artefacts?
5. **Third-party deps policy** (010 Q3, 005 Q2). Core is `fastmcp`-only today. Do we
   add `jsonschema` (novel/NCP), and is an optional `context-mode` dependency
   license-compatible? Or vendor/hand-roll.
6. **Is a hook layer in scope?** (005, 011 Q1). Output-side context capture and
   loop-detection throttling both want Claude-Code hooks; Agency has none yet.

## Provenance

Source research lives under `research/` (committed, incl. each agent's `_ingest.md`
ledger). This plan supersedes the raw per-agent specs for *implementation* purposes;
the research is retained as evidence and for the citations each spec relies on.
