<!-- agency-generated: v1 -->
# music.load_override

Load a user-authored override file from the configured overrides dir (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name (override file stem).` |  |  |

## Returns

``{name, found, body}``.

## Chain-next

pass ``body`` into a verb that takes the override as input.

## Details

Bitwize lets users author `{overrides}/<name>.md` (e.g. a custom pronunciation guide or genre tweak); this verb reads it. Empty/missing returns ``found=False``.

## Example

```bash
agency-music-load_override --intent-id $IID …
```
