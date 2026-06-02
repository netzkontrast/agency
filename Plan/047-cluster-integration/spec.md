---
spec_id: "047"
slug: cluster-integration
status: draft
last_updated: 2026-06-02
owner: "@agency"
depends_on: [023, 029, 030, 039, 040, 041, 042, 043, 044, 045, 046]
affects:
  - Plan/047-cluster-integration/                          # THIS spec (integration master)
  - CLAUDE.md                                              # add Cluster-coherence section
  - docs/vision/CAPABILITY-CLUSTERS.md                     # extend with the 13 SC+SP cluster mappings
estimated_jules_sessions: 0   # NO implementation — this spec is the cluster-integration master plan only
domain: meta
wave: 2
nature: integration-master
covers_clusters: [C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, C13]
---

# Spec 047 — Cluster Integration Master Plan

## Why

The PR #17 audit conversation (cluster analysis of SuperClaude's 33
commands + Superpowers' 14 skills) identified **13 capability clusters**
covering the full SDLC + meta-disciplines. Specs 039–046 implement
parts of those clusters as agency capabilities, skills, and substrate
tools. But **no single document explains how the 13 clusters compose
into a coherent Agency** — how the surfaces relate, where they share
substrate, where the user experience is unified, where coherence-risks
hide.

This spec answers that question. **It writes no code and ships no
verbs.** It writes one **integration plan per cluster**, naming:

- the agency primitives the cluster builds on (engine substrate, existing
  capabilities, ontology fragments),
- the existing specs that implement parts of it (cross-reference the 8
  specs in this branch + relevant main-line specs),
- the **integration pattern** — how the cluster's surface composes with
  the rest of Agency (which verbs call which, which skills delegate to
  which capabilities, which substrate tools bootstrap the cluster),
- the **coherence interactions** — where the cluster TOUCHES other
  clusters (overlapping verbs, shared ontology nodes, shared driver
  slots),
- the open coherence questions per cluster.

When a cluster's plan grows large enough to need its own dedicated
spec, this master can **promote** the plan to a standalone spec (the
same pattern Spec 015 used for promoting 017/018/019). Until then, the
master is the single source of truth for "how does cluster X integrate
into Agency?".

## Done When

- [ ] All 13 clusters have an integration plan in §"Design", each
  covering: scope, agency primitives, existing specs, integration
  pattern, coherence interactions, open questions.
- [ ] The plan identifies **at least three cross-cluster coherence
  risks** (places where two clusters' integration could conflict) and
  documents the resolution.
- [ ] `docs/vision/CAPABILITY-CLUSTERS.md` is updated with a pointer
  table listing the 13 clusters and their integration-plan section in
  this spec.
- [ ] `CLAUDE.md` gains a §"Cluster coherence" subsection summarising
  the master pattern: when you add a verb or skill, check which
  cluster it lands in and whether the cluster's integration plan
  covers your addition (or needs amendment).
- [ ] `TODO.md` adds a row for Spec 047 (Status: Shipped, Not started,
  Partial — depending on how much of the per-cluster plan has been
  filled in).
- [ ] No new capability, no new skill, no new substrate tool is added
  by this spec. The deliverable is **the plan** — orchestrating
  documents that organise the existing surface plus the 8 in-flight
  specs.

## Design

### Cluster taxonomy (the 13)

Derived from PR #17 deep-dive analysis of SuperClaude (33 commands +
core/PRINCIPLES.md, RULES.md, FLAGS.md, RESEARCH_CONFIG.md, modes/,
agents/) and Superpowers (14 skills + episodic-memory, developing-
claude-code-plugins, working-with-claude-code, deep-research). Each
cluster is named by SDLC phase or meta-discipline.

