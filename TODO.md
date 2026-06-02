# TODO — Spec State

> **Binding spec status index.** This file is the single source of truth
> for "which specs are shipped / partial / not started / drafted".
> Per-spec details live in `Plan/NNN-slug/spec.md`'s
> `## Followup — Implementation Status (…)` section; THIS file is the
> across-spec roll-up.
>
> **Maintenance discipline (also recorded in `CLAUDE.md`):** every PR
> that ships a spec, opens a new spec, or changes a spec's status MUST
> update the corresponding row here in the same commit. No drift.
>
> **Last reviewed:** 2026-06-02 (branch `claude/blissful-volta-rJ3rP`).
> **Wave-3 + audit-bundle baseline:** 333 tests passed at consolidation
> review (per `Plan/000-overview.md`'s 2026-05-31 snapshot); recent main
> activity adds Spec 031 + 032 implementation work.

## Verdicts at a glance

| Verdict | Count | Specs |
|---|---|---|
| **Shipped** | 13 | 012, 013, 015, 029, 030, 039, 040, 042, 043, 044, 045, 047, 048 |
| **Partially implemented** | 11 | 001, 006, 007, 016, 018, 020, 023, 024, 025, 031, 032 |
| **Not started** | 18 | 002, 003, 004, 005, 008, 009, 010, 011, 014, 017, 019, 021, 022, 026, 028, 041, 046, 049 + (010 deferred-v2 axes) |

Total active specs: **41** (counting 000-overview).

## Status table

| Spec | Slug | Status | One-line | Blocker / Next step |
|---|---|---|---|---|
| 001 | toolresult-and-typed-errors | Partial | Internal `ToolResult` envelope | `Codes`, `to_dict/from_dict`, convenience ctors, full verb migration absent |
| 002 | boundary-driver-protocol | Not started | Generic Boundary/Driver + DriverRegistry | Hard-blocks 007's full music surface |
| 003 | skill-phase-objects | Not started | Typed `Skill`/`Phase` parse/validate boundary | Wave-1 backlog; revisit when canon needs new ground |
| 004 | template-schema-coverage | Not started | Wire generate/validate loop for uncovered kinds | Wave-1 backlog |
| 005 | context-mode-and-token-economics | Not started | Output-overflow capture + recall | Wave-1 backlog |
| 006 | core-hardening | Partial | Red-team fixes: tick, pagination, verify | Fixes #1 O(1), #2 `seen_tokens`, #4 `capture_api_key` absent; `tests/test_hardening.py` missing |
| 007 | music-domain-capability | Partial | Music domain (in `examples/music.py`) | Full surface depends on 002 driver registry |
| 008 | superclaude-analysts | Not started | SuperClaude analysis (`transmute` cluster) | Superseded by Spec 042 (`analyze`) — close out? |
| 009 | superpowers-remainder | Not started | Finish the superpowers port | Superseded by Specs 041 + 046 — close out? |
| 010 | novel-domain | Not started | Novel domain (Dramatica/NCP, gates) | 0% impl; 7 loops sequenced; spec rebased 2026-05-31 |
| 011 | agentic-capabilities | Not started | Agentic guardrails (middleware + `gate` + skill) | Depends on Spec 021 monitor channel |
| 012 | jules-complete-lifecycle-and-watcher | **Shipped** | Full Jules v1alpha + watcher + recovery | (frontmatter says draft — flip to done) |
| 013 | jules-skills-and-capability-improvements | **Shipped** | 6 Jules skills + AGENCY_PROTOCOL + lint + flag matrix | (flip frontmatter) |
| 014 | observation-to-spec-amendment | Not started | Reflection → spec-amendment loop | Depends on 017 + 020 |
| 015 | architecture-review | **Shipped** | Architecture review docs + 017/018/019 promoted | (milestone; review-only spec) |
| 016 | capability-authoring-doctrine | Partial | 11 authoring hints + folder-form discover | Hint #7 docstring sweep never done; Phase 5 cleanup partial; Phase 6 → 028 |
| 017 | graph-native-dogfood-ledgers | Not started | `dogfood.note` + `dogfood.render` | Closes Jules's Spec 015 W1/W2; depends on 020 |
| 018 | cli-token-efficiency-bundle | Partial | 5 token wins + Jules's `--fields` + traceback wrapper | Depends on 016 lint scaffold + 020 |
| 019 | engine-output-shape-contract | Not started | Document unwrap-as-contract; lint enforces docstring | Depends on 016 lint extensibility |
| 020 | central-graph-db | Partial | `.agency/session.db` as per-project default | One verb (`dogfood.export`) away from done |
| 021 | engine-monitor-channel | Not started | Engine-level Monitor channel (1 monitors.json) | **Hard-blocks 022 and 011** |
| 022 | jules-monitor-capability | Not started | First use of 021 for Jules watcher transitions | Depends on 021 |
| 023 | adaptive-disclosure | Partial | Token-budget gate + brief slices | Docstring sweep shared open item with 016/019 |
| 024 | capability-authoring-discipline | Partial | Block-mode lint when `# agency-scaffold: v1` marker present | Sweep of existing capabilities for marker addition |
| 025 | skill-first-discovery | Partial | Skill-search ranks above tool-search | Refinement needed per consolidation pass |
| 026 | skills-as-core-capability | Not started | Skill surface as a first-class capability | Depends on 016 cleanup |
| 028 | jules-folder-migration | Not started | Migrate `_jules_*` modules into folder form | Depends on 016 Phase 6 |
| 029 | mcp-bootstrap-and-self-explain | **Shipped** | `agency_welcome` + `agency_install` + `intent_bootstrap` substrate tools | (flip frontmatter) |
| 030 | jules-key-doctor-stateful-welcome | **Shipped** | `agency_doctor` + stateful welcome + JULES_API_KEY clarity | (flip frontmatter) |
| **031** | skills-progressive-disclosure | Partial | Per-spec skill rendering — `emit_skill`, references, bash wrappers | Active work on main (multiple recent commits) |
| **032** | templates-schemas-oop-extensions | Partial | Materialised schemas + draft-07 validation + OOP extension dataclasses | Active work on main; capability_loader, path-safety landed |
| 039 | distribution-and-e2e-hardening | **Shipped** | pipx + three console-scripts + discovery shims + E2E MCP tests + install-collision guard | v1 ships Distribution + E2E core; 17/18/19 incorporation scope-cut to follow-up PRs. 543 + 4 E2E tests green; agency_doctor reports install_method; install-collision detection; shim exit-127 discipline tested |
| 040 | subagent-decision-heuristics | **Shipped** | 11-signal dispatch heuristic + cache/Jules budget model + dispatch-decision skill folder | 36 tests green (25 new extended + 11 updated original); `delegate.dispatch_decision` extended; skills/dispatch-decision/ + 4 references; CLAUDE.md Rule #3 updated |
| 041 | implementation-discipline-skills | Not started | Port 3 Superpowers skills + 2 deepenings | Designed in this branch |
| 042 | analyze-capability | **Shipped** | 4-axis decidable analysis (quality/security/performance/architecture) + run/improve/cleanup acts; code-analysis skill | 33 spec tests + 502 full-suite green; 4 code-review passes + 2 dogfood-driven false-positive fixes (`from __future__` + `__all__`); lint_capability ok=True block mode; engine dedupe bug fixed alongside |
| 043 | document-capability | **Shipped** | render (4 scopes graph→md) + explain (3 depths, composition not generation) + index_repo (94% reduction; self-test < 3K tokens on agency repo) + repo-briefing skill | 29 spec tests + 532 full-suite green; 3 code-review passes incl. dogfood-driven fix (P002 false-positive on int counter caught by meta-dogfood); lint_capability ok=True block mode; intent-filter edge-traversal bug caught + regression test added |
| 044 | research-capability | **Shipped** | lead+specialist+verify verbs; 3 specialist roles (codebase/prior-reflections/doc-corpus); 2 verifier checks (evidence-supports-claim + contradiction-cluster); web boundary slot reserved | 23 spec tests green; dogfooded via wire (composes 040+045+048); web specialist defers to v2 (no default driver); v2 followups: document.render(scope='research-report') + web-reachability check |
| **049** | naming-and-token-economy | Not started | Audit + proposal spec for renaming substrate tools + capability verbs to reduce token-cost of every discovery call | Drafted from user audit 2026-06-03; pairs with future Spec 050 implementation PR; lands ONLY the audit + per-name verdict (KEEP / ALIAS-AND-RENAME / RENAME-HARD), not the renames themselves |
| 045 | reflect-semantic-recall | **Shipped** | TF-IDF + optional BGE embedder; `reflect.recall_semantic` verb; agency_doctor surfaces backend + fallback | 19 spec tests + 469 full-suite green; 4 code-review passes (F4 zip-sort cleanup, F9 doctor fallback messaging differentiated by failure mode, F13 k<=0 guard, DRY KNOWN_EMBEDDERS) |
| 046 | micro-extensions-bundle | Not started | Code-review split + visual-companion + smart-commit + estimate + token-efficiency + doc-autosync | Designed in this branch |
| **047** | cluster-integration | **Shipped** | Master plan: 13-cluster integration map (Discovery/Plan/Impl/Quality/Debug/Cleanup/Doc/Memory/Git/Research/Orch/Meta/Plugin) | The deliverable IS the plan — no code; promotes individual cluster plans to standalone specs when criteria hit (cluster-section > 150 LOC OR ≥ 3 cross-cluster decisions) |
| **048** | intent-chain-and-owners | **Shipped** | PARENT_INTENT edge + closed owner enum {user/agent/subagent/jules/system} + analyze.paths axis (IP001/IP002/IP003) + render(provenance) sub-intents | User-requested for session traceability + capability-opportunity detection. 25 spec tests green; dogfooded via wire (5-deep chain → IP001 fires); 2 minor regression-test updates for the new axis enum |

## Suggested implementation order (next 5)

Per `Plan/000-overview.md` § "Recommended next implementation order"
plus this branch's audit bundle:

1. **Spec 020** finish — `dogfood.export` (one verb away).
2. **Spec 021** — engine-monitor-channel (hard-blocks 011 + 022).
3. **Spec 040** — subagent-decision-heuristics (informs 042-046).
4. **Spec 017** — graph-native-dogfood-ledgers (depends on 020).
5. **Spec 010** — novel domain Loop 0+1 (in parallel with above; F1-F5
   Gemini-deep-research prompts already shipped under
   `research/novel-prompts/`).

## When to update this file

Update THIS file (TODO.md) in the SAME PR / commit when:

1. A spec ships (Not started / Partial → Shipped). Move row's Status
   column; bump verdict-counts at top.
2. A spec's implementation makes meaningful progress (Not started →
   Partial; document the partial scope in `Plan/NNN-…/spec.md`'s
   Followup section).
3. A new spec gets a folder under `Plan/`. Add a row here.
4. A spec is closed (deferred / superseded / cancelled). Note in row's
   "Blocker / Next step".
5. A spec is renumbered (rare; happens on naming collision after a
   merge — see 2026-06-02 history where 031-038 became 039-046).

Per-spec deep state (test counts, file:line evidence, verbatim
"Done / Still-to-implement / Refinement needed") lives in each
`Plan/NNN-…/spec.md`'s `## Followup — Implementation Status (…)` section.
This file rolls up; that section grounds.

## Pointers

- Per-spec details: `Plan/NNN-slug/spec.md` § Followup section.
- Historical overview: `Plan/000-overview.md`.
- The doctrine drives implementation order: see CLAUDE.md Rule §
  "Decide before dispatching" — do not parallelise spec implementation
  unless dependencies are crisp.
