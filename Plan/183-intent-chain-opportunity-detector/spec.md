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
      raw-tool sequences across intents (from PARENT_INTENT chains +
      Invocation nodes, via Spec 084) ranked by frequency.
- [ ] **High-frequency sequences become amendment proposals** (Spec 150)
      — "promote sequence X to a verb in capability Y", classified via
      the Spec 147 Driver.
- [ ] **Provenance preserved** — each proposal cites the chains it
      generalizes (PRODUCES-from edges).
- [ ] Test: a 5×-repeated sequence surfaces as the top opportunity and
      yields a promote-to-verb proposal (mocked Driver).
- [ ] TODO row + drift clean.

## Interconnects

- **Dogfood-loop chain** (150): opportunities ARE amendment proposals.
- **LLM-driver chain** (147): classifies the proposal.
- Spec 084 (analyze.graph) supplies the chain census.

## Open questions

1. Sequence-similarity threshold? **Recommend**: exact verb-name
   sequence v1 (cheap); fuzzy sequence matching is a Slice-2.
