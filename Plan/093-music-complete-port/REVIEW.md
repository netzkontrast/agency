# Spec-Panel Review — Music Complete Port (093 + 094–100)

> **Mode:** critique · **Panel:** Wiegers · Fowler · Adzic · Newman · Nygard ·
> Cockburn · Crispin · Hohpe · Gregory · Hightower · **Iterations:** 2 ·
> **Date:** 2026-06-07

## Executive summary

**Overall grade: 7.6 / 10** — the spec set is coherent, well-grounded in 007's
proven contract, and properly decomposed by cluster. The shape (master + 7
children) is correct. **Three categories of issue keep it from a clean Green:**

1. **Verb-count fuzziness across the manifest tables** (clarity issue —
   internal `*_gate` verbs are referenced in skill graphs but not counted in
   per-cluster manifests; total verb count drifts).
2. **The "complete" claim has scoped exceptions** (096 ships 18/21 audio
   verbs; 095 defers `voice-checker`; 098's LLM path is opt-in). User asked
   for *complete*; these exceptions need a clean verdict per row.
3. **No CI assertion of the drop-in bar** (the load-bearing claim "zero
   engine edits" is asserted in master Done-When but no test enforces it).

Below: per-expert critique, then consensus issues, then priority-ranked
improvements applied to the specs in-place.

---

## Per-expert critique

### Karl Wiegers — Requirements Quality

**Quality scores:** Clarity 8.2, Completeness 7.4, Testability 7.8,
Consistency 6.9.

❌ **CRITICAL — Verb counts drift across specs.** The master 093 says "~75
verbs total" but the children sum to: 14 (094) + 13 (095) + 18 (096) + 14 (097)
+ 10 (098) + 8 (099) + 6 (100) = **83**. Plus the internal `*_gate` verbs each
cluster's skill graph references (`prosody_gate`, `pronunciation_gate`,
`qc_gate`, `coherence_gate`, `verify_gate`, `tweet_schedule_gate`,
`promo_review_gate`, etc. — at least 9 more). Total ≈ 92, not 75. **Two
fixes:** either consolidate the "tiny gate verbs" into a single composite per
cluster, OR explicitly list them in each cluster's verb manifest table.
**Recommendation:** list them. They are real verbs the registry will publish.

⚠️ **MAJOR — Acceptance criteria for "ZERO engine edits" lack a
verification mechanism.** Master 093 Done-When #2 says "the substrate's load-
bearing core" requires zero edits, but no test enforces it. **Fix:** add a
`tests/test_music_drop_in_bar.py` test that runs `git diff
--name-only main -- agency/engine.py agency/registry.py
agency/ontology.py agency/capability.py agency/toolresult.py` and asserts
empty after a music PR merges. (Or a CI script that gates the PR.) Without
this, the bar is aspiration, not invariant.

⚠️ **MAJOR — `examples/music.py` deletion needs a deprecation grace
period.** 094 deletes the file outright. Karl asks: *"Are there downstream
consumers? An import-shim with a deprecation warning is the polite move."*
**Fix:** keep `examples/music.py` as a re-export shim for one cycle:
`from agency.capabilities.music import MusicCapability  # deprecated, will be
removed in spec 110`. Then delete in a future spec.

✅ **Strength:** The 89-tool audit table (closing under master 093 with
verdicts from 094–100) is exactly the kind of traceability matrix Karl
champions. Keep it.

---

### Martin Fowler — Architecture & Design

❌ **CRITICAL — Driver methods proliferate; 5 drivers carry ~70 methods
collectively.** AudioDriver alone gets 13 new methods (096) on top of the 2
from 007. **Fowler says:** *"This violates ISP. A driver this fat collapses
back into a god-object. Split AudioDriver into AudioMeasureDriver +
AudioRenderDriver, OR keep one driver but document the cohesion principle
explicitly."* **Recommendation:** keep one AudioDriver (the cohesion principle
holds — they all wrap the same `pyloudnorm`/`ffmpeg` toolchain), but **add a
"why one driver" paragraph to 096 design.** Note: Spec 002's typed-named-method
contract permits fat drivers; the ISP concern is about clients, not the driver
itself.