| # | Cluster | One-line |
|---|---|---|
| **C01** | Discovery / Brainstorm | Explore intent + requirements before code |
| **C02** | Planning / Specs | Decompose a multi-step task into bite-sized plan |
| **C03** | Implementation Disciplines | TDD, executing plans, subagent-driven dev |
| **C04** | Quality / Review / Verify | Multi-axis analysis, code review, verification |
| **C05** | Debug / Troubleshoot | Root-cause-first investigation, hypothesis testing |
| **C06** | Cleanup / Refactor | Dead-code removal, refactor with safety nets |
| **C07** | Documentation / Knowledge | Render-from-graph, index, explain, briefings |
| **C08** | Session Lifecycle / Memory | Reflection, semantic recall, cross-session continuity |
| **C09** | Git / VCS | Workspace isolation, smart commits, branch finishing |
| **C10** | Research | Lead + specialists + verifier, cited reports |
| **C11** | Orchestration / Subagents | Dispatch decisions, fan-out, driver selection |
| **C12** | Meta / Help / Dispatch | Discovery, command map, recommendation |
| **C13** | Plugin / MCP Authoring | Capability scaffold, skill creation, plugin release |

---

### C01 — Discovery / Brainstorm

**Scope.** Open-ended exploration of intent, requirements, design space,
trade-offs. The phase before any artefact is built.

**Agency primitives:**
- `agency_welcome` substrate (Spec 029) — onboarding payload + state
  detection (fresh vs. in_progress).
- `intent_bootstrap` substrate (Spec 029) — mints the Intent every
  subsequent verb SERVES.
- `agency:brainstorming` skill — discipline (no engine verbs).

**Existing specs implementing this:**
- Spec 029 (mcp-bootstrap-and-self-explain).
- Spec 030 (jules-key-doctor-stateful-welcome).
- Spec 046 §F-B (visual-companion port — brainstorming with browser-
  rendered mockups when applicable).

**Integration pattern:**
```
intent_bootstrap (substrate)
  └─► agency:brainstorming (skill walk)
        ├─► [optional] visual-companion (Spec 046 §F-B)
        └─► HAND-OFF to writing-plans (C02)
```

The skill walks `explore → propose → present → approve → write design
doc → user review`. The substrate provides the `intent_id` anchor;
the skill never mints intents itself.

**Coherence interactions:**
- **With C02 (Planning):** `brainstorming` hands off to `writing-plans`
  on its terminal phase. The design doc the brainstorm produces is the
  input to the plan. Coherence: the hand-off is *explicit* via the
  skill chain, not implicit via context.
- **With C10 (Research):** if brainstorming surfaces a research
  question, the skill can dispatch to `research.lead` (Spec 044). The
  research result becomes input to a subsequent brainstorming phase.

**Open questions:**
- Should `brainstorming` produce a `Reflection` of `kind=design-doc`
  for the design output, OR write to `docs/superpowers/specs/`? The
  graph-vs-file doctrine says graph; but design docs are read by
  humans outside the agency engine, so disk export is necessary.
  Lean: graph-canonical + render-on-demand via Spec 043 `document.render`.

---

### C02 — Planning / Specs

**Scope.** Turn a design / requirement into a bite-sized, ordered,
TDD-ready implementation plan. Includes spec-panel review of the plan.

**Agency primitives:**
- `agency:writing-plans` skill — discipline.
- `agency:spec-panel` skill — multi-expert critique.
- `Plan/NNN-slug/spec.md` files — the persisted spec format.
- `Plan/NNN-slug/IMPLEMENTATION-PLAN.md` — the persisted plan format.

