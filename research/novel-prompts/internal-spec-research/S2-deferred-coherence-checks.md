# F2 — Reviving the Deferred Coherence Checks

> **Audience:** Gemini Deep Research (or equivalent).
> **Maps to:** Spec 010 §"Open Question 7" (which deferred checks can
> become genuinely decidable transforms?) and Loop 4 (`coherence_check`)
> v2 followup.
> **Deliverable expected from Gemini:** ≤ 4000 tokens cited markdown.

---

## Question

Spec 010 §"The decidable coherence subset" identifies **11 coherence
checks** in the source shipped code, of which only **6 ship as
genuine `transform`s in v1** (decidable from the bundled 303-entry
Dramatica ontology):

1. `dynamic_pair_reciprocity` ✓
2. `storybeat_moment_refs` ✓
3. `throughline_partition` ✓
4. `slot_fill` ✓
5. `ktad_coverage` ✓ (conditional — needs quad reverse-index)
6. `quad_completeness` ✓ (conditional — needs quad reverse-index)

The remaining **5 are deferred** as "needs-judgement → skill / v2":

7. `signpost_permutation`
8. `resolve_mirror`
9. `mental_sex_problem_solving`
10. `crucial_element_placement`
11. `approach_concern`

Plus the **Q1–Q5 scene-bridge judgement** (5 sub-checks under one rubric).

The shipped source repo (the-agency-system @ 0a6a9e71) implements all
11 — but mostly as **fixture-discriminating heuristics** (e.g.
`check_ktad_coverage` hard-codes `if concern_id == "t.progress": FAIL`).

**Which of the 5 deferred checks can be REBUILT as genuinely-decidable
transforms** if the bundled ontology is augmented with the right
reverse-indexes?

## Specialists (sources to consult)

| Source kind | Specific targets |
|---|---|
| **Source repo code** | the-agency-system @ 0a6a9e71 — `servers/agency-mcp/src/agency_mcp/handlers/novel/coherence.py`, `structure.py`, plus the data file `reference/novel/dramatica/ontology.json` |
| **Dramatica theory docs** | Dramatica.com 2020+ on signposts, resolution-judgement-outcome, mental-sex-problem-solving (search "Dramatica MC Resolve Outcome Judgment"), crucial-element-placement (the "Crucial Element" page), approach-concern (the "Approach" page) |
| **The shipped ontology JSON** | Count what's actually in it (kinds: class, type, variation, element, dynamic-pair, quad, concept, archetype, throughline, character-dynamic, plot-dynamic); identify the reverse-indexes that could be derived (quad↔element, signpost-permutation table, etc.) |
| **Narrative-theory academic** | If any 2020+ paper on Dramatica formalisation exists (search Google Scholar) — Dramatica is mostly self-published; academic engagement is sparse but check |

## Method (verification rules)

- **Each of the 5 deferred checks** must be evaluated against THREE
  questions:
  1. **Is the check definable** purely from the bundled 303-entry
     ontology + a derivable reverse-index? (Y/N + which index)
  2. **Does the shipped code's failure mode** suggest the heuristic IS
     the rule, or the heuristic is a placeholder for an unimplemented
     rule? (Read the actual code — the source-fidelity note in Spec
     010 §7 lists examples)
  3. **What would a CORRECT decidable implementation look like?** In
     pseudo-code, sourced from the Dramatica.com canonical definition
     (link it).
- **No claim accepted without** (a) a Dramatica.com URL for the canonical
  definition, AND (b) the corresponding shipped-code path that
  implements the heuristic.
- **Heuristic ≠ decidable.** If the rule can only be checked with
  arbitrary thresholds OR requires interpreting prose, it's not
  decidable. Be honest about which is which.

## Output format

```
# Reviving the Deferred Coherence Checks

## 1. The bundled ontology — what's actually in it
A short table: 11 kinds × measured count (303 total). Identify the
THREE non-obvious reverse-indexes that can be derived deterministically
from this data:
  (a) quad-reverse-index (element → quad)
  (b) signpost-permutation-table (valid orderings)
  (c) crucial-element-domain-map (which throughline owns which elements)

## 2. The 5 deferred checks — verdict per check
For each of {signpost_permutation, resolve_mirror, mental_sex_problem_
solving, crucial_element_placement, approach_concern}:

### <check name>
- **Canonical Dramatica definition** (link + 2-line summary)
- **Shipped heuristic** (file:line + verbatim of the hardcode)
- **Decidability verdict**: DECIDABLE-with-<index> | HEURISTIC-INHERENTLY |
  PROSE-JUDGEMENT-INHERENTLY
- **If decidable**: the rule in pseudo-code (≤ 20 lines)
- **If heuristic**: why no amount of ontology augmentation saves it
- **If prose-judgement**: which skill it BELONGS as (conceptualizer?
  revision-pass?) and what the skill's hard-gate output looks like

## 3. The Q1–Q5 scene-bridge judgement
Q1–Q5 are five sub-checks under one rubric. Are they five separate
deferred items, or one item with five facets? Recommend the v2
implementation shape (one verb `scene_bridge_judgement` returning a
5-tuple report? Five separate `transform`s?).

## 4. Recommendation for Spec 010 v2 followup
A prioritized list: which of the 5 deferred checks should v2 attempt
first, in what order, and what ontology-augmentation work would unblock
the most? Estimate per-check implementation cost (low/medium/high).

## 5. Cited bibliography
Numbered list with the Dramatica.com URLs + the source-repo line
numbers.
```

## Acceptance

- [ ] Every verdict cites the canonical Dramatica.com page AND the
  shipped-source-line.
- [ ] Each DECIDABLE-with-<index> verdict carries a concrete pseudo-code
  rule that someone could implement.
- [ ] HEURISTIC-INHERENTLY verdicts are defended with a specific
  ontology-completeness gap, not just "this seems hard".
- [ ] §4 ranks the 5 by implementation-cost; the highest-leverage v2
  candidate is named.
- [ ] §3's Q1–Q5 recommendation has a concrete v2 shape.

## How to feed into Spec 010

- §1 → augments Spec 010 §"Dramatica + NCP libraries" with the
  reverse-index plan. Indexes that the v2 `coherence_check` extension
  would compute at startup.
- §2 → directly resolves Spec 010 Open Question 7: which deferred
  checks come back as `transform`s, which stay as v2 judgement skills.
- §3 → informs Spec 010 §"Migration / coverage map" row "021 10
  prompt-builders" (the scene-bridge judgement IS a prompt-builder
  candidate).
- §4 → becomes the v2 implementation order for Spec 010 followup.

## Anti-patterns (Gemini should avoid these)

- Treating Dramatica's prose theory as decidable. The point is which
  parts SURVIVE the decidability test.
- Inventing rules that aren't in the canonical Dramatica.com docs. If
  the SOTA Dramatica doesn't define `mental_sex_problem_solving`
  precisely, we don't get to invent a precise rule.
- Recommending "use an LLM" for the heuristic checks. The whole point
  of the decidable subset is to AVOID LLM judgement; the alternative
  is a SKILL with a hard human gate, not an LLM call.
- Citing the source repo's heuristic implementation as the canonical
  rule. The source repo itself acknowledges these are stubs (Spec 010
  §7).
