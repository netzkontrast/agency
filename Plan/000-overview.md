# Plan — Agency Plugin

Spec set for growing the **Agency** plugin (one FastMCP engine + one
bi-temporal GraphQLite graph; capabilities self-register via `@verb`;
**code-mode IS the contract**).

> **Read first:** [`docs/vision/GOALS.md`](../docs/vision/GOALS.md) (why),
> [`docs/vision/CORE.md`](../docs/vision/CORE.md) (canon),
> [`../AGENTS.md`](../AGENTS.md) (operational),
> [`../AGENCY_PROTOCOL.md`](../AGENCY_PROTOCOL.md) (remote-agent doctrine).

## How to use this plan

Each `Plan/NNN-slug/spec.md` is a standalone, Plan-style spec
(frontmatter · Why · Done When · Files · Open Questions · Evidence). Pick
the next spec by depends_on order; answer its **Open Questions** first
(those are real blocking decisions, deliberately not guessed); design +
implement (TDD); keep `pytest` green; flip `status: draft → done`.

Spec frontmatter convention: see
[`Plan/014-observation-to-spec-amendment/spec.md`](014-observation-to-spec-amendment/spec.md)
as the format reference. Required fields: `spec_id`, `slug`, `status`,
`owner`, `depends_on`, `affects`, `domain`, `wave`.

## Active spec landscape

### Shipped (done — code merged on the working branch)

| Spec | What it delivered |
|---|---|
| **001** [`toolresult-and-typed-errors`](001-toolresult-and-typed-errors/spec.md) | Internal `ToolResult` envelope dataclass (Option C — in-sandbox, wire shape unchanged). |
| **006** [`core-hardening`](006-core-hardening/spec.md) | Red-team fixes: tick, pagination, verify, env validation. |
| **012** [`jules-complete-lifecycle-and-watcher`](012-jules-complete-lifecycle-and-watcher/spec.md) | Full Jules v1alpha REST surface + the long-polling watcher (state-aware adaptive cadence) + per-intent queue + recovery flow. |
| **013** [`jules-skills-and-capability-improvements`](013-jules-skills-and-capability-improvements/spec.md) | Six Jules-specific skills + AGENCY_PROTOCOL.md doctrine + `jules.lint_prompt` + `jules.review_comment` + Mode A/B preamble + flag matrix. |
| **015** [`architecture-review`](015-architecture-review/) | Jules-led architecture review (dogfood pass). Produced JULES-OBSERVATIONS, ARCHITECTURE-REVIEW, and the three proposals promoted to specs 017-019. |

### In flight (drafted; awaiting design loop)

