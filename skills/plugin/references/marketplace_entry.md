<!-- agency-generated: v1 -->
# plugin.marketplace_entry

Render a marketplace.json entry.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name (plugin slug), version (semver), description (str), source (git URL or local path).` |  |  |

## Returns

``{result: <entry_dict>}``.

## Chain-next

merge into ``.claude-plugin/marketplace.json``.

## Details

(no further detail)

## Example

```bash
agency-plugin-marketplace_entry --intent-id $IID …
```
