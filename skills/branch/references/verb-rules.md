<!-- agency-generated: v1 -->
# Writing branch verb descriptions

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

## branch verb audit — 1 of 3 verbs need work

| Verb | Role | tool-desc flags |
|------|------|-----------------|
| `branch.assess` | transform | ✓ clean |
| `branch.commit_smart` | transform | ✓ clean |
| `branch.finish` | effect | `long_brief` |

> Generated from each verb's live docstring (`prompt.evaluate(target="tool-desc")`).
> A clean row meets the grammar; a flagged row names the rule it breaks. The
> repo-wide sweep `scripts/optimize-verb-docs` emits an optimized candidate for
> every flagged verb (advisory — writes no source).
