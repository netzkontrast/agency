---
spec_id: "017"
slug: graph-native-dogfood-ledgers
status: draft
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
