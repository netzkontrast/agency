<!-- agency steward handover — read this first next run -->
# Steward Handover 001 — 2026-06-19

## What shipped this run
**Spec 330 follow-up: wire the dormant typed read API into `manage`.**

Added two read verbs to the `manage` capability
(`agency/capabilities/manage/_main.py`):
- `manage.provenance(for_intent_id)` → consumes `IntentStore.provenance`
  (which internally calls `serves`): the typed cross-concern join
  (invocations + agents + artefacts + lifecycle) as one query set.
- `manage.subtree(root_intent_id)` → consumes `IntentStore.intent_tree`:
  the `PARENT_INTENT` sub-intent tree over the typed `parent_intent_id` FK.

**Why (the impact ranking):** a dormant-surface audit (CLAUDE.md field-tested
heuristic #1) on the freshly-shipped Spec 326–330 typed-entity program found
that `IntentStore.serves` / `provenance` / `intent_tree` had a **parity-gate
acceptance test but ZERO production reader** — only `fulfilment` was wired (into
`manage.state`). Spec 330's own followup had named this re-route as the deferred
follow-up. Reach: completes the Memory+Intent pillar **read** side; reclaims 3 of
4 dormant typed methods; the natural Goal-5 FastAPI endpoint shape — all additive,
behaviour-preserving, no ontology change.

## Evidence
- RED→GREEN: 2 new scenarios in `tests/acceptance/features/typed_read_api.feature`
  + step defs in `test_typed_read_api.py`. `pytest tests/acceptance/test_typed_read_api.py`
  → **7 passed** (was 5).
- Invariant slice (`-k "naming or install or manage or typed_read or drift or surface"`)
  → **61 passed**.
- `scripts/check-drift` → clean after install regen (the two verbs added to the
  wire surface: `skills/{help,manage}/SKILL.md`, `bin/agency-manage-{provenance,subtree}`,
  `skills/manage/references/{provenance,subtree}.md` regenerated).
- TODO.md row updated (typed-entities program); Spec 330 followup appended.
- Reflection `reflection:e0ef9cc7` + dogfood observation `reflection:95898011` recorded.

## Deferred runner-up (architecturally significant — for a human, not a steward guess)
**The FastAPI read surface (Goal 5/7).** `IntentStore`'s dict returns + these
`manage` verbs are the read models. Building the server is a new long-running
surface / new entrypoint — open a human-reviewed spec rather than guess it in a
scheduled run. (Rail: architecturally-significant top candidate → handover.)

## Next 3 candidates (ranked)
1. **FastAPI read surface (Goal 5/7)** — the capstone the whole typed-entity
   program points at; needs a human-reviewed spec for the server boundary,
   auth, and lifecycle. Highest reach, but needs a decision.
2. **schema_coverage at 21%** (doctor: 19/89 labels covered; Spec 153 Slice 6).
   Many newly-typed labels (Intent/Agent/Invocation/Gate/AcceptanceCriterion/
   Artefact) have no template/schema for the Document convergence. Bounded,
   testable (coverage fraction rises). Caveat: "highest-traffic" ranking is
   degenerate on a fresh graph (node counts all 0) — pick by label centrality
   instead.
3. **codes_coverage orphans** (doctor: 12 orphan `Codes` members defined but
   unused — e.g. `AMENDMENT_*`, `PHASE_*`, `SKILL_PARSE_INVALID`). Dormant enum
   surface; Spec 151. Low-risk cleanup, low impact — good filler slice.

## Proposed amendment (dogfood)
When a read API ships behind a parity gate, the SAME slice should wire ≥1
**production** reader per method — else the dormant-surface heuristic flags it
next audit (as happened here). Candidate addition to CLAUDE.md heuristic #1 /
the "Dormant-surface audit" bullet.

## Pillar gate (held)
Intent · Capability · Lifecycle · Memory each own write+read; the typed read
methods are now all load-bearing (no dormant surface); Document convergence
untouched (no ontology/schema change this run). Drift + suite green.
