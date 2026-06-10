---
spec_id: "267"
slug: substrate-vendoring-discipline
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "060"
depends_on: ["060", "174", "129", "133"]
vision_goals: [4, 7]
affects:
  - agency/_templates/
  - scripts/check-vendoring
  - tests/test_vendoring_discipline.py
---

# Spec 267 — substrate vendoring discipline

## Why

Spec 060 + Spec 174 close template/schema coverage. As enhancements
land, MORE vendored data accumulates (KP fragments 143, structure
templates 133, Dramatica fragments 129, rubrics). Each carries
provenance ("vendored from X, date Y") that's hand-maintained. The
discipline: every vendored file has a `# vendor:` header → check-drift
extension audits sources still exist + versions match.

## Done When

- [ ] **`# vendor: <source> <date>` header** required on every
      `data/*` file.
- [ ] **`scripts/check-vendoring`** asserts sources accessible (URL or
      git ref) + content hashes match documented vendor versions.
- [ ] **Updates produce supersede records** — vendored data has the
      same canon-status discipline as story-canon (Spec 137).
- [ ] Test: missing vendor header trips audit; stale vendor warns.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 060/174 (template substrate); Spec 137 (canon-status applied to
  data files).
- **Drift-derivation chain** for vendored data.
