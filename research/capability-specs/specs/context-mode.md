---
spec_id: context-mode-001
slug: context-mode
status: draft
owner: "@claude"
depends_on: []
affects:
  - "agency/capabilities/context.py"
source-repos:
  - "https://github.com/netzkontrast/the-agency-system @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22"
estimated_jules_sessions: 2
domain: "context"
wave: 1
---

# Context Mode Cluster

## Why
`context-mode` is a specialized, read-only variant of `code-mode` designed to isolate state management, file caching, and manifest generation from the arbitrary side-effects of tool execution. This spec ports the `context-mode-manifest`, `contextignore-hardblock`, and cache subscriptions from the source `the-agency-system` (specs 111, 113, 121) directly into a dedicated capability to keep context synchronization fast and isolated.

## Done When
- [ ] Create `agency/capabilities/context.py` exposing a `context` capability.
- [ ] Implement `context.cache` to trigger deterministic delta updates.
- [ ] Implement `context.manifest` to read and enforce `contextignore`.

## Source clones
```bash
git clone --depth=1 https://github.com/netzkontrast/the-agency-system.git ~/work/vendor/the-agency-system
# SHA: 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22
```

## Files
- Create: `agency/capabilities/context.py`

## Evidence
- `the-agency-system/Plan/111-context-mode-manifest/spec.md`
- `the-agency-system/Plan/113-context-cache-and-subscriptions/spec.md`
- `the-agency-system/Plan/121-contextignore-hardblock/spec.md`

## Self-Review
Extracts the context synchronization responsibilities exactly as outlined in the Plan blueprints into their own capability.
