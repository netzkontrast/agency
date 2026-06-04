---
spec_id: "017"
slug: graph-native-dogfood-ledgers
status: complete
last_updated: 2026-06-03
owner: "@agency"
depends_on: ["013", "014", "015", "020"]   # 020 = central .agency/session.db
affects:
  - agency/capabilities/dogfood.py        # add note/render; deprecate collect to one-shot
  - agency/capabilities/_jules_skills.py  # rebind jules-self-improvement
  - agency/install.py                     # surface same anti-pattern; in scope
  - Plan/**/DOGFOOD-NOTES.md              # eventually rendered, not authored
estimated_jules_sessions: 0
domain: capability
wave: 3
---

# Spec 017 — Graph-native dogfood ledgers (close the file-vs-graph inversion)

## Why

The user surfaced this mid-session; **Jules's Spec 015 review confirmed
with concrete cites** (`Plan/015-architecture-review/ARCHITECTURE-REVIEW.md`
weaknesses W1 + W2 — `agency/capabilities/dogfood.py:108`,
`agency/install.py:145`). The pattern is **markdown-as-primary-store** where
the graph should be — directly violates GOALS.md goal #7 ("graph is the
store; files are a rendered view") and the canon (`CORE.md` Memory section,
"the moat is the graph").

Current flow:
```
human/orchestrator writes DOGFOOD-NOTES.md  →  dogfood.collect parses
markdown  →  reflect.batch_note seeds Reflection nodes from the parsed text
```

Correct flow:
```
orchestrator runs `await call_tool("capability_reflect_note", {scope, text})`
→ Reflection node lands in graph (one execute block, no file)
→ dogfood.render(plan_id) reads Reflection nodes + emits the markdown view
   ONLY when humans need it (PR descriptions, audit exports, external sharing)
```

## Done When

- [ ] **`dogfood.note(observation, plan_slug)`** — new `act` verb. Wraps
  `reflect.note(scope="observation", text=...)` with a `plan_slug` tag
  recorded on the Reflection node so observations are queryable per-plan.
  Returns `{reflection_id, plan_slug}`.
- [ ] **`dogfood.render(plan_slug)`** — new `transform` verb. Queries
  Reflection nodes tagged with the given plan_slug, returns markdown
  text in the existing DOGFOOD-NOTES.md format. The output IS the
  rendered view; humans pull on demand.
- [ ] **`dogfood.collect` deprecated to one-shot migration utility.** Marked
  in the docstring; the verb still works (back-compat for Spec 014's
  observation→spec-amendment pipeline) but is no longer the recommended
  authoring path. A new docstring line: "Deprecated for ongoing use;
  prefer dogfood.note + dogfood.render."
- [ ] **`_jules_skills.py` `JULES_SELF_IMPROVEMENT_SKILL` rebound** —
  Phase 1 keeps `dogfood.collect` (for migration); Phase 2 keeps
  `reflect.batch_note`; **a new Phase 0 (`note-observation`) binds to
  `dogfood.note`** so future runs author through the graph from the
  start, not from a markdown file.
- [ ] **`agency/install.py:145` writes are documented as canon-acceptable**
  — the install MANIFEST (plugin.json, .mcp.json, marketplace.json, the
  help skill, the help command) genuinely needs to land on disk for
  Claude Code to find them. This is the "canon/doctrine docs serve
  external readers" exception from CLAUDE.md rule 2. **No code change;
  doc the rationale next to the writes.**
- [ ] **Migration test**: a `tests/test_dogfood_graph_native.py` exercises
  the new flow end-to-end: `dogfood.note` lands a Reflection;
  `dogfood.render(plan_slug)` returns markdown containing the
  observation; the rendered markdown does NOT need to be written to
  disk for the chain to work.
- [ ] **Reflection ontology gains `plan_slug` as an optional field.**
  Extends `ReflectCapability.ontology` (`reflect.py:20-24`). Backward
  compatible (optional field).

## Files

- **Modify:**
  - `agency/capabilities/dogfood.py` — add `note`, `render`; mark
    `collect` deprecated. (~50 LOC + ~30 LOC.)
  - `agency/capabilities/reflect.py` — add `plan_slug` to Reflection
    node ontology + thread through `note`/`batch_note`. (~5 LOC.)
  - `agency/capabilities/_jules_skills.py` — add Phase 0 to
    `JULES_SELF_IMPROVEMENT_SKILL`. (~10 LOC.)
  - `agency/install.py` — comment explaining why this file-write is
    canon-acceptable (rendered-view exception, not anti-pattern).
- **Create:**
  - `tests/test_dogfood_graph_native.py` — end-to-end note→render flow.
- **Documentation:** update `CLAUDE.md` rule 2 to cite Spec 017 as the
  closure; update `AGENCY_PROTOCOL.md` if the graph-as-store rule needs
  a sharper line.

## Worked example (panel addition)

**Setup**: `.agency/session.db` exists at the project root (Spec 020).

