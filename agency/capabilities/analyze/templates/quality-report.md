<!-- agency-node: $report_node_id -->
<!-- doc-source: brooks-lint@ec44ec8 skills/_shared/common.md (Report Template + Iron Law + Language rule) -->
# Quality Review — $mode

**Scope:** $scope
**Health Score:** $score/100$trend_suffix
$config_line

$verdict

<!-- BEGIN IF is_audit -->
## Module Dependency Graph

<!-- AGENT: audit mode ONLY — render the module import graph as mermaid (graph TD).
     A cycle or a high→low-level edge is the primary R5 signal. Omit this whole
     section for every other mode. -->
$module_graph
<!-- END IF -->

## Findings

<!-- AGENT: sort by tier critical → warning → suggestion; OMIT an empty tier's
     heading. Each finding renders the iron-law-finding template (Symptom · Source ·
     Consequence · Remedy). A finding missing Consequence or Remedy was REJECTED
     upstream by the Iron Law gate (Spec 380 §2) — never render a partial finding. -->
$findings_block

$suppressed_block

## Summary

<!-- AGENT: 2–3 sentences — the most important action + the overall trend. Under
     the legacy-friendly preset, LEAD with the three highest-leverage fixes (Spec
     381 §1) so a first run is not a wall of Criticals. -->
$summary

<!-- AGENT: Language rule — render the finding prose + the verdict + the summary in
     the user's language; keep in English the Iron Law labels (Symptom / Source /
     Consequence / Remedy), book titles, principle + smell names (e.g. "Shotgun
     Surgery"), and the structural headers above (Findings, Summary, Module
     Dependency Graph, Critical, Warning, Suggestion). -->
