<!-- agency-generated: v1 -->
# music.format_clipboard

Format text for clipboard paste into Suno / other generation services (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `text, format (one of ``lyrics`` / ``style-prompt``; default ``lyrics``).` |  |  |

## Returns

``{text, format, char_count}``.

## Chain-next

paste into Suno / external generation service.

## Details

Bitwize ports ``format_for_clipboard`` from the content handler. Two shapes: - ``lyrics``: strips bracketed section tags + trailing whitespace (Suno-safe). - ``style-prompt``: collapses multi-line prompts to single-line + cap at 200 chars (Suno style-prompt limit).

## Example

```bash
agency-music-format_clipboard --intent-id $IID …
```
