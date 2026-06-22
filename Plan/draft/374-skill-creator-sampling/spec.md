---
spec_id: "374"
slug: skill-creator-sampling
status: partial
state: draft
last_updated: 2026-06-22
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

## Followup — Implementation Status (2026-06-22)

**Slice 1 — SHIPPED: the grounding-context builder.** Slices 2 (host.sample +
per-type prompts) and 3 (validation + source_stamp + review/commit) remain.

Done (file:line evidence):
- `agency/capabilities/skill_generator/_main.py` — `build_grounding(cap, spec_text="")`
  reads a capability's LIVE surface into a structured dict: `{capability, home,
  verbs:[{name, role, signature, doc}], ontology:{nodes, edges, skills}, spec}`.
  Pure + deterministic (registry-only, no host, no I/O) — same cap ⇒ same bytes
  (A7). Verb signatures strip `self`/`ctx`/declared `@verb(inject=…)` params via
  `_public_signature` (derived from the live `fn`, rule 2); docstrings carried in
  FULL (rule 9). Surfaced as the `skill_generator.ground(capability, spec_text=)`
  verb (role=transform) — the no-host fallback an author reads by hand (acceptance
  "no host ⇒ graceful return"); unknown capability → typed `{error, available}`.
- Tests: `tests/acceptance/features/skill_author.feature` + `test_skill_author.py`
  — 3 scenarios: (1) grounding lists EXACTLY the live verbs, each mirroring live
  role + docstring, signature omitting injected params; (2) determinism (same cap,
  identical bytes); (3) unknown cap → typed error. All derive from the live
  registry (rule 8). 3/3 green; install regen committed (help + skill-generator
  surface gained the `ground` verb); `check-drift` clean.

Still:
- **Slice 2** — per-type skill-creator prompts (R1–A7 as the system prompt) +
  the `ctx.host.sample` call (the Spec 147/285 seam; stubbed in tests) → parse the
  completion into the `Skill`/`Phase` schema (371). Graceful pause when no host.
- **Slice 3** — registry + type-schema validation of the draft (a referenced verb
  not in the live registry is rejected); `source_stamp = hash(cap code + spec +
  prompt-version)`; the `dry_run` review/commit path. Plus the guard test that
  `install.generate` never samples (deterministic install, A7).
