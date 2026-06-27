# Improvement Plan — Analysis {{ analysis_id }}

{# AGENT: This is the rendered output of analyze.improve. Each item names a Finding
   + the suggested fix. The agent walks the list and applies fixes one-by-one; each
   fix becomes a separate commit with the Finding id in the commit message for
   traceability. #}

_axes: {{ axes }}_  ·  _items: {{ item_count }}_

## Items

{{ items_list }}

{# AGENT: Apply fixes in severity order: fail → warn → info. After each fix, re-run
   analyze.run(path=…) to confirm the Finding disappeared. Items linked to the same
   Analysis stay associated via the IMPROVES edge. #}
{% if has_external_findings %}
## External-tool findings

{# AGENT: These come from ruff / bandit / radon when the [analyze] extra is
   installed. The fix may be `--fix` (ruff auto-fix) or a manual remediation;
   consult the rule's documentation linked in evidence. #}

{{ external_block }}
{% endif %}