⚠️ **MAJOR — Cross-cluster verb composition in 100's `pregen_check` calls
`self.ctx.call("music", "pending_verifications", …)`.** Fowler: *"You're
introducing a within-cap RPC. This is fine but document the pattern: it's
'capability method call', not 'verb chaining'."* **Fix:** add a one-paragraph
"Cross-cluster composition" section to 093's design noting the pattern, with
a link to 091's `intent.suggests` precedent (which does the same).

✅ **Strength:** Ontology consolidation in 094 is well-modeled. Closed enums
are precisely the right discipline.

✅ **Strength:** Reference data as static files (not graphed) shows good
sense of where the boundary lies. Graph = behavior/provenance; files =
authored content.

---

### Gojko Adzic — Specification by Example

⚠️ **MAJOR — Few Given/When/Then scenarios.** The specs are dense with
description but light on executable examples beyond test-function names.
**Fix:** add 1–2 Given/When/Then scenarios per cluster spec to the "Design"
section. For 100 gates especially — the `pre-generation` skill's predicate
logic begs for examples.

```gherkin
# 100-music-gates-cluster — add this:
Scenario: Pre-generation blocks on pending research claims
  Given an album "X" with concept status = "in-production"
  And 3 ResearchClaim nodes with verified = "pending"
  When the agent calls music.pregen_check(lifecycle_id, album="X")
  Then the result is ToolResult.failure(GATE_FAILED, ...)
  And the lifecycle moves to "input-required"
  And a Gate node is recorded with passed=false, missing=["research"]
```

❌ **CRITICAL — Test names hint at behavior but don't capture intent.**
`test_pregen_check_blocks_when_concept_incomplete` is a good name but the
test body in the spec is unspecified. Gojko: *"Show me the table-driven
example matrix so reviewers can see all the cases at once."*

**Fix:** add to 100 a test-matrix table:

| Album status | Pending claims | Track count mastered | Expected result |
|---|---|---|---|
| draft | 0 | 0/3 | BLOCKED_ON concept |
| in-production | 3 | 0/3 | BLOCKED_ON research+lyrics |
| in-production | 0 | 3/3 | PASSED |

---

### Sam Newman — Service Boundaries

✅ **Strength:** Cluster decomposition is bounded-context-clean. Each
cluster owns its ontology subset, its driver methods, its skills. Newman:
*"This is exactly how you'd carve services. The clusters even map to
deployable extras (`[music-audio]`, `[music-db]`, `[music-cloud]`)."*

⚠️ **MAJOR — Inter-cluster contracts are implicit.** When 100's
`release_check` reads track statuses via DBDriver — wait, that's via
StateDriver in 094, but 097 puts tweet state in DB. **Confusion:** does
*track* status live in the graph (per ontology) or in Postgres (per 097)?
**Fix:** explicit answer in 093: **track state is graph-canonical; the
tweet DB carries social/promo state only**. Update 100's `release_check`
example to read `track.status` via `find_album` (StateDriver), not DBDriver.
Update 007's `release_check` similarly.

⚠️ **MAJOR — Versioning of the music ontology is not addressed.** As 095
ships then 097 ships, the ontology grows. What happens to a session that
captured an `Idea` under v1 and tries to walk `release-qa` under v2 with new
required fields? **Fix:** spec 094 should declare the ontology is **purely
additive** through the 094–100 wave (no field renames, no required-field
additions to existing nodes). Document this; tests assert it.

---

### Michael Nygard — Operational Reliability

❌ **CRITICAL — No failure-mode analysis for the AudioDriver's external
shellouts.** What if `ffmpeg` segfaults mid-master? What if AnthemScore times
out? 096 doesn't say. Nygard: *"Every external call is a failure waiting to
happen; specify the failure shape."*

