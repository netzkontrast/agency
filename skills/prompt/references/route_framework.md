<!-- agency-generated: v1 -->
# prompt.route_framework

Route a free-text ``draft`` to the ONE right framework (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `draft (str — the rough prompt/goal), intent_hint (str — override category detection), top (int — ranked candidates).` |  |  |

## Returns

``{intent, framework: {slug, name, complexity_tier}, alts: [...], rationale, scaffold}``.

## Chain-next

``prompt.render(framework_slug, fields)`` to fill it.

## Details

Two-level routing (Spec 305): (1) detect the ``intent_category`` by matching ``draft`` against the vendored category signals + each framework's ``discriminators`` (DERIVED from the library, not a hardcoded keyword table); (2) within that category, rank candidates by discriminator + token overlap. **Token-efficient — returns ONE framework plus ≤ 1 alt, never the whole library.** Records a ``Recommendation`` node SERVING the intent (298 parity).

## Example

```bash
agency-prompt-route_framework --intent-id $IID …
```
