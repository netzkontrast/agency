<!-- agency-generated: v1 -->
# jules.detect_mode

Mode A (dogfood) vs Mode B (delegate) — pure decision on dispatch source.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `source (str — owner/repo of the dispatch target).` |  |  |

## Returns

``{mode: dogfood|delegate, self_source, reason}``.

## Chain-next

pass ``mode`` to ``_jules_preambles.assemble(...)``.

## Details

Mode A when ``source == DISPATCH_SELF_SOURCE`` (the agency repo itself); Mode B for any other source. Bound by Phase 1 of the ``jules-protocol-preamble`` skill.

## Example

```bash
agency-jules-detect_mode --intent-id $IID …
```
