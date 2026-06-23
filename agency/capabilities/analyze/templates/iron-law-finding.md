<!-- doc-source: brooks-lint@ec44ec8 skills/_shared/common.md (Iron Law finding form) + agency/capabilities/analyze/_findings.py -->
**$risk_name — $title**
Symptom: $symptom
Source: $source
Consequence: $consequence
Remedy: $remedy$fix_tier_label

<!-- AGENT: The Iron Law as a rendered invariant — four required slots (Symptom ·
     Source · Consequence · Remedy). $fix_tier_label is the [quick-fix]/[guided]/
     [manual] tag ONLY under --fix (the quality-remedy template); empty otherwise.
     A finding missing Consequence or Remedy is REJECTED upstream (the Iron Law
     gate, Spec 380 §2) — this template never renders a partial finding. -->
