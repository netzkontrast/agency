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
      finding) against the pinned version; document the current state.
- [ ] **If aliasing is now possible** — expose the bare verb
      (`call_tool("dispatch_decision", …)`) as an ADDITIVE alias on the
      code-mode surface; the wire name stays prefixed (Goal 5, no break).
- [ ] **The discovery payload shrinks** by the measured prefix tokens
      (Spec 146 prefix is shorter + cache-stable); the Spec 049
      reproducibility tests confirm the delta.
- [ ] **If still impossible** — record the re-confirmed finding + keep
      the `bare_name_*` WARN lints (no code change; close the loop).
- [ ] TODO row + drift clean.

## Interconnects

- **Output-budget chain** (146): bare names shrink the discovery prefix.
- Spec 068 (tiered discovery) already captured most of the win; this is
  the remaining surface.

## Open questions

1. Worth a CodeMode fork? **Recommend**: no — wait for native support;
   the tiered-discovery win (068) already banked the bulk.
