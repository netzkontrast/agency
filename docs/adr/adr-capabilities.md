<!-- agency-node: adr-theme-Capabilities -->
---
kind: adr-theme
layer: Capabilities
title: "Skills teach the call"
status: in-progress
---

# Skills teach the call

| Master ADR | Layer | Aggregate Status | Decisions |
|---|---|---|---|
| Skills teach the call | Capabilities | in-progress | 6 live · 0 superseded |

## D1 fix generator+substrate, not 36 skills by hand

| Decision ID | Status | Proposed By |
|---|---|---|
| CAPABILITIES-01 | approved | user |

**In the context of** single source = docstring/registry/schema (rule 2),  
**facing** ,  
**we decided for** D1 fix generator+substrate, not 36 skills by hand,  
**and neglected** ,  
**to achieve** ,  
**accepting that** .

## D2 get_schema renders nested object/array shapes

| Decision ID | Status | Proposed By |
|---|---|---|
| CAPABILITIES-02 | approved | user |

**In the context of** highest-leverage; closes block-aborting errors for all clients,  
**facing** ,  
**we decided for** D2 get_schema renders nested object/array shapes,  
**and neglected** ,  
**to achieve** ,  
**accepting that** .

## D3 examples use real prefixed wire names + threaded intent_id

| Decision ID | Status | Proposed By |
|---|---|---|
| CAPABILITIES-03 | approved | user |

**In the context of** the example IS the naming lesson,  
**facing** ,  
**we decided for** D3 examples use real prefixed wire names + threaded intent_id,  
**and neglected** ,  
**to achieve** ,  
**accepting that** .

## D4 using-agency stays curated constant, gains naming rule

| Decision ID | Status | Proposed By |
|---|---|---|
| CAPABILITIES-04 | approved | user |

**In the context of** cross-cutting meta-skill; authored prose,  
**facing** ,  
**we decided for** D4 using-agency stays curated constant, gains naming rule,  
**and neglected** ,  
**to achieve** ,  
**accepting that** .

## Documentation generation mixes a deterministic template scaffold with MCP-sampled custom sections via document.compose

| Decision ID | Status | Proposed By |
|---|---|---|
| CAPABILITIES-05 | approved | agent |

**In the context of** render/explain give reproducible graph projections; ctx.host.sample (Spec 285 HostBridge) can author prose a projection cannot derive, but no verb assembled the two together.,  
**facing** How to author docs that are part deterministic-from-graph and part LLM-authored without losing reproducibility or the keep-both round-trip.,  
**we decided for** Documentation generation mixes a deterministic template scaffold with MCP-sampled custom sections via document.compose,  
**and neglected** a pure-template generator with no sampled prose; a pure-LLM generator with no grounding; a separate post-processing pass outside the substrate,  
**to achieve** one verb yields the mix; sampled sections are grounded in the scaffold; degrades honestly without a host (prompt preserved, rule 9); keep-both round-trip; clarity gate stays a separate ingest pass so the sampler never overfits its own score.,  
**accepting that** sampled sections need a host to fill; without one, the placeholder defers prose to a later agent..

| Relationship | Decision / Spec |
|---|---|
| Refines | /home/user/agency/Plan/draft/394-document-compose-template-sample/spec.md |

## Fix the generator + substrate, never hand-edit the 36 skills

| Decision ID | Status | Proposed By |
|---|---|---|
| CAPABILITIES-06 | proposed | user |

**In the context of** docstring/registry/schema is the single source (rule 2),  
**facing** ,  
**we decided for** Fix the generator + substrate, never hand-edit the 36 skills,  
**and neglected** ,  
**to achieve** ,  
**accepting that** .

