# Narrative Context Protocol — Coherence Check

## The "Graph is the Store, Files are a View" Rule

According to the Agency plugin model (`PLUGIN-CONCEPTS.md`), the core operating principle is that **queryable and derived state lives in the bi-temporal graph**, while files on disk are merely rendered views of that state. Provenance and intent are captured as nodes and edges via `act` verbs.

## Where the Rule Fits the NCP Workflow

In the ideal plugin architecture, the storyform's evolution—such as adding a Dramatica perspective or defining the main character's resolve—should be recorded directly to the graph as a series of actions. The resulting complete NCP document (`story.json`) would then be exported or "rendered" to the filesystem dynamically (an `effect` verb). This aligns perfectly with the plugin model's lifecycle and memory concepts, ensuring a fully auditable trail of *how* a story was developed, step-by-step.

## Where Hand-Authored JSON Fights the Rule

However, the current specification and skill design introduce a friction point where hand-authored or monolithic JSON updates fight this canonical rule.

Specifically, the workflow architecture in `research/ncp-novel-co-authoring-spec/output/SPEC.md` (§7.6) dictates an "Autonomous hand-off via NCP-state" pattern:

> "Agents MUST read the entire JSON file, update their specific scope (e.g., Phase 2 updates `subtext.storypoints`), and increment `status` to `complete` when all validations pass."

This establishes the `.ncp.json` file on disk as the canonical state machine, not the graph. If an agent (or human user) directly edits `subtext.storypoints` within the JSON file and changes the `status` string, the plugin's bi-temporal graph is bypassed.

To resolve this coherence gap within the Agency plugin model:
1. The `.ncp.json` skeleton should be considered a "human-authored canon document" exception *during* active drafting.
2. OR, to strictly adhere to the "graph is the store" rule, the `ncp-io` skill (mentioned in `SPEC.md` §8.10) must intercept file saves (`/save`) and parse the diffs into distinct graph `act` operations, effectively making the file a bi-directional projection of the graph rather than the sole source of truth.
