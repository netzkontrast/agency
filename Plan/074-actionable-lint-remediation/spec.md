---
spec_id: "074"
slug: actionable-lint-remediation
status: done   # Shipped 2026-06-06 (branch claude/spec-074-impl-actionable-lint)
last_updated: 2026-06-06
owner: "@agency"
serves_intent: "intent:fee6c64d"
depends_on: ["016", "019", "054", "067"]
affects:
  - agency/capabilities/plugin/_main.py     # remediation catalog + finding enrichment + lint_explain verb
  - scripts/check-drift                       # open-vs-accepted WARN counts
  - tests/test_lint_remediation.py            # NEW
  - docs/vision/CAPABILITY-AUTHORING.md       # the rework recipes
estimated_jules_sessions: 0
domain: meta
wave: 5
---

# Spec 074 — Prescriptive lint: tell the agent HOW to rework, not just that it's bad

## Why

The lint pipeline (Spec 016/019/067 `_check_*` rules) tells an author/agent WHAT
is wrong (`msg`) and a terse one-line `fix`. It does **not** give a clear,
sufficient recipe for HOW to rework the surface. Facing a `surface_size` WARN, an
agent learns "jules has 22 verbs (> 12)" — a verdict — but not the *steps* to fix
it ("audit for near-duplicates; collapse A+B behind one verb+param; see Spec 070;
e.g. `jules.status` + `status_all` → `jules.status(all=True)`"). A warning should
be an **instruction**, not a judgement.

Two problems compound:
1. **Findings are diagnostic, not prescriptive** — no ordered steps, no doctrine
   reference, no before→after example. The agent has to derive the rework from
   scratch every time.
2. **WARN noise** — a standing/accepted WARN (e.g. the kept-wire-form
   `name_token_budget` from cancelled Spec 069) sits in the same bucket as a
   genuinely-actionable one, so "the WARN count" stops meaning "work to do."

## Done When

- [ ] **Every finding carries a structured remediation.** The finding dict grows
  (additively — existing `{verb, kind, msg, fix}` keys preserved) to
  `{verb, kind, msg, fix, severity, steps: [str, …], reference, example?}`:
  - `steps` — an ordered, concrete rework recipe (the HOW).
  - `reference` — the doctrine section to read (`CAPABILITY-AUTHORING.md §…` or a
    Spec number).
  - `example` — a tiny before→after (optional, where it clarifies).
  - `severity` — `"warn"` | `"block"` | `"accepted"`.
- [ ] **A per-rule remediation catalog** — `_REMEDIATION: dict[kind, {steps,
  reference, example}]` — so messages are consistent + maintainable and each rule
  declares its recipe ONCE. `_check_*` rules look up their kind to enrich findings
  (a small `_with_remediation(finding)` helper) instead of hand-writing `fix`
  strings per site.
- [ ] **`# agency-accept-warn: <kind> <reason>` marker.** A verb/site can accept a
  specific WARN with a recorded reason (mirrors the Spec 058 `agency-skip-link-
  check` marker). Accepted findings move to `severity="accepted"` and a separate
  `accepted` bucket — they DON'T inflate the open-WARN count, but the reason is
  retained (auditable). The standing WARNs from cancelled Spec 069
  (`name_token_budget`, `bare_name_*`) get a documented blanket-accept so the open
  count reflects genuine work.
- [ ] **`plugin.lint_explain(rule: str)`** verb (`transform`) — returns the full
  remediation recipe for a rule kind (`{kind, what, steps, reference, example}`)
  so an agent can ASK "how do I fix a `surface_size`?" and get the recipe without
  tripping it first. Dogfoods the surface (the agent uses agency to learn agency).
- [ ] **`scripts/check-drift`** prints `open` vs `accepted` WARN counts per kind
  (so CI surfaces real work, not accepted noise). Exit code unchanged (WARN-only).
- [ ] **`tests/test_lint_remediation.py`** — a finding carries steps+reference; the
  catalog covers every shipped rule kind; an accept-warn marker moves a finding to
  `accepted`; `lint_explain` returns a recipe; check-drift open/accepted split.
- [ ] **`CAPABILITY-AUTHORING.md`** — a "Rework recipes" section: per rule kind,
  the steps + example (the human mirror of the catalog).
- [ ] `pytest -n auto -m "not e2e"` green; `check-drift` clean.

## Design

### The remediation catalog (single source of the HOW)

```python
_REMEDIATION = {
  "surface_size": {
    "steps": [
      "Audit the capability's verbs for near-duplicates (Spec 070 model).",
      "Collapse each near-duplicate pair behind ONE verb + a discriminating param.",
      "Alias-and-deprecate the old verb names (old → new+param for one minor).",
      "If no duplicates, the surface is genuinely broad — accept the WARN with "
      "`# agency-accept-warn: surface_size <why>`.",
    ],
    "reference": "Spec 070 + CAPABILITY-AUTHORING §Token-economy budgets",
    "example": "jules.status + jules.status_all → jules.status(all=False)",
  },
  "reflection_link": { "steps": [...], "reference": "Spec 058 + CAPABILITY-AUTHORING §Reflection write convention", ... },
  # … one entry per shipped rule kind
}
```

### Why a marker, not a config file

The accept-warn marker lives AT the site (the verb/module), like the Spec 058
skip marker and the Spec 054 drift tags — so the reason travels with the code and
`grep -rn "agency-accept-warn"` inventories every accepted exception. No central
suppression file to drift.

### Severity model (reduces noise without hiding work)

- `warn` — open, actionable; counts as work.
- `accepted` — a WARN with a recorded `agency-accept-warn` reason; surfaced
  separately, not counted as open work.
- `block` — a violation in block mode (existing behaviour).

The cancelled-069 standing WARNs (`name_token_budget`, `bare_name_*`) ship with a
blanket module-level accept (the kept-wire-form reason), so the open-WARN set is
exactly `{surface_size, skill_name_parity}` — the genuine 070/071 work.

## Migration

Additive: the finding dict GAINS keys; the existing `{verb, kind, msg, fix}`
contract is untouched (no consumer breaks). `lint_explain` + the accept-marker are
new; check-drift's split is presentation-only.

## Open Questions

1. **Catalog completeness gate.** A lint rule with no remediation entry is itself
   a (meta) lint smell — add a test asserting every shipped `kind` has a catalog
   entry, so a new rule can't ship a bare verdict. (Resolved: yes, a test.)
2. **Per-finding vs per-kind example.** v1: per-kind example in the catalog
   (consistent, cheap). A per-finding dynamic example (naming the actual offending
   verbs) is a v2 nicety.

## Evidence

- `agency/capabilities/plugin/_main.py` — the `_check_*` family + the terse `fix`
  strings this spec upgrades to structured remediations.
- Spec 058 `agency-skip-link-check` + Spec 054 `AGENCY-DRIFT` tags — the at-the-
  site marker precedent.
- Spec 067 — the token-economy rules whose WARNs most need actionable recipes;
  the cancelled-069 standing WARNs that motivate the `accepted` bucket.
- User directives (2026-06-06): "adjust the linting … add clearer rules and
  instructions for reworking effective surfaces when warning, so the agent gets
  hints what to do — not only that something is bad."


## Followup --- Implementation Status (2026-06-06)

> Shipped on branch `claude/spec-074-impl-actionable-lint`. TDD (RED 7 -> GREEN).
> Chosen by the user as the token-economy cluster CAPSTONE (resolves 070/071's
> residual WARNs honestly).

**Verdict:** Shipped

### Done
- `plugin._REMEDIATION` --- per-rule rework catalog (14 kinds): each
  `{what, steps[], reference, example?}`. The single source of the HOW.
- `_with_remediation(finding)` enriches every finding additively (existing
  `{verb,kind,msg,fix}` preserved) with `{severity, steps, reference, example}`.
- `_STANDING_ACCEPTS` + `# agency-accept-warn: <kind> <reason>` at-the-site marker
  + `_accepted_kinds()` / `_split_accepted()` --- WARNs move to an `accepted`
  bucket (with reason) so the OPEN set is genuine work. `lint_capability` /
  `lint_surface` now return `accepted` alongside `warnings`.
- `plugin.lint_explain(rule)` verb --- returns the recipe so an agent learns the
  fix WITHOUT tripping it (dogfoods the surface).
- `scripts/check-drift` prints OPEN vs ACCEPTED counts.
- CAPABILITY-AUTHORING "Rework recipes" section + `AGENCY-DRIFT: accepted-warns` tag.

### Cluster resolution (the capstone effect)
With the accept mechanism, the live token-economy WARN surface is now **OPEN:
none** --- every WARN is fixed or documented-accepted:
- jules `surface_size` --- accepted at the site (legitimately broad; Spec 070
  audit found only ~3 cosmetic merges).
- `skill_name_parity` (14) --- accepted-tracked (Spec 071 reconciliation).
- `name_token_budget` + `bare_name_*` --- standing-accepted (kept wire form; Spec
  069 cancelled).

### Tests
- `tests/test_lint_remediation.py` --- 7 (enrichment, catalog completeness meta-
  lint, accept marker + standing accepts, open/accepted split, lint_explain). The
  067 + naming-audit snapshots updated for the new `lint_explain` verb (70 verbs)
  and the accepted-bucket split. Full suite 800 passed / 3 skipped; drift clean.
