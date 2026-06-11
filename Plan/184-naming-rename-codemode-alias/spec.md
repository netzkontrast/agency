---
spec_id: "184"
slug: naming-rename-codemode-alias
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "049"
depends_on: ["049", "068", "146", "149"]
vision_goals: [1, 5]
affects:
  - agency/engine.py
  - tests/test_codemode_bare_alias.py
---

# Spec 184 — code-mode bare-verb alias (revisit the 069 finding)

## Why

Spec 049's audit measured the `capability_<cap>_` verb prefix at 202
tokens of pure repetition (65% of the name corpus). Spec 069 (the
rename impl) was CANCELLED because FastMCP's CodeMode resolves over one
shared catalog — a hidden-but-callable bare alias wasn't possible
without doubling the catalog or forking CodeMode. CORE.md flags it
"Revisit if CodeMode gains native alias support." This spec re-checks
that constraint against the current FastMCP and, if alias support
landed, ships the bare-verb code-mode surface — the −210-token discovery
win Spec 049 quantified.

## Done When

- [ ] **Re-verify the FastMCP CodeMode constraint** (the cancelled-069
      finding) against the pinned version; record finding as a typed
      `CodeModeAliasProbe{fastmcp_version, alias_supported: bool,
      evidence_url}` reflection so future audits don't re-investigate.
- [ ] **If aliasing is now possible** — expose the bare verb
      (`call_tool("dispatch_decision", …)`) as an ADDITIVE alias on the
      code-mode surface; the wire name stays prefixed (Goal 5, no break).
      Both names MUST resolve to the same handler object (identity, not
      equality) — proves additive aliasing, not a forked dispatch path.
- [ ] **Discovery payload shrinks measurably** (rule 8, relationship):
      `tokens(discovery_with_alias) < tokens(discovery_baseline)` AND
      the saving ≥ the measured prefix-repetition share Spec 049
      quantified (not pinned to 210); Spec 146 prefix stays byte-stable
      across the change.
- [ ] **If still impossible** — record the re-confirmed finding as the
      probe reflection + keep the `bare_name_*` WARN lints (no code
      change; close the loop). The probe is the artefact that closes
      the cancelled-069 question.
- [ ] **Wire contract invariant** — the over-the-wire `tools/list`
      response still carries ONLY the prefixed names; the bare alias is
      a code-mode-only resolution shortcut (Goal 5: never rename a
      shipped verb).
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  FastMCP version pinned in pyproject.toml supports code-mode aliases
When:   the engine registers `capability_decide_dispatch_decision` AND
        registers `dispatch_decision` as an additive alias on code-mode
Then:   call_tool("dispatch_decision", {...}) resolves to the SAME
        handler object as call_tool("capability_decide_dispatch_decision",
        {...}) (identity check), AND the MCP tools/list response over
        the wire contains only the prefixed name

Given:  FastMCP still routes one shared catalog (the cancelled-069 finding holds)
When:   the probe runs
Then:   spec records CodeModeAliasProbe{alias_supported: False, ...},
        no code change ships, bare_name_* WARN lints stay in place
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Catalog duplication | naive alias registers a second tool entry | `len(tools/list) != len(canonical_verbs)` | reject registration; require shared handler identity |
| Wire-shape break | alias leaks onto `tools/list` | drift test diffs the wire surface | hide aliases from the public schema; code-mode resolver only |
| Cache drift | alias name interpolates into the prefix | Spec 146 prefix-stability probe | alias resolution happens AFTER the prefix is frozen |

## Interconnects

- **Output-budget chain** (146): bare names shrink the discovery prefix
  AND the discovery prefix must remain byte-stable across the change.
- Spec 068 (tiered discovery) already captured most of the win; this is
  the remaining surface.
- Spec 149 (derived docs): the alias map is derived from the live
  registry, never hand-maintained.
- Spec 189 (verb-surface consolidation) is the sibling input-side win
  on the same goal-1 axis — both reduce discovery cost, neither breaks
  the wire.
- Spec 187 (output-side token lints) gates that the alias addition
  does not regress the prefix-stability invariant.

## Open questions

1. Worth a CodeMode fork? **Recommend**: no — wait for native support;
   the tiered-discovery win (068) already banked the bulk; a fork is
   ongoing maintenance debt for a marginal win.
2. If aliasing lands, do we ALSO publish bare names on the MCP wire?
   **Recommend**: no — bare on code-mode only, prefixed on the wire;
   keeps the per-cap namespace + Goal-5 stability promise intact.
3. Probe cadence after a first negative finding? **Recommend**: re-run
   on every FastMCP version bump (CI hook reads the pinned version);
   no time-based polling.
