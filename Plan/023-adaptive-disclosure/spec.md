---
spec_id: "023"
slug: adaptive-disclosure
status: draft
owner: "@agency"
depends_on: ["016", "018", "019"]
affects:
  - agency/engine.py                              # search/get_schema signatures + surface auto-detect
  - agency/capability.py                          # docstring → T1/T2/T3 chunk parse at registration
  - agency/render.py                              # NEW — render(node, surface, depth, format)
  - agency/intent.py                              # match_score for intent-slice filter
  - agency/install.py                             # per-surface skill section rendering
  - agency/capabilities/plugin.py                 # lint_capability docstring contract (pair w/ Spec 016 Phase 4)
  - tests/test_render.py                          # NEW — RED→GREEN matrix
  - tests/test_search_delta_shape.py              # NEW — verifies new search return shape
estimated_jules_sessions: 0  # spec-panel + Codex review first, then inline TDD
domain: meta / engine-output
wave: 3
---

# Spec 023 — Adaptive disclosure (token-efficient slice emission)

## Why

Every `search` result and skill body the engine emits today is a fixed,
maximum-detail rendering. Concrete waste from the live registry (49 verbs):

- A typical `search "reflect note"` returns **~500 tokens** of docstring prose;
  the agent reading it usually needs the **~100 tokens** of signature + role +
  one-line gist.
- The `help` skill emitted by `install.py` after 68cf4d2 bundles MCP + bash
  forms (80 lines); an MCP-only Claude Code session pays for the bash half it
  never executes.
- The 49 verb docstrings sum to ~5k tokens; a real task discovers via 3–5 of
  them. The other ~4.5k tokens are deadweight.
- `develop.reference` already implements a T1/T2/T3 progressive disclosure
  pattern — but only for *disciplines*, not for the search surface itself.

**The canon's promise (`GOALS.md` #1) — "the full tool list never loads into
context" — is partially false today.** `search` does narrow the catalog; it
does not narrow the prose-per-match. Spec 023 closes that gap.

## Done When

- [ ] `agency/render.py` lands as a single entry point:
  `render(node, *, surface, depth, format) -> str` where:
  - `surface` ∈ {`mcp`, `bash`} — never `both` in render output (panel F3.2;
    `both` would double the emission and defeat the point).
  - `depth` ∈ {`brief`, `standard`, `deep`}; default `brief`.
  - `format` ∈ {`markdown`, `json`, `snippet`}; default `markdown`.
- [x] **v1 (shipped, dadd9d1)**: `agency/engine.py:_wire()` parses the
  verb's docstring at registration via `parse_slices()` and caches the
  **brief slice** as `impl.__doc__` — this is what FastMCP's catalog
  reads. Other slices are computed on demand by `render_verb` (fast: one
  `re.search` per axis on a ≤2KB string). No `_render_slices` cache
  populated in v1 because the brief alone closes the Phase-7 budget gap.
  v2 promotes to a `dict[(surface, depth, format), str]` cache on
  `VerbSpec` if profiling shows render hot-path cost (current measurement:
  negligible).
- [ ] **v2 (deferred)**: When v2 lands, verbs WITHOUT Spec-016-Hint-#7
  compliant docstrings get a single `(mcp, standard, markdown)` fallback
  slice; `plugin.lint_capability` (paired with Spec 016 Phase 4) flags them.
- [ ] `agency/engine.py` `search` signature extended:
  `search(query, *, depth='brief', intent_id=None, format='markdown', limit=20)`.
  Surface is **NOT** a runtime kwarg (panel F1.1 — removed to eliminate
  drift). Returns the delta shape (see below). The previous verbose dump is
  reachable via `depth='deep'`.
