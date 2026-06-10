<!-- agency-generated: v1 -->
# prompt.fragment

Look up a single Dramatica prompt fragment (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `slug (str — ontology id like ``th.main-character`` or any kind-prefix alias the novel cap's ``_resolve_term`` recognises).` |  |  |

## Returns

``{slug, canonical_id, kind, text, tokens}`` OR ``{slug, error: 'NO_FRAGMENT'}`` when no fragment is authored for that entry yet.

## Chain-next

``prompt.fragments_for(scope)`` for multi-entry composition.

## Details

(no further detail)

## Example

```bash
agency-prompt-fragment --intent-id $IID …
```