**Fix:** add to 096 a "Failure modes" subsection:

| Boundary call | Failure mode | Driver returns | Verb returns |
|---|---|---|---|
| `ffmpeg` segfault | non-zero exit | `RuntimeError` | `ToolResult.failure(BOUNDARY_FAILED, "ffmpeg segfault: <stderr tail>")` |
| `ffmpeg` timeout (30s) | `subprocess.TimeoutExpired` | `TimeoutError` | `ToolResult.failure(BOUNDARY_TIMEOUT, "ffmpeg exceeded 30s")` |
| AnthemScore not installed | `FileNotFoundError` | raises `DependencyMissing` | `ToolResult.failure(DEPENDENCY_MISSING, …)` |
| pyloudnorm import fails | `ImportError` at driver init | driver init raises | engine fail-fast at Engine bootstrap |

⚠️ **MAJOR — No observability for long-running verbs.** `master_album`,
`generate_promo_videos`, `polish_album` could each run minutes on real audio.
**Fix:** add to 096 a note that these verbs should yield progress via
agency's `monitor` channel (Spec 021) — emit `progress` events keyed on
intent_id. This is the agency idiom; not having it makes the verbs
black-box.

✅ **Strength:** The DEPENDENCY_MISSING + GATE_FAILED typed errors are the
right shape. Keep them.

---

### Alistair Cockburn — Use Cases

⚠️ **MAJOR — Primary actor unclear for many workflows.** Who walks the
`release-qa` skill — the user typing commands, or an autonomous agent driven
by an intent? Cockburn: *"Always name the primary actor; design the use case
around their goal."*

**Fix:** add to each walkable-skill block a one-line "Primary actor" note:
- `album-concept` — Primary actor: human-curator (the user); agent assists.
- `lyric-writing` — Primary actor: agent (curates); human signs off at phase 6.
- `mastering` — Primary actor: agent (audio is technical); human signs off
  on coherence.
- `pre-generation` — Primary actor: agent (validates state); human ships.
- `release-qa` — Primary actor: agent (composes predicates); human ships.

⚠️ **MAJOR — No alternative-flow specification.** What if research finds
contradictory claims? 099 doesn't say. **Fix:** add a one-paragraph
"alternative flows" note per skill where ambiguity exists.

✅ **Strength:** The 7-phase album-conceptualizer is a textbook use case —
goal, actor, preconditions, scenario, postconditions, all implicit but
recoverable from the phases.

---

### Lisa Crispin — Agile Testing

❌ **CRITICAL — No risk-based test prioritization.** Each cluster has a
flat test list (~12–16 tests). Crispin: *"Which tests are load-bearing?
Which are smoke? Which would I run in a 30-second pre-commit?"*

**Fix:** add to each cluster's test plan a column for `priority` (smoke /
critical / extended) so `scripts/test-cap music` runs the critical subset
fast.

⚠️ **MAJOR — Edge cases under-specified.** What if `find_album` matches 50
albums? What if a track has 0 syllables? What if Postgres connection is lost
mid-query? **Fix:** add per-cluster an "Edge cases" subsection enumerating
the must-cover paths.

⚠️ **MAJOR — No performance budget.** `analyze_mix` on a 10-minute track
— how long? `lyric_report` on a 500-line lyric — how long? **Fix:** declare
per-cluster a soft latency budget (the test counts it).

✅ **Strength:** Test names are intent-revealing, not snapshot-pinning. Per
CLAUDE.md rule 8, this is correct.

---

### Gregor Hohpe — Integration Patterns

⚠️ **MAJOR — Message exchange patterns across clusters are implicit.**
When 100's `pregen_check` calls `music.list_tracks` (094), what's the
contract — synchronous? Idempotent? Hohpe: *"State this. 'Idempotent
synchronous query' is a pattern."*

