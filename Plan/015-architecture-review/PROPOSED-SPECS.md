> **PROMOTED TO STANDALONE SPECS.** The three proposals below were the
> Spec 015 dogfood-run deliverable; they have since been promoted to full
> standalone specs (with deeper Done When lists, Open Questions, and
> evidence). Use the standalone files as the canonical versions:
> - Spec 017 → [`Plan/inprogress/017-graph-native-dogfood-ledgers/spec.md`](../017-graph-native-dogfood-ledgers/spec.md)
> - Spec 018 → [`Plan/inprogress/018-cli-token-efficiency-bundle/spec.md`](../018-cli-token-efficiency-bundle/spec.md)
>   (broader than Jules's narrow CLI proposal — bundles 5 token wins + Jules's two)
> - Spec 019 → [`Plan/inprogress/019-engine-output-shape-contract/spec.md`](../019-engine-output-shape-contract/spec.md)
>
> The content below stays as a historical record of Jules's
> architecture-review-pass output.
>
> ---

---
spec_id: "017"
slug: "dogfood-graph-inversion"
status: draft
owner: "@agency"
depends_on: ["014"]
affects: ["agency/capabilities/dogfood.py", "agency/capabilities/_jules_skills.py"]
source-repos: []
estimated_jules_sessions: 2
domain: "capability"
wave: 2
---
# Spec 017 — Graph-Native Dogfood Ledgers

## Why

The current `dogfood.collect` flow relies on markdown ledgers (`DOGFOOD-NOTES.md`) as the primary store for feedback, reading files on disk and extracting patterns. This directly violates the canon architecture principle ("the moat is the graph" — CORE.md). Inverting this relationship creates a system where knowledge is stored natively as `Reflection` nodes in the bi-temporal graph, and the markdown files become on-demand rendered views of the state. Additionally, `agency/install.py:145` writes to files via `with open(path, "w") as f:` directly, utilizing the same anti-pattern. Both should be addressed for architectural consistency.

## Done When

- [ ] Add the `dogfood.render` transform capability to emit a markdown ledger from `Reflection` nodes.
- [ ] Deprecate the `dogfood.collect` capability into a one-shot migration utility.
- [ ] Modify the self-improvement skills in `_jules_skills.py` to use `reflect.note` from code-mode instead of depending on files on disk.
- [ ] Refactor `agency/install.py` file writes to output rendered views natively.

## Source clones

None

## Files

- `agency/capabilities/dogfood.py` (add `render`, deprecate `collect`).
- `agency/capabilities/_jules_skills.py` (modify skill schemas).
- `agency/install.py` (refactor writes).

## Evidence

- `ARCHITECTURE-REVIEW.md` `graph-vs-file-misuse` weaknesses 1 & 2.

## Open Questions

1. Should the `dogfood.render` capability overwrite `DOGFOOD-NOTES.md` natively, or return a payload that the agent will render instead? Overwriting creates a hybrid state, returning payloads enforces separation of concerns.
2. Should `install.py` be decoupled entirely from graph principles, or should all writes be strictly audited by the core?

## Self-Review

The change forces the `dogfood` and `install` systems into proper compliance with the core doctrine where the graph is the primary store for knowledge.

---
spec_id: "018"
slug: "cli-token-efficiency-code-mode"
status: draft
owner: "@agency"
depends_on: []
affects: ["agency/cli.py", "agency/engine.py"]
source-repos: []
estimated_jules_sessions: 2
domain: "capability"
wave: 2
---
# Spec 018 — CLI Execution Output Formatting & Token Efficiency

## Why

The current `agency.cli` executes Python scripts via the code-mode Sandbox provider. When errors or large sets of objects occur, stringification operations within `_structured` map the raw objects into text which dumps tracebacks or deeply nested elements entirely to standard output. This causes severe token leaks for agents reading the CLI and adds noise to the parsing output logic. We need an enforcement strategy or structured output response dict parameter limit so only requested attributes are emitted.

## Done When

- [ ] Add a `--fields` argument to `agency.cli execute` to specify allowed output keys dynamically (e.g. `--fields result,status`).
- [ ] Implement a token-safe traceback wrapper that extracts only the specific `ToolError` message instead of the full Python Traceback.

