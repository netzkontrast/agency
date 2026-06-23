<!-- doc-source: agency/capabilities/analyze/data/review-chain.json brooks-lint@ec44ec8 skills/brooks-debt/debt-guide.md -->
# Quality walk — Tech Debt Assessment

<!-- AGENT: The ordered debt chain (full decay-risk scan → Pain×Spread score →
     classify debt intent → group by risk) is the single source
     review-chain.json["debt"], delivered one step at a time (Spec 380). Render
     the steps from the chain; do NOT restate them (rule 2). -->

<!-- AGENT: Score each finding Pain × Spread — Pain = how much it hurts to work
     near it; Spread = how much code it touches; the product ranks remediation
     leverage. Classify each as deliberate/inadvertent × prudent/reckless
     (Fowler's debt quadrant) to frame urgency. -->

<!-- AGENT: Group findings by decay risk so the report shows systemic patterns,
     not a flat list. Apply the shared methodology from
     review-chain.json["_methodology"]; emit only judgment-only risks. -->
