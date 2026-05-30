---
spec_id: "016"
slug: "dogfood-graph-inversion"
status: draft
depends_on: ["014"]
affects: ["agency/capabilities/dogfood.py", "agency/capabilities/_jules_skills.py"]
---
# Spec 016 — Graph-Native Dogfood Ledgers

## Why

The current `dogfood.collect` flow relies on markdown ledgers (`DOGFOOD-NOTES.md`) as the primary store for feedback, reading files on disk and extracting patterns. This directly violates the canon architecture principle ("the moat is the graph" — CORE.md). Inverting this relationship creates a system where knowledge is stored natively as `Reflection` nodes in the bi-temporal graph, and the markdown files become on-demand rendered views of the state.

## Done When

- [ ] Add the `dogfood.render` transform capability to emit a markdown ledger from `Reflection` nodes.
- [ ] Deprecate the `dogfood.collect` capability into a one-shot migration utility.
- [ ] Modify the self-improvement skills in `_jules_skills.py` to use `reflect.note` from code-mode instead of depending on files on disk.

## Source clones

None

## Files

- `agency/capabilities/dogfood.py` (add `render`, deprecate `collect`).
- `agency/capabilities/_jules_skills.py` (modify skill schemas).

## Evidence

- `ARCHITECTURE-REVIEW.md` `graph-vs-file-misuse` weaknesses 1 & 2.

## Self-Review

The change forces the `dogfood` system into proper compliance with the core doctrine where the graph is the primary store for knowledge.

---
spec_id: "017"
slug: "cli-token-efficiency-code-mode"
status: draft
depends_on: []
affects: ["agency/cli.py", "agency/engine.py"]
---
# Spec 017 — CLI Execution Output Formatting & Token Efficiency

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

## Self-Review

Limits token consumption for orchestrators heavily reliant on the CLI outputs.

---
spec_id: "018"
slug: "engine-result-unwrapping-vision-drift"
status: draft
depends_on: []
affects: ["agency/engine.py", "agency/capability.py"]
---
# Spec 018 — Enforce Standardized Output Shapes for Capabilities

## Why

Currently, `agency/engine.py` uses `out = result["result"] if isinstance(result, dict) and "result" in result else result` to extract results from capabilities dynamically. This results in unpredictable returned types via `execute`, where a function like `capability_reflect_note` natively returns a dictionary `{"result": rid}`, but via `execute`, it evaluates to a string `"reflection:xxxx"`. This introduces a vision drift from expected `call_tool` shapes vs the engine CLI shapes, leading to trial-and-error executions.

## Done When

- [ ] Remove the unwrapping logic in `agency/engine.py`. Capabilities that specify an output shape must map perfectly onto what `execute` returns.
- [ ] Add validation tests to `tests/test_engine.py` to assert that output remains unmutated dicts if defined by the schema.

## Source clones

None

## Files

- `agency/engine.py`
- `tests/test_engine.py`

## Evidence

- `ARCHITECTURE-REVIEW.md` `vision-drift` weakness.

## Self-Review

Removing automatic unwrapping makes API design strictly explicit and typed.