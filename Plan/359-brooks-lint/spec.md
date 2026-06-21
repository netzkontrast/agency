---
spec_id: "359"
slug: brooks-lint
status: draft
last_updated: 2026-06-20
owner: "@agency"
depends_on: ["091", "092", "283"]
vision_goals: [6]
domain: core
wave: adr-workflow
affects:
  - agency/capabilities/intent/_main.py
  - agency/capabilities/panel/_main.py
  - tests/acceptance/features/brooks_lint.feature
---

# Spec 359 — Brooks-lint: a conceptual-integrity critical-thinking pass

> Child of **353**. Adds the *deeper* design-critique the owner asked to slot in
> after spec-panel ("jetzt neu auch tiefer Brooks-lint"). A 9th critical-thinking
> method grounded in Fred Brooks, run in the workflow improve-loop (358).

## Why

Owner directive: the design loop should be *"spec → spec-panel → **jetzt neu auch
tiefer Brooks-lint** — hinterfragen … dann improve, im Loop bis das Design gut
ist."* spec-panel (Spec 283) brings a *business/strategy* expert panel
(Christensen, Porter, Taleb, …) and `intent` ships eight *reasoning* methods
(Spec 091/092: decompose, assumptions, first_principles, tradeoffs, steelman,
second_order, premortem, inversion). What is missing is a pass focused on
**software conceptual integrity** — the Fred Brooks lens (*The Mythical Man-Month*,
*No Silver Bullet*) — which catches a different class of defect than either: the
spec that is *clever but incoherent*, that confuses essential with accidental
complexity, or that exhibits the second-system effect (gold-plating a design with
every feature the author wished the first system had).

This is the cheapest possible insurance against the most expensive defects in *this*
repo, where conceptual integrity (CORE.md's "four irreducible concepts") is the
explicit design value.

## Design

### `intent.brooks_lint(target, kind="spec")` — role `transform`

The 9th method on the `intent` critical-thinking surface (joins the Spec 091/092
family, same shape: takes a target — a spec id, design text, or decision —
returns structured findings). It scores the target against **five Brooks
principles**, each a decidable heuristic + an optional LLM sharpening (barbell,
like 356): findings emit with no key; an LLM refines wording when keyed.

| Principle | Question the lint asks | Decidable signal |
|---|---|---|
| **Conceptual integrity** | Does this fit the system's few core ideas, or bolt on a parallel one? | new top-level concept / parallel store / second tracking system introduced (cf. agency's "no parallel store" non-goal) |
| **Essential vs accidental complexity** | Is the complexity inherent to the problem, or incidental to the chosen mechanism? | mechanism-heavy `## Design` with a thin `## Why`; new deps where stdlib/native would do (frugal floor) |
| **Second-system effect** | Is this gold-plating — every feature the author wished for, not what's needed? | acceptance criteria far exceed the stated `## Why`; many "nice-to-have" slices; YAGNI smell |
| **No silver bullet** | Does it claim a 10× win from one change without the trade-off? | benefit claims with an empty/again-thin `## Failure modes` / tradeoffs |
| **Plan to throw one away / what doesn't change** | Is the irreversible part minimised; is the stable core separated from the volatile? | irreversible surface (wire contract, ontology enums) changed without an additive-migration note |

Output:

```
{target, kind, findings:[{principle, severity: info|warn|block, msg, evidence}],
 conceptual_integrity_ok: bool, summary}
```

