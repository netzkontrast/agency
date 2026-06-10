---
spec_id: "182"
slug: cluster-coherence-live-audit
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "047"
depends_on: ["047", "149", "157", "084"]
vision_goals: [4, 6]
affects:
  - scripts/check-cluster-coherence
  - tests/test_cluster_coherence_audit.py
---

# Spec 182 — cluster-coherence live audit

## Why

Spec 047 (cluster-integration) maps the 13 SDLC+meta clusters onto the
agency surface — but it is a STATIC plan document. CLAUDE.md rule 5
("check cluster coherence before adding a verb/skill") relies on a
human reading the master spec. The check should be LIVE: every verb /
skill / substrate tool in the registry maps to exactly one cluster, and
an audit flags any verb that lands in no cluster (dormant surface) or
breaks a cluster's documented integration pattern.

## Done When

- [ ] **`scripts/check-cluster-coherence`** maps every live verb to a
      cluster (from a derived cluster→capability table, Spec 149) and
      flags unclustered verbs.
- [ ] **The ≥150-LOC / ≥3-cross-cluster-decision promotion trigger
      (CLAUDE.md rule 5)** is measured, not eyeballed — the audit
      reports which cluster sections have outgrown the master.
- [ ] **`analyze.graph` (Spec 084) backs the verb census.**
- [ ] CI job runs it; a new unclustered verb warns.
- [ ] Test: an unclustered fixture verb is flagged; a cluster over the
      promotion threshold is reported.
- [ ] TODO row + drift clean.

## Interconnects

- **Drift-derivation chain** (149): cluster→capability table derived.
- Spec 157 (architecture gate) is the sibling standing audit.
- Spec 084 (analyze.graph) is the census surface.

## Open questions

1. Block on unclustered verbs? **Recommend**: warn (a verb may
   legitimately span clusters); block only on the no-cluster case.
