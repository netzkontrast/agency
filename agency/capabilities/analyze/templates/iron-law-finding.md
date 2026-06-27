{# doc-source: brooks-lint@ec44ec8 skills/_shared/common.md (Iron Law finding form) + agency/capabilities/analyze/_findings.py #}
**{{ f.risk_name }} — {{ f.title }}**
Symptom: {{ f.symptom }}
Source: {{ f.source }}
Consequence: {{ f.consequence }}
Remedy: {{ f.remedy }}{{ f.fix_tier_label }}
{# AGENT: The Iron Law as a rendered invariant — four required slots (Symptom ·
   Source · Consequence · Remedy). f.fix_tier_label is the [quick-fix]/[guided]/
   [manual] tag ONLY under --fix (the quality-remedy template); empty otherwise.
   This form is included once per finding by quality-report.md's findings loop;
   `f` is a finding view-dict (see analyze/_report.py::_finding_view). A finding
   missing Consequence or Remedy is REJECTED upstream (the Iron Law gate, Spec
   380 §2) — this template never renders a partial finding. #}
