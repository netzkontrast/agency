---
spec_id: "250"
slug: project-rulesets-llm-author
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "140"
depends_on: ["140", "147", "150", "183", "146", "245", "247", "249"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_project_rulesets_author.py
---

# Spec 250 — project rulesets: LLM-authored R-rules

## Why

Spec 140 ships ProjectRule + 4 predicate kinds (mutual-exclusion,
per-scene-budget, forbidden-verbatim, register-forbidden) + the
R-rule registry. Authoring an R-rule from a recurring defect is
exactly the dogfood loop (Spec 150) + opportunity detector (Spec 183)
applied to prose: a recurring sensitivity or voice finding becomes a
proposed R-rule. The Driver authors the rule params; the author confirms.

## Done When

- [ ] **`suggest_r_rule(novel_id, source_findings: list[FindingRef]) ->
      RRuleProposal`** — typed return `RRuleProposal{ rule:
      ProjectRule{predicate_kind: Literal["mutual_exclusion",
      "per_scene_budget","forbidden_verbatim","register_forbidden"],
      params: dict, scope: ScopeRef}, source_findings: list[FindingRef],
      coverage: {caught: int, total: int, fraction: float}, status:
      Literal["proposal"], driver_model: str }`. Driver composes the
      predicate + params; output flows through `propose_canon`
      (Spec 247) for approval before registering.
- [ ] **Invariant: predicate_kind is closed set** — derived from the
      4 kinds Spec 140 registered; new kind = registry edit, not
      Driver hallucination. Test asserts Driver output is REJECTED
      if `predicate_kind` is unknown.
- [ ] **Invariant: coverage is computed against the source findings
      pre-registration** — `proposal.coverage.fraction = caught /
      total` where `caught` is found by running the proposed rule
      against the source findings as fixtures. Relationship:
      `coverage.fraction >= MIN_COVERAGE` (default 0.8) gates
      surfacing the proposal — under-fitting rules are never proposed.
- [ ] **Invariant: source-findings traceability** — every proposal
      carries the ≥ N findings it was authored from; rejection by
      author records WHICH findings were misclassified (Spec 150
      feedback).
- [ ] **`run_project_rules` validates** the new rule against the
      source findings AND against a held-out validation slice (other
      scenes in the novel) — over-broad rules show false-positive
      rate; surfaced in the proposal.
- [ ] **Failure modes**: Driver proposes a `forbidden_verbatim` with
      a too-short pattern (< 3 tokens) → reject + log to Spec 150
      (signal: the rule kind is too coarse); coverage < MIN_COVERAGE
      → proposal surfaces as `status="proposal_under_threshold"`,
      author can force-approve; Driver REFUSAL on sensitivity-
      sourced findings → return zero proposals, dogfood the reason;
      register-forbidden rule that contradicts an existing R-rule →
      conflict flagged via `run_project_rules` before propose_canon.
- [ ] Test: 5× recurring finding → proposed R-rule that catches the 5
      instances + 0 false positives on a held-out slice (mocked).
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  6 sensitivity findings (Spec 245) across 4 scenes, all
        flagging the verbatim phrase "wheelchair-bound" with
        category="disability"; held-out slice contains 12 scenes
        with no such phrase
When:   Spec 183 opportunity-detector pipes the 6 findings into
        suggest_r_rule(novel_id, findings); Driver composes a
        ProjectRule{predicate_kind="forbidden_verbatim",
        params={pattern: "wheelchair-bound"}, scope=novel}
Then:   proposal.coverage = {caught: 6, total: 6, fraction: 1.0};
        held-out false-positive rate = 0/12; status="proposal";
        flow routes through Spec 247 propose_canon; on approval,
        the R-rule registers and run_project_rules catches future
        instances automatically
```

## Interconnects

- **Dogfood-loop chain** (150) — the loop that mints R-rules from
  findings is THIS spec; recurring rejections of proposals also
  feed the loop (the kind taxonomy might need extending).
- Spec 183 (opportunity detector) — upstream signal source.
- **LLM-driver chain** (147) — Driver authors predicate + params.
- Spec 245 (sensitivity managed), Spec 249 (veil LLM) — primary
  finding sources; their `proposal` findings cluster into R-rule
  candidates here.
- Spec 247 (canon-lock approval) — R-rule proposals flow through
  the canon approval workflow; author confirms before registration.
- **Output-budget chain** (146) — finding-cluster context obeys
  envelope; the rule-kind taxonomy sits in cacheable prefix.

## Open questions

1. **Minimum source-finding threshold.** Cluster size to trigger
   suggestion? **Recommend**: default N=3 distinct scenes (NOT 3
   findings — repeat findings in one scene aren't a pattern); make
   it per-project configurable.
2. **MIN_COVERAGE threshold.** What fraction of source findings
   must a proposed rule catch to surface? **Recommend**: 0.8 — leaves
   room for one outlier without forcing the rule to over-fit.
3. **Multi-rule composition.** May a single proposal bundle multiple
   ProjectRules? **Recommend**: no — one proposal, one rule. Bundles
   obscure approval; the dogfood loop loses per-rule signal.
