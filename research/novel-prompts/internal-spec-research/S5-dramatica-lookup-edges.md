# F5 — `dramatica_lookup` Edge Cases Beyond Reciprocity

> **Audience:** Gemini Deep Research (or equivalent).
> **Maps to:** Spec 010 Loop 1 (`dramatica_lookup` transform) — the
> FIRST loop, blocked on this answer for completeness.
> **Deliverable expected from Gemini:** ≤ 4000 tokens cited markdown.

---

## Question

The `dramatica_lookup` transform is the cleanest port from the source
the-agency-system shipped code (the `navigator` module:
`by_id`, `by_class`, `by_type`, `by_variation`, `by_element`,
`by_dynamic_pair`, `check_dynamic_pair_reciprocity`).

The shipped navigator handles reciprocity faithfully. But Dramatica's
data model has **other relational structures** beyond dynamic-pair
reciprocity that a fuller `dramatica_lookup` could query:

1. **Quad consistency** — quads are 4-element groups
   (Knowledge–Thought–Ability–Desire, etc.) with rotation and
   neighbour relationships. Is the navigator missing a `by_quad` /
   `check_quad_consistency` method?
2. **Archetype ↔ element pairing** — Dramatica's 8 archetypes
   (Protagonist, Antagonist, Guardian, Contagonist, Reason, Emotion,
   Sidekick, Skeptic) each map to a Motivation-Quad position. Is this
   pairing in the bundled data? Decidable?
3. **Throughline ↔ class membership** — each throughline (MC, IC, OS,
   RS) maps to a Dramatica class (Universe / Physics / Mind /
   Psychology). The mapping has rules. Lookup helpers?
4. **Concern ↔ type narrowing** — concerns are sub-types within
   throughline class. Navigation helpers for "given an MC throughline,
   what concerns are valid?"
5. **Plot-dynamic propagation** — Resolve / Growth / Approach /
   Mental-Sex are plot-dynamics that propagate constraints across
   throughlines. Does any structural rule fall out as a transform?
6. **Storypoint ↔ signpost ↔ moment chain** — the NCP draft-07 schema
   has storybeat→moment refs (Spec 010 §F2 lists `storybeat_moment_refs`
   as decidable); is there a similar lookup-side helper?

For each of the 6 candidate edges, what should the v1 (or v1.5)
`dramatica_lookup` shape be?

## Specialists (sources to consult)

| Source kind | Specific targets |
|---|---|
| **Source-shipped code** | the-agency-system @ 0a6a9e71 — `servers/agency-mcp/src/agency_mcp/lib/dramatica/navigator.py` (the v1 port reference); also the bundled `reference/novel/dramatica/ontology.json` to inspect the data shape directly |
| **Dramatica.com canonical** | The Dramatica theory pages (2020+): "Quads", "Archetypes", "Throughlines", "Classes", "Concerns", "Resolve/Growth/Approach", "Mental Sex". Each has structured definitions usable for rule formalisation |
| **Dramatica Pro user docs** | If available — the Dramatica desktop software's help docs document the cross-throughline constraints the engine enforces; those are the runtime rules we'd want as transforms |
| **Spec 010 itself** | §"Source fidelity §1–§2, §6, §7" — three of those source-fidelity facts directly bear on F5's question (303 entries, 65 dynamic-pair kinds, navigator port faithfulness) |
| **Web archive of Dramatica.com** | Some pages have moved or rephrased over time; web-archive for the 2020-vintage canonical definitions |

## Method (verification rules)

- **For each of the 6 candidate edges**:
  1. **Is the data IN the bundled 303-entry ontology**? Cite the entry
     kinds it would draw from (e.g. quad-consistency uses entries of
     kind `quad` (35) + `element` (63) + the implicit positional
     index).
  2. **Is the rule decidable** from that data alone (no LLM, no prose
     interpretation, no external Dramatica-Pro state)?
  3. **What's the navigator method signature** that would expose it?
     (Match the v1 navigator style: `by_<thing>(<id_or_query>) -> dict`.)
  4. **Is this v1 or v1.5?** v1 = port faithfulness (matches the
     shipped navigator); v1.5 = additive helpers (decidable extensions
     the shipped navigator omits but the bundled data supports).
