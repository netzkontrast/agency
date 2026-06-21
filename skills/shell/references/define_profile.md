<!-- agency-generated: v1 -->
# shell.define_profile

Define a named filter profile (include/exclude/context/budget) in the graph.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name (str), profile (JSON string — ``{include, exclude, context, budget}``).` |  |  |

## Returns

``{profile_id, name}``; or ``{error}`` on invalid JSON.

## Chain-next

reference by name in relevance calls.

## Details

Records an ``Artefact{kind:"filter-profile", name, profile=<JSON>}`` so named profiles can be referenced by name via ``load_filter_profile`` (Spec 350 Slice 3). Re-defining a name SUPERSEDES the prior version (bi-temporal trail kept). Graph-stored profiles override same-named config-file profiles.

## Example

```bash
agency-shell-define_profile --intent-id $IID …
```
