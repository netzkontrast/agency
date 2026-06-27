{# doc-source: brooks-lint@ec44ec8 skills/_shared/common.md (Report Template + Iron Law + Language rule) #}
{# AGENT: the Spec-292 `<!-- agency-node: <id> -->` anchor is stamped by
   document.emit on persist (analyze.report) — not templated here, so the
   Document binding is never duplicated. #}
# Quality Review — {{ mode }}

**Scope:** {{ scope }}
**Health Score:** {{ score }}/100{{ trend_suffix }}
{{ config_line }}

{{ verdict }}
{% if is_audit %}
## Module Dependency Graph

{# AGENT: audit mode ONLY — the module import graph as mermaid (graph TD). A cycle
   or a high→low-level edge is the primary R5 signal. This whole section is gated by
   {% raw %}{% if is_audit %}{% endraw %} — absent for every other mode. #}
{{ module_graph }}
{% endif %}
## Findings

{# AGENT: findings arrive tier-sorted critical → warning → suggestion (analyze/
   _report.py::tier_sorted). Each renders the iron-law-finding form (Symptom · Source
   · Consequence · Remedy) via the loop below — the engine composes the list, not the
   verb. A finding missing Consequence or Remedy was REJECTED upstream by the Iron Law
   gate (Spec 380 §2) — this template never renders a partial finding. #}
{% for f in findings %}{% include "iron-law-finding" %}{% if not loop.last %}

{% endif %}{% endfor %}

{{ suppressed_block }}

## Summary

{# AGENT: 2–3 sentences — the most important action + the overall trend. Under the
   legacy-friendly preset, LEAD with the three highest-leverage fixes (Spec 381 §1)
   so a first run is not a wall of Criticals. #}
{{ summary }}

{# AGENT: Language rule — render the finding prose + the verdict + the summary in the
   user's language; keep in English the Iron Law labels (Symptom / Source /
   Consequence / Remedy), book titles, principle + smell names (e.g. "Shotgun
   Surgery"), and the structural headers above (Findings, Summary, Module Dependency
   Graph, Critical, Warning, Suggestion). #}
