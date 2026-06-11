---
spec_id: "221"
slug: novel-research-fanout
status: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "105"
depends_on: ["105", "180", "126", "168", "132", "147", "217", "222"]
vision_goals: [8, 1]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_research_fanout.py
---

# Spec 221 — novel research fan-out + ingest reuse

## Why

Spec 105 (novel-research) ships the research surface for a novel
(worldbuilding facts, period detail, technical accuracy). It delegates
to `agency.research`, which is gaining Managed-Agent fan-out (Spec 180)
+ server-side web (Spec 168) + the large-corpus ingest (Spec 126, the
KP example). Novel research should inherit all three: a historical-novel
fact-check can fan out, and a large source corpus ingests
subagent-isolated (the KP pattern, proven). The novel never grows
research-specific LLM code — the 105 delegation pattern is the contract.

## Done When

- [ ] **Novel research inherits Spec 180 fan-out + Spec 168 web depth +
      Spec 126 ingest** — no novel-specific LLM code (the 105 delegation
      pattern, validated).
- [ ] **Typed return shape**:
      ```python
      NovelResearchResult = {
        "intent_id":      str,
        "question":       str,
        "citations":      list[dict],   # [{url|doc_id, span, claim, confidence}]
        "ingested_sources": list[str],  # Artefact ids (Spec 126 pattern)
        "codex_links":    list[str],    # entity ids extended via Spec 132
        "fanout_count":   int,          # Spec 180 sub-agents spawned
        "driver":         Literal["spec147","fake"],
        "refusal":        dict | None,
      }
      ```
- [ ] **Ingested sources link to the novel** (the KP `ingested-source`
      Artefact pattern) as research provenance — every ingest produces
      an `Artefact(kind="ingested-source") PRODUCES Novel`.
- [ ] **Citations flow into the codex** (Spec 132) as entity sources —
      every citation that names an entity in the codex appends a
      `SOURCED_BY` edge.
- [ ] **Invariant — citation-to-codex edge fidelity.** Assert that for
      every citation whose `claim` mentions a codex entity name, the
      result includes an entry in `codex_links` and the graph has a
      matching `SOURCED_BY` edge. No silent dropping.
- [ ] **Invariant — fan-out is non-degenerate.** When `fanout=True`,
      assert `fanout_count >= 1` AND every sub-agent's output is
      attached as a citation or ingested-source Artefact. A fan-out
      that returns zero attached children is a bug, not a no-op.
- [ ] **Invariant — delegation purity.** A grep of
      `agency/capabilities/novel/` MUST find zero direct
      `AnthropicDriver`/`research_*` LLM-call sites — the novel
      surface delegates only. CI asserts the count is zero (a
      relationship: novel-LLM-call-count == 0, derived live).
- [ ] **Invariant — ingest provenance roundtrip.** Every entry in
      `ingested_sources` MUST resolve to a graph Artefact whose
      `PRODUCES Novel` edge survives a session restart (the KP
      durability bar).
- [ ] **Failure modes**:
      - `Codes.RESEARCH_FANOUT_TIMEOUT` propagated from Spec 180 when
        a sub-agent exceeds the wall-clock budget — partial citations
        still attached;
      - `Codes.INGEST_OVERSIZED` from Spec 126 when a single source
        exceeds the per-ingest cap — surfaces a recall handle instead;
      - `Codes.WEB_DRIVER_REFUSAL` from Spec 168 / 147 — recorded as
        a research-refusal Artefact, other sub-agents proceed;
      - `Codes.CITATION_UNVERIFIABLE` when a sub-agent returns a claim
        with no resolvable URL/doc_id — claim recorded as
        `confidence="unverified"`, not silently dropped.
- [ ] Test: a novel research call uses the upgraded path (mocked);
      ingest links to the novel; codex SOURCED_BY edges appear; fan-out
      timeout preserves partial citations.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a novel set in 1920s Shanghai with a codex entity "Bund
        Customs House" and a research question "what currencies traded
        on the Bund in 1923?"
When:   novel_research(question, fanout=True) dispatches 3 sub-agents
        via Spec 180 and 1 ingest of a 400-page period gazetteer via
        Spec 126
Then:   result.fanout_count == 3
        AND result.citations contains ≥ 1 entry per sub-agent
        AND result.ingested_sources contains the gazetteer Artefact id
        AND the gazetteer Artefact has PRODUCES Novel{id:X}
        AND codex_links contains "Bund Customs House" because the
            citation claim names it
        AND the codex entity has a new SOURCED_BY edge to the citation

Given:  Spec 168 web driver refuses one sub-agent's query
        (sensitive content category)
When:   novel_research collects sub-agent results
Then:   that sub-agent's slot records Artefact(kind="research-refusal")
        AND the other 2 sub-agents' citations remain attached
        AND result.refusal is None at the top level (partial success)
        AND result.fanout_count still reports 3 (dispatch count)

Given:  a developer adds a direct anthropic.complete call inside
        agency/capabilities/novel/_main.py
When:   the delegation-purity invariant runs in CI
Then:   the test fails naming the offending file:line
```

## Failure modes

LLM-touching surfaces (Spec 147 driver, Spec 168 web, Spec 180 fan-out)
all propagate typed refusal/timeout codes. The novel research wrapper
treats each sub-agent as independently fallible — one refusal does NOT
fail the whole call; partial citations remain attached as long as ≥ 1
sub-agent or ingest succeeds. Spec 126 ingest of an oversized source
returns a recall handle rather than crashing the call. Unverifiable
claims are recorded as `confidence="unverified"` rather than dropped —
the author decides whether to keep them.

## Interconnects

- Spec 180 (fan-out) + Spec 168 (web) + Spec 126 (ingest) inherited.
- Spec 132 (codex) consumes the citations as `SOURCED_BY` edges.
- Spec 147 (Driver) underlies the LLM-touching sub-agents via Spec 180.
- Spec 217 (build walkable) calls this verb at the research phase.
- Spec 222 (catalogue graph-query) — cross-work research queries
  ("every source cited by ≥ 2 of my novels") traverse the same
  citation moat.
- Spec 252 (novel skill-walks managed) — wraps this verb on the
  Managed-Agents path.

## Open questions

1. Novel-specific specialist roles? **Recommend**: reuse shared roles;
   a `period-accuracy` specialist is a Slice-2 if demand appears —
   adding before demand inflates the role registry.
2. Citation confidence scoring — Driver-judged or rule-based?
   **Recommend**: rule-based for v1 (URL resolves + claim verbatim in
   source = `high`; claim paraphrased = `medium`; no source =
   `unverified`); Driver-judged is a Slice-2.
3. Ingest deduplication across novels? **Recommend**: yes — Spec 126
   already keys ingests by content hash; a second novel re-using the
   gazetteer reuses the Artefact and adds a second `PRODUCES Novel`
   edge.
4. Should fan-out timeouts be per-subagent or aggregate? **Recommend**:
   per-subagent (Spec 180 default) — one slow sub-agent shouldn't kill
   the others; aggregate timeout is the wrapping intent's budget.
