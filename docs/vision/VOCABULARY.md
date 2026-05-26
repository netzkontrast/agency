---
slug: vision-vocabulary
type: vision
status: ready
summary: Canonical terms for the v2.1 four-domain 5W1H model. One self-describing definition each, used consistently across canon, specs, and code. Defines intent, who/how/when/where, capability, home domain, aspect, lazy-domaining, the two verb axes, DRIVES, dispatcher-vs-dispatchee, engine guards, where.project, and the naming scheme.
---

# Vocabulary

| Term | Meaning |
|---|---|
| **Intent (why / what)** | The human's root — the reason the work exists and what "done" means. Captured via `why.capture` → `why.confirm`; persisted as a single **Intent node**, pinned once and thereafter referenced by node-id (cache-safe). Every action edges back to it via `SERVES_INTENT`. Intent is its OWN root, distinct from `where`'s execution memory. |
| **who** | The agent-SESSION lifecycle domain — which actor performs the work: dispatch, handoff, supervision, harness-in-harness. Closed domain; verbs map to the canonical frame. |
| **how** | The craft domain — skills, tools, actions. The OPEN domain: capability-specific verbs, discoverable via a mandatory `how.<capability>.help`. Each verb is tagged with the frame role it fills. |
| **when** | The TASK / process lifecycle domain — order, gates, scheduling, triggers. Closed domain; verbs map to the canonical frame. |
| **where** | The memory domain — a bi-temporal, append-only GraphQLite graph plus artefacts. Closed domain; verbs map to the canonical frame. The only persistent state. |
| **Capability** | A vertical area of work (e.g. `jules`, `music`, `novel`, `meta-development`). Authored in exactly one home domain and expressed across the four domains as aspects. |
| **Home domain** | The single domain in which a capability is authored — its primary concern (orchestration → who; craft → how; process → when; data/memory → where). Home ≠ exclusive ownership. |
| **Aspect** | A capability's expression in one domain (its who aspect, how aspect, when aspect, where aspect). The aspects are the same capability faithfully restated per domain — isomorphic. The holding domain owns the aspect. |
| **Lazy-domaining** | A capability materializes an aspect in a non-home domain only when it needs one. Default = lazy graph data (when `Task`/gate nodes; where `Artefact`/memory nodes), no authored folder; a capability with fixed structure may instead author the aspect. No eager 4× triplication. |
| **Two verb axes** | The canonical frame for the closed domains (who/when/where). **Lifecycle** (write): `open · move · close`. **Observe** (read): `read · find · check` (+ `watch` for live/subscribe). Every closed-domain function maps to exactly one axis-role. |
| **Frame role** | Which of the six canonical roles (open/move/close/read/find/check) a verb fills. Closed-domain verbs are named for their role directly; an open (`how`) verb declares its role and may surface it as a call-site alias. |
| **Canonical alias** | A call-site alias mapping a specialist verb to its frame role — e.g. `where.music.supersede` ≡ `where.music.close`. The frame is the spine; specialist names are skins over it. |
| **DRIVES** | The edge linking a who-session to the when-task it advances. The join across the who ↔ when boundary: `when` owns the TASK lifecycle, `who` owns the AGENT-SESSION lifecycle, and state is never duplicated across them. |
| **Dispatcher vs dispatchee** | In `who.dispatch(role=jules)`, `who.<actor>` is the DISPATCHER and the target role is a PARAMETER (the dispatchee). A who-capability is the orchestrator; the role it spawns is data, not a separate domain. |
| **Orchestration verbs** | `who` verbs beyond the frame: `retry` / `respawn` (canon guard: NEVER respawn jules if a patch already exists; DO if the patch is empty), `escalate`, `fan_out`, `reclaim_slot`. |
| **Dispatch node** | A per-hop correlation node in `where` that records one dispatch hop; nesting them enables harness-in-harness (a dispatchee that itself dispatches). |
| **SharedContext node** | A `where` node ensuring a handoff passes CONTEXT, not just a baton — the receiving session inherits what the prior one knew. |
| **Engine guards** | Cross-cutting engine concerns (NOT domains): quality-score, loop-detection, compaction checkpoints, and `Slot`/quota accounting. Referenced by who/when, owned by the engine. |
| **where.project()** | The mandatory read path into `where`: a ranked, token-budgeted, TOON-encoded projection that returns DELTAS, never raw history. How append-only memory coexists with compaction. |
| **Four-verb meta-contract** | The engine's entire public surface: `list_tools`, `call_tool`, `list_skills`, `dispatch_skill`. Not a domain — the host. |
| **Code-mode** | The engine rendering the domains as a callable code API (`who.*`, `how.*`, `when.*`, `where.*`); filter/join in-sandbox; return deltas. The token-efficiency primitive. |
| **Naming scheme** | Every public name derives from `(domain, capability, verb)`: MCP `mcp__<domain>_<capability>_<verb>`; skill `/agency:<domain>:<capability>:<verb>`; code-mode `domain.capability.verb()`. The name alone tells you domain, capability, and verb. |
| **Aspect (authored) shape** | When a capability authors an aspect it follows that domain's canonical shape, so knowing a domain teaches you all its aspects. |
| **Intent node / Session / Task / Artefact** | Typed `where` nodes: `Intent` (the pinned root), `Session` (a who actor's run), `Task` (a when process instance), `Artefact` (a recorded product whose bytes live in user storage via a driver). |
| **TOON** | Token-oriented object notation — the compact tabular encoding used for `where.project()` output. |
| **Bi-temporal / append-only** | `where` records valid-time and transaction-time and never overwrites; a corrected fact `supersede`s the prior one via a `SUPERSEDES` edge. |
| **Frontmatter canon** | Required front-matter on canon docs and skills: `slug`, `type`, `status`, `summary` (summary ≤ 240 chars for specs, ≤ 120 for skills). |
