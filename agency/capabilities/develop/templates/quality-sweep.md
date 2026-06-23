<!-- doc-source: agency/capabilities/analyze/data/review-chain.json brooks-lint@ec44ec8 skills/brooks-sweep/sweep-guide.md -->
# Quality walk — Full Sweep

<!-- AGENT: The sweep chain (review pass R1–R6 → test pass T1–T6 → debt pass →
     architecture pass → aggregate residuals) is the single source
     review-chain.json["sweep"], delivered one step at a time (Spec 380). Render
     the passes from the chain; do NOT restate them (rule 2). -->

<!-- AGENT: Run each mode's pass in sequence for a complete decay picture, then
     de-duplicate findings ACROSS passes (one Finding per (risk_code, file, line))
     and produce one ranked report, Critical first. -->

<!-- AGENT: This is the broadest mode — it carries the remedy phase. Apply the
     shared methodology from review-chain.json["_methodology"]; emit only
     judgment-only risks (decidable ones are mechanical). -->
