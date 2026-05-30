---
spec_id: agentic-001
slug: agentic-cluster
status: draft
owner: "@claude"
depends_on: []
affects:
  - "agency/capabilities/agentic.py"
  - "agency/core.py"
source-repos:
  - "https://github.com/netzkontrast/the-agency-system @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22"
estimated_jules_sessions: 3
domain: "engine"
wave: 1
---

# Agentic Capability Cluster

## Why
Autonomous operation requires structural guardrails against infinite loops and resource exhaustion. `the-agency-system` introduced token budget invariants and engine-level loop detection middleware. Porting these directly into the Agency runtime (as `agentic.verify_invariants` and middleware injection in `core.py`) ensures safe swarm capabilities.

## Done When
- [ ] Implement `agentic.verify_invariants` to assert structural constraints post-delegate.
- [ ] Add engine-level loop detection middleware preventing recursion past a defined depth limit (replacing simple `ctx.spawn` depth guards).

## Source clones
```bash
git clone --depth=1 https://github.com/netzkontrast/the-agency-system.git ~/work/vendor/the-agency-system
# SHA: 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22
```

## Files
- Create: `agency/capabilities/agentic.py`
- Modify: `agency/core.py`

## Evidence
- `the-agency-system/Plan/119-loop-detection/spec.md`
- `the-agency-system/Plan/decisions/0009-token-budget-invariants.md`

## Self-Review
Integrates necessary autonomous runtime safeguards to safely enable complex subagent trees.
