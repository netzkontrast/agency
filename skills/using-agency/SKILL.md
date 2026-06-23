---
name: using-agency
description: Use when starting any conversation that may touch the agency engine (capabilities, intents, provenance, MCP code-mode) — bootstrap an Intent via agency_welcome BEFORE invoking any agency verb.
allowed-tools:
  - mcp__plugin_agency_agency__execute
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
---

# using-agency

The entry skill the orchestrator MUST invoke before calling any agency
capability verb. Modelled on the `using-superpowers` pattern: a broad-
trigger skill that primes the canonical bootstrap chain.

## The two-step bootstrap (load-bearing)

**Every agency-related task starts with the same two calls.** No
exceptions:

1. `agency_welcome` — returns the canonical bootstrap example + the
   live capability list + the resolved `.agency/` DB path. This IS
   the first call of every session.
2. `intent_bootstrap(purpose=, deliverable=, acceptance=)` — mints
   AND confirms the Intent that EVERY subsequent verb will SERVE.

```python
# Inside an MCP execute block:
welcome = await call_tool("agency_welcome", {})
# Read welcome["capabilities"] for the live verb surface, then:
i = await call_tool("intent_bootstrap", {
    "purpose":     "<one-line why>",
    "deliverable": "<one-line what>",
    "acceptance":  "<one-line how to verify>"
})
intent_id = i["intent_id"]
# Now any capability verb is reachable:
r = await call_tool("capability_<cap>_<verb>", {"intent_id": intent_id, ...})
```

## Naming verbs: BARE substrate tools vs `capability_<cap>_<verb>`

Two naming shapes coexist — guessing the wrong one burns a call:

- **BARE substrate tools** (call by their plain name, NO prefix):
  `agency_welcome`, `intent_bootstrap`, `agency_doctor`, `agency_reload`,
  `agency_install`, and `memory_graph_provenance` (read an intent's
  provenance — there is NO `manage_provenance`/`manage.provenance`).
- **Every capability verb is PREFIXED** `capability_<cap>_<verb>`, with the
  capability name in **underscores** (e.g. `capability_skill_generator_author`,
  NOT the hyphenated skill-folder name). `search("<keyword>")` returns the exact
  wire names; never hand-derive one from a dotted `cap.verb` guess.

**`get_schema` an unfamiliar verb BEFORE the first call** — and for an
object/array parameter use `detail="full"`, because `detailed` can render a
nested param as a bare `any[]` and hide its required shape (e.g. `[{id, text}]`).
A wrong-shaped argument raises and **aborts the whole `execute` block** (prior
graph writes in the block are NOT rolled back — make batches idempotent, or guard
each `call_tool` in try/except).

## Elicit / sample mid-chain (and the universal fallback)

A `develop.skill_walk` phase may **sample** (ask the host LLM to generate) or
**elicit** (ask you). When the client supports it, the walk advances inline.
When it does NOT (many clients decline server-initiated sampling), the walk
returns `{"status": "input-required", "blocked_on": "sample:<key>", ...}` — that
is the **universal mid-chain interaction**, not an error: you supply the value
and resume with `skill_walk(name, inputs={<key>: <value>}, resume_from="<phase>")`.
`agency_doctor`'s `host` block advertises capability but is honest it is verified
only at call time — so always be ready to handle the `input-required` resume.

## Why both calls are required

- **`agency_welcome`** is pure introspection (no graph writes). It
  returns the discoverable surface — without it, the agent has to
  guess capability names.
- **`intent_bootstrap`** records the orchestrator's why/what/accept
  triple as an `Intent` node. Every later verb call writes an
  `Invocation` that `SERVES` this Intent. The cross-concern
  provenance traversal starts here — skip it and the engine treats
  your calls as orphaned activity.

## When this skill applies (broad trigger)

- The user mentions "agency", "capability", "intent", "verb",
  "provenance", "dispatch", "Jules", "research", "analyze", "explain",
  "reflect"…
- The user asks the orchestrator to do anything in a repo where
  `.agency/` exists.
- A fresh session starts and any MCP code-mode block is about to call
  a `capability_*` tool.
- The user asks for a status/health check on the substrate
  (`agency_doctor`).

**When in doubt, invoke `agency_welcome` first.** Cheap (sub-1KB
return) + cancellable; nothing else stands between a stale start and
a clean dispatch.

## Failure modes the skill prevents

| Symptom | Root cause (this skill closes it) |
|---|---|
| `error: intent_id required` from a verb call | Skipped `intent_bootstrap` |
| `unknown capability` | Skipped `agency_welcome` — guessed name |
| Orphaned Invocation (no SERVES edge) | Verb called outside the intent flow |
| `.agency/session.db` missing on first call | SessionStart hook hadn't finished — re-call `agency_welcome` which surfaces the resolved path |

## See also

- `agency_doctor` — health-check substrate tool when something silently fails.
- `skills/help/SKILL.md` — the live capability map (regenerated by
  `agency install`).
- `dispatch-decision` — once an intent exists, this skill decides
  inline vs subagent/Jules.
