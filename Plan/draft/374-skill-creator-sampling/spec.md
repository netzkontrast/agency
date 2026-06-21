---
spec_id: "374"
slug: skill-creator-sampling
status: draft
state: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [1, 3, 8]
depends_on: ["147", "371", "373"]
parent_spec: "370"
domain: skills
---

# Spec 374 — The skill-creator (authoring-time MCP sampling)

> Child 4 of Spec 370. The "optimized content, not docstring extracts" engine: an
> AUTHORING-TIME generator that samples the host LLM with per-type skill-creator
> prompts, grounded in the capability's code + spec(s), to fill the committed
> schema (371). Reviewed, then committed (A7). NOT an install-time step.

## Why
Templated derivation is capped by docstring quality. To get genuinely good skills,
an LLM must write the judgment content — but doing so at install breaks
reproducibility (A7). So it runs at authoring time and its reviewed output is
committed; install just renders it (373).

## Design (sketch)
- **`skill.author(cap, type=…)` / `skill.regenerate(cap)`** (new cluster, likely on
  the existing `skill_generator` capability — extend, don't duplicate): builds the
  **grounding context** (verbs + signatures + docstrings + the capability's governing
  `Plan/NNN` spec(s) + ontology nodes/edges) and the **per-type skill-creator prompt**
  (the R1–A7 rules as the system prompt) → calls `host.sample` (the Spec 147 Driver
  seam, surfaced as MCP sampling) → parses the result into the `Skill`/`Phase` schema.
- **Validation (anti-hallucination, F3):** every verb the draft references MUST exist
  in the live registry; the draft MUST satisfy the type schema (371) + R1/R3/R4
  checks; failures → re-sample or surface for hand-fix. Never commit an invalid skill.
- **Stamp:** record `source_stamp = hash(cap code + spec + prompt-version)` on the
  committed skill (feeds the 377 staleness gate).
- **Review gate:** the verb returns the draft for the developer to review/edit before
  it is written to `skill.yaml` (Anthropic's Agent-A→review loop). `dry_run` default.
- **Degrades gracefully:** no host LLM ⇒ the verb returns the grounding + the prompt
  so a human (or another agent) can author by hand; the deterministic template
  fallback (373) still yields a valid minimal skill.

## Slices (TDD)
1. The grounding-context builder (code + spec + ontology → a structured prompt input).
2. The per-type skill-creator prompts + the `host.sample` call (Driver-seam, stubbed
   in tests) → schema-parsed draft.
3. Registry + schema validation of the draft; the `source_stamp`; the review/commit path.

## Acceptance
- `skill.author(cap)` with a stub Driver returns a schema-valid draft grounded in the
  cap's real verbs (a verb not in the registry is rejected).
- The draft carries a `source_stamp`; re-running with unchanged source is stable.
- No host ⇒ graceful return (grounding + prompt), no crash, deterministic fallback intact.
- Install never calls the sampler (a test asserts `install.generate` does no sampling).
