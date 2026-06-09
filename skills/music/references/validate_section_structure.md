<!-- agency-generated: v1 -->
# music.validate_section_structure

Validate section tag well-formedness (Title Case in brackets) (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lyrics.` |  |  |

## Returns

``{ok, findings: [{line, tag, issue, severity}]}``.

## Chain-next

fix flagged tags before the prosody pass.

## Details

(no further detail)

## Example

```bash
agency-music-validate_section_structure --intent-id $IID …
```
