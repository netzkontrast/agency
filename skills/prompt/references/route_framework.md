<!-- agency-generated: v1 -->
# prompt.route_framework

Route a free-text ``draft`` to the ONE right framework (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `draft (str — the rough prompt/goal), intent_hint (str — override category detection), top (int — how many ALTERNATES to return beyond the best; ``top=1`` ⇒ best + ≤ 1 alt).` |  |  |

## Returns

``{intent, framework: {slug, name, complexity_tier}, alts: [...], rationale, scaffold}``.

## Chain-next

``prompt.render(framework_slug, fields)`` to fill it.

## Details

Two-level routing (Spec 305): (1) detect the ``intent_category`` by matching ``draft`` against the vendored category signals + each framework's ``discriminators`` (DERIVED from the library, not a hardcoded keyword table); (2) within that category, rank candidates by discriminator + token overlap. **Token-efficient — returns ONE framework plus ≤ 1 alt, never the whole library.** Records a ``Recommendation`` node SERVING the intent (298 parity). Trigger vocabulary — which words route to which intent (a SUMMARY so you can phrase a draft or pick an ``intent_hint``; the live, authoritative signals live in ``data/frameworks.json`` → ``intent_signals`` + per-framework ``discriminators``): - **recover** ← "reverse engineer", "recover prompt", "what prompt produced" - **clarify** ← "not sure what I need", "help me figure out", "interview me" - **create** ← "write", "create", "draft", "generate", "build", "design" - **transform**← "rewrite", "refactor", "improve", "summarize", "convert" - **reason** ← "calculate", "solve", "analyze", "compare options", "should I" - **critique** ← "review", "stress test", "find flaws", "risks", "what could go wrong" - **agentic** ← "use tools", "search and", "run code", "query a database" When a draft is ambiguous or the words straddle two intents, pass ``intent_hint`` to pin the category; the discriminators then pick the framework within it.

## Example

```bash
agency-prompt-route_framework --intent-id $IID …
```
