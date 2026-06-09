<!-- agency-generated: v1 -->
# music.transcribe_sheet

Transcribe audio → sheet music via AudioDriver (act); produces sheet-music artefact.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, path (the audio file).` |  |  |

## Returns

``{result, artefact}`` where artefact.kind = ``sheet-music`` with source path.

## Chain-next

``music.publish_asset``.

## Details

The transcription tool (AnthemScore-class) runs behind the driver, never inline.

## Example

```bash
agency-music-transcribe_sheet --intent-id $IID …
```
