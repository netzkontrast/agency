# Spec-Panel Review — Brooks-Lint Port Program (371–377)

`/sc:sc-spec-panel` · critique mode · 10 experts · 2026-06-20. Consolidated
scorecard + disagreements + the fold status. Per-fix detail lives in each child's
`## Followup` "Amended" note; this file is the cross-spec record.

## Scorecard

| Dimension | Score | After-fold |
|---|---|---|
| Requirements quality | 7.5 | gate predicate + "leverage" now defined |
| Architecture clarity | 7.0 | review/remediate split + headless twin + merge contract |
| Testability | 7.0 | language matrix + det/wet split + fixtures + per-mode |
| **Operational readiness** | **5.5** | **the hardening target** — keyless CI, graph cache, SARIF cap, override, partial-walk |
| Completeness | 6.5 | migration → Spec 377; vendored-data `_source` |
| **Overall** | **6.8** | all immediate blockers folded |

## Findings → fold status

| # | Sev | Expert | Finding | Folded into |
|---|---|---|---|---|
| 1 | 🔴 | Fowler | `review(fix=bool)` can't switch a static `@verb(role=)` | 372 §3/§4 — split `review`/`remediate` |
| 2 | 🔴 | Wiegers | Iron Law gate had no measurable predicate | 354 §1 + 372 §2 — `all(f.consequence and f.remedy)` |
| 3 | 🔴 | Hightower | trend broken in ephemeral CI (fresh graph) | 373 §3 + 374 §3 — base-branch `.agency` cache |
| 4 | 🔴 | Crispin | Python-only decidable regression, unstated | 372 §3c — stated language matrix |
| 5 | ⚠️ | Cockburn+Hightower | two actors (human/CI) collapsed | 372 §3a — `analyze.review` headless twin |
| 6 | ⚠️ | Hohpe | decidable→judgment merge unspecified (double-count) | 354 §3 + 372 §3b — join key + enrich-in-place |
| 7 | ⚠️ | Hightower | LLM credential/cost in CI unspecified | 374 §3 — keyless decidable-only degradation |
| 8 | ⚠️ | Nygard | mid-walk failure / SARIF size / wedged PR | 373 §3 + 374 §3 — `status:incomplete`, `--max-results`, override |
| 9 | ⚠️ | Newman | no migration; asymmetric vendored-data versioning | **Spec 377** + `_source` on 354/375 data |
| 10 | ⚠️ | Adzic | scenarios illustrative, not executable | 375 §2 — fixture-backed scenarios |
| 11 | ⚠️ | Crispin | wet-LLM scenarios would flake the PR gate | 375 §2 — `-m wet` tag split |
| 12 | ◽ | Wiegers | "highest-leverage" undefined | 373 §1 — `deduction_weight × occurrence_count` |
| 13 | ◽ | Gregory | ~14 OQs deferred unilaterally | blocking OQs resolved (371-OQ3, 374-OQ1/2); rest ride their slice |

## Disagreements (and resolutions)

- **Fowler vs the spec's own §4** (one `review(fix=)` verb): *resolved to split* — the role tag is static, so it was not stylistic but a correctness bug.
- **Adzic vs Crispin** (executable examples in the gate vs flakiness): *resolved by altitude* — concrete fixtures for the **decidable** half (deterministic, in the gate); `-m wet` tag for the **judgment** half.
- **Newman vs Wiegers** (version-later vs resolve-now on OQs): *resolved* — close the 3 critical-path OQs now, defer the rest.
- **Hightower vs Cockburn/Crispin** (ship py-first vs don't-regress-any-language): *resolved as a documented v1 limitation* — judgment stays language-agnostic, only decidable tagging is py-first, with an evolution path. (The one product-call; flagged for owner override.)

## Architecture verdict

Re-examined per owner request: the home decomposition (`analyze` engine ·
`develop` seam · `intent` triage · `gate` quality gate · templates in
`analyze`/`develop`) **holds**. The actor split resolved onto the existing twin
shape, so the changes are refinements, not a rebuild. One genuine correctness fix
(Fowler's role split); the rest hardened the operational axis.
