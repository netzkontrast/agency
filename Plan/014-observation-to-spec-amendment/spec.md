---
spec_id: "014"
slug: observation-to-spec-amendment
status: draft
owner: "@agency"
depends_on: ["013"]
affects:
  - agency/capabilities/dogfood.py    # extend with amendment-proposal verb
  - agency/capabilities/reflect.py    # query API for marked observations
  - skills/                            # `jules-self-improvement` rebinds to chain through the new verbs
estimated_jules_sessions: 0   # design only; implementation comes after spec-panel
domain: capability
wave: 3
---

# Spec 014 — Observation → spec amendment (the half of self-improvement v1 deferred)

## Why

Spec 013 closed the *durable-memory* half of self-improvement:
`dogfood.collect → reflect.batch_note` lands one `Reflection` node per
observation from `Plan/**/DOGFOOD-NOTES.md`. That gives us a queryable
history of "what surprised us while building this." It does **not** close
the loop — the observations don't yet feed back into the specs that
generated them.

This spec is the second half: **take a Reflection and propose a concrete
edit to a DESIGN.md / spec.md / IMPLEMENTATION-PLAN.md.** Pre-baked hints
below come from running `jules-self-improvement` on the *real* `Plan/`
tree once (commit `a07c65a`) — 10 observations across specs 012 + 013.

## Done When

- [ ] **Phase A — Research (parallel subagents).** Mine the existing 10
  observations for the *structural patterns* a generator needs to detect,
  the resolution-status taxonomy, the spec-section targeting rules.
