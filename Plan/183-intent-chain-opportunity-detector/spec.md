---
spec_id: "183"
slug: intent-chain-opportunity-detector
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "048"
depends_on: ["048", "150", "147", "084"]
vision_goals: [2, 6]
affects:
  - agency/capabilities/analyze/_main.py
  - tests/test_intent_opportunity.py
---

# Spec 183 — intent-chain capability-opportunity detector

## Why

Spec 048 ships PARENT_INTENT edges + the owner enum + the
analyze.paths axis (IP001/IP002/IP003) "for session traceability +
capability-opportunity detection". The opportunity-DETECTION half is
latent: the IP axis finds chain shapes but nothing turns a recurring
shape into a "you should build a capability for this" proposal. With the
Spec 150 classifier + Spec 147 Driver, a recurring sub-intent pattern
(the same raw-tool sequence SERVING many intents) becomes an amendment
proposal: "promote this sequence to a verb".

## Done When

- [ ] **`analyze.paths` gains an opportunity report** — recurring
      raw-tool sequences across intents ranked by frequency. Typed
      shape:
      ```python
      OpportunityReport = {
        "opportunities":      list[Opportunity],
        "intents_scanned":    int,
        "sequences_observed": int,
        "min_frequency":      int,                 # documented threshold
        "min_intent_breadth": int,                 # how many distinct intents
      }
      Opportunity = {
        "sequence":            list[str],          # raw verb/tool names
        "frequency":           int,                # occurrences
        "intent_breadth":      int,                # distinct intents seen across
        "proposed_capability": str,                # Driver-suggested home
        "proposed_verb":       str,                # Driver-suggested name
        "rationale":           str,                # ≥ 40 chars; from Driver
        "confidence":          float,              # 0..1; Driver-reported
        "chain_ids":           list[str],          # PRODUCES-from sources
      }
      ```
- [ ] **Invariant — frequency floor is RELATIONSHIP, not pinned.**
      Assert `opportunity.frequency ≥ min_frequency` AND
      `opportunity.intent_breadth ≥ min_intent_breadth` (documented
      config, defaults 5 and 3 respectively) — never freeze the live
      live count. CLAUDE.md rule 8.
- [ ] **Invariant — provenance preserved.** Each Opportunity produces
      exactly one Reflection node (Spec 045) with PRODUCES-from edges
      to EVERY chain in `chain_ids`. Assert
      `len(chain_ids) == opportunity.frequency` (no dropped lineage).
- [ ] **Invariant — proposal lands as Spec-150 amendment.** Each
      Opportunity above the floor produces an amendment proposal node
      typed `proposal.kind == "promote-to-verb"`; Spec 150 classifier
      consumes it (no separate ingestion path).
- [ ] **Invariant — census source.** `analyze.graph` (Spec 084) is the
      sole source for Invocation walks; no independent registry walk.
- [ ] **Invariant — duplicate suppression.** Before emitting,
      `reflect.recall_semantic` (Spec 045/181) is queried for prior
      proposals on the same sequence; existing proposals are LINKED
      via SUPERSEDES, not duplicated.
- [ ] **Degrades cleanly** without the Spec 147 Driver — opportunities
      surface with `proposed_capability=None`, `rationale=""`; the
      report still ranks frequency (Driver augments, doesn't gate).
- [ ] Test: a 5×-repeated sequence across 3 distinct intents surfaces
      as the top opportunity and yields a promote-to-verb proposal
      (mocked Driver); confidence + chain_ids populated; duplicate run
      yields a SUPERSEDES link, not a second proposal.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a graph with 40 intents, 7 of which share the raw-tool
        sequence [Grep, Read, Edit, Bash("pytest")] (frequency=7,
        intent_breadth=7)
When:   analyze.paths(opportunity_report=True, driver="anthropic")
Then:   returns OpportunityReport{
            opportunities: [Opportunity{
                sequence: ["Grep","Read","Edit","Bash(pytest)"],
                frequency: 7,
                intent_breadth: 7,
                proposed_capability: "develop",
                proposed_verb: "tdd_cycle",
                confidence: 0.82,
                rationale: "Recurring grep→read→edit→test loop across…",
                chain_ids: [7 Invocation chain ids]
            }],
            intents_scanned: 40,
            min_frequency: 5,
            min_intent_breadth: 3
        }
        AND a Reflection node exists with 7 PRODUCES-from edges
        AND Spec 150 classifier ingests it as kind="promote-to-verb"
        AND a re-run produces a SUPERSEDES edge, not a duplicate
```

## Failure modes (Nygard)

| Failure | Detector response |
|---|---|
| `DriverError.REFUSAL` on classification | emit Opportunity with `proposed_capability=None`, `rationale=""`; Reflection records the refusal; Spec 150 may re-classify later |
| Driver hallucinates non-existent capability name | typed `Codes.UNKNOWN_TARGET_CAPABILITY`; validate against live registry (Spec 084); drop the proposal |
| Sequence matches a verb that already exists | suppress; emit Reflection(`scope="opportunity-already-shipped"`) so the loop learns |
| Census mismatch (analyze.graph vs registry) | typed `Codes.CENSUS_DRIFT`; defer to Spec 182 cluster-coherence audit |
| Recall lookup (Spec 181) fails | proceed without dedup; mark Opportunity `dedup_skipped=True`; Spec 150 handles downstream duplicates |
| Frequency threshold tuned too low (proposal flood) | Spec 150 amendment proposes raising `min_frequency`; the threshold IS tunable config, not a fixed magic number |

## Interconnects

- **Dogfood-loop chain** (150): opportunities ARE amendment proposals;
  this surface is the loop's primary input from chain analysis.
- **LLM-driver chain** (147): classifies proposed capability + verb +
  rationale; shares the `Usage` envelope.
- Spec 084 (analyze.graph): supplies the Invocation + PARENT_INTENT
  chain census — single source.
- Spec 048 (intent-chain): the PARENT_INTENT edge structure this spec
  walks; opportunity detection IS the IP-axis latent half.
- Spec 045/181 (reflect recall_semantic): duplicate-suppression
  lookup; embedder quality directly bounds dedup quality.
- Spec 178 (analyze judge axis): a peer producer of Reflections; the
  proposal stream merges with judged findings into Spec 150's queue.
- Spec 179 (document-render LLM narrative): renders the proposal
  report into the audit-narrative scope.
- Spec 182 (cluster-coherence live audit): sibling audit — that one
  finds spec-cluster opportunities, this one finds verb opportunities;
  they share the registry census via Spec 084.
- Spec 180 (research managed-agent fan-out): produces SubagentSession
  chains that become candidate sequences here.

## Open questions

1. **Sequence-similarity threshold?** **Recommend**: exact verb-name
   sequence v1 (cheap, deterministic, easy to validate);
   fuzzy/embedding-based sequence matching is Slice-2, gated by
   measured miss rate exceeding 20% on a labelled fixture.
2. **Window for sequence detection — full chain or sliding?**
   **Recommend**: sliding window of length 2–6 over each chain;
   surface every distinct contiguous subsequence whose frequency
   crosses the floor. The 2–6 bound is documented config.
3. **Proposal lifetime — when do unaccepted opportunities expire?**
   **Recommend**: never auto-expire — Spec 150 handles
   accepted/rejected/superseded state machine. Stale proposals
   surface to doctor (Spec 170) as a coherence signal.
