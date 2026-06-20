# Spec 023 — IMPLEMENTATION-PLAN

Workflow output of the Design → spec-panel → refine → **Workflow** → Implement
loop. Each phase: RED → GREEN → green `python -m pytest -q` → commit → push.
Review checkpoints between groups (agency:code-review). Token-budget gate at
the end re-enters Design if missed.

Ship order: **Phase 0 (Spec 016 Phase 4) ships BEFORE Phase 1** per the spec's
"paired ship order" — 023 GREEN waits on the lint roster reaching 0 non-compliant.

---

## Phase 0 — Spec 016 Phase 4: `lint_capability` + docstring migration

> **Prerequisite for 023.** Without compliant docstrings the parser has
> nothing to cleave on.

### 0.1 RED
- `tests/test_lint_capability.py`:
  - asserts a compliant docstring (carries `Inputs:` / `Returns:` /
    `chain_next:` markers) lints clean
  - asserts a non-compliant docstring lints with `kind=docstring_contract`
    + `fix=…` hints per marker
  - asserts `skip_lint=True` decorator (panel W3 from Spec 016) is honored

### 0.2 GREEN
- `agency/capabilities/plugin.py` — add `lint_capability(name) -> {ok,
  violations, skipped}` verb, mirror of `lint_skill`.

### 0.3 Migration roster
- `tests/test_docstring_compliance_roster.py` — enumerates the verbs the
  parser must handle; baseline 5 compliant / 44 non-compliant.
- Migrate the 44 non-compliant verbs to Hint #7 format. **Mechanical**
  per-verb; one commit per cluster of ≤8 verbs.
  - `reflect`, `gate`, `develop`, `dogfood`, `workspace`, `branch`,
    `delegate`, `subagent`, `skill_generator`, `plugin` (the ones likely
    landing one cluster each).
  - `jules` (heaviest) — one commit per sub-area: dispatch+approve,
    watch+recover, patch+apply, alias+resolve, message+stop+verify+plan.

### 0.4 Gate
- `python -m pytest -q` green.
- `lint_capability` over the live registry returns
  `{ok: True, violations: [], skipped: N}`.
- Commit + push per cluster; PR open against `main`.

### 0.5 Review checkpoint
- agency:code-review on the docstring migrations (mechanical, low-risk).

---

## Phase 1 — `render.py` + `_render_slices` on `VerbSpec`

### 1.1 RED
- `tests/test_render.py`:
  - `render(verb, surface='mcp', depth='brief', format='markdown')` returns
    `name + role + brief` only
  - `depth='standard'` adds `Inputs:` + `Returns:`
  - `depth='deep'` adds `chain_next:` + free-text body
  - `format='json'` returns `{name, role, brief, …}` dict, NOT a string
  - `format='snippet'` returns a code block with the call signature
  - `surface='bash'` swaps MCP-form examples for bash-CLI equivalents
  - Non-compliant docstring (no markers) yields the `mcp/standard/markdown`
    fallback slice — never crashes

### 1.2 GREEN
- `agency/render.py`:
  - `render(node, *, surface, depth, format) -> str | dict`
  - dispatches on node kind: `VerbSpec` → verb-render; `Skill` → skill-render
- `agency/capability.py`:
  - `_parse_slices(docstring) -> dict[(surface, depth, format), str]`
  - at `Registry.register(cap)`, walk every verb and populate
    `verb_spec._render_slices`
  - parse happens **once per engine start** (not hot-path)

### 1.3 Gate
- `python -m pytest tests/test_render.py -q` green; full suite green.
- Commit + push.

---

## Phase 2 — Engine surface auto-detect

### 2.1 SPIKE
- Read fastmcp 3.3.1 source under `.venv/lib/python3.11/site-packages/fastmcp/`
  to confirm whether `ctx` exposes the calling client's tool list.
- Decide: real introspection OR session-init flag.

