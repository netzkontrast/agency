<!-- agency-generated: v1 -->
# Writing loop verb descriptions

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

## loop verb audit — 1 of 15 verbs need work

| Verb | Role | tool-desc flags |
|------|------|-----------------|
| `loop.add_criterion` | effect | ✓ clean |
| `loop.add_member` | effect | ✓ clean |
| `loop.advance` | effect | ✓ clean |
| `loop.compile` | transform | ✓ clean |
| `loop.critique_goal` | transform | ✓ clean |
| `loop.detect_models` | act | ✓ clean |
| `loop.egress_consent` | transform | ✓ clean |
| `loop.emit` | effect | ✓ clean |
| `loop.emit_runner` | effect | ✓ clean |
| `loop.frame_goal` | effect | ✓ clean |
| `loop.open` | effect | `long_brief` |
| `loop.preview` | act | ✓ clean |
| `loop.recommend_council` | transform | ✓ clean |
| `loop.register_model` | effect | ✓ clean |
| `loop.verify_report` | transform | ✓ clean |

> Generated from each verb's live docstring (`prompt.evaluate(target="tool-desc")`).
> A clean row meets the grammar; a flagged row names the rule it breaks. The
> repo-wide sweep `scripts/optimize-verb-docs` emits an optimized candidate for
> every flagged verb (advisory — writes no source).
