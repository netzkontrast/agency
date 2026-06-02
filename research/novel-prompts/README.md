# Novel-Capability — Gemini Deep-Research Prompts

These five prompts (F1–F5) inform the implementation of **Spec 010 — Novel Domain Capability**. Each is a self-contained brief you can paste into Gemini's Deep Research (or any comparable research tool) and consume the answer as input to a Spec 010 implementation loop.

> **Why these five?** The Spec 010 spec is grounded in the *shipped*
> the-agency-system code, not its source-Plan specs (which it deviates
> from in three documented places). Five questions remain genuinely
> open or worth verifying against the 2026 SOTA before we lock down the
> v1 surface. These prompts make those questions explicit and bounded.

## The five prompts

| File | Question (one-line) | Maps to Spec 010 § | Loop blocked |
|---|---|---|---|
| [`F1-narrative-validation-sota.md`](F1-narrative-validation-sota.md) | What's the canonical 2026 SOTA for narrative-structural validation? | Source fidelity §3 (NCP draft-07) | Loop 2 (`ncp_validate`) |
| [`F2-deferred-coherence-checks.md`](F2-deferred-coherence-checks.md) | Which of the 11 deferred coherence checks can be made genuinely decidable? | Open Question 7 | Loop 4 (`coherence_check`) — v2 followup |
| [`F3-walker-phase-order.md`](F3-walker-phase-order.md) | What's the optimal phase order for the `work-concept` skill walker? | Skills §`work-concept` | Loop 6 (the conceptualizer skill) |
| [`F4-decidable-style-transforms.md`](F4-decidable-style-transforms.md) | Which prosodic/style features survive as `transform`s (no LLM judgement)? | Deferred §revision passes | v2 — but informs v1 surface design |
| [`F5-dramatica-lookup-edges.md`](F5-dramatica-lookup-edges.md) | How should `dramatica_lookup` handle edge cases beyond reciprocity? | `dramatica_lookup` verb | Loop 1 (the first transform) — most urgent |

## How to use them

1. **Pick the prompt** that maps to the loop you're about to start.
2. **Copy-paste** the prompt body into Gemini Deep Research (or comparable). The prompt is self-contained — it carries its own source list, scope, and output requirements.
3. **Review the returned report** against the per-prompt `## Acceptance` section. If it passes, use it as input to the matching Spec 010 loop. If not, refine and re-run.
4. **Save the verified report** to `research/novel-prompts/responses/F<n>-response.md` and link it from the matching Spec 010 loop section.

## Why this format and not a `research.lead` call?

The `research` capability (Spec 036) ships a graph-native version of exactly this pattern (lead + specialists + verifier). When that capability lands, these prompts become **valid inputs** to it — the prompt body translates directly into `research.lead(question=…, depth="deep")`. Until then, the prompts are usable standalone via Gemini's Deep Research, with the user playing the verifier role manually.

The five prompts share a structure that mirrors `research`'s output contract:

```
## Question
## Specialists (sources to consult)
## Method (verification rules)
## Output format
## Acceptance (how to verify the answer is trustable)
## How to feed into Spec 010
```

This structural identity is deliberate — when the agency `research` capability is implemented, these prompts roundtrip without rewriting.

## What's deliberately out of scope here

- **Generative prompt-builders** (Plan 021 in the source repo) — those are v2.
- **Prose-analysis depth** — Spec 010 v1 scope cut excludes this; F4 surveys the literature but doesn't ask for an implementation.
- **Agentic layer** (source repo Plan 016) — separate spec, not Novel-domain.
- **Schema generation** — `ncp_validate` consumes the bundled draft-07 schema; we don't ask Gemini to design a new one.

## Source-fidelity discipline (applies to every prompt)

Every Gemini response MUST be evaluated against the SHIPPED code, not aspirational specs. Spec 010 §"Source fidelity" lists three documented places where the source repo's Plan specs claim things the shipped code never honoured (303 not 304 ontology entries; ≈54 not 75 reciprocal pairs; draft-07 not 2020-12 NCP). If a Gemini response cites a spec but doesn't verify against the shipped artefact, it fails acceptance.
