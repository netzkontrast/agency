<!-- agency-generated: v1 -->
# prompt.register_framework

Write a custom framework to the project overlay (effect; extensible).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `slug (str), payload (dict — at minimum ``template``; any of name/intent_category/complexity_tier/audience/components/ when_to_use/discriminators override the vendored defaults). ``intent_category``/``complexity_tier``/``audience`` must be valid ontology enum values (validated HERE so a bad overlay fails fast, not later at ``render`` time when the ``PromptFramework`` node is recorded). overlay_path (str — defaults to the project overlay).` |  |  |

## Returns

``{slug, name, intent_category, audience, overlay_path}`` OR ``{slug, error: 'INVALID_ARGUMENT', invalid: {...}}`` when the template is missing or an enum field is out of range.

## Chain-next

``prompt.framework(slug)`` to verify the round-trip.

## Details

(no further detail)

## Example

```bash
agency-prompt-register_framework --intent-id $IID …
```