### 2.2 RED
- `tests/test_surface_resolution.py`:
  - explicit `surface='mcp'` (or CLI `--surface=mcp`) → `mcp`
  - env `AGENCY_SURFACE=bash` (no arg) → `bash`
  - both unset, `ctx.client` is `JulesClient` → `bash`
  - both unset, `ctx.client` exposes the MCP execute tool → `mcp`
  - both unset, introspection fails → `mcp` (panel F3.2 fallback)
  - precedence: arg > env > auto

### 2.3 GREEN
- `agency/engine.py` — `ctx.client_surface() -> str` helper.
- Read `AGENCY_SURFACE` env once at Engine init; cache on self.

### 2.4 Gate
- Tests green; commit + push.

---

## Phase 3 — Engine `search` delta shape

### 3.1 RED
- `tests/test_search_delta_shape.py`:
  - `search(query)` returns `{matches: [...], next: {...}, total, truncated}`
    (no `result` string by default)
  - `matches[i]` has `name, role, brief, schema_hint`; no `score` unless
    `intent_id` supplied
  - `next: {verb: "get_schema", args: {name: "<placeholder>"}}` shape
  - `depth='deep'` returns the legacy verbose dump (backward-compat path)
  - `limit` default 20; `truncated=True` iff cropped

### 3.2 GREEN
- `agency/engine.py` — extend `search` signature
  `search(query, *, depth='brief', intent_id=None, format='markdown', limit=20)`.
- Dispatch each match through `render(verb_spec, surface=ctx.client_surface(),
  depth, format)`.
- Compose the delta shape.

### 3.3 Gate
- Tests green. Full suite green. Commit + push.

### 3.4 Review checkpoint
- agency:code-review on `engine.py` + `render.py` (this is the load-bearing
  surface change).

---

## Phase 4 — Intent slice + `match_score`

### 4.1 RED
- `tests/test_intent_slice.py`:
  - `match_score(intent_id, "lorem ipsum")` returns a float in [0, 1]
  - `search(query, intent_id=iid)` filters matches by score; ranks by score
  - meta-verbs (`*_help`, `*_search`, `plugin_help`, …) always present in
    matches regardless of score
  - complexity bound (sanity check): score over 49 verbs completes in <50ms

### 4.2 GREEN
- `agency/intent.py` — `match_score`: lowercase token Jaccard over
  `purpose + acceptance` ∪ verb's `brief + name-tokens`.
- `engine.search` — apply filter when `intent_id` provided; keep meta-verbs.

### 4.3 Gate
- Tests green. Commit + push.

---

## Phase 5 — CLI surface flags

