<!-- agency-generated: v1 -->
# Writing intent verb descriptions

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

## intent verb audit — 0 of 9 verbs need work

| Verb | Role | tool-desc flags |
|------|------|-----------------|
| `intent.assumptions` | transform | ✓ clean |
| `intent.decompose` | transform | ✓ clean |
| `intent.first_principles` | transform | ✓ clean |
| `intent.inversion` | transform | ✓ clean |
| `intent.premortem` | transform | ✓ clean |
| `intent.second_order` | transform | ✓ clean |
| `intent.steelman` | transform | ✓ clean |
| `intent.suggests` | transform | ✓ clean |
| `intent.tradeoffs` | transform | ✓ clean |

> Generated from each verb's live docstring (`prompt.evaluate(target="tool-desc")`).
> A clean row meets the grammar; a flagged row names the rule it breaks. The
> repo-wide sweep `scripts/optimize-verb-docs` emits an optimized candidate for
> every flagged verb (advisory — writes no source).
