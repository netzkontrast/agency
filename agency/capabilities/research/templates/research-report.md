# Research: {{ question }}

{# AGENT: This is a published research report — the canonical publication shape for
   the deep-research flow. Frontmatter carries status / verdict / ok from the Research
   node. Render via document.render(scope='research-report', for_intent_id=<research_id>). #}

_status: {{ status }}_  ·  _verdict: {{ verdict }}_  ·  _ok: {{ ok }}_

## Summary

{{ summary }}

## Citations

{{ citations_table }}

{# AGENT: VERIFY each citation URL resolves and the evidence text actually supports
   the claim. Flag broken URLs or weak evidence in the Verification section below. #}
{% if has_verification %}
## Verification

{{ verification_block }}
{% endif %}

{# AGENT: After rendering, link the Artefact PRODUCES the calling Invocation
   (Memory.provenance walks this edge). The Research node stays the source of truth;
   this report is the rendered view. #}
