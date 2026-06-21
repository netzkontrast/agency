---
spec_id: "198"
slug: cli-mirror-chain-parity
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "079"
depends_on: ["079", "160", "146", "157", "149", "201", "203"]
vision_goals: [5, 8, 1]
affects:
  - agency/cli.py
  - tests/test_cli_mirror_parity.py
---

# Spec 198 — CLI mirror ↔ code-mode parity proof

## Why

Spec 079 mirrors every capability verb as `agency <cap> <verb>` for
non-MCP agents (Goal 8), "code-mode stays canonical beneath it". Spec
160 adds `--chain`/`--fields`. The isomorphism CORE.md promises (the
same contract three ways — MCP/Skills/bash) needs a STANDING parity
proof: every verb reachable via code-mode is reachable via the CLI with
the same result shape, so a bash-only agent (Jules) is genuinely
first-class. The bash↔MCP isomorphism test exists for the wire verbs;
this extends it to the full mirror.

## Done When

- [ ] **`ParityReport` typed return** for the parity test —
      `ParityReport = {verb_count_total, verb_count_cli_reachable,
      verb_count_codemode_reachable, mismatches: list[Mismatch]}` where
      `Mismatch = {verb, surface, expected_shape_hash, actual_shape_hash,
      diff_path}`. The standing assertion is
      `verb_count_cli_reachable == verb_count_codemode_reachable`
      AND `len(mismatches) == 0`.
- [ ] **Invariant — registry-derived completeness** (relationship,
      not pinned count): for every verb name `V` returned by
      `live_registry.verbs()`, `cli_help_includes(V)` AND
      `execute_dispatches(V)` — both sides are computed live; a missing
      mirror trips the count delta.
- [ ] **Invariant — result-shape equivalence**: for every property-tested
      verb, `shape_hash(cli_result) == shape_hash(codemode_result)` where
      `shape_hash` ignores per-call body fields (intent_id, timestamps)
      but pins schema keys + types (Spec 019 wire-shape).
- [ ] **Invariant — prefix discipline both surfaces** (Spec 146):
      `ResponseEnvelope.prefix` bytes are identical on CLI and code-mode
      for the same verb on a frozen capability set.
- [ ] **`--chain` parity** — a YAML chain (Spec 160) returns
      `shape_hash`-equal output to the equivalent code-mode `execute`
      block over the same fixture inputs.
- [ ] **Architecture gate (Spec 157)** — a new verb auto-appears on the
      CLI or CI fails; the gate reads `live_registry.verbs()` and
      asserts `mirror_completeness == 1.0`.
- [ ] Test: parity property over a sampled-mutating + full-readonly cut
      of the registry; a synthetic missing mirror trips the gate.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a fresh capability ships with verbs ["analyze.census",
        "analyze.peek"] and no CLI surface is hand-edited
When:   the architecture gate (Spec 157) runs in CI
Then:   `agency analyze census` and `agency analyze peek` are both
        reachable AND ParityReport.verb_count_cli_reachable ==
        verb_count_codemode_reachable AND len(mismatches) == 0

Given:  someone hand-edits cli.py to skip a verb
When:   the parity property test runs
Then:   ParityReport.mismatches includes that verb with
        surface="cli" / expected != actual / a non-zero diff_path
        AND CI fails

Given:  a YAML chain `[analyze.census, analyze.peek]` is run on Jules
        (bash-only) and the same chain runs in code-mode in Claude
When:   both surfaces return
Then:   shape_hash(jules_result) == shape_hash(codemode_result)
        AND ResponseEnvelope.prefix bytes are identical
```

## Failure modes (Nygard)

| Failure | Parity-gate response |
|---|---|
| New verb missing on CLI (mirror gap) | gate fails with `MIRROR_INCOMPLETE`; lists the missing verb |
| CLI shape drifts from code-mode shape | `SHAPE_DIVERGED` carries `expected_keys` vs `actual_keys` diff |
| Property test exceeds wall-clock | sample reduces to mutating-verbs + a rotating read-only slice; nightly job runs full sweep |
| `--chain` YAML schema invalid | typed `BAD_REQUEST{detail:"chain_yaml"}` — never silently coerce |
| Prefix bytes differ across surfaces | `PREFIX_NONDETERMINISTIC` (Spec 146 Codes) with the offending key |
| Live registry changed mid-test | re-snapshot once; on second drift, fail with `REGISTRY_RACE` |

## Interconnects

- Spec 160 (CLI chain/fields) is the surface; Spec 157 gate enforces.
- **output-budget chain** (146) — both surfaces budget identically.
- Spec 149 (derived docs) — the CLI help is derived from the same
  registry, so a doc drift is a mirror drift; same gate.
- Spec 201 (TokenCounter API) — when bash-only Jules counts tokens via
  the local backend, the parity gate tolerates the band (Spec 082) but
  asserts shape equality regardless.
- Spec 203 (analyze.graph_query) — the parity verb-set is itself
  queryable so an audit can ask "which verbs are CLI-only / code-mode-only?"
- Spec 155 (red-team re-runner) — the parity gate is a standing check
  in the same family.

## Open questions

1. Property-test every verb (slow)? **Recommend**: sample + always-test
   the mutating verbs; full sweep nightly under a tagged CI job
   (`parity-full`) so the cheap path stays fast.
2. How are `--fields` projections asserted equal across surfaces?
   **Recommend**: project then `shape_hash` — the projection itself
   is a verb wrapper; same shape rule applies.
3. Where does the parity baseline live? **Recommend**: nowhere — it's
   recomputed every run from `live_registry.verbs()`; never pinned to
   a snapshot (CLAUDE.md rule 8).
