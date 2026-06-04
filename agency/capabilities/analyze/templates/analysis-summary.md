# Analysis Summary

<!-- AGENT: This template renders the results of `analyze.run`. The
4 axes (quality, security, performance, architecture) plus paths
each contribute a Finding count by severity. Use this to triage at
a glance; drill into individual Findings via the analysis_id. -->

_path: $path_  ·  _started_at: $started_at_

## Totals by axis

$totals_table

<!-- AGENT: Highest-severity findings appear first in the table. A
'fail' severity is a hard block — fix before merging. A 'warn' is a
soft block — fix if practical. 'info' is FYI. -->

## Next steps

<!-- AGENT: Run `analyze.improve(analysis_id, axes=[...])` to generate
an improvement plan filtered by axis. Run `analyze.cleanup(path)` to
remove dead code surfaced by the architecture axis. -->

- `analyze.improve(analysis_id=$analysis_id)` — improvement plan
- `analyze.cleanup(path='$path')` — dead-code removal
