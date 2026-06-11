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
      flags unclustered verbs. Returns a typed shape:
      ```python
      CoherenceReport = {
        "clusters":              list[ClusterRow],
        "unclustered_verbs":     list[str],         # verbs in NO cluster
        "multi_cluster_verbs":   list[tuple[str,list[str]]],  # spans
        "over_threshold":        list[ClusterRow],  # past promotion gate
        "verb_count":            int,
        "cluster_count":         int,
        "exit_code":             Literal[0, 1],     # 0 clean, 1 drift
      }
      ClusterRow = {
        "name":                 str,
        "capabilities":         list[str],
        "verb_count":           int,
        "spec_section_loc":     int,                # live, from master spec
        "cross_cluster_refs":   int,                # named decisions
        "promotion_due":        bool,               # ≥150 LOC OR ≥3 refs
      }
      ```
- [ ] **Invariant — every verb has a home (or is flagged).** Assert
      `len(unclustered_verbs) == 0` OR exit code is 1 — no silent
      dormant surface. Computed from the live registry, never pinned.
- [ ] **Invariant — promotion trigger is measured, not eyeballed.**
      The CLAUDE.md rule 5 gate (≥ 150 LOC OR ≥ 3 cross-cluster
      decisions) is COMPUTED from the master spec section — assert
      `promotion_due == (spec_section_loc ≥ 150 OR cross_cluster_refs ≥ 3)`.
      The thresholds are documented config, not hardcoded asserts.
- [ ] **Invariant — derivation freshness.** The cluster→capability
      table is derived (Spec 149); a doc-drift run after a verb add
      flips at least one cluster's `capabilities` list — no manual
      edit window.
- [ ] **Invariant — census source.** `analyze.graph` (Spec 084) is the
      ONLY source for `verb_count`; an assertion verifies the audit
      does not re-walk the registry independently (one census, one
      truth).
- [ ] **CI job runs it on every PR;** a new unclustered verb produces
      a warn-only annotation; the no-cluster case (and only it) blocks.
- [ ] Test: an unclustered fixture verb is flagged; a cluster over the
      promotion threshold is reported; live-derived counts match
      `analyze.graph` output.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a registry with 47 verbs across 13 clusters; one new verb
        `cluster_x_widget` lives in no cluster section of Spec 047;
        the "develop" cluster section has grown to 187 LOC
When:   scripts/check-cluster-coherence
Then:   returns CoherenceReport{
            verb_count: 47,
            unclustered_verbs: ["cluster_x_widget"],
            over_threshold: [ClusterRow{
                name: "develop",
                spec_section_loc: 187,
                cross_cluster_refs: 2,
                promotion_due: True
            }],
            exit_code: 1
        }
        AND CI annotates the PR with the unclustered verb (warn)
        AND CI does NOT block merge (warn-only on non-fatal cases)
        AND `analyze.graph` reports verb_count: 47 (matches audit)
```

## Failure modes (Nygard)

| Failure | Audit response |
|---|---|
| Master spec section parse error | typed `Codes.CLUSTER_MASTER_PARSE_FAILED`; exit 1; CI surfaces the line |
| `analyze.graph` unavailable | fall back to direct registry walk; report `census_source="registry_fallback"` so the audit is honest about its source |
| Verb in 0 clusters | exit 1; CI warns (does NOT block) — verb may be legitimately new |
| Verb in ≥ 2 clusters | warn-only; recorded in `multi_cluster_verbs`; allowed (clusters can overlap) |
| Cluster section past promotion gate but no promoted spec exists | warn-only; create a Plan/NNN-… task entry via Spec 150 amendment proposal |
| Derived cluster→capability table drift vs CLAUDE.md rule 5 quote | doc-drift run (Spec 149) flags it; this audit defers to that signal |

## Interconnects

- **Drift-derivation chain** (149): cluster→capability table is
  derived; this audit consumes the derivation.
- **Standing-audit chain** (157, architecture gate): sibling audit
  surface; both report into the PR status check matrix.
- Spec 084 (analyze.graph): the verb census surface — single source
  of truth for `verb_count`.
- Spec 047 (cluster-integration master): the static plan this audit
  makes LIVE.
- Spec 048 (PARENT_INTENT): cross-cluster decisions are intents
  spanning ≥ 2 clusters — counted as `cross_cluster_refs`.
- Spec 150 (dogfood loop): a chronic over-threshold cluster becomes
  an amendment proposal ("promote to standalone spec").
- Spec 183 (intent-chain opportunity detector): peer audit — that
  one finds verb opportunities, this one finds spec-cluster
  opportunities; they share the registry census.
- Spec 170 (doctor): the report's `exit_code` flows into doctor's
  overall health rollup.

## Open questions

1. **Block on unclustered verbs?** **Recommend**: warn only (a verb
   may legitimately span clusters or be new and pending
   classification); block ONLY if the unclustered state persists
   across two consecutive PRs to the same verb name (a separate
   stickiness check).
2. **Where does the cluster→capability table live?** **Recommend**:
   derived from the master spec (Spec 047) via a parsed-section
   walk; never hand-maintained. A `<!-- cluster: develop -->` marker
   per section, parsed at audit time.
3. **Promotion thresholds — fixed or learned?** **Recommend**: fixed
   in v1 (the CLAUDE.md rule 5 numbers: 150 LOC, 3 cross-cluster
   refs); revisit only after measured signal — Slice-2 may learn from
   historical promotion events recorded in the graph.