- [ ] **Phase B — Design draft.** Lands `Plan/014-…/DESIGN.md` covering
  the proposed pipeline shape (see hint #1 below) and the closed set of
  amendment kinds (hint #4).
- [ ] **Phase C — Spec-panel.** Multi-expert review per the established loop.
- [ ] **Phase D — Refine.** Per the panel's must-fixes.
- [ ] **Phase E — Implementation plan.** Mirrors Spec 012's structure;
  per-phase boundary calls (us-inline vs Jules dispatched per the
  `delegate.dispatch-decision` skill heuristic).
- [ ] **Phase F — TDD execution.** Out of scope for spec 014's draft.

## Hints from the live self-improvement run (the actual signal)

These are NOT speculation — they're patterns observed in our own
`Plan/012/DOGFOOD-NOTES.md` + `Plan/013/DOGFOOD-NOTES.md`, surfaced as
`Reflection` nodes by walking the `jules-self-improvement` skill. They
are the meta-shape Spec 014's design should match.

### Hint 1 — Many observations carry an explicit "→ Design fold-back:" prescription

Pattern (literal, from the ledger): every observation that proposes a
spec change ends with a markdown line of the form
`→ **Design fold-back:** <prescription>` or `→ **Lesson:** <rule>`.

The Reflection node already carries the full text including this marker.
The generator's lowest-cost entry point is therefore **pattern extract**,
not LLM synthesis:

```python
@verb(role="transform")
def parse_amendment(self, reflection_id: str) -> dict:
    """Extract the `→ **Design fold-back:**` (or `→ **Lesson:**`) tail
    from a Reflection and return {has_amendment, kind, prescription,
    cited_artefacts}."""
```

For the 10 reflections we collected, this pattern hits **6 of 10**
observations cleanly. The other 4 are either self-resolving
("Now documented in the docstring") or tactical (no architectural
fold-back). → Build the pure-pattern verb first; LLM-shaped synthesis
is a separate verb for the cases where no explicit marker exists.

### Hint 2 — Observations differ by *resolution status*

The 10 reflections fall into three buckets:

| status            | example trigger                                  | what Spec 014 should do |
|-------------------|--------------------------------------------------|---|
| `proposed`        | "→ Design fold-back: add `protocol_preset` field" | propose an amendment to the relevant DESIGN.md |
| `already-resolved`| "Fix: added `engine` field to `CapabilityContext`" | mark as `RESOLVED in commit X`; skip proposal |
| `tactical-only`   | "Phase 5 should precede Phase 4 in any future re-run" | leave in the ledger; no spec edit |

The generator MUST classify before proposing. Without classification,
Spec 14 would re-propose fixes already committed — token cost +
reviewer confusion. → Add `dogfood.classify(observation)` as the second
extraction verb; the resolution classifier is heuristic (presence of
"Fix:" / "Now documented" / past-tense vs imperative) and cheap.

### Hint 3 — Some observations cite line numbers + file paths verbatim

Examples from the ledger: `CORE.md:38-45`, `jules.py:261`,
`memory.py:161-175`, `gate.py:25`. These are PRE-RESOLVED cite targets —
the generator doesn't need to find them. The amendment-proposal verb
should extract these inline and use them as the SOURCE OF TRUTH the
proposed edit must match.

```python
_CITE_RE = re.compile(r"`?([A-Za-z][\w/]*\.md|[A-Za-z][\w/]*\.py):(\d+)(?:-(\d+))?`?")
```

→ Build the cite-extractor as a tiny utility in `dogfood.py`. Spec 14's
pipeline reads cites; the LLM-shaped synthesis step (if any) operates
on the cited file region, not the whole file.

### Hint 4 — The closed set of amendment kinds is small

From the 10 observations the prescribed amendments are EXCLUSIVELY one of:

1. **Add a section / paragraph** — most common ("add to the spec's
   Refinement notes that …", "document in `docs/vision/specs/…`").
2. **Add a configurable field** — second most common ("Phase 5 should
   add a `protocol_preset` field to `dispatch`").
3. **Promote a value to a first-class enum** — once ("consider adding
   `dogfood` as a real scope in the next core ontology update").
4. **Mark a follow-on as parking-lot** — once ("Track upstream; remove
   the filter when a fixed version ships").

A closed-set amendment kind enum lets the spec-amendment proposer
return STRUCTURED output rather than free-text — and lets the
orchestrator review/apply each amendment uniformly. → Define the
`AMENDMENT_KINDS` enum on `dogfood`'s `OntologyExtension` in Spec 14's
DESIGN.md.

### Hint 5 — The "cut, don't carry" meta-rule applies to spec amendments too

Observation: when Spec 013 Phase 4 landed the `auto_create_pr`
deprecation alias, it was cut in the next commit per the user's
"initial version — no users to keep back-compat for" directive.

The amendment proposer MUST NOT add deprecation paths to specs in
their first iteration. If a spec's draft contradicts an observation,
the right amendment is to **rewrite the relevant section**, not append a
"deprecated:" note. This keeps the spec a live decision, not a
versioned changelog. → Codify in Spec 14's DESIGN.md as a generation
rule the proposer enforces.

### Hint 6 — The "cited artefact must exist" verification step

Multiple observations cite paths that didn't exist when the ledger was
written but now do (e.g. `AGENCY_PROTOCOL.md` was new in this session).
The amendment proposer must `git ls-files | grep -F "<cite>"` before
proposing an edit — proposing an amendment to a non-existent file
is the silent-fail mode for *this* loop. → Add as a Phase B design
constraint: every proposed amendment passes `cite_exists` before
landing as a candidate.

### Hint 7 — The proposer should call `reflect.search` for cross-spec dedupe

Two of the 10 observations have semantically similar prescriptions
("add `protocol_preset`" appears in two distinct observations 5
months apart in the ledger as we collected it). The proposer must
`reflect.search(query)` against Reflection nodes to avoid proposing
the same amendment twice. → Spec 14's pipeline includes a dedupe
phase that returns `{novel, duplicates}`; only novel candidates land
as proposed amendments.

### Hint 8 — Walk the existing skill schema, don't introduce a new one

`jules-self-improvement` is the canonical skill for this loop today
(2 phases: collect → batch_note). Spec 14 should **extend** it with two
additional phases (parse-amendments + classify + propose) rather than
introducing a parallel skill. The intersection model from Spec 013
says "skills compose by binding to each other's hard gates"; for v2
self-improvement, the same skill with deeper phases is the right shape.

```python
JULES_SELF_IMPROVEMENT_V2_SKILL = {
    "name": "jules-self-improvement",
    "phases": [
        {"index": 1, "name": "collect-dogfood", "invoke": dogfood.collect, ...},
        {"index": 2, "name": "fold-into-graph", "invoke": reflect.batch_note, ...},
        # NEW in Spec 14:
        {"index": 3, "name": "parse-amendments", "invoke": dogfood.parse_amendment, ...},
        {"index": 4, "name": "classify", "invoke": dogfood.classify, ...},
        {"index": 5, "name": "propose", "invoke": dogfood.propose, ...},
        {"index": 6, "name": "review", "gate": "hard", ...},
    ],
}
```

The HARD GATE at `review` is the canonical "orchestrator approves
amendments before they touch the spec" step.

## Files (the design will refine)

- **Create**:
  - `agency/capabilities/dogfood.py` — extend with `parse_amendment`,
    `classify`, `propose`, `cite_exists` verbs (Hints 1, 2, 3, 6).
  - `Plan/014-…/DESIGN.md` (Phase B), `REVIEW.md` (Phase C),
    `IMPLEMENTATION-PLAN.md` (Phase E).
- **Modify** later (Phase F):
  - `agency/capabilities/_jules_skills.py` — extend
    `JULES_SELF_IMPROVEMENT_SKILL` per Hint 8.

## Open Questions / for the spec-panel

1. **Is `dogfood` the right capability home for amendment proposing?** Or
   does a new `improve` capability deserve to exist?
2. **Does the proposer write directly to DESIGN.md** (effect) **or
   return a candidate diff** for the orchestrator to apply (transform)?
   Per the Spec 012 REVIEW must-fix #1 doctrine (verbs propose, agents
   apply), transform is the canon-aligned answer; confirm in Phase C.
3. **How does the proposer disambiguate when a cite points to a
   moved file?** (e.g. `Plan/JULES_PROTOCOL.md` was renamed to
   `AGENCY_PROTOCOL.md` mid-session.)
4. **`reflect.search` is keyword-only today.** Hint 7's dedupe step
   wants semantic similarity. Out of scope for v1, OR extend
   `reflect.search` with a `similarity_threshold` arg backed by
   embeddings? Defer to v2 unless the keyword path proves too noisy
   in practice.

## Evidence

- `Plan/012-…/DOGFOOD-NOTES.md` — the original ledger, 5 observations.
- `Plan/013-…/DOGFOOD-NOTES.md` — the second ledger, 5 observations.
- The 10 Reflection nodes recorded by the canonical self-improvement
  walk against the live `Plan/` tree (commit `a07c65a` — see
  `tests/test_dogfood_and_batch_note.py::test_collect_against_real_repo_plan_tree`
  for the path).
- `docs/vision/CORE.md` §47-62 (skills compose), §131-133
  (capability-owned ontology).
