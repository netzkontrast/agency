<!-- agency-generated: v1 -->
# Writing prompt verb descriptions

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

## prompt verb audit — 2 of 19 verbs need work

| Verb | Role | tool-desc flags |
|------|------|-----------------|
| `prompt.assemble_scene_brief` | act | ✓ clean |
| `prompt.audit` | effect | ✓ clean |
| `prompt.audit_gate` | effect | ✓ clean |
| `prompt.brief_audit` | effect | ✓ clean |
| `prompt.brief_finalize` | effect | ✓ clean |
| `prompt.brief_render` | act | ✓ clean |
| `prompt.catalog_list` | transform | ✓ clean |
| `prompt.engineer` | act | ✓ clean |
| `prompt.evaluate` | effect | ✓ clean |
| `prompt.fragment` | transform | ✓ clean |
| `prompt.fragments_for` | transform | ✓ clean |
| `prompt.framework` | transform | ✓ clean |
| `prompt.frameworks_for` | transform | ✓ clean |
| `prompt.intent_capture` | act | ✓ clean |
| `prompt.register_fragment` | effect | `long_brief` |
| `prompt.register_framework` | effect | `long_brief` |
| `prompt.render` | act | ✓ clean |
| `prompt.route_framework` | effect | ✓ clean |
| `prompt.token_budget_gate` | effect | ✓ clean |

> Generated from each verb's live docstring (`prompt.evaluate(target="tool-desc")`).
> A clean row meets the grammar; a flagged row names the rule it breaks. The
> repo-wide sweep `scripts/optimize-verb-docs` emits an optimized candidate for
> every flagged verb (advisory — writes no source).