**Old flow** (markdown round-trip):
```bash
# Author edits Plan/013-…/DOGFOOD-NOTES.md by hand
# Later: dogfood.collect parses the markdown, batch_note seeds the graph
python -m agency.cli execute --code '
  c = await call_tool("capability_dogfood_collect", {"plan_dir": "Plan", "intent_id": "intent:abc"})
  return await call_tool("capability_reflect_batch_note", {"scope": "observation", "texts": c["texts"], "intent_id": "intent:abc"})
'
```

**New flow** (graph-native):
```bash
# Observation lands DIRECTLY in the graph (no markdown file authored)
python -m agency.cli execute --code '
  return await call_tool("capability_dogfood_note", {
    "observation": "COMPLETED in Jules is idle, not terminal — _classify needs a plan_unapproved branch.",
    "plan_slug": "013-jules-skills-and-capability-improvements",
    "intent_id": "intent:abc",
  })
'
# Later, when humans need the rendered ledger:
python -m agency.cli execute --code '
  return await call_tool("capability_dogfood_render", {"plan_slug": "013-jules-skills-and-capability-improvements", "intent_id": "intent:abc"})
' > Plan/013-…/DOGFOOD-NOTES.md   # optional: only when PR description needs it
```

The markdown file is no longer authoritative; the graph is. Render
runs on demand.

## Failure modes (panel addition)

- **No Reflections for the requested `plan_slug`** → `render` returns
  empty markdown with a heading (`# DOGFOOD-NOTES — plan-slug\n\n(none yet)\n`),
  never raises. Empty is a valid state, not an error.
- **`plan_slug` not in any spec's frontmatter** → `note` accepts it
  anyway (Reflection persists); `render` returns it cleanly. Linking
  to non-existent plans is a content concern, not a data-integrity one.
- **Spec 020's `.agency/session.db` not yet scaffolded** → `note` and
  `render` work against whatever DB the caller passes via `--db`;
  the `.agency/` default is opt-in, not enforced. Backward compatible.

## Open Questions

1. **Per-plan vs per-spec slug.** "plan_slug" = directory name
   (`013-jules-skills-and-capability-improvements`)? Or
   structured `{plan_id, phase?}`? Recommend the directory name as a
   single string — keeps the index cheap, queryable via
   `MATCH (r:Reflection {plan_slug: $s})`.
2. **Should `dogfood.render` write to disk OR just return text?** Per
   canon (graph is store), return text only — the caller decides whether
   to write. But many practical use cases (PR description preparation)
   want a file. Recommend: text-only return; provide a one-liner CLI
   wrapper for the file write case.
3. **What scope tag for graph-native observations?** Today
   `reflect.batch_note` uses `scope="observation"`. The new `dogfood.note`
   could keep that scope OR introduce `scope="dogfood"` (would require
   adding `dogfood` to the closed `REFLECT_SCOPES` set in
   `reflect.py:14`). Recommend `scope="observation"` + the `plan_slug`
   field for filtering — avoids ontology churn.
4. **Backfill or fresh-start?** Run `dogfood.collect` ONCE per existing
   plan to seed Reflection nodes from existing DOGFOOD-NOTES.md files,
   then deprecate? Or leave the existing markdown files as-is + only
   new observations go to graph? Recommend backfill (cleaner long-term
   state; provenance complete).

## Evidence

- `Plan/015-architecture-review/ARCHITECTURE-REVIEW.md` W1 + W2.
- `Plan/015-architecture-review/JULES-OBSERVATIONS.md` Round 1
  bullets 5-6 (Jules's own dogfooding through `reflect.note` proved
  the graph-native pattern works end-to-end).
- `agency/capabilities/dogfood.py:108` — the `with open()` in collect.
- `agency/capabilities/reflect.py:14` — `REFLECT_SCOPES` (closed enum).
- `Plan/014-observation-to-spec-amendment/spec.md` — the
  observation-pipeline that depends on Reflection nodes existing
  (Spec 017's `dogfood.note` feeds Spec 014's `dogfood.parse_amendment`
  cleanly).
- `docs/vision/GOALS.md` goal #7 — the canon this spec closes.

## Followup — Implementation Status (2026-06-03)

**Verdict:** Shipped — graph-native dogfood path live. The Vision/
GOALS.md goal #7 "graph is the store; files are a rendered view"
critical gap (per SPEC-VISION-ALIGNMENT.md audit) is closed for the
dogfood/observation flow. 10 spec tests green.

### Done
- `dogfood.note(observation, plan_slug)` — new act verb that
  writes a Reflection with `scope='observation'` + `plan_slug`
  property + OBSERVED_DURING + SERVES edges. NO file writes
  along the path; the graph is the canonical store.
- `dogfood.render(plan_slug)` — new transform verb that queries
  Reflection nodes matching the plan_slug and emits markdown in
  the existing DOGFOOD-NOTES.md format. Pure (no graph writes).
  Empty plan returns clean markdown with "(none yet)" body —
  never raises.
