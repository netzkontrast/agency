---
spec_id: "072"
slug: core-vision-alignment
status: draft
last_updated: 2026-06-06
owner: "@agency"
serves_intent: "intent:97534079"
parent: "066"
build_order: 0   # the DOCTRINAL ANCHOR — builds FIRST, before the lint rules (068)
depends_on: []
affects:
  - docs/vision/CORE.md          # the canon edits (via spec-panel)
  - docs/vision/GOALS.md         # only the §"How the goals show up" table row(s)
estimated_jules_sessions: 0
domain: meta
wave: 5
---

# Spec 072 — Align CORE.md with the Vision goals (doctrinal anchor)

> Builds FIRST in the token-economy cluster (Spec 066). The lint rules (068) and
> the implementations (069–072) enforce the doctrine this spec corrects. Because
> it edits **canon**, the CORE.md changes go through the `spec-panel` discipline
> (multi-expert critique) BEFORE commit — per the cluster charter.

## Why

CORE.md is the canon "how"; GOALS.md is the "why". This session's work (Spec 049
audit + the 056/058 lint extensions) surfaced four places where CORE has **drifted
from its own goals** — so the doctrine the lint pipeline is about to enforce is
itself misaligned. Fix the doctrine first.

## The misalignments (each cites the goal it under-serves)

1. **§Naming is token-blind (GOALS #1).** "Tool names
   `<concept>_<capability>_<verb>`" endorses the verbose wire form with no
   reference to token cost or the code-mode-vs-wire distinction the 049 audit
   established. CORE must say: the `<concept>_<capability>_<verb>` form is the
   **FastMCP wire name** (kept — it disambiguates multi-plugin hosts), but the
   **code-mode `call_tool` surface SHOULD expose a bare alias** (token
   efficiency), and names carry a **token budget** (enforced by Spec 068 lint).

2. **Progressive disclosure is scoped only to skill-walks (GOALS #1).** §"Skills
   are atomic, gated, progressively-disclosed step-graphs" says tokens are paid
   per step — but nothing says **discovery itself** is tiered, and GOALS #1
   promises "the full tool list never loads into context" while `search` dumps
   all 69 verbs flat. CORE must state progressive disclosure applies to
   **discovery** too: capability-level index → verb-level drill-in (the basis
   for Spec 069 tiered-discovery).

3. **The two skill surfaces are unacknowledged (readability).** CORE implies one
   skill concept; the engine has BOTH `ontology.skills` keys (walkable Lifecycle
   templates) AND `skills/<name>/SKILL.md` folders (marketplace), and they
   **diverge** (`tdd` ↔ `test-driven-development`, only ~7 of 21 match). CORE must
   name both surfaces + the canonical-name direction (Spec 072 reconciliation).

4. **§Status is stale (accuracy).** "56 passing… the only net-new specs were
   delegate and reflect… Next: build the delegate spec" — all obsolete (delegate
   shipped; 37 specs shipped; 766+ tests; 14 capabilities). CORE must either
   refresh to current reality OR (preferred) become **version-agnostic** and
   point at `TODO.md` as the live index (so it never drifts again).

## Done When

- [ ] **spec-panel run** on the proposed CORE.md diff (multi-expert critique →
  synthesized revision) recorded as provenance; no goal weakened.
- [ ] **§Naming** rewritten: wire form vs code-mode bare alias + the token-budget
  pointer (Spec 068).
- [ ] **§Skills / §Engine** gains an explicit "progressive disclosure at the
  discovery layer" statement (grounds Spec 069).
- [ ] **A skills-surface note** added: the two surfaces + the reconciliation
  direction (grounds Spec 072).
- [ ] **§Status** made version-agnostic, pointing at `TODO.md` (the binding
  index) instead of a frozen count — so it cannot re-drift.
- [ ] **GOALS.md §"How the goals show up"** row for Goal 1 updated to cite the
  tiered-discovery + name-budget surfaces once they exist (forward-reference OK).
- [ ] No code changes; no behaviour change. Doctrine-only. `check-drift` clean.

## What this spec does NOT do

- It does NOT change any tool name, verb, or skill (those are 069–072).
- It does NOT add a goal or remove one — it re-aligns the HOW with the existing WHY.
- It does NOT touch GOALS.md's goal list (only the "how the goals show up" table).

## Migration

Doctrine-only — no runtime migration. But the CORE edits are **forward-compatible
promises**: they describe the target state (bare code-mode alias, tiered
discovery, reconciled skills) that 069–072 then implement. Each implementation
spec cites the CORE section it fulfils, closing the doctrine→code loop (GOALS #6).

## Evidence

- `docs/vision/CORE.md` §Naming, §Skills, §Status (the drift sites).
- `docs/vision/GOALS.md` #1 (token efficiency), #5 (code-mode contract), #6
  (dogfood loop), #7 (graph-as-store).
- `Plan/049-naming-and-token-economy/naming-audit-report.md` (the measured basis
  for the naming + skill-surface corrections).
- `agency/skills/spec-panel` + `develop.spec-panel` discipline (the canon-edit gate).
