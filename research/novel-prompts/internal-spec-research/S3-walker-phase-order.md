# F3 — Optimal Phase Order for the `work-concept` Skill Walker

> **Audience:** Gemini Deep Research (or equivalent).
> **Maps to:** Spec 010 §"Skills `work-concept`" and Loop 6 (the
> conceptualizer skill walker).
> **Deliverable expected from Gemini:** ≤ 4000 tokens cited markdown.

---

## Question

The `work-concept` Lifecycle skill in Spec 010 currently proposes seven
phases:

```
foundation → premise → storyform → cast → structure → world → confirmation(hard)
```

This mirrors the `examples/music.py::album-concept` precedent (the only
shipped conceptualizer-kind skill in agency). The Novel domain has
multiple competing canonical phase orders in the field:

- **Save-the-Cat 15-beat structure** (Blake Snyder) — opening image →
  theme stated → setup → catalyst → debate → break-into-2 → b-story
  → fun-and-games → midpoint → bad-guys-close-in → all-is-lost → dark-
  night-of-the-soul → break-into-3 → finale → final-image.
- **Story Grid 5-leaf structure** (Shawn Coyne) — global story →
  internal story → genre conventions → obligatory scenes → quintet
  arcs.
- **The Snowflake Method 10-step** (Randy Ingermanson) — one-sentence
  summary → expand to paragraph → character sheet per character →
  expand to one-page synopsis → expand to four-page synopsis → expand
  to one-page-per-scene → write the draft → revise.
- **John Truby's 22-step** (Anatomy of Story).
- **Dramatica's own 4-throughline + 6-gate** (the source-shipped
  pre-drafting gate Spec 010 ports as `pre_drafting_gate`).

What is the **optimal phase order** for an author-facing skill walker
that **hard-gates pre-drafting**?

The optimisation criteria are agency-specific:

1. **Each phase must produce a strict artefact** (a Premise node, a
   Storyform node, etc. — the OntologyExtension's node types are the
   v1 anchors).
2. **Progressive disclosure** — only the active phase's body is in
   context; the user / orchestrator never sees the full walker.
3. **The terminal phase is a hard human-confirm gate** (matches
   `album-concept`).
4. **The `pre_drafting_gate` (6 gates) DELEGATES to a verb**, doesn't
   inflate the walker — one source of truth.

## Specialists (sources to consult)

| Source kind | Specific targets |
|---|---|
| **Existing competitors** | The five canonical structures above + their tool implementations (Save-the-Cat Software, Story Grid Workbook, Snowflake Pro, Truby's BlockbusterPlot) |
| **Computational authoring** | Any 2022+ academic paper on staged authoring (paper search "staged narrative composition", "story scaffolding skills") |
| **Agency precedent** | `examples/music.py::album-concept` (read the actual phases, the artefact-per-phase schema) |
| **Spec 010 source-fidelity** | The 6-gate `pre_drafting_gate` already names: dramatica_confirmed, ncp_valid, premise_locked, cast_complete, pov_declared, sources_verified. The walker must HAND OFF to the gate, not duplicate it. |
| **Narrative-craft authors** | John Truby, Robert McKee, Lisa Cron, Donald Maass — published craft-books on order-of-operations in pre-drafting |

## Method (verification rules)

- **No phase recommendation** without naming WHICH ARTEFACT NODE TYPE
  it produces (matched to the Spec 010 OntologyExtension: `Work`,
  `Chapter`, `Scene`, `Character`, `Premise`, `Storyform`, `Coherence`).
  If a phase doesn't produce one of these, it doesn't belong in the
  walker (it's a sub-step or a skill-walker-level detail).
- **Phase order MUST be justifiable by dependency** — a phase can only
  cite artefacts from earlier phases. No cycles.
- **Terminal phase MUST be a hard gate** — not a soft check, not a
  publication step. The same shape as `album-concept`.
- **Comparison MUST be normalised against the agency artefact set** —
  Save-the-Cat's "All Is Lost" beat is a scene-level event, NOT an
  artefact node; map it correctly (it's a Scene with a specific
  `throughline` field value, not its own walker phase).

## Output format

```
# Optimal Phase Order for `work-concept` Skill Walker

## 1. The five competing structures — normalised
For each of {Save-the-Cat, Story Grid, Snowflake, Truby-22, Dramatica-
4+6}: a table mapping their named "steps" to the agency artefact node
types (Work / Premise / Storyform / Character / Chapter / Scene). Many
steps will collapse onto the same node type — that's the point of
normalisation.

## 2. Phase-order dependency graph
A DAG (textual representation acceptable; ASCII or markdown-table) of
the artefact dependencies:
- Work needs (Premise, Storyform); Storyform needs Dramatica selections;
  Cast (Character set) needs Storyform's throughlines; etc.

## 3. The proposed 7-phase order (with critique)
Take the Spec 010 proposed order:
  foundation → premise → storyform → cast → structure → world →
    confirmation(hard)
Critique each transition. Should "structure" come before "cast" or
after? Is "foundation" a meaningful phase or does it dissolve into
premise + storyform? Should "world" precede "cast" for high-fantasy
works?

## 4. Alternative proposals
Propose 2 alternative phase orders, each justified by a specific
target sub-genre or authorial workflow. Score each against the four
optimisation criteria (artefact-per-phase, progressive disclosure,
hard terminal gate, gate-delegates-to-verb).

## 5. Recommendation
ONE recommended phase order with full justification. Identify any
phases that should be OPTIONAL (param-driven) vs. MANDATORY. Identify
the artefact each phase emits + the schema it validates against.

## 6. Hand-off to pre_drafting_gate
At what point does the walker call `pre_drafting_gate`? Before
confirmation, or AS the confirmation? Recommendation + rationale.

## 7. Cited bibliography
```

## Acceptance

- [ ] Every recommended phase names the artefact node type it produces.
- [ ] The DAG (§2) has no cycles.
- [ ] §5 picks ONE order; alternatives are documented but not
  bet-hedged.
- [ ] §6 has a concrete answer (timestamp of `pre_drafting_gate` call).
- [ ] At least 3 of the 5 competing structures are normalised against
  the agency artefact set in §1.

## How to feed into Spec 010

- §5 → becomes the v1 `work-concept` skill walker's phase list (Spec
  010 §"Skills"). Either confirms the proposed 7-phase order or
  replaces it.
- §6 → resolves Spec 010 §"Open Question 6" (skill walker vs.
  `gate.check` composition for the 6-gate) — currently resolved to
  "skill delegates to verb", but F3 confirms the exact phase.
- §3+§4 → the rationale section in the walker's docstring; users
  reading the walker can see the alternatives we considered.
- §1's normalisation table → goes into a new file
  `docs/vision/NARRATIVE-STRUCTURES-COMPARISON.md` as a reference.

## Anti-patterns (Gemini should avoid these)

- Recommending a 15-phase walker. The agency skill-walker discipline
  emphasises progressive disclosure; >10 phases is anti-pattern.
- Recommending phases that don't emit artefact nodes. Walker phases
  ≠ author craft-steps. Many author craft-steps collapse to one
  walker phase.
- Treating all five competing structures as equally good. The point
  of the survey is to pick.
- Inventing a brand-new structure. Survey existing canonical ones;
  pick or adapt; don't invent.
- Letting `work-concept` swallow `pre_drafting_gate`'s 6 gates. The
  gate is a separate verb (the walker delegates to it).
