---
spec_id: superclaude-analysts-001
slug: superclaude-analysts
status: draft
owner: "@claude"
depends_on: []
affects:
  - "agency/capabilities/subagent.py"
  - "agency/capabilities/delegate.py"
source-repos:
  - "https://github.com/SuperClaude-Org/SuperClaude_Framework @ 226c45cc93b865108843a669c6545d421784b68c"
  - "https://github.com/SuperClaude-Org/SuperClaude_Plugin @ de431dcc37aa6754be4a8d1be8c83cc834ac9dd5"
estimated_jules_sessions: 5
domain: "agents"
wave: 1
---

# SuperClaude Analysts Cluster

## Why
The `SuperClaude` ecosystem uses specialized personas and an exhaustive command/hooks framework to handle distinct concerns. We must ingest the *entirety* of this system—not just the agents. This includes the `scripts/`, `references/`, `docs/`, `config/`, `hooks/`, the install/setup machinery, MCP integrations, and every command/mode file from both the Framework and Plugin. In Agency, this translates to driving these configurations via the `delegate` capability, paired with formal profiles and setup lifecycle bindings.

## Done When
- [ ] Define the `AnalystProfile` ontology extension to register known personas (e.g., Requirements Analyst, Quality Engineer).
- [ ] Implement the `setup` verbs porting the installation and MCP integrations (`setup-mcp`, `verify-mcp`).
- [ ] Port the configuration and hooks machinery (`hooks/`, `config/`) as native Agency lifecycle pre/post triggers.
- [ ] Map the exhaustive command set (`sc-spec-panel`, `sc-test`, `sc-implement`, etc.) into `develop` skill verbs.
- [ ] Incorporate `references/` and `docs/` into T3 documentation bundles requested via context-mode.
- [ ] Add the `analyst.review_requirements` and `analyst.audit_quality` templates.

## Source clones
```bash
git clone --depth=1 https://github.com/SuperClaude-Org/SuperClaude_Framework.git ~/work/vendor/superclaude-framework
# SHA: 226c45cc93b865108843a669c6545d421784b68c
git clone --depth=1 https://github.com/SuperClaude-Org/SuperClaude_Plugin.git ~/work/vendor/superclaude-plugin
# SHA: de431dcc37aa6754be4a8d1be8c83cc834ac9dd5
```

## Files
- Modify: `agency/capabilities/subagent.py`
- Modify: `agency/capabilities/delegate.py`

## Evidence
- `superclaude-plugin/commands/` (exhaustive command ingestion: `setup-mcp.md`, `verify-mcp.md`, `sc-test.md`, `sc-implement.md`, etc.).
- `superclaude-framework/config/` and `hooks/`.
- `superclaude-framework/scripts/` (installation and setup logic).
- `superclaude-plugin/agents/` (personas).
- Full tree recursion spanning 400+ files mapped in `_ingest.md`.

## Self-Review
Maps the entirety of the SuperClaude ecosystem (personas + commands + setup + MCP + hooks) directly into Agency's structural subagent/delegate and lifecycle hooks capability.
