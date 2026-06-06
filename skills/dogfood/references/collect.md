<!-- agency-generated: v1 -->
# dogfood.collect

Walk ``plan_dir`` for ``DOGFOOD-NOTES.md`` files; extract observations.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `plan_dir (str — root dir of plans; default ``Plan``).` |  |  |

## Returns

``{observations: [{plan, kind, index, title, text}], texts: [str], count, plans: [str], warnings: [str]}``.

## Chain-next

``reflect.batch_note(scope='observation', texts=)`` to seed the graph from one-shot migration of legacy files.

## Details

Deprecated for ongoing use — prefer ``dogfood.note`` (graph- native authoring) + ``dogfood.render`` (markdown projection on demand). Errors (missing dir, unreadable file) degrade into the ``warnings`` list rather than raising.

## Example

```bash
agency-dogfood-collect --intent-id $IID …
```
