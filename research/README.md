# research/ — the PR1 review effort

A multi-agent critique of PR1 (the complete Agency plugin), run by Jules research
agents. The aim: concrete improvements to PR1 — more/better **templates**,
**schemas**, and **object-oriented design** — grounded in the prior art
(`the-agency-system`'s `Plan/`) and the installed plugins (superpowers, SuperClaude,
bitwize-music).

## Contract

- [`JULES_RESEARCH_PROTOCOL.md`](JULES_RESEARCH_PROTOCOL.md) — the binding protocol
  (four research gates: recursive ingestion → evidence → synthesis → self-review).
- [`SOURCES.md`](SOURCES.md) — the source repos (each agent decides what it can
  cleanly clone, read-only, never committed).

## Agents (each writes only its own dir; each opens one PR into the PR1 branch)

| Agent | Dir | Lens |
|---|---|---|
| 1 | `oo-architecture/` | OO critique + redesign (ToolResult envelope, boundary/driver protocols, Phase/Skill objects) |
| 2 | `templates-and-schemas/` | the artefact×capability gap matrix → a full Template×Schema library |
| 3 | `capability-specs/` | map every Plan-spec + plugin capability → an Agency target |
| 4 | `red-team/` | adversarial critique (sandbox, scaling, provenance, open review findings) |
| 5 | `code-context-mode/` | code-mode/context-mode token-economics + anchor-triad / next_suggested_tools |

The per-agent briefs are in [`prompts/`](prompts/). Findings land as five
independent PRs into `claude/extract-agency-plugin-o4JRc`; the human reviews and
distils them into the next iteration of PR1.
