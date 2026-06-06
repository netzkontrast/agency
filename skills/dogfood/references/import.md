<!-- agency-generated: v1 -->
# dogfood.import

Replay a JSON export into this graph, preserving ids + windows.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `path (str — JSON file written by ``dogfood.export``).` |  |  |

## Returns

``{imported_nodes, imported_edges, version}``. Raises: FileNotFoundError on missing path; ValueError on unsupported export version.

## Chain-next

terminal — caller can verify with ``MATCH (n) RETURN count(n)`` or ``reflect.search``.

## Details

Closes Spec 020's merge-conflict recovery loop: each branch's DB is exported, the binary conflict is discarded, and both JSONs replay into a fresh DB on the merged branch. Preservation discipline: nodes land at their original ids with the original ``vfrom``/``vto`` window — bypassing ``record()``'s clock tick so bi-temporal history is exact. After replay, the memory's logical clock advances past every imported tick so new writes cannot collide with imported windows.

## Example

```bash
agency-dogfood-import --intent-id $IID …
```
