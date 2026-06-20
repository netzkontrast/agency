---
spec_id: "161"
slug: skill-first-discovery-llm-rank
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "025"
depends_on: ["025", "068", "147", "146"]
vision_goals: [1, 5]
affects:
  - agency/_discovery.py
  - tests/test_skill_first_discovery.py
---

# Spec 161 — Skill-first discovery with optional LLM rank

## Why

Spec 025 (skill-first-discovery) is Partial — "skill-search ranks above
tool-search; refinement needed per consolidation pass". Tiered
discovery (Spec 068) ships the capability-tier-first surface, but the
RANKING within a tier is lexical. When the `[anthropic]` extra is
present, the Spec 147 Driver can re-rank the top-N candidates by intent
relevance — without ever loading the full tool list (Goal 1) and on a
cache-stable prefix (Spec 146).

## Done When (measurable invariants — rule 8)

- [ ] **Invariant: skill rank ≤ verb rank** for every (query, skill, verb)
      triple where the skill's `Use when:` matches — asserted across the
      live skill+verb set, not pinned to a count.
- [ ] **Invariant: rank-order is deterministic when `[anthropic]` is
      absent** — same query, same DB hash ⇒ byte-identical result order.
- [ ] **Invariant: re-rank touches the body only** — a re-rank call
      produces zero byte-delta in the response prefix (Spec 146
      `prefix_stability`).
- [ ] **Relationship: `mean_rank_lift(LLM) ≥ mean_rank_lift(lexical)`**
      on the 10-query benchmark fixture (mocked Driver in CI; live
      behind a `[llm-live]` tag) — derived from the fixture, not a
      pinned score.
- [ ] **Failure modes (LLM path):** Driver timeout → fall back to
      lexical with a `Codes.RERANK_TIMEOUT` warning Reflection; Driver
      returns malformed structured output → fall back to lexical;
      Driver returns IDs not in the candidate set → reject + lexical
      fallback (never trust opaque IDs back from the model).
- [ ] **Optional LLM re-rank gated on ambiguity** — top-2 lexical
      scores within ε; otherwise skip the call (cost discipline).
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  query "find prior reflections on dispatch decisions" and
        a skill `develop.brainstorm` lexically ranked 3rd, verb
        `analyze.graph` ranked 1st
When:   search(query, detail="brief") runs with `[anthropic]` installed
        and top-2 lexical scores within ε
Then:   response.results[0].kind == "skill" AND
        results[0].name == "develop.brainstorm" AND
        envelope.prefix bytes are byte-identical to a prior call
        (cache held — Spec 146)

Given:  same query, `[anthropic]` absent
When:   search(query) runs twice
Then:   the two result orderings are byte-identical (deterministic
        lexical fallback)
```

## Interconnects

- **LLM-driver chain** (147) · **output-budget chain** (146).
- Spec 068 (tiered discovery) is the surface this refines.
- Spec 162 (`skills.llm_select` Matcher) shares the re-rank
  structured-output contract — same Driver call shape, different
  candidate type.
- Spec 170 (doctor) reports `rerank_available` (derived from
  `[anthropic]` + benchmark parity).
- Spec 151 (Codes coverage) supplies `RERANK_TIMEOUT` +
  `RERANK_MALFORMED`.

## Open questions

1. **Re-rank cost vs benefit?** **Recommend**: only when top-2 lexical
   scores within ε (ambiguity gate); skip the call otherwise. The
   ambiguity threshold is a tunable, not a snapshot.
2. **N for top-N re-rank.** **Recommend**: 10 — matches tiered-
   discovery's brief-tier payload (Spec 068); avoids re-ranking
   candidates the user will never see.
3. **Cache the re-rank verdict?** **Recommend**: session-scoped
   `(query_hash, candidate_set_hash) → ordering` — repeat searches
   in a walk shouldn't re-pay the Driver call.

## Followup — Implementation Status (Slice 1, 2026-06-12)

**Verdict:** Slice 1 SHIPPED on `claude/autonomous-completion`.

The typed shape this spec carries was shipped as part of the wave-1+2
batch (intents trackable in graph). See TODO.md row + the corresponding
test module under `tests/`.

