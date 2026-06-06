<!-- agency-generated: v1 -->
# plugin.step_doc

Render a step-doc markdown block (audit trail entry).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `step (title), output (deliverable), status (done|partial|skip), inputs (str, optional), notes (str, optional).` |  |  |

## Returns

``{result: <markdown_str>}``.

## Chain-next

append to the working step-doc file.

## Details

(no further detail)

## Example

```bash
agency-plugin-step_doc --intent-id $IID …
```
