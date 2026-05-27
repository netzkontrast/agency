# Ingestion Ledger


**Deep Read Note:** Extracted 88 MCP tools from `bitwize-music/servers/bitwize-music-server/handlers`. Deeply ingested scripts, hooks, configs, and all skills/plugins across `SuperClaude_Framework`, `SuperClaude_Plugin`, and `superpowers-marketplace` using direct file parsing for functional enumeration.

| Path | Read? | Summary |
|---|---|---|
| agency/__init__.py | y | """agency — an installable Claude Code plugin: the v4 core on the real substrate. |
| agency/capabilities/__init__.py | y | """Capabilities — discovered by REFLECTION, not hand-wired. |
| agency/capabilities/_jules_api.py | y | """Minimal, self-contained Jules REST client (vendored into the agency plugin). |
| agency/capabilities/_vcs.py | y | """_vcs — the version-control boundary the `workspace` and `branch` capabilities |
| agency/capabilities/branch.py | y | """branch — finish a development branch: detect state, then merge / open a PR / |
| agency/capabilities/delegate.py | y | """delegate — agent orchestration: fan-out + quota + join. |
| agency/capabilities/develop.py | y | """develop — the development-workflow capability. |
| agency/capabilities/gate.py | y | """gate — a reusable, programmatic gate predicate. |
| agency/capabilities/jules.py | y | """jules — the agent capability. An agent IS a Lifecycle parameterization that |
| agency/capabilities/plugin.py | y | """The plugin-development capability — everything needed to develop a good plugin: |
| agency/capabilities/reflect.py | y | """reflect — durable, scope-tagged cross-session memory. |
| agency/capabilities/skill_generator.py | y | """skill_generator — generate a deploy-ready skill in one call. |
| agency/capabilities/subagent.py | y | """subagent — subagent-driven-development as a composition. |
| agency/capabilities/workspace.py | y | """workspace — isolate work in a git worktree + record a green baseline. |
| agency/capability.py | y | """Capability — the craft (the open concept). Verbs are capability-defined and |
| agency/cli.py | y | """Bash-callable engine — the L3 layer of the harness-in-harness ladder. |
| agency/engine.py | y | """Engine — one FastMCP server + one graph. |
| agency/install.py | y | """Setup for the Agency Plugin for Claude Code. |
| agency/intent.py | y | """Intent — the human-owned root (why/what merged; deliverable is an attribute). |
| agency/lifecycle.py | y | """Lifecycle — task/agent state-machine. Verb frame: open · move · close (write) |
| agency/memory.py | y | """Memory — the moat. One bi-temporal, append-only graph on real GraphQLite. |
| agency/ontology.py | y | """Strict, EXTENSIBLE ontology for the agency graph. |
| agency/skill.py | y | """Micro-step skill walker. |
| agency/templates.py | y | """Templates — the prestructure for the resulting document of each step of a chain. |
| docs/EXTENSION-PLAN.md | y | --- |
| docs/README.md | y | # Agency documentation |
| docs/ROADMAP.md | y | --- |
| docs/examples/README.md | y | # Examples |
| docs/examples/author_a_plugin.py | y | #!/usr/bin/env python |
| docs/getting-started.md | y | # Getting started with Agency |
| docs/guide/capabilities.md | y | # Capability reference |
| docs/guide/concepts.md | y | # Concepts (plain language) |
| docs/guide/extending.md | y | # Extending Agency |
| docs/guide/usage.md | y | # Using the engine |
| docs/vision/ARCHITECTURE.md | y | --- |
| docs/vision/CAPABILITY-CLUSTERS.md | y | # Capability roadmap |
| docs/vision/CORE.md | y | # agency — Core (v4) |
| docs/vision/EXAMPLE.md | y | --- |
| docs/vision/LESSONS.md | y | --- |
| docs/vision/OVERVIEW.md | y | --- |
| docs/vision/README.md | y | --- |
| docs/vision/VOCABULARY.md | y | --- |
| docs/vision/specs/README.md | y | --- |
| docs/vision/specs/capability-base.md | y | --- |
| docs/vision/specs/capability.md | y | --- |
| docs/vision/specs/engine.md | y | --- |
| docs/vision/specs/intent.md | y | --- |
| docs/vision/specs/lifecycle.md | y | --- |
| docs/vision/specs/memory.md | y | --- |
| docs/vision/specs/skills-and-gates.md | y | --- |
| docs/vision/specs/superpowers-port.md | y | --- |
| tests/test_agency.py | y | """The agency engine's proof. Runs on the REAL substrate (graphqlite + fastmcp). |
| vendor/the-agency-system/Plan/decisions/0010-single-delegate-pre-commit.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0009-token-budget-invariants.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0004-anchor-triad-as-wire-form.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0011-repair-authority-tiers.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0012-content-tier-ladder.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0007-code-mode-opt-in.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0004-five-handler-domains.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0006-frontmatter-canon.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0003-domain-plugin-contract.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0005-four-verb-contract.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0001-master-default-branch.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0006-code-mode-anchor-triad.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0007-context-mode-path-b.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0001-single-central-routing-skill.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0005-shared-toolresult-envelope.md | y | --- |
| vendor/the-agency-system/Plan/decisions/readme.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0003-single-mcp-server.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0002-sub-spec-zero-padding.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0008-harness-path-a.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0002-single-codemode-mcp-server.md | y | --- |
| vendor/the-agency-system/Plan/decisions/0008-wave-d-ontology-graph.md | y | --- |
| vendor/the-agency-system/Plan/023-harness-in-harness/spec.md | y | --- |
| vendor/the-agency-system/Plan/000-overview.md | y | # Plan 000 — Agency-System Unified Plugin (Master Overview, v2) |
| vendor/the-agency-system/Plan/008-codemode-registry/spec.md | y | --- |
| vendor/the-agency-system/Plan/harness/restructure/spec.md | y | --- |
| vendor/the-agency-system/Plan/harness/_research/01-fastmcp-in-memory.md | y | # Research 01 — FastMCP in-memory transport |
| vendor/the-agency-system/Plan/harness/_research/06-phase-2-through-8-forward-compat.md | y | # Research 06 — Phase 2-8 forward-compat audit (2026-05-18) |
| vendor/the-agency-system/Plan/harness/_research/05-domain-isomorphism.md | y | # Research 05 — Per-domain isomorphism audit (2026-05-18) |
| vendor/the-agency-system/Plan/harness/_research/03-test-coverage-baseline.md | y | # Research 03 — Test-coverage baseline (2026-05-18) |
| vendor/the-agency-system/Plan/harness/_research/02-claude-bare-plugin-dir.md | y | # Research 02 — `claude --bare --plugin-dir <path>` boot path |
| vendor/the-agency-system/Plan/harness/design.md | y | --- |
| vendor/the-agency-system/Plan/harness/VOCABULARY.md | y | --- |
| vendor/superclaude-framework/KNOWLEDGE.md | y | # KNOWLEDGE.md |
| vendor/superclaude-framework/TASK.md | y | # TASK.md |
| vendor/superclaude-framework/.env.example | y | Binary or unreadable file |
| vendor/superclaude-framework/CHANGELOG.md | y | # Changelog |
| vendor/superclaude-framework/PARALLEL_INDEXING_PLAN.md | y | # Parallel Repository Indexing Execution Plan |
| vendor/superclaude-framework/LICENSE | y | Binary or unreadable file |
| vendor/superclaude-framework/src/superclaude/commands/git.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/explain.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/sc.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/workflow.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/estimate.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/save.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/pm.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/index.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/task.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/implement.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/troubleshoot.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/research.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/__init__.py | y | Binary or unreadable file |
| vendor/superclaude-framework/src/superclaude/commands/select-tool.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/improve.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/reflect.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/business-panel.md | y | # /sc:business-panel - Business Panel Analysis System |
| vendor/superclaude-framework/src/superclaude/commands/help.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/design.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/analyze.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/spec-panel.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/cleanup.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/agent.md | y | name: sc:agent |
| vendor/superclaude-framework/src/superclaude/commands/load.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/brainstorm.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/spawn.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/test.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/build.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/recommend.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/README.md | y | # SuperClaude Commands |
| vendor/superclaude-framework/src/superclaude/commands/index-repo.md | y | --- |
| vendor/superclaude-framework/src/superclaude/commands/document.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/deep-research-agent.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/repo-index.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/technical-writer.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/frontend-architect.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/self-review.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/performance-engineer.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/python-expert.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/root-cause-analyst.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/quality-engineer.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/devops-architect.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/__init__.py | y | Binary or unreadable file |
| vendor/superclaude-framework/src/superclaude/agents/learning-guide.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/requirements-analyst.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/socratic-mentor.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/security-engineer.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/refactoring-expert.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/backend-architect.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/system-architect.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/pm-agent.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/deep-research.md | y | --- |
| vendor/superclaude-framework/src/superclaude/agents/README.md | y | # SuperClaude Agents |
| vendor/superclaude-framework/src/superclaude/agents/business-panel-experts.md | y | --- |
| vendor/superclaude-framework/src/superclaude/examples/__init__.py | y | Binary or unreadable file |
| vendor/superclaude-framework/src/superclaude/examples/deep_research_workflows.md | y | # Deep Research Workflows |
| vendor/superclaude-framework/src/superclaude/hooks/hooks.json | y | { |
| vendor/superclaude-framework/src/superclaude/hooks/__init__.py | y | Binary or unreadable file |
| vendor/superclaude-framework/src/superclaude/hooks/README.md | y | # SuperClaude Hooks |
| vendor/superclaude-framework/src/superclaude/pytest_plugin.py | y | """ |
| vendor/superclaude-framework/src/superclaude/core/PRINCIPLES.md | y | # Software Engineering Principles |
| vendor/superclaude-framework/src/superclaude/core/FLAGS.md | y | # SuperClaude Framework Flags |
| vendor/superclaude-framework/src/superclaude/core/RESEARCH_CONFIG.md | y | # Deep Research Configuration |
| vendor/superclaude-framework/src/superclaude/core/__init__.py | y | Binary or unreadable file |
| vendor/superclaude-framework/src/superclaude/core/RULES.md | y | # Claude Code Behavioral Rules |
| vendor/superclaude-framework/src/superclaude/core/BUSINESS_SYMBOLS.md | y | # BUSINESS_SYMBOLS.md - Business Analysis Symbol System |
| vendor/superclaude-framework/src/superclaude/core/BUSINESS_PANEL_EXAMPLES.md | y | # BUSINESS_PANEL_EXAMPLES.md - Usage Examples and Integration Patterns |
| vendor/superclaude-framework/src/superclaude/mcp/MCP_Mindbase.md | y | # MindBase MCP Server |
| vendor/superclaude-framework/src/superclaude/mcp/configs/magic.json | y | { |
| vendor/superclaude-framework/src/superclaude/mcp/configs/serena-docker.json | y | { |
| vendor/superclaude-framework/src/superclaude/mcp/configs/mindbase.json | y | { |
| vendor/superclaude-framework/src/superclaude/mcp/configs/airis-agent.json | y | { |
| vendor/superclaude-framework/src/superclaude/mcp/configs/context7.json | y | { |
| vendor/superclaude-framework/src/superclaude/mcp/configs/__init__.py | y | Binary or unreadable file |
| vendor/superclaude-framework/src/superclaude/mcp/configs/morphllm.json | y | { |
| vendor/superclaude-framework/src/superclaude/mcp/configs/serena.json | y | { |
| vendor/superclaude-framework/src/superclaude/mcp/configs/playwright.json | y | { |
| vendor/superclaude-framework/src/superclaude/mcp/configs/sequential.json | y | { |
| vendor/superclaude-framework/src/superclaude/mcp/configs/tavily.json | y | { |
| vendor/superclaude-framework/src/superclaude/mcp/MCP_Serena.md | y | # Serena MCP Server |
| vendor/superclaude-framework/src/superclaude/mcp/__init__.py | y | Binary or unreadable file |
| vendor/superclaude-framework/src/superclaude/mcp/MCP_Tavily.md | y | # Tavily MCP Server |
| vendor/superclaude-framework/src/superclaude/mcp/MCP_Magic.md | y | # Magic MCP Server |
| vendor/superclaude-framework/src/superclaude/mcp/MCP_Morphllm.md | y | # Morphllm MCP Server |
| vendor/superclaude-framework/src/superclaude/mcp/MCP_Context7.md | y | # Context7 MCP Server |
| vendor/superclaude-framework/src/superclaude/mcp/MCP_Chrome-DevTools.md | y | # Chrome DevTools MCP Server |
| vendor/superclaude-framework/src/superclaude/mcp/MCP_Sequential.md | y | # Sequential MCP Server |
| vendor/superclaude-framework/src/superclaude/mcp/MCP_Playwright.md | y | # Playwright MCP Server |
| vendor/superclaude-framework/src/superclaude/mcp/MCP_Airis-Agent.md | y | # Airis Agent MCP Server |
| vendor/superclaude-framework/src/superclaude/__init__.py | y | """ |
| vendor/superclaude-framework/src/superclaude/pm_agent/reflexion.py | y | """ |
| vendor/superclaude-framework/src/superclaude/pm_agent/token_budget.py | y | """ |
| vendor/superclaude-framework/src/superclaude/pm_agent/__init__.py | y | """ |
| vendor/superclaude-framework/src/superclaude/pm_agent/self_check.py | y | """ |
| vendor/superclaude-framework/src/superclaude/pm_agent/confidence.py | y | """ |
| vendor/superclaude-framework/src/superclaude/cli/main.py | y | """ |
| vendor/superclaude-framework/src/superclaude/cli/install_mcp.py | y | """ |
| vendor/superclaude-framework/src/superclaude/cli/__init__.py | y | """ |
| vendor/superclaude-framework/src/superclaude/cli/install_commands.py | y | """ |
| vendor/superclaude-framework/src/superclaude/cli/doctor.py | y | """ |
| vendor/superclaude-framework/src/superclaude/cli/install_skill.py | y | """ |
| vendor/superclaude-framework/src/superclaude/scripts/__init__.py | y | Binary or unreadable file |
| vendor/superclaude-framework/src/superclaude/scripts/session-init.sh | y | Binary or unreadable file |
| vendor/superclaude-framework/src/superclaude/scripts/clean_command_names.py | y | #!/usr/bin/env python3 |
| vendor/superclaude-framework/src/superclaude/scripts/README.md | y | # SuperClaude Scripts |
| vendor/superclaude-framework/src/superclaude/execution/__init__.py | y | """ |
| vendor/superclaude-framework/src/superclaude/execution/reflection.py | y | """ |
| vendor/superclaude-framework/src/superclaude/execution/self_correction.py | y | """ |
| vendor/superclaude-framework/src/superclaude/execution/parallel.py | y | """ |
| vendor/superclaude-framework/src/superclaude/skills/__init__.py | y | Binary or unreadable file |
| vendor/superclaude-framework/src/superclaude/skills/confidence-check/confidence.ts | y | Binary or unreadable file |
| vendor/superclaude-framework/src/superclaude/skills/confidence-check/__init__.py | y | Binary or unreadable file |
| vendor/superclaude-framework/src/superclaude/skills/confidence-check/SKILL.md | y | --- |
| vendor/superclaude-framework/src/superclaude/__version__.py | y | """Version information for SuperClaude""" |
| vendor/superclaude-framework/src/superclaude/modes/MODE_Task_Management.md | y | # Task Management Mode |
| vendor/superclaude-framework/src/superclaude/modes/MODE_DeepResearch.md | y | --- |
| vendor/superclaude-framework/src/superclaude/modes/MODE_Orchestration.md | y | # Orchestration Mode |
| vendor/superclaude-framework/src/superclaude/modes/MODE_Introspection.md | y | # Introspection Mode |
| vendor/superclaude-framework/src/superclaude/modes/__init__.py | y | Binary or unreadable file |
| vendor/superclaude-framework/src/superclaude/modes/MODE_Brainstorming.md | y | # Brainstorming Mode |
| vendor/superclaude-framework/src/superclaude/modes/MODE_Business_Panel.md | y | # MODE_Business_Panel.md - Business Panel Analysis Mode |
| vendor/superclaude-framework/src/superclaude/modes/MODE_Token_Efficiency.md | y | # Token Efficiency Mode |
| vendor/superclaude-framework/PLUGIN_INSTALL.md | y | # SuperClaude Plugin Installation Guide |
| vendor/superclaude-framework/README-kr.md | y | <div align="center"> |
| vendor/superclaude-framework/README-zh.md | y | <div align="center"> |
| vendor/superclaude-framework/DELETION_RATIONALE.md | y | # Deletion Rationale (Evidence-Based) |
| vendor/superclaude-framework/plugins/superclaude/commands/git.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/explain.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/sc.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/workflow.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/estimate.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/save.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/pm.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/index.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/task.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/implement.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/troubleshoot.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/research.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/select-tool.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/improve.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/reflect.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/business-panel.md | y | # /sc:business-panel - Business Panel Analysis System |
| vendor/superclaude-framework/plugins/superclaude/commands/help.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/design.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/analyze.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/spec-panel.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/cleanup.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/agent.md | y | name: sc:agent |
| vendor/superclaude-framework/plugins/superclaude/commands/load.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/brainstorm.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/spawn.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/test.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/build.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/recommend.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/index-repo.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/commands/document.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/deep-research-agent.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/repo-index.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/technical-writer.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/frontend-architect.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/self-review.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/performance-engineer.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/python-expert.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/root-cause-analyst.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/quality-engineer.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/devops-architect.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/learning-guide.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/requirements-analyst.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/socratic-mentor.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/security-engineer.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/refactoring-expert.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/backend-architect.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/system-architect.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/pm-agent.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/deep-research.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/agents/business-panel-experts.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/examples/deep_research_workflows.md | y | # Deep Research Workflows |
| vendor/superclaude-framework/plugins/superclaude/hooks/hooks.json | y | { |
| vendor/superclaude-framework/plugins/superclaude/.claude-plugin/plugin.json | y | { |
| vendor/superclaude-framework/plugins/superclaude/core/PRINCIPLES.md | y | # Software Engineering Principles |
| vendor/superclaude-framework/plugins/superclaude/core/FLAGS.md | y | # SuperClaude Framework Flags |
| vendor/superclaude-framework/plugins/superclaude/core/RESEARCH_CONFIG.md | y | # Deep Research Configuration |
| vendor/superclaude-framework/plugins/superclaude/core/RULES.md | y | # Claude Code Behavioral Rules |
| vendor/superclaude-framework/plugins/superclaude/core/BUSINESS_SYMBOLS.md | y | # BUSINESS_SYMBOLS.md - Business Analysis Symbol System |
| vendor/superclaude-framework/plugins/superclaude/core/BUSINESS_PANEL_EXAMPLES.md | y | # BUSINESS_PANEL_EXAMPLES.md - Usage Examples and Integration Patterns |
| vendor/superclaude-framework/plugins/superclaude/mcp/configs/magic.json | y | { |
| vendor/superclaude-framework/plugins/superclaude/mcp/configs/serena-docker.json | y | { |
| vendor/superclaude-framework/plugins/superclaude/mcp/configs/context7.json | y | { |
| vendor/superclaude-framework/plugins/superclaude/mcp/configs/morphllm.json | y | { |
| vendor/superclaude-framework/plugins/superclaude/mcp/configs/serena.json | y | { |
| vendor/superclaude-framework/plugins/superclaude/mcp/configs/playwright.json | y | { |
| vendor/superclaude-framework/plugins/superclaude/mcp/configs/sequential.json | y | { |
| vendor/superclaude-framework/plugins/superclaude/mcp/configs/tavily.json | y | { |
| vendor/superclaude-framework/plugins/superclaude/mcp/MCP_Serena.md | y | # Serena MCP Server |
| vendor/superclaude-framework/plugins/superclaude/mcp/MCP_Tavily.md | y | # Tavily MCP Server |
| vendor/superclaude-framework/plugins/superclaude/mcp/MCP_Magic.md | y | # Magic MCP Server |
| vendor/superclaude-framework/plugins/superclaude/mcp/MCP_Morphllm.md | y | # Morphllm MCP Server |
| vendor/superclaude-framework/plugins/superclaude/mcp/MCP_Context7.md | y | # Context7 MCP Server |
| vendor/superclaude-framework/plugins/superclaude/mcp/MCP_Chrome-DevTools.md | y | # Chrome DevTools MCP Server |
| vendor/superclaude-framework/plugins/superclaude/mcp/MCP_Sequential.md | y | # Sequential MCP Server |
| vendor/superclaude-framework/plugins/superclaude/mcp/MCP_Playwright.md | y | # Playwright MCP Server |
| vendor/superclaude-framework/plugins/superclaude/.mcp.json | y | { |
| vendor/superclaude-framework/plugins/superclaude/scripts/session-init.sh | y | Binary or unreadable file |
| vendor/superclaude-framework/plugins/superclaude/scripts/clean_command_names.py | y | #!/usr/bin/env python3 |
| vendor/superclaude-framework/plugins/superclaude/skills/troubleshoot/SKILL.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/skills/token-efficiency/SKILL.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/skills/confidence-check/confidence.ts | y | Binary or unreadable file |
| vendor/superclaude-framework/plugins/superclaude/skills/confidence-check/SKILL.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/skills/deep-research/SKILL.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/skills/pm/SKILL.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/skills/brainstorm/SKILL.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/README.md | y | # SuperClaude Plugin for Claude Code |
| vendor/superclaude-framework/plugins/superclaude/modes/MODE_Task_Management.md | y | # Task Management Mode |
| vendor/superclaude-framework/plugins/superclaude/modes/MODE_DeepResearch.md | y | --- |
| vendor/superclaude-framework/plugins/superclaude/modes/MODE_Orchestration.md | y | # Orchestration Mode |
| vendor/superclaude-framework/plugins/superclaude/modes/MODE_Introspection.md | y | # Introspection Mode |
| vendor/superclaude-framework/plugins/superclaude/modes/MODE_Brainstorming.md | y | # Brainstorming Mode |
| vendor/superclaude-framework/plugins/superclaude/modes/MODE_Business_Panel.md | y | # MODE_Business_Panel.md - Business Panel Analysis Mode |
| vendor/superclaude-framework/plugins/superclaude/modes/MODE_Token_Efficiency.md | y | # Token Efficiency Mode |
| vendor/superclaude-framework/setup.py | y | """ |
| vendor/superclaude-framework/QUALITY_COMPARISON.md | y | # Quality Comparison: Python vs TypeScript Implementation |
| vendor/superclaude-framework/docs/agents/pm-agent-guide.md | y | # PM Agent Guide |
| vendor/superclaude-framework/docs/testing/pm-workflow-test-results.md | y | # PM Agent Workflow Test Results - 2025-10-14 |
| vendor/superclaude-framework/docs/testing/procedures.md | y | # テスト手順とCI/CD |
| vendor/superclaude-framework/docs/reference/advanced-workflows.md | y | # SuperClaude Advanced Workflows Collection |
| vendor/superclaude-framework/docs/reference/mcp-server-guide.md | y | # MCP Server Troubleshooting Guide |
| vendor/superclaude-framework/docs/reference/suggested-commands.md | y | # 推奨コマンド集 |
| vendor/superclaude-framework/docs/reference/troubleshooting.md | y | # SuperClaude Troubleshooting Guide 🔧 |
| vendor/superclaude-framework/docs/reference/integration-patterns.md | y | # SuperClaude Integration Patterns Collection |
| vendor/superclaude-framework/docs/reference/basic-examples.md | y | # SuperClaude Basic Examples Collection |
| vendor/superclaude-framework/docs/reference/common-issues.md | y | # SuperClaude Common Issues - Quick Reference 🚀 |
| vendor/superclaude-framework/docs/reference/claude-code-history-management.md | y | # Claude Code Conversation History Management Research |
| vendor/superclaude-framework/docs/reference/advanced-patterns.md | y | # SuperClaude Advanced Patterns |
| vendor/superclaude-framework/docs/reference/pm-agent-autonomous-reflection.md | y | # PM Agent: Autonomous Reflection & Token Optimization |
| vendor/superclaude-framework/docs/reference/comprehensive-features.md | y | # SuperClaude Framework - Comprehensive Feature List |
| vendor/superclaude-framework/docs/reference/diagnostic-reference.md | y | # SuperClaude Diagnostic Reference Guide |
| vendor/superclaude-framework/docs/reference/commands-list.md | y | # SuperClaude Commands Reference |
| vendor/superclaude-framework/docs/reference/examples-cookbook.md | y | # SuperClaude Examples Cookbook |
| vendor/superclaude-framework/docs/reference/README.md | y | # SuperClaude Framework Reference Documentation |
| vendor/superclaude-framework/docs/plugin-reorg.md | y | # SuperClaude Plugin Re-organization Plan |
| vendor/superclaude-framework/docs/PR_STRATEGY.md | y | # PR Strategy for Clean Architecture Migration |
| vendor/superclaude-framework/docs/Development/PROJECT_STATUS.md | y | # SuperClaude Project Status |
| vendor/superclaude-framework/docs/Development/pm-agent-integration.md | y | # PM Agent Mode Integration Guide |
| vendor/superclaude-framework/docs/Development/TASKS.md | y | # SuperClaude Development Tasks |
| vendor/superclaude-framework/docs/Development/tasks/current-tasks.md | y | # Current Tasks - SuperClaude Framework |
| vendor/superclaude-framework/docs/Development/project-structure-understanding.md | y | # SuperClaude Framework - Project Structure Understanding |
| vendor/superclaude-framework/docs/Development/ROADMAP.md | y | # SuperClaude Development Roadmap |
| vendor/superclaude-framework/docs/Development/installation-flow-understanding.md | y | # SuperClaude Installation Flow - Complete Understanding |
| vendor/superclaude-framework/docs/Development/pm-agent-ideal-workflow.md | y | # PM Agent - Ideal Autonomous Workflow |
| vendor/superclaude-framework/docs/Development/hypothesis-pm-autonomous-enhancement-2025-10-14.md | y | # PM Agent Autonomous Enhancement - 改善提案 |
| vendor/superclaude-framework/docs/Development/ARCHITECTURE.md | y | # SuperClaude Architecture |
| vendor/superclaude-framework/docs/user-guide-jp/commands.md | y | # SuperClaude コマンドガイド |
| vendor/superclaude-framework/docs/user-guide-jp/session-management.md | y | # セッション管理ガイド |
| vendor/superclaude-framework/docs/user-guide-jp/agents.md | y | # SuperClaude エージェントガイド 🤖 |
| vendor/superclaude-framework/docs/user-guide-jp/mcp-servers.md | y | # SuperClaude MCP サーバーガイド 🔌 |
| vendor/superclaude-framework/docs/user-guide-jp/modes.md | y | # SuperClaude 行動モードガイド 🧠 |
| vendor/superclaude-framework/docs/user-guide-jp/flags.md | y | # SuperClaude フラグガイド 🏁 |
| vendor/superclaude-framework/docs/sessions/2025-10-14-summary.md | y | # Session Summary - PM Agent Enhancement (2025-10-14) |
| vendor/superclaude-framework/docs/next-refactor-plan.md | y | # Next Refactor Direction Overview |
| vendor/superclaude-framework/docs/troubleshooting/serena-installation.md | y | # Serena MCP Installation Troubleshooting |
| vendor/superclaude-framework/docs/mcp/mcp-integration-policy.md | y | # MCP Integration Policy |
| vendor/superclaude-framework/docs/mcp/mcp-optional-design.md | y | # MCP Optional Design |
| vendor/superclaude-framework/docs/user-guide-zh/commands.md | y | # SuperClaude 命令指南 |
| vendor/superclaude-framework/docs/user-guide-zh/session-management.md | y | # 会话管理指南 |
| vendor/superclaude-framework/docs/user-guide-zh/agents.md | y | # SuperClaude 智能体指南 🤖 |
| vendor/superclaude-framework/docs/user-guide-zh/mcp-servers.md | y | # SuperClaude MCP 服务器指南 🔌 |
| vendor/superclaude-framework/docs/user-guide-zh/modes.md | y | # SuperClaude 行为模式指南 🧠 |
| vendor/superclaude-framework/docs/user-guide-zh/flags.md | y | # SuperClaude 标志指南 🏁 |
| vendor/superclaude-framework/docs/pm-agent-implementation-status.md | y | # PM Agent Implementation Status |
| vendor/superclaude-framework/docs/user-guide/mcp-installation.md | y | # MCP Server Installation Guide |
| vendor/superclaude-framework/docs/user-guide/commands.md | y | # SC Commands Reference |
| vendor/superclaude-framework/docs/user-guide/session-management.md | y | # Session Management Guide |
| vendor/superclaude-framework/docs/user-guide/agents.md | y | # SuperClaude Agents Guide 🤖 |
| vendor/superclaude-framework/docs/user-guide/memory-system.md | y | # Memory System Guide |
| vendor/superclaude-framework/docs/user-guide/mcp-servers.md | y | # SuperClaude MCP Servers Guide 🔌 |
| vendor/superclaude-framework/docs/user-guide/modes.md | y | # SuperClaude Behavioral Modes Guide 🧠 |
| vendor/superclaude-framework/docs/user-guide/claude-code-integration.md | y | # Claude Code Integration Guide |
| vendor/superclaude-framework/docs/user-guide/flags.md | y | # SuperClaude Flags Guide 🏁 |
| vendor/superclaude-framework/docs/research/research_oss_fork_workflow_2025.md | y | # OSS Fork Workflow Best Practices 2025 |
| vendor/superclaude-framework/docs/research/parallel-execution-findings.md | y | # Parallel Execution Findings & Implementation |
| vendor/superclaude-framework/docs/research/skills-migration-test.md | y | # Skills Migration Test - PM Agent |
| vendor/superclaude-framework/docs/research/research_serena_mcp_2025-01-16.md | y | # Serena MCP Research Report |
| vendor/superclaude-framework/docs/research/mcp-installer-fix-summary.md | y | # MCP Installer Fix Summary |
| vendor/superclaude-framework/docs/research/phase1-implementation-strategy.md | y | # Phase 1 Implementation Strategy |
| vendor/superclaude-framework/docs/research/research_installer_improvements_20251017.md | y | # SuperClaude Installer Improvement Recommendations |
| vendor/superclaude-framework/docs/research/research_python_directory_naming_automation_2025.md | y | # Research: Python Directory Naming & Automation Tools (2025) |
| vendor/superclaude-framework/docs/research/reflexion-integration-2025.md | y | # Reflexion Framework Integration - PM Agent |
| vendor/superclaude-framework/docs/research/research_python_directory_naming_20251015.md | y | # Python Documentation Directory Naming Convention Research |
| vendor/superclaude-framework/docs/research/python_src_layout_research_20251021.md | y | # Python Src Layout Research - Repository vs Package Naming |
| vendor/superclaude-framework/docs/research/pm_agent_roi_analysis_2025-10-21.md | y | # PM Agent ROI Analysis: Self-Improving Agents with Latest Models (2025) |
| vendor/superclaude-framework/docs/research/parallel-execution-complete-findings.md | y | # Complete Parallel Execution Findings - Final Report |
| vendor/superclaude-framework/docs/research/repository-understanding-proposal.md | y | # Repository Understanding & Auto-Indexing Proposal |
| vendor/superclaude-framework/docs/research/research_git_branch_integration_2025.md | y | # Git Branch Integration Research: Master/Dev Divergence Resolution (2025) |
| vendor/superclaude-framework/docs/research/pm-mode-performance-analysis.md | y | # PM Mode Performance Analysis |
| vendor/superclaude-framework/docs/research/task-tool-parallel-execution-results.md | y | # Task Tool Parallel Execution - Results & Analysis |
| vendor/superclaude-framework/docs/research/research_repository_scoped_memory_2025-10-16.md | y | # Repository-Scoped Memory Management for AI Coding Assistants |
| vendor/superclaude-framework/docs/research/pm-skills-migration-results.md | y | # PM Agent Skills Migration - Results |
| vendor/superclaude-framework/docs/research/pm-mode-validation-methodology.md | y | # PM Mode Validation Methodology |
| vendor/superclaude-framework/docs/research/markdown-to-python-migration-plan.md | y | # Markdown → Python Migration Plan |
| vendor/superclaude-framework/docs/research/complete-python-skills-migration.md | y | # Complete Python + Skills Migration Plan |
| vendor/superclaude-framework/docs/research/llm-agent-token-efficiency-2025.md | y | # LLM Agent Token Efficiency & Context Management - 2025 Best Practices |
| vendor/superclaude-framework/docs/research/intelligent-execution-architecture.md | y | # Intelligent Execution Architecture |
| vendor/superclaude-framework/docs/architecture/PHASE_1_COMPLETE.md | y | # Phase 1 Migration Complete ✅ |
| vendor/superclaude-framework/docs/architecture/PM_AGENT_COMPARISON.md | y | # PM Agent: Upstream vs Clean Architecture Comparison |
| vendor/superclaude-framework/docs/architecture/PHASE_2_COMPLETE.md | y | # Phase 2 Migration Complete ✅ |
| vendor/superclaude-framework/docs/architecture/MIGRATION_TO_CLEAN_ARCHITECTURE.md | y | # Migration to Clean Plugin Architecture |
| vendor/superclaude-framework/docs/architecture/pm-agent-responsibility-cleanup.md | y | # PM Agent Responsibility Cleanup & MCP Integration |
| vendor/superclaude-framework/docs/architecture/SKILLS_CLEANUP.md | y | # Skills Cleanup for Clean Architecture |
| vendor/superclaude-framework/docs/architecture/PHASE_3_COMPLETE.md | y | # Phase 3 Migration Complete ✅ |
| vendor/superclaude-framework/docs/architecture/pm-agent-auto-activation.md | y | # PM Agent Auto-Activation Architecture |
| vendor/superclaude-framework/docs/architecture/CONTEXT_WINDOW_ANALYSIS.md | y | # Context Window Analysis: Old vs New Architecture |
| vendor/superclaude-framework/docs/user-guide-kr/commands.md | y | # SuperClaude 명령어 가이드 |
| vendor/superclaude-framework/docs/user-guide-kr/session-management.md | y | # 세션 관리 가이드 |
| vendor/superclaude-framework/docs/user-guide-kr/agents.md | y | # SuperClaude 에이전트 가이드 🤖 |
| vendor/superclaude-framework/docs/user-guide-kr/mcp-servers.md | y | # SuperClaude MCP 서버 가이드 🔌 |
| vendor/superclaude-framework/docs/user-guide-kr/modes.md | y | # SuperClaude 행동 모드 가이드 🧠 |
| vendor/superclaude-framework/docs/user-guide-kr/flags.md | y | # SuperClaude 플래그 가이드 🏁 |
| vendor/superclaude-framework/docs/memory/WORKFLOW_METRICS_SCHEMA.md | y | # Workflow Metrics Schema |
| vendor/superclaude-framework/docs/memory/next_actions.md | y | # Next Actions |
| vendor/superclaude-framework/docs/memory/token_efficiency_validation.md | y | # Token Efficiency Validation Report |
| vendor/superclaude-framework/docs/memory/last_session.md | y | # Last Session Summary |
| vendor/superclaude-framework/docs/memory/pm_context.md | y | # PM Agent Context |
| vendor/superclaude-framework/docs/memory/reflexion.jsonl.example | y | Binary or unreadable file |
| vendor/superclaude-framework/docs/memory/solutions_learned.jsonl | y | Binary or unreadable file |
| vendor/superclaude-framework/docs/memory/patterns_learned.jsonl | y | Binary or unreadable file |
| vendor/superclaude-framework/docs/memory/README.md | y | # Memory Directory |
| vendor/superclaude-framework/docs/memory/workflow_metrics.jsonl | y | Binary or unreadable file |
| vendor/superclaude-framework/docs/developer-guide/testing-debugging.md | y | # SuperClaude Verification and Troubleshooting Guide |
| vendor/superclaude-framework/docs/developer-guide/documentation-index.md | y | # SuperClaude Framework developer-guide Index |
| vendor/superclaude-framework/docs/developer-guide/contributing-code.md | y | # Contributing Context Files to SuperClaude Framework 🛠️ |
| vendor/superclaude-framework/docs/developer-guide/README.md | y | # SuperClaude Framework Developer Guide |
| vendor/superclaude-framework/docs/developer-guide/technical-architecture.md | y | # SuperClaude Context Architecture Guide |
| vendor/superclaude-framework/docs/getting-started/windows-installation.md | y | # Windows Installation Guide |
| vendor/superclaude-framework/docs/getting-started/quick-start.md | y | <div align="center"> |
| vendor/superclaude-framework/docs/getting-started/installation.md | y | <div align="center"> |
| vendor/superclaude-framework/docs/README.md | y | # SuperClaude Documentation |
| vendor/superclaude-framework/docs/Templates/__init__.py | y | Binary or unreadable file |
| vendor/superclaude-framework/docs/capability-mapping-v5.md | y | # SuperClaude v5: Capability-Driven Architecture |
| vendor/superclaude-framework/docs/mistakes/test_database_connection-2025-11-14.md | y | # Mistake Record: test_database_connection |
| vendor/superclaude-framework/docs/mistakes/test_reflexion_with_real_exception-2025-11-14.md | y | # Mistake Record: test_reflexion_with_real_exception |
| vendor/superclaude-framework/docs/mistakes/unknown-2025-11-14.md | y | # Mistake Record: unknown |
| vendor/superclaude-framework/docs/mistakes/test_reflexion_with_real_exception-2026-03-22.md | y | # Mistake Record: test_reflexion_with_real_exception |
| vendor/superclaude-framework/docs/mistakes/unknown-2026-03-22.md | y | # Mistake Record: unknown |
| vendor/superclaude-framework/docs/mistakes/test_database_connection-2026-03-22.md | y | # Mistake Record: test_database_connection |
| vendor/superclaude-framework/docs/mistakes/test_reflexion_with_real_exception-2025-11-11.md | y | # Mistake Record: test_reflexion_with_real_exception |
| vendor/superclaude-framework/docs/mistakes/unknown-2025-11-11.md | y | # Mistake Record: unknown |
| vendor/superclaude-framework/docs/mistakes/test_database_connection-2025-11-11.md | y | # Mistake Record: test_database_connection |
| vendor/superclaude-framework/PROJECT_INDEX.md | y | # Project Index: SuperClaude Framework |
| vendor/superclaude-framework/PLANNING.md | y | # PLANNING.md |
| vendor/superclaude-framework/PR_DOCUMENTATION.md | y | # PR: PM Mode as Default - Phase 1 Implementation |
| vendor/superclaude-framework/TEST_PLUGIN.md | y | # PM Agent Plugin Performance Test |
| vendor/superclaude-framework/scripts/publish.sh | y | Binary or unreadable file |
| vendor/superclaude-framework/scripts/analyze_workflow_metrics.py | y | #!/usr/bin/env python3 |
| vendor/superclaude-framework/scripts/ab_test_workflows.py | y | #!/usr/bin/env python3 |
| vendor/superclaude-framework/scripts/uninstall_legacy.sh | y | Binary or unreadable file |
| vendor/superclaude-framework/scripts/sync_from_framework.py | y | #!/usr/bin/env python3 |
| vendor/superclaude-framework/scripts/README.md | y | # SuperClaude PyPI Publishing Scripts |
| vendor/superclaude-framework/scripts/cleanup.sh | y | Binary or unreadable file |
| vendor/superclaude-framework/scripts/build_superclaude_plugin.py | y | #!/usr/bin/env python3 |
| vendor/superclaude-framework/CONTRIBUTING.md | y | # Contributing to SuperClaude Framework |
| vendor/superclaude-framework/CLAUDE.md | y | # CLAUDE.md |
| vendor/superclaude-framework/README-ja.md | y | <div align="center"> |
| vendor/superclaude-framework/pyproject.toml | y | Binary or unreadable file |
| vendor/superclaude-framework/CODE_OF_CONDUCT.md | y | # Code of Conduct |
| vendor/superclaude-framework/install.sh | y | Binary or unreadable file |
| vendor/superclaude-framework/PROJECT_INDEX.json | y | { |
| vendor/superclaude-framework/.pre-commit-config.yaml | y | # SuperClaude Framework - Pre-commit Hooks |
| vendor/superclaude-framework/AGENTS.md | y | # Repository Guidelines |
| vendor/superclaude-framework/SECURITY.md | y | # Security Policy |
| vendor/superclaude-framework/Makefile | y | Binary or unreadable file |
| vendor/superclaude-framework/skills/confidence-check/confidence.ts | y | Binary or unreadable file |
| vendor/superclaude-framework/skills/confidence-check/SKILL.md | y | --- |
| vendor/superclaude-framework/MANIFEST.in | y | Binary or unreadable file |
| vendor/superclaude-framework/package.json | y | { |
| vendor/superclaude-framework/VERSION | y | Binary or unreadable file |
| vendor/superclaude-framework/.claude/settings.json | y | {} |
| vendor/superclaude-framework/.claude/skills/confidence-check/confidence.ts | y | Binary or unreadable file |
| vendor/superclaude-framework/.claude/skills/confidence-check/SKILL.md | y | --- |
| vendor/superclaude-framework/README.md | y | <div align="center"> |
| vendor/superclaude-framework/tests/conftest.py | y | """ |
| vendor/superclaude-framework/tests/integration/test_execution_engine.py | y | """ |
| vendor/superclaude-framework/tests/integration/__init__.py | y | """ |
| vendor/superclaude-framework/tests/integration/test_pytest_plugin.py | y | """ |
| vendor/superclaude-framework/tests/__init__.py | y | """ |
| vendor/superclaude-framework/tests/unit/test_confidence.py | y | """ |
| vendor/superclaude-framework/tests/unit/test_parallel.py | y | """ |
| vendor/superclaude-framework/tests/unit/test_reflexion.py | y | """ |
| vendor/superclaude-framework/tests/unit/__init__.py | y | """ |
| vendor/superclaude-framework/tests/unit/test_self_correction.py | y | """ |
| vendor/superclaude-framework/tests/unit/test_cli_install.py | y | """ |
| vendor/superclaude-framework/tests/unit/test_self_check.py | y | """ |
| vendor/superclaude-framework/tests/unit/test_reflection.py | y | """ |
| vendor/superclaude-framework/tests/unit/test_token_budget.py | y | """ |
| vendor/superclaude-framework/CODEOWNERS | y | Binary or unreadable file |
| vendor/superclaude-plugin/commands/sc-spec-panel.md | y | --- |
| vendor/superclaude-plugin/commands/sc-agent.md | y | name: sc:agent |
| vendor/superclaude-plugin/commands/sc-recommend.md | y | --- |
| vendor/superclaude-plugin/commands/setup-mcp.md | y | --- |
| vendor/superclaude-plugin/commands/sc-test.md | y | --- |
| vendor/superclaude-plugin/commands/sc-implement.md | y | --- |
| vendor/superclaude-plugin/commands/sc-document.md | y | --- |
| vendor/superclaude-plugin/commands/sc-help.md | y | --- |
| vendor/superclaude-plugin/commands/sc-design.md | y | --- |
| vendor/superclaude-plugin/commands/sc-troubleshoot.md | y | --- |
| vendor/superclaude-plugin/commands/sc-sc.md | y | --- |
| vendor/superclaude-plugin/commands/sc-index-repo.md | y | --- |
| vendor/superclaude-plugin/commands/sc-brainstorm.md | y | --- |
| vendor/superclaude-plugin/commands/sc-pm.md | y | --- |
| vendor/superclaude-plugin/commands/sc-cleanup.md | y | --- |
| vendor/superclaude-plugin/commands/sc-explain.md | y | --- |
| vendor/superclaude-plugin/commands/sc-research.md | y | --- |
| vendor/superclaude-plugin/commands/sc-business-panel.md | y | # /sc:sc:sc:business-panel - Business Panel Analysis System |
| vendor/superclaude-plugin/commands/sc-git.md | y | --- |
| vendor/superclaude-plugin/commands/sc-load.md | y | --- |
| vendor/superclaude-plugin/commands/sc-reflect.md | y | --- |
| vendor/superclaude-plugin/commands/sc-README.md | y | # SuperClaude Commands |
| vendor/superclaude-plugin/commands/sc-estimate.md | y | --- |
| vendor/superclaude-plugin/commands/sc-analyze.md | y | --- |
| vendor/superclaude-plugin/commands/sc-build.md | y | --- |
| vendor/superclaude-plugin/commands/sc-improve.md | y | --- |
| vendor/superclaude-plugin/commands/sc-select-tool.md | y | --- |
| vendor/superclaude-plugin/commands/verify-mcp.md | y | --- |
| vendor/superclaude-plugin/commands/sc-spawn.md | y | --- |
| vendor/superclaude-plugin/commands/sc-index.md | y | --- |
| vendor/superclaude-plugin/commands/sc-workflow.md | y | --- |
| vendor/superclaude-plugin/commands/sc-save.md | y | --- |
| vendor/superclaude-plugin/commands/sc-task.md | y | --- |
| vendor/superclaude-plugin/agents/sc-business-panel-experts.md | y | --- |
| vendor/superclaude-plugin/agents/sc-performance-engineer.md | y | --- |
| vendor/superclaude-plugin/agents/sc-backend-architect.md | y | --- |
| vendor/superclaude-plugin/agents/ContextEngineering/metrics-analyst.md | y | --- |
| vendor/superclaude-plugin/agents/ContextEngineering/output-architect.md | y | --- |
| vendor/superclaude-plugin/agents/ContextEngineering/IMPLEMENTATION_SUMMARY.md | y | # Context Engineering Implementation Summary |
| vendor/superclaude-plugin/agents/ContextEngineering/documentation-specialist.md | y | --- |
| vendor/superclaude-plugin/agents/ContextEngineering/context-orchestrator.md | y | --- |
| vendor/superclaude-plugin/agents/ContextEngineering/README.md | y | # Context Engineering Agents for SuperClaude |
| vendor/superclaude-plugin/agents/sc-socratic-mentor.md | y | --- |
| vendor/superclaude-plugin/agents/sc-frontend-architect.md | y | --- |
| vendor/superclaude-plugin/agents/sc-self-review.md | y | --- |
| vendor/superclaude-plugin/agents/sc-system-architect.md | y | --- |
| vendor/superclaude-plugin/agents/sc-requirements-analyst.md | y | --- |
| vendor/superclaude-plugin/agents/sc-quality-engineer.md | y | --- |
| vendor/superclaude-plugin/agents/sc-repo-index.md | y | --- |
| vendor/superclaude-plugin/agents/sc-root-cause-analyst.md | y | --- |
| vendor/superclaude-plugin/agents/sc-python-expert.md | y | --- |
| vendor/superclaude-plugin/agents/sc-security-engineer.md | y | --- |
| vendor/superclaude-plugin/agents/sc-devops-architect.md | y | --- |
| vendor/superclaude-plugin/agents/sc-learning-guide.md | y | --- |
| vendor/superclaude-plugin/agents/sc-deep-research.md | y | --- |
| vendor/superclaude-plugin/agents/sc-README.md | y | # SuperClaude Agents |
| vendor/superclaude-plugin/agents/sc-deep-research-agent.md | y | --- |
| vendor/superclaude-plugin/agents/sc-refactoring-expert.md | y | --- |
| vendor/superclaude-plugin/agents/sc-technical-writer.md | y | --- |
| vendor/superclaude-plugin/agents/sc-pm-agent.md | y | --- |
| vendor/superclaude-plugin/LICENSE | y | Binary or unreadable file |
| vendor/superclaude-plugin/BACKUP_GUIDE.md | y | # 🛡️ SuperClaude Plugin - Complete Backup & Safety Guide |
| vendor/superclaude-plugin/README-zh.md | y | <div align="center"> |
| vendor/superclaude-plugin/.claude-plugin/marketplace.json | y | { |
| vendor/superclaude-plugin/.claude-plugin/plugin.json | y | { |
| vendor/superclaude-plugin/docs/SYNC_SYSTEM.md | y | # Automated Sync System Documentation |
| vendor/superclaude-plugin/docs/.framework-sync-commit | y | Binary or unreadable file |
| vendor/superclaude-plugin/core/PRINCIPLES.md | y | # Software Engineering Principles |
| vendor/superclaude-plugin/core/FLAGS.md | y | # SuperClaude Framework Flags |
| vendor/superclaude-plugin/core/RESEARCH_CONFIG.md | y | # Deep Research Configuration |
| vendor/superclaude-plugin/core/RULES.md | y | # Claude Code Behavioral Rules |
| vendor/superclaude-plugin/core/BUSINESS_SYMBOLS.md | y | # BUSINESS_SYMBOLS.md - Business Analysis Symbol System |
| vendor/superclaude-plugin/core/BUSINESS_PANEL_EXAMPLES.md | y | # BUSINESS_PANEL_EXAMPLES.md - Usage Examples and Integration Patterns |
| vendor/superclaude-plugin/plugin.json | y | { |
| vendor/superclaude-plugin/MIGRATION_GUIDE.md | y | # SuperClaude Migration Guide |
| vendor/superclaude-plugin/scripts/backup-claude-config.sh | y | Binary or unreadable file |
| vendor/superclaude-plugin/scripts/sync_from_framework.py | y | #!/usr/bin/env python3 |
| vendor/superclaude-plugin/scripts/clean_command_names.py | y | #!/usr/bin/env python3 |
| vendor/superclaude-plugin/CLAUDE.md | y | # SuperClaude Plugin |
| vendor/superclaude-plugin/benchmark/results/benchmark_20251121_121132.json | y | { |
| vendor/superclaude-plugin/benchmark/results/detailed_analysis_20251121_121502.json | y | Binary or unreadable file |
| vendor/superclaude-plugin/benchmark/results/fair_comparison_20251121_122250.json | y | { |
| vendor/superclaude-plugin/benchmark/results/detailed_analysis_20251121_121528.json | y | { |
| vendor/superclaude-plugin/benchmark/performance-test.sh | y | Binary or unreadable file |
| vendor/superclaude-plugin/benchmark/detailed-analysis.sh | y | Binary or unreadable file |
| vendor/superclaude-plugin/benchmark/fair-comparison-test.sh | y | Binary or unreadable file |
| vendor/superclaude-plugin/benchmark/BIAS_ANALYSIS.md | y | # Test Bias Analysis - Critical Review |
| vendor/superclaude-plugin/benchmark/SUMMARY.md | y | # Benchmark Summary - Quick Reference |
| vendor/superclaude-plugin/benchmark/FAIR_CONCLUSION.md | y | # Fair Performance Comparison - Honest Analysis |
| vendor/superclaude-plugin/benchmark/PERFORMANCE_EVIDENCE.md | y | # SuperClaude Plugin Performance Evidence |
| vendor/superclaude-plugin/benchmark/README.md | y | # Performance Benchmark |
| vendor/superclaude-plugin/benchmark/STRATEGIC_ANALYSIS.md | y | # Strategic Analysis: Plugin vs MCP Gateway Architecture |
| vendor/superclaude-plugin/README-ja.md | y | <div align="center"> |
| vendor/superclaude-plugin/SECURITY.md | y | # Security Policy |
| vendor/superclaude-plugin/backups/plugin.json.20260212_001942.backup | y | Binary or unreadable file |
| vendor/superclaude-plugin/backups/plugin.json.20260212_001931.backup | y | Binary or unreadable file |
| vendor/superclaude-plugin/README.md | y | <div align="center"> |
| vendor/superclaude-plugin/tests/test_sync.py | y | """ |
| vendor/superclaude-plugin/modes/MODE_Task_Management.md | y | # Task Management Mode |
| vendor/superclaude-plugin/modes/MODE_DeepResearch.md | y | --- |
| vendor/superclaude-plugin/modes/MODE_Orchestration.md | y | # Orchestration Mode |
| vendor/superclaude-plugin/modes/MODE_Introspection.md | y | # Introspection Mode |
| vendor/superclaude-plugin/modes/MODE_Brainstorming.md | y | # Brainstorming Mode |
| vendor/superclaude-plugin/modes/MODE_Business_Panel.md | y | # MODE_Business_Panel.md - Business Panel Analysis Mode |
| vendor/superclaude-plugin/modes/MODE_Token_Efficiency.md | y | # Token Efficiency Mode |
| vendor/bitwize-music/templates/track.md | y | --- |
| vendor/bitwize-music/templates/album.md | y | --- |
| vendor/bitwize-music/templates/research.md | y | # [Album Name] - Research & Source Documentation |
| vendor/bitwize-music/templates/ideas.md | y | # Album Ideas |
| vendor/bitwize-music/templates/sources.md | y | # [Album Name] - Sources & Documentation |
| vendor/bitwize-music/templates/genre.md | y | # [Genre Name] |
| vendor/bitwize-music/templates/promo/facebook.md | y | # [Album Name] — Facebook |
| vendor/bitwize-music/templates/promo/instagram.md | y | # [Album Name] — Instagram |
| vendor/bitwize-music/templates/promo/tiktok.md | y | # [Album Name] — TikTok |
| vendor/bitwize-music/templates/promo/youtube.md | y | # [Album Name] — YouTube |
| vendor/bitwize-music/templates/promo/twitter.md | y | # [Album Name] — Twitter/X |
| vendor/bitwize-music/templates/promo/campaign.md | y | # [Album Name] — Promo Campaign |
| vendor/bitwize-music/templates/artist.md | y | # [Artist Name] |
| vendor/bitwize-music/CHANGELOG.md | y | # Changelog |
| vendor/bitwize-music/config/config.example.yaml | y | # ============================================================================= |
| vendor/bitwize-music/config/overrides.example/suno-preferences.md | y | # Suno Preferences |
| vendor/bitwize-music/config/overrides.example/research-preferences.md | y | # Research Preferences |
| vendor/bitwize-music/config/overrides.example/album-planning-guide.md | y | # Album Planning Guide |
| vendor/bitwize-music/config/overrides.example/promotion-preferences.md | y | # Promotion Preferences |
| vendor/bitwize-music/config/overrides.example/mastering-presets.yaml | y | # Custom Mastering Presets |
| vendor/bitwize-music/config/overrides.example/album-art-preferences.md | y | # Album Art Preferences |
| vendor/bitwize-music/config/overrides.example/sheet-music-preferences.md | y | # Sheet Music Preferences |
| vendor/bitwize-music/config/overrides.example/CLAUDE.md | y | # Custom Workflow Instructions |
| vendor/bitwize-music/config/overrides.example/explicit-words.md | y | # Custom Explicit Words |
| vendor/bitwize-music/config/overrides.example/lyric-writing-guide.md | y | # Lyric Writing Guide |
| vendor/bitwize-music/config/overrides.example/pronunciation-guide.md | y | # Pronunciation Guide (Override) |
| vendor/bitwize-music/config/overrides.example/README.md | y | # Override Examples |
| vendor/bitwize-music/config/overrides.example/release-preferences.md | y | # Release Preferences |
| vendor/bitwize-music/config/README.md | y | # Configuration |
| vendor/bitwize-music/reference/promotion/promotion-preferences-override.md | y | # Promotion Preferences Override Template |
| vendor/bitwize-music/reference/promotion/platform-specs.md | y | # Platform Specifications for Promo Videos |
| vendor/bitwize-music/reference/promotion/social-media-best-practices.md | y | # Social Media Best Practices for Music Promotion |
| vendor/bitwize-music/reference/promotion/ffmpeg-reference.md | y | # ffmpeg Technical Reference for Promo Videos |
| vendor/bitwize-music/reference/promotion/example-output.md | y | # Promo Video Example Output |
| vendor/bitwize-music/reference/promotion/promo-workflow.md | y | # Promo Video Workflow |
| vendor/bitwize-music/reference/quick-start/true-story-album.md | y | # Quick Start: True Story Album |
| vendor/bitwize-music/reference/quick-start/first-album.md | y | # Quick Start: Your First Album |
| vendor/bitwize-music/reference/quick-start/bulk-releases.md | y | # Quick Start: Bulk Releases |
| vendor/bitwize-music/reference/model-strategy.md | y | # Model Selection Strategy |
| vendor/bitwize-music/reference/overrides/override-index.md | y | # Override Index |
| vendor/bitwize-music/reference/overrides/how-to-customize.md | y | # How to Customize the Plugin |
| vendor/bitwize-music/reference/sheet-music/workflow.md | y | # Sheet Music Generation Workflow |
| vendor/bitwize-music/reference/sheet-music/troubleshooting.md | y | # Sheet Music Troubleshooting |
| vendor/bitwize-music/reference/sheet-music/genre-recommendations.md | y | # Sheet Music Genre Recommendations |
| vendor/bitwize-music/reference/cloud/setup-guide.md | y | # Cloud Storage Setup Guide |
| vendor/bitwize-music/reference/mastering/genre-specific-presets.md | y | # Genre-Specific Mastering Presets |
| vendor/bitwize-music/reference/mastering/mastering-workflow.md | y | # Audio Mastering Workflow for Album Releases |
| vendor/bitwize-music/reference/mastering/mastering-checklist.md | y | # Mastering Checklist |
| vendor/bitwize-music/reference/mastering/loudness-measurement.md | y | # Loudness Measurement Guide |
| vendor/bitwize-music/reference/cross-platform/tool-compatibility-matrix.md | y | # Tool Compatibility Matrix |
| vendor/bitwize-music/reference/cross-platform/wsl-setup-guide.md | y | # WSL2 Setup Guide for Claude AI Music Skills |
| vendor/bitwize-music/reference/SKILL_INDEX.md | y | # Skill Index & Decision Tree |
| vendor/bitwize-music/reference/distribution.md | y | # Distribution Reference |
| vendor/bitwize-music/reference/workflows/importing-audio.md | y | # Importing Audio Files |
| vendor/bitwize-music/reference/workflows/release-procedures.md | y | # Release Procedures |
| vendor/bitwize-music/reference/workflows/checkpoint-scripts.md | y | # Checkpoint Scripts |
| vendor/bitwize-music/reference/workflows/album-planning-phases.md | y | # Album Planning: The 7 Phases |
| vendor/bitwize-music/reference/workflows/source-verification-handoff.md | y | # Source Verification Handoff Procedures |
| vendor/bitwize-music/reference/workflows/status-tracking.md | y | # Status Tracking |
| vendor/bitwize-music/reference/workflows/error-recovery.md | y | # Error Recovery Procedures |
| vendor/bitwize-music/reference/state-schema.md | y | # State Cache Schema (v1.2.0) |
| vendor/bitwize-music/reference/terminology.md | y | # Terminology Glossary |
| vendor/bitwize-music/reference/suno/structure-tags.md | y | # Suno Structure Tags Reference |
| vendor/bitwize-music/reference/suno/CHANGELOG.md | y | # Suno Documentation Changelog |
| vendor/bitwize-music/reference/suno/voice-tags.md | y | # Suno Voice Tags Reference |
| vendor/bitwize-music/reference/suno/genre-list.md | y | # Suno Genre List |
| vendor/bitwize-music/reference/suno/tips-and-tricks.md | y | # Suno Tips & Tricks |
| vendor/bitwize-music/reference/suno/workspace-management.md | y | # Suno Workspace Management |
| vendor/bitwize-music/reference/suno/artist-blocklist.md | y | # Artist Name Blocklist for Suno |
| vendor/bitwize-music/reference/suno/v5-best-practices.md | y | # Suno V5 / V5.5 Best Practices |
| vendor/bitwize-music/reference/suno/instrumental-tags.md | y | # Suno Instrumental Tags Reference |
| vendor/bitwize-music/reference/suno/pronunciation-guide.md | y | # Pronunciation Guide for Suno Lyrics |
| vendor/bitwize-music/reference/suno/README.md | y | # Suno Reference Documentation |
| vendor/bitwize-music/reference/suno/version-history/v5-changes.md | y | # Suno V4 → V5 Migration Guide |
| vendor/bitwize-music/reference/release/distributor-guide.md | y | # Distributor Comparison Guide |
| vendor/bitwize-music/reference/release/platform-comparison.md | y | # Platform Comparison Guide |
| vendor/bitwize-music/reference/release/metadata-by-platform.md | y | # Metadata Requirements by Platform |
| vendor/bitwize-music/reference/release/rights-and-claims.md | y | # Rights and Claims Guide |
| vendor/bitwize-music/reference/streaming-mastering-specs.md | y | # Streaming Mastering Specs |
| vendor/bitwize-music/LICENSE | y | Binary or unreadable file |
| vendor/bitwize-music/hooks/hooks.json | y | { |
| vendor/bitwize-music/hooks/validate_track.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/hooks/install.sh | y | Binary or unreadable file |
| vendor/bitwize-music/hooks/pre-commit | y | Binary or unreadable file |
| vendor/bitwize-music/hooks/README.md | y | # Git Hooks |
| vendor/bitwize-music/hooks/check_version_sync.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/.claude-plugin/marketplace.json | y | { |
| vendor/bitwize-music/.claude-plugin/plugin.json | y | { |
| vendor/bitwize-music/requirements-test.txt | y | # Test dependencies |
| vendor/bitwize-music/docs/images/be-excellent-to-each-other.jpg | y | Binary or unreadable file |
| vendor/bitwize-music/docs/skills.md | y | # Skills Reference |
| vendor/bitwize-music/docs/troubleshooting.md | y | # Troubleshooting |
| vendor/bitwize-music/docs/configuration.md | y | # Configuration |
| vendor/bitwize-music/.mcp.json | y | { |
| vendor/bitwize-music/TESTING.md | y | # Testing Plan for claude-ai-music-skills |
| vendor/bitwize-music/CONTRIBUTING.md | y | # Contributing to claude-ai-music-skills |
| vendor/bitwize-music/requirements.txt | y | # Claude AI Music Skills - Python Dependencies |
| vendor/bitwize-music/CLAUDE.md | y | # AI Music Skills - Claude Instructions |
| vendor/bitwize-music/pyproject.toml | y | Binary or unreadable file |
| vendor/bitwize-music/CODE_OF_CONDUCT.md | y | # Code of Conduct |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/maintenance.py | y | """Maintenance tools — reset mastering, legacy cleanup, audio layout migration.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/streaming.py | y | """Streaming URL management tools.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/skills.py | y | """Skills listing tools — query and filter plugin skills.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/text_analysis.py | y | """Text analysis tools — homographs, artist names, pronunciation, explicit content, lyrics stats.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/_shared.py | y | """Shared state, constants, and helpers used across handler modules. |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/promo.py | y | """Promo directory tools — promo status and content retrieval.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/gates.py | y | """Pre-generation gates and release readiness checks.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/database.py | y | """Database tools — tweet/promo management via PostgreSQL.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/__init__.py | y | """Handler modules for the bitwize-music MCP server. |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/core.py | y | """Core query tools — albums, tracks, sessions, config, search, paths.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/lyrics_analysis.py | y | """Lyrics analysis tools — plagiarism detection, syllable counting, readability, rhyme analysis.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/status.py | y | """Album status transitions and track creation tools.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/ideas.py | y | """Idea management tools — create, update, and promote album ideas.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/rename.py | y | """Rename tools — album and track renaming with mirrored path updates.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/content.py | y | """Content and override tools — loading reference files, overrides, and clipboard formatting.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/processing/_helpers.py | y | """Shared helpers for processing submodules.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/processing/mixing.py | y | """Mix polish tools — per-stem audio cleanup before mastering.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/processing/__init__.py | y | """Processing tools — audio mastering, sheet music, promo videos, mix polishing. |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/processing/video.py | y | """Promo video generation tools.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/processing/audio.py | y | """Audio mastering and analysis tools.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/processing/sheet_music.py | y | """Sheet music transcription and publishing tools.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/processing/_album_stages.py | y | """Per-stage implementations for master_album (#290 D5 — stage extraction). |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/_atomic.py | y | """Atomic file write utility. |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/health.py | y | """Plugin version, venv health check, and diagnostic tools.""" |
| vendor/bitwize-music/servers/bitwize-music-server/handlers/album_ops.py | y | """Album operation tools — full album query, structure validation, album creation.""" |
| vendor/bitwize-music/servers/bitwize-music-server/server.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/servers/bitwize-music-server/__init__.py | y | # bitwize-music-state MCP server |
| vendor/bitwize-music/servers/bitwize-music-server/README.md | y | # bitwize-music MCP Server |
| vendor/bitwize-music/servers/bitwize-music-server/run.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/Makefile | y | Binary or unreadable file |
| vendor/bitwize-music/skills/mix-engineer/mix-presets.md | y | # Mix Polish Genre Presets |
| vendor/bitwize-music/skills/mix-engineer/SKILL.md | y | --- |
| vendor/bitwize-music/skills/test/SKILL.md | y | --- |
| vendor/bitwize-music/skills/test/test-definitions.md | y | # TEST CATEGORIES |
| vendor/bitwize-music/skills/clipboard/USAGE_EXAMPLES.md | y | # Clipboard Skill - Usage Examples |
| vendor/bitwize-music/skills/clipboard/SKILL.md | y | --- |
| vendor/bitwize-music/skills/document-hunter/SKILL.md | y | --- |
| vendor/bitwize-music/skills/document-hunter/site-patterns.md | y | # Site-Specific Patterns |
| vendor/bitwize-music/skills/plagiarism-checker/SKILL.md | y | --- |
| vendor/bitwize-music/skills/album-dashboard/SKILL.md | y | --- |
| vendor/bitwize-music/skills/voice-checker/SKILL.md | y | --- |
| vendor/bitwize-music/skills/album-ideas/STATUS_VALUES.md | y | # Album Ideas - Status Values |
| vendor/bitwize-music/skills/album-ideas/SKILL.md | y | --- |
| vendor/bitwize-music/skills/promo-director/visualization-guide.md | y | # Promo Video Visualization Styles |
| vendor/bitwize-music/skills/promo-director/SKILL.md | y | --- |
| vendor/bitwize-music/skills/promo-director/technical-reference.md | y | # Promo Director - Technical Reference |
| vendor/bitwize-music/skills/researchers-legal/DISCOVERY_GUIDE.md | y | # Legal Document Discovery Guide |
| vendor/bitwize-music/skills/researchers-legal/SKILL.md | y | --- |
| vendor/bitwize-music/skills/new-album/SKILL.md | y | --- |
| vendor/bitwize-music/skills/researchers-journalism/SKILL.md | y | --- |
| vendor/bitwize-music/skills/researchers-journalism/SOURCE_EXTRACTION.md | y | # Journalism Source Extraction Guide |
| vendor/bitwize-music/skills/pronunciation-specialist/SKILL.md | y | --- |
| vendor/bitwize-music/skills/pronunciation-specialist/word-lists.md | y | # Pronunciation Word Lists |
| vendor/bitwize-music/skills/suno-engineer/genre-practices.md | y | # Genre-Specific Best Practices |
| vendor/bitwize-music/skills/suno-engineer/SKILL.md | y | --- |
| vendor/bitwize-music/skills/mastering-engineer/genre-presets.md | y | # Genre-Specific Mastering Presets |
| vendor/bitwize-music/skills/mastering-engineer/SKILL.md | y | --- |
| vendor/bitwize-music/skills/cloud-uploader/SKILL.md | y | --- |
| vendor/bitwize-music/skills/about/SKILL.md | y | --- |
| vendor/bitwize-music/skills/about/PROJECT_HISTORY.md | y | # Project History |
| vendor/bitwize-music/skills/researcher/templates.md | y | # Research Templates & Examples |
| vendor/bitwize-music/skills/researcher/source-standards.md | y | # Source Standards & Hierarchy |
| vendor/bitwize-music/skills/researcher/SKILL.md | y | --- |
| vendor/bitwize-music/skills/researcher/free-sources.md | y | # Free Document Sources |
| vendor/bitwize-music/skills/promo-writer/copy-formulas.md | y | # Copy Formulas Reference |
| vendor/bitwize-music/skills/promo-writer/SKILL.md | y | --- |
| vendor/bitwize-music/skills/sheet-music-publisher/anthemscore-reference.md | y | # AnthemScore CLI Reference |
| vendor/bitwize-music/skills/sheet-music-publisher/SKILL.md | y | --- |
| vendor/bitwize-music/skills/sheet-music-publisher/REQUIREMENTS.md | y | # Sheet Music Publisher - Software Requirements |
| vendor/bitwize-music/skills/sheet-music-publisher/publishing-guide.md | y | # Sheet Music Distribution Guide |
| vendor/bitwize-music/skills/sheet-music-publisher/musescore-reference.md | y | # MuseScore Polish Reference |
| vendor/bitwize-music/skills/sheet-music-publisher/workflow-detail.md | y | # Sheet Music Publisher - Workflow Detail |
| vendor/bitwize-music/skills/next-step/SKILL.md | y | --- |
| vendor/bitwize-music/skills/help/SKILL.md | y | --- |
| vendor/bitwize-music/skills/help/SKILL_GLOSSARY.md | y | # Skill Glossary |
| vendor/bitwize-music/skills/genre-creator/SKILL.md | y | --- |
| vendor/bitwize-music/skills/pre-generation-check/SKILL.md | y | --- |
| vendor/bitwize-music/skills/import-audio/SKILL.md | y | --- |
| vendor/bitwize-music/skills/session-start/SKILL.md | y | --- |
| vendor/bitwize-music/skills/import-art/SKILL.md | y | --- |
| vendor/bitwize-music/skills/validate-album/SKILL.md | y | --- |
| vendor/bitwize-music/skills/configure/SETTINGS_REFERENCE.md | y | # Configure Skill - Settings Reference |
| vendor/bitwize-music/skills/configure/SKILL.md | y | --- |
| vendor/bitwize-music/skills/skill-model-updater/SKILL.md | y | --- |
| vendor/bitwize-music/skills/resume/SKILL.md | y | --- |
| vendor/bitwize-music/skills/setup/SKILL.md | y | --- |
| vendor/bitwize-music/skills/researchers-gov/AGENCY_SOURCES.md | y | # Government Agency Sources Guide |
| vendor/bitwize-music/skills/researchers-gov/SKILL.md | y | --- |
| vendor/bitwize-music/skills/researchers-tech/PROJECT_RESEARCH.md | y | # Tech Project Research Guide |
| vendor/bitwize-music/skills/researchers-tech/SKILL.md | y | --- |
| vendor/bitwize-music/skills/explicit-checker/SKILL.md | y | --- |
| vendor/bitwize-music/skills/researchers-biographical/INTERVIEW_SOURCES.md | y | # Interview and Biographical Sources Guide |
| vendor/bitwize-music/skills/researchers-biographical/SKILL.md | y | --- |
| vendor/bitwize-music/skills/tutorial/phases.md | y | # The 7 Planning Phases |
| vendor/bitwize-music/skills/tutorial/SKILL.md | y | --- |
| vendor/bitwize-music/skills/researchers-historical/ARCHIVE_SOURCES.md | y | # Historical Archive Sources Guide |
| vendor/bitwize-music/skills/researchers-historical/SKILL.md | y | --- |
| vendor/bitwize-music/skills/lyric-reviewer/checklist-reference.md | y | # 14-Point Checklist Reference |
| vendor/bitwize-music/skills/lyric-reviewer/SKILL.md | y | --- |
| vendor/bitwize-music/skills/album-conceptualizer/album-types.md | y | # Album Types Reference |
| vendor/bitwize-music/skills/album-conceptualizer/SKILL.md | y | --- |
| vendor/bitwize-music/skills/promo-reviewer/SKILL.md | y | --- |
| vendor/bitwize-music/skills/promo-reviewer/platform-rules.md | y | # Platform Rules Reference |
| vendor/bitwize-music/skills/promote-idea/SKILL.md | y | --- |
| vendor/bitwize-music/skills/lyric-refiner/SKILL.md | y | --- |
| vendor/bitwize-music/skills/import-track/SKILL.md | y | --- |
| vendor/bitwize-music/skills/lyric-writer/SKILL.md | y | --- |
| vendor/bitwize-music/skills/lyric-writer/examples.md | y | # Lyric Writer Examples |
| vendor/bitwize-music/skills/lyric-writer/documentary-standards.md | y | # Documentary & True Crime Legal Standards |
| vendor/bitwize-music/skills/lyric-writer/craft-reference.md | y | # Lyric Writer Craft Reference |
| vendor/bitwize-music/skills/researchers-primary-source/SKILL.md | y | --- |
| vendor/bitwize-music/skills/researchers-primary-source/DIRECT_SOURCES.md | y | # Direct Source Research Guide |
| vendor/bitwize-music/skills/researchers-verifier/checklists.md | y | # Verification Checklists |
| vendor/bitwize-music/skills/researchers-verifier/patterns.md | y | # Common Verification Patterns |
| vendor/bitwize-music/skills/researchers-verifier/SKILL.md | y | --- |
| vendor/bitwize-music/skills/researchers-verifier/VERIFICATION_CHECKLIST.md | y | # Verification Methodology Guide |
| vendor/bitwize-music/skills/verify-sources/SKILL.md | y | --- |
| vendor/bitwize-music/skills/researchers-financial/SEC_FILING_GUIDE.md | y | # SEC Filing Guide |
| vendor/bitwize-music/skills/researchers-financial/SKILL.md | y | --- |
| vendor/bitwize-music/skills/researchers-security/CVE_RESEARCH.md | y | # CVE and Security Research Guide |
| vendor/bitwize-music/skills/researchers-security/SKILL.md | y | --- |
| vendor/bitwize-music/skills/health-check/SKILL.md | y | --- |
| vendor/bitwize-music/skills/album-art-director/album-types.md | y | # Album Types & Visual Approaches |
| vendor/bitwize-music/skills/album-art-director/SKILL.md | y | --- |
| vendor/bitwize-music/skills/album-art-director/visual-styles.md | y | # Visual Styles & References |
| vendor/bitwize-music/skills/album-art-director/prompt-examples.md | y | # AI Art Prompt Examples |
| vendor/bitwize-music/skills/rename/SKILL.md | y | --- |
| vendor/bitwize-music/skills/release-director/platform-guides.md | y | # Platform Upload Guides |
| vendor/bitwize-music/skills/release-director/SKILL.md | y | --- |
| vendor/bitwize-music/tools/promotion/generate_all_promos.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/promotion/generate_album_sampler.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/promotion/generate_promo_video.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/database/__init__.py | y | Binary or unreadable file |
| vendor/bitwize-music/tools/database/schema.sql | y | Binary or unreadable file |
| vendor/bitwize-music/tools/database/connection.py | y | """PostgreSQL database connection helper for bitwize-music tools.""" |
| vendor/bitwize-music/tools/database/README.md | y | # Database Tools |
| vendor/bitwize-music/tools/database/migrations/001_initial_schema.sql | y | Binary or unreadable file |
| vendor/bitwize-music/tools/n8n/n8n-auto-post-twitter.json | y | { |
| vendor/bitwize-music/tools/n8n/README.md | y | # n8n Workflows |
| vendor/bitwize-music/tools/mixing/excitation.py | y | """Harmonic excitation: generate synthetic upper harmonics to add brightness |
| vendor/bitwize-music/tools/mixing/__init__.py | y | Binary or unreadable file |
| vendor/bitwize-music/tools/mixing/mix-presets.yaml | y | # Mix Polish Presets — Per-Stem Processing Settings |
| vendor/bitwize-music/tools/mixing/mix_tracks.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/sheet-music/create_songbook.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/sheet-music/prepare_singles.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/sheet-music/transcribe.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/sheet-music/README.md | y | # Sheet Music Tools |
| vendor/bitwize-music/tools/cloud/upload_to_cloud.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/mastering/archival.py | y | """Archival-dir helpers for the mastering pipeline (#290 phase 4). |
| vendor/bitwize-music/tools/mastering/ceiling_guard.py | y | """Album-ceiling guard for the mastering pipeline (#290 phase 5, step 8). |
| vendor/bitwize-music/tools/mastering/fix_dynamic_track.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/mastering/metadata.py | y | """ID3v2.4 metadata embedding for mastered WAV delivery files (#290). |
| vendor/bitwize-music/tools/mastering/mono_fold_report.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/mastering/mono_fold.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/mastering/signature_persistence.py | y | """Persist and load ``ALBUM_SIGNATURE.yaml`` (#290 phase 4). |
| vendor/bitwize-music/tools/mastering/analyze_tracks.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/mastering/config.py | y | """Config loader for the mastering pipeline. |
| vendor/bitwize-music/tools/mastering/album_signature.py | y | """Album signature aggregation and anchor-delta computation (#290 phase 3a). |
| vendor/bitwize-music/tools/mastering/layout.py | y | """Album-layout metadata emitter for the mastering pipeline |
| vendor/bitwize-music/tools/mastering/anchor_selector.py | y | """Album-mastering anchor selector (#290 pipeline step 2). |
| vendor/bitwize-music/tools/mastering/reference_master.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/mastering/genre-presets.yaml | y | # Genre-Specific Mastering Presets |
| vendor/bitwize-music/tools/mastering/master_tracks.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/mastering/coherence.py | y | """Album coherence classification + correction planning (#290 phase 3b). |
| vendor/bitwize-music/tools/mastering/codec_preview.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/mastering/adm_validation.py | y | """ADM (Apple Digital Masters) inter-sample clip validation (#290 step 9). |
| vendor/bitwize-music/tools/mastering/qc_tracks.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/shared/progress.py | y | """Progress indicators for long-running operations.""" |
| vendor/bitwize-music/tools/shared/logging_config.py | y | """Logging configuration for bitwize-music tools.""" |
| vendor/bitwize-music/tools/shared/__init__.py | y | # Shared utilities for bitwize-music tools |
| vendor/bitwize-music/tools/shared/text_utils.py | y | """Shared text utilities for track naming and formatting.""" |
| vendor/bitwize-music/tools/shared/fonts.py | y | """System font discovery for video generation.""" |
| vendor/bitwize-music/tools/shared/config.py | y | """Configuration loading and override validation for bitwize-music tools.""" |
| vendor/bitwize-music/tools/shared/colors.py | y | """ANSI color utilities for terminal output.""" |
| vendor/bitwize-music/tools/shared/paths.py | y | """Path resolver utility for bitwize-music tools. |
| vendor/bitwize-music/tools/shared/media_utils.py | y | """Shared media utilities for promotion video and album sampler generation. |
| vendor/bitwize-music/tools/validate_help_completeness.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/userscripts/suno-autofill.user.js | y | Binary or unreadable file |
| vendor/bitwize-music/tools/userscripts/README.md | y | # Userscripts |
| vendor/bitwize-music/tools/state/__main__.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/state/parsers.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/state/__init__.py | y | # State cache tools for claude-ai-music-skills |
| vendor/bitwize-music/tools/state/indexer.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tools/state/README.md | y | # State Cache Indexer |
| vendor/bitwize-music/ruff.toml | y | Binary or unreadable file |
| vendor/bitwize-music/README.md | y | # Claude AI Music Skills |
| vendor/bitwize-music/tests/fixtures/albums/coherence/__init__.py | y | """Synthetic multi-track album fixtures for coherence testing (#290). |
| vendor/bitwize-music/tests/fixtures/albums/__init__.py | y | Binary or unreadable file |
| vendor/bitwize-music/tests/fixtures/adm/__init__.py | y | """Synthetic ADM test fixtures — PCM-clean and near-clip WAVs (#290 step 9). |
| vendor/bitwize-music/tests/fixtures/__init__.py | y | Binary or unreadable file |
| vendor/bitwize-music/tests/fixtures/audio/__init__.py | y | """Realistic synthetic audio fixture generators for testing. |
| vendor/bitwize-music/tests/fixtures/README.md | y | # Test Fixtures |
| vendor/bitwize-music/tests/conftest.py | y | """Shared pytest fixtures for plugin and unit tests.""" |
| vendor/bitwize-music/tests/__init__.py | y | Binary or unreadable file |
| vendor/bitwize-music/tests/unit/promotion/test_generate_album_sampler.py | y | """Tests for tools/promotion/generate_album_sampler.py.""" |
| vendor/bitwize-music/tests/unit/promotion/test_generate_promo_video.py | y | """Tests for tools/promotion/generate_promo_video.py.""" |
| vendor/bitwize-music/tests/unit/promotion/test_generate_all_promos.py | y | """Tests for tools/promotion/generate_all_promos.py.""" |
| vendor/bitwize-music/tests/unit/promotion/__init__.py | y | Binary or unreadable file |
| vendor/bitwize-music/tests/unit/sheet_music/test_prepare_singles.py | y | """Tests for tools/sheet-music/prepare_singles.py.""" |
| vendor/bitwize-music/tests/unit/sheet_music/test_transcribe.py | y | """Tests for tools/sheet-music/transcribe.py.""" |
| vendor/bitwize-music/tests/unit/sheet_music/test_create_songbook.py | y | """Tests for tools/sheet-music/create_songbook.py utility functions.""" |
| vendor/bitwize-music/tests/unit/sheet_music/__init__.py | y | Binary or unreadable file |
| vendor/bitwize-music/tests/unit/handlers/test_shared_helpers.py | y | """Tests for handlers/_shared.py helpers.""" |
| vendor/bitwize-music/tests/unit/handlers/__init__.py | y | Binary or unreadable file |
| vendor/bitwize-music/tests/unit/mixing/test_polish_analyzer_overrides.py | y | """Unit tests for _get_stem_settings analyzer_rec merge behavior (#336).""" |
| vendor/bitwize-music/tests/unit/mixing/test_excitation.py | y | """Unit tests for the harmonic excitation DSP primitive.""" |
| vendor/bitwize-music/tests/unit/mixing/test_mix_tracks.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/mixing/test_polish_adm_aware_excitation.py | y | """End-to-end tests: analyzer recommends excitation_db on dark stems |
| vendor/bitwize-music/tests/unit/mixing/__init__.py | y | Binary or unreadable file |
| vendor/bitwize-music/tests/unit/mixing/test_analyze_mix_issues.py | y | """Unit tests for analyze_mix_issues dark-track condition + threshold resolution.""" |
| vendor/bitwize-music/tests/unit/mixing/test_detector_parity.py | y | """Analyzer / processor click detector parity (#323 follow-up). |
| vendor/bitwize-music/tests/unit/mixing/test_polish_peak_invariant.py | y | """Per-stem polish must not increase peak amplitude (#323 follow-up). |
| vendor/bitwize-music/tests/unit/mixing/test_polish_audio_stems.py | y | """Tests for per-stem polished WAV output from mix_track_stems (#290).""" |
| vendor/bitwize-music/tests/unit/mixing/test_analyzer_canonical_stem_keys.py | y | """analyze_mix_issues must key per-stem analysis by canonical STEM_NAMES |
| vendor/bitwize-music/tests/unit/cloud/__init__.py | y | Binary or unreadable file |
| vendor/bitwize-music/tests/unit/cloud/test_upload_to_cloud.py | y | """Tests for tools/cloud/upload_to_cloud.py.""" |
| vendor/bitwize-music/tests/unit/mastering/test_master_album_recovery_delivery_format.py | y | """Recovery path must write at ctx.targets['output_sample_rate'], not |
| vendor/bitwize-music/tests/unit/mastering/test_master_album_coherence_stages.py | y | """Unit tests for Stage 5.1 (coherence check) and Stage 5.2 (coherence correct) |
| vendor/bitwize-music/tests/unit/mastering/test_signature_metrics.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/mastering/test_post_master_spectral_regression.py | y | """Post-QC emits tinniness-regression WARN when mastering pushes |
| vendor/bitwize-music/tests/unit/mastering/test_album_stages_ctx.py | y | """Tests for MasterAlbumCtx dataclass and _build_notices (#290 D5).""" |
| vendor/bitwize-music/tests/unit/mastering/test_fix_dynamic_convergence.py | y | """Unit tests for fix_dynamic's iterative LUFS convergence.""" |
| vendor/bitwize-music/tests/unit/mastering/test_integration_realistic_audio.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/mastering/test_analyze_tracks_is_dark.py | y | """analyze_track must return is_dark=True when high_mid band energy is |
| vendor/bitwize-music/tests/unit/mastering/test_reference_master.py | y | """Tests for tools/mastering/reference_master.py.""" |
| vendor/bitwize-music/tests/unit/mastering/test_post_qc_genre.py | y | """Post-QC must pass the album genre through to qc_track. |
| vendor/bitwize-music/tests/unit/mastering/test_mono_fold_report.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/mastering/test_master_album_freeze_flags.py | y | """Tests for --freeze-signature / --new-anchor MCP params (#290 phase 4).""" |
| vendor/bitwize-music/tests/unit/mastering/test_master_audio_config_wiring.py | y | """Integration test: master_audio / master_album consume mastering config. |
| vendor/bitwize-music/tests/unit/mastering/test_master_tracks.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/mastering/test_album_coherence_handlers.py | y | """Integration tests for album_coherence_check / album_coherence_correct (#290 phase 3b).""" |
| vendor/bitwize-music/tests/unit/mastering/test_pipeline.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/mastering/test_coherence_presets.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/mastering/test_mono_fold.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/mastering/test_signature_metrics_snapshot.py | y | """Snapshot tests: STL-95, low-RMS, short_term_range on standard fixtures (regression catch, #290). |
| vendor/bitwize-music/tests/unit/mastering/test_fix_dynamic.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/mastering/test_master_album_adm_flow.py | y | """Integration tests for Stage 5.5 (ADM validation) inside master_album (#290 step 9).""" |
| vendor/bitwize-music/tests/unit/mastering/__init__.py | y | Binary or unreadable file |
| vendor/bitwize-music/tests/unit/mastering/test_archival_prune.py | y | """Tests for tools/mastering/archival.py prune helper (#290 phase 4, PR #304 A5).""" |
| vendor/bitwize-music/tests/unit/mastering/test_signature_persistence.py | y | """Tests for tools/mastering/signature_persistence.py (#290 phase 4).""" |
| vendor/bitwize-music/tests/unit/mastering/test_master_album_selective_remaster.py | y | """When ctx.remaster_filenames is a non-empty set, _stage_mastering |
| vendor/bitwize-music/tests/unit/mastering/test_master_album_signature_flow.py | y | """Integration tests for signature persistence inside master_album (#290 phase 4).""" |
| vendor/bitwize-music/tests/unit/mastering/test_master_album_adm_retry.py | y | """Tests for ADM retry loop (max 2 cycles, ceiling tightening) in master_album (#290 step 9).""" |
| vendor/bitwize-music/tests/unit/mastering/test_build_effective_preset.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/mastering/test_mastering_config.py | y | """Unit tests for tools/mastering/config.py.""" |
| vendor/bitwize-music/tests/unit/mastering/test_master_album_layout_flow.py | y | """Integration tests for Stage 6.7 (LAYOUT.md emitter) inside |
| vendor/bitwize-music/tests/unit/mastering/test_notices_on_failure.py | y | """Test that notices appear in early-exit failure JSON (A4 — #290).""" |
| vendor/bitwize-music/tests/unit/mastering/test_ceiling_guard.py | y | """Tests for tools/mastering/ceiling_guard.py (#290 phase 5, step 8).""" |
| vendor/bitwize-music/tests/unit/mastering/test_master_album_dark_track_adm.py | y | """When a dark track clips ADM, it must NOT be tightened — instead it |
| vendor/bitwize-music/tests/unit/mastering/test_adm_validation.py | y | """Tests for tools/mastering/adm_validation.py (#290 step 9).""" |
| vendor/bitwize-music/tests/unit/mastering/test_layout_preservation.py | y | """Tests for LAYOUT.md hand-edit preservation (#290 phase 6, step 7).""" |
| vendor/bitwize-music/tests/unit/mastering/test_album_signature.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/mastering/test_master_album_lra_floor.py | y | """Tests for LRA floor hard-fail in _stage_post_qc (#290 step 10).""" |
| vendor/bitwize-music/tests/unit/mastering/test_archival_output.py | y | """Tests for master_album's archival output path. |
| vendor/bitwize-music/tests/unit/mastering/test_master_album_adm_off_end_to_end.py | y | """Regression: master_album runs end-to-end with ADM off. Explicitly |
| vendor/bitwize-music/tests/unit/mastering/test_tilt_eq.py | y | """Unit tests for apply_tilt_eq (#290 step 6 tilt-EQ coherence correction).""" |
| vendor/bitwize-music/tests/unit/mastering/test_qc_tracks.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/mastering/test_master_album_progress_log.py | y | """MASTERING_PROGRESS.log sidecar emitted during master_album runs. |
| vendor/bitwize-music/tests/unit/mastering/test_master_album_per_track_ceiling.py | y | """Per-track ADM ceiling helper behaves like the legacy closure. |
| vendor/bitwize-music/tests/unit/mastering/test_coherence.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/mastering/test_codec_preview.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/mastering/test_metadata.py | y | """Tests for tools/mastering/metadata.py (#290 metadata embedding).""" |
| vendor/bitwize-music/tests/unit/mastering/test_stage_status_update.py | y | """Unit tests for _stage_status_update — master_album track/album status promotion. |
| vendor/bitwize-music/tests/unit/mastering/test_anchor_selector.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/mastering/test_measure_album_signature_handler.py | y | """Integration tests for the measure_album_signature MCP handler (#290 phase 3a).""" |
| vendor/bitwize-music/tests/unit/mastering/test_analyze_tracks.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/mastering/test_master_album_verification_warn_fallback.py | y | """Verification must warn-fallback (not halt) when recovery was attempted |
| vendor/bitwize-music/tests/unit/mastering/test_layout.py | y | """Tests for tools/mastering/layout.py (#290 phase 5, step 7).""" |
| vendor/bitwize-music/tests/unit/mastering/test_master_album_ceiling_guard_flow.py | y | """Integration tests for Stage 5.4 (album-ceiling guard) inside |
| vendor/bitwize-music/tests/unit/mastering/test_master_album_config_wiring.py | y | """Integration tests: master_album consumes mastering config for delivery. |
| vendor/bitwize-music/tests/unit/mastering/test_config_album_overrides.py | y | """build_delivery_targets must apply the per-album override rule for |
| vendor/bitwize-music/tests/unit/mastering/test_master_album_metadata_flow.py | y | """Integration tests for Stage 6.6 (metadata embedding) in master_album (#290).""" |
| vendor/bitwize-music/tests/unit/mastering/test_prune_archival.py | y | """Tests for the prune_archival MCP tool.""" |
| vendor/bitwize-music/tests/unit/shared/test_progress.py | y | """Tests for tools.shared.progress module.""" |
| vendor/bitwize-music/tests/unit/shared/test_colors.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/shared/test_debug_logging.py | y | """Tests for configure_file_logging() in tools.shared.logging_config.""" |
| vendor/bitwize-music/tests/unit/shared/__init__.py | y | Binary or unreadable file |
| vendor/bitwize-music/tests/unit/shared/test_fonts.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/shared/test_media_utils.py | y | """Tests for tools/shared/media_utils.py.""" |
| vendor/bitwize-music/tests/unit/shared/test_paths.py | y | """Unit tests for the path resolver utility.""" |
| vendor/bitwize-music/tests/unit/shared/test_config.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/shared/test_logging_config.py | y | """Tests for tools.shared.logging_config module.""" |
| vendor/bitwize-music/tests/unit/__init__.py | y | Binary or unreadable file |
| vendor/bitwize-music/tests/unit/state/fixtures/album-readme.md | y | --- |
| vendor/bitwize-music/tests/unit/state/fixtures/ideas.md | y | # Album Ideas |
| vendor/bitwize-music/tests/unit/state/fixtures/track-file.md | y | # Boot Sequence |
| vendor/bitwize-music/tests/unit/state/fixtures/track-not-started.md | y | # Kernel Panic |
| vendor/bitwize-music/tests/unit/state/test_parsers_layout.py | y | """Tests for album-README layout frontmatter parsing (#290 phase 5).""" |
| vendor/bitwize-music/tests/unit/state/test_state_recovery.py | y | """Tests for corrupted state.json recovery.""" |
| vendor/bitwize-music/tests/unit/state/test_server_qc.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/state/test_server_integration.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/state/test_atomic_write.py | y | """Tests for atomic file write utility.""" |
| vendor/bitwize-music/tests/unit/state/test_server.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/state/test_indexer.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/state/test_lock_backoff.py | y | """Tests for lock acquisition with exponential backoff.""" |
| vendor/bitwize-music/tests/unit/state/test_handlers_promote_idea.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/state/test_parsers.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/state/__init__.py | y | Binary or unreadable file |
| vendor/bitwize-music/tests/unit/state/test_server_features.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/state/test_handlers_streaming.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/state/test_server_database.py | y | """Tests for database handler pagination (db_list_tweets, db_search_tweets).""" |
| vendor/bitwize-music/tests/unit/state/test_silent_exceptions.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/state/test_server_lyrics.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/state/test_server_mastering_samples.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/state/test_handlers_gates.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/state/test_handlers_mixing.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/state/test_handlers_rename.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/unit/state/test_handlers_album_ops.py | y | #!/usr/bin/env python3 |
| vendor/bitwize-music/tests/plugin/test_consistency.py | y | """Tests for cross-reference consistency: versions, skill counts, model tiers, .gitignore.""" |
| vendor/bitwize-music/tests/plugin/test_skills.py | y | """Tests for skill definitions: frontmatter, model refs, prerequisites, sections.""" |
| vendor/bitwize-music/tests/plugin/test_state.py | y | """Tests for state cache tool files and structure.""" |
| vendor/bitwize-music/tests/plugin/test_templates.py | y | """Tests for template files: existence, structure, references.""" |
| vendor/bitwize-music/tests/plugin/test_references.py | y | """Tests for reference documentation: Suno refs, mastering docs, CLAUDE.md refs.""" |
| vendor/bitwize-music/tests/plugin/__init__.py | y | Binary or unreadable file |
| vendor/bitwize-music/tests/plugin/test_terminology.py | y | """Tests for consistent terminology: deprecated terms, path variables, hardcoded paths.""" |
| vendor/bitwize-music/tests/plugin/test_integration.py | y | """Tests for cross-skill integration: prerequisite chains, workflow consistency.""" |
| vendor/bitwize-music/tests/plugin/test_links.py | y | """Tests for internal markdown link validation.""" |
| vendor/bitwize-music/tests/plugin/test_migrations.py | y | """Tests for migration file format and consistency.""" |
| vendor/bitwize-music/tests/plugin/test_config.py | y | """Tests for configuration files: config.example.yaml structure and docs.""" |
| vendor/bitwize-music/tests/plugin/test_genres.py | y | """Tests for genre directory structure vs INDEX.md and genre-list.md.""" |
| vendor/bitwize-music/migrations/0.44.0.md | y | --- |
| vendor/bitwize-music/migrations/0.90.0.md | y | --- |
| vendor/bitwize-music/migrations/0.91.0.md | y | --- |
| vendor/bitwize-music/migrations/0.43.0.md | y | --- |
| vendor/bitwize-music/migrations/0.59.0.md | y | --- |
| vendor/bitwize-music/migrations/0.40.0.md | y | --- |
| vendor/bitwize-music/migrations/README.md | y | # Plugin Migration Notes |
| vendor/bitwize-music/genres/qawwali/README.md | y | # Qawwali |
| vendor/bitwize-music/genres/afroswing/README.md | y | # Afroswing |
| vendor/bitwize-music/genres/lovers-rock/README.md | y | # Lovers Rock |
| vendor/bitwize-music/genres/fuji/README.md | y | # Fuji |
| vendor/bitwize-music/genres/jazz/README.md | y | # Jazz |
| vendor/bitwize-music/genres/jangle-pop/README.md | y | # Jangle Pop |
| vendor/bitwize-music/genres/big-band/README.md | y | # Big Band |
| vendor/bitwize-music/genres/p-funk/README.md | y | # P-Funk |
| vendor/bitwize-music/genres/synthwave/artists/the-midnight.md | y | # The Midnight — Deep Dive |
| vendor/bitwize-music/genres/synthwave/artists/timecop1983.md | y | # Timecop1983 — Deep Dive |
| vendor/bitwize-music/genres/synthwave/artists/fm-84.md | y | # FM-84 — Deep Dive |
| vendor/bitwize-music/genres/synthwave/artists/gunship.md | y | # GUNSHIP — Deep Dive |
| vendor/bitwize-music/genres/synthwave/artists/INDEX.md | y | # Synthwave — Artist References |
| vendor/bitwize-music/genres/synthwave/README.md | y | # Synthwave |
| vendor/bitwize-music/genres/space-disco/README.md | y | # Space Disco |
| vendor/bitwize-music/genres/reggaeton/README.md | y | # Reggaeton |
| vendor/bitwize-music/genres/benga/README.md | y | # Benga |
| vendor/bitwize-music/genres/post-punk/README.md | y | # Post-Punk |
| vendor/bitwize-music/genres/lo-fi/README.md | y | # Lo-Fi |
| vendor/bitwize-music/genres/witch-house/README.md | y | # Witch House |
| vendor/bitwize-music/genres/bakersfield-sound/README.md | y | # Bakersfield Sound |
| vendor/bitwize-music/genres/chanson/README.md | y | # Chanson |
| vendor/bitwize-music/genres/smooth-jazz/README.md | y | # Smooth Jazz |
| vendor/bitwize-music/genres/bounce/README.md | y | # Bounce |
| vendor/bitwize-music/genres/grime/README.md | y | # Grime |
| vendor/bitwize-music/genres/roots-reggae/README.md | y | # Roots Reggae |
| vendor/bitwize-music/genres/ranchera/README.md | y | # Ranchera |
| vendor/bitwize-music/genres/future-bass/README.md | y | # Future Bass |
| vendor/bitwize-music/genres/cantopop/README.md | y | # Cantopop |
| vendor/bitwize-music/genres/death-metal/README.md | y | # Death Metal |
| vendor/bitwize-music/genres/stoner-rock/README.md | y | # Stoner Rock |
| vendor/bitwize-music/genres/power-metal/README.md | y | # Power Metal |
| vendor/bitwize-music/genres/riddim/README.md | y | # Riddim |
| vendor/bitwize-music/genres/bro-country/README.md | y | # Bro-Country |
| vendor/bitwize-music/genres/post-dubstep/README.md | y | # Post-Dubstep |
| vendor/bitwize-music/genres/psychobilly/README.md | y | # Psychobilly |
| vendor/bitwize-music/genres/flamenco/README.md | y | # Flamenco |
| vendor/bitwize-music/genres/chimurenga/README.md | y | # Chimurenga |
| vendor/bitwize-music/genres/horrorcore/README.md | y | # Horrorcore |
| vendor/bitwize-music/genres/djent/README.md | y | # Djent |
| vendor/bitwize-music/genres/quiet-storm/README.md | y | # Quiet Storm |
| vendor/bitwize-music/genres/thrash-metal/README.md | y | # Thrash Metal |
| vendor/bitwize-music/genres/ebm/README.md | y | # EBM |
| vendor/bitwize-music/genres/dembow/README.md | y | # Dembow |
| vendor/bitwize-music/genres/art-pop/README.md | y | # Art Pop |
| vendor/bitwize-music/genres/vocaloid/README.md | y | # Vocaloid |
| vendor/bitwize-music/genres/electro/README.md | y | # Electro |
| vendor/bitwize-music/genres/carnatic/README.md | y | # Carnatic |
| vendor/bitwize-music/genres/uk-funky/README.md | y | # UK Funky |
| vendor/bitwize-music/genres/latin-jazz/README.md | y | # Latin Jazz |
| vendor/bitwize-music/genres/laiko/README.md | y | # Laiko |
| vendor/bitwize-music/genres/classical/README.md | y | # Classical |
| vendor/bitwize-music/genres/britpop/README.md | y | # Britpop |
| vendor/bitwize-music/genres/funk/README.md | y | # Funk |
| vendor/bitwize-music/genres/disco/README.md | y | # Disco |
| vendor/bitwize-music/genres/turbo-folk/README.md | y | # Turbo-Folk |
| vendor/bitwize-music/genres/cabaret/README.md | y | # Cabaret |
| vendor/bitwize-music/genres/trap-soul/README.md | y | # Trap Soul |
| vendor/bitwize-music/genres/reggae/README.md | y | # Reggae |
| vendor/bitwize-music/genres/choir/README.md | y | # Choir |
| vendor/bitwize-music/genres/electroswing/README.md | y | # Electroswing |
| vendor/bitwize-music/genres/bebop/README.md | y | # Bebop |
| vendor/bitwize-music/genres/boogaloo/README.md | y | # Boogaloo |
| vendor/bitwize-music/genres/edm/README.md | y | # Electronic Dance Music (EDM) |
| vendor/bitwize-music/genres/guaracha/README.md | y | # Guaracha |
| vendor/bitwize-music/genres/music-hall/README.md | y | # Music Hall |
| vendor/bitwize-music/genres/garage-rock/README.md | y | # Garage Rock |
| vendor/bitwize-music/genres/hardstyle/README.md | y | # Hardstyle |
| vendor/bitwize-music/genres/crust-punk/README.md | y | # Crust Punk |
| vendor/bitwize-music/genres/deep-techno/README.md | y | # Deep Techno |
| vendor/bitwize-music/genres/middle-eastern-pop/README.md | y | # Middle Eastern Pop |
| vendor/bitwize-music/genres/nu-jazz/README.md | y | # Nu Jazz |
| vendor/bitwize-music/genres/surf-rock/README.md | y | # Surf Rock |
| vendor/bitwize-music/genres/bass-house/README.md | y | # Bass House |
| vendor/bitwize-music/genres/crossover-thrash/README.md | y | # Crossover Thrash |
| vendor/bitwize-music/genres/vallenato/README.md | y | # Vallenato |
| vendor/bitwize-music/genres/vocal-trance/README.md | y | # Vocal Trance |
| vendor/bitwize-music/genres/g-funk/README.md | y | # G-Funk |
| vendor/bitwize-music/genres/visual-kei/README.md | y | # Visual Kei |
| vendor/bitwize-music/genres/hardwave/README.md | y | # Hardwave |
| vendor/bitwize-music/genres/latin-trap/README.md | y | # Latin Trap |
| vendor/bitwize-music/genres/dark-jazz/README.md | y | # Dark Jazz |
| vendor/bitwize-music/genres/motown/README.md | y | # Motown |
| vendor/bitwize-music/genres/celtic/README.md | y | # Celtic |
| vendor/bitwize-music/genres/mumble-rap/README.md | y | # Mumble Rap |
| vendor/bitwize-music/genres/rai/README.md | y | # Rai |
| vendor/bitwize-music/genres/glitch-hop/README.md | y | # Glitch Hop |
| vendor/bitwize-music/genres/kuduro/README.md | y | # Kuduro |
| vendor/bitwize-music/genres/hyperpop/README.md | y | # HYPERPOP |
| vendor/bitwize-music/genres/city-pop/README.md | y | # City Pop |
| vendor/bitwize-music/genres/merengue/README.md | y | # Merengue |
| vendor/bitwize-music/genres/indie-rock/artists/rilo-kiley.md | y | # Rilo Kiley — Deep Dive |
| vendor/bitwize-music/genres/indie-rock/artists/INDEX.md | y | # Indie Rock — Artist References |
| vendor/bitwize-music/genres/indie-rock/README.md | y | # Indie Rock |
| vendor/bitwize-music/genres/childrens-music/README.md | y | # Children's Music |
| vendor/bitwize-music/genres/swing/README.md | y | # Swing / Neo-Swing |
| vendor/bitwize-music/genres/darksynth/README.md | y | # Darksynth |
| vendor/bitwize-music/genres/acid-jazz/README.md | y | # Acid Jazz |
| vendor/bitwize-music/genres/emo/README.md | y | # Emo |
| vendor/bitwize-music/genres/dark-electro/README.md | y | # Dark Electro |
| vendor/bitwize-music/genres/hip-hop/artists/brock-berrigan.md | y | # Brock Berrigan — Deep Dive |
| vendor/bitwize-music/genres/hip-hop/artists/immortal-technique.md | y | # Immortal Technique — Artist Deep Dive |
| vendor/bitwize-music/genres/hip-hop/artists/run-the-jewels.md | y | # Run the Jewels — Deep Dive |
| vendor/bitwize-music/genres/hip-hop/artists/INDEX.md | y | # Hip-Hop — Artist References |
| vendor/bitwize-music/genres/hip-hop/artists/kendrick-lamar.md | y | # Kendrick Lamar — Deep Dive |
| vendor/bitwize-music/genres/hip-hop/README.md | y | # Hip-Hop |
| vendor/bitwize-music/genres/morna/README.md | y | # Morna |
| vendor/bitwize-music/genres/pc-music/README.md | y | # PC Music |
| vendor/bitwize-music/genres/piano-blues/README.md | y | # Piano Blues |
| vendor/bitwize-music/genres/thai-pop/README.md | y | # Thai Pop |
| vendor/bitwize-music/genres/cowpunk/README.md | y | # Cowpunk |
| vendor/bitwize-music/genres/emo-rap/README.md | y | # Emo Rap |
| vendor/bitwize-music/genres/doom-metal/README.md | y | # Doom Metal |
| vendor/bitwize-music/genres/mandopop/README.md | y | # Mandopop |
| vendor/bitwize-music/genres/moombahton/README.md | y | # Moombahton |
| vendor/bitwize-music/genres/mbalax/README.md | y | # Mbalax |
| vendor/bitwize-music/genres/industrial/README.md | y | # Industrial |
| vendor/bitwize-music/genres/juju/README.md | y | # Juju |
| vendor/bitwize-music/genres/punk/artists/mest.md | y | # Mest — Deep Dive |
| vendor/bitwize-music/genres/punk/artists/lagwagon.md | y | # Lagwagon — Deep Dive |
| vendor/bitwize-music/genres/punk/artists/masked-intruder.md | y | # Masked Intruder — Deep Dive |
| vendor/bitwize-music/genres/punk/artists/me-first-and-the-gimme-gimmes.md | y | # Me First and the Gimme Gimmes — Deep Dive |
| vendor/bitwize-music/genres/punk/artists/propagandhi.md | y | # Propagandhi — Deep Dive |
| vendor/bitwize-music/genres/punk/artists/blink-182.md | y | # Blink-182 — Deep Dive |
| vendor/bitwize-music/genres/punk/artists/the-offspring.md | y | # The Offspring — Deep Dive |
| vendor/bitwize-music/genres/punk/artists/bad-religion.md | y | # Bad Religion — Deep Dive |
| vendor/bitwize-music/genres/punk/artists/INDEX.md | y | # Punk — Artist References |
| vendor/bitwize-music/genres/punk/artists/green-day.md | y | # Green Day — Deep Dive |
| vendor/bitwize-music/genres/punk/artists/descendents.md | y | # Descendents — Deep Dive |
| vendor/bitwize-music/genres/punk/artists/nofx.md | y | # NOFX — Deep Dive |
| vendor/bitwize-music/genres/punk/artists/rancid.md | y | # Rancid — Deep Dive |
| vendor/bitwize-music/genres/punk/README.md | y | # Punk |
| vendor/bitwize-music/genres/noise-pop/README.md | y | # Noise Pop |
| vendor/bitwize-music/genres/afropop/README.md | y | # Afropop |
| vendor/bitwize-music/genres/go-go/README.md | y | # Go-Go |
| vendor/bitwize-music/genres/zydeco/README.md | y | # Zydeco |
| vendor/bitwize-music/genres/complextro/README.md | y | # Complextro |
| vendor/bitwize-music/genres/maskandi/README.md | y | # Maskandi |
| vendor/bitwize-music/genres/deathcore/README.md | y | # Deathcore |
| vendor/bitwize-music/genres/deconstructed-club/README.md | y | # Deconstructed Club |
| vendor/bitwize-music/genres/zouk/README.md | y | # Zouk |
| vendor/bitwize-music/genres/isicathamiya/README.md | y | # Isicathamiya |
| vendor/bitwize-music/genres/dance-punk/README.md | y | # Dance-Punk |
| vendor/bitwize-music/genres/post-punk-revival/README.md | y | # Post-Punk Revival |
| vendor/bitwize-music/genres/medieval/README.md | y | # Medieval |
| vendor/bitwize-music/genres/boom-bap/README.md | y | # Boom Bap |
| vendor/bitwize-music/genres/piano-rock/artists/elton-john.md | y | # Elton John — Deep Dive |
| vendor/bitwize-music/genres/piano-rock/artists/INDEX.md | y | # Piano Rock — Artist References |
| vendor/bitwize-music/genres/piano-rock/artists/ben-folds-solo.md | y | # Ben Folds — Solo Career Deep Dive |
| vendor/bitwize-music/genres/piano-rock/artists/billy-joel.md | y | # Billy Joel — Deep Dive |
| vendor/bitwize-music/genres/piano-rock/artists/ben-folds-five.md | y | # Ben Folds Five — Deep Dive |
| vendor/bitwize-music/genres/piano-rock/README.md | y | # Piano Rock |
| vendor/bitwize-music/genres/post-britpop/README.md | y | # Post-Britpop |
| vendor/bitwize-music/genres/gospel/README.md | y | # Gospel |
| vendor/bitwize-music/genres/kayokyoku/README.md | y | # Kayokyoku |
| vendor/bitwize-music/genres/amapiano/README.md | y | # Amapiano |
| vendor/bitwize-music/genres/chicha/README.md | y | # Chicha |
| vendor/bitwize-music/genres/underground-hip-hop/README.md | y | # Underground Hip Hop |
| vendor/bitwize-music/genres/ska-punk/README.md | y | # Ska Punk |
| vendor/bitwize-music/genres/bachata/README.md | y | # Bachata |
| vendor/bitwize-music/genres/nerdcore/README.md | y | # Nerdcore |
| vendor/bitwize-music/genres/pagode/README.md | y | # Pagode |
| vendor/bitwize-music/genres/post-disco/README.md | y | # Post-Disco |
| vendor/bitwize-music/genres/blues/README.md | y | # Blues |
| vendor/bitwize-music/genres/progressive-house/README.md | y | # Progressive House |
| vendor/bitwize-music/genres/dream-pop/README.md | y | # Dream Pop |
| vendor/bitwize-music/genres/sludge-metal/README.md | y | # Sludge Metal |
| vendor/bitwize-music/genres/cool-jazz/README.md | y | # Cool Jazz |
| vendor/bitwize-music/genres/italo-disco/README.md | y | # Italo Disco |
| vendor/bitwize-music/genres/worship/README.md | y | # Worship |
| vendor/bitwize-music/genres/oi/README.md | y | # Oi! |
| vendor/bitwize-music/genres/post-rock/README.md | y | # Post-Rock |
| vendor/bitwize-music/genres/breakcore/README.md | y | # Breakcore |
| vendor/bitwize-music/genres/piano-pop/README.md | y | # Piano Pop |
| vendor/bitwize-music/genres/psychedelic-rock/README.md | y | # Psychedelic Rock |
| vendor/bitwize-music/genres/beatboxing/README.md | y | # Beatboxing |
| vendor/bitwize-music/genres/bongo-flava/README.md | y | # Bongo Flava |
| vendor/bitwize-music/genres/soul-jazz/README.md | y | # Soul Jazz |
| vendor/bitwize-music/genres/drone/README.md | y | # Drone |
| vendor/bitwize-music/genres/contemporary-christian/README.md | y | # Contemporary Christian Music |
| vendor/bitwize-music/genres/abstract-hip-hop/README.md | y | # Abstract Hip-Hop |
| vendor/bitwize-music/genres/kompa/README.md | y | # Kompa |
| vendor/bitwize-music/genres/rockabilly/README.md | y | # Rockabilly |
| vendor/bitwize-music/genres/ragga/README.md | y | # Ragga |
| vendor/bitwize-music/genres/forro/README.md | y | # Forro |
| vendor/bitwize-music/genres/darkwave/README.md | y | # Darkwave |
| vendor/bitwize-music/genres/boogie/README.md | y | # Boogie |
| vendor/bitwize-music/genres/new-age/README.md | y | # New Age |
| vendor/bitwize-music/genres/grindcore/README.md | y | # Grindcore |
| vendor/bitwize-music/genres/ghazal/README.md | y | # Ghazal |
| vendor/bitwize-music/genres/riot-grrrl/README.md | y | # Riot Grrrl |
| vendor/bitwize-music/genres/cumbia/README.md | y | # Cumbia |
| vendor/bitwize-music/genres/delta-blues/README.md | y | # Delta Blues |
| vendor/bitwize-music/genres/punta/README.md | y | # Punta |
| vendor/bitwize-music/genres/polka/README.md | y | # Polka |
| vendor/bitwize-music/genres/screamo/README.md | y | # Screamo |
| vendor/bitwize-music/genres/crunk/README.md | y | # Crunk |
| vendor/bitwize-music/genres/nu-metal/README.md | y | # Nu-Metal |
| vendor/bitwize-music/genres/metal/README.md | y | # Metal |
| vendor/bitwize-music/genres/gabber/README.md | y | # Gabber |
| vendor/bitwize-music/genres/opera/README.md | y | # Opera |
| vendor/bitwize-music/genres/tejano/README.md | y | # Tejano |
| vendor/bitwize-music/genres/sea-shanties/README.md | y | # Sea Shanties |
| vendor/bitwize-music/genres/chamber-pop/README.md | y | # Chamber Pop |
| vendor/bitwize-music/genres/hindustani/README.md | y | # Hindustani |
| vendor/bitwize-music/genres/glitch/README.md | y | # Glitch |
| vendor/bitwize-music/genres/jazz-fusion/README.md | y | # Jazz Fusion |
| vendor/bitwize-music/genres/wave/README.md | y | # Wave |
| vendor/bitwize-music/genres/shoegaze/README.md | y | # Shoegaze |
| vendor/bitwize-music/genres/klezmer/README.md | y | # Klezmer |
| vendor/bitwize-music/genres/folk-metal/README.md | y | # Folk Metal |
| vendor/bitwize-music/genres/gengetone/README.md | y | # Gengetone |
| vendor/bitwize-music/genres/eurodance/README.md | y | # Eurodance |
| vendor/bitwize-music/genres/dark-cabaret/README.md | y | # Dark Cabaret |
| vendor/bitwize-music/genres/future-house/README.md | y | # Future House |
| vendor/bitwize-music/genres/rock/artists/linkin-park.md | y | # Linkin Park — Deep Dive |
| vendor/bitwize-music/genres/rock/artists/hoobastank.md | y | # Hoobastank -- Deep Dive |
| vendor/bitwize-music/genres/rock/artists/polaris.md | y | # Polaris — Deep Dive |
| vendor/bitwize-music/genres/rock/artists/weezer.md | y | # Weezer — Deep Dive |
| vendor/bitwize-music/genres/rock/artists/toto.md | y | # Toto — Deep Dive |
| vendor/bitwize-music/genres/rock/artists/incubus.md | y | # Incubus -- Deep Dive |
| vendor/bitwize-music/genres/rock/artists/INDEX.md | y | # Rock — Artist References |
| vendor/bitwize-music/genres/rock/artists/fountains-of-wayne.md | y | # Fountains of Wayne — Deep Dive |
| vendor/bitwize-music/genres/rock/artists/phil-collins.md | y | # Phil Collins — Deep Dive |
| vendor/bitwize-music/genres/rock/artists/jeff-buckley.md | y | # Jeff Buckley -- Deep Dive |
| vendor/bitwize-music/genres/rock/README.md | y | # Rock |
| vendor/bitwize-music/genres/goa-trance/README.md | y | # Goa Trance |
| vendor/bitwize-music/genres/nightcore/README.md | y | # Nightcore |
| vendor/bitwize-music/genres/bassline/README.md | y | # Bassline |
| vendor/bitwize-music/genres/rebetiko/README.md | y | # Rebetiko |
| vendor/bitwize-music/genres/phonk/README.md | y | # PHONK |
| vendor/bitwize-music/genres/d-beat/README.md | y | # D-Beat |
| vendor/bitwize-music/genres/symphonic-metal/README.md | y | # Symphonic Metal |
| vendor/bitwize-music/genres/corridos-tumbados/README.md | y | # Corridos Tumbados |
| vendor/bitwize-music/genres/mento/README.md | y | # Mento |
| vendor/bitwize-music/genres/chutney/README.md | y | # Chutney |
| vendor/bitwize-music/genres/neo-soul/README.md | y | # Neo-Soul |
| vendor/bitwize-music/genres/country/artists/dolly-parton.md | y | # Dolly Parton — Deep Dive |
| vendor/bitwize-music/genres/country/artists/tyler-childers.md | y | # Tyler Childers — Deep Dive |
| vendor/bitwize-music/genres/country/artists/sturgill-simpson.md | y | # Sturgill Simpson — Deep Dive |
| vendor/bitwize-music/genres/country/artists/randy-travis.md | y | # Randy Travis — Deep Dive |
| vendor/bitwize-music/genres/country/artists/george-strait.md | y | # George Strait — Deep Dive |
| vendor/bitwize-music/genres/country/artists/alan-jackson.md | y | # Alan Jackson — Deep Dive |
| vendor/bitwize-music/genres/country/artists/johnny-cash.md | y | # Johnny Cash — Deep Dive |
| vendor/bitwize-music/genres/country/artists/INDEX.md | y | # Country — Artist References |
| vendor/bitwize-music/genres/country/artists/garth-brooks.md | y | # Garth Brooks — Deep Dive |
| vendor/bitwize-music/genres/country/artists/willie-nelson.md | y | # Willie Nelson — Deep Dive |
| vendor/bitwize-music/genres/country/README.md | y | # Country |
| vendor/bitwize-music/genres/progressive-rock/README.md | y | # Progressive Rock |
| vendor/bitwize-music/genres/bolero/README.md | y | # Bolero |
| vendor/bitwize-music/genres/krautrock/README.md | y | # Krautrock |
| vendor/bitwize-music/genres/soca/README.md | y | # Soca |
| vendor/bitwize-music/genres/math-rock/README.md | y | # Math Rock |
| vendor/bitwize-music/genres/dark-ambient/README.md | y | # Dark Ambient |
| vendor/bitwize-music/genres/dub-techno/README.md | y | # Dub Techno |
| vendor/bitwize-music/genres/space-rock/README.md | y | # Space Rock |
| vendor/bitwize-music/genres/turkish-pop/README.md | y | # Turkish Pop |
| vendor/bitwize-music/genres/powerviolence/README.md | y | # Powerviolence |
| vendor/bitwize-music/genres/gregorian-chant/README.md | y | # Gregorian Chant |
| vendor/bitwize-music/genres/electroacoustic/README.md | y | # Electroacoustic |
| vendor/bitwize-music/genres/jam-band/README.md | y | # Jam Band |
| vendor/bitwize-music/genres/bubblegum-pop/README.md | y | # Bubblegum Pop |
| vendor/bitwize-music/genres/west-coast-rap/README.md | y | # West Coast Rap |
| vendor/bitwize-music/genres/coupe-decale/README.md | y | # Coupe-Decale |
| vendor/bitwize-music/genres/trip-hop/README.md | y | # Trip-Hop |
| vendor/bitwize-music/genres/indian-classical/README.md | y | # Indian Classical |
| vendor/bitwize-music/genres/ragtime/README.md | y | # Ragtime |
| vendor/bitwize-music/genres/celtic-punk/artists/dropkick-murphys.md | y | # Dropkick Murphys --- Deep Dive |
| vendor/bitwize-music/genres/celtic-punk/artists/INDEX.md | y | # Celtic Punk --- Artist References |
| vendor/bitwize-music/genres/celtic-punk/README.md | y | # Celtic Punk / Irish Punk |
| vendor/bitwize-music/genres/grunge/README.md | y | # Grunge |
| vendor/bitwize-music/genres/trap-metal/README.md | y | # Trap Metal |
| vendor/bitwize-music/genres/anisong/README.md | y | # Anisong |
| vendor/bitwize-music/genres/dancehall/README.md | y | # Dancehall |
| vendor/bitwize-music/genres/sophisti-pop/README.md | y | # Sophisti-pop |
| vendor/bitwize-music/genres/dangdut/README.md | y | # Dangdut |
| vendor/bitwize-music/genres/happy-hardcore/README.md | y | # Happy Hardcore |
| vendor/bitwize-music/genres/uk-garage/README.md | y | # UK Garage |
| vendor/bitwize-music/genres/cloud-rap/README.md | y | # Cloud Rap |
| vendor/bitwize-music/genres/tech-house/README.md | y | # Tech House |
| vendor/bitwize-music/genres/bossa-nova/README.md | y | # Bossa Nova |
| vendor/bitwize-music/genres/huayno/README.md | y | # Huayno |
| vendor/bitwize-music/genres/honky-tonk/README.md | y | # Honky-Tonk |
| vendor/bitwize-music/genres/conscious-hip-hop/README.md | y | # Conscious Hip-Hop |
| vendor/bitwize-music/genres/jungle/README.md | y | # Jungle |
| vendor/bitwize-music/genres/gypsy-jazz/README.md | y | # Gypsy Jazz |
| vendor/bitwize-music/genres/metalcore/README.md | y | # Metalcore |
| vendor/bitwize-music/genres/sega/README.md | y | # Sega |
| vendor/bitwize-music/genres/schlager/README.md | y | # Schlager |
| vendor/bitwize-music/genres/norteno/README.md | y | # Norteno |
| vendor/bitwize-music/genres/INDEX.md | y | # Genre Index |
| vendor/bitwize-music/genres/gangsta-rap/README.md | y | # Gangsta Rap |
| vendor/bitwize-music/genres/speed-metal/README.md | y | # Speed Metal |
| vendor/bitwize-music/genres/techno/README.md | y | # Techno |
| vendor/bitwize-music/genres/hair-metal/README.md | y | # Hair Metal |
| vendor/bitwize-music/genres/gnawa/README.md | y | # Gnawa |
| vendor/bitwize-music/genres/alternative/README.md | y | # Alternative Rock |
| vendor/bitwize-music/genres/heartland-rock/README.md | y | # Heartland Rock |
| vendor/bitwize-music/genres/new-wave/README.md | y | # New Wave |
| vendor/bitwize-music/genres/pop/artists/ace-of-base.md | y | # Ace of Base — Deep Dive |
| vendor/bitwize-music/genres/pop/artists/aqua.md | y | # Aqua — Deep Dive |
| vendor/bitwize-music/genres/pop/artists/taylor-swift.md | y | # Taylor Swift — Deep Dive |
| vendor/bitwize-music/genres/pop/artists/INDEX.md | y | # Pop — Artist References |
| vendor/bitwize-music/genres/pop/artists/carly-rae-jepsen.md | y | # Carly Rae Jepsen — Deep Dive |
| vendor/bitwize-music/genres/pop/artists/la-bouche.md | y | # La Bouche — Deep Dive |
| vendor/bitwize-music/genres/pop/README.md | y | # Pop |
| vendor/bitwize-music/genres/hard-bop/README.md | y | # Hard Bop |
| vendor/bitwize-music/genres/2-step-garage/README.md | y | # 2-Step Garage |
| vendor/bitwize-music/genres/j-pop/README.md | y | # J-Pop |
| vendor/bitwize-music/genres/noise-rock/README.md | y | # Noise Rock |
| vendor/bitwize-music/genres/rocksteady/README.md | y | # Rocksteady |
| vendor/bitwize-music/genres/vocal-house/README.md | y | # Vocal House |
| vendor/bitwize-music/genres/afro-cuban/README.md | y | # Afro-Cuban |
| vendor/bitwize-music/genres/red-dirt/README.md | y | # Red Dirt |
| vendor/bitwize-music/genres/ska/README.md | y | # Ska |
| vendor/bitwize-music/genres/calypso/README.md | y | # Calypso |
| vendor/bitwize-music/genres/indie-folk/README.md | y | # Indie Folk |
| vendor/bitwize-music/genres/western-swing/README.md | y | # Western Swing |
| vendor/bitwize-music/genres/k-pop/artists/ateez.md | y | # ATEEZ — Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/stray-kids.md | y | # Stray Kids — Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/itzy.md | y | # ITZY -- Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/blackpink.md | y | # BLACKPINK — Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/newjeans.md | y | # NewJeans — Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/aespa.md | y | # aespa — Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/ive.md | y | # IVE — Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/twice.md | y | # TWICE -- Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/seventeen.md | y | # SEVENTEEN — Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/enhypen.md | y | # ENHYPEN -- Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/dreamcatcher.md | y | # Dreamcatcher -- Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/zion-t.md | y | # Zion.T -- Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/dean.md | y | # DEAN -- Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/gi-dle.md | y | # (G)I-DLE — Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/iu.md | y | # IU -- Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/epik-high.md | y | # Epik High -- Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/INDEX.md | y | # K-Pop — Artist References |
| vendor/bitwize-music/genres/k-pop/artists/crush.md | y | # Crush -- Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/girls-generation.md | y | # Girls' Generation (SNSD) — Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/tvxq.md | y | # TVXQ -- Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/big-bang.md | y | # Big Bang — Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/le-sserafim.md | y | # LE SSERAFIM — Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/txt.md | y | # TXT (TOMORROW X TOGETHER) -- Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/exo.md | y | # EXO — Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/2ne1.md | y | # 2NE1 -- Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/shinee.md | y | # SHINee — Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/bts.md | y | # BTS (Bangtan Sonyeondan) — Deep Dive |
| vendor/bitwize-music/genres/k-pop/artists/red-velvet.md | y | # Red Velvet -- Deep Dive |
| vendor/bitwize-music/genres/k-pop/README.md | y | # K-Pop |
| vendor/bitwize-music/genres/ambient/artists/INDEX.md | y | # Ambient — Artist References |
| vendor/bitwize-music/genres/ambient/artists/enya.md | y | # Enya --- Deep Dive |
| vendor/bitwize-music/genres/ambient/README.md | y | # Ambient |
| vendor/bitwize-music/genres/doo-wop/README.md | y | # Doo-Wop |
| vendor/bitwize-music/genres/afro-house/README.md | y | # Afro House |
| vendor/bitwize-music/genres/viking-metal/README.md | y | # Viking Metal |
| vendor/bitwize-music/genres/champeta/README.md | y | # Champeta |
| vendor/bitwize-music/genres/mambo/README.md | y | # Mambo |
| vendor/bitwize-music/genres/nwobhm/README.md | y | # NWOBHM |
| vendor/bitwize-music/genres/progressive-metal/README.md | y | # Progressive Metal |
| vendor/bitwize-music/genres/desert-blues/README.md | y | # Desert Blues |
| vendor/bitwize-music/genres/neurofunk/README.md | y | # Neurofunk |
| vendor/bitwize-music/genres/chillwave/README.md | y | # CHILLWAVE |
| vendor/bitwize-music/genres/tropicalia/README.md | y | # Tropicalia |
| vendor/bitwize-music/genres/vaporwave/README.md | y | # Vaporwave |
| vendor/bitwize-music/genres/black-metal/README.md | y | # Black Metal |
| vendor/bitwize-music/genres/enka/README.md | y | # Enka |
| vendor/bitwize-music/genres/tango/README.md | y | # Tango |
| vendor/bitwize-music/genres/spoken-word/README.md | y | # Spoken Word |
| vendor/bitwize-music/genres/sufi/README.md | y | # Sufi |
| vendor/bitwize-music/genres/groove-metal/README.md | y | # Groove Metal |
| vendor/bitwize-music/genres/lo-fi-house/README.md | y | # Lo-Fi House |
| vendor/bitwize-music/genres/folktronica/README.md | y | # Folktronica |
| vendor/bitwize-music/genres/northern-soul/README.md | y | # Northern Soul |
| vendor/bitwize-music/genres/kizomba/README.md | y | # Kizomba |
| vendor/bitwize-music/genres/canterbury-scene/README.md | y | # Canterbury Scene |
| vendor/bitwize-music/genres/musicals/README.md | y | # Musicals |
| vendor/bitwize-music/genres/lounge/README.md | y | # Lounge |
| vendor/bitwize-music/genres/chopped-and-screwed/README.md | y | # Chopped and Screwed |
| vendor/bitwize-music/genres/no-wave/README.md | y | # No Wave |
| vendor/bitwize-music/genres/baroque-pop/README.md | y | # Baroque Pop |
| vendor/bitwize-music/genres/soukous/README.md | y | # Soukous |
| vendor/bitwize-music/genres/southern-hip-hop/README.md | y | # Southern Hip Hop |
| vendor/bitwize-music/genres/cinematic/README.md | y | # Cinematic |
| vendor/bitwize-music/genres/glitch-pop/README.md | y | # Glitch Pop |
| vendor/bitwize-music/genres/chiptune/README.md | y | # Chiptune |
| vendor/bitwize-music/genres/ethio-jazz/README.md | y | # Ethio-Jazz |
| vendor/bitwize-music/genres/vocal-jazz/README.md | y | # Vocal Jazz |
| vendor/bitwize-music/genres/new-jack-swing/README.md | y | # New Jack Swing |
| vendor/bitwize-music/genres/samba/README.md | y | # Samba |
| vendor/bitwize-music/genres/gqom/README.md | y | # Gqom |
| vendor/bitwize-music/genres/axe/README.md | y | # Axe |
| vendor/bitwize-music/genres/dungeon-synth/README.md | y | # Dungeon Synth |
| vendor/bitwize-music/genres/idm/README.md | y | # IDM |
| vendor/bitwize-music/genres/psychedelic-soul/README.md | y | # Psychedelic Soul |
| vendor/bitwize-music/genres/electropop/README.md | y | # Electropop |
| vendor/bitwize-music/genres/rave/README.md | y | # Rave |
| vendor/bitwize-music/genres/modal-jazz/README.md | y | # Modal Jazz |
| vendor/bitwize-music/genres/drill/README.md | y | # Drill |
| vendor/bitwize-music/genres/dubstep/README.md | y | # Dubstep |
| vendor/bitwize-music/genres/sevdah/README.md | y | # Sevdah |
| vendor/bitwize-music/genres/drum-and-bass/README.md | y | # Drum and Bass |
| vendor/bitwize-music/genres/shaabi/README.md | y | # Shaabi |
| vendor/bitwize-music/genres/semba/README.md | y | # Semba |
| vendor/bitwize-music/genres/speed-garage/README.md | y | # Speed Garage |
| vendor/bitwize-music/genres/spaghetti-western/README.md | y | # Spaghetti Western |
| vendor/bitwize-music/genres/slowcore/README.md | y | # Slowcore |
| vendor/bitwize-music/genres/barbershop/README.md | y | # Barbershop |
| vendor/bitwize-music/genres/swamp-pop/README.md | y | # Swamp Pop |
| vendor/bitwize-music/genres/future-funk/README.md | y | # Future Funk |
| vendor/bitwize-music/genres/afrobeats/README.md | y | # Afrobeats |
| vendor/bitwize-music/genres/singer-songwriter/README.md | y | # Singer-Songwriter |
| vendor/bitwize-music/genres/rnb/README.md | y | # R&B / Soul |
| vendor/bitwize-music/genres/fado/README.md | y | # Fado |
| vendor/bitwize-music/genres/outlaw-country/README.md | y | # Outlaw Country |
| vendor/bitwize-music/genres/brostep/README.md | y | # Brostep |
| vendor/bitwize-music/genres/alternative-rnb/README.md | y | # Alternative R&B |
| vendor/bitwize-music/genres/speedcore/README.md | y | # Speedcore |
| vendor/bitwize-music/genres/drone-metal/README.md | y | # Drone Metal |
| vendor/bitwize-music/genres/pop-rap/README.md | y | # Pop Rap |
| vendor/bitwize-music/genres/deep-house/README.md | y | # Deep House |
| vendor/bitwize-music/genres/broken-beat/README.md | y | # Broken Beat |
| vendor/bitwize-music/genres/mbaqanga/README.md | y | # Mbaqanga |
| vendor/bitwize-music/genres/hardcore-punk/README.md | y | # Hardcore Punk |
| vendor/bitwize-music/genres/dabke/README.md | y | # Dabke |
| vendor/bitwize-music/genres/americana/README.md | y | # Americana |
| vendor/bitwize-music/genres/blackgaze/README.md | y | # Blackgaze |
| vendor/bitwize-music/genres/chicano-rap/README.md | y | # Chicano Rap |
| vendor/bitwize-music/genres/synth-pop/README.md | y | # Synth-Pop |
| vendor/bitwize-music/genres/east-coast-hip-hop/README.md | y | # East Coast Hip Hop |
| vendor/bitwize-music/genres/dub/README.md | y | # Dub |
| vendor/bitwize-music/genres/post-metal/README.md | y | # Post-Metal |
| vendor/bitwize-music/genres/jersey-club/README.md | y | # Jersey Club |
| vendor/bitwize-music/genres/kwaito/README.md | y | # Kwaito |
| vendor/bitwize-music/genres/twee-pop/README.md | y | # Twee Pop |
| vendor/bitwize-music/genres/neotraditional-country/README.md | y | # Neotraditional Country |
| vendor/bitwize-music/genres/cyberpunk/README.md | y | # Cyberpunk |
| vendor/bitwize-music/genres/manele/README.md | y | # Manele |
| vendor/bitwize-music/genres/highlife/README.md | y | # Highlife |
| vendor/bitwize-music/genres/latin/README.md | y | # Latin |
| vendor/bitwize-music/genres/soundtrack/README.md | y | # Soundtrack |
| vendor/bitwize-music/genres/downtempo/README.md | y | # Downtempo |
| vendor/bitwize-music/genres/footwork/README.md | y | # Footwork |
| vendor/bitwize-music/genres/a-cappella/README.md | y | # A Cappella |
| vendor/bitwize-music/genres/banda/README.md | y | # Banda |
| vendor/bitwize-music/genres/trance/artists/cascada.md | y | # Cascada — Deep Dive |
| vendor/bitwize-music/genres/trance/artists/tatu.md | y | # t.A.T.u. — Deep Dive |
| vendor/bitwize-music/genres/trance/artists/ian-van-dahl.md | y | # Ian Van Dahl — Deep Dive |
| vendor/bitwize-music/genres/trance/artists/INDEX.md | y | # Trance — Artist References |
| vendor/bitwize-music/genres/trance/artists/alice-deejay.md | y | # Alice Deejay — Deep Dive |
| vendor/bitwize-music/genres/trance/artists/atb.md | y | # ATB — Deep Dive |
| vendor/bitwize-music/genres/trance/README.md | y | # Trance |
| vendor/bitwize-music/genres/trot/README.md | y | # Trot |
| vendor/bitwize-music/genres/video-game-music/README.md | y | # Video Game Music |
| vendor/bitwize-music/genres/pop-punk/README.md | y | # Pop Punk |
| vendor/bitwize-music/genres/breakbeat/README.md | y | # Breakbeat |
| vendor/bitwize-music/genres/mpb/README.md | y | # MPB (Musica Popular Brasileira) |
| vendor/bitwize-music/genres/country-rap/README.md | y | # Country Rap |
| vendor/bitwize-music/genres/madchester/README.md | y | # Madchester |
| vendor/bitwize-music/genres/bluegrass/README.md | y | # Bluegrass |
| vendor/bitwize-music/genres/bhangra/README.md | y | # Bhangra |
| vendor/bitwize-music/genres/bollywood/README.md | y | # Bollywood |
| vendor/bitwize-music/genres/plugg/README.md | y | # Plugg |
| vendor/bitwize-music/genres/cajun/README.md | y | # Cajun |
| vendor/bitwize-music/genres/throat-singing/README.md | y | # Throat Singing |
| vendor/bitwize-music/genres/electronic/artists/daft-punk.md | y | # Daft Punk — Deep Dive |
| vendor/bitwize-music/genres/electronic/artists/INDEX.md | y | # Electronic — Artist References |
| vendor/bitwize-music/genres/electronic/artists/eiffel-65.md | y | # Eiffel 65 — Deep Dive |
| vendor/bitwize-music/genres/electronic/README.md | y | # Electronic |
| vendor/bitwize-music/genres/musical-comedy/README.md | y | # Musical Comedy |
| vendor/bitwize-music/genres/madrigal/README.md | y | # Madrigal |
| vendor/bitwize-music/genres/jazz-rap/README.md | y | # Jazz Rap |
| vendor/bitwize-music/genres/house/README.md | y | # House |
| vendor/bitwize-music/genres/balearic/README.md | y | # Balearic |
| vendor/bitwize-music/genres/melodic-death-metal/README.md | y | # Melodic Death Metal |
| vendor/bitwize-music/genres/nu-disco/README.md | y | # Nu Disco |
| vendor/bitwize-music/genres/tropical-house/README.md | y | # Tropical House |
| vendor/bitwize-music/genres/taarab/README.md | y | # Taarab |
| vendor/bitwize-music/genres/arena-rock/README.md | y | # Arena Rock |
| vendor/bitwize-music/genres/son-cubano/README.md | y | # Son Cubano |
| vendor/bitwize-music/genres/baile-funk/README.md | y | # Baile Funk |
| vendor/bitwize-music/genres/trap/README.md | y | # Trap |
| vendor/bitwize-music/genres/folk/artists/israel-kamakawiwoole.md | y | # Israel Kamakawiwoʻole (IZ) — Deep Dive |
| vendor/bitwize-music/genres/folk/artists/INDEX.md | y | # Folk — Artist References |
| vendor/bitwize-music/genres/folk/artists/mumford-and-sons.md | y | # Mumford & Sons — Deep Dive |
| vendor/bitwize-music/genres/folk/README.md | y | # Folk |
| vendor/bitwize-music/genres/minimal-techno/README.md | y | # Minimal Techno |
| vendor/bitwize-music/genres/mariachi/README.md | y | # Mariachi |
| vendor/bitwize-music/genres/french-house/README.md | y | # French House |
| vendor/bitwize-music/genres/psychedelic-trance/README.md | y | # Psychedelic Trance |
| vendor/bitwize-music/genres/psybient/README.md | y | # Psybient |
