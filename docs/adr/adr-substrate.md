<!-- agency-node: adr-theme-substrate -->
---
kind: adr-theme
layer: substrate
title: "Substrate — decisions"
scope: "the FastMCP engine and the wire contract every capability rides"
status: proposed
last_updated: 2026-06-21
---

# Substrate — decisions

> the FastMCP engine and the wire contract every capability rides

| Master ADR | Layer | Aggregate Status | Decisions |
|---|---|---|---|
| Substrate — decisions | substrate | proposed | 3 live · 0 superseded |

## run multi-step work in code-mode execute so chains stay inside the sandbox

| Decision ID | Status | Proposed By |
|---|---|---|
| decision:61562e4c | proposed | agent |

**In the context of** an agent needing to chain many capability calls in one task,  
**facing** N network round-trips and N intermediate payloads crossing the boundary,  
**we decided for** run multi-step work in code-mode execute so chains stay inside the sandbox,  
**and neglected** step-by-step tool calls returning a result each hop,  
**to achieve** only the final return crosses back, for far fewer tokens and round-trips,  
**accepting that** errors surface as code exceptions rather than per-tool results and the sandbox must host the capability surface.

| Relationship | ID | Notes |
|---|---|---|
| Part Of | document:02093ef9 | Substrate — decisions |

## exactly three wire verbs — search, get_schema, execute

| Decision ID | Status | Proposed By |
|---|---|---|
| decision:e6235538 | proposed | agent |

**In the context of** an MCP client discovering and calling an open-ended, growing capability set,  
**facing** exposing every verb as its own MCP tool (hundreds), blowing the client tool budget,  
**we decided for** exactly three wire verbs — search, get_schema, execute,  
**and neglected** one-tool-per-verb, or a single do-everything tool,  
**to achieve** a fixed tiny tool surface that capabilities grow behind without changing the contract,  
**accepting that** an extra discover-schema-execute indirection and the client must compose code rather than call a named tool.

| Relationship | ID | Notes |
|---|---|---|
| Part Of | document:02093ef9 | Substrate — decisions |

## every verb returns a typed ToolResult envelope with a severity taxonomy

| Decision ID | Status | Proposed By |
|---|---|---|
| decision:fd39057d | proposed | agent |

**In the context of** callers needing to tell success, a recoverable refusal and a hard error apart,  
**facing** verbs raising raw exceptions or returning ad-hoc dicts,  
**we decided for** every verb returns a typed ToolResult envelope with a severity taxonomy,  
**and neglected** bare return values, or an exceptions-only contract,  
**to achieve** uniform success and failure handling, retry on transient severity, and a trace_id on every call,  
**accepting that** verbs must wrap their returns and callers unwrap an envelope rather than read a value directly.

| Relationship | ID | Notes |
|---|---|---|
| Part Of | document:02093ef9 | Substrate — decisions |