**Existing specs implementing this:**
- (No new capability needed — skills are the surface.)
- Spec 046 §F-D `develop.estimate` verb supports planning (rule-table
  estimation feeds the plan's wall-clock budget).

**Integration pattern:**
```
HAND-OFF from C01 brainstorming
  └─► agency:writing-plans (skill walk)
        ├─► [optional] develop.estimate (Spec 046 §F-D) per task
        ├─► [optional] agency:spec-panel critique
        └─► HAND-OFF to executing-plans (C03 Spec 041) OR
              subagent-driven-development (C03 Spec 041)
```

**Coherence interactions:**
- **With C03 (Implementation):** the plan is the input contract for
  executing-plans / subagent-driven-development. Coherence: the
  plan's task shape (file map, ordering, TDD-structure) must match
  what C03 skills expect.
- **With C07 (Documentation):** specs themselves are documentation;
  `document.render(scope="provenance")` (Spec 043) can project an
  intent's plan-execution history into a markdown summary. The spec
  format IS a document, but it's hand-authored; the Followup-section
  is render-able.

**Open questions:**
- Should `Plan/NNN/spec.md` files be graph-canonical (i.e. authored
  as `Spec` nodes + `document.render`-ed)? Today they're disk-canonical
  (the cleanest violation of CLAUDE.md Rule #2 — but defended as
  "doctrine docs serve external readers", same exception as
  CORE/AGENTS/AGENCY_PROTOCOL). v2 question.

---

### C03 — Implementation Disciplines

**Scope.** TDD, plan execution (serial or subagent-driven), parallel-
agent dispatch.

**Agency primitives:**
- `agency:test-driven-development` skill.
- `agency:verification-before-completion` skill.
- `agency/capabilities/delegate.py` (engine — fan-out + quota + join).
- `agency/capabilities/subagent.py` (engine — local subagent driver).
- `agency/capabilities/workspace.py` (engine — workspace isolation).

**Existing specs implementing this:**
- Spec 041 (implementation-discipline-skills) — ports `executing-plans`,
  `subagent-driven-development`, `dispatching-parallel-agents` + deepens
  TDD with anti-patterns + deepens systematic-debugging with find-
  polluter.sh.
- Spec 040 (subagent-decision-heuristics) — the 11-signal heuristic
  every C03 skill calls.

**Integration pattern:**
```
HAND-OFF from C02 writing-plans
  ├─► executing-plans (Spec 041 — serial)         OR
  └─► subagent-driven-development (Spec 041)
        ├─► PER TASK: delegate.dispatch_decision (Spec 040)
        │   ├─► inline (own context)              OR
        │   ├─► subagent (Spec 041 implementer-prompt)
        │   │   └─► spec-reviewer → code-reviewer (two-stage gate)
        │   └─► jules (Spec 040 S11=False)
        └─► HAND-OFF to finishing-a-development-branch (C09)
```

**Coherence interactions:**
- **With C04 (Quality):** the `code-reviewer` subagent in
  subagent-driven-development calls `capability_analyze_run`
  (Spec 042) at the code-review phase. Tight coupling — Spec 041's
  prompt template names Spec 042 directly.
- **With C11 (Orchestration):** every dispatch decision routes through
  Spec 040. Coherence: C03 skills NEVER dispatch without consulting
  Spec 040; Spec 040 NEVER mutates without C03 discipline.

**Open questions:**
- Should `executing-plans` and `subagent-driven-development` share an
  underlying `execute` capability verb, OR remain pure skills?
  Currently both are skills; the engine surface is just `delegate.*`
  + `subagent.*`. Adding an `execute` capability would duplicate
  delegate's semantics. Lean: keep as skills.

---

### C04 — Quality / Review / Verify

**Scope.** Multi-axis code analysis (quality, security, performance,
architecture), code review (requesting + receiving), verification
discipline before completion claims.

**Agency primitives:**
- `agency:verification-before-completion` skill.
- `agency/capabilities/plugin.py::lint_capability` (block-mode lint).
- `agency/capabilities/develop.py::review` skill.

**Existing specs implementing this:**
- Spec 042 (analyze capability) — the 4-axis decidable transforms +
  improve/cleanup acts.
- Spec 046 §F-A (code-review split — requesting + receiving).
- Spec 041 §"code-reviewer-prompt.md" — the subagent prompt that calls
  Spec 042's analyze.run.

**Integration pattern:**
```
Quality entry points (any of these):
  - capability_analyze_run (Spec 042, inline)
  - skill: code-analysis walker (Spec 042)
  - skill: requesting-code-review (Spec 046 §F-A) — dispatches subagent
  - skill: receiving-code-review (Spec 046 §F-A) — rigour against blind impl
  - capability_plugin_lint_capability (existing — block-mode lint at scaffold)

ALL CONVERGE on:
  Finding shape {rule, severity, file, line, message, evidence}
  Severity enum {info, warn, fail}
  Stored as Finding nodes (Spec 042 ontology fragment)
```

**Coherence interactions:**
- **With C03 (Implementation):** Spec 041's code-reviewer-prompt
  returns `{verdict, findings}` USING Spec 042's Finding shape.
  Coherence: ONE Finding shape across all C04 surfaces.
- **With C06 (Cleanup):** `analyze.cleanup` (Spec 042) is a mode of
  `analyze.improve` restricted to dead-code findings. Coherence: not
  two capabilities, one capability with focused acts.
- **With C07 (Documentation):** Findings can be rendered to markdown
  via `document.render` (Spec 043) — a new scope `"analysis"` to add.

**Open questions:**
- Should `verification-before-completion` invoke `analyze.run` at its
  verification phase? Today it's a manual run-the-command discipline;
  Spec 042 could automate it. Lean: yes for `analyze.quality` axis;
  no for `analyze.architecture` (too slow for a verification gate).
- The proposed `"analysis"` render scope is NOT in Spec 043's v1 list.
  Add to Spec 043 v1 (small change) or v2.

---

### C05 — Debug / Troubleshoot

**Scope.** Root-cause-first investigation with hypothesis-test cycles.
Phase-gated to prevent quick-fix anti-patterns.

**Agency primitives:**
- `agency:systematic-debugging` skill (existing, deepened by Spec 041).
- `agency_doctor` substrate tool (Spec 030) — first stop for runtime
  issues.

**Existing specs implementing this:**
- Spec 041 §"systematic-debugging extension" — adds find-polluter.sh
  script + anti-patterns.md reference.
- Spec 042 §"analyze.performance/security" — provides decidable
  findings during the Phase-1 investigation.

**Integration pattern:**
```
Bug encountered (test failure / unexpected behaviour)
  └─► agency_doctor (substrate first — covers runtime issues)
        └─► agency:systematic-debugging skill walk
              ├─► Phase 1: investigate (find-polluter.sh if test isolation)
              ├─► Phase 2: pattern (capability_analyze_run optional)
              ├─► Phase 3: hypothesis (≤ 2 attempts before architecture)
              ├─► Phase 4: test (capability_test_driven_development)
              └─► HAND-OFF to implementation (C03) for the fix
```

**Coherence interactions:**
- **With C03 (TDD):** the fix is implemented via TDD discipline.
  Coherence: ≤ 3 hypothesis failures triggers architecture review
  escalation (Spec 041 anti-pattern doctrine), NOT a 4th attempt.
- **With C04 (Analyze):** Phase-2 pattern recognition can call
  `analyze.run`. Coherence: opt-in, not auto — analyze runs on
  request, not at every Phase-2 step.

**Open questions:**
- Should `agency_doctor` add a `--for-debug` mode that runs deeper
  checks (DB integrity, schema drift, recent reflection patterns)?
  v2 question.

---

### C06 — Cleanup / Refactor

**Scope.** Dead-code removal, refactor with safety nets, structural
hygiene.

**Agency primitives:**
- No new engine verbs — covered by `analyze.cleanup` + `analyze.improve`
  (Spec 042).

**Existing specs implementing this:**
- Spec 042 §`analyze.cleanup` verb (act) — focused on dead-code
  findings only.
- Spec 042 §`analyze.improve(axes=…)` verb (act) — general improvement
  plan from findings.

**Integration pattern:**
```
Manual entry:
  capability_analyze_cleanup(path, dry_run=True, intent_id=...)
    ├─► reuses analyze.quality findings
    ├─► proposes patches (Reflection node, kind=improvement-plan)
    └─► dry_run=False → applies WITH gate.check per cluster
```

**Coherence interactions:**
- **With C04 (Quality):** cleanup IS a mode of analyze. Coherence: no
  separate `cleanup` capability; agency_doctor for runtime hygiene,
  analyze for code hygiene.

**Open questions:**
- Should refactor patterns (extract-method, rename-symbol) ship as
  separate verbs or as `analyze.improve` modes? Lean: v2; the
  decidable subset doesn't include refactor-as-transform safely.

---

### C07 — Documentation / Knowledge

**Scope.** Render-from-graph, code explanation, repo briefing/indexing,
on-demand documentation projection.

**Agency primitives:**
- `agency/render.py::parse_slices` (existing — brief slice extraction).
- Reflection nodes (existing — the storage substrate).

**Existing specs implementing this:**
- Spec 043 (document capability) — render/explain/index_repo.
- Spec 017 (graph-native dogfood ledgers — not started; render side
  closed by Spec 043).
- Spec 046 §F-F (update_docs.py — upstream-doc autosync).

**Integration pattern:**
```
Documentation entry points:
  - capability_document_render(scope=...) — projects graph state
  - capability_document_explain(target, depth=...) — composes signature
      + brief + callers + reflect.recall_semantic (Spec 045)
  - capability_document_index_repo(path, apply=...) — the 94%-reduction
      briefing
  - skill: repo-briefing walker (Spec 043)
  - script: skills/plugin-development/scripts/update_docs.py (Spec 046 §F-F)
```

**Coherence interactions:**
- **With C04 (Quality):** add a `"analysis"` render scope (see C04
  open questions).
- **With C08 (Memory):** `document.explain` reads `reflect.recall_semantic`
  (Spec 045) for the "see also" section. Coherence: explain doesn't
  generate — it composes deterministic features INCLUDING graph
  reflections.
- **With C13 (Plugin):** `agency.install` will switch from direct file-
  write to `document.render(scope="install-artefacts")` once Spec 043
  ships (closes the Spec 017 render-side gap).

**Open questions:**
- Where does `index_repo`'s output (PROJECT_INDEX.md) live? Spec 043
  Open Q2 (`.agency/` vs `docs/`). Resolution affects how C13's
  plugin-development references it.

---

### C08 — Session Lifecycle / Memory

**Scope.** Cross-session continuity, semantic recall over reflections,
state recovery on session resume.

**Agency primitives:**
- `agency/capabilities/reflect.py` — note/batch_note/recall/search (existing).
- `.agency/session.db` (Spec 020 — bi-temporal graph DB, per-project).
- `agency_welcome` substrate (Spec 029) — state-aware: fresh vs.
  in_progress.

**Existing specs implementing this:**
- Spec 045 (reflect-semantic-recall) — adds `reflect.recall_semantic`
  with TF-IDF + optional vector embedder.
- Spec 030 (jules-key-doctor-stateful-welcome) — agency_welcome state
  detection.
- (Adoption target via future MCP-client driver:) Superpowers
  `episodic-memory` MCP server for Claude Code transcript corpus
  (orthogonal to agency's Reflection corpus — see Spec 045
  §"complementary adoption").

**Integration pattern:**
```
Session start:
  agency_welcome
    ├─► state="fresh" → next: intent_bootstrap
    └─► state="in_progress" → next: search('<keyword>') OR
          memory_graph_provenance('<last_intent>')

Mid-session memory:
  reflect.note(scope, text) → write
  reflect.recall_semantic(query, k) → top-k semantic search

Cross-session: the .agency/session.db is committed (Spec 020 doctrine).
```

**Coherence interactions:**
- **With C10 (Research):** `research.specialist(role="prior-reflections",
  …)` calls `reflect.recall_semantic`. Coherence: agency reflections
  are first-class evidence in research.
- **With C07 (Documentation):** `document.explain`'s "see also" reads
  recall_semantic. Coherence: explanations are graph-grounded.

**Open questions:**
- The MCP-client driver (audit F6) is needed to adopt episodic-memory
  externally. Spec 040 Open Q3 names it as the first adoptee. Timing:
  driver-spec is separate (not in this branch); episodic-memory
  adoption happens after.

---

### C09 — Git / VCS

**Scope.** Workspace isolation, smart commits, branch lifecycle finishing.

**Agency primitives:**
- `agency/capabilities/branch.py` (existing — finish verb + PR creation).
- `agency/capabilities/workspace.py` (existing — isolate + baseline).
- `agency/capabilities/_vcs.py::GitClient` (boundary driver).

**Existing specs implementing this:**
- Spec 046 §F-C (branch.commit_smart — conventional-commit messages
  from diff stats).

**Integration pattern:**
```
Workspace lifecycle:
  capability_workspace_baseline(...) → isolate
    └─► [implementation work via C03]
          └─► capability_branch_commit_smart (Spec 046 §F-C)
                └─► capability_branch_finish_or_create_pr

Driver boundary: ctx.vcs = GitClient() (default) or stub (test)
```

**Coherence interactions:**
- **With C03 (Implementation):** the `finishing-a-development-branch`
  discipline (from Spec 041 ports if it lands as skill, or directly
  via `branch.finish` cap) is the canonical end of any implementation
  loop.
- **With C13 (Plugin release):** release-and-distribution.md (in the
  plugin-development skill references) describes the tag-and-push
  flow. Coherence: branch.create_pr is one step; the tag flow is
  manual today.

**Open questions:**
- Should `branch.commit_smart` be the default for `branch.commit`, or
  remain a separate verb? Lean: separate (explicit > clever).

---

### C10 — Research

**Scope.** Lead + specialists + verifier composition. Cited reports
with adversarial verification.

**Agency primitives:**
- `agency/capabilities/delegate.py` (engine — fan-out for specialists).
- `agency/capabilities/gate.py` (engine — verifier hard-gate).
- `agency/capabilities/reflect.py::recall_semantic` (Spec 045 — for
  `prior-reflections` specialist).

**Existing specs implementing this:**
- Spec 044 (research capability) — lead/specialist/verify + Citation
  ontology fragment.
- Spec 044 §"Novel-research prompts (task F)" + the 5 files in
  `research/novel-prompts/` — usable today as standalone Gemini-deep-
  research briefs; valid inputs to the capability when it ships.

**Integration pattern:**
```
research.lead(question, depth)
  └─► delegate.dispatch (per planned specialist)
        ├─► research.specialist(role="web", query)
        ├─► research.specialist(role="codebase", query)
        ├─► research.specialist(role="prior-reflections", query)
        │     └─► reflect.recall_semantic
        └─► research.specialist(role="doc-corpus", query)
  └─► research.verify (decidable checks: reachability +
        evidence-supports-claim + contradiction-cluster)
  └─► document.render(scope="research-report") (Spec 043)
  └─► gate.check (publish hard-gate)
```

**Coherence interactions:**
- **With C11 (Orchestration):** every specialist fan-out routes through
  Spec 040 dispatch_decision. Coherence: `research.lead` MUST consult
  Spec 040 in its planning phase.
- **With C07 (Documentation):** report rendering goes through Spec 043.
  Coherence: rendering NEVER lives inside `research`; always via
  `document.render`.

**Open questions:**
- Web-search driver default — Spec 044 Open Q1. Lazy-import host's
  `WebSearch` tool; fail-loud if absent. Acceptable v1.

---

### C11 — Orchestration / Subagents

**Scope.** Dispatch decisions, fan-out, driver selection, tool selection.

**Agency primitives:**
- `agency/capabilities/delegate.py` (engine — dispatch + quota + join).
- `agency/capabilities/subagent.py` (engine — local-subagent driver).
- `agency/capabilities/jules.py` (engine — remote-Jules driver).

**Existing specs implementing this:**
- Spec 040 (subagent-decision-heuristics) — the 11-signal heuristic +
  driver-choice matrix + cache-and-budget-model reference.
- Spec 041 (implementation-discipline-skills) — dispatching-parallel-
  agents skill consumes the heuristic.
- Spec 044 (research) — research.lead consumes the heuristic.

**Integration pattern:**
```
ANY verb / skill considering dispatch:
  └─► delegate.dispatch_decision(s1...s11)
        ├─► returns {recommendation, driver, rationale,
        │             token_cost_estimate, local_budget_token_estimate}
        └─► caller acts on the decision

Drivers:
  - inline: same agent context
  - local: subagent.* capability (own context, local budget)
  - jules: jules.* capability (remote, separate budget)
  - mcp (future): MCP-client-driver (audit F6, separate spec)
```

**Coherence interactions:**
- **Touches EVERY other cluster.** Spec 040 is the universal arbiter.
  Coherence: NO skill / verb should dispatch without consulting
  dispatch_decision; this is a CLAUDE.md Rule #3 doctrine.

**Open questions:**
- Should dispatch_decision auto-fire from inside `delegate.dispatch`?
  Spec 040 Open Q4 — lean no (explicit > clever).

---

### C12 — Meta / Help / Dispatch

**Scope.** Discovery surface, command map, recommendation, what-to-do-next.

**Agency primitives:**
- `agency:help` skill (existing).
- `agency/capabilities/plugin.py::help` verb (existing — macroskill map).
- `agency_welcome` substrate (Spec 029).

**Existing specs implementing this:**
- (No new spec — covered by existing surface.)
- Spec 043 §`document.render(scope="capability-catalogue")` provides
  the rendered catalogue (replaces today's `agency.install`-regenerated
  `skills/help/SKILL.md`).

**Integration pattern:**
```
Fresh session:
  agency_welcome (substrate) → state-aware payload

Discovery:
  search('<keyword>') → ranked tools + skills
  capability_plugin_help → macroskill map
  document.render(scope="capability-catalogue") → full catalogue
```

**Coherence interactions:**
- **With C07 (Documentation):** the catalogue render is a Spec 043
  scope. Coherence: ONE source of catalogue rendering (Spec 043);
  `plugin.help` returns a smaller subset.

**Open questions:**
- Once Spec 043 ships, deprecate the in-engine catalogue rendering in
  `agency.install` and route through `document.render`. v1 of Spec 043
  designs for this.

---

### C13 — Plugin / MCP Authoring

**Scope.** Scaffold a capability, author a skill, publish to marketplace,
release a version, install via pipx.

**Agency primitives:**
- `agency:plugin-development` skill (existing — extended in this branch
  with 7 references).
- `agency:authoring-capabilities` skill (existing — deep capability-
  authoring discipline).
- `agency:skill-creation` skill (existing — CSO lint discipline).
- `agency/capabilities/plugin.py` (engine — lint_skill, lint_capability,
  scaffold).
- `agency/capabilities/develop.py::scaffold_capability` (engine).
- `agency/install.py` (engine — regen `plugin.json` / `.mcp.json` /
  slash-commands).

**Existing specs implementing this:**
- Spec 039 (distribution-and-e2e-hardening) — pipx + E2E + incorporates
  017/018/019.
- Spec 046 §F-A (code-review skill split).
- Spec 046 §F-F (update_docs.py upstream-doc autosync).
- Existing Spec 031 (main — skills-progressive-disclosure).
- Existing Spec 032 (main — templates-schemas-oop-extensions).

**Integration pattern:**
```
New plugin / capability authoring:
  agency:plugin-development (outer lens)
    ├─► authoring-capabilities (for capability files)
    │     └─► capability_develop_scaffold_capability
    │     └─► capability_plugin_lint_capability (block-mode)
    ├─► skill-creation (for SKILL.md files)
    │     └─► capability_plugin_lint_skill
    └─► release: python -m agency.install → regen → commit → tag
```

**Coherence interactions:**
- **With C04 (Quality):** capability lint IS a code-quality check;
  Spec 042 analyze.quality COULD subsume it long-term. Coherence:
  lint stays scaffold-time; analyze stays general code-time. Different
  invocation points, no overlap.
- **With C07 (Documentation):** plugin-development bundled references
  + update_docs.py share the references/ pattern. Coherence: one
  references/ dir per skill, ports of upstream go under `upstream/`
  subdir.

**Open questions:**
- Spec 031 and Spec 032 on main are doing significant implementation
  work (skill_emit, capability_loader, materialiser, etc.). When this
  PR merges, those changes need to be reflected here. Action: re-read
  main commits + write a coherence-check pass before merging.

---

### Cross-cluster coherence risks (the audit)

Three places where the 13 clusters' integrations could conflict if
not deliberately coordinated:

**Risk 1 — Two analyses, two Finding shapes.**
Spec 042's `analyze.*` emits Finding nodes. Spec 041's `code-reviewer-
prompt.md` returns `findings: [...]`. If these diverge in shape, the
review-loop breaks.
**Resolution:** Spec 041 prompt template explicitly says "reuses Spec
042 Finding shape". Pinned in Spec 041 Done When (after the panel pass).

**Risk 2 — Two rendering surfaces.**
Spec 043 `document.render(scope="capability-catalogue")` projects the
catalogue. Today `agency.install` regenerates `skills/help/SKILL.md`
directly. After Spec 043 ships, both could exist.
**Resolution:** Spec 043 Open Q2 (where PROJECT_INDEX.md lives) + the
Spec 047 §C12 open question (deprecate the in-engine catalogue render).
Action: Spec 043 v1 ships the scope; `agency.install` switch is a
follow-up commit; ONE source of catalogue rendering thereafter.

**Risk 3 — Two semantic-search surfaces.**
Spec 045 `reflect.recall_semantic` searches agency Reflections.
Future MCP-client-driver adopting `episodic-memory` searches Claude
Code transcripts. Both return similar shapes; agents could conflate.
**Resolution:** different `source_kind` in Citation (Spec 044); agents
pick by question shape. Spec 045 §"What this is NOT" makes the split
explicit.

### Promotion criteria (when a cluster plan becomes its own spec)

Following the Spec 015 → Specs 017/018/019 promotion pattern: a
cluster plan promotes to a dedicated spec when ANY of the following:

- The integration pattern grows past ~150 lines (loses skim-clarity).
- Cross-cluster coherence interactions require ≥ 3 named decisions
  (each becomes a Done-When).
- An implementation kicks off — at that point the cluster needs its
  own IMPLEMENTATION-PLAN.md anyway.

Until promotion, the cluster's section in THIS spec is the source of
truth.

## Files

- **Create:**
  - `Plan/047-cluster-integration/spec.md` (THIS file).
- **Modify (when this spec ships):**
  - `CLAUDE.md` — add §"Cluster coherence" subsection summarising the
    master pattern.
  - `docs/vision/CAPABILITY-CLUSTERS.md` — add a pointer table to the
    13 cluster sections in this spec.
  - `TODO.md` — add a row for Spec 047.
- **Do not modify:**
  - Specs 039–046 — their cross-references to this master are added
    only IF the master changes (e.g. a promotion to standalone spec).
  - Existing capabilities, skills, substrate tools — this is a plan
    spec, not an implementation.

## Open Questions

1. **Promotion vs. integration.** Some cluster sections may grow large
   enough to deserve standalone specs (especially C04 Quality, C10
   Research, C13 Plugin). When to promote? See §"Promotion criteria".
2. **Spec 031/032 on main.** Main is actively shipping spec 031
   (skills-progressive-disclosure) and 032 (templates-schemas-oop-
   extensions). Their finished surfaces will land in C13. Need a
   coherence-check pass once those PRs settle.
3. **The MCP-client-driver spec.** Audit F6 — referenced from Spec
   040 (Open Q3) and C08 (above). Should THIS master spec name it as
   Spec 048 (next available number) or stay agnostic until someone
   writes that spec?
4. **`docs/vision/CAPABILITY-CLUSTERS.md` reconciliation.** That file
   already has a cluster mapping (older — from Spec 015 era). This
   spec's 13 clusters partially overlap. Action: merge — keep the
   older file's per-CORE-concept mapping, add the SC+SP 13-cluster
   overlay as a new section.
5. **TODO.md auto-update.** CLAUDE.md Rule #4 (just added) requires
   TODO.md updates per spec change. This spec adds Spec 047 to
   TODO.md but doesn't yet exist as a row — should the row be added
   in this spec's commit, or in a follow-up commit? Lean: same
   commit; the row's status is "Shipped" because the deliverable IS
   the plan and the plan is this file.

## Evidence

- PR #17 audit conversation — deep-dive on SuperClaude (33 commands +
  core/ + modes/ + agents/) and Superpowers (14 skills +
  episodic-memory, developing-claude-code-plugins, working-with-claude-
  code, deep-research).