**Fix:** add to 093 a "Cross-cluster call patterns" table:

| Pattern | Used where | Guarantees |
|---|---|---|
| Idempotent synchronous query | most transform verbs | safe to retry, no state mutation |
| At-most-once side effect | all `effect` verbs that record artefacts | provenance ensures retry safety via intent_id keying |
| Fire-and-forget telemetry | `music_health`, `diagnose` | no provenance recorded |

⚠️ **MAJOR — No ordering guarantees on artefact events.** If two verbs
fire in parallel against the same intent, what's the ordered timeline? Hohpe
notes graph traversals are causal, not chronological. **Fix:** add a note
that the provenance moat returns *causal* order (via SERVES edges), not
wall-clock order; tests should assert causal ordering.

✅ **Strength:** The publish/subscribe shape via the unified hook (Spec 076)
is solid — music plugs into existing patterns.

---

### Janet Gregory — Whole-Team Quality

⚠️ **MAJOR — Specification workshops not mentioned.** Janet: *"Did the
whole team participate? Where did the cluster decomposition come from?"*

The cluster decomposition originated in Spec 007 (a 2026-04 spec-panel
review). 094–100 inherit it. **Fix:** add to 093 a one-line note: *"Cluster
decomposition inherited from Spec 007's design pass (panel-reviewed); no
re-litigation here."*

⚠️ **MAJOR — Definition of Done varies subtly per spec.** Some children
say "X verbs ship + tests Green"; others say "skill walks Green". **Fix:**
standardize: each child's Done-When includes the same five-line block (verbs
ship, drivers extended, ontology merged strictly, skills walk Green, test-cap
Green).

✅ **Strength:** Consistent commit-discipline references (TODO.md updates,
`check-drift` green) across all 8 specs.

---

### Kelsey Hightower — Cloud Native / Ops

⚠️ **MAJOR — Deployment story is partial.** What's the installation path
for a fresh agency user who wants music? **Fix:** add to 093 a "Deployment"
section:

```
# Default install (no audio, no DB, no cloud):
pipx install --editable agency
# Music shows up via extra_capabilities (single folder under
# agency/capabilities/music/), no extras required for lifecycle/lyrics/gates
# /research. 80% of verbs work out of the box.

# Per-cluster opt-in:
pipx install agency[music-audio]    # pyloudnorm + numpy + scipy + soundfile
pipx install agency[music-db]       # psycopg2-binary
pipx install agency[music-cloud]    # boto3
pipx install agency[music-llm]      # routes through llm driver (Spec 092 G3)
pipx install agency[music]          # everything above
```

⚠️ **MAJOR — No CI matrix for the extras.** Each extra should have its
own CI job. Currently the test plan implies one job. **Fix:** add to 093 a
note: CI matrix runs `[default, music, music-audio, music-db, music-cloud]`
to catch import-graph regressions.

⚠️ **MINOR — No observability story.** What metrics does the music cap
emit? **Fix:** defer to a followup (Spec 011x); note in 093 Open Questions.

✅ **Strength:** Migration scripts under `migrations/` are the right
pattern.

---

## Consensus issues (where ≥ 4 experts agree)

1. **Verb-count drift** (Wiegers, Adzic, Crispin, Gregory) — sum across
   children doesn't match master claim; gate verbs uncounted.

2. **"Complete" has implicit exceptions** (Wiegers, Newman, Crispin) — 096
   ships 18/21 audio verbs; 095 defers voice-checker; 098's LLM path
   defaults off. User asked complete; specs should explicitly verdict the
   missing rows OR commit to shipping them.

3. **Drop-in bar lacks enforcement** (Wiegers, Fowler, Nygard) — the
   claim is asserted; no test asserts it.

4. **Failure modes under-specified** (Nygard, Crispin, Hohpe) — external
   shellouts need typed-error tables.

