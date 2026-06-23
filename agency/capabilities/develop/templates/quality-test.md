<!-- doc-source: agency/capabilities/analyze/data/review-chain.json brooks-lint@ec44ec8 skills/brooks-test/test-guide.md -->
# Quality walk — Test Quality Review

<!-- AGENT: The ordered test chain (Test Obscurity → Brittleness → Mock Abuse →
     Duplication → Coverage Illusion + Architecture Mismatch → Iron-Law report) is
     the single source review-chain.json["test"], delivered one step at a time
     (Spec 380). Render the steps from the chain; do NOT restate them (rule 2). -->

<!-- AGENT: Scope — all test files by default; if a diff exists, prioritise test
     files co-located with changed production files (src/foo.py → tests for foo). -->

<!-- AGENT: These are the six TEST risks (T1–T6), all judgment-only. Apply the
     shared methodology from review-chain.json["_methodology"]; every test finding
     still needs Symptom → Source → Consequence → Remedy. -->