- Specs 039–046 — the implementation surface this master organises.
- `Plan/000-overview.md` — historical spec landscape + verdict snapshot.
- `docs/vision/CAPABILITY-CLUSTERS.md` — pre-existing cluster mapping
  (CORE-concept-based; this spec extends it).
- `CLAUDE.md` Rules #1–#4 — the four working-in-this-repo rules; Rule
  #4 (TODO.md maintenance, just added) underlies the master's
  durability.

## Followup — Implementation Status (2026-06-02)

**Verdict:** Shipped (this spec IS the deliverable).

### Done
- The 13 cluster taxonomy is defined.
- Each cluster has an integration plan (Scope / Agency primitives /
  Existing specs / Integration pattern / Coherence interactions /
  Open questions).
- Three cross-cluster coherence risks identified + resolution
  documented.
- Promotion criteria for cluster-to-standalone-spec defined.
- Cross-references to Specs 039–046 (and main's 031/032) anchor the
  master to the in-flight work.

### Still to implement (downstream of this spec)
- `CLAUDE.md` §"Cluster coherence" subsection.
- `docs/vision/CAPABILITY-CLUSTERS.md` extension with the 13-cluster
  overlay.
- `TODO.md` row for Spec 047 (Shipped).
- Per-cluster promotion (only when triggered by the §"Promotion
  criteria" thresholds).

### Refinement needed
- Open Question 2 (Spec 031/032 reconciliation) needs a follow-up
  pass after those PRs land.
- Open Question 3 (MCP-client driver spec) needs a one-line policy
  call on numbering.
