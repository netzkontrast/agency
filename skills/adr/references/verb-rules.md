<!-- agency-generated: v1 -->
# Writing adr verb descriptions

A verb description is a **functional** prompt — its job is invocation + cheap
discovery, not persuasion, and **not routing** (that is the capability's job:
`search` / `recommend` / the SkillDoc's "When to use"). Full rules + canon
(Spec 023): `agency/capabilities/prompt/references/tool-desc-authoring.md`. Score
any verb docstring with `prompt.evaluate(target="tool-desc")`.

**The grammar (each maps to a `tool-desc` flag):**
- **first sentence** — ≤120 chars, single clause, verb-first, role-tagged; **no Role** (`role_padding` · `long_brief`)
- **`Inputs:`** — `name (type) — meaning`, per user-facing arg (`missing_inputs`)
- **`Returns:`** — the wire shape; error / null cases too (`missing_returns`)
- **`chain_next:`** — the verb to call next, or `(terminal)` (advisory `no_chain_next`)

## adr verb audit — 1 of 19 verbs need work

| Verb | Role | tool-desc flags |
|------|------|-----------------|
| `adr.approve` | act | ✓ clean |
| `adr.architecture` | act | ✓ clean |
| `adr.catalogue` | transform | ✓ clean |
| `adr.dod_check` | transform | ✓ clean |
| `adr.draft` | act | ✓ clean |
| `adr.extract_decisions` | act | ✓ clean |
| `adr.hints` | transform | ✓ clean |
| `adr.impact` | transform | ✓ clean |
| `adr.link` | act | ✓ clean |
| `adr.publish` | effect | ✓ clean |
| `adr.read` | act | ✓ clean |
| `adr.render` | act | ✓ clean |
| `adr.review_sweep` | effect | ✓ clean |
| `adr.spec_decisions_ready` | transform | ✓ clean |
| `adr.supersede` | act | ✓ clean |
| `adr.theme` | act | ✓ clean |
| `adr.theme_status` | transform | ✓ clean |
| `adr.update` | act | ✓ clean |
| `adr.validate` | transform | `long_brief` |

> Generated from each verb's live docstring (`prompt.evaluate(target="tool-desc")`).
> A clean row meets the grammar; a flagged row names the rule it breaks. The
> repo-wide sweep `scripts/optimize-verb-docs` emits an optimized candidate for
> every flagged verb (advisory — writes no source).
