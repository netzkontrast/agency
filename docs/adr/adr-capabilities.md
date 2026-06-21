<!-- agency-node: adr-theme-capabilities -->
---
kind: adr-theme
layer: capabilities
title: "Capabilities — decisions"
scope: "how capabilities are authored, discovered and bounded"
status: proposed
---

# Capabilities — decisions

> how capabilities are authored, discovered and bounded

| Master ADR | Layer | Aggregate Status | Decisions |
|---|---|---|---|
| Capabilities — decisions | capabilities | proposed | 2 live · 0 superseded |

## a capability is a self-registering folder under agency/capabilities/ (the drop-in bar)

| Decision ID | Status | Proposed By |
|---|---|---|
| CAPABILITIES-01 | proposed | agent |

**In the context of** agency needing to grow its capability surface without central wiring edits,  
**facing** registering each capability by hand in an engine manifest, the CLI and the MCP wiring,  
**we decided for** a capability is a self-registering folder under agency/capabilities/ (the drop-in bar),  
**and neglected** a central registry list, or explicit per-capability install wiring,  
**to achieve** adding a folder gains a discoverable, walkable, CLI-exposed and MCP-wired capability for free,  
**accepting that** auto-discovery hides load order and a malformed folder can fail registration at import time.

## keep manage as capability-agnostic generic CRUD; domain verbs live in their own capability

| Decision ID | Status | Proposed By |
|---|---|---|
| CAPABILITIES-02 | proposed | agent |

**In the context of** ADR needing WH(Y)-validate, supersede-with-forward-ref and aggregate-status verbs,  
**facing** the pull to add ADR-specific verbs onto the generic manage surface,  
**we decided for** keep manage as capability-agnostic generic CRUD; domain verbs live in their own capability,  
**and neglected** ADR verbs on manage, or a single god-capability,  
**to achieve** manage keeps a clean generic charter while the adr capability owns its domain,  
**accepting that** two surfaces to learn (generic CRUD versus domain) and some duplicated create/read ergonomics.

