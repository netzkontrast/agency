<!-- doc-source: agency/capabilities/analyze/data/review-chain.json brooks-lint@ec44ec8 skills/brooks-review/pr-review-guide.md -->
# Quality walk — PR Review

<!-- AGENT: The ORDERED review chain for this mode (title · purpose · the
     step-by-step risk scan) is the single source review-chain.json["review"],
     delivered one step at a time by the judgment pass (Spec 380). Do NOT restate
     the steps here (rule 2) — render them from the chain. This template carries
     only the cross-cutting WALK framing that is not per-step chain data. -->

<!-- AGENT: Scope calibration — <50 LOC: steps 1–3 + 6a/6b only if imports/names
     changed; 50–300: all steps; >300: sample the highest-risk areas and SAY the
     review is sampled; >500: flag the PR size itself as a Change-Propagation
     signal in the Summary (a change that can't be reviewed in one pass = tangled
     responsibilities). Skip generated files (stubs, clients, migrations, locks). -->

<!-- AGENT: Order matters — scan Change Propagation (R2) FIRST (most visible in a
     diff), then Cognitive Overload (R1). Quick Test Check is three signals only
     (Coverage Illusion, Mock Abuse, Test Obscurity) — not a full test audit;
     skip it for docs/config-only changes. -->

<!-- AGENT: Apply the shared methodology (Iron Law · severity tiers · fix order ·
     restraint) from review-chain.json["_methodology"]; emit findings ONLY for the
     judgment-only risks — the decidable ones are already caught mechanically. -->