### 5.1 RED
- `tests/test_cli_surface_flags.py`:
  - `agency search "x" --depth=brief --format=json` returns brief JSON
  - `agency search "x" --surface=bash --intent-id=<iid>` honors all four
  - `agency get-schema name --depth=standard` (depth flag SILENTLY no-ops
    here per spec Open Q #3 — get_schema is always standard)
  - default depth is `brief` (matches engine default)

### 5.2 GREEN
- `agency/cli.py` — wire argparse flags.
- Map flags to kwargs; pass through to engine.

### 5.3 Gate
- Tests green. Commit + push.

---

## Phase 6 — Isomorphism: MCP ≡ CLI

### 6.1 RED
- `tests/test_search_isomorphism.py`:
  - capture `mcp__plugin_agency_agency__search(query="reflect note",
    depth="brief")` via Engine.in_process
  - capture `python -m agency.cli search "reflect note" --depth=brief`
    (subprocess; parse stdout as JSON)
  - assert `json.loads(mcp) == json.loads(cli)` — **structurally identical
    after JSON parse** (panel F3.1)

### 6.2 GREEN
- If MCP and CLI diverge: track the offending field; collapse it. Likely
  candidates: `score` rounding; key ordering in dict (shouldn't matter
  after parse but worth a sanity assertion).

### 6.3 Gate
- Tests green. Commit + push.

---

## Phase 7 — Token-budget acceptance + final tuning

### 7.1 RED
- `tests/test_token_budget.py`:
  - measure `tiktoken.encoding_for_model("gpt-4").encode(json_wire_bytes)`
    of `search("reflect note", depth="brief")`
  - assert ≤120 tokens
  - fallback char-count proxy if tiktoken not installed
  - measure `search → get_schema → execute` chained discovery; assert
    ≤250 tokens cumulative

### 7.2 GREEN (only if budget missed)
- Tighten `brief` slice — drop `role` from delta if budget tight; keep
  only `name + brief + schema_hint`
- Lower default `limit` to 12
- Drop `total` if `truncated=False` (saves ~12 bytes/response)

### 7.3 Gate
- Tests green. Commit + push.

### 7.4 Review checkpoint (loop exit decision)
- If budget met → continue to Phase 8.
- If budget missed AFTER 7.2 tightening → **re-enter Design** (loop). Open
  a new Plan/023/REVISION-1.md with the gap analysis; iterate.

---

## Phase 8 — `install.py` per-surface skill sections

### 8.1 RED
- `tests/test_install_surface_sections.py`:
  - generated `skills/help/SKILL.md` carries
    `## Quick start — MCP (Claude Code)` AND `## Quick start — bash` H2s
  - `commands/help.md` mirrors
  - `allowed-tools` still lists the four MCP tools + Bash
  - skill body content is now generated via `render(skill, surface=…)` —
    test asserts the rendered content matches `render(skill, surface='mcp',
    depth='standard', format='markdown')` for the MCP section

### 8.2 GREEN
- `agency/install.py` — replace the hardcoded `_MCP_QUICKSTART` constant
  with calls through `render(skill, surface='mcp', …)` +
  `render(skill, surface='bash', …)`.
- The doctrine: install.py composes; render.py owns the slice content.

### 8.3 Regenerate
- `python -m agency.install`
- Commit the regenerated artefacts.

### 8.4 Gate
- Tests green. Commit + push.

### 8.5 Final review
- agency:code-review full diff vs `main`.
- Measure final cumulative token cost; record `reflection:<id>` in the
  graph SERVES `intent:<spec-023-impl>`.

---

## Loop exit conditions (matches spec Done When)

The Design → spec-panel → … → Improve cycle exits when ALL true:

1. ✅ `search "reflect note"` ≤ 120 JSON-wire tokens (Phase 7)
2. ✅ MCP and CLI surfaces return structurally identical deltas (Phase 6)
3. ✅ Chained discovery cost ≤ 250 tokens (Phase 7)
4. ✅ Full `python -m pytest -q` green throughout

If any of (1)-(3) fails after Phase 7.2 tightening, the loop re-enters
**Design** with a `REVISION-N.md` gap analysis and the cycle repeats. Each
revision keeps the previous spec immutable in history (additive — never
rewrite).

---

## Cumulative test additions

```
tests/test_lint_capability.py                # Phase 0
tests/test_docstring_compliance_roster.py    # Phase 0
tests/test_render.py                         # Phase 1
tests/test_surface_resolution.py             # Phase 2
tests/test_search_delta_shape.py             # Phase 3
tests/test_intent_slice.py                   # Phase 4
tests/test_cli_surface_flags.py              # Phase 5
tests/test_search_isomorphism.py             # Phase 6
tests/test_token_budget.py                   # Phase 7
tests/test_install_surface_sections.py       # Phase 8
```

≈ 10 new test files; each ≤ 60 LOC; cumulative ≤ 600 LOC of test code over
~1k LOC of impl code. Test pyramid: each axis independent, smoke matrix at
the top.

---

## Risk register (panel-derived)

| Risk | Mitigation |
|---|---|
| fastmcp introspection unavailable (Q1) | F3.2 fallback to `mcp`; spike in Phase 2.1 confirms. |
| Skill-loader frontmatter unsupported (Q2) | Single-file-with-sections covers v1; v2 promotion deferred. |
| 44-verb docstring migration noisy | Cluster commits ≤8 verbs each; lint gate is the proof. |
| Tiktoken adds dep | Optional dep; char-count proxy floor for CI. |
| Token budget genuinely unreachable | Loop re-enters Design — that's the point of the loop. |
