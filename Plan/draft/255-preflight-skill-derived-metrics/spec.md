---
spec_id: "255"
slug: preflight-skill-derived-metrics
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "145"
depends_on: ["145", "149", "150", "170", "146", "245", "248", "251"]
vision_goals: [6, 4]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_preflight_metrics.py
---

# Spec 255 — preflight: derived metrics + dogfood-fed warnings

## Why

Spec 145 ships `novel-preflight` (5-phase read-only audit, <200ms on
40-chapter graph). Its `verdicts` payload is hand-shaped; over time
recurring `warnings` reveal drift patterns. Per Spec 149 the verdict
structure should derive from the audit verbs (any new audit
auto-appears). Per Spec 150 recurring warnings become amendment
proposals.

## Done When

- [ ] **Verdict structure derived from registered audit verbs** —
      typed return `PreflightReport{ novel_id, verdicts: dict[PhaseId,
      PhaseVerdict{status: Literal["pass","warn","fail"], findings:
      list[Finding], duration_ms: int}], total_duration_ms: int,
      audit_verb_set_hash: str, generated_at: datetime }`. The
      `verdicts` dict keys derive from `registered_audit_verbs` at
      call time — adding a 6th preflight phase auto-extends the dict
      with no preflight-module edits.
- [ ] **Invariant: derivation parity** — `set(report.verdicts.keys())
      == registered_audit_verbs()`; assertion runs in test and at
      runtime (with a debug flag). A new audit verb auto-appears;
      a removed one auto-disappears.
- [ ] **Invariant: <200ms wall-clock on a 40-chapter graph** preserved —
      `total_duration_ms < 200` on the standard fixture; relationship
      `total_duration_ms <= sum(verdicts[p].duration_ms) + epsilon`
      (no hidden overhead). Test runs against a fixture of pinned
      shape, never a pinned exact ms.
- [ ] **Invariant: no LLM in the loop** — preflight is GRAPH-ONLY by
      doctrine; test asserts zero AnthropicDriver invocations during
      a preflight run (Spec 147 driver-call counter == 0).
- [ ] **Invariant: recurring warnings classify structurally** — a
      warning recurring `>= N` times (default N=3) across scenes
      WITH the same `(phase_id, finding.category)` mints a Spec 150
      amendment proposal; relationship `proposals_minted ==
      count(recurring_clusters)`.
- [ ] **`agency_doctor` reports preflight readiness** (Spec 170) — for
      a given novel, every registered audit verb has a wired source
      (graph nodes present); readiness = `wired / total`.
- [ ] **Failure modes**: missing graph nodes for a phase → verdict
      `status="warn"` with `category="missing_substrate"`, NOT crash;
      duration overrun (>200ms) → still returns full report + emits
      `Codes.PREFLIGHT_SLOW` (Spec 151), the user sees it; concurrent
      preflight on same novel → idempotent (same node-set, same
      report); audit verb raises → phase verdict marks `status=
      "fail"` with the exception text, other phases continue.
- [ ] Test: a 6th phase auto-extends; 3× warning becomes a proposal;
      LLM-driver invocation counter is zero; 40-chapter fixture
      completes under 200ms.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a novel with 40 chapters, 5 registered preflight phases;
        the user adds a 6th audit verb "check_plural_canon_drift"
        (via Spec 248 query) that produces a warning when alter
        roster diverges from canon; this warning fires on 4 scenes
        across the novel with the same category
When:   novel-preflight runs; then a second run after the warning
        fires 4 times across the run history
Then:   report.verdicts has 6 keys (auto-extended), including the
        new phase; total_duration_ms < 200; verdicts[
        "check_plural_canon_drift"].findings contains 4 entries;
        the recurring cluster (4 >= N=3) mints a Spec 150 amendment
        proposal suggesting a canon Lock refinement (Spec 247);
        the LLM-driver counter remains 0 (graph-only doctrine
        preserved)
```

## Interconnects

- **Drift-derivation chain** (149) — verdict structure derives from
  the registry; preflight stays in sync with the audit-verb set.
- **Dogfood-loop chain** (150) — recurring warnings → amendments.
- Spec 170 (`agency_doctor`) — preflight readiness reported.
- Spec 145 is the parent.
- **Output-budget chain** (146) — report payload obeys envelope;
  per-phase findings cursored on large novels.
- Spec 248 (plural-character query) — a natural source of new
  audit verbs (canon-drift detectors).
- Spec 245 (sensitivity managed) — sensitivity findings are NOT
  preflight inputs (Driver-mediated), but recurring sensitivity
  warnings may suggest new graph-only audit verbs to add.
- Spec 251 (chapter briefing render) — preflight verdict is a
  decidable section in the briefing.

## Open questions

1. **Recurrence threshold N.** Project-configurable? **Recommend**:
   yes — default N=3, override per-project. Sensitivity-heavy
   projects may want N=2 to surface faster.
2. **Phase ordering.** Allow audit verbs to declare ordering, or
   parallel-safe? **Recommend**: parallel-safe by default; serial
   only when a verb declares `requires: [other_phase]` — most
   audits are independent.
3. **Slow-phase budget.** Per-phase ms budget, or only total?
   **Recommend**: both — each phase declares `max_ms` (default
   50ms); total has the 200ms hard cap. A slow phase surfaces
   `Codes.PREFLIGHT_SLOW` naming the phase.

## Followup — Implementation Status (IMPLEMENTED 2026-07-02, PR #328)

Shipped as a rewrite of `agency/capabilities/novel/clusters/preflight.py` —
TDD, 7 tests in `tests/test_preflight_metrics.py` (legacy Spec-145 suite
`tests/test_novel_preflight_skill.py` stays green).

**Done:**
- `@preflight_phase(phase_id, label, source_labels)` decorator + registry
  scan over the composed capability's MRO — the five Spec-145 audits are now
  registered phases; the verdicts dict derives from the registry at call
  time. A 6th phase attached anywhere on `NovelCapability` auto-appears
  (tested); removal auto-disappears and changes `audit_verb_set_hash`.
- Derivation parity: `set(verdicts) == audit_verbs` asserted in test and at
  runtime under `debug=True`.
- Per-phase `duration_ms` + `total_duration_ms`; no-hidden-overhead
  relation (`total <= sum(phases) + epsilon`); 40-chapter fixture under the
  `PREFLIGHT_BUDGET_MS=200` tunable. Overrun emits a `Codes.PREFLIGHT_SLOW`
  warning — full report always returned.
- Graph-only invariant: counting fake drivers registered under every
  plausible name record zero calls during a run.
- Failure isolation: a phase that raises marks `status="fail"` with the
  exception text; all other phases continue.
- Recurrence → amendment feed: each run stores a `findings_index` on the
  pre-flight Artefact; a `(phase, category)` recurring `>= RECURRENCE_N=3`
  across the novel's run history mints ONE `scope="observation"` Reflection
  (`kind="preflight-recurrence"`) — the Spec-150 `parse_amendment` feed —
  idempotently (already-reflected clusters never re-mint).
- `novel.preflight_readiness(novel_id)` — wired/total per phase from the
  declared `source_labels` (RevealRule / ProjectRule / ModeBlock /
  VoiceProfile presence).

**Still open (deferred):**
- `agency_doctor` integration (Spec 170) — readiness ships as a novel verb;
  surfacing it inside the doctor report is the 170 slice.
- Open Q2 phase ordering (`requires:` declarations) unimplemented — all
  phases run serially in declaration order; revisit if a phase gains a
  dependency.
- Per-phase `max_ms` budgets (Open Q3) — only the total budget ships;
  per-verdict `duration_ms` already names the slow phase.
