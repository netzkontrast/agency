<!-- agency-generated: v1 -->
# jules.patch

Per-output stats (``files``, ``lines``, ``bytes``) from the session's outputs — NO body.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session (sid).` |  |  |

## Returns

``{outputs: [{index, files, lines, bytes}]}``.

## Chain-next

``jules.patch_body(session=, output_index=)`` for the actual unidiff bytes; ``jules.apply_patch`` for recovery.

## Details

Used by the watcher to classify silent-fail variants (empty patch vs missing push). Body retrieval is the explicit ``patch_body`` verb.

## Example

```bash
agency-jules-patch --intent-id $IID …
```
