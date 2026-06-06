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
> **Last reviewed:** 2026-06-06 (branch `claude/affectionate-meitner-H4vTJ`).
> Verdict counts reconciled row-by-row against the Status column (the
> 2026-06-05 glance had drifted — 016/019/023/059/061/062/064 were
> Shipped but undercounted, 001/016/023 sat in Partial, 032 had moved to
> Superseded). Specs 008 + 009 closed as superseded this pass.

## Verdicts at a glance

| Verdict | Count | Specs |
|---|---|---|
| **Shipped** | 30 | 001, 012, 013, 015, 016, 017, 019, 020, 023, 029, 030, 039, 040, 042, 043, 044, 045, 047, 048, 050, 052, 053, 054, 055, 059, 060, 061, 062, 064, 065 |
| **Partially implemented** | 6 | 006, 007, 018, 024, 025, 031 |
| **Not started** | 17 | 002, 003, 004, 005, 010, 011, 014, 021, 022, 026, 041, 046, 049, 051, 056, 057, 058 |
| **Closed / Superseded** | 5 | 008 (→042), 009 (→041+046), 028 (→060), 032 (→060), 063 (→065) |

Total spec rows: **58** (001–065, with 027 + 033–038 renumbered away).

## Status table

| Spec | Slug | Status | One-line | Blocker / Next step |
|---|---|---|---|---|
| 001 | toolresult-and-typed-errors | **Shipped (carry-over → 059)** | Internal `ToolResult` envelope (Option C) + `Registry.invoke` unwraps `.data` + records warnings/archived_to/PRODUCES from artefacts_written | Q-2 wire-contract territory superseded by Spec 019; remaining convenience-layer work (Codes, .success/.failure, trace_id stamping, "when to use" doctrine) carried over to Spec 059. Spec text + frontmatter kept verbatim per supersede pattern (GOALS.md #7) |
| 002 | boundary-driver-protocol | Not started | Generic Boundary/Driver + DriverRegistry | Hard-blocks 007's full music surface |
| 003 | skill-phase-objects | Not started | Typed `Skill`/`Phase` parse/validate boundary | Wave-1 backlog; revisit when canon needs new ground |
| 004 | template-schema-coverage | Not started | Wire generate/validate loop for uncovered kinds | Wave-1 backlog |
| 005 | context-mode-and-token-economics | Not started | Output-overflow capture + recall | Wave-1 backlog |
| 006 | core-hardening | Partial | Red-team fixes: tick, pagination, verify | Fixes #1 O(1), #2 `seen_tokens`, #4 `capture_api_key` absent; `tests/test_hardening.py` missing |
| 007 | music-domain-capability | Partial | Music domain (in `examples/music.py`) | Full surface depends on 002 driver registry |
| 008 | superclaude-analysts | **Closed (superseded → 042)** | SuperClaude analysis (`transmute` cluster) | Closed 2026-06-06. The `analyze` capability (Spec 042, Shipped) delivers the 4-axis decidable analysis this spec scoped via a `transmute` cluster; no separate port needed. Frontmatter flipped; spec text kept verbatim per supersede pattern (GOALS.md #7) |
| 009 | superpowers-remainder | **Closed (superseded → 041 + 046)** | Finish the superpowers port | Closed 2026-06-06. Remaining superpowers surface is carried by Spec 041 (implementation-discipline-skills) + Spec 046 (micro-extensions-bundle); both supersede the catch-all "remainder" port. Frontmatter flipped; spec text kept verbatim |
| 010 | novel-domain | Not started | Novel domain (Dramatica/NCP, gates) | 0% impl; 7 loops sequenced; spec rebased 2026-05-31 |
| 011 | agentic-capabilities | Not started | Agentic guardrails (middleware + `gate` + skill) | Depends on Spec 021 monitor channel |
| 012 | jules-complete-lifecycle-and-watcher | **Shipped** | Full Jules v1alpha + watcher + recovery | (frontmatter says draft — flip to done) |
| 013 | jules-skills-and-capability-improvements | **Shipped** | 6 Jules skills + AGENCY_PROTOCOL + lint + flag matrix | (flip frontmatter) |
| 014 | observation-to-spec-amendment | Not started | Reflection → spec-amendment loop | Depends on 017 + 020 |
| 015 | architecture-review | **Shipped** | Architecture review docs + 017/018/019 promoted | (milestone; review-only spec) |
| 016 | capability-authoring-doctrine | **Shipped** | 11 authoring hints + folder-form discover + Hint #7 docstring sweep complete (49 verbs all carry Inputs:/Returns:/chain_next:) | Phase 5 fixture cleanup partial; Phase 6 → 028 |
| 017 | graph-native-dogfood-ledgers | **Shipped** | dogfood.note (act) + dogfood.render (transform) close Goal 7 write-side gap; collect deprecated for ongoing use | 10 spec tests green; backward-compat preserved (plan_slug optional, collect still works); follow-up: jules-self-improvement Phase 0 + install.py canon-comment + CLAUDE.md rule #2 cross-ref |
| 018 | cli-token-efficiency-bundle | Partial | 5 token wins + Jules's `--fields` + traceback wrapper | Depends on 016 lint scaffold + 020 |
| 019 | engine-output-shape-contract | **Shipped** | Defensive comment at engine.py unwrap site + `wire_shape` lint rule + docstring sweep (10 verbs corrected) + test landmark + CAPABILITY-AUTHORING.md §"Wire shape vs internal wrap" + CORE.md addendum | 5 unwrap-contract tests green; 0 wire_shape leaks across live registry |
| 020 | central-graph-db | **Shipped** | v2: `.agency/session.db` + DB path resolution + `.agency/` scaffold + `dogfood.export` + `dogfood.import` (JSON round-trip preserving ids + vfrom/vto windows) — closes merge-conflict recovery loop | 10 export tests + 10 import tests green; round-trip verified |
| 021 | engine-monitor-channel | Not started | Engine-level Monitor channel (1 monitors.json) | **Hard-blocks 022 and 011** |
| 022 | jules-monitor-capability | Not started | First use of 021 for Jules watcher transitions | Depends on 021 |
| 023 | adaptive-disclosure | **Shipped** | Token-budget gate + brief slices + substrate-tool brief-slicing parity + Hint #7 docstring migration roster 0 non-compliant | Phase 3 structured `search` delta-shape + Phase 4 intent-slice filter remain deferred to v2 |
| 024 | capability-authoring-discipline | Partial | Block-mode lint when `# agency-scaffold: v1` marker present | Sweep of existing capabilities for marker addition |
| 025 | skill-first-discovery | Partial | Skill-search ranks above tool-search | Refinement needed per consolidation pass |
| 026 | skills-as-core-capability | Not started | Skill surface as a first-class capability | Depends on 016 cleanup |
| 028 | jules-folder-migration | **Absorbed → 060** | Folder-form `jules/` lands as heavy-migration wave of Spec 060 | Closed standalone; carries over verbatim into 060 |
| 029 | mcp-bootstrap-and-self-explain | **Shipped** | `agency_welcome` + `agency_install` + `intent_bootstrap` substrate tools | (flip frontmatter) |
| 030 | jules-key-doctor-stateful-welcome | **Shipped** | `agency_doctor` + stateful welcome + JULES_API_KEY clarity | (flip frontmatter) |
| **031** | skills-progressive-disclosure | Partial | Per-spec skill rendering — `emit_skill`, references, bash wrappers | Active work on main (multiple recent commits) |
| **032** | templates-schemas-oop-extensions | **Superseded → 060** | Substrate shipped (loader+dataclasses+materialiser+path-safety+agency/render); inert: no cap declares render_templates / artefact_schemas | Superseded 2026-06-03 — Spec 060 ships the missing 30% (bootstrap wire-up + per-capability migrations + agent-instruction doctrine + lint rule) |
| 060 | templates-schemas-agent-instructions | **Mostly shipped** | Bootstrap wire-up + agent-instruction doctrine + lint rule + 10 capability folder-migrations + 15 schema files + 7 template files. Substrate fix: as_capability deepcopy resolves shared-dict bug. sys.modules aliases preserve legacy `_jules_*` paths. Phases 1+2+3+4+6 complete | 663 tests + 1 skip green. Phase 5 (verb migration to `ctx.template()`) remains as opt-in: dogfood.render migrated; jules._main.preambles + document.explain + analyze.run/improve can flip when iteration pressure justifies. Phase 7 review loop closed for this wave. |
| 039 | distribution-and-e2e-hardening | **Shipped** | pipx + three console-scripts + discovery shims + E2E MCP tests + install-collision guard | v1 ships Distribution + E2E core; 17/18/19 incorporation scope-cut to follow-up PRs. 543 + 4 E2E tests green; agency_doctor reports install_method; install-collision detection; shim exit-127 discipline tested |
| 040 | subagent-decision-heuristics | **Shipped** | 11-signal dispatch heuristic + cache/Jules budget model + dispatch-decision skill folder | 36 tests green (25 new extended + 11 updated original); `delegate.dispatch_decision` extended; skills/dispatch-decision/ + 4 references; CLAUDE.md Rule #3 updated |
| 041 | implementation-discipline-skills | Not started | Port 3 Superpowers skills + 2 deepenings | Designed in this branch |
| 042 | analyze-capability | **Shipped** | 4-axis decidable analysis (quality/security/performance/architecture) + run/improve/cleanup acts; code-analysis skill | 33 spec tests + 502 full-suite green; 4 code-review passes + 2 dogfood-driven false-positive fixes (`from __future__` + `__all__`); lint_capability ok=True block mode; engine dedupe bug fixed alongside |
| 043 | document-capability | **Shipped** | render (4 scopes graph→md) + explain (3 depths, composition not generation) + index_repo (94% reduction; self-test < 3K tokens on agency repo) + repo-briefing skill | 29 spec tests + 532 full-suite green; 3 code-review passes incl. dogfood-driven fix (P002 false-positive on int counter caught by meta-dogfood); lint_capability ok=True block mode; intent-filter edge-traversal bug caught + regression test added |
| 044 | research-capability | **Shipped** | lead+specialist+verify verbs; 3 specialist roles (codebase/prior-reflections/doc-corpus); 2 verifier checks (evidence-supports-claim + contradiction-cluster); web boundary slot reserved | 23 spec tests green; dogfooded via wire (composes 040+045+048); web specialist defers to v2 (no default driver); v2 followups: document.render(scope='research-report') + web-reachability check |
| **049** | naming-and-token-economy | Not started | Audit + proposal spec for renaming substrate tools + capability verbs to reduce token-cost of every discovery call | Drafted from user audit 2026-06-03; pairs with future Spec 050 implementation PR; lands ONLY the audit + per-name verdict (KEEP / ALIAS-AND-RENAME / RENAME-HARD), not the renames themselves |
| **050** | analyze-deps-integration | **Shipped** | `[analyze]` extra wires ruff + bandit + radon into analyze axes (compose, don't replace) | 9 spec tests green; live dogfood (this repo) activates 700+ ruff rules, bandit B-series, radon CC+MI; silent fallback when deps missing; agency_doctor reports analyze_extras |
| **051** | analyze-architecture-networkx | Not started | networkx-driven A001 cycle refactor + A004 fan-out / A005 fan-in / A006 god-module metrics | Drafted from deps-extension push; warm-recommend dep |
| **052** | research-web-httpx | **Shipped** | DuckDuckGoClient zero-config default + AGENCY_WEB_BACKEND env resolution + web-reachability check (3rd verifier check) | 13 spec tests green; live wire confirms 3-check verify payload; closes Spec 044 v1 scope-cut |
| **053** | test-suite-organization-ci | **Shipped** | conftest auto-markers + pytest-xdist + slicing scripts (test-cap, test-changed) + CI workflow upgrade | analyze 6.6s, research 12.2s, dogfood 17.8s; full parallel 2:43 vs 4:13 sequential (35% speedup); CI: `pytest -n auto -m "not e2e"` + E2E on tag |
| **054** | drift-management | **Shipped** | AGENCY-DRIFT code tags + scripts/check-drift + agency_doctor.drift field + CLAUDE.md Rule #6 + README install rewrite | 8 canonical tag sites seeded; live `scripts/check-drift` reports NO DRIFT on this branch; v1 ships tag-convention guard layer, install dry-run drift, capability-test-gap report |
| **055** | pipx-only-install | **Shipped** | bin/agency-install removed; bin/agency-mcp + bin/agency reduced to thin PATH routers; collision guard vestigial; install_method enum 5→2 values; tests rewritten | One canonical install path (pipx); marketplace install still works (shim routes to pipx); 22 distribution+install tests in 2.6s; README + docs/getting-started.md migrated |
| 056 | type-safe-node-id-discipline | Not started | `memory.recall_typed(id, label)` substrate helper + `_check_node_id_guards` lint rule + audit/migration of 3+ existing guards | Drafted 2026-06-03 from session learnings; three independent label-check bugs surfaced in PR #17 review = systemic. Depends on 016 + 019. |
| 057 | analyzer-rule-axis-registry | Not started | Each `_<tool>.py` analyzer wrapper declares its `AXIS_PREFIXES` constant; `_main.py` builds registry by union | Drafted 2026-06-03 — refactors round-2 review fix from "central if-elif" to "wrapper-local declaration"; cleaner extension surface for future linters (mypy, pylint, semgrep). Depends on 050. |
| 058 | reflection-link-lint | Not started | `_check_reflection_links` lint rule: a verb writing Reflection must link BOTH SERVES and OBSERVED_DURING | Drafted 2026-06-03 from the document.explain bug pattern in PR #17 round-1 review; pairs with Spec 016/019 lint scaffold extensibility. Expect 1-3 sites to migrate. Depends on 016 + 019. |
| 059 | toolresult-convenience-layer | **Shipped** | Codes namespace + `.success`/`.failure` ctors + `Registry.invoke` stamps `error.trace_id` via `dataclasses.replace` + `next_cursor` opt-in + "when to use ToolResult vs plain dict" doctrine | 6 tests green in 0.62s; closes the carry-over from Spec 001 |
| 061 | install-surface-refresh | **Shipped** | `.mcp.json` PYTHONPATH stripped (vestigial post-Spec 055); `marketplace.json` description now reads the live registry (cap count + first-7 surface signal, bounded < 400 chars); README capability table 11→14 rows; test count 216+→663; stale docstring references cleaned | Drafted + shipped 2026-06-04 from review-from-scratch audit. 2 new tests assert `.mcp.json` env shape + dynamic description. |
| 062 | session-start-pipx-install | **Shipped** | SessionStart hook (`hooks/session-start.sh` + `hooks/hooks.json`) auto-runs `pipx install --editable ${CLAUDE_PLUGIN_ROOT}` on first session so marketplace installs (esp. Claude Code Web) don't silently fail. Idempotent (early-exit when agency-mcp already on PATH); pip --user fallback; install.py regen wires the hook into generate(); install.write() marks hooks/*.sh executable | 5 new tests green; README documents the auto-install flow + fallback chain |
| 063 | venv-fallback-install-path | **Superseded → 065** | Original 3-step fallback chain shipped, then withdrawn after PR #19 review surfaced 4 P2 correctness issues (shim self-detection on PATH, pip --user PATH not guaranteed, Windows venv layout, wrong python interpreter for scaffold-db). Spec 065 replaces with pipx-only doctrine | Superseded 2026-06-05; frontmatter flipped; venv/pip-user code paths removed |
| 064 | plugin-reference-compliance | **Shipped** | Cross-platform polyglot wrapper `hooks/run-hook.cmd` + extensionless `hooks/session-start`; `hooks.json` gains `matcher: "startup\|resume\|clear"` + `async: false`; `.mcp.json` gains `cwd: ${CLAUDE_PROJECT_DIR}` + `env_vars` passthrough (AGENCY_EMBEDDER etc); `${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}` fallback for Cursor/Codex; new `skills/using-agency/SKILL.md` broad-trigger meta-skill mirrors using-superpowers pattern; `install.write()` chmods any `hooks/*` file (not just `.sh`) | 10 new tests green; mirrors superpowers 5.1.0 + episodic-memory 1.4.2 reference patterns |
| **065** | pipx-direct-doctrine | **Shipped** | Pipx-only install (no shims, no venv fallback); `bin/agency` + `bin/agency-mcp` removed; `.mcp.json` uses bare `command: "agency-mcp"` (PATH-resolved); SessionStart hook prints HINT pointing at pipx.pypa.io when pipx missing; `agency` CLI grows `install`, `welcome`, `doctor`, `provenance` subcommands wrapping the substrate MCP tools; all docs (`README.md`, `docs/getting-started.md`, `docs/guide/extending.md`, `AGENTS.md`, `skills/using-agency/SKILL.md`) sweep `python -m agency.cli` → `agency` and `python -m agency.install` → `agency install` | Closes 4 P2 findings from PR #19; 683 passed + 1 skipped + 4 deselected (3m51s); 6 distribution-shim tests deleted; 5 new CLI subcommand tests added; supersedes Spec 063 |
| 045 | reflect-semantic-recall | **Shipped** | TF-IDF + optional BGE embedder; `reflect.recall_semantic` verb; agency_doctor surfaces backend + fallback | 19 spec tests + 469 full-suite green; 4 code-review passes (F4 zip-sort cleanup, F9 doctor fallback messaging differentiated by failure mode, F13 k<=0 guard, DRY KNOWN_EMBEDDERS) |
| 046 | micro-extensions-bundle | Not started | Code-review split + visual-companion + smart-commit + estimate + token-efficiency + doc-autosync | Designed in this branch |
| **047** | cluster-integration | **Shipped** | Master plan: 13-cluster integration map (Discovery/Plan/Impl/Quality/Debug/Cleanup/Doc/Memory/Git/Research/Orch/Meta/Plugin) | The deliverable IS the plan — no code; promotes individual cluster plans to standalone specs when criteria hit (cluster-section > 150 LOC OR ≥ 3 cross-cluster decisions) |
| **048** | intent-chain-and-owners | **Shipped** | PARENT_INTENT edge + closed owner enum {user/agent/subagent/jules/system} + analyze.paths axis (IP001/IP002/IP003) + render(provenance) sub-intents | User-requested for session traceability + capability-opportunity detection. 25 spec tests green; dogfooded via wire (5-deep chain → IP001 fires); 2 minor regression-test updates for the new axis enum |

## Suggested implementation order (next 5)

Refreshed 2026-06-06 (the prior list named 020 + 040, both Shipped).
Ranked by leverage — what unblocks the most downstream work first:

1. **Spec 021** — engine-monitor-channel. Highest leverage: hard-blocks
   BOTH 022 (jules-monitor) and 011 (agentic-guardrails). Substrate;
   depends only on Shipped 020. *(in progress, branch
   `claude/affectionate-meitner-H4vTJ`)*
2. **Specs 056 + 057 + 058** — review-driven lint batch (type-safe
   node-id, analyzer-rule-axis-registry, reflection-link-lint). Cheap:
   1–3 sites each; deps (016 + 019 + 050) all Shipped; share the lint
   scaffold context so they batch cleanly.
3. **Spec 049** — naming-and-token-economy audit. Cuts the token cost of
   every discovery call; audit-only, low-risk; do before more verbs accrete.
4. **Spec 002** — boundary-driver-protocol. Generic Boundary/Driver +
   DriverRegistry; unblocks Spec 007's full music surface.
5. **Spec 010** — novel domain Loop 0+1 (F1–F5 Gemini-deep-research
   prompts already shipped under `research/novel-prompts/`).

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
