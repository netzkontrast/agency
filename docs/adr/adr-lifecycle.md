<!-- agency-node: adr-theme-Lifecycle -->
---
kind: adr-theme
layer: Lifecycle
title: "Lifecycle decisions"
status: approved
---

# Lifecycle decisions

| Master ADR | Layer | Aggregate Status | Decisions |
|---|---|---|---|
| Lifecycle decisions | Lifecycle | approved | 1 live · 0 superseded |

## Lifecycle transitions are enforced by a data-driven A2A table with a typed IllegalTransition and a terminal floor; Lifecycle.move is the sole state writer, guarded statically by check-drift (B3)

| Decision ID | Status | Proposed By |
|---|---|---|
| LIFECYCLE-01 | approved | agent |

**In the context of** Spec 338 introduced the lifecycle write-frame; 340 needed the transition table to reject illegal edges and protect terminal states.,  
**facing** How to make lifecycle transitions safe and monotonically extensible without letting any capability write Lifecycle state directly.,  
**we decided for** Lifecycle transitions are enforced by a data-driven A2A table with a typed IllegalTransition and a terminal floor; Lifecycle.move is the sole state writer, guarded statically by check-drift (B3),  
**and neglected** per-capability ad-hoc state writes; a hardcoded if/else transition guard; no terminal-floor protection,  
**to achieve** data-driven monotone extension (a new machine adds a JSON entry); typed IllegalTransition propagates instead of being swallowed; terminal floor cannot be reopened; the B3 static guard fails CI on any out-of-band state writer.,  
**accepting that** the base table is data not code; the static guard needs a small whitelist for the one legitimate plan-step state writer..

| Relationship | Decision / Spec |
|---|---|
| Refines | /home/user/agency/Plan/inprogress/340-lifecycle-state-machine-transitions/spec.md |