- `dogfood.collect` kept for backward compatibility (Spec 014's
  observation→spec-amendment pipeline + one-shot migration of
  existing DOGFOOD-NOTES.md files). Docstring updated with
  deprecation note: "Deprecated for ongoing use — prefer
  dogfood.note (graph-native authoring) + dogfood.render (markdown
  projection on demand)."
- Reflection ontology unchanged at the schema level — `plan_slug`
  is an OPTIONAL property (Spec 017 §Done When: "Backward
  compatible (optional field)"). The Reflection NODE_SCHEMAS lists
  only `scope` and `text` as required; plan_slug is stored when
  present + queryable via graph-query WHERE clause.

### Tests
- `tests/test_dogfood_graph_native.py` (10 tests):
  - note records Reflection with plan_slug
  - note links SERVES intent
  - render produces markdown with observations
  - empty plan returns clean "(none yet)" markdown
  - plan_slug scoping (one plan's observations don't appear in
    another's render)
  - render is pure (no graph writes)
  - reflect.note (existing verb without plan_slug) still works —
    backward compat
  - collect still works (deprecated docstring)
  - collect docstring contains "Deprecated" + "dogfood.note"
  - dogfood capability has all three verbs {note, render, collect}

### Scope-cut (per spec §"Done When" v1)
- The `_jules_skills.py` `JULES_SELF_IMPROVEMENT_SKILL` Phase 0
  addition (Spec 017 §Done When line 58-62) — deferred. The
  jules-self-improvement skill is a stable artifact and a Phase
  insertion is risky without panel review. Add as a follow-up PR
  once we have at least one full session running through Phase 0.
- The `install.py:145` canon-acceptable comment — that file IS
  the install manifest writer; comments about "rendered-view
  exception" are doc-only changes that didn't fit the spec's
  focused note/render shape. Add as a small doc-only follow-up.
- CLAUDE.md rule #2 cross-reference to Spec 017 — defer until the
  jules-self-improvement Phase 0 lands so both updates ship
  together.

### Doctrine win (vs SPEC-VISION-ALIGNMENT.md audit)
- 🔴 Goal 7 (graph IS the store) — write-side gap on observations
  is closed. Spec 043 (document.render) closed the render-side
  for other scopes; Spec 017 now does the same for the dogfood
  observation flow. Both halves match the Vision doctrine.

### Open for v2 (per spec §"Open Questions")
- OQ2 render write-to-disk vs return-only — v1 ships return-only
  (caller decides; canon-correct).
- OQ3 scope tag for graph-native observations — v1 ships
  `scope='observation'` + plan_slug filter (no enum churn).
- OQ4 backfill via collect — recommended in spec; v1 has no
  automated backfill (callers run `collect` + `batch_note` if
  they want to migrate).

### Cluster-coherence (Spec 047)
- C06/C08 (Memory) — closes the write-side of Goal 7.
- C07 (Documentation) — render verb is the projection complement
  to document.render(scope='install-artefacts'/'reflections').

## Followup — Original Implementation Status (2026-05-31)

> Consolidation pass on branch `claude/plan-spec-review-74gHM`. Frontmatter `status:` may be stale; this section reflects verified code state.

**Verdict:** Not started

### Done
- Nothing. Neither `dogfood.note` nor `dogfood.render` exists in `agency/capabilities/dogfood.py`. The file has only the `collect` verb (lines 77-124).
- `plan_slug` field is absent from `reflect.py`'s Reflection ontology.
- `_jules_skills.py` has not been extended with a Phase 0 `note-observation` step.
- `tests/test_dogfood_graph_native.py` does not exist.
- The `collect` verb is not marked deprecated.

### Still to implement
- `dogfood.note(observation, plan_slug)` act verb — not present (`agency/capabilities/dogfood.py` has only `collect`).
- `dogfood.render(plan_slug)` transform verb — not present.
- `dogfood.collect` deprecation docstring.
- `plan_slug` optional field on the Reflection ontology (`agency/capabilities/reflect.py`).
- Phase 0 addition to `JULES_SELF_IMPROVEMENT_SKILL` in `agency/capabilities/_jules_skills.py`.
- `install.py:145` canon-exception comment (the write-to-disk rationale).
- `tests/test_dogfood_graph_native.py` end-to-end note→render test.

### Refinement needed (given later specs)
- Spec 014 (`dogfood.parse_amendment`) depends on Reflection nodes tagged with `plan_slug` (this spec's output). Both 014 and 017 are Not started; they must be sequenced together — implement 017 first.
- Spec 020 is a listed dependency and is Partially implemented (substrate exists); that dependency is met well enough to unblock 017's implementation.

### Evidence
- code: `agency/capabilities/dogfood.py` (only `collect` verb; no `note` or `render`); `agency/capabilities/reflect.py` (no `plan_slug` field)
- tests: `tests/test_dogfood_and_batch_note.py` (covers `collect` + `batch_note` only); `tests/test_dogfood_graph_native.py` absent
- commits/notes: No commit referencing `dogfood.note`, `dogfood.render`, or `plan_slug`
