<!-- agency-generated: v1 -->
# novel.promote_idea

Transition an Idea to a Novel, recording the PROMOTED_TO edge (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `idea_id, title, author.` |  |  |

## Returns

``{idea_id, novel_id, title, status}``.

## Chain-next

``novel.create_chapter`` to start outlining.

## Details

Flips the Idea's status to ``promoted``, mints a Novel node, and wires a PROMOTED_TO edge. Mirrors music's promote_idea / Idea-to- Album lineage.

## Example

```bash
agency-novel-promote_idea --intent-id $IID …
```
