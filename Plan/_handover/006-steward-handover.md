<!-- agency steward handover — read this first next run -->
# Steward Handover 006 — 2026-06-20

## What shipped this run

**Spec 337 — per-tool output filters (Slice 1, complete).**

The Spec 336 toolcall capture shipped a generic `head:20` filter for Bash.
Spec 337 completes this: a declarative `_FILTER_PROFILES` registry that
distils each high-volume tool's output to its *signal*, not its first 20 lines.

### Key changes

**`agency/capabilities/shell/_main.py`**
- `_FILTER_PROFILES` — 13-entry ordered list (first-match wins; Bash shapes are
  regexes matched against the command string; non-Bash match by tool name/prefix).
  Entries for: git(status/diff/log), pytest, grep/rg, ls, Bash default, Read,
  Edit, Write, ToolSearch, mcp__github__*, codegraph_*.
- New strategies in `_apply_filter`: `head+tail:N` (first+last with elision marker),
  `count+head:N` (line count + head sample), `stat` (git diff stat block, drop hunks),
  `fields:A,B,...` (JSON key extraction), `names` (JSON identifier list).
- `_resolve_profile(tool, command)` — first-match lookup returning strategy string;
  falls back to `"head:20"` (Spec 336 back-compat).
- `capture_filter` updated: new params `tool="Bash"` and `spec=None` (auto-resolves
  when None; explicit `spec=` still wins); `locator` strategy handled inline
  (path + line-count + sha16; no body copy); tool-appropriate header lines.
- New `AGENCY-DRIFT: shell-filter-profiles` tag at the registry.

**`agency/engine.py`**
- `_default_hook_handler` widened: ALL captured tools now route through
  `capture_filter(..., tool=tool_name, spec=None)` — Read extracts `file_path`,
  Edit/Write extract `file_path`, others stringify the tool input dict.
  Previously only Bash was filtered; non-Bash had `filtered=""`.

**`tests/acceptance/features/toolcalls.feature`**
- S3 scenario updated: command changed from `ls -la /tmp` (now uses `count+head:20`
  profile) → `custom-script.sh --run` (neutral fallback → head:20).
- 5 new Spec 337 Gherkin scenarios added.

**`tests/acceptance/test_toolcalls.py`**
- S3 step updated to match new command.
- 15 new step implementations for the 5 Spec 337 scenarios.

## Evidence

- RED→GREEN: 5 new scenarios + 5 updated steps; all 10 `test_toolcalls.py` scenarios green.
- `tests/acceptance/test_shell.py` — all 14 scenarios green (no regressions).
- `scripts/check-drift` → NO DRIFT (dormant-schemas gate clean).
- `scripts/check-doc-drift --update` → 7 docs re-stamped (engine.py + shell sources
  changed; pre-existing drift closed).
- TODO.md Spec 337 row updated (Drafted → Shipped; count 88→89).
- `Plan/337-per-tool-output-filters/spec.md` Followup updated.
- Reflections: `reflection:9bd15b10` (candidate selection), `reflection:b7aa89a8` (lessons).

## Next 3 candidates (ranked)

1. **Spec 153 Slice 5 — deferred-tag gate (`--fix-baseline` auto-trim)**
   After 12 batches of Slice 6 schema backfill, the manual "trim N entries from
   baseline" step is the only friction left in the schema-coverage workflow. Slice 5
   adds `--fix-baseline` to `scripts/check_schema_coverage.py` (rewrites the baseline
   in-place: remove fixed labels, warn on new ones). Medium effort, high ergonomic
   value; eliminates the most tedious maintenance step.

2. **Proposed amendment from handover 005 — dormant_schemas in scripts/check-drift**
   Add the `dormant_schemas` check from `agency_doctor` into the CI drift gate
   (currently only fires when the user invokes the doctor or schema CLI). The
   `scripts/check-drift` snippet was drafted in handover 005 — a short, low-risk
   addition that closes the gap between the per-PR drift gate and the runtime gate.
   Blocked three Slice 6 batches before being caught; now it's a known pattern.

3. **Spec 337 deferred — graph-override read path for FilterProfile**
   Analogous to `shell.define` for command templates: let a project store a
   `FilterProfile` Artefact in the graph to override a seed profile without a code
   change. The AGENCY-DRIFT tag at `_FILTER_PROFILES` protects the surface. Medium
   effort; low urgency (seed registry covers the known high-volume tools).

## Pillar gate (held)

Intent/Capability/Lifecycle/Memory — all pillars read+write load-bearing.
Schema coverage: 89/89 = 1.0 (full; Spec 153 Slice 6 complete).
Dormant schemas: 0. Drift: clean. Doc-drift: clean (7 re-stamped this run).

## Key lesson

The S3 test fixture used `ls -la /tmp` as a "generic Bash command" — but Spec 337
added an `ls` profile (`count+head:20`), silently changing the expected output.
The symptom is `filtered.count("line") == 21` vs the `<= 20` assertion.

**Pattern:** test fixtures for "generic behavior" (fall-through / default path)
should use inputs that are GUARANTEED to stay unmatched as the profile set grows.
A `custom-script.sh` command is never going to gain a profile; `ls` might.
When adding a new profile, grep existing tests for the tool name to catch this.
