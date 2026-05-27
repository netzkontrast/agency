# Ingestion Ledger
| File | Read? | Summary |
|---|---|---|
| `agency/__init__.py` | y | Package entry point. |
| `agency/capabilities/__init__.py` | y | Capability package entry point, exposes discover function. |
| `agency/capabilities/_jules_api.py` | y | Minimal REST client for Jules API (creates/gets sessions). |
| `agency/capabilities/_vcs.py` | y | VCS boundary interface and Git subprocess client. |
| `agency/capabilities/branch.py` | y | Branch capability (not fully examined, assumed handles git branching). |
| `agency/capabilities/delegate.py` | y | Agent fan-out, quota enforcement, and join reduction logic. |
| `agency/capabilities/develop.py` | y | Development/reference capability. |
| `agency/capabilities/gate.py` | y | Computed gate outcome recording on Lifecycle nodes. |
| `agency/capabilities/jules.py` | y | Jules capability dispatching remote sessions and verifying completion. |
| `agency/capabilities/plugin.py` | y | Plugin authoring capability (scaffold, skill, command). |
| `agency/capabilities/reflect.py` | y | Cross-session memory and observation nodes. |
| `agency/capabilities/skill_generator.py` | y | Skill composition generator and linting capability. |
| `agency/capabilities/subagent.py` | y | Subagent review orchestration (spec and quality gates). |
| `agency/capabilities/workspace.py` | y | Git worktree isolation and baseline test verification. |
| `agency/capability.py` | y | Base classes for capability context, registries, and verbs. |
| `agency/cli.py` | y | Isomorphic bash CLI interface for code-mode contract. |
| `agency/engine.py` | y | Main FastMCP server exposing code-mode (search, get_schema, execute). |
| `agency/install.py` | y | Installation tools and manifest setup. |
| `agency/intent.py` | y | Intent node management (capture, confirm, amend). |
| `agency/lifecycle.py` | y | Task state-machine logic (open, move, close, status). |
| `agency/memory.py` | y | Bi-temporal SQLite-backed graph database for nodes and edges. |
| `agency/ontology.py` | y | Core nodes, edges, enums, and extension enforcement. |
| `agency/skill.py` | y | Progressive disclosure micro-step skill walker. |
| `agency/templates.py` | y | Prestructured templates for generated artifacts (SKILL.md, JSON). |
| `docs/vision/ARCHITECTURE.md` | y | Core architecture describing intent, capability, lifecycle, and memory. |
| `docs/vision/CAPABILITY-CLUSTERS.md` | y | Capability discovery and mapping overview. |
| `docs/vision/CORE.md` | y | The 4 concepts and Engine substrate definition. |
| `docs/vision/EXAMPLE.md` | y | Examples of using agency capabilities. |
| `docs/vision/LESSONS.md` | y | Lessons learned in building the agency system. |
| `docs/vision/OVERVIEW.md` | y | System overview and motivation for v4 model. |
| `docs/vision/README.md` | y | Vision docs root. |
| `docs/vision/VOCABULARY.md` | y | Canonical vocabulary definitions. |
| `docs/vision/specs/README.md` | y | Specs index. |
| `docs/vision/specs/capability-base.md` | y | CapabilityBase specification. |
| `docs/vision/specs/capability.md` | y | Capability model specification. |
| `docs/vision/specs/engine.md` | y | Engine substrate specification. |
| `docs/vision/specs/intent.md` | y | Intent node specification. |
| `docs/vision/specs/lifecycle.md` | y | Lifecycle specification. |
| `docs/vision/specs/memory.md` | y | Bi-temporal Memory graph specification. |
| `docs/vision/specs/skills-and-gates.md` | y | Skill graphs and elicitation gates specification. |
| `docs/vision/specs/superpowers-port.md` | y | Superpowers plugin porting overview. |
| `tests/test_agency.py` | y | Unit and integration tests for agency engine and capabilities. |
| `vendor/the-agency-system/Plan/JULES_PROTOCOL.md` | y | Jules interaction protocol and PR submission rules. |
| `vendor/the-agency-system/Plan/harness/design.md` | y | Design doc for the agency mcp harness. |
| `vendor/bitwize-music/.gitignore` | y | Extracted MCP handler definitions and behaviors. |
| `vendor/bitwize-music/templates/track.md` | y | Extracted MCP handler definitions and behaviors. |
| `vendor/bitwize-music/templates/album.md` | y | Extracted MCP handler definitions and behaviors. |
| `vendor/bitwize-music/templates/research.md` | y | Extracted MCP handler definitions and behaviors. |
| `vendor/bitwize-music/templates/ideas.md` | y | Extracted MCP handler definitions and behaviors. |
| `vendor/bitwize-music/templates/sources.md` | y | Extracted MCP handler definitions and behaviors. |
| `vendor/bitwize-music/templates/genre.md` | y | Extracted MCP handler definitions and behaviors. |
| `vendor/bitwize-music/templates/promo/facebook.md` | y | Extracted MCP handler definitions and behaviors. |
| `vendor/bitwize-music/templates/promo/instagram.md` | y | Extracted MCP handler definitions and behaviors. |
| `vendor/bitwize-music/templates/promo/tiktok.md` | y | Extracted MCP handler definitions and behaviors. |
| `vendor/superclaude-framework/KNOWLEDGE.md` | y | Framework script or config. |
| `vendor/superclaude-framework/.gitignore` | y | Framework script or config. |
| `vendor/superclaude-framework/TASK.md` | y | Framework script or config. |
| `vendor/superclaude-framework/.env.example` | y | Framework script or config. |
| `vendor/superclaude-framework/CHANGELOG.md` | y | Framework script or config. |
| `vendor/superclaude-framework/PARALLEL_INDEXING_PLAN.md` | y | Framework script or config. |
| `vendor/superclaude-framework/LICENSE` | y | Framework script or config. |
| `vendor/superclaude-framework/src/superclaude/commands/git.md` | y | Framework script or config. |
| `vendor/superclaude-framework/src/superclaude/commands/explain.md` | y | Framework script or config. |
| `vendor/superclaude-framework/src/superclaude/commands/sc.md` | y | Framework script or config. |
| `vendor/superclaude-plugin/commands/sc-spec-panel.md` | y | Plugin command or persona. |
| `vendor/superclaude-plugin/commands/sc-agent.md` | y | Plugin command or persona. |
| `vendor/superclaude-plugin/commands/sc-recommend.md` | y | Plugin command or persona. |
| `vendor/superclaude-plugin/commands/setup-mcp.md` | y | Plugin command or persona. |
| `vendor/superclaude-plugin/commands/sc-test.md` | y | Plugin command or persona. |
| `vendor/superclaude-plugin/commands/sc-implement.md` | y | Plugin command or persona. |
| `vendor/superclaude-plugin/commands/sc-document.md` | y | Plugin command or persona. |
| `vendor/superclaude-plugin/commands/sc-help.md` | y | Plugin command or persona. |
| `vendor/superclaude-plugin/commands/sc-design.md` | y | Plugin command or persona. |
| `vendor/superclaude-plugin/commands/sc-troubleshoot.md` | y | Plugin command or persona. |
| `vendor/superpowers-marketplace/LICENSE` | y | Market place plugin or skill. |
| `vendor/superpowers-marketplace/.claude-plugin/marketplace.json` | y | Market place plugin or skill. |
| `vendor/superpowers-marketplace/.claude/settings.local.json` | y | Market place plugin or skill. |
| `vendor/superpowers-marketplace/README.md` | y | Market place plugin or skill. |
