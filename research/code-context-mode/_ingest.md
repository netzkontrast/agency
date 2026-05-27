# Ingestion Ledger

## Work repo
agency/engine.py · y · engine core, wires tools by reflection, exports search/get_schema/execute code-mode
agency/cli.py · y · bash-callable cli, uses search/get_schema/execute, identical to code-mode mcp
agency/skill.py · y · progressive disclosure of skill phases, current() returns only active spec
agency/capabilities/plugin.py · y · plugin capability, imports from templates, returns artefacts, help verb
agency/capabilities/develop.py · y · develop capability, checklist and reference verbs for T3 docs
tests/test_agency.py · y · tests engine integration, reference docs fetch, help output

## Sources
vendor/the-agency-system/Plan/000-overview.md · y · references anchor triads, token limits (<4 KB, <500 tokens context)
vendor/the-agency-system/Plan/008-codemode-registry/spec.md · y · CodeMode registry, background tools, defer_schema, 500 token budget
vendor/the-agency-system/Plan/harness/restructure/spec.md · y · restructure plan
vendor/the-agency-system/Plan/harness/_research/01-fastmcp-in-memory.md · y · fastmcp details
vendor/the-agency-system/Plan/harness/_research/06-phase-2-through-8-forward-compat.md · y · phase planning
vendor/the-agency-system/Plan/harness/_research/05-domain-isomorphism.md · y · isomorphism
vendor/the-agency-system/Plan/harness/_research/03-test-coverage-baseline.md · y · testing
vendor/the-agency-system/Plan/harness/_research/02-claude-bare-plugin-dir.md · y · claude plugin
vendor/the-agency-system/Plan/harness/design.md · y · overall design
vendor/the-agency-system/Plan/harness/VOCABULARY.md · y · vocabulary

## Web
FastMCP Code Mode docs (https://gofastmcp.com/servers/transforms/code-mode) · y · search, get_schema, execute meta-tools, detail levels, patterns
