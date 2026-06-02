# F4 — Decidable Style/Prosody Transforms vs. Judgement Skills

> **Audience:** Gemini Deep Research (or equivalent).
> **Maps to:** Spec 010 §"Deferred to v2" (revision passes) and
> v2 followup design.
> **Deliverable expected from Gemini:** ≤ 4500 tokens cited markdown.

---

## Question

Spec 010 v1 deliberately defers `analyze_prose` and prose-analysis
depth. The v2 plan mentions "the `manuscript-revision` skill" with
four revision passes: structural / line / copy / proof.

For the v2 prose-analysis surface, the doctrine question is the same as
Spec 010 §"The decidable coherence subset" asked for narrative
structure: **which prosodic / rhythm / pacing / style features of
contemporary literary fiction can be characterised as
`transform`s (decidable, no LLM), vs. which inherently require
judgement skills?**

Specifically:

- **Decidable transform candidates** — features computable by AST /
  POS / dependency-parse / vocabulary stats / rule-based pattern
  matching:
  - Sentence-length variance & distribution
  - Adverb / adjective density per POS
  - Passive-voice frequency
  - Dialogue-attribution patterns ("said" frequency vs. alternatives)
  - Repetition (n-gram / word / phrase)
  - Reading-grade-level (Flesch-Kincaid, ARI, SMOG)
  - POV consistency (first/third-person markers within a scene)
  - Tense consistency (within a scene)
  - Cliché / overused-phrase detection (against a fixed list)
- **Judgement-skill candidates** — features requiring interpretation:
  - "Show, don't tell" violations
  - Emotional resonance
  - Character voice consistency across scenes
  - Subtext effectiveness
  - Pacing felt-quality
  - Whether a metaphor lands

What does the **2026 SOTA in computational stylistics** offer for the
decidable-transform candidates?

## Specialists (sources to consult)

| Source kind | Specific targets |
|---|---|
| **Linguistic corpora** | The Project Gutenberg English Corpus, the British National Corpus, the Stanford Literature Corpus, COCA (Corpus of Contemporary American English) — for what "literary fiction" baselines look like statistically |
| **Stylometry tools** | spaCy 3.7+ for POS/dep-parse; TextStat for readability; LIWC-2022 (Linguistic Inquiry and Word Count); Stanford Stylo-R; the Coh-Metrix tool family |
| **Computational stylistics literature** | ACL / EMNLP 2023+ on stylometry; the Digital Humanities Quarterly archives; "Distant Reading" (Moretti 2013) and its successors |
| **Editing software** | ProWritingAid, AutoCrit, Hemingway Editor, Grammarly Premium — what do production tools claim to detect? What's the false-positive rate? |
| **Editor / craft books** | Strunk & White, Stephen King's "On Writing", Roy Peter Clark's "Writing Tools", Ursula K. Le Guin's "Steering the Craft" — for the canonical "rules" that decidable checks would implement |

## Method (verification rules)

- **Each decidable-transform candidate** must be evaluated against
  THREE questions:
  1. **Is a deterministic algorithm published / implementable** for it?
     (Y/N + cite — paper or production tool)
  2. **What's the false-positive rate** the tool / paper reports on
     contemporary literary fiction? (e.g. Hemingway Editor's passive-
     voice detector reports X% FP; ProWritingAid's reports Y%)
  3. **Is the rule context-sensitive in a way that breaks decidability?**
     (e.g. "passive voice is bad" is a heuristic; specifically-bad
     passive constructions may be decidable, but a blanket flag is
     ALWAYS-FAIL on literary fiction with deliberate stylistic
     passive use)
- **Each judgement-skill candidate** must be evaluated for: is there
  an algorithm that approximates it well enough for a TOOL but not
  well enough for an AGENCY transform? (i.e. "Hemingway Editor scores
  readability"; agency rejects readability-as-a-single-number per
  Source-fidelity discipline. Where IS the line?)
- **No SOTA claim** without a 2023+ academic OR production-tool
  citation.

## Output format

```
# Decidable Style/Prosody Transforms — 2026 Computational Stylistics

## 1. The candidate matrix
A table:
| Candidate feature | Decidability verdict | Best-evidence tool/paper | False-positive estimate | Context-sensitivity caveat |
For each of the 9 decidable candidates + the 6 judgement candidates
listed in the question.

## 2. The decidable subset — implementation sketches
For each of the candidates verdict-ed DECIDABLE: a 10–20-line
pseudo-code rule, citing the algorithm source.
(e.g. sentence-length variance: spaCy tokenize → sentence-split →
stdev; threshold > X is "monotonous"; cite the corpus baseline used.)

## 3. The judgement subset — what they belong to
For each judgement candidate: which `manuscript-revision` PASS does
it belong to (structural / line / copy / proof)? What's the shape of
the human gate the skill ends with?

## 4. The gray zone
The decidability-edge cases — features that are decidable for a
class of fiction but break on literary deliberate-rule-breaking.
(e.g. "fragment sentences" — decidable count, but literary fiction
fragments intentionally.) Recommendation: surface as warn-severity
with the rule fingerprint, not fail; let the author dismiss.

## 5. Recommendation for Spec 010 v2 `analyze_prose`
A v2 verb proposal:
  analyze_prose(text: str, axes: list[str] = None) -> dict
where axes is the subset of decidable transforms the user wants.
Default axes = the 5 most-defensible from §2. Returns findings in the
SAME shape as Spec 034 analyze's Finding type (rule / severity /
message / evidence).

## 6. Tools-vs-transforms boundary
Why ProWritingAid and Hemingway Editor SHIP these checks but the
agency `analyze_prose` should ship a smaller subset: the agency
discipline rejects context-blind heuristics. Document the line.

## 7. Cited bibliography
≥ 12 entries, 2023+ where possible.
```

## Acceptance

- [ ] Each candidate has a verdict with cited evidence.
- [ ] §2 produces pseudo-code that would pass a Spec 010-style review.
- [ ] §5 names ≤ 5 default axes — over-eager defaults are anti-pattern.
- [ ] §4 names ≥ 3 specific gray-zone features with a recommended
  policy (warn-not-fail).
- [ ] §6 states the doctrinal boundary explicitly.

## How to feed into Spec 010

- §2 → directly seeds the v2 `analyze_prose` transform implementation.
- §3 → the four revision-pass skills (structural / line / copy / proof)
  get their phase contents.
- §5 → the v2 verb proposal goes into Spec 010 §"Deferred to v2" as
  the concrete v2 surface (replacing the current handwave).
- §6 → adds a paragraph to Spec 010 §"Source fidelity" justifying the
  axis cut against the production-tool baseline.

## Anti-patterns (Gemini should avoid these)

- Recommending features like "sentence variety" as a single score.
  Agency's discipline demands rule-level findings, not aggregate
  scores.
- Citing Hemingway Editor's rules without the false-positive rate on
  literary fiction. Literary fiction breaks rules deliberately; FP
  rate matters.
- Recommending ML-based stylometry (e.g. BERT-fine-tuned). That's
  judgement-with-extra-steps; transforms must be decidable.
- Defaulting to the full 9-feature axis set in §5. The agency surface
  is small; default-small is the doctrine.
- Citing readability scores without acknowledging their well-documented
  bias against literary prose (Flesch-Kincaid flags Hemingway as
  too-simple, Faulkner as too-hard — neither is wrong).