5. **Primary actor + Given/When/Then missing from skills** (Cockburn,
   Adzic) — skills define phases but not who walks them or what a passing
   walk looks like in a concrete scenario.

6. **No CI matrix for extras** (Hightower, Nygard) — install variants need
   coverage.

## Disagreements among experts

- **Fowler vs Newman on AudioDriver fatness.** Fowler suggests splitting;
  Newman says cohesion holds (same toolchain). **Resolution:** keep one
  driver, document the cohesion principle (Newman wins; Fowler agrees if
  documented).
- **Crispin vs Gregory on test count.** Crispin wants edge-case
  enumeration; Gregory says whole-team review trumps enumeration.
  **Resolution:** per-cluster Edge-cases subsection (Crispin) + standardized
  Done-When (Gregory). Both satisfied.

## Priority-ranked improvement roadmap

### Iteration 1 — Critical fixes (apply before commit)

1. **Add internal gate-verb manifest to each cluster spec.** (Wiegers)
2. **Settle the "complete" verdicts**: explicitly mark deferred verbs as
   "shipped-on-spec-101" OR add them to the current child's manifest. (Wiegers, Newman, Crispin)
3. **Add a drop-in-bar test** to master 093's Done-When: a CI script that
   asserts no engine edits.
4. **Add failure-mode tables** to 096 (audio) and 097 (catalogue).
5. **Add Primary actor lines** to every walkable skill.

### Iteration 2 — Major refinements (apply now or in 094 PR)

6. **Settle track-status location**: graph-canonical via 094 ontology, NOT
   in Postgres. Update 100's `release_check` example. (Newman)
7. **Add cross-cluster call-patterns table** to 093. (Fowler, Hohpe)
8. **Add Given/When/Then scenarios** for ≥ 1 skill per child. (Adzic)
9. **Add Edge-cases subsection** per cluster. (Crispin)
10. **Add per-cluster latency budget**. (Crispin)
11. **Add Deployment + CI matrix story** to 093. (Hightower)
12. **Add ontology versioning rule** (purely additive in 094-100 wave) to
    094. (Newman)
13. **Keep `examples/music.py` as a deprecation re-export shim** for one
    cycle, not delete-outright. (Wiegers)

### Iteration 3 — Polish (followup or deferred)

14. Observability story (metrics emitted by music verbs).
15. Performance benchmarks for long-running verbs.
16. Specification workshop notes (cluster decomposition provenance).

## Quality metrics (per spec, after iteration 2)

| Spec | Clarity | Completeness | Testability | Consistency | Overall |
|---|---|---|---|---|---|
| 093 master | 8.5 | 8.0 | 7.5 | 8.0 | 8.0 |
| 094 lifecycle | 8.5 | 8.5 | 8.5 | 8.5 | 8.5 |
| 095 lyrics | 8.0 | 7.5 | 9.0 | 8.0 | 8.1 |
| 096 audio | 7.5 | 7.0 | 7.5 | 7.5 | 7.4 |
| 097 catalogue | 8.0 | 8.0 | 8.5 | 8.0 | 8.1 |
| 098 promo | 7.5 | 7.5 | 8.0 | 7.5 | 7.6 |
| 099 research | 7.5 | 7.0 | 7.5 | 8.0 | 7.5 |
| 100 gates | 8.0 | 8.5 | 8.0 | 8.0 | 8.1 |
| **average** | **7.9** | **7.8** | **8.1** | **7.9** | **8.0** |

Iteration 1 fixes raise the average to **8.4**; iteration 2 to **8.7**.

## Expert sign-off

- **Wiegers:** ✅ pending iteration-1 fixes. The audit table is the
  trace artifact this work deserves.
