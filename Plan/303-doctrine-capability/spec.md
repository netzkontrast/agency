---
spec: 303
title: doctrine-capability
status: Drafted (spec only — the last SuperClaude port aspect)
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

- [ ] `doctrine.principles`/`rules`/`resolve`/`cite` + a `DoctrineCitation` node.
- [ ] A **real caller**: `gate.check` (or `develop`) consults `doctrine.resolve`
  on a conflicting decision — no dormant surface.
- [ ] Acceptance scenarios (priority filter, conflict resolution, citation
  provenance).

## Audit conclusion (the goal's answer)

**Almost nothing is left to port.** SuperClaude is fully reimplemented (294-300)
or mapped (299); superpowers' disciplines are all agency skills (301). The lone
residual — PRINCIPLES + RULES — is **doctrine**, already lived through CLAUDE.md
+ skills + personas + mode. This spec captures the one net-new framing (make it
*queryable + citable*) but **gates building it on a real consumer** — per
`/simplify`, prose doctrine should not become a dormant capability.
