---
spec_id: jules-orchestration-001
slug: jules-orchestration
status: draft
owner: "@claude"
depends_on: []
affects:
  - "agency/capabilities/jules.py"
  - "agency/capabilities/_jules_api.py"
source-repos:
  - "https://github.com/netzkontrast/the-agency-system @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22"
estimated_jules_sessions: 2
domain: "orchestration"
wave: 2
---

# Jules Orchestration Cluster

## Why
The `jules` capability in the Agency base (`agency/capabilities/jules.py`) currently exposes only dispatch, status, and verify. This is insufficient for full orchestrator-agent negotiation; the orchestrator was observed falling back to `the-agency-system`'s legacy MCP client just to send this review message. The source repository `the-agency-system` implements the full REST API footprint (resume, feedback, approve_plan, activities, list, and complex resume semantics where COMPLETED != done). We must port these missing verbs into the Agency capability to eliminate the orchestrator-side fallback.

## Done When
- [ ] `agency/capabilities/jules.py` implements the `message` verb (wrapping `POST /v1alpha/sessions/{id}:sendMessage`).
- [ ] `agency/capabilities/jules.py` implements the `approve_plan` verb (wrapping `POST /v1alpha/sessions/{id}:approvePlan`).
- [ ] `agency/capabilities/jules.py` implements the `activities` and `list` verbs for session inspection.
- [ ] The `resume` semantics correctly distinguish between session state COMPLETED and verification done (silently recovering and allowing verification on origin branches).
- [ ] The new verbs are properly registered via `ctx.register_verb`.

## Source clones
```bash
git clone --depth=1 https://github.com/netzkontrast/the-agency-system.git ~/work/vendor/the-agency-system
# SHA: 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22
```

## Files
- Modify: `agency/capabilities/jules.py`
- Modify: `agency/capabilities/_jules_api.py`

## Evidence
- `the-agency-system/servers/agency-mcp/src/agency_mcp/handlers/jules/lifecycle.py`
- `the-agency-system/jules-plugin/mcp-server/src/jules_mcp/tools/lifecycle.py`
  (both at SHA `0a6a9e71f6c26bc120a8fc1db02f8990b7916f22`)

## Self-Review
This specification closes a live gap identified in the orchestrator runtime, pulling the missing REST bindings from the known complete source (`the-agency-system`) directly into the Agency runtime. Coverage is complete against the requested endpoints.
