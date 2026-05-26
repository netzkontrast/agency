---
slug: specs-index
type: spec-index
status: ready
summary: The contracts for each system part of the v2.1 four-domain model. One spec per part — the engine, the four domains, intent, and the capability/aspect model. Read OVERVIEW.md and ARCHITECTURE.md first.
---

# Specs — the contracts (per system part)

Each spec is the authoritative contract for one part of the system. Read
`../OVERVIEW.md` (the model) and `../ARCHITECTURE.md` (the runtime) first. Every
spec carries a **Status** line; unless noted, the contract is **specced — not
built**.

| Spec | Owns |
|---|---|
| [engine](engine.md) | the four-verb meta-contract + code-mode + engine guards |
| [intent](intent.md) | `why.capture` / `why.confirm`; the Intent node; `SERVES_INTENT`; pin-once |
| [who](who.md) | agent-session lifecycle; dispatch/handoff/release + poll/roster/verify; Dispatch/SharedContext/Slot nodes; orchestration verbs |
| [how](how.md) | open craft verbs + mandatory help + frame-role tagging |
| [when](when.md) | task lifecycle; start/advance/complete + status/list/check; gates; DRIVES |
| [where](where.md) | bi-temporal append-only graph; record/link/supersede + recall/find/validate; `where.project`; drivers |
| [capability-and-aspects](capability-and-aspects.md) | lazy-domaining over the four domains |

The canonical two-axis verb frame is shared by who / when / where:

| Domain | open | move | close | read | find | check |
|---|---|---|---|---|---|---|
| who | dispatch | handoff | release | poll | roster | verify |
| when | start | advance | complete | status | list | check (gate) |
| where | record | link | supersede | recall | find | validate |
