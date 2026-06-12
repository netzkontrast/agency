---
spec_id: "165"
slug: micro-extensions-closure
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "046"
depends_on: ["046", "081", "079", "149"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/branch/_main.py
  - agency/capabilities/develop/_main.py
  - tests/test_micro_extensions_closure.py
---

# Spec 165 — Micro-extensions closure

## Why

Spec 046 (micro-extensions-bundle) is Partial — F-C (`branch.commit_smart`)
+ F-D (`develop.estimate`) shipped, but "F-A/B/E/F (skill content +
scripts) superseded/deferred under the derive model". Rather than leave
them dangling, this spec resolves each deferred fragment explicitly:
either derive it (080/081) or formally cancel it with a pointer, so the
046 row reads clean.

## Done When (measurable invariants — rule 8)

- [ ] **Typed verdict shape: `FragmentVerdict{fragment_id, verdict:
      Literal["derived", "cli_folded", "cancelled"], pointer: str |
      None, resolved_at: timestamp}`** — every 046 fragment carries one;
      stored as a graph node SERVES Spec 046.
- [ ] **Invariant: `{F-A, F-B, F-C, F-D, F-E, F-F} == set(verdicts.fragment_id)`** —
      the verdict set equals the declared fragment set; derived from the
      live graph, not pinned.
- [ ] **Invariant: every `derived` verdict has a live SkillDoc** —
      `branch.commit_smart` + `develop.estimate` SkillDocs derive
      byte-equal under Spec 080/081 (derivability audit, CLAUDE.md
      rule 2).
- [ ] **Invariant: every `cli_folded` verdict maps to a live `agency
      <cap> <verb>`** — `pointer` resolves under the Spec 079 CLI mirror.
- [ ] **Invariant: every `cancelled` verdict carries a non-empty
      `pointer`** — no silent dangling; a cancellation must point at the
      replacement or the rationale.
- [ ] **Relationship: 046 TODO row flips Shipped/Closed iff
      `len(verdicts) == 6`** — derived status, Spec 149.
- [ ] **Failure mode:** a fragment without a verdict at audit time fails
      `Codes.FRAGMENT_UNRESOLVED` (Spec 151); a verdict with a stale
      pointer (the verb/CLI no longer exists) fails
      `Codes.FRAGMENT_POINTER_STALE`.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  046 fragments F-A..F-F; F-C + F-D shipped; F-A/B/E/F pending
When:   `agency analyze fragments --spec 046` runs the audit
Then:   returns 6 FragmentVerdicts; F-C/D = "derived" with live SkillDoc
        pointer; F-A/B = "cli_folded" with `agency <cap> <verb>` pointer;
        F-E/F = "cancelled" with rationale pointer naming Spec 079
        as the replacement surface

Given:  later, branch.commit_smart verb deleted
When:   audit reruns
Then:   F-C verdict trips Codes.FRAGMENT_POINTER_STALE — the live verb
        no longer exists, the verdict is stale; CI fails the drift gate
```

## Failure modes

| Failure | Audit response |
|---|---|
| Fragment without a verdict | `Codes.FRAGMENT_UNRESOLVED` — block 046 close |
| Verdict pointer no longer resolves | `Codes.FRAGMENT_POINTER_STALE` — drift fail |
| `derived` verdict but SkillDoc differs from docstring | Spec 163 derivability lint fails |
| `cli_folded` verdict but CLI command missing | Spec 079 mirror audit fails |

## Interconnects

- **Drift-derivation chain** (149) — verdicts derive from the live
  registry; no hand-maintained TODO row state.
- Spec 079 (CLI mirror) + Spec 081 (walkable skills) are the
  resolution surfaces.
- Spec 163 (progressive-disclosure closure) supplies the SkillDoc
  derive engine that `derived` verdicts depend on.
- Spec 175 (install-surface derived) consumes the verdict set for the
  README capability row of `branch` + `develop`.
- Spec 151 (Codes coverage) supplies `FRAGMENT_UNRESOLVED` +
  `FRAGMENT_POINTER_STALE`.
- Spec 174 (template verb-migration closure) is the sibling
  closure-of-a-partial pattern.

## Open questions

1. Cancel or implement F-E/F? **Recommend**: decide per fragment from
   the live graph (is anything calling for it via `analyze.graph
   call-sites`?); default cancel-with-pointer absent a consumer.
2. Where do verdicts live? **Recommend**: as graph nodes (Verdict label,
   SERVES Spec 046, PRODUCED_BY the audit verb) — survives the session,
   queryable by drift, doctrine rule 2.
3. Audit cadence? **Recommend**: on every spec-touching commit (CI hook,
   Spec 149) + on demand via the `analyze fragments` verb.

## Followup — Implementation Status (Slice 1, 2026-06-12)

**Verdict:** Slice 1 SHIPPED on `claude/autonomous-completion`.

The typed shape this spec carries was shipped as part of the wave-1+2
batch (intents trackable in graph). See TODO.md row + the corresponding
test module under `tests/`.