- **No claim** without citing the bundled ontology JSON structure
  (peek at it directly — Spec 010 measured it as 303 entries with 11
  kinds; that's the ground truth, not the source Plan-012 spec).

## Output format

```
# `dramatica_lookup` Edge Cases — v1 vs. v1.5 Surface

## 1. The bundled-data inventory
A short table: 11 kinds × measured count × what relationships are
encoded (explicitly via fields, implicitly via dynamic-pair-id or
quad-membership). This anchors what's decidable from the bundled data.

## 2. The 6 candidate edges — verdict per edge
For each of {quad_consistency, archetype_element_pairing,
throughline_class_membership, concern_type_narrowing,
plot_dynamic_propagation, storybeat_chain}:

### <edge name>
- **Bundled-data evidence**: kinds + fields used (Y/N decidable)
- **Decidability verdict**: DECIDABLE-v1.5 | DECIDABLE-but-stretches-
  navigator-shape | NOT-DECIDABLE-bundled-data-insufficient
- **Proposed method signature** (matches `by_id`-style if DECIDABLE):
  `def by_<edge>(self, …) -> dict: …`
- **Test fixture** (one concrete query → expected result, sourced
  from the bundled data — not invented)

## 3. v1 (port-faithful) navigator surface
Lock the v1 to the 7 shipped methods. List any candidate that ALMOST
made v1 but should wait for v1.5 (rationale: scope discipline, not
ability).

## 4. v1.5 (additive helpers) navigator surface
The DECIDABLE-v1.5 candidates from §2 become a v1.5 PR addendum.
Order them by leverage (how many other transforms could call this
helper) × implementation cost.

## 5. NOT-DECIDABLE recommendations
For each NOT-DECIDABLE-bundled-data-insufficient candidate: what
ontology augmentation WOULD unblock it? (Cross-reference F2 for the
quad-reverse-index work.)

## 6. Cited bibliography
Dramatica.com URLs + source-repo navigator line numbers.
```

## Acceptance

- [ ] Every verdict cites the bundled ontology JSON's actual structure.
- [ ] §3 doesn't expand v1 beyond the 7 shipped methods (port
  discipline).
- [ ] §4 names the v1.5 additions in priority order with rationale.
- [ ] At least one candidate has a concrete test-fixture query
  (deterministic, replayable) sourced from the bundled data.
- [ ] §5 cross-references F2 where the answers overlap.

## How to feed into Spec 010

- §3 → directly locks Spec 010 Loop 1's `dramatica_lookup` v1 method
  list. The seven `by_*` + `check_dynamic_pair_reciprocity` from the
  shipped navigator stay; nothing else added in v1.
- §4 → becomes a v1.5 PR for Loop 1 (a separate small additive PR
  after the v1 port lands). Each v1.5 method gets its own test.
- §5 → augments Spec 010 §"Dramatica + NCP libraries" with the
  v2-ontology-augmentation list. Cross-references F2's reverse-index
  work.
- §2's test fixtures → directly into
  `tests/test_novel_capability.py` parametric tests.

## Anti-patterns (Gemini should avoid these)

- Recommending v1 expansion beyond the shipped 7 methods. Port
  faithfulness is the discipline.
- Inventing data that isn't in the bundled ontology JSON. The 303
  entries are the truth; if a relationship isn't encoded there, the
  answer is "needs ontology augmentation", not "implement it anyway".
- Treating Dramatica Pro's runtime state as available. Only the
  BUNDLED data is queryable; Dramatica-Pro proprietary state isn't.
- Designing a "smart" navigator that infers relationships not in the
  data. Decidable means deterministic from the bundled JSON. No
  inference.
- Recommending edges F2 also covers. Where overlap exists, defer to
  F2 and reference it; don't duplicate the analysis.