`block` findings are reserved for conceptual-integrity / irreversible-surface
violations (the ones agency's canon treats as non-negotiable); everything else is
`warn`/`info`. The lint **advises**; it does not auto-edit — findings fold into the
spec like spec-panel findings (a `## Brooks-lint findings folded in` section), and
the human/owner decides.

### Panel surfacing

`panel` (or `develop.spec_panel`) gains **Brooks** as a named lint pass so the
existing "fold panel findings into the spec" plumbing carries Brooks-lint output
with zero new mechanism — it is one more finding source, recorded as an
`Artefact`/`Reflection` `SERVES` the intent (provenance, Goal 6).

### Where it runs

In `workflow.develop-spec` (358), Brooks-lint is the phase **after** spec-panel
and **before** the improve gate: panel critiques *strategy/market*, Brooks-lint
critiques *conceptual integrity*, then the improve-loop iterates both until the
design gate passes. It is also independently callable (`intent.brooks_lint(spec)`)
on any spec, any time.

## Done When

- [x] `intent.brooks_lint(target, kind="spec")` returns findings across the five
      principles with correct severities; decidable path works with **no API key**
      (LLM sharpening is a later barbell add).
- [x] A clean spec yields `conceptual_integrity_ok=true`; a fixture spec that
      introduces a parallel store yields a `block` conceptual-integrity finding; a
      gold-plated fixture yields a second-system `warn`.
- [~] Brooks-lint folds into a spec's `## Brooks-lint findings folded in` section
      via the panel-fold plumbing — DEFERRED to the 358 improve-loop (which runs
      the lint + folds); the method + its `critical-thinking` stress-test phase
      wiring shipped here.
- [x] Acceptance scenarios (behaviour, rule 7); no unit tests on the heuristics'
      internals (the heuristics live in `intent/_brooks.py`, exercised only
      through the verb).

## Failure modes (Nygard)

| Failure | Response |
|---|---|
| Heuristics are vibes; findings are noise | Each principle has an *evidence* anchor (the span/section that triggered it); a finding with no evidence is suppressed |
| Brooks-lint becomes a hard gate and stalls every spec | It advises; only conceptual-integrity / irreversible-surface findings are `block`, and the owner can override (provenance-stamped) in the improve-loop |
| Duplicates spec-panel | Distinct lens (conceptual integrity vs market/strategy); the two run as separate, complementary finding sources |
| Frozen thresholds (e.g. "≥N slices = second system") | Documented tunable budgets, not snapshots (rule 8) |

## Interconnects

- **091/092** — the `intent` critical-thinking method family; this is the 9th.
- **283 (spec-panel)** — reuses the fold-findings plumbing; Brooks is a new pass.
- **358 (workflow)** — runs Brooks-lint in the design improve-loop.
- **353** master.

## Followup — Implementation Status (2026-06-21)

### Done — the lint method (TDD, shipped)
- `intent.brooks_lint(target, kind="spec")` — the 9th critical-thinking method
  (joins the Spec 091/092 family on `intent`), but an ANALYSER not a scaffold:
  decidable, evidence-anchored findings across the five Brooks principles. Pure
  heuristics live in `agency/capabilities/intent/_brooks.py` (`brooks_findings`):
  - **conceptual-integrity** (block): a `parallel/second/separate … store/system/
    index` or a `bypass the substrate` regex match.
  - **essential-vs-accidental** (warn): `len(## Design) > 3×len(## Why)` (tunable).
  - **second-system** (warn): ≥2 gold-plating markers (nice-to-have / future
    enhancement / while-we're-at-it / wish-list …).
  - **no-silver-bullet** (warn): a 10×/"solves all"/"just works" claim with a thin
    (<40-char) Failure-modes section.
  - **plan-to-throw-one-away** (block): an irreversible surface (wire contract /
    breaking change / remove-the-X-edge) touched with NO additive-migration note.
  Every finding cites `evidence` (no evidence ⇒ never emitted — Nygard row);
  `conceptual_integrity_ok` = no block. `target` resolves a Document id → latest
  revision body, "" → the serving intent's deliverable, else raw text.
- Wired into the `critical-thinking` skill's **stress-test** phase (verb list).
- **4 acceptance scenarios** (`brooks_lint.feature`): coherent → ok · parallel-store
  → block · gold-plated → second-system warn · every finding cites evidence.
- Distinct from the 380s brooks-lint **code-quality** program (that lints code
  decay on `analyze`; this lints **design conceptual integrity** on `intent`).

### Still
- Panel surfacing + the `## Brooks-lint findings folded in` fold — lands with the
  358 improve-loop (it runs the lint + folds the findings).
- Optional LLM sharpening of finding wording when keyed (barbell; decidable
  stands alone).
