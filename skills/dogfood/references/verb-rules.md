<!-- agency-generated: v1 -->
# Writing dogfood verb descriptions

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

## dogfood verb audit — 3 of 14 verbs need work

| Verb | Role | tool-desc flags |
|------|------|-----------------|
| `dogfood.apply_amendment` | effect | ✓ clean |
| `dogfood.boundary_use_audit` | transform | ✓ clean |
| `dogfood.collect` | transform | ✓ clean |
| `dogfood.export` | effect | ✓ clean |
| `dogfood.import` | effect | ✓ clean |
| `dogfood.note` | act | ✓ clean |
| `dogfood.parse_amendment` | transform | ✓ clean |
| `dogfood.recall_overflow_slice` | transform | ✓ clean |
| `dogfood.record_decision` | effect | ✓ clean |
| `dogfood.render` | transform | ✓ clean |
| `dogfood.replay_events` | transform | ✓ clean |
| `dogfood.spec_refs` | transform | `missing_inputs`, `missing_returns`, `no_chain_next` |
| `dogfood.spec_status` | transform | `missing_inputs`, `missing_returns`, `no_chain_next` |
| `dogfood.specs` | transform | `missing_inputs`, `missing_returns`, `no_chain_next` |

> Generated from each verb's live docstring (`prompt.evaluate(target="tool-desc")`).
> A clean row meets the grammar; a flagged row names the rule it breaks. The
> repo-wide sweep `scripts/optimize-verb-docs` emits an optimized candidate for
> every flagged verb (advisory — writes no source).
