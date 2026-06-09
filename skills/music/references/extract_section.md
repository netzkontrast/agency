<!-- agency-generated: v1 -->
# music.extract_section

Extract the body under a ``[<label>]`` section tag (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lyrics, label (e.g. ``Verse 1``).` |  |  |

## Returns

``{section, body}``.

## Chain-next

pass the section body to a per-section transform.

## Details

(no further detail)

## Example

```bash
agency-music-extract_section --intent-id $IID …
```
