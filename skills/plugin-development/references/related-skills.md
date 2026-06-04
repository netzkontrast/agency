# Related Skills — Decision Matrix

This skill (`plugin-development`) is the **outer lens** for working on the
agency plugin as a whole: manifest, install, distribution, MCP server,
component layout. For deep work inside specific component types, defer to
the right specialised skill.

## Decision matrix

| What you want to do | Skill to use | Where it lives |
|---|---|---|
| Build a generic (non-agency) Claude Code plugin | `superpowers-developing-for-claude-code:developing-claude-code-plugins` | Superpowers marketplace |
| Author a new agency capability (file in `agency/capabilities/`) | `agency:authoring-capabilities` | This repo, `skills/authoring-capabilities/` |
| Author or refine a SKILL.md (any plugin) | `superpowers:writing-skills` or `agency:skill-creation` | Both — Superpowers is generic; agency adds CSO lint |
| Brainstorm what to build before touching code | `superpowers:brainstorming` | Superpowers |
| Write the spec for a multi-step change | `superpowers:writing-plans` (via brainstorming) | Superpowers |
| Implement following TDD | `agency:test-driven-development` or `superpowers:test-driven-development` | Identical content, choose either |
| Debug a failure (root cause first) | `agency:systematic-debugging` | This repo |
| Verify before claiming done | `agency:verification-before-completion` | This repo |
| Review your own diff before PR | `agency:code-review` | This repo |
| Spec-panel review (multi-expert critique) | `agency:spec-panel` | This repo |
| Dispatch coding work to a remote Jules agent | `agency:jules-dispatch` | This repo |
| Get a fresh-session overview of the agency engine | `agency:help` | This repo |

## When THIS skill is the right one

Use `agency:plugin-development` when:

- You're adding a top-level component to the plugin (not a capability — that's `authoring-capabilities`).
- You're touching `pyproject.toml`, `.claude-plugin/plugin.json`, `.mcp.json`, `bin/*`, `agency/install.py`, or the slash-commands/skills regen path.
- You're publishing a release, tagging a version, or updating the marketplace entry.
- Your question is about Claude Code's plugin contract (manifest schema, `${CLAUDE_PLUGIN_ROOT}`, hook events, MCP server entrypoint shape).
- You're troubleshooting an install or MCP-startup failure.

## When `authoring-capabilities` is the right one

Use `agency:authoring-capabilities` when:

- You're adding or extending a file in `agency/capabilities/`.
- You're defining `@verb`-decorated methods.
- You're writing an `OntologyExtension` (nodes, enums, edges, skills, schemas).
- You're running `capability_develop_scaffold_capability` or `capability_plugin_lint_capability`.

The boundary: `plugin-development` is "I'm working on the plugin",
`authoring-capabilities` is "I'm working inside the agency engine".

## When `skill-creation` is the right one

Use `agency:skill-creation` (or `superpowers:writing-skills`) when:

- You're writing or editing a SKILL.md anywhere in the plugin (including this one).
- You need to validate against the Claude-Skill Ontology (kebab-case name, "Use when…" trigger, allowed-tools sanity, structural markers).
- You want the RED-GREEN-REFACTOR discipline for skill authoring.

The Superpowers `writing-skills` skill and the agency `skill-creation` skill
overlap heavily. `skill-creation` adds the agency-specific CSO linter
(`capability_plugin_lint_skill`); pick `writing-skills` for a generic
Claude Code plugin and `skill-creation` for this repo.

## When Superpowers is the right one

Use the Superpowers `developing-claude-code-plugins` skill when:

- You're building a Claude Code plugin that has nothing to do with the agency engine.
- You need the canonical Claude Code plugin contract reference (the
  `references/` in that skill are the upstream truth — this skill's
  `plugin-structure.md` is a port).
- You need cross-platform hook patterns (`polyglot-hooks.md`).

## Working with multiple skills

It's common to combine:

1. **Start** with `superpowers:brainstorming` (or `agency:brainstorming`) to
   refine the idea into a design.
2. **Plan** via `superpowers:writing-plans` to produce an implementation plan.
3. **Implement** with TDD (`agency:test-driven-development`), using
   `agency:plugin-development` (this skill) when you touch plugin-edge files
   and `agency:authoring-capabilities` when you touch capability-internal files.
4. **Verify** with `agency:verification-before-completion`.
5. **Review** with `agency:code-review`.
6. **Release** following [`release-and-distribution.md`](release-and-distribution.md).

The skills don't conflict — they hand off cleanly when the focus shifts.
