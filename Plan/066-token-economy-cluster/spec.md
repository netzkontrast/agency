---
spec_id: "066"
slug: token-economy-cluster
status: draft
last_updated: 2026-06-06
owner: "@agency"
serves_intent: "intent:97534079"
children: ["072", "067", "068", "069", "070", "071"]   # 072 = doctrinal anchor, builds FIRST
informs: ["023", "049", "047"]
domain: meta
wave: 5
---

# Spec 066 — Token-Economy & Readability cluster (master)

> Master coordination spec (the Spec 047 precedent: a master maps the program;
> children ship the code). The master is the source of truth UNTIL a child ships;
> the child's Followup wins thereafter.

## Why

Spec 049's audit established the measurement: the agency surface costs tokens on
**every** session's discovery call, and the cost scales with a surface that grew
to 69 verbs / 14 capabilities / two skill surfaces. The audit's headline — the
`capability_<cap>_` prefix is 202 tok of pure repetition — is real but only 14%
of the discovery payload; the flat dump of all 69 verbs is the larger tax, and
the two-skill-surface divergence is a readability tax.

This cluster makes the system **measurably cheaper to read, write, and discover**
without weakening a `GOALS.md` goal. It is **lint-first**: the goals are encoded
as decidable `plugin.lint_capability` rules BEFORE the surface changes, so each
subsequent change is gated by the executable test for the goal.

## The charter (binding self-instruction)

Implement autonomously, spec by spec, lint-first, TDD (RED→GREEN). Quality,
agency-integration, and migration are non-negotiable:
- **Quality:** every change passes `pytest -n auto -m "not e2e"` + `check-drift`
  + self-review; merge green before the next.
- **Agency-integration:** code-mode stays the only contract (Goal 5); the
  `<concept>_<capability>_<verb>` form stays on the FastMCP wire per CORE §Naming
  (only the code-mode call surface gains a bare alias); lint rules extend the
  existing `_check_*` family; provenance (SERVES) stays whole.
- **Migration:** every rename/consolidation is alias-and-deprecate (old + new one
  minor, deprecation flag, removal next minor) — never a hard break.
- If a change would weaken a GOALS goal, STOP and carry the trade-off into the
  spec body + panel review.

## Goal → lint-rule map (the executable test, Spec 067)

| GOALS.md goal | Readability/token pressure | Lint rule (Spec 067) |
|---|---|---|
| 1 — token efficiency | long names repeated on every discovery call | `name_token_budget` (warn when a verb/tool name > N cl100k tokens) |
| 1 — token efficiency | flat dump of the whole surface | `surface_size` (warn when a capability exceeds M verbs without sub-grouping) |
| 5 — code-mode contract | bare-name dispatch ambiguity | `bare_name_unique` (warn on cross-capability bare-name collision) |
| (readability) | two skill surfaces diverge | `skill_name_parity` (warn when an ontology skill key has no matching SKILL.md, or they diverge) |
| 1 — token efficiency | verbose discovery brief | `brief_budget` (already shipped as Spec 023 `render_slice` ≤120 chars — assert parity) |

All Spec 067 rules ship WARN-first (the established 056/058 migration discipline),
flip to BLOCK once the audited surface is clean.

## Children

> **Doctrine before enforcement before implementation.** Spec 072 (the CORE.md
> alignment) builds FIRST so the lint rules (067) enforce *aligned* doctrine, not
> drifted doctrine. Build order ≠ spec number (072 is the newest number but the
> first build) — the table below is authoritative.

| Build | Spec | Role | Gate it must pass (from 067) | Migration |
|---|---|---|---|---|
| **0** | **072** core-vision-alignment | doctrine: fix CORE §Naming/§Skills/§Status to serve GOALS #1 (via spec-panel) | — (defines the WHY the rules encode) | doctrine-only |
| **1** | **067** lint-token-economy-rules | encode the goals as `lint_capability` rules | (defines the gates) | additive WARN rules |
| **2** | **068** tiered-discovery | capability-level discovery → drill-in (extends 023) | `surface_size` | additive; flat search stays a fallback |
| ~~3~~ | ~~**069** naming-rename-impl~~ | **CANCELLED** — FastMCP-blocked (one CodeMode catalog) + marginal post-068; `name_token_budget`/`bare_name_*` accepted as standing WARNs | — | n/a |
| **3** | **070** verb-surface-consolidation | collapse near-duplicate verbs | `surface_size` → BLOCK | alias-and-deprecate per collapsed verb |
| **4** | **071** skill-surface-reconciliation | unify ontology key ↔ SKILL.md folder | `skill_name_parity` → BLOCK | alias old skill names one minor |

## Promotion criteria

Per CLAUDE.md Rule #5: when a child's integration plan grows past ~150 lines OR
triggers ≥ 3 cross-cluster decisions, it stays a standalone spec (already the
case — each child has its own folder). This master only carries the roll-up.

## What this cluster does NOT do

- It does NOT hard-break any name (migration is alias-and-deprecate throughout).
- It does NOT drop the `<concept>_<capability>_<verb>` wire form (CORE §Naming).
- It does NOT add a parallel measurement system — the lint pipeline + `check-drift`
  ARE the measurement (Goal 2/7: the graph + the existing guards, not new markdown).

## Evidence

- `GOALS.md` goals 1, 2, 5, 6, 7; `CORE.md` §Naming (wire form) + §"Skills are
  atomic, gated, progressively-disclosed step-graphs" (the tiered-discovery basis).
- Spec 049 `naming-audit-report.md` (the measured baseline + per-name verdicts).
- Spec 023 (adaptive disclosure — the brief-budget + slice machinery 067/068 extend).
- Spec 047 (cluster-integration master precedent); Spec 016/019/054/056/058 (the
  lint pipeline this cluster extends).