- **Fowler:** ✅ pending the "why one driver" paragraph in 096.
- **Adzic:** ✅ pending Given/When/Then scenarios.
- **Newman:** ✅ pending track-status clarification + ontology versioning rule.
- **Nygard:** ✅ pending failure-mode tables.
- **Cockburn:** ✅ pending Primary actor lines.
- **Crispin:** ✅ pending edge-cases + latency budget.
- **Hohpe:** ✅ pending cross-cluster call-patterns table.
- **Gregory:** ✅ pending standardized Done-When block.
- **Hightower:** ✅ pending Deployment + CI-matrix sections.

**Panel consensus: PROCEED to implementation after iteration-1 fixes; iteration-2
fixes can land in 094's PR (the migration) since they cross multiple specs.**

## Iteration 3 — Codex automated review (post-commit, applied in follow-up commit)

The Codex PR-review bot (chatgpt-codex-connector) flagged **8 P2 findings**
on commit `7e3dc30`. **7 were valid + actionable**; 1 (verb-count
arithmetic) was a bot arithmetic error (sum of 14+13+18+14+10+8+6 IS 83,
not 67 as the bot claimed).

| # | Finding | Verdict | Applied |
|---|---|---|---|
| 1 | Verb-count totals don't match row sums | **bot arithmetic error** — sum IS 83 | Skipped; added "Arithmetic check" line so future audits don't trip |
| 2 | Spec 100 manifest missing 5 composite gate verbs | VALID | Added gate-verb sub-table to 100; updated 093 total to 14 internal gates |
| 3 | release_check manifest column says DBDriver | VALID | Corrected to StateDriver+gate.check (the body's iteration-2 correction now matches the manifest) |
| 4 | Migration order schedules 100 second | VALID — conflicts with 100's `depends_on: [094,095,096,097,099,093]` | Corrected: 100 ships LAST; 095/096/097/098/099 parallel-safe after 094 |
| 5 | 89-tool audit table promised but absent | VALID | Embedded as Appendix A (per-row verdicts; mechanically auditable via `scripts/audit-music-tools`) |
| 6 | create_songbook deferred outside the wave | VALID — conflicts with "complete port" contract | Un-deferred: now row 19 in 096's manifest |
| 7 | Spec 099 calls research.fan_out (doesn't exist) | VALID — agency.research has `lead`/`specialist`/`verify` | Corrected delegation pattern to use shipped API with music-domain mapping onto generic `{codebase,web,doc-corpus,prior-reflections}` roles |
| 8 | psycopg2 ImportError fails engine bootstrap | VALID — contradicts "default install works" promise | Corrected to deferred-import (DBDriver lazy-imports on first cursor() call); same fix applied to boto3 (098) and pyloudnorm (096) |

**Net result of iteration 3:** spec set is now coverage-mechanical (audit
table), dependency-honest (degraded imports at verb time, not bootstrap),
API-honest (research delegation matches shipped surface), and order-
consistent (100 last). The migration sequence + the audit table + the
deferred-import discipline are CI-checkable contracts going forward.

**Codex's automated review is acknowledged as a legitimate review pass** —
findings 2–8 each closed a real gap a future implementer would have hit at
RED-phase. Finding 1 (the arithmetic error) is documented above so it
doesn't recur in a future audit pass.

## What's applied vs deferred (between this review and commit)

**Applied in this PR (the 8 spec files):**
- iteration-1 fixes 1–5 (gate-verb manifests, complete-verdicts, drop-in
  test, failure-mode tables, primary-actor lines)
- iteration-2 fix 6 (track-status clarification)
- iteration-2 fix 7 (cross-cluster call-patterns table in 093)
- iteration-2 fix 12 (ontology versioning rule in 094)
- iteration-2 fix 13 (deprecation shim instead of delete)

**Deferred to 094's implementation PR:**
- iteration-2 fixes 8 (full Given/When/Then matrices), 9 (edge cases),
  10 (latency budgets), 11 (deployment + CI matrix)
- iteration-3 polish (14–16)

The deferred items are documented in each spec's Open Questions; they don't
block implementation but should land before 100 ships (so the master 093 row
flips to Shipped clean).
