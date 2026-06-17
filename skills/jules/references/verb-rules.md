<!-- agency-generated: v1 -->
# Writing jules verb descriptions

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

## jules verb audit — 0 of 22 verbs need work

| Verb | Role | tool-desc flags |
|------|------|-----------------|
| `jules.activities` | transform | ✓ clean |
| `jules.alias` | act | ✓ clean |
| `jules.apply_patch` | transform | ✓ clean |
| `jules.approve_awaiting` | effect | ✓ clean |
| `jules.approve_plan` | effect | ✓ clean |
| `jules.detect_mode` | transform | ✓ clean |
| `jules.dispatch` | effect | ✓ clean |
| `jules.lint_prompt` | transform | ✓ clean |
| `jules.list` | transform | ✓ clean |
| `jules.message` | effect | ✓ clean |
| `jules.patch` | transform | ✓ clean |
| `jules.patch_body` | transform | ✓ clean |
| `jules.plan` | transform | ✓ clean |
| `jules.quota` | transform | ✓ clean |
| `jules.recover` | effect | ✓ clean |
| `jules.resolve_source` | transform | ✓ clean |
| `jules.review_comment` | transform | ✓ clean |
| `jules.status` | transform | ✓ clean |
| `jules.status_all` | transform | ✓ clean |
| `jules.stop` | transform | ✓ clean |
| `jules.verify` | transform | ✓ clean |
| `jules.watch` | transform | ✓ clean |

> Generated from each verb's live docstring (`prompt.evaluate(target="tool-desc")`).
> A clean row meets the grammar; a flagged row names the rule it breaks. The
> repo-wide sweep `scripts/optimize-verb-docs` emits an optimized candidate for
> every flagged verb (advisory — writes no source).
