<!-- agency-generated: v1 -->
# develop.scaffold_capability

Emit a CAPABILITY-AUTHORING.md-compliant capability skeleton.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name (kebab-case), kind (light|medium|heavy), base_dir (optional).` |  |  |

## Returns

{result: <path>, artefact: {kind, name, path, scaffold_version}}.

## Chain-next

plugin.lint_capability(name) — verify lint-clean.

## Details

(no further detail)

## Example

```bash
agency-develop-scaffold_capability --intent-id $IID …
```