| Spec | What it proposes | depends_on |
|---|---|---|
| **014** [`observation-to-spec-amendment`](014-observation-to-spec-amendment/spec.md) | Close the self-improvement loop — Reflection → spec amendment via `dogfood.parse_amendment` + `classify` + `propose` (structured JSON ops, not LLM free-text). | 013, 017, 020 |
| **016** [`capability-authoring-doctrine`](016-capability-authoring-doctrine/spec.md) | **First Core Expansion.** 11 hints for capability authors (folder layout, role tags, docstring contract, `input-required` convention, graph-as-store, …). | 001, 012, 013 |
| **017** [`graph-native-dogfood-ledgers`](017-graph-native-dogfood-ledgers/spec.md) | `dogfood.note` + `dogfood.render` invert the markdown-as-store anti-pattern; closes Jules's Spec 015 W1/W2. | 013, 014, 015, 020 |
| **018** [`cli-token-efficiency-bundle`](018-cli-token-efficiency-bundle/spec.md) | Five token wins bundled: `skill.walk`, capability-prefix elision, implicit `intent_id`, compact `get_schema`, YAML `--chain`. Plus Jules's `--fields` + traceback wrapper. | 016, 020 |
| **019** [`engine-output-shape-contract`](019-engine-output-shape-contract/spec.md) | Document the engine unwrap as the contract; `lint_capability` enforces docstring describes WIRE shape (resolves Jules's Spec 015 W4 without removing the unwrap). | 016 |
| **020** [`central-graph-db`](020-central-graph-db/spec.md) | `.agency/session.db` as the per-project default; committed to git; auto-scaffolded on install. Foundational — every spec relying on cross-session persistence depends on this. | — |
| **021** [`engine-monitor-channel`](021-engine-monitor-channel/spec.md) | Engine-level Monitor channel: ONE `monitors/monitors.json` entry; capabilities fan in via `ctx.emit_monitor(...)`. Same shape principle as code-mode (one wire surface; many tools). | 020 |
| **022** [`jules-monitor-capability`](022-jules-monitor-capability/spec.md) | First use of 021: Jules watcher state transitions + `dispatch`/`recover`/`verify` surface through the engine monitor stream. No new monitors.json entry. | 012, 013, 021 |

### Wave `adr-workflow` — ADR × agency port + repo-development lifecycle (drafted 2026-06-20)

Port the `adr` repo (enhanced WH(Y) ADR) onto the substrate as a *binding*, and
build the repo's own development lifecycle around it with ADRs at the centre.
Build order: 354 → 355 → (357 ‖ 359) → 356 → 358. See the master for the full
mapping + reconciliations.

| Spec | What it proposes | depends_on |
|---|---|---|
| **353** [`adr-agency-port`](353-adr-agency-port/spec.md) | **Master.** Maps every ADR concept onto a substrate primitive; the four owner-confirmed reconciliations; reserved ontology; child sequencing. | 290, 292, 293, 307, 091, 018, 339, 047 |
| **354** [`adr-ontology-capability`](354-adr-ontology-capability/spec.md) | `AdrTheme`/`Decision` nodes (WH(Y) schema) + dependency edges + the dedicated `adr` capability (draft·validate·link·supersede·theme_status·render·impact). | 353, 293, 292, 339 |
| **355** [`adr-definition-of-done-gate`](355-adr-definition-of-done-gate/spec.md) | Definition of Done (ECADR+Dp/Rf/M) as a `ctx.elicit` Gate; decision status as a Lifecycle; cadence-driven `expired`. | 354, 339 |
| **356** [`spec-decision-extraction`](356-spec-decision-extraction/spec.md) | `extract_decisions` (spec→ADR draft) + `spec_decisions_ready` (the `/open→/inprogress` predicate) + `hints` (architecture hints loaded at impl start). | 354, 355, 292, 290 |
| **357** [`spec-state-lifecycle`](357-spec-state-lifecycle/spec.md) | Physical `Plan/<state>/` folders + `SpecLifecycle` graph mirror + `state:` frontmatter + `move_spec`·`index`·`board`; legacy grandfathered. | 353, 292, 339, 351 |
| **358** [`workflow-capability`](358-workflow-capability/spec.md) | The `workflow` capability: the walkable `develop-spec` 14-phase lifecycle + chainable per-step verbs; the ADR hinge. | 353-357, 359, 307, 018, 047 |
| **359** [`brooks-lint`](359-brooks-lint/spec.md) | A 9th `intent` critical-thinking method — conceptual integrity / essential-vs-accidental complexity / second-system effect; folds like panel findings. | 091, 092, 283 |

### Wave-1 backlog (early planning era — revisit when canon needs new ground)

| Spec | What it proposed |
|---|---|
| 002 boundary-driver-protocol | Generic Boundary/Driver + DriverRegistry (engine substrate). |
| 003 skill-phase-objects | Typed `Skill`/`Phase` parse/validate boundary. |
| 004 template-schema-coverage | Wire the generate/validate loop for the uncovered kinds. |
| 005 context-mode-and-token-economics | Output-overflow capture + recall (engine middleware). |
| 007 music-domain-capability | Prove the clustered contract on a real domain (kept as `examples/music.py`). |
| 008 superclaude-analysts | The SuperClaude analysis surface (`transmute` cluster). |
| 009 superpowers-remainder | Finish the superpowers port. |
| 010 novel-domain | Novel domain (Dramatica/NCP, gates). |
| 011 agentic-capabilities | Agentic guardrails (middleware + `gate` predicates + a skill). |

Each backlog spec has a Plan/NNN-…/REVIEW.md beside it from the earlier
spec-panel run.

## Recommended next implementation order

The wave-3 specs (012-020) are the active push. Sequence:

1. **Spec 020** (central `.agency/session.db`) — foundational; gives every
   subsequent spec a stable persistent store. Small (~100 LOC + tests),
   no dependencies, unblocks cross-session continuity.
2. **Spec 016** (capability authoring doctrine — first Core Expansion).
   The doctrine page + the subpackage-form discovery patch + the
   `lint_capability` scaffold are prerequisites for clean execution of 017-019.
3. **Spec 017** (graph-native dogfood) — depends on 020; closes the
   highest-visibility anti-pattern + makes Spec 014's amendment
   pipeline cleaner.
4. **Spec 018** (CLI compactness) — the structural lever; saves tokens
   for every future session. Depends on 016 (lint scaffold) + 020
   (skill.walk resume across sessions).
5. **Spec 019** (output-shape contract) — proves Spec 016's lint
   extensibility on a real rule.
6. **Spec 014** (observation → amendment) — depends on 017's Reflection-
   tagging + 020's persistent DB. Closes the self-improvement loop.

## Done When (this overview)

- When a spec ships, flip `status: draft → done` in its frontmatter +
  add it to the "Shipped" table above + remove from "In flight."
- When a new spec proposal lands, add it to "In flight" with depends_on
  accurate.
- When a backlog spec is revived, promote to "In flight"; keep its
  REVIEW.md in place.

This file is the **index**, not the source of truth — `Plan/NNN-…/spec.md`
files always win on conflict.

---

## Implementation Status Snapshot (2026-05-31)

Consolidation pass: every spec was reviewed against the actual code/tests on
branch `claude/plan-spec-review-74gHM` and given a verified verdict. Each
`spec.md` now carries a **`## Followup — Implementation Status (2026-05-31)`**
section with Done / Still-to-implement / Refinement-needed detail and
`file:line` + test evidence. Suite at time of review: **333 passed, 1
skipped**. This snapshot is the index; the per-spec Followup sections win on
conflict.

### Verdicts at a glance

| Verdict | Specs |
|---|---|
| **Shipped** (5) | 012, 013, 015 *(milestone — review docs + promoted 017/018/019)*, 029, 030 |
| **Partially implemented** (9) | 001, 006, 007, 016, 018, 020, 023, 024, 025 |
| **Not started** (15) | 002, 003, 004, 005, 008, 009, 010, 011, 014, 017, 019, 021, 022, 026, 028 |

### Frontmatter ↔ reality reconciliations (recommended flips — left unchanged here for owner sign-off)

- **001** frontmatter `done` → **Partially implemented** (`Codes`, `to_dict/from_dict`, convenience ctors, full verb migration, isomorphism test all absent).
- **006** overview row says *Shipped* → **Partially implemented** (fixes #1-O(1), #2 `seen_tokens`, #4 `capture_api_key` absent; `tests/test_hardening.py` missing). Spec's own `draft` is the honest value.
- **016** frontmatter `complete` → **Partially implemented** (Hint #7 docstring sweep never done; Phase 5 fixture cleanup partial; Phase 6 → Spec 028).
- **012 / 013** frontmatter `draft` → **Shipped** (overview already lists them shipped; flip frontmatter to match).
- **029 / 030** frontmatter `draft` → **Shipped** (fully implemented + tested; not yet in the Shipped table above).

### Critical-path blockers (what unblocks the most)

1. **Spec 021** (engine-monitor-channel) is *not started* and hard-blocks **022**. Nothing of the monitor channel exists yet (`agency/_monitor.py`, `monitors.json`, `ctx.emit_monitor`).
2. **Spec 002** (DriverRegistry) *not started* — hard-blocks **007**'s full music surface.
3. **Docstring sweep (Hint #7)** is the shared open item across **016 / 019 / 023** — until existing verbs gain `Inputs:`/`Returns:`/`chain_next:` markers, all three stay formally open.
4. **Spec 020** is one verb (`dogfood.export`) away from done; **014 + 017** (the self-improvement loop) remain *not started* and depend on 020 + 017's `dogfood.note/render`.
