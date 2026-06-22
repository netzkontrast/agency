---
spec_id: "247"
slug: canon-locks-managed-approval
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "137"
depends_on: ["137", "150", "147", "176", "146", "245", "243"]
vision_goals: [2, 6]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_canon_locks_approval.py
---

# Spec 247 — canon locks: approval workflow + dogfood pipe

## Why

Spec 137 ships CANON_STATUS + Lock + the source-hierarchy + canon-gate.
Today `set_canon_status` and `record_lock` are one-call writes. Real
projects need an APPROVAL workflow (propose → review → canon) that
mirrors the [V]→[K] discipline. With Spec 176 SessionStart capture +
Spec 150 dogfood loop, approval requests become tracked Intents that
classify into amendment proposals if approved → applied.

## Done When

- [ ] **`propose_canon(scope, payload, rationale) -> CanonProposal`** and
      **`approve_canon(proposal_id, approver, decision) -> CanonDecision`** —
      typed shapes `CanonProposal{id, scope: ScopeRef, payload: dict,
      rationale: str, source_hierarchy_tier: Literal["V","K","author"],
      status: Literal["proposal","approved","rejected","superseded"],
      proposed_at, proposed_by}` and `CanonDecision{proposal_id,
      decision: Literal["approve","reject"], lock_id: LockId | None,
      decided_by, decided_at, dogfood_reflection_id: ReflectionId}`.
      Approval is the ONLY path to mint a [K] Lock; rejection records
      a Reflection with the reason.
- [ ] **Invariant: approval is monotonic** — a proposal in
      `status="approved"` cannot revert; supersession mints a NEW
      proposal that references the prior `lock_id`. Property test
      asserts `status` only transitions along the legal DAG
      (proposal→approved | proposal→rejected | approved→superseded).
- [ ] **Invariant: Lock provenance is queryable** — every Lock carries
      `proposed_by + approved_by + proposal_id`; relationship
      `count(Locks) == count(approved proposals)` across the session.
      No Lock exists without a CanonProposal ancestor.
- [ ] **Invariant: source-hierarchy gate enforced at propose-time** —
      a `source_hierarchy_tier="K"` proposal MUST cite an approved
      [K] Lock as evidence; `tier="V"` proposes against a recorded
      [V] source; tier="author" requires explicit author override.
      Relationship: `all(p.evidence != None for p in K-tier proposals)`.
- [ ] **Approval requests as captured Intents** (Spec 176) — every
      `propose_canon` mints an Intent SERVING the proposal; the Intent
      survives the proposal's lifecycle (provenance moat).
- [ ] **Amendments via Spec 150** — recurring proposal/rejection patterns
      (e.g. "same scope keeps proposing-rejecting") classify into
      amendment proposals for the rule that keeps triggering them.
- [ ] **Failure modes**: approver lacks authority for scope →
      `Codes.APPROVAL_DENIED` (Spec 151) with required-role surfaced;
      proposal payload schema mismatch → reject + log to Spec 150 (the
      schema needs work); concurrent approve on same proposal →
      idempotent (first approval wins, second returns the existing
      decision); Driver-mediated proposal (via Spec 245/250) with
      malformed evidence → reject without minting a Lock.
- [ ] Test: full propose→approve→canon flow on a fixture; rejected
      proposal records Reflection; superseded approval keeps lineage.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a project with the "magic-system-no-resurrection" rule in
        canon at [V] tier; a sensitivity finding (Spec 245) recurring
        across 3 scenes proposes promoting it to [K]
When:   propose_canon(scope="magic-system", payload={...},
        rationale="3× recurrence", source_hierarchy_tier="K",
        evidence=[lock-id-V-007]) is called; the lead author calls
        approve_canon(proposal_id, decision="approve")
Then:   a CanonDecision is recorded with lock_id=K-013;
        Lock(K-013).proposed_by + approved_by are queryable; the
        scene-writer (252) now sees the [K] Lock; a Spec 176 Intent
        captures the approval moment; concurrent re-approve returns
        the same decision idempotently
```

## Interconnects

- **Dogfood-loop chain** (150) — proposal/rejection patterns become
  amendments; rejected proposals are signal, not noise.
- Spec 176 (intent capture) — every proposal mints a serving Intent.
- Spec 137 is the substrate (source hierarchy + Lock minting).
- **LLM-driver chain** (147) — Driver-mediated proposers (245, 250,
  243) all flow through this approval gate.
- **Output-budget chain** (146) — proposal payloads obey the response
  envelope; proposal lists are cursored for large sets.
- Spec 245 (sensitivity managed) and Spec 243 (structure anchors) are
  major upstream proposers; their `proposal` outputs feed propose_canon.

## Open questions

1. **Approval quorum.** Single approver, or N-of-M for high-tier? 
   **Recommend**: single-approver by default with a per-scope
   `quorum_policy` overridable to N-of-M for `tier="K"` proposals on
   sensitive scopes (sensitivity findings, plural-character canon).
2. **Auto-expire stale proposals.** Time-out unaccepted proposals?
   **Recommend**: derive — a proposal with no decision after the
   project's configured `proposal_ttl_days` flips to
   `status="lapsed"` (not rejected); the proposer can re-propose.
   Lapsed proposals are signal for Spec 150 (rule too noisy / wrong
   approver routed).
3. **Driver-as-approver.** May a Managed-Agent ever approve?
   **Recommend**: no — approval is human-only by doctrine; the Driver
   may propose, never approve. A test asserts `approver.kind !=
   "managed_agent"` across the corpus.
