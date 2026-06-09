<!-- agency-generated: v1 -->
# novel.check_content_warnings

Content-warning category scanner (transform, driver-free).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `body.` |  |  |

## Returns

``{warnings: [categories], hits: {category: [keywords]}}``.

## Chain-next

add to manuscript front-matter or trigger sensitivity-reader workflow (Slice 3).

## Details

Scans body for canonical content-warning keyword stems (violence / sex / substance / death / self-harm). Returns matched categories so publishers + reviewers can flag in front-matter.

## Example

```bash
agency-novel-check_content_warnings --intent-id $IID …
```
