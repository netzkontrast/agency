---
spec_id: "092"
slug: substrate-hardening-and-authoring-guardrails
status: shipped
state: done
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["054", "080", "081", "002"]
domain: meta / substrate
wave: 6
research_first: false
---

# Spec 092 — Substrate hardening & authoring guardrails

## Why

This generation shipped ~15 capability/feature PRs (002 DriverRegistry · 026 skills
capability · 080–084 Agent Skills + TokenCounter + Skills-API + `analyze.graph` · 007
music · 091 `intent` · complete docs + doc-drift · 006 hardening). Building them surfaced
**six recurring tool/substrate frictions** that each cost a debug cycle or leave a
dormant surface. The **drop-in-capability bar** (CLAUDE.md: "add a folder, nothing else")
is the north star — this spec closes the gaps that keep it from being *fully* true, and
adds the author-time guardrails that would have caught the foot-guns we hit.

Grounded in session reflections: `e42e67fe` (prune), `d728c118` (verify-before-finish),
`74630096` (the review synthesis), the docs-drift work (`160de79f`).

## The six improvements

### G1 — Installer prunes to the live verb set (the biggest drop-in leak)
`python -m agency.install` **writes** `bin/agency-<cap>-<verb>` + `skills/<cap>/
references/<verb>.md` but never **prunes** them when a verb is removed/renamed — and
`scripts/check-drift` does not flag the orphans (it checks generated == committed for
files it generates, not that no *extra* files exist). We hit this relocating
`skills.suggests` → `intent.suggests` (orphan `bin/agency-skills-suggests` removed by
hand). **Fix:** `install.generate` computes the exact expected file set per capability and
deletes stale `bin/`/`references/` entries; `check-drift` gains an **orphan check**
(any `bin/agency-*` / `skills/*/references/*.md` with no live verb → drift).

### G2 — Author-time lints for the two reserved-name collisions
Two foot-guns each cost a debug cycle, both statically detectable:
- a verb **parameter** named `intent_id` (or `memory`/`ctx`) collides with the reserved
  injected param → `ValueError: duplicate parameter name` at signature build.
- a verb **return key** named `artefact` carrying a *string* collides with the
  auto-artefact-record (`Registry.invoke` expects a dict) → `ValueError` at unwrap.
**Fix:** extend `plugin.lint_capability` with `reserved-param-name` + `reserved-return-key`
rules (the latter best-effort/AST), so the authoring gate catches them before runtime.

### G3 — An LLM-decider Driver seam (unblocks `llm_select`)
`intent.suggests`'s Matcher taxonomy has `pattern` + `verb_code` but `llm_select` is
deferred because there is **no LLM boundary** on the engine. **Fix:** add an
`llm` Driver to the Spec-002 registry (a `Boundary` with a typed `decide(prompt,
options) -> {choice, confidence}`), default lazy/stubbed like `skills_client`; wire it as
the `llm_select` Matcher backend. Also the seam `agentic`/pressure-test (Spec 011) and a
future `develop` reasoning step want.

### G4 — Wire `intent` reasoning into `develop` (kill a dormant surface)
The `intent` critical-thinking methods (091) and the derived `<cap>-usage` walks (081)
are *available* but not *used* — a half-built surface by the dormant-surface heuristic.
**Fix:** `develop`'s `plan` / `spec-panel` disciplines reference `intent.premortem` /
`intent.assumptions` / `intent.tradeoffs` as phase steps (cue, not hard dependency), so
reasoning fires in the workflow that needs it.

### G5 — Doc-drift in CI
`scripts/check-doc-drift` (this generation) is standalone. **Fix:** add it to the CI drift
job (advisory first: report stale docs without failing the build; promote to gating once
the marked-doc set stabilises), and/or fold it into `scripts/check-drift` as a reported
section. Keeps the new docs honest automatically.

### G6 — Followup-grounding check (claims match code)
A "Partial" TODO row (006) overstated completeness — #1 was still an O(N) scan. **Fix
(lightweight):** a `scripts/check-followup` advisory that, for each spec marked Shipped,
greps its Followup's named symbols/tests exist (e.g. the `tests/test_*.py` it cites is
present). Not a hard gate — a nudge that a roll-up claim is ungrounded.

## Done When

- [x] **G1** `install.generate` prunes stale `bin/`/`references/` to the live verb set;
  `check-drift` flags orphans; relocating/removing a verb leaves no orphan. Test: add then
  remove a verb on a probe capability → no stale files; orphan check trips on a planted one.
- [x] **G2** `plugin.lint_capability` flags a verb with a reserved param name + a
  reserved string return key; tests cover both; the existing caps still lint clean.
- [x] **G3** an `llm` Driver Protocol + lazy default on the `DriverRegistry`; `intent
  .suggests` evaluates an `llm_select` Matcher through it (stubbed in tests).
- [x] **G4** `develop`'s plan/spec-panel skills name the `intent.*` reasoning steps; a
  test asserts the cue is present + walkable.
- [x] **G5** `check-doc-drift` runs in CI (advisory); documented in `operations/`.
- [x] **G6** `scripts/check-followup` advisory exists + documented.
- [x] Each lands as its own merged-green PR; `check-drift` + `check-doc-drift` clean.

## Spec-panel critique

- **Doctrine (drop-in bar):** G1 is the highest-value item — an un-pruned install is a
  real leak in the central promise. Do G1 first. *Accepted: G1 leads.*
- **Token economist:** G2/G6 lints add author-time cost; keep them WARN-by-default
  (block only the two hard collisions G2 catches, which already crash at runtime).
  *Accepted.*
- **Skeptic (scope):** six items risk a mega-PR. Ship as **six independent PRs** behind
  this master spec — G1, G2, G4 are small + high-value; G3 (LLM Driver) is the largest
  and should stay a clean boundary (no real LLM call in tests). *Accepted: one PR each.*
- **Architect (no fifth concept):** none of these add a concept/public tool/role —
  G1/G6 are scripts, G2 is a lint rule, G3 extends the existing Driver registry, G4 is
  skill content, G5 is CI. Canon-clean. *Accepted.*
- **Cluster coherence (Spec 047):** G1/G5/G6 land in `wire-handlers`/`drift` (the
  engine-itself cluster); G2 in `authoring`; G3 in `drivers`; G4 in `develop`. No new
  cluster. *Accepted.*

**Verdict:** APPROVE — master spec; ship G1 → G2 → G4 → G3 → G5 → G6 as six PRs.

## Followup — Implementation Status (2026-06-07)

**Verdict:** Shipped — all six improvements, six merged-green PRs (#54 G1 · #56 G2 ·
#57 G3 · #55 G4 · this G5+G6).

- **G1** installer prunes stale `bin/`/`references/`; `check-drift` orphan check.
- **G2** `plugin.lint_capability` flags reserved param names (hard) + string `artefact`
  return keys (soft AST); all 17 caps collision-free.
- **G3** the `llm` Driver via **OpenRouter** (httpx, no SDK; `AGENCY_LLM_MODEL`,
  `response_format` json_schema + tolerant parse); `intent.suggests` evaluates `llm_select`.
- **G4** `develop`'s brainstorm/plan/spec-panel disciplines cue the `intent.*` methods.
- **G5** `scripts/check-doc-drift` runs in CI (advisory `continue-on-error`).
- **G6** `scripts/check-followup` (advisory) — a Shipped spec cites tests that exist;
  27 cited test files across 23 Shipped specs all present.

`tests/test_advisory_scripts.py` (2) + the per-improvement suites. Full suite 955 passed,
3 skipped; `check-drift` + `check-doc-drift` clean.