- [ ] **Surface resolution** (panel F1.1 + F3.3) — single source of truth:
  ```
  arg (CLI --surface=)  >  env (AGENCY_SURFACE=mcp|bash)  >  auto
  ```
  `auto` resolution:
  1. `ctx.client` exposes `mcp__plugin_agency_agency__execute` → `mcp`
  2. `ctx.client` is `JulesClient` → `bash`
  3. **Introspection unresolved → `mcp`** (panel F3.2 — the more-capable
     surface; bash agents can read MCP prose, MCP agents seeing bash prose
     can't call the bash tools)
- [ ] `agency/intent.py` exposes `match_score(intent_id: str, text: str) -> float`
  via token Jaccard over `purpose + acceptance`. Used by `search`'s
  intent-slice filter when `intent_id` is supplied. **Complexity**:
  `O(verbs × intent_tokens)` ≈ 49 × 20 = ~1k char-ops/search (panel F2.1 —
  bound pinned for the perf-engineer's audit trail). Meta-verbs
  (`*_help`, `*_search`, `*_capture`) always pass the floor.
- [ ] New `search` return shape (panel F1.3 — structured `next`, not hint
  string; panel F1.2 — `score` schema is explicit "present iff intent_id
  supplied"):
  ```json
  {
    "matches": [
      {
        "name": "capability_reflect_note",
        "role": "act",
        "brief": "Write a scope-tagged insight node; SERVES the intent.",
        "schema_hint": "scope, text, intent_id",
        "score": 0.42
      }
    ],
    "next": {"verb": "get_schema", "args": {"name": "<match.name>"}},
    "total": 12,
    "truncated": false
  }
  ```
  `score` is present iff the caller passed `intent_id`; otherwise the field
  is omitted (not `null` — saves 8 bytes × matches).
- [ ] `agency/install.py` skill rendering emits per-surface H2 sections with
  a `## Quick start — <surface>` heading convention so the skill loader (or
  the agent reading the skill) can pick the section that matches its harness.
  Research item Q2 below decides if separate `SKILL.md` files per surface are
  preferable; default for v1 is single-file-with-sections.
- [ ] **Token-budget acceptance** (panel F2.3 — pinned definition):
  `search "reflect note"` on the live registry returns **JSON-wire bytes
  whose tiktoken cl100k count is ≤120 tokens** (currently ~500). Measured
  via `tests/test_token_budget.py`. Tiktoken is the project's stable proxy
  for the Claude tokenizer; char-count fallback for minimal-install CI.
- [ ] **Isomorphism acceptance** (panel F3.1 — re-spec): the MCP form
  `mcp__plugin_agency_agency__search(...)` and the CLI form
  `python -m agency.cli search ...` return values that are
  **structurally identical after JSON parse** (not byte-identical — MCP
  ships Python dicts on the wire, CLI ships stringified JSON via stdout).
  Asserted by `tests/test_search_isomorphism.py`.
- [ ] **Migration roster** (panel F4.1 — concrete, falsifiable):
  - Compliant docstrings today (5 verbs, sampled from grep `Returns: \\{`):
    `jules.dispatch`, `jules.review_comment`, `delegate.dispatch_decision`,
    `reflect.batch_note`, `plugin.help` — verified via
    `tests/test_docstring_compliance_roster.py`.
  - Non-compliant: the remaining 44 verbs.
  - Migration lands in Spec 016 Phase 4 (lint_capability) FIRST; Spec 023
    GREEN waits on the roster shrinking to 0 non-compliant via the lint
    gate. **Paired ship order**: 016 P4 → 023.
- [ ] **Test sweep** (panel F4.2): grep for tests that assert on
  pre-render docstring shape and update them BEFORE flipping `search`'s
  default depth.
- [ ] **Third-party authors contract** (panel F4.3): docs page states
  "Capability authors write Spec-016-Hint-#7 docstrings; the engine derives
  render slices automatically. No hand-written slices."
- [ ] `python -m pytest -q` stays green (234 baseline + new tests).

## Architecture

### Rendering pass first (no schema change)

The graph stays the store; `render.py` is the view. Each `VerbSpec` carries
`_micro_chunks` derived at registration — a pure transform of the docstring
the author already wrote. No new node types in v1.

If the (surface, depth, format) combinatorics later need per-surface variants
stored independently (e.g. an MCP-specific example with no bash equivalent),
v2 promotes to a `MicroSkill` node linked `RENDERS_AS` to the canonical Skill
(panel item to discuss; not in v1).

### The four axes

| Axis | Values | Default | Source of truth |
|---|---|---|---|
| **Surface** | `mcp` / `bash` / `both` | `auto` → `ctx.client_surface()` | Engine introspection |
| **Depth** | `brief` / `standard` / `deep` | `brief` | T1/T2/T3 of the docstring |
| **Intent slice** | `any` / `<intent_id>` | auto-injected | Jaccard over Intent.purpose+acceptance |
| **Format** | `markdown` / `json` / `snippet` | `markdown` | Renderer dispatch |

Orthogonally composable: 3 × 3 × 2 × 3 = 54 combos. Tests pyramid — each axis
independently + a smoke subset of the matrix.

### Docstring cleavage rules (paired with Spec 016 Hint #7)

A Spec-016-Hint-7-compliant docstring:

```python
"""Spawn a remote Jules session.                          # T1: gist (the lead line)

Inputs: source (owner/repo), starting_branch, prompt,     # T2 chunk: standard
        title?, require_plan_approval=True, ...
Returns: {status, session, url, alias, artefact}.         # T2 chunk: standard
chain_next: jules.status(session=) once dispatched;       # T3 chunk: deep
            jules.approve_plan if state in {...}.

Free-text body explaining nuances ...                     # T3 chunk: deep
"""
```

The parser splits on those markers. Non-compliant docstrings fall back to
`(both, standard)` — the whole docstring as one chunk — and
`lint_capability` warns.

## Surfaces

### MCP (in-process, code-mode)

```python
# brief by default
r = await mcp__plugin_agency_agency__search(query="reflect note")
# delta-shape; iterate r["matches"]
```

### Bash CLI (Jules / no-MCP)

```bash
agency --db .agency/session.db search "reflect note" --depth=brief --format=json
```

Both surfaces are isomorphic — same `search(query, **kwargs)` underneath,
same delta shape returned. The CLI parses `--depth=` / `--format=` /
`--surface=` / `--intent-id=` into the kwargs.

## Files

- **Create:**
  - `agency/render.py` — the renderer.
  - `tests/test_render.py` — axis-independent and matrix-smoke coverage.
  - `tests/test_token_budget.py` — the ≤120-token acceptance.
  - `tests/test_search_isomorphism.py` — MCP ≡ CLI assertion.
  - `Plan/023-adaptive-disclosure/IMPLEMENTATION-PLAN.md` — Workflow output.
- **Modify:**
  - `agency/engine.py` — extend `search` / `get_schema` signatures; add
    `ctx.client_surface()` helper.
  - `agency/capability.py` — registration-time docstring parse →
    `_micro_chunks`.
  - `agency/cli.py` — new `--depth/--surface/--intent-id/--format` flags on
    `search` + `get-schema`.
  - `agency/intent.py` — `match_score`.
  - `agency/install.py` — per-surface H2 sections in the help skill.
  - `agency/capabilities/plugin.py` — `lint_capability` (paired with Spec 016
    Phase 4) flags non-compliant docstrings.

## Open Questions (research items — resolved in spike or v2)

1. **fastmcp client introspection.** Does `ctx` expose the calling client's
   tool list reliably (so `auto` resolution detects `mcp` vs `bash`), or do
   we fall back to a session-level flag set at engine construction? Either
   way, the F3.2 fallback (`mcp`) is safe — but accurate detection improves
   the bash path. **Spike before implementation Phase 2.** Research target:
   fastmcp 3.3.1 source under `.venv/lib/python3.11/site-packages/fastmcp/`.

2. **Skill loader frontmatter.** Does Claude Code respect a custom
   `surface: mcp` frontmatter key on `SKILL.md` for per-harness skill
   selection? If yes, v1 emits separate `skills/help-mcp/SKILL.md` +
   `skills/help-bash/SKILL.md`. If no, v1 stays single-file-with-sections.
   **Defer to v2** — single-file-with-sections is workable for v1.
   Research target: `working-with-claude-code` skill's `skills.md` ref.

3. **`get_schema` interaction with `depth`.** Resolved: `get_schema(name)`
   is always `standard` (the full signature). `deep` content goes through
   `develop.reference`. `get_schema` does NOT take a `depth` kwarg — the
   progressive flow is `search(brief) → get_schema(standard) →
   develop.reference(deep)`.

4. **MicroSkill node-promotion.** v1 is rendering-pass-only. If panel F4.3
   surfaces a third-party capability whose author legitimately needs to
   override the parser's slices (e.g. an `examples/` capability with a
   bash-only surface but no bash sibling docs), v2 promotes the slice
   storage to a `MicroSkill` node `RENDERS_AS` the Skill. Track as
   `reflection:<observation>` after first v1 ship.

## Evidence (cites)

- `docs/vision/GOALS.md:8-12` — "token-efficient agentic loops … the full
  tool list never loads into context." The promise this spec closes.
- `docs/vision/CORE.md:7-18` — search · get_schema · execute as the contract.
- `agency/engine.py` (current `search` signature) — the change site.
- `agency/capabilities/develop.py:reference` — the T1/T2/T3 precedent for
  progressive disclosure (applied today to disciplines, not to search results).
- `agency/capabilities/plugin.py:106-130` — `help_map` (the auto-generated
  capability list; would gain depth/surface awareness via `render`).
- `agency/install.py:68cf4d2` — the help skill that just doubled tokens by
  dual-emitting MCP + bash forms; the trigger for this spec.
- `Plan/016-capability-authoring-doctrine/spec.md:217-242` — Hint #7
  (docstring contract) — the cleavage points Spec 023 reads.
- `Plan/018-cli-token-efficiency-bundle/` — overlaps; this spec subsumes
  most of 018.
- `Plan/019-engine-output-shape-contract/` — codifies the new delta shape.
- `Plan/016-…/spec.md:202-217` — **Hint #6** ("Returns must be deltas, not
  dumps") — Spec 023 IS the search-side implementation of Hint #6 (panel
  F5.4 cross-link).
- `reflection:9cd97a38` (MCP/CLI DB divergence; since closed) — the artefact
  that exposed how MCP and CLI must remain isomorphic in their output too.

## Goal (the loop's exit condition)

The user's confirmed loop runs until:

1. **Token-efficient**: `search "reflect note"` ≤ **120 tokens**
   (currently ~500); typical chained discovery (`search → get_schema →
   execute`) drops from ~1200 to ~250 tokens.
2. **Works via MCP code-mode**: `mcp__plugin_agency_agency__search(...)`
   returns the delta shape; `await call_tool("capability_<x>_<y>", {...})`
   inside `execute` resolves normally.
3. **Works via CLI**: `python -m agency.cli search "reflect note"
   --depth=brief` returns byte-identical output to the MCP form (asserted by
   `test_search_isomorphism.py`).

If any iteration's measurement misses the budget, the loop re-enters
**Design (improve)** — typical fixes: tighter docstring parser, smarter
intent-slice ranking, narrower default `limit`.

## Followup — Implementation Status (2026-05-31)

> Consolidation pass on branch `claude/plan-spec-review-74gHM`. Frontmatter `status:` may be stale; this section reflects verified code state.

**Verdict:** Partially implemented

### Done

By IMPLEMENTATION-PLAN phase:

- **Phase 0 (Spec 016 Phase 4 — lint_capability + docstring migration)**: `plugin.lint_capability` landed with structural + render-slice + role-tag + consumer-contract + token-budget rules (`agency/capabilities/plugin.py:279-302`). However, the docstring migration roster (44 → 0 non-compliant) is NOT done — `reflect`, `gate`, `delegate`, `jules` all have zero Hint #7 markers. This is the gating prerequisite for 023 GREEN.
- **Phase 1 — `render.py`**: `agency/render.py` shipped with `parse_slices`, `render_verb`, `_render_markdown`, `_render_json`, `_render_snippet`, and `render_phase`. All four axes (surface/depth/format + non-compliant fallback). (`agency/render.py:1-303`; `tests/test_render.py`)
- **Phase 2 — surface resolution**: `resolve_surface(arg)` with arg > env > auto (fallback `mcp`) landed in `agency/engine.py:56-83`; `Engine.__init__` caches `self.surface`. (`tests/test_surface_resolution.py`)
- **Phase 3 — engine `_wire` brief-slice tightening (partial)**: `engine.py:_wire` sets `impl.__doc__ = parse_slices(raw)["brief"]` so FastMCP's catalog sees only the brief slice, cutting catalog tokens by >50%. (`agency/engine.py:139-141`; `tests/test_engine_brief_descriptions.py`) — this is the Phase-7 outcome shipped early, not the full Phase-3 delta-shape.
- **Phase 7 — token-budget gate**: `tests/test_token_budget.py` asserts `search "reflect note"` ≤120 cl100k tokens (and `dispatch` ≤120, `graph` ≤200). Tests pass via FastMCP's built-in search returning brief-slice descriptions.
- **Phase 6 — isomorphism (partial)**: `tests/test_search_isomorphism.py` asserts MCP and CLI search return structurally identical results. Currently verifies against the plain-text search result (not the structured delta shape); the isomorphism gate is real but precedes Phase-3's structured shape.
- **install.py per-surface H2 sections**: `agency/install.py` emits `## Quick start — MCP (Claude Code)` and `## Quick start — bash (Jules / no-MCP)` in the help skill. (`agency/install.py:67, 98`)
- **`render_phase` (Spec 025 Phase 1)**: `agency/render.py:241-303` with T1/T2/T3 tiers + verb-bound phase delegation. (`tests/test_skill_walk_slices.py`)

### Still to implement
- **Phase 3 — structured `search` delta shape**: `search(query, *, depth, intent_id, format, limit)` extended signature does NOT exist; search is FastMCP's built-in with `limit` passthrough only. The `{matches: [{name, role, brief, schema_hint, score}], next, total, truncated}` return shape is unimplemented. `tests/test_search_delta_shape.py` does not exist.
- **Phase 4 — `match_score` + intent-slice filter**: `agency/intent.py` has no `match_score`. `tests/test_intent_slice.py` does not exist.
- **Phase 5 — CLI surface flags**: `agency/cli.py` has no `--depth`, `--surface`, `--intent-id`, `--format` flags on `search` or `get-schema`. `tests/test_cli_surface_flags.py` does not exist.
- **Docstring migration roster (Phase 0 gate)**: 44 non-compliant verbs (all of `reflect`, `gate`, `delegate`, `jules`, `branch`, `workspace`, `subagent`, `dogfood`, `skill_generator`). `tests/test_docstring_compliance_roster.py` does not exist.
- **`agency/capability.py` registration-time `_micro_chunks` cache**: not added; `parse_slices` is called at `_wire` time (Phase 1 design noted v2 promotes to per-VerbSpec cache).

### Refinement needed (given later specs)
- The "paired ship order: 016 P4 → 023" means 023 GREEN formally waits on the docstring sweep (a 016 deliverable), which is also a 019 prerequisite. All three specs share the same blocking work item.
- `render_phase` was promoted to `agency/render.py` ahead of Spec 025's formal spec, effectively pre-shipping Spec 025 Phase 1. This is a positive convergence but means 025 should reference `render.py:241-303` as already done.
- Spec 018's Win 4 (compact `get_schema`) overlaps Phase 3 of 023; 023's subsumption claim in its Evidence section is correct — Win 4 should be retired from 018's backlog once Phase 3 ships.

### Evidence
- code: `agency/render.py` (Phase 1 complete), `agency/engine.py:56-83` (surface resolution — Phase 2), `agency/engine.py:139-141` (brief-slice in `_wire` — Phase 7 early), `agency/install.py:67,98` (per-surface H2)
- tests: `tests/test_render.py`, `tests/test_surface_resolution.py`, `tests/test_token_budget.py`, `tests/test_engine_brief_descriptions.py`, `tests/test_search_isomorphism.py` (partial); missing: `test_search_delta_shape.py`, `test_intent_slice.py`, `test_cli_surface_flags.py`, `test_docstring_compliance_roster.py`
- commits/notes: Spec 023 says `[x] v1 (shipped, dadd9d1)` for the brief-slice caching; confirmed. Phases 3–5 and the docstring migration remain open. Frontmatter `status: draft` is accurate.
