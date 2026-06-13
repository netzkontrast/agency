# Token economy — the TokenCounter boundary + the doctrine

<!-- doc-source: agency/_tokens.py agency/disclosure.py -->
<!-- doc-hash: 44a7aa689e4e3808 -->

Token cost is a first-class budget in agency: discovery, verb briefs, and payloads are
measured and gated so the system stays cheap to read/write/discover (Spec 066–074).

## The `TokenCounter` boundary (`agency/_tokens.py`, Spec 082)

One place to count tokens, with tiers (best first):

1. **`count_tokens`** — Anthropic `messages.count_tokens` (model-specific, authoritative;
   used when the `anthropic` SDK + `ANTHROPIC_API_KEY` are present).
2. **`tiktoken`** — cl100k approximation (close for English; undercounts code).
3. **`proxy`** — `len(text)//4` (zero-dependency, hermetic).

`resolve_token_counter()` picks the best available; `AGENCY_TOKENS=proxy|tiktoken` pins a
tier (hermetic CI). The engine exposes `token_counter`; `agency_doctor` reports the live
`token_backend` so a silent fallback is visible. `count_tokens()` is the module-level
convenience that previously-scattered helpers now route through (DRY).

## The doctrine (Spec 066–074)

- **Tunable budgets, not magic snapshots** (CLAUDE.md rule 8): a budget like "the `graph`
  search payload ≤ 200 tokens" is documented config with a rationale; tests assert
  *invariants/relationships* (`wire_tok > bare_tok * 2.5`; proxy↔tiktoken within a band),
  not frozen counts.
- **Tiered discovery** (Spec 068) — `search` returns a budgeted slice; `disclosure.py`
  governs the L1/L2/L3 tiers so an agent pays for detail only when it drills in.
- **Concise verb briefs** — the first docstring line is the brief; keeping it tight is
  what keeps discovery cheap (a too-verbose brief is a real cause of budget failures).
- **Lints** (Spec 067/074) — `plugin.lint_*` + `scripts/check-drift`'s token-economy lint
  flag regressions; accepted WARNs are documented.

## Related

- Where briefs/skills are emitted under budget: [skills.md](skills.md).
- The drift gate that runs the lint: [../../operations/README.md](../../operations/README.md).
