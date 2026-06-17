---
spec: 303
title: doctrine-capability
status: Shipped
depends_on: [294, 295, 299, 301]
clusters: [thinking, develop]
vision_goals: [4]
---

# Spec 303 — `doctrine`: queryable engineering principles + behavioral rules

> Closes the SuperClaude/superpowers port audit (goal 2026-06-17): after panel ·
> mode · select · persona · recommend · symbols (294-300), the **only**
> genuinely-unported aspect is SuperClaude's `core/PRINCIPLES.md` +
> `core/RULES.md` — its behavioral doctrine. Everything else is reimplemented or
> mapped (FLAGS→`mode`, RESEARCH_CONFIG→`research`, BUSINESS_SYMBOLS→`symbols`,
> dev-for-cc→`plugin`).

## Extract (what's actually there)

- **PRINCIPLES** — engineering principles: SOLID, evidence-based reasoning,
  task-first (Understand→Plan→Execute→Validate), context-awareness.
- **RULES** — behavioral rules with a **priority system** (🔴 CRITICAL / 🟡
  IMPORTANT / 🟢 RECOMMENDED) and a **conflict-resolution hierarchy** ("Safety
  First: security/data rules always win").

## Brainstorm → the gap

Agency already *expresses* this doctrine — but as PROSE (CLAUDE.md rules), skill
**Red flags**, persona **approaches**, and `mode` **behaviors**. What's missing
is making it **queryable + citable**: a verb that returns the priority-ranked
rule for a situation, resolves a conflict ("safety vs speed → safety"), and
records that a principle was *applied* (provenance), the same way `mode`
records an adopted posture.

## Design (simplified — ONE capability, not two)

`doctrine` — decidable, like `mode`/`panel` (no LLM):

- `doctrine.principles()` — the engineering-principles roster (name · statement).
- `doctrine.rules(priority="")` — behavioral rules, optionally filtered by
  priority; each `{rule, priority, triggers}`.
- `doctrine.resolve(a, b)` — given two rule names/categories, return the winner
  by the conflict hierarchy (safety > correctness > maintainability > speed).
- `doctrine.cite(name)` — record a `DoctrineCitation` node SERVING the intent
  (an action was taken *because of* a principle/rule — auditable provenance).

## Spec-panel pass (multi-lens critique, then revise)

- **Christensen (job-to-be-done):** what job does this do that CLAUDE.md
  doesn't? → make doctrine *machine-queryable + citable*, not just human prose.
  If no verb ever calls `doctrine.resolve`/`cite`, it's dormant surface (Spec
  031 anti-pattern) — **so gate adoption on a real caller** (e.g. `gate.check`
  consulting `doctrine.resolve` on a conflict).
- **Taleb (fragility):** a frozen rule list rots. → `principles`/`rules` are
  *derived where possible* (e.g. persona approaches already encode SOLID) and
  the set is small + overridable, not a snapshot (CLAUDE.md rule 8).
- **Meadows (systems):** the highest leverage is the *conflict hierarchy*, not
  the rule list — that's the part agency lacks. Keep `resolve` central; the
  roster is secondary.
- **Doumont (least effort):** don't add `principles` AND `rules` AND `flags`
  capabilities — `flags` is already `mode`; fold principles+rules into ONE
  `doctrine` capability. (Applied above.)

**Revised decision:** ship `doctrine` ONLY if a real consumer needs
`resolve`/`cite` (gate or develop). Otherwise the doctrine stays prose — porting
it as dormant surface would be the over-engineering `/simplify` warns against.

## Done-When (if built)

- [x] `doctrine.principles`/`rules`/`resolve`/`cite` + a `DoctrineCitation` node.
- [x] A **real caller**: `gate.adjudicate(a, b)` consults `doctrine.resolve` on a
  conflicting decision (recording a `doctrine.resolve` Invocation that SERVES
  the intent) — no dormant surface.
- [x] Acceptance scenarios (priority filter, conflict resolution, citation
  provenance, gate-adjudication integration).

## Followup — Implementation Status (2026-06-17)

- **Status: Shipped.** Built behind the spec-panel gate (a real consumer
  exists), so this is not the dormant surface `/simplify` warns against.

**Done (`agency/capabilities/doctrine/_main.py`):**
- `principles()` — 5-entry engineering-principles roster (SOLID, evidence-based,
  task-first, context-awareness, derive-dont-duplicate).
- `rules(priority="")` — 7 behavioral rules with the SuperClaude priority system
  (critical/important/recommended), each carrying its hierarchy `category` +
  `triggers`; filterable by priority.
- `resolve(a, b)` — the conflict-resolution hierarchy (the highest-leverage part
  per the Meadows lens): classifies each concern (rule name / category /
  free-text like "ship fast") into `safety > correctness > maintainability >
  speed` and names the winner; equal categories → `tie` (caller decides).
- `cite(name, rationale="")` — records a `DoctrineCitation` node SERVING the
  intent (provenance); rejects an unknown principle/rule by naming it.
- `DoctrineCitation` ontology node (`["name"]` required) registered via
  `OntologyExtension`.

**Real caller (non-dormancy gate satisfied):** `gate.adjudicate(a, b,
lifecycle_id="")` in `agency/capabilities/gate/_main.py` delegates to
`doctrine.resolve` via `ctx.call` — recording a `doctrine.resolve` Invocation
that SERVES the intent — and persists the verdict as a Gate node. The
acceptance suite asserts that Invocation is recorded (proving the surface is
exercised by a non-test consumer).

**Tests** — `tests/acceptance/features/doctrine.feature` (7 scenarios) +
`tests/acceptance/test_doctrine.py`: roster lookup, priority filter, hierarchy
resolution, citation provenance, unknown-name rejection, and the gate→doctrine
integration. The doctrine config is a small named/overridable set (like `mode`'s
`_MODES`), not a frozen snapshot of live state — rule 8 compliant.

**Decisions:** the spec's draft named `gate.check` as the consumer; shipped as a
dedicated `gate.adjudicate` verb instead (additive, non-invasive — `gate.check`'s
subtle SUPERSEDED_BY-chain guard stays untouched).

## Audit conclusion (the goal's answer)

**Almost nothing is left to port.** SuperClaude is fully reimplemented (294-300)
or mapped (299); superpowers' disciplines are all agency skills (301). The lone
residual — PRINCIPLES + RULES — is **doctrine**, already lived through CLAUDE.md
+ skills + personas + mode. This spec captures the one net-new framing (make it
*queryable + citable*) but **gates building it on a real consumer** — per
`/simplify`, prose doctrine should not become a dormant capability.
