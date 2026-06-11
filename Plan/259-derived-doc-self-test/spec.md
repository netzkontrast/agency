---
spec_id: "259"
slug: derived-doc-self-test
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "149"
depends_on: ["149", "191", "175", "177", "269", "267"]
vision_goals: [4]
affects:
  - scripts/check-doc-drift
  - tests/test_derived_doc_self_test.py
---

# Spec 259 — derived-doc discipline: self-test

## Why

Spec 149 anchors the drift-derivation chain — TODO/matrix/SkillDoc
derive from the live registry. But does the discipline derive ITSELF?
Today there's no standing proof that a registry mutation propagates
through every derived surface in a single pass. Without that proof,
drift can hide in the gap between two derivers (e.g. TODO updates,
matrix doesn't), and the only signal is a manual audit. The self-test
mutates a fixture capability, runs derive-docs, and asserts every
derived surface (TODO row, alignment matrix Goal status, install
marketplace description, SkillDoc triggers, slash-command family)
updates in lock-step. Standing proof that drift is dead.

## Done When

- [ ] **End-to-end derive-docs self-test** — fixture mutates a test
      capability (add verb, rename verb, remove verb, add ontology
      enum); the test asserts:
      - TODO.md row regenerates with new verb count
      - alignment matrix Goal-mapping updates
      - install surface (Spec 175) reflects new verb
      - SkillDoc triggers re-derive from the new docstring
      - slash-command family (Spec 148) advertises new shortcut
      - per-spec Followup section (Spec 269) refreshes
- [ ] **`check-doc-drift` includes itself** in the audit (meta-coverage)
      — running the script must touch its OWN documentation page; if
      the doc-source hash drifts, the script flags itself.
- [ ] **Typed `DerivationReport` return shape**:
      ```python
      class DerivationReport(TypedDict):
          surfaces_total: int            # N derived surfaces audited
          surfaces_updated: int          # how many actually changed
          surfaces_stale: list[str]      # NAMED stale surfaces
          unmarked_files: list[str]      # missing doc-source marker
          duration_ms: int
      ```
- [ ] **Failure modes are surfaceable** — a partial derivation reports
      WHICH surface fell behind (not a binary green/red). The
      orchestrator can read the report and propose a fix.
- [ ] **Measurable invariants** (computed, not pinned):
      - `surfaces_total == count(derived-files-on-disk)` — discovery
        is live, not a frozen list
      - `len(surfaces_stale) == 0` after a clean derive
      - `surfaces_updated <= surfaces_total` (trivial sanity)
      - mutation in the fixture cap MUST appear in every surface that
        documents that cap (relationship, not a pinned count)
- [ ] Test: full self-test green on the live tree; a deliberate
      sabotaged surface (e.g. stale TODO row) trips and is named in
      `surfaces_stale`.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  fixture capability "demo" with verbs [a, b]; all derived
        surfaces clean (TODO row says "2 verbs", matrix maps a+b to
        Goal 5, marketplace.json lists 2 verbs)
When:   test mutates the fixture to add verb "c" and runs derive-docs
Then:   DerivationReport{surfaces_total: 6, surfaces_updated: 6,
        surfaces_stale: [], unmarked_files: []}
        AND TODO row now says "3 verbs"
        AND matrix maps a+b+c to Goal 5
        AND marketplace.json lists 3 verbs
        AND SkillDoc for "demo" includes c's docstring triggers

Given:  same fixture; test sabotages by writing a stale TODO row by
        hand AFTER derive-docs ran
When:   check-doc-drift runs
Then:   surfaces_stale == ["TODO.md#demo"]; CI fails; report names the
        exact file:line of the drift so the next session can fix it
        without further investigation
```

## Failure modes (Nygard)

| Failure | Self-test response |
|---|---|
| One deriver crashes mid-run | `surfaces_stale` lists every surface downstream of the crash; exit code != 0 |
| Doc-source marker missing on a hand-written doc | `unmarked_files` lists it; `--strict` mode fails CI |
| Fixture mutation doesn't propagate to a surface | The specific surface name lands in `surfaces_stale`; the test prints a unified diff so the gap is obvious |
| Derivation produces churn (no semantic change but bytes differ) | Comparison uses semantic equality (parsed AST / normalized JSON) — not byte equality — to avoid false positives on whitespace |
| Self-coverage gap (check-doc-drift's own doc unmarked) | Meta-coverage catches it; reported as `unmarked_files: ["docs/.../check-doc-drift.md"]` |

## Interconnects

- Spec 149 (parent) — this spec is the standing proof for the parent.
- Spec 191 (alignment matrix) — one of the audited surfaces.
- Spec 175 (install surface derived) — one of the audited surfaces.
- Spec 177 (plugin reference audit) — sibling drift discipline; this
  spec covers DOC drift, 177 covers REFERENCE drift; together they
  span the full surface.
- Spec 269 (per-spec Followup derived) — the most spec-touching of the
  derived surfaces; this self-test covers it.
- Spec 267 (vendoring discipline) — vendored-data drift is a related
  axis; share the `# vendor:` / `<!-- doc-source: -->` marker pattern.
- **Drift-derivation chain** completion (the standing proof layer).

## Open questions

1. **Where does the fixture capability live?** **Recommend**:
   `tests/fixtures/_demo_cap/` — isolated from the live registry,
   loaded only by the self-test via `Engine(extra_capabilities=[...])`.
2. **Should the self-test run on every PR, or weekly?** **Recommend**:
   every PR — drift detection is the whole point; running it weekly
   means a week of drift can accumulate undetected.
3. **How is the doc-source hash stored?** **Recommend**: inline
   `<!-- doc-source-hash: sha256:abc... -->` next to the
   `<!-- doc-source: ... -->` marker; `--update` re-stamps both
   together so they never diverge.
