# Agency cookbook — recipes for using the plugin

Copy-paste recipes for the agency surface. Every recipe runs through the **one
contract**: code-mode `execute` chaining `call_tool(...)` (the same calls work
from `mcp__agency__execute` in Claude Code or `agency execute --code "…"` from
the shell). Each verb call records provenance — every action becomes a node in
the graph that `SERVES` your intent.

<!-- doc-source: agency/capabilities/panel/_main.py agency/capabilities/mode/_main.py agency/capabilities/persona/_main.py agency/capabilities/select/_main.py agency/capabilities/recommend/_main.py agency/capabilities/symbols/_main.py agency/capabilities/manage/_main.py agency/capabilities/document/_main.py agency/_substrate_tools.py -->
<!-- doc-hash: 5747745618381639 -->

## 0. Onboarding (one-time)

```bash
# Install AND enable the plugin in this project's .claude/settings.json (one step):
python -m agency.install --enable

# Health-check — is the substrate ready, and can a fresh call succeed?
agency doctor        # → ok, plugin_enabled, drift.surface_freshness, onboarding{ok, ms}
```

Every session then starts the same way:

```python
welcome = await call_tool("agency_welcome", {})          # live capability list + DB path
iid = (await call_tool("intent_bootstrap", {
    "purpose": "<why>", "deliverable": "<what>", "acceptance": "<how to verify>"
}))["intent_id"]
# every later call passes intent_id=iid so its provenance SERVES this intent.
```

## 1. Discover, don't memorize

```python
# Find a capability by what you want to do (beats raw tool search):
hits = await call_tool("search", {"query": "compress output with symbols",
                                  "detail": "brief"})
# Get the exact schema before calling:
schema = await call_tool("get_schema", {"tools": ["capability_symbols_compress"]})
# Or have the engine route a free-text request to the best verb:
rec = await call_tool("capability_recommend_route",
                      {"intent_id": iid, "agent_id": "me",
                       "request": "research cited evidence on a question"})
# -> {top: "research", recommendations: [{capability, verb, why}, …]}
```

## 2. Think before acting — the SuperClaude reimplementations

```python
# Pick a working posture (decidable from the request):
mode = await call_tool("capability_mode_activate",
                       {"intent_id": iid, "agent_id": "me", "mode": "auto",
                        "context": "I'm not sure yet — let's explore options"})
# -> {mode: "brainstorming", behaviors: ["Ask probing questions…", …]}

# Stress-test a decision through 9 strategy frameworks (auto-picks debate mode
# for a risky subject):
panel = await call_tool("capability_panel_convene",
                        {"intent_id": iid, "agent_id": "me",
                         "subject": "a controversial high-risk pricing change"})
# -> {mode: "debate", experts: ["Christensen","Taleb",…], analysis: [...]}

# Summon the right specialist persona for a task + get a dispatch brief:
brief = await call_tool("capability_persona_summon",
                        {"intent_id": iid, "agent_id": "me", "persona": "auto",
                         "task": "find the auth vulnerability and fix it"})
# -> {persona: "security-engineer", brief: "# Role — security-engineer …"}

# Route an operation to the right approach archetype:
route = await call_tool("capability_select_route",
                        {"intent_id": iid, "agent_id": "me",
                         "operation": "rename a symbol across the project",
                         "file_count": 9})
# -> {approach: "semantic", score: 0.8, fallback: ["pattern","native"]}

# Compress a status line for a token-tight reply:
c = await call_tool("capability_symbols_compress",
                    {"intent_id": iid, "agent_id": "me",
                     "text": "tests failed therefore the build is critical"})
# -> {compressed: "tests ❌ ∴ the build is 🚨", reduction: …}
```

## 3. The Document — graph ↔ markdown, both ways

```python
# Project graph state to a file AND event-source it (graph→file):
mirror = await call_tool("capability_document_mirror",
                         {"intent_id": iid, "agent_id": "me",
                          "scope": "reflections", "apply_path": "NOTES.md"})

# A human edits NOTES.md on disk → round-trip it back (file→graph), keep-both:
ing = await call_tool("capability_document_ingest",
                      {"intent_id": iid, "agent_id": "me", "path": "NOTES.md"})
# -> {action: "revised", clarity_score: …}  (every file is also a prompt)

# Read the keep-both history (graph- and file-authored versions coexist):
revs = await call_tool("capability_document_revisions",
                       {"intent_id": iid, "agent_id": "me",
                        "document_id": ing["document_id"]})

# Render the whole session as a Document (Intent · Capability · Lifecycle ·
# Memory) — archived under .agency/sessions/ and restorable later:
sess = await call_tool("capability_document_session",
                       {"intent_id": iid, "agent_id": "me"})
```

## 4. Memory CRUD — `manage` over any node type

```python
# Create / read / list / update / amend / retract ANY graph node:
doc = await call_tool("capability_manage_create",
                      {"intent_id": iid, "agent_id": "me", "label": "Document",
                       "props": {"path": "/x.md", "content_sha": "abc"}})
await call_tool("capability_manage_read",
                {"intent_id": iid, "agent_id": "me", "node_id": doc["id"]})
# Read-API (folded onto manage): the "where are we" rollup + timeline:
await call_tool("capability_manage_state",
                {"intent_id": iid, "agent_id": "me", "for_intent_id": iid})
await call_tool("capability_manage_timeline",
                {"intent_id": iid, "agent_id": "me", "for_intent_id": iid})
# Retract = bi-temporal soft delete (history retained, never destructive):
await call_tool("capability_manage_retract",
                {"intent_id": iid, "agent_id": "me", "node_id": doc["id"]})
```

## 5. Reload the server mid-session (no restart)

```python
# Edited or added a capability? Pick it up live — no reinstall, no restart:
r = await call_tool("agency_reload", {})
# -> {reloaded: True, added: ["mynewcap"], removed: [], rewired_tools: 2}
# (agency_doctor.drift.surface_freshness tells you WHEN you need this.)
```

## See also

- [`docs/guide/usage.md`](../guide/usage.md) — the three-surface contract + the
  search → get_schema → execute loop.
- [`docs/guide/capabilities.md`](../guide/capabilities.md) — the generated
  reference for every capability + verb.
- [`Plan/292`](../../Plan/292-graph-markdown-interconnect/spec.md) …
  [`Plan/302`](../../Plan/302-plugin-accessibility-and-reload/spec.md) — the
  specs behind the recipes above.
