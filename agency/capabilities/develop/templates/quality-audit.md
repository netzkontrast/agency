<!-- doc-source: agency/capabilities/analyze/data/review-chain.json brooks-lint@ec44ec8 skills/brooks-audit/architecture-guide.md -->
# Quality walk — Architecture Audit

<!-- AGENT: The ORDERED audit chain (gather context → draw the graph → Dependency
     Disorder → Domain Model Distortion → remaining risks → testability → Conway)
     is the single source review-chain.json["audit"], delivered one step at a time
     (Spec 380). Render the steps from the chain; do NOT restate them (rule 2). -->

<!-- AGENT: Draw the module dependency graph FIRST and INCLUDE it (mermaid) in the
     report — the quality-report template renders a Module Dependency Graph section
     for audit mode only. A cycle or a high→low-level edge is the audit's primary
     signal (R5 Dependency Disorder). -->

<!-- AGENT: Default scope is the whole project; with --since=<ref>, analyze only
     the modules touching files changed since <ref> and note "Incremental audit". -->

<!-- AGENT: Apply the shared methodology from review-chain.json["_methodology"];
     emit findings only for the judgment-only risks (decidable ones are mechanical). -->
