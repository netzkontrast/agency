# F1 — Narrative-Structural Validation: 2026 SOTA Survey

> **Audience:** Gemini Deep Research (or equivalent).
> **Maps to:** Spec 010 §"Source fidelity §3" (NCP draft-07 placement
> in the field) and Loop 2 (`ncp_validate` implementation choice).
> **Deliverable expected from Gemini:** ≤ 5000 tokens cited markdown.

---

## Question

What is the canonical state-of-the-art for **narrative-structural
validation** as of 2026, and where does Dramatica's **NCP draft-07
schema** (`{schema_version, story{…narratives{subtext, storytelling}…}}`)
sit relative to its peers?

Specifically, compare NCP against:

1. **Save-the-Cat beat-sheet validation** — Blake Snyder's 15-beat
   structure; any computational implementations (validation tools,
   plugins for Scrivener / Final Draft).
2. **Story-Engine-style state machines** — Hartwell-Bell or similar
   narrative-state-machine formalisms; the BBC R&D StoryFormer
   project; any productionised authoring-engine schemas.
3. **Academic narrative schemas** — LRA (Latent Representation of
   Affect), Story-Generator (CMU / MIT Media Lab), Narrative-Schema
   work from Jurafsky et al., the OntoStory ontology family.
4. **Game-narrative formalisms** — INK (Inkle), Yarn Spinner, ChoiceScript,
   Twine — any of these that ship a validatable graph schema.

The point of the survey is **not** to recommend swapping NCP. It's to
**place NCP honestly** in the 2026 field, so the Spec 010 implementation
of `ncp_validate` can defend its choice against the question "why this
schema, not X?".

## Specialists (sources to consult)

| Source kind | Specific targets |
|---|---|
| **Academic literature** | ACL, EMNLP, COLING proceedings 2022–2025 on narrative representation; NarrativeQA-related datasets; the NarrativeOntology paper family |
| **Industry tools** | Dramatica.com 2020+; STORY-Engine BBC R&D; Inkle's INK schema; Yarn Spinner; Articy:Draft 3 export schemas |
| **Open-source repos** | github.com search for "narrative schema", "story validation", "beat sheet validator" — find live code, not just papers |
| **Authoring-software ecosystem** | Scrivener plugins; Final Draft custom data; World Anvil; Campfire Blaze — any of these exposing structured story data |
| **Web archive** | Web archive snapshots of dramatica.com for the schema's version history (the draft-07 vintage matters) |

## Method (verification rules)

- **No claim about NCP** is accepted without citing the actual JSON
  schema text (the `state/schema/ncp.schema.json` file in the source
  repo, or its public mirror).
- **No claim about a comparator schema** is accepted without a link to
  the schema definition (not a blog post about it).
- **Industry-vs-academic distinction matters**: a peer-reviewed paper
  and a Medium blog post are not equal evidence.
- **2026-recency**: any source older than 2022 must be supplemented with
  a 2024+ source confirming the comparator is still maintained / in use.
  Dead schemas (last-updated-2017 Twine forks, etc.) count as historical
  context, not SOTA.

## Output format

```
# Narrative-Structural Validation — 2026 SOTA Survey

## 1. The four families
For each of {Dramatica/NCP, Save-the-Cat-computational, Story-Engine-SMs,
academic-schemas, game-narrative}: a 2–3 paragraph summary covering
shape, validation-discipline (what does "valid" mean for them?),
maintenance state, and the canonical schema/source.

## 2. NCP draft-07 in the field
Where does NCP sit? Strengths it shares with comparators; weaknesses it
shares; unique stances (the {subtext, storytelling} bisection is unusual
— is it?).

## 3. The validation-style spectrum
A spectrum chart: at one end "syntactic-only" (does this JSON parse?),
at the other end "semantic-with-narrative-theory" (does this story have
a coherent throughline?). Where do all five families sit?

## 4. Implementation choices for agency
For the agency Spec 010 implementation of `ncp_validate`, what does this
survey suggest about:
- (a) the right verifier strictness for v1 (Schema-conformance only?
  Schema + cross-reference checks like F2's quad-reverse-index?
  Heuristic narrative-coherence?)
- (b) whether to surface NCP-specific terminology in error messages,
  or normalise to schema-agnostic shapes
- (c) which comparators to mention in the verb's docstring as
  alternatives

## 5. Cited bibliography
Numbered list, ≥ 15 entries, each with a 2026-recency note
(last-updated date) and one-line relevance.
```

## Acceptance

- [ ] Every claim is sourced; numbered citations match the bibliography.
- [ ] At least 3 of the 4 comparator families have a *live* (2024+)
  schema link, not just a paper.
- [ ] NCP's placement is defended against ≥ 2 explicit critiques (e.g.
  "the subtext/storytelling split is over-engineered for v1" or "the
  storybeat references are an under-specified foreign-key system" —
  whatever the survey actually surfaces).
- [ ] §4 (Implementation choices) gives a CONCRETE recommendation for
  Spec 010 Loop 2, not handwaving.
- [ ] Cited Dramatica.com page is from 2024+ (or web-archive timestamp).

## How to feed into Spec 010

- §1+§2 → Spec 010 §"Source fidelity §3" gets a new paragraph
  documenting where NCP sits relative to the 2026 SOTA. Citations get
  appended to §"Evidence".
- §4(a) → directly chooses the implementation strictness for the
  `ncp_validate` transform in Loop 2.
- §4(b) → informs the error-message wording in the verb (Spec 010's
  Wiegers/Nygard error contract — name the schema, not the implementation).
- §4(c) → goes into the `ncp_validate` verb's docstring's `Returns:`
  slice as a "see also" pointer for callers wanting an alternative.

## Anti-patterns (Gemini should avoid these)

- Citing dramatica.com without checking the schema version actually
  shipped in the source repo (draft-07; the public-facing site may have
  moved on).
- Treating Save-the-Cat as a schema — it's a beat sheet; the schema is
  the computational validator someone built FOR it.
- Surveying narrative-generation (LLM creative writing) instead of
  narrative-validation. Generation is a different problem.
- Including more than 5000 tokens of output. Be terse; cite, don't
  paraphrase.