## Source clones

None

## Files

- `agency/cli.py` (Add argument and logic handling).
- `agency/engine.py` (Intercept traceback for execution limits).

## Evidence

- `ARCHITECTURE-REVIEW.md` `token-leak` weakness.

## Open Questions

1. Should `--fields` support nested dictionary projections (e.g., `--fields result.id,status`), or just top-level keys?
2. Should the `ToolError` extraction completely eliminate stack traces, or keep an abbreviated 1-level trace for critical debugging?

## Self-Review

Limits token consumption for orchestrators heavily reliant on the CLI outputs.

---
spec_id: "019"
slug: "engine-result-unwrapping-vision-drift"
status: draft
owner: "@agency"
depends_on: []
affects: ["agency/engine.py", "tests/test_engine.py"]
source-repos: []
estimated_jules_sessions: 1
domain: "meta"
wave: 2
---
# Spec 019 — Document Explicit Result Unwrapping Contract for Code-Mode

## Why

Currently, `agency/engine.py` uses `out = result["result"] if isinstance(result, dict) and "result" in result else result` to extract results from capabilities dynamically. This is intentional: verbs return `{"result": <delta>}` internally; the engine surfaces `<delta>` as the wire shape to keep code-mode lean (the Spec 001 envelope discipline). However, docstrings often mistakenly document the internal shape (e.g., `Returns: {result: rid}`) rather than the unwrapped shape.

## Done When

- [ ] Add explicit documentation inside `agency/engine.py` that verbs return `{result: <delta>}` internally, while clients see `<delta>`.
- [ ] Enforce docstring compliance to ensure that tools document their unwrapped returns, avoiding trial-and-error by agents reading `get-schema`.

## Source clones

None

## Files

- `agency/engine.py`
- `tests/test_engine.py`

## Evidence

- `ARCHITECTURE-REVIEW.md` `vision-drift` weakness.

## Open Questions

1. Can `lint_capability` natively statically analyze docstring mismatch against engine execution types, or do we rely on manual PR review to enforce this new documentation standard?

## Self-Review

This solidifies the existing engine unwrapping contract through documentation and policy instead of a destructive refactor, minimizing maintenance burden.

## Followup — Implementation Status (2026-05-31)

> Consolidation pass on branch `claude/plan-spec-review-74gHM`. Frontmatter `status:` may be stale; this section reflects verified code state.

**Verdict:** Shipped (as a milestone, not as code)

### Done
- Spec 015 was explicitly scoped as a Jules-led dogfood/architecture-review pass whose deliverable was documentation + three promoted proposals. That work is complete: `Plan/015-architecture-review/ARCHITECTURE-REVIEW.md`, `JULES-OBSERVATIONS.md`, and `PROPOSED-SPECS.md` (this file) all exist and contain the review output.
- The three spec proposals embedded here (017, 018, 019) were promoted to standalone specs (`Plan/017-…/spec.md`, `Plan/018-…/spec.md`, `Plan/019-…/spec.md`). The header note at the top of this file records the promotion.
- Spec 015 is listed as "Shipped" in `Plan/000-overview.md` ("Jules-led architecture review (dogfood pass). Produced JULES-OBSERVATIONS, ARCHITECTURE-REVIEW, and the three proposals promoted to specs 017-019.").

### Still to implement
- Nothing — the spec's own deliverable (review docs + promoted proposals) is fully shipped. Implementation of the identified weaknesses lives in the promoted specs (017, 018, 019) whose status is tracked separately.

### Refinement needed (given later specs)
- Spec 020 partially addresses W1/W2 at the substrate level (`.agency/session.db` committed). `dogfood.note`/`dogfood.render` (Spec 017) still needed to close W1/W2 at the capability level.
- Weakness W4 (`vision-drift` on engine unwrapping) is the subject of Spec 019 — currently "In flight / draft", not yet implemented.

### Evidence
- code: `Plan/015-architecture-review/ARCHITECTURE-REVIEW.md`, `JULES-OBSERVATIONS.md`
- tests: none (review-only spec; no code deliverable)
- commits/notes: Spec 015 row in `Plan/000-overview.md` § Shipped