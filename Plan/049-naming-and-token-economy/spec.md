---
spec_id: "049"
slug: naming-and-token-economy
status: done   # Shipped (audit-only) 2026-06-06 (branch claude/spec-049-naming-token-economy)
last_updated: 2026-06-03
owner: "@agency"
depends_on: [023, 029, 042, 043]
informs: [044, 045, 048]
affects:
  - agency/engine.py                      # substrate tool names + verb-emission
  - agency/install.py                     # regenerates skills/help/SKILL.md
  - agency/capabilities/*/                # potential verb renames
  - docs/vision/CORE.md                   # update referenced names
  - CLAUDE.md                              # references to substrate tools
estimated_jules_sessions: 1
domain: meta
wave: 2
---

# Spec 049 — Naming & Token-Economy Review

## Why

User audit (2026-06-03): "What about renaming capability aspect names —
to be shorter — like: `intent-bootstrap` could be just `intent`?". The
suggestion lands in three open problems:

1. **Token tax on every search/help dump.** `agency.cli search` returns
   the verb-name + brief slice. Verb names appear in EVERY discovery
   call. Average verb name is ~24 chars (`capability_delegate_dispatch_decision`
   = 38). The `capability_` prefix repeats across all 56 verbs.

2. **Substrate tool names are verbose.** `intent_bootstrap`,
   `agency_welcome`, `agency_install`, `agency_doctor`,
   `lifecycle_gate`, `memory_graph_provenance`. Each appears in
   chain_next hints AND in agent-side prose. Long names are
   self-tax.

3. **Per-verb naming inconsistency.** `dispatch_decision` (snake),
   `dispatch-decision` (skill name; kebab), `dispatch_bash_hints`
   (no-noun verb), `recall_semantic` (semantic-as-suffix vs.
   `semantic_recall` symmetric alternative). The naming has drifted
   across specs.

This spec **does NOT auto-rename**. It is a **review spec** that:
1. Audits every public-facing name (substrate tools + capability
   verbs + skill names).
2. Measures the token cost of the current names (`tiktoken cl100k`
   over the full search payload at the search-default limit).
3. Proposes a renaming proposal per the Spec 023 token-budget
   discipline.
4. Surfaces backward-compat strategy (aliases? deprecation? hard
   break?).
5. Recommends a per-name action: KEEP, ALIAS-AND-RENAME, RENAME-HARD.

The recommendation lands as a SECOND spec (050 or similar) that
implements the actual renames per the audit decisions. v1 of this
spec ships ONLY the audit + report.

## Done When

### Audit

- [ ] `agency/capabilities/research/_main.py` documents:
  - the 6 substrate tool names + their average token cost
    (cl100k), per-name AND aggregate
  - the 56 capability verb names + aggregate
  - the 12 skill folder names + aggregate
- [ ] A `naming-audit-report.md` (Reflection node scope=technical,
  kind=naming-audit OR a render of the same) emits per-name:
  - current name + length in cl100k tokens
  - proposed shorter name (or "KEEP" if no proposal)
  - rename strategy: ALIAS-AND-RENAME | RENAME-HARD | KEEP
  - backward-compat note (who currently references the old name)

### Proposals

- [ ] **Substrate tools** — concrete proposals:
  - `intent_bootstrap` → `intent` (verb, not noun-suffix)
  - `agency_welcome`   → `welcome` (the namespace is implicit when
    the tool is the only one from agency in the MCP host)
  - `agency_install`   → `install` (same logic)
  - `agency_doctor`    → `doctor` (same logic)
  - `lifecycle_gate`   → `gate` (matches the capability concept)
  - `memory_graph_provenance` → `provenance` (the noun says it all)
- [ ] **Capability verb prefix** — drop the
  `capability_<capname>_<verb>` MCP-tool naming for code-mode tools:
  - In code-mode, `call_tool("dispatch_decision", …)` is the call,
    not `call_tool("capability_delegate_dispatch_decision", …)`.
  - The capability-namespace stays in the Python class hierarchy;
    the MCP tool surface drops it for code-mode tools.
  - Backward-compat: emit BOTH names (old + new) for one minor;
    deprecate the old in the next minor.
- [ ] **Skill name canonical form** — pick one: kebab (current
  CLAUDE Code marketplace convention) OR snake (matches Python
  module conventions). Recommendation: kebab for SKILL.md
  frontmatter `name`; snake_case_python for the ontology key
  registration. ALREADY split today; document it explicitly.
- [ ] **`recall_semantic` vs `semantic_recall`** — pick one. v1
  ships `recall_semantic` (recall.suffix variant). Spec 049
  recommendation: KEEP (the noun-first reading "recall semantic"
  parses correctly).

### Implementation strategy

- [ ] The actual renames land in a FOLLOW-UP spec (050). This spec
  is the audit + proposal. Splitting prevents:
  - the audit becoming an excuse to ship behaviour-changes
    silently;
  - the rename PR getting reviewed alongside the audit
    discussion;
  - reverting a single proposal without reverting the whole rename.
- [ ] Spec 050 (out of scope here) will:
  - emit the renamed tools alongside the old (alias-and-rename)
  - mark old names `deprecated=True` in the MCP tool description
  - regen skills/help/SKILL.md with the new names
  - update CLAUDE.md + docs/vision/CORE.md references
  - target one minor for full removal of the old names

### Token-economy measurement

- [ ] `tiktoken cl100k` token count of `agency.cli search ""` (all
  verbs) baseline measured BEFORE Spec 050 + measured AFTER as the
  win.
- [ ] The win is the deliverable proof — Spec 050 only ships when
  the AFTER measurement < BEFORE by at least 20%.

## Design

### Why audit before rename

The naming discussion is opinionated — `intent` vs `intent_bootstrap`
is a STYLE choice with concrete trade-offs. An audit forces those
trade-offs into the open:

- "intent" — shorter but ambiguous (every conversation has intents).
  Without the `_bootstrap` suffix, the verb sounds like "select an
  intent" or "describe an intent", not "MINT a new one".
- "intent_bootstrap" — longer but unambiguous. "Bootstrap" carries
  the "this is the first call" semantic.

Without an audit document, every reader has to derive these trade-
offs from scratch. The audit centralises the discussion.

### Why two specs (049 audit, 050 implement)

The Spec 015 → 017/018/019 precedent: a master audit spec promotes
proposals to standalone implementation specs. Same shape here. The
audit ships the discussion; the implementation ships the renames.

### How to bound the audit's depth

The audit is ALL-VERBS, not a subset, because the token-economy
measurement only makes sense across the full corpus. But the
PROPOSALS are SUBSET-ABLE — the recommendation may be "rename
substrate tools, keep capability verbs". The audit surfaces, the
proposal narrows, the implementation acts.

### What the audit does NOT do

- It does NOT change any code in this PR.
- It does NOT mint a deprecation timeline (Spec 050 owns that).
- It does NOT change `pyproject.toml` console-scripts (Spec 039's
  `agency-mcp`, `agency`, `agency-doctor` stay — those names face
  the SHELL, not the MCP wire).

## Files

- **Add:**
  - `naming-audit-report.md` — the audit deliverable (or a
    `document.render(scope='naming-audit')` Reflection emission).
- **Do not modify** (v1):
  - any verb name, substrate tool name, or skill name.
  - any CLAUDE.md / docs/vision/CORE.md reference.

## Open Questions

1. **Aliases vs hard-rename for substrate tools.** Substrate tools
   are short — adding aliases doubles the namespace. Lean: alias-
   and-rename with a one-minor deprecation window.
2. **`capability_<cap>_<verb>` prefix on the WIRE.** Code-mode users
   don't see this — they call `await call_tool("verb_name", …)`
   inside `execute`. But the FastMCP wire DOES register the full
   name. The proposal: keep the wire-level prefix (it disambiguates
   when an MCP host has multiple plugins), drop the prefix only in
   code-mode `call_tool` dispatch. Needs a one-line policy.
3. **Skill name kebab vs snake.** Two conventions today: SKILL.md
   uses kebab (`dispatch-decision`), ontology uses kebab too. So no
   split exists; this is informational.
4. **Verb-name suffix conventions.** `_bootstrap`, `_decision`,
   `_check`, `_run` — are these informative or noise? Per-name
   analysis in the audit.

## Evidence

- User audit (2026-06-03): "What about renaming capability aspect
  names — to be shorter — like: intent-bootstrap could be just intent?"
- Spec 023 (adaptive disclosure) — token budget enforcement is
  agency's existing standard for this kind of cost analysis.
- Spec 029 (welcome/install substrate) — the substrate tool
  vocabulary lives here.

## Followup — Implementation Status (2026-06-03)

**Verdict:** Not started — spec drafted from user request. Audit +
proposal not yet executed.

### Still to implement
- All "Done When" deliverables (the audit + proposal documents).
- A Spec 050 to actually rename (follow-up).


## Followup — Implementation Status (2026-06-06, supersedes the 2026-06-03 entry)

> Shipped (audit-only) on branch `claude/spec-049-naming-token-economy`.

**Verdict:** Shipped — audit + per-name verdicts delivered. NO code renames (by
design; those are a follow-up spec).

### Done
- `Plan/049-…/naming-audit-report.md` — the audit deliverable. `cl100k_base`
  token measurement over the LIVE registry (69 verbs / 19 skills — already larger
  than the drafted 56/12). Per-surface tables + per-name verdicts (KEEP /
  ALIAS-AND-RENAME / RENAME).
- Headline finding: the `capability_<cap>_` verb prefix = **202 tok of pure
  repetition** (65% of the 311-tok name corpus; −210 tok / 14% of the full
  `search` payload). Substrate tools already short (18 tok; rename saves 10).
  Skills are consistent kebab (no split — Open Q3 resolved informational).
- One disagreement with the user's prompt, argued in the report: KEEP
  `intent_bootstrap` (bare `intent` loses the "mint the first intent" semantic
  for 1 token).
- `tests/test_naming_audit.py` — 5 reproducibility guards so the report can't
  drift from the live registry; they flip when the rename spec lands.

### Handoff
- Renames land in a NEW spec. The draft said "Spec 050", but **050 already
  shipped** as `analyze-deps-integration`; the implementation spec is proposed as
  **Spec 066** (needs a folder). Gated on ≥20% name-corpus reduction (audit shows
  65%). Must resolve the COMPLETE bare-name collision set flagged in report §4 —
  cross-capability verbs `note` (dogfood+reflect), `render` (document+dogfood),
  `verify` (jules+research), plus the contract shadow `reflect.search` vs the
  `search` tool — before exposing bare dispatch.
