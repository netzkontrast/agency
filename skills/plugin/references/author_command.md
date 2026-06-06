<!-- agency-generated: v1 -->
# plugin.author_command

Render a slash-command markdown stub.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name (command name), description (str), body (markdown).` |  |  |

## Returns

``{result: <command_md_str>}``.

## Chain-next

write to ``commands/<name>.md``.

## Details

(no further detail)

## Example

```bash
agency-plugin-author_command --intent-id $IID …
```
