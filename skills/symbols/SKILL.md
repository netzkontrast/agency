---
name: symbols
description: "Use when output must be compact without losing meaning — large-scale results,"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# symbols capability

A native reimplementation of SuperClaude's Token-Efficiency symbol system (`MODE_Token_Efficiency` + `BUSINESS_SYMBOLS`): a decidable phrase↔symbol substitution that compresses prose for dense communication and expands it back. Pure transforms (like `thinking`), so they compose anywhere; pairs with `mode.token_efficiency` (the posture) — this is the mechanism.

## When to use

- A token-constrained context that needs compressed output
- A status or logic digest that benefits from symbolic shorthand
- Expanding a symbol-dense note back into prose for a reader

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `compress` | transform | Substitute known phrases with symbols — dense, decidable (Spec 300). | [details](references/compress.md) |
| `expand` | transform | Expand symbols back into prose (the inverse of ``compress``). | [details](references/expand.md) |
| `legend` | transform | The phrase↔symbol legend. | [details](references/legend.md) |

## Example

```bash
await call_tool('capability_symbols_compress', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Padding a token-tight reply with prose → symbols.compress it
- Pasting symbol-dense text to a reader who needs prose → symbols.expand it

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`symbols-usage`** (usage): use-transform → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'symbols-usage', 'inputs': {}, 'intent_id': '…'})`
