<!-- agency-generated: v1 -->
# plugin.scaffold

Render the plugin scaffold (plugin.json + .mcp.json).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name (plugin slug), version (semver), description (str).` |  |  |

## Returns

``{result: {plugin_json, mcp_json}}``.

## Chain-next

write the rendered files; commit; install.

## Details

(no further detail)

## Example

```bash
agency-plugin-scaffold --intent-id $IID …
```
