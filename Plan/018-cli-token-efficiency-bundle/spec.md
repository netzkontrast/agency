---
spec_id: "018"
slug: cli-token-efficiency-bundle
status: draft
owner: "@agency"
depends_on: ["016", "020"]   # 020 needed for cross-session skill.walk resume
affects:
  - agency/engine.py                 # tool name registration (capability-prefix elision)
  - agency/cli.py                    # --chain (YAML compiler), --fields, traceback wrapper
  - agency/skill.py                  # skill.walk verb
  - agency/capability.py             # implicit intent_id default; compact get_schema rendering
estimated_jules_sessions: 0
domain: capability
wave: 3
---

# Spec 018 — Code-mode compactness (five token-efficiency wins, bundled)

## Why

GOALS.md goal #1: token-efficient agentic loops. The session that produced
this spec averaged ~520 tokens of Python boilerplate per orchestration
block (dispatching Jules + watching state). The semantic payload was
maybe 100 tokens of those 520 — the rest was substrate ceremony
(`e.registry.invoke(e.memory, iid, "jules", verb, agent_id=..., **kwargs)`
× N calls).

**Jules's Spec 015** flagged the same surface area from a different angle:
W3 (`token-leak`, `agency/cli.py:27`) noted that `_structured` dumps full
Python dicts including tracebacks on error paths. Jules's `Plan/015-…/
PROPOSED-SPECS.md` "Spec 017" proposed a narrow fix (`--fields` arg +
traceback wrapper). **This spec generalizes:** the five wins identified
in the prior orchestrator session + Jules's two — bundled because they
share infrastructure and individually are small.

## Done When

**Five wins, ranked by tokens-saved ÷ effort. Land in order; each is
independently useful and reverts cleanly.**

- [ ] **Win 1 — `skill.walk(name, inputs)` verb on the `develop` capability
  (~80 LOC + tests).** Atomic walker that runs an entire skill to first
  hard gate. Replaces the 5× `SkillRun(...).submit(...)` boilerplate
  pattern (~300 tokens per walk) with a single call (~30 tokens).
  This is the structural lever — DSPy-style "compile the program, run
  it, return the result."

  **Return shapes (the contract):**
  - **Success** → `{status: "completed", skill_id, outputs: <map>}`
  - **Hard-gate pause** → `{status: "input-required", phase, blocked_on, resume_with: [keys], skill_id, partial_outputs}` (Spec 016 Hint #8)
  - **Phase failure** → `{status: "failed", phase, error, skill_id, completed_phases}` — walk ABORTS on first phase failure (not a half-walked state); the `Gate{passed:False, paused:False, error}` node lands in the graph for audit (parallel to Codex C3 pause persistence).

  **Resume contract** (panel addition):
  - Caller re-invokes `skill.walk(name, inputs, resume_from=skill_id)` with
    the `resume_with` keys populated. The walker looks up the skill_id,
    resumes at the paused phase, supplies the new inputs.
  - Resume is **idempotent**: re-calling with the same args after a
    `completed` status returns the same outputs (read from the graph,
    no re-execution).
  - Resume across orchestrator sessions: the skill_id is the bridge
    (lives in the central `.agency/session.db` per Spec 020).

- [ ] **Win 2 — capability-prefix elision in tool names (~30 LOC).** The
  engine registers verbs as `capability_jules_dispatch`; agents type
  `capability_jules_dispatch` in `call_tool(...)`. Patch
  `agency/engine.py:_wire` to register both the long form AND
  `jules.dispatch` as aliases. Saves ~11 chars × every tool reference.
  Tests assert both names resolve to the same handler.

- [ ] **Win 3 — implicit `intent_id` via env / CLI default (~20 LOC).**
  Today every verb invocation needs `intent_id="intent:abc"`. Add an
  `AGENCY_INTENT` env var read at `cli.py` entry; if set + no
  `intent_id` in kwargs, inject it. Plus `agency intent --set <iid>`
  subcommand to set it for the session. Saves ~25 tokens per call.

- [ ] **Win 4 — compact `get_schema` rendering (~50 LOC).** Today
  `get_schema(tools=["jules.dispatch"])` returns full JSON Schema (~400
  tokens per tool). Add a compact renderer: signature DSL
  (`jules.dispatch(source: str, ..., automation_mode: str = "")`) +
  return-shape one-liner (`-> {status, session, url, alias, artefact}`)
  + `chain_next:` hint from the docstring (per Spec 016 Hint #7).
  ~80 tokens per tool. **5× compression on the discovery surface.**

- [ ] **Win 5 — YAML chain compiler (`agency exec --chain`) (~60 LOC).**
  Take a YAML ops list; compile to the equivalent Python code-mode
  script; run inside Monty sandbox. Same `$N.field` reference syntax
  the recovery-plan format uses (`_jules_patch.build_recovery_plan`).
  Agent emits data, not code. 2-3× compression on multi-call chains
  vs equivalent Python.

- [ ] **Jules's Win 6 — `--fields key1,key2` arg on `agency exec` (~15 LOC).**
  Filters the response dict to just the named keys. Token-safe by
  construction. From `Plan/015-…/PROPOSED-SPECS.md` Spec 017.

- [ ] **Jules's Win 7 — Traceback wrapper for `ToolError` (~20 LOC).**
  When `execute` raises a `ToolError`, surface ONLY the error message
  (not the full Python traceback). Today errors dump megabytes of
  context. From `Plan/015-…/PROPOSED-SPECS.md` Spec 017.

- [ ] **End-to-end token measurement test** — `tests/test_cli_token_efficiency.py`
  measures char-length of:
  - The 520-token "dispatch + watch" example pre-Spec 018.
  - The same flow post-Spec 018 (using skill.walk + tool aliasing +
    implicit intent_id + compact get_schema + chain DSL).
  - Asserts ≥ 60% reduction on the equivalent semantic payload.

## Files

- **Modify:**
  - `agency/engine.py` — `_wire` adds short-name alias.
  - `agency/cli.py` — `--chain`, `--fields` flags; traceback wrapper.
  - `agency/skill.py` OR new `agency/capabilities/develop.py` —
    `skill.walk` verb (decision in Open Question 1).
  - `agency/capability.py` — implicit-intent-id default helper.
- **Create:**
  - `tests/test_cli_token_efficiency.py` — the measurement test.
  - `tests/test_skill_walk.py` — coverage of the new walker.
  - `tests/test_chain_compiler.py` — YAML → Python compilation.
- **Documentation:** update `AGENTS.md` "Running the engine from bash
  only" section with the new compact forms. Update `CLAUDE.md` rule 1
  to cite Spec 018's skill.walk + chain syntax as the first-instinct
  primitives.

## Open Questions

1. **`skill.walk` home: `develop` capability or `skill_generator` or
   new top-level surface?** It's not a discipline (so not `develop`); not
   a generator (so not `skill_generator`). Recommend: NEW capability
   `walker` (single-verb, light) — symmetric with `gate` being a
   single-verb capability for hard-gate predicates. Folds cleanly into
   the canon's "open set" via Spec 016's authoring rules.
2. **Tool-name aliasing — both names, or alias replaces the long form?**
   Recommend: BOTH for one release (back-compat for any external
   code-mode scripts), then deprecate the long form per the
   "cut-don't-carry" doctrine.
3. **YAML chain references (`$N.field`) — JMESPath, dot-path, or simple
   index+key?** Recommend simple `$N.field` (one level of nesting; if
   you need deeper, write Python). The recovery-plan format
   (`_jules_patch.build_recovery_plan`) is the canonical precedent.
4. **Compact `get_schema` output as the default, or behind a `--compact`
   flag?** Recommend default for new sessions (the wins compound) +
   leave a `--verbose` flag for the long form (for debugging /
   schema-validation use cases).
5. **End-to-end token measurement methodology.** Counting characters is
   approximate; closer would be tokenizing through `tiktoken`. Recommend:
   start with char-count (cheap, no external dep); add tokenizer-based
   measurement when we want to be precise. The ≥60% bar is the gate.

## Evidence

- `Plan/015-architecture-review/ARCHITECTURE-REVIEW.md` W3 (token-leak).
- `Plan/015-architecture-review/PROPOSED-SPECS.md` Spec 017 (Jules's
  narrow framing; Wins 6 + 7 here are exactly that proposal).
- The session that produced this spec (the agency dev loop) — the
  ~520-token dispatch boilerplate example is the live measurement.
- `agency/capability.py:75-100` — `_wrap_method` + the auto-wiring path
  that registers the long tool names.
- `agency/cli.py:46-95` — the CLI's execute path; where `--chain` and
  `--fields` slot in.
- `agency/skill.py:24-86` — `SkillRun` (the walker the new `walk` verb
  composes).
- `docs/vision/GOALS.md` goal #1.
